"""Datos en vivo para la web (WEB-05): se publica el snapshot válido; si falta, se conserva el anterior."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_web_live import publish


def _snap(root: Path, name: str, data: object) -> None:
    (root / name).mkdir(parents=True)
    doc = {
        "fetched_at": "2026-11-14T17:00:00+00:00",
        "source_url": "u",
        "stale_after_s": 600,
        "data": data,
    }
    (root / name / "latest.json").write_text(json.dumps(doc), encoding="utf-8")


def test_publica_snapshot_valido_con_fetched_at(tmp_path: Path) -> None:
    _snap(tmp_path / "s", "parkings", [{"nombre": "Urzáiz"}])
    doc = publish("parkings", tmp_path / "s", tmp_path / "out")
    assert doc is not None and doc["fetched_at"].startswith("2026-11-14")
    out = json.loads((tmp_path / "out" / "parkings.json").read_text(encoding="utf-8"))
    assert out["data"] == [{"nombre": "Urzáiz"}] and out["stale_after_s"] == 600


def test_sin_snapshot_o_vacio_no_pisa_el_publicado(tmp_path: Path) -> None:
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "agenda.json").write_text('{"data": ["viejo"]}', encoding="utf-8")
    assert publish("agenda", tmp_path / "s", tmp_path / "out") is None
    _snap(tmp_path / "s", "agenda", [])
    assert publish("agenda", tmp_path / "s", tmp_path / "out") is None
    assert "viejo" in (tmp_path / "out" / "agenda.json").read_text(encoding="utf-8")
