"""Tests de los helpers puros de scripts/geas_add_actor.py (sin servidor)."""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def _cargar():
    spec = importlib.util.spec_from_file_location(
        "geas_add_actor", RAIZ / "scripts" / "geas_add_actor.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


add = _cargar()


def _db(tmp_path: Path) -> Path:
    db = tmp_path / "geas.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE organizations (id TEXT PRIMARY KEY, name TEXT, active INTEGER DEFAULT 1);
        CREATE TABLE roles (id TEXT PRIMARY KEY, organization_id TEXT, name TEXT);
        CREATE TABLE users (id TEXT PRIMARY KEY, organization_id TEXT, name TEXT);
        CREATE TABLE agents (id TEXT PRIMARY KEY, organization_id TEXT, name TEXT);
        INSERT INTO organizations VALUES ('org-1', 'NavaHack', 1);
        INSERT INTO roles VALUES ('role-agent', 'org-1', 'agent');
        INSERT INTO roles VALUES ('role-manager', 'org-1', 'manager');
        """
    )
    conn.commit()
    conn.close()
    return db


def test_token_key_normaliza():
    assert add.token_key("Ana Pérez") == "ANA_PEREZ"
    assert add.token_key("  raspy-01 ") == "RASPY_01"
    assert add.token_key("!!!") == "ACTOR"


def test_token_block_es_dos_lineas_con_uuid():
    bloque = add.token_block("Raspy", "uuid-123", "secreto")
    assert bloque == "GEAS_TOKEN_RASPY=secreto\n# Raspy = uuid-123\n"


def test_resolve_org_unica(tmp_path: Path):
    assert add.resolve_org(_db(tmp_path)) == "org-1"


def test_resolve_org_por_nombre(tmp_path: Path):
    assert add.resolve_org(_db(tmp_path), org_name="NavaHack") == "org-1"


def test_resolve_org_desconocida(tmp_path: Path):
    with pytest.raises(SystemExit, match="no existe"):
        add.resolve_org(_db(tmp_path), org_id="nope")


def test_resolve_role(tmp_path: Path):
    assert add.resolve_role(_db(tmp_path), "org-1", "agent") == "role-agent"


def test_resolve_role_desconocido_lista_los_que_hay(tmp_path: Path):
    with pytest.raises(SystemExit, match="agent, manager"):
        add.resolve_role(_db(tmp_path), "org-1", "admin")


def test_resolve_actor_vacio_si_no_existe(tmp_path: Path):
    assert add.resolve_actor(_db(tmp_path), "agent", "Raspy", "org-1") == ""


def test_append_token_crea_fichero_0600(tmp_path: Path):
    tokens = tmp_path / "tokens.env"
    add.append_token(tokens, "Raspy", "uuid-1", "tok")
    assert tokens.read_text() == "GEAS_TOKEN_RASPY=tok\n# Raspy = uuid-1\n"
    assert (tokens.stat().st_mode & 0o777) == 0o600


def test_append_token_no_sobrescribe(tmp_path: Path):
    tokens = tmp_path / "tokens.env"
    tokens.write_text("GEAS_TOKEN_RASPY=viejo\n# Raspy = uuid-viejo\n")
    with pytest.raises(SystemExit, match="ya tiene"):
        add.append_token(tokens, "Raspy", "uuid-2", "nuevo")


def test_append_token_respeta_los_anteriores(tmp_path: Path):
    tokens = tmp_path / "tokens.env"
    tokens.write_text("GEAS_TOKEN_RASPY=uno\n# Raspy = uuid-1\n")
    add.append_token(tokens, "Ana", "uuid-2", "dos")
    texto = tokens.read_text()
    assert "GEAS_TOKEN_RASPY=uno" in texto
    assert "GEAS_TOKEN_ANA=dos\n# Ana = uuid-2" in texto
