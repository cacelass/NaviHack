"""Tests de la sincronización git previa al claim (sin red, todo local)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agents.tools import git_sync


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    remote.mkdir()
    subprocess.run(["git", "init", "--bare", "-q"], cwd=remote, check=True)

    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    _git(root, "remote", "add", "origin", str(remote))
    (root / "README.md").write_text("# hola\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "chore: inicial")
    _git(root, "branch", "-M", "main")
    _git(root, "push", "-u", "origin", "main")
    return root, remote


def test_sync_limpio_pushea_y_devuelve_head(tmp_path: Path):
    root, _ = _repo(tmp_path)
    result = git_sync.sync_before_claim(root, ticket="A-001")
    assert result.ok
    assert result.branch == "main"
    assert result.head == git_sync.current_head(root)
    assert result.pushed
    assert not result.committed


def test_sync_hace_commit_wip_si_hay_cambios(tmp_path: Path):
    root, _ = _repo(tmp_path)
    (root / "nuevo.txt").write_text("trabajo\n")
    assert git_sync.is_dirty(root)
    result = git_sync.sync_before_claim(root, ticket="A-001")
    assert result.ok
    assert result.committed
    assert not git_sync.is_dirty(root)
    log = _git(root, "log", "-1", "--pretty=%s")
    assert "A-001" in log


def test_sync_sin_auto_commit_falla_con_needs(tmp_path: Path):
    root, _ = _repo(tmp_path)
    (root / "nuevo.txt").write_text("trabajo\n")
    result = git_sync.sync_before_claim(root, auto_commit=False)
    assert not result.ok
    assert result.needs
    assert git_sync.is_dirty(root)


def test_sync_se_niega_a_commitear_env(tmp_path: Path):
    root, _ = _repo(tmp_path)
    (root / ".env").write_text("GEAS_TOKEN=secreto\n")
    result = git_sync.sync_before_claim(root)
    assert not result.ok
    assert ".env" in result.message
    assert git_sync.is_dirty(root)


def test_sync_excluye_env_example(tmp_path: Path):
    root, _ = _repo(tmp_path)
    (root / ".env.example").write_text("GEAS_TOKEN=\n")
    result = git_sync.sync_before_claim(root)
    assert result.ok
    assert result.committed


def test_sync_sin_remoto_falla(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("# hola\n")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "inicial")
    result = git_sync.sync_before_claim(root)
    assert not result.ok
    assert "remoto" in result.message.lower()
    assert result.needs


def test_sync_fuera_de_git_falla(tmp_path: Path):
    result = git_sync.sync_before_claim(tmp_path)
    assert not result.ok
    assert "repositorio git" in result.message


def test_sync_sube_una_rama_nueva(tmp_path: Path):
    root, _ = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "feature")
    result = git_sync.sync_before_claim(root, branch="feature")
    assert result.ok
    assert result.pushed


@pytest.mark.parametrize(
    "linea,path",
    [
        ("?? .env", ".env"),
        ("?? .env.local", ".env.local"),
        ("?? cert.pem", "cert.pem"),
        ("?? private.key", "private.key"),
        ("?? secrets/db.txt", "secrets/db.txt"),
    ],
)
def test_guard_detecta_ficheros_sensibles(tmp_path: Path, linea: str, path: str):
    assert git_sync._forbidden(tmp_path, [linea]) == [path]


def test_guard_permite_env_example(tmp_path: Path):
    assert git_sync._forbidden(tmp_path, ["?? .env.example"]) == []


def _otro_clon(tmp_path: Path, remote: Path) -> Path:
    other = tmp_path / "otro"
    subprocess.run(["git", "clone", "-q", "-b", "main", str(remote), str(other)], check=True)
    _git(other, "config", "user.email", "otro@example.com")
    _git(other, "config", "user.name", "Otro")
    return other


def _con_espejo(tmp_path: Path) -> tuple[Path, Path]:
    root, remote = _repo(tmp_path)
    mirror = root / "harness" / "featureslist.json"
    mirror.parent.mkdir()
    mirror.write_text('{"features": [{"id": "A", "status": "pending"}]}\n')
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "espejo")
    _git(root, "push", "-q", "origin", "main")
    return root, remote


def test_conflicto_solo_en_el_espejo_se_resuelve_con_la_version_del_remoto(tmp_path: Path):
    root, remote = _con_espejo(tmp_path)
    other = _otro_clon(tmp_path, remote)
    (other / "harness" / "featureslist.json").write_text(
        '{"features": [{"id": "A", "status": "done"}]}\n'
    )
    _git(other, "commit", "-qam", "otro cierra A")
    _git(other, "push", "-q", "origin", "main")

    (root / "harness" / "featureslist.json").write_text(
        '{"features": [{"id": "A", "status": "in_progress"}]}\n'
    )
    result = git_sync.sync_before_claim(root, ticket="B-001")

    assert result.ok, result.message
    text = (root / "harness" / "featureslist.json").read_text()
    assert "<<<<<<<" not in text and '"done"' in text
    assert _git(root, "status", "--porcelain") == ""


def test_conflicto_en_codigo_aborta_sin_marcadores(tmp_path: Path):
    root, remote = _repo(tmp_path)
    other = _otro_clon(tmp_path, remote)
    (other / "README.md").write_text("# del otro\n")
    _git(other, "commit", "-qam", "otro")
    _git(other, "push", "-q", "origin", "main")

    (root / "README.md").write_text("# mío\n")
    result = git_sync.sync_before_claim(root, ticket="B-001")

    assert not result.ok and "código" in result.needs[0]
    assert "<<<<<<<" not in (root / "README.md").read_text()


def test_no_commitea_marcadores_de_conflicto(tmp_path: Path):
    root, _ = _repo(tmp_path)
    (root / "roto.json").write_text("<<<<<<< HEAD\n{}\n=======\n[]\n>>>>>>> abc (x)\n")
    with pytest.raises(git_sync.GitSyncError, match="roto.json"):
        git_sync._commit_wip(root, "wip")
    assert _git(root, "log", "-1", "--pretty=%s") == "chore: inicial"
