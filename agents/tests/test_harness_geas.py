"""Tests del modo GEAS del arnés, sin tocar la red ni un servidor real."""

from __future__ import annotations

import json

from agents.agents import geas_backlog
from agents.agents.harness_agent import HarnessAgent
from agents.core.base_agent import AgentResult
from agents.tools import git_sync


def _feature(**kw):
    base = {
        "id": "A-001",
        "title": "Primera",
        "description": "d",
        "acceptance_criteria": ["c1"],
        "status": "pending",
        "depends_on": [],
        "ticket_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "raw_status": "FREE",
    }
    base.update(kw)
    return base


def _contexto_geas(context):
    (context.root / "harness").mkdir(exist_ok=True)
    (context.root / "harness" / "featureslist.json").write_text(
        json.dumps({"version": 1, "project": "NavaHack", "features": []}),
        encoding="utf-8",
    )
    (context.root / "harness" / "progress").mkdir(exist_ok=True)
    (context.root / "harness" / "geas.json").write_text(
        json.dumps(
            {
                "backend": "geas",
                "enabled": True,
                "url": "http://127.0.0.1:8790",
                "auto_commit": True,
                "sync_after_claim": True,
            }
        ),
        encoding="utf-8",
    )
    return context


def test_status_geas_usa_el_servidor_y_no_el_espejo(context, monkeypatch):
    _contexto_geas(context)
    feats = [_feature(), _feature(id="B-001", title="Segunda", status="done", raw_status="DONE")]
    monkeypatch.setattr(geas_backlog, "features", lambda root: feats)
    monkeypatch.setattr(geas_backlog, "write_mirror", lambda root, features=None: True)
    monkeypatch.setattr(geas_backlog, "available", lambda root: [{"id": feats[0]["ticket_id"]}])
    monkeypatch.setattr(geas_backlog, "feature_id", lambda ticket: "A-001")

    result = HarnessAgent(context=context).status()
    assert result.success
    assert result.data["backend"] == "geas"
    assert result.data["counts"]["pending"] == 1
    assert result.data["counts"]["done"] == 1
    assert result.data["eligible"] == ["A-001"]


def test_status_geas_falla_cerrado_si_el_servidor_no_responde(context, monkeypatch):
    _contexto_geas(context)
    monkeypatch.setattr(
        geas_backlog,
        "features",
        lambda root: (_ for _ in ()).throw(geas_backlog.GeasUnavailable("sin red")),
    )
    result = HarnessAgent(context=context).status()
    assert not result.success
    assert "GEAS no disponible" in result.message
    assert result.needs


def test_start_geas_sincroniza_git_antes_de_reclamar(context, monkeypatch):
    _contexto_geas(context)
    eventos: list[str] = []
    feat = _feature()

    monkeypatch.setattr(geas_backlog, "find", lambda root, identifier: feat)
    monkeypatch.setattr(geas_backlog, "features", lambda root: [feat])
    monkeypatch.setattr(geas_backlog, "write_mirror", lambda root, features=None: True)

    def fake_sync(root, **kwargs):
        eventos.append("sync")
        return git_sync.SyncResult(ok=True, message="sync ok", branch="main", head="abc123")

    def fake_start(root, identifier, commit_before=""):
        eventos.append("claim")
        assert commit_before == "abc123"
        return {"ticket_id": feat["ticket_id"], "status": "IN_PROGRESS"}

    monkeypatch.setattr(git_sync, "sync_before_claim", fake_sync)
    monkeypatch.setattr(geas_backlog, "start", fake_start)

    result = HarnessAgent(context=context).start(id="A-001")
    assert result.success
    assert eventos[0] == "sync"
    assert eventos[1] == "claim"
    assert result.data["commit_before"] == "abc123"
    current = (context.root / "harness" / "progress" / "current.md").read_text()
    assert "A-001" in current
    assert "c1" in current


def test_start_geas_no_reclama_si_git_falla(context, monkeypatch):
    _contexto_geas(context)
    feat = _feature()
    monkeypatch.setattr(geas_backlog, "find", lambda root, identifier: feat)
    monkeypatch.setattr(geas_backlog, "features", lambda root: [feat])
    monkeypatch.setattr(
        git_sync,
        "sync_before_claim",
        lambda root, **kwargs: git_sync.SyncResult(
            ok=False, message="conflicto", needs=["resuelve"]
        ),
    )
    llamado = {"claim": False}

    def fake_start(root, identifier, commit_before=""):
        llamado["claim"] = True
        return {}

    monkeypatch.setattr(geas_backlog, "start", fake_start)

    result = HarnessAgent(context=context).start(id="A-001")
    assert not result.success
    assert result.needs == ["resuelve"]
    assert llamado["claim"] is False


def test_start_geas_rechaza_ticket_no_free(context, monkeypatch):
    _contexto_geas(context)
    feat = _feature(raw_status="IN_PROGRESS")
    monkeypatch.setattr(geas_backlog, "find", lambda root, identifier: feat)
    result = HarnessAgent(context=context).start(id="A-001")
    assert not result.success
    assert "FREE" in result.message


def test_finish_geas_exige_puerta_y_evidencia(context, monkeypatch):
    _contexto_geas(context)
    feat = _feature(status="in_progress", raw_status="IN_PROGRESS")
    monkeypatch.setattr(geas_backlog, "find", lambda root, identifier: feat)
    monkeypatch.setattr(
        HarnessAgent,
        "gate",
        lambda self: AgentResult(
            success=False,
            agent="harness",
            action="gate",
            message="rojo",
            data={"checks": []},
        ),
    )
    result = HarnessAgent(context=context).finish(id="A-001", evidence="ok")
    assert not result.success
    assert "no se cierra" in result.message.lower()


def test_finish_geas_cierra_con_commit_after(context, monkeypatch):
    _contexto_geas(context)
    feat = _feature(status="in_progress", raw_status="IN_PROGRESS")
    llamado = {}
    monkeypatch.setattr(geas_backlog, "find", lambda root, identifier: feat)
    monkeypatch.setattr(geas_backlog, "write_mirror", lambda root, features=None: True)
    monkeypatch.setattr(git_sync, "current_head", lambda root: "deadbeef")
    monkeypatch.setattr(git_sync, "is_dirty", lambda root: False)
    monkeypatch.setattr(
        HarnessAgent,
        "gate",
        lambda self: AgentResult(
            success=True,
            agent="harness",
            action="gate",
            message="verde",
            data={"checks": [{"check": "pytest", "detail": "3 passed"}]},
        ),
    )

    def fake_complete(root, identifier, commit_after="", result_text="OK"):
        llamado["commit_after"] = commit_after
        return {"ticket_id": feat["ticket_id"]}

    monkeypatch.setattr(geas_backlog, "complete", fake_complete)

    result = HarnessAgent(context=context).finish(id="A-001", evidence="3 passed")
    assert result.success
    assert llamado["commit_after"] == "deadbeef"
    history = (context.root / "harness" / "progress" / "history.md").read_text()
    assert "A-001" in history
    assert "3 passed" in history


def test_add_geas_crea_ticket_y_refresca_espejo(context, monkeypatch):
    _contexto_geas(context)
    monkeypatch.setattr(geas_backlog, "find", lambda root, identifier: None)
    monkeypatch.setattr(geas_backlog, "write_mirror", lambda root, features=None: True)
    creado = {}

    def fake_create(root, **kwargs):
        creado.update(kwargs)
        return {"id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "feature_id": kwargs["feature_id"]}

    monkeypatch.setattr(geas_backlog, "create_feature", fake_create)

    result = HarnessAgent(context=context).add(id="C-001", title="Tercera", criteria="uno;dos")
    assert result.success
    assert creado["feature_id"] == "C-001"
    assert creado["criteria"] == ["uno", "dos"]
    assert creado["title"] == "Tercera"
