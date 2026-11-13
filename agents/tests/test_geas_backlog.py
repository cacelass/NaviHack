"""Tests de la traducción GEAS ↔ backlog del arnés (sin red)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.agents import geas_backlog


def test_parse_criteria_acepta_encabezado_con_y_sin_acento():
    texto = "Descripción\n\nCriterios de aceptación:\n  1. uno\n  2. dos\n\nOtra cosa"
    assert geas_backlog.parse_criteria(texto) == ["uno", "dos"]
    legacy = "Criterios de aceptacion:\n  1. uno\n  2. dos"
    assert geas_backlog.parse_criteria(legacy) == ["uno", "dos"]


def test_parse_criteria_sin_bloque_devuelve_vacio():
    assert geas_backlog.parse_criteria("solo una descripción") == []


def test_split_title_reconoce_id_y_titulo():
    assert geas_backlog.split_title("SCOPE-001: Definir el rumbo") == (
        "SCOPE-001",
        "Definir el rumbo",
    )
    assert geas_backlog.split_title("MIG-GEAS-001: Migrar") == (
        "MIG-GEAS-001",
        "Migrar",
    )
    assert geas_backlog.split_title("sin prefijo") == ("", "sin prefijo")


def test_feature_id_cae_al_uuid_corto_si_no_hay_prefijo():
    ticket = {"id": "12345678-aaaa-bbbb-cccc-ddddeeeeffff", "title": "sin prefijo"}
    assert geas_backlog.feature_id(ticket) == "GEAS-12345678"


def test_status_of_mapea_los_estados_del_servidor():
    assert geas_backlog.status_of({"status": "FREE"}) == "pending"
    assert geas_backlog.status_of({"status": "IN_PROGRESS"}) == "in_progress"
    assert geas_backlog.status_of({"status": "REVIEW"}) == "in_progress"
    assert geas_backlog.status_of({"status": "DONE"}) == "done"
    assert geas_backlog.status_of({"status": "BLOCKED"}) == "blocked"
    assert geas_backlog.status_of({"status": "CANCELLED"}) == "blocked"


def test_to_feature_resuelve_dependencias_a_ids_de_feature():
    a = {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "title": "A-001: primera"}
    b = {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "title": "B-001: segunda",
        "status": "FREE",
        "description": "d\n\nCriterios de aceptación:\n  1. c1",
        "dependencies": [a["id"]],
    }
    feature = geas_backlog.to_feature(b, {a["id"]: a, b["id"]: b})
    assert feature["id"] == "B-001"
    assert feature["title"] == "segunda"
    assert feature["depends_on"] == ["A-001"]
    assert feature["acceptance_criteria"] == ["c1"]
    assert feature["ticket_id"] == b["id"]


def test_enabled_es_false_sin_config(tmp_path: Path):
    assert geas_backlog.enabled(tmp_path) is False


def test_enabled_es_true_con_backend_geas(tmp_path: Path):
    (tmp_path / "harness").mkdir()
    (tmp_path / "harness" / "geas.json").write_text(
        json.dumps({"backend": "geas", "enabled": True}), encoding="utf-8"
    )
    assert geas_backlog.enabled(tmp_path) is True


def test_config_con_comodin_ip_falla_claro(tmp_path: Path, monkeypatch):
    (tmp_path / "harness").mkdir()
    (tmp_path / "harness" / "geas.json").write_text(
        json.dumps({"backend": "geas", "url": "http://<IP>:8790"}), encoding="utf-8"
    )
    monkeypatch.setenv("GEAS_TOKEN", "token")
    monkeypatch.setenv("GEAS_CLIENT_CONFIG", str(tmp_path / "no-existe.env"))
    monkeypatch.delenv("GEAS_URL", raising=False)
    with pytest.raises(geas_backlog.GeasUnavailable, match="<IP>"):
        geas_backlog.load(tmp_path)


def test_config_sin_token_falla_claro(tmp_path: Path, monkeypatch):
    (tmp_path / "harness").mkdir()
    (tmp_path / "harness" / "geas.json").write_text(
        json.dumps({"backend": "geas", "url": "http://127.0.0.1:8790"}), encoding="utf-8"
    )
    monkeypatch.delenv("GEAS_TOKEN", raising=False)
    monkeypatch.delenv("GEAS_ACTOR", raising=False)
    monkeypatch.delenv("GEAS_ACTOR_ID", raising=False)
    monkeypatch.setenv("GEAS_CLIENT_CONFIG", str(tmp_path / "no-existe.env"))
    with pytest.raises(geas_backlog.GeasUnavailable, match="GEAS_TOKEN"):
        geas_backlog.load(tmp_path)


def test_write_mirror_conserva_metadatos_y_no_reescribe_si_igual(tmp_path: Path):
    (tmp_path / "harness").mkdir()
    (tmp_path / "harness" / "featureslist.json").write_text(
        json.dumps({"version": 7, "project": "NavaHack", "features": []}), encoding="utf-8"
    )
    features = [
        {
            "id": "A-001",
            "title": "A",
            "description": "d",
            "acceptance_criteria": ["c"],
            "status": "pending",
            "depends_on": [],
        }
    ]
    assert geas_backlog.write_mirror(tmp_path, features) is True
    doc = json.loads((tmp_path / "harness" / "featureslist.json").read_text())
    assert doc["version"] == 7
    assert doc["project"] == "NavaHack"
    assert doc["features"][0]["id"] == "A-001"
    assert geas_backlog.write_mirror(tmp_path, features) is False


def test_build_description_incluye_criterios_numerados():
    text = geas_backlog.build_description("haz algo", ["uno", "dos"])
    assert "haz algo" in text
    assert "Criterios de aceptación:" in text
    assert "  1. uno" in text
    assert "  2. dos" in text
