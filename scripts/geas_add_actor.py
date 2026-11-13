#!/usr/bin/env python3
"""Da de alta un actor (persona o agente) en un GEAS y le emite un token.

La API de GEAS **lista** actores (`list_actors`) pero no los crea: hay que
escribir en su base de datos, y el servidor SQLite es de un solo escritor. Este
script hace el ciclo completo en el host del servidor:

  1. resuelve la organización y el rol (lectura de la BD, sin abrir el server);
  2. para el servidor de GEAS (si hace falta);
  3. crea el actor con `geas user/agent create`;
  4. lo vuelve a levantar (pase lo que pase, con try/finally);
  5. emite un token y lo añade a `tokens.env` en el formato que lee el proxy;
  6. reinicia el proxy para que lo cargue;
  7. verifica con `list_actors` (si le pasas --url).

Uso:
    uv run python scripts/geas_add_actor.py --name "Ana" --kind user --role manager
    uv run python scripts/geas_add_actor.py --name "Raspy" --kind agent \\
        --provider local --model qwen3-coder --role agent --url http://192.168.1.50:8790
    uv run python scripts/geas_add_actor.py --name "Ana" --kind user --dry-run

Nunca imprime tokens ya existentes; el nuevo token sale por stdout una sola vez
para que se lo pases a la persona. No escribe secretos en el repo.
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_DATA_DIR = Path(os.environ.get("GEAS_DATA_DIR", Path.home() / ".local" / "share" / "geas"))
DEFAULT_DB = Path(os.environ.get("GEAS_DB", DEFAULT_DATA_DIR / "geas.db"))
DEFAULT_TOKENS = Path(os.environ.get("GEAS_TOKENS", DEFAULT_DATA_DIR / "tokens.env"))
SERVER_UNIT = os.environ.get("GEAS_SERVER_UNIT", "geas-server")
PROXY_UNIT = os.environ.get("GEAS_PROXY_UNIT", "geas-proxy")
ROLE_POR_DEFECTO = {"agent": "agent", "user": "manager"}


# ── helpers puros (testables sin servidor) ──────────────────────────────


def token_key(name: str) -> str:
    """`Ana Pérez` → `ANA_PEREZ`, la clave de `GEAS_TOKEN_<clave>`.

    Solo ASCII: la clave acaba en una variable de entorno, y un acento ahí es
    una variable distinta que nadie va a poder exportar.
    """
    plano = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    limpio = "".join(c if c.isalnum() else "_" for c in plano.upper())
    return limpio.strip("_") or "ACTOR"


def token_block(name: str, actor_id: str, token: str) -> str:
    """Las dos líneas que el proxy necesita para mapear token→actor.

    El proxy lee la clave, guarda el valor como "último token" y lo asigna al
    comentario que venga después. Si el comentario no es el UUID, el actor que
    llega a GEAS no existe y todo responde FORBIDDEN.
    """
    return f"GEAS_TOKEN_{token_key(name)}={token}\n# {name} = {actor_id}\n"


def gen_token() -> str:
    return secrets.token_urlsafe(32)


def _connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def resolve_org(db: Path, org_id: str = "", org_name: str = "") -> str:
    with _connect(db) as conn:
        filas = conn.execute("SELECT id, name FROM organizations WHERE active = 1").fetchall()
    if org_id:
        for rid, _ in filas:
            if rid == org_id:
                return rid
        raise SystemExit(f"La organización {org_id!r} no existe o está inactiva.")
    if org_name:
        coincide = [rid for rid, nombre in filas if nombre == org_name]
        if len(coincide) == 1:
            return coincide[0]
        if not coincide:
            raise SystemExit(f"No hay ninguna organización llamada {org_name!r}.")
        raise SystemExit(f"Hay varias organizaciones llamadas {org_name!r}: pasa --org-id.")
    if len(filas) == 1:
        return filas[0][0]
    visibles = ", ".join(f"{nombre}({rid[:8]})" for rid, nombre in filas) or "(ninguna)"
    raise SystemExit(f"Hay {len(filas)} organizaciones; pasa --org-id o --org-name. {visibles}")


def resolve_role(db: Path, org_id: str, role_name: str) -> str:
    with _connect(db) as conn:
        filas = conn.execute(
            "SELECT id, name FROM roles WHERE organization_id = ?", (org_id,)
        ).fetchall()
    for rid, nombre in filas:
        if nombre == role_name:
            return rid
    visibles = ", ".join(nombre for _, nombre in filas) or "(ninguno)"
    raise SystemExit(f"No existe el rol {role_name!r} en la organización. Roles: {visibles}.")


_CONSULTA_ACTOR = {
    "agent": "SELECT id FROM agents WHERE organization_id = ? AND name = ?",
    "user": "SELECT id FROM users WHERE organization_id = ? AND name = ?",
}


def resolve_actor(db: Path, kind: str, name: str, org_id: str) -> str:
    with _connect(db) as conn:
        fila = conn.execute(_CONSULTA_ACTOR[kind], (org_id, name)).fetchone()
    return fila[0] if fila else ""


def append_token(tokens_path: Path, name: str, actor_id: str, token: str) -> None:
    """Añade el bloque del token sin pisar los que ya hay. Crea el fichero 0600."""
    clave = f"GEAS_TOKEN_{token_key(name)}="
    existente = tokens_path.read_text(encoding="utf-8") if tokens_path.is_file() else ""
    if any(line.startswith(clave) for line in existente.splitlines()):
        raise SystemExit(
            f"{tokens_path} ya tiene {clave!r}. No se sobrescribe un token: "
            "bórralo a mano si de verdad quieres reemitirlo."
        )
    bloque = token_block(name, actor_id, token)
    texto = existente
    if texto and not texto.endswith("\n"):
        texto += "\n"
    texto += bloque
    tokens_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(tokens_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as fh:
        fh.write(texto)


# ── acciones sobre el host ──────────────────────────────────────────────


def _systemctl(accion: str, unidad: str) -> bool:
    if not shutil.which("systemctl"):
        return False
    return (
        subprocess.run(
            ["systemctl", "--user", accion, unidad],
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def _geas_bin() -> str:
    ruta = os.environ.get("GEAS_BIN") or shutil.which("geas")
    if not ruta:
        raise SystemExit("No encuentro el binario `geas`. Instálalo o pásalo en GEAS_BIN.")
    return ruta


def _crear_actor(binario: str, db: Path, args, org_id: str, role_id: str) -> None:
    env = {**os.environ, "GEAS_DB": str(db)}
    if args.kind == "agent":
        cmd = [
            binario,
            "agent",
            "create",
            org_id,
            args.name,
            args.provider,
            args.model,
            "",
            role_id,
        ]
    else:
        cmd = [binario, "user", "create", org_id, args.name, args.email, "", role_id]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise SystemExit("No se pudo crear el actor:\n" + (proc.stdout or "") + (proc.stderr or ""))
    print("   " + (proc.stdout or "").strip())


def verificar(url: str, token: str) -> None:
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/tools/list_actors",
        data=b"{}",
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            import json

            data = json.loads(resp.read() or b"{}")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
        print(f"   AVISO: no pude verificar con list_actors: {exc}")
        return
    actores = (data.get("data") or {}).get("actors") or []
    print(f"   GEAS ve {len(actores)} actor(es) en la organización.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--name", required=True, help="nombre visible del actor")
    parser.add_argument("--kind", choices=("agent", "user"), default="agent")
    parser.add_argument("--role", default="", help="rol de GEAS (por defecto: agent|manager)")
    parser.add_argument("--provider", default="local", help="solo agent")
    parser.add_argument("--model", default="", help="solo agent")
    parser.add_argument("--email", default="", help="solo user")
    parser.add_argument("--org-id", default="")
    parser.add_argument("--org-name", default="")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--tokens-file", type=Path, default=DEFAULT_TOKENS)
    parser.add_argument("--no-token", action="store_true", help="crea el actor sin emitir token")
    parser.add_argument("--no-proxy", action="store_true", help="no reinicia el proxy")
    parser.add_argument("--no-systemd", action="store_true", help="no para/levanta el servidor")
    parser.add_argument("--url", default="", help="URL del proxy, para verificar al final")
    parser.add_argument("--dry-run", action="store_true", help="enseña el plan y sale")
    args = parser.parse_args(argv)

    if not args.db.is_file():
        raise SystemExit(f"No encuentro la base de datos de GEAS en {args.db}.")
    role_name = args.role or ROLE_POR_DEFECTO[args.kind]

    org_id = resolve_org(args.db, args.org_id, args.org_name)
    role_id = resolve_role(args.db, org_id, role_name)
    if resolve_actor(args.db, args.kind, args.name, org_id):
        raise SystemExit(f"El {args.kind} {args.name!r} ya existe en esa organización.")

    print(f"GEAS: {args.db}")
    print(f"organización: {org_id[:8]} · rol: {role_name} ({role_id[:8]})")
    print(f"actor: {args.kind} {args.name!r}")
    if args.no_token:
        print("token: no (--no-token)")
    else:
        print(f"token: se añadirá a {args.tokens_file} y se reiniciará {PROXY_UNIT}")

    if args.dry_run:
        print("[dry-run] no se para el servidor, ni se crea el actor, ni se escribe nada.")
        return 0

    binario = _geas_bin()
    parado = False
    if not args.no_systemd:
        parado = _systemctl("stop", SERVER_UNIT)
        print("   servidor parado" if parado else "   AVISO: no pude parar el servidor (¿systemd?)")
    try:
        _crear_actor(binario, args.db, args, org_id, role_id)
    finally:
        if not args.no_systemd and parado:
            _systemctl("start", SERVER_UNIT)

    actor_id = resolve_actor(args.db, args.kind, args.name, org_id)
    if not actor_id:
        raise SystemExit("El actor se creó pero no encuentro su UUID en la BD.")
    print(f"actor creado: {actor_id}")

    if args.no_token:
        return 0

    token = gen_token()
    append_token(args.tokens_file, args.name, actor_id, token)
    print(f"token escrito en {args.tokens_file} (permisos 600)")
    if not args.no_proxy:
        reiniciado = _systemctl("restart", PROXY_UNIT)
        print("   proxy reiniciado" if reiniciado else "   AVISO: reinicia el proxy a mano")

    if args.url:
        verificar(args.url, token)

    print("\nPásale esto al actor (no lo commitees):")
    print(f"  GEAS_URL={args.url or 'http://<IP>:8790'}")
    print(f"  GEAS_TOKEN={token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
