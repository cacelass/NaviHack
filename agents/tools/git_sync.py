"""Sincronización git antes de reclamar un ticket de GEAS.

Una hackathon con 3-4 personas sobre un servidor de tickets compartido no
sirve de nada si el checkout local lleva tres commits de retraso: reclamas un
ticket que ya está resuelto o pisas el trabajo de otra persona. Este módulo
deja el árbol en un estado conocido antes de ``start_ticket``:

  1. comprueba que hay repo, remoto y rama;
  2. si hay cambios, hace un commit WIP (salvo que ``auto_commit`` sea False);
  3. ``fetch`` + ``pull --rebase``;
  4. ``push``.

Nunca resuelve conflictos a ciegas: si el rebase se para, lo aborta y devuelve
un fallo con lo que hay que hacer. Tampoco commitea secretos: si ve un
``.env`` o una clave en el índice, se niega.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

FORBIDDEN_NAMES = (".env", "id_rsa", "id_ed25519")
FORBIDDEN_SUFFIXES = (".pem", ".key", ".p12", ".pfx")


class GitSyncError(RuntimeError):
    """No se pudo dejar el árbol listo para reclamar."""


@dataclass
class SyncResult:
    ok: bool
    message: str
    branch: str = ""
    head: str = ""
    committed: bool = False
    pulled: bool = False
    pushed: bool = False
    dirty: bool = False
    warnings: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)


def _run(
    root: Path, *args: str, check: bool = False, timeout: int = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
    )


def _git(root: Path, *args: str) -> str:
    proc = _run(root, *args)
    if proc.returncode != 0:
        raise GitSyncError((proc.stderr or proc.stdout or f"git {' '.join(args)}").strip())
    return proc.stdout.strip()


def current_head(root: Path) -> str:
    try:
        return _git(root, "rev-parse", "HEAD")
    except GitSyncError:
        return ""


def _branch(root: Path, branch: str) -> str:
    if branch:
        return branch
    name = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if not name or name == "HEAD":
        raise GitSyncError("Estás en detached HEAD: cambia a una rama antes de reclamar un ticket.")
    return name


def _status(root: Path) -> list[str]:
    raw = _git(root, "status", "--porcelain")
    return [line for line in raw.splitlines() if line.strip()]


def is_dirty(root: Path) -> bool:
    """¿Hay cambios sin commitear? (False si no es un repo git)."""
    try:
        return bool(_status(root))
    except GitSyncError:
        return False


def _path_of(status_line: str) -> str:
    # Formato porcelain: "XY path" (o "XY old -> new" en renombrados).
    path = status_line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip('"')


def _forbidden(root: Path, lines: list[str]) -> list[str]:
    bad: list[str] = []
    for line in lines:
        path = _path_of(line)
        name = Path(path).name
        if name == ".env.example":
            continue
        if (
            name in FORBIDDEN_NAMES
            or name.startswith(".env.")
            or name.endswith(FORBIDDEN_SUFFIXES)
            or any(part == "secrets" for part in Path(path).parts)
        ):
            bad.append(path)
    return bad


def _commit_wip(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    proc = _run(root, "commit", "-m", message)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        if "Please tell me who you are" in detail or "user.email" in detail:
            raise GitSyncError(
                "git no tiene user.name/user.email configurados y el commit WIP "
                "no se puede crear. Configúralos y reintenta."
            )
        raise GitSyncError(f"git commit falló: {detail}")


def sync_before_claim(
    root: Path,
    *,
    ticket: str = "",
    remote: str = "origin",
    branch: str = "",
    auto_commit: bool = True,
    push: bool = True,
    timeout: int = 120,
) -> SyncResult:
    """Deja el repo listo para ``start_ticket`` y devuelve el SHA resultante."""
    root = root.resolve()
    if not (root / ".git").exists():
        return SyncResult(
            ok=False,
            message=f"{root} no es un repositorio git.",
            needs=["Ejecuta `git init` y añade un remoto (`git remote add origin ...`)."],
        )

    try:
        branch = _branch(root, branch)
    except GitSyncError as exc:
        return SyncResult(ok=False, message=str(exc), needs=["Cambia a una rama de trabajo."])

    if _run(root, "remote", "get-url", remote).returncode != 0:
        return SyncResult(
            ok=False,
            message=f"No existe el remoto '{remote}'.",
            branch=branch,
            needs=[f"Configura el remoto: `git remote add {remote} <url>`."],
        )

    dirty = False
    committed = False
    try:
        lines = _status(root)
        dirty = bool(lines)
        if dirty:
            forbidden = _forbidden(root, lines)
            if forbidden:
                return SyncResult(
                    ok=False,
                    message="Hay secretos sin ignorar en el árbol: " + ", ".join(forbidden),
                    branch=branch,
                    dirty=True,
                    needs=[
                        "Añádelos a .gitignore y sácalos del índice "
                        "(`git rm --cached <fichero>`) antes de reclamar."
                    ],
                )
            if not auto_commit:
                return SyncResult(
                    ok=False,
                    message="El árbol tiene cambios y auto_commit está desactivado.",
                    branch=branch,
                    dirty=True,
                    needs=["Haz commit o activa auto_commit en harness/geas.json."],
                )
            stamp = ticket or "ticket"
            _commit_wip(
                root,
                f"wip(harness): checkpoint antes de reclamar {stamp}",
            )
            committed = True
            dirty = False

        head_before = current_head(root)
        pulled = False
        _git(root, "fetch", remote, "--prune")

        remote_ref = f"refs/remotes/{remote}/{branch}"
        has_remote = _run(root, "rev-parse", "--verify", "--quiet", remote_ref).returncode == 0

        if has_remote:
            if not head_before:
                return SyncResult(
                    ok=False,
                    message="El repo local no tiene commits pero el remoto sí.",
                    branch=branch,
                    committed=committed,
                    needs=[
                        "Clona el repositorio en vez de hacer `git init`, o haz un "
                        "commit inicial antes de reclamar."
                    ],
                )
            pull = _run(root, "pull", "--rebase", remote, branch)
            if pull.returncode != 0:
                _run(root, "rebase", "--abort")
                return SyncResult(
                    ok=False,
                    message="El pull --rebase falló (posible conflicto).",
                    branch=branch,
                    committed=committed,
                    pulled=False,
                    needs=[
                        "Resuelve el conflicto a mano, haz commit del resultado y "
                        "vuelve a lanzar `harness start`."
                    ],
                    warnings=[(pull.stderr or pull.stdout).strip()[-800:]],
                )
            pulled = current_head(root) != head_before
        if push:
            if has_remote:
                push_args = ("push", remote, f"HEAD:{branch}")
            else:
                push_args = ("push", "-u", remote, branch)
            push_proc = _run(root, *push_args)
            if push_proc.returncode != 0:
                return SyncResult(
                    ok=False,
                    message="El push al remoto falló después del pull.",
                    branch=branch,
                    head=current_head(root),
                    committed=committed,
                    pulled=pulled,
                    needs=[
                        "Revisa el estado del remoto; si alguien acaba de pushear, "
                        "vuelve a lanzar `harness start` para rebasar otra vez."
                    ],
                    warnings=[(push_proc.stderr or push_proc.stdout).strip()[-800:]],
                )
            pushed = True

        return SyncResult(
            ok=True,
            message=(
                f"git sincronizado en {branch} ({current_head(root)[:8]})"
                + (" · commit WIP" if committed else "")
                + (" · pull" if pulled else "")
                + (" · push" if pushed else "")
            ),
            branch=branch,
            head=current_head(root),
            committed=committed,
            pulled=pulled,
            pushed=pushed,
        )
    except GitSyncError as exc:
        return SyncResult(ok=False, message=str(exc), branch=branch, needs=["Revisa `git status`."])
