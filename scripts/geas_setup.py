#!/usr/bin/env python3
"""Deja el arnés de NavaHack apuntando a un GEAS y siembra el backlog.

Solo hay que pasar la IP/URL del servidor (y el token si no está ya en
``.env`` o en ``~/.config/geas/client.env``). El script:

  1. pregunta a GEAS la organización y el repositorio;
  2. escribe ``harness/geas.json`` y ``.geas.yml`` (sin secretos);
  3. importa ``harness/featureslist.json`` como tickets, respetando el orden
     topológico de ``depends_on``;
  4. cierra los tickets que ya estaban en ``done``;
  5. regenera el espejo local desde GEAS.

Uso:
    ./scripts/geas_setup.sh 192.168.1.50
    uv run python scripts/geas_setup.py --url http://192.168.1.50:8790 --token "$GEAS_TOKEN"
    uv run python scripts/geas_setup.py --url ... --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from agents.tools.geas_client import GeasClient, GeasError  # noqa: E402

FEATURES = REPO / "harness" / "featureslist.json"
CONFIG = REPO / "harness" / "geas.json"
MANIFEST = REPO / "harness" / "geas_map.json"
GEAS_YML = REPO / ".geas.yml"
DOTENV = REPO / ".env"
CLIENT_ENV = Path(
    os.environ.get("GEAS_CLIENT_CONFIG", Path.home() / ".config" / "geas" / "client.env")
)
CRITERIA_HEADER = "Criterios de aceptación:"
UUID_LEN = 36


def read_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return env
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        env[key.strip()] = value
    return env


def write_env(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    rendered: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in updates:
                if key not in seen:
                    rendered.append(f"{key}={updates[key]}")
                    seen.add(key)
                continue
        rendered.append(line)
    for key, value in updates.items():
        if key not in seen:
            rendered.append(f"{key}={value}")
            seen.add(key)
    path.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw.rstrip("/")
    if ":" in raw:
        return f"http://{raw}".rstrip("/")
    return f"http://{raw}:8790"


def topological(features: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    by_id = {f["id"]: f for f in features}
    pending = {f["id"]: [d for d in (f.get("depends_on") or []) if d in by_id] for f in features}
    warnings: list[str] = []
    for feature in features:
        for dep in feature.get("depends_on") or []:
            if dep not in by_id:
                warnings.append(f"{feature['id']} -> {dep} (no está en el backlog)")
    ordered: list[dict[str, Any]] = []
    done: set[str] = set()
    while len(ordered) < len(features):
        ready = [
            by_id[fid]
            for fid, deps in pending.items()
            if fid not in done and all(d in done for d in deps)
        ]
        if not ready:
            rest = [by_id[fid] for fid in pending if fid not in done]
            ordered.extend(rest)
            warnings.append(f"ciclo al ordenar: {len(rest)} features")
            break
        for feature in ready:
            ordered.append(feature)
            done.add(feature["id"])
    return ordered, warnings


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} no es JSON válido: {exc}") from exc


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def resource_map(
    client: GeasClient, repo_id: str, features: list[dict[str, Any]]
) -> dict[str, str]:
    try:
        resources = client.list_resources(repo_id)
    except GeasError:
        return {}
    by_path = {r["path"].rstrip("/"): r["id"] for r in resources if r.get("path")}
    declared = {p for f in features for p in (f.get("resources") or [])}
    mapping: dict[str, str] = {}
    for path in declared:
        norm = path.rstrip("/")
        ancestors = [p for p in by_path if norm == p or norm.startswith(p + "/")]
        if ancestors:
            mapping[path] = by_path[max(ancestors, key=len)]
    return mapping


def build_description(feature: dict[str, Any]) -> str:
    parts = [(feature.get("description") or "").strip()]
    criteria = feature.get("acceptance_criteria") or []
    if criteria:
        parts.append(
            CRITERIA_HEADER + "\n" + "\n".join(f"  {i}. {c}" for i, c in enumerate(criteria, 1))
        )
    if feature.get("blocked_reason"):
        parts.append(f"motivo de bloqueo en el arnés: {feature['blocked_reason']}")
    parts.append(f"[importada desde harness/featureslist.json: {feature['id']}]")
    return "\n\n".join(p for p in parts if p)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="IP, host:puerto o URL de GEAS")
    parser.add_argument("--token", default="", help="token del actor (no se imprime)")
    parser.add_argument("--actor", default="", help="nombre o UUID del actor")
    parser.add_argument("--org-id", default="", help="organización (si no, la deduce GEAS)")
    parser.add_argument("--repo", default="NavaHack", help="nombre del repositorio")
    parser.add_argument("--repo-id", default="", help="UUID del repositorio (opcional)")
    parser.add_argument("--no-import", action="store_true", help="solo configura, no importa")
    parser.add_argument("--dry-run", action="store_true", help="no escribe ni crea nada")
    args = parser.parse_args()

    url = normalize_url(args.url)
    env_file = read_env(DOTENV)
    client_env = read_env(CLIENT_ENV)
    token = (
        args.token
        or os.environ.get("GEAS_TOKEN")
        or env_file.get("GEAS_TOKEN", "")
        or client_env.get("GEAS_TOKEN", "")
    )
    actor = (
        args.actor
        or os.environ.get("GEAS_ACTOR")
        or env_file.get("GEAS_ACTOR", "")
        or client_env.get("GEAS_ACTOR", "")
    )
    if not token and not actor:
        raise SystemExit(
            "Falta GEAS_TOKEN. Pásalo con --token, ponlo en .env o en "
            f"{CLIENT_ENV}. No se escribe en harness/geas.json."
        )

    client = GeasClient(
        url,
        token=token,
        actor_id=actor if not token else "",
        org_id=args.org_id,
    )
    print(f"GEAS: {url}")
    try:
        org = client.get_organization(args.org_id)
    except GeasError as exc:
        raise SystemExit(f"No se pudo leer la organización: {exc}") from exc
    org_id = str(org.get("id") or args.org_id)
    if not org_id:
        raise SystemExit("GEAS no devolvió el id de la organización.")
    print(
        f"organización: {org.get('name', '?')} ({org_id[:8]}) · backend: {org.get('backend', '?')}"
    )

    try:
        repos = client.list_repositories(org_id)
    except GeasError as exc:
        raise SystemExit(f"No se pudieron listar los repositorios: {exc}") from exc
    repo = None
    if args.repo_id:
        repo = next((r for r in repos if r.get("id") == args.repo_id), None)
    if repo is None:
        repo = next((r for r in repos if r.get("name") == args.repo), None)
    if repo is None:
        visibles = (
            ", ".join(f"{r.get('name')}({str(r.get('id'))[:8]})" for r in repos) or "(ninguno)"
        )
        raise SystemExit(
            f"No encuentro el repositorio '{args.repo}' en la organización. "
            f"Visibles: {visibles}. Créalo en GEAS o pasa --repo-id."
        )
    print(f"repositorio: {repo.get('name')} ({str(repo.get('id'))[:8]})")

    cfg = load_json(CONFIG, {})
    cfg.update(
        {
            "backend": "geas",
            "enabled": True,
            "url": url,
            "org_id": org_id,
            "repository": repo.get("name", args.repo),
            "repository_id": repo.get("id", ""),
            "remote": cfg.get("remote", "origin"),
            "branch": cfg.get("branch", ""),
            "auto_commit": cfg.get("auto_commit", True),
            "push": cfg.get("push", True),
            "sync_after_claim": cfg.get("sync_after_claim", True),
        }
    )

    if args.dry_run:
        print("[dry-run] escribiría harness/geas.json, .geas.yml y .env")
        print("[dry-run] importaría el backlog si --no-import no está")
        return 0

    save_json(CONFIG, cfg)
    GEAS_YML.write_text(
        f"repository: {repo.get('name', args.repo)}\n"
        f"repository_id: {repo.get('id', '')}\n"
        f"organization_id: {org_id}\n",
        encoding="utf-8",
    )
    if token:
        write_env(DOTENV, {"GEAS_URL": url, "GEAS_TOKEN": token})
    else:
        write_env(DOTENV, {"GEAS_URL": url})
    print("configuración escrita: harness/geas.json · .geas.yml · .env")

    if args.no_import:
        return 0

    document = load_json(FEATURES, {})
    features = document.get("features") if isinstance(document, dict) else document
    if not isinstance(features, list):
        raise SystemExit(f"{FEATURES} no tiene una lista 'features'.")

    manifest = load_json(MANIFEST, {"features": {}})
    known: dict[str, str] = dict(manifest.get("features") or {})
    try:
        existing = {
            t["title"].split(":", 1)[0].strip(): t["id"] for t in client.list_tickets(org_id=org_id)
        }
    except GeasError:
        existing = {}
    for fid, tid in existing.items():
        known.setdefault(fid, tid)

    rmap = resource_map(client, repo["id"], features)
    ordered, topology_warnings = topological(features)
    for warning in topology_warnings:
        print(f"AVISO: {warning}")

    created = 0
    for feature in ordered:
        fid = feature["id"]
        if fid in known:
            continue
        deps: list[str] = []
        missing: list[str] = []
        for dep in feature.get("depends_on") or []:
            if dep in known:
                deps.append(known[dep])
            elif dep in existing:
                deps.append(existing[dep])
            else:
                missing.append(dep)
        if missing:
            print(f"SALTO {fid}: dependencias sin importar: {', '.join(missing)}")
            continue
        resources = sorted({rmap[p] for p in (feature.get("resources") or []) if p in rmap})
        if any(len(r) != UUID_LEN for r in resources):
            raise SystemExit(f"{fid} declara recursos que no son UUID: {resources}")
        try:
            ticket = client.create_ticket(
                title=f"{fid}: {feature['title']}",
                description=build_description(feature),
                repository_id=repo["id"],
                resources=resources,
                dependencies=deps,
                priority=0,
            )
        except GeasError as exc:
            print(f"ERR {fid}: {exc}")
            continue
        known[fid] = ticket["id"]
        manifest["features"] = dict(sorted(known.items()))
        save_json(MANIFEST, manifest)
        state = "FREE"
        if feature.get("status") == "done":
            try:
                client.complete_ticket(
                    ticket["id"],
                    result=f"importada desde featureslist.json ({fid}, done)",
                )
                state = "DONE"
            except GeasError as exc:
                state = f"FREE (no se pudo cerrar: {exc})"
        created += 1
        print(f"OK {str(ticket['id'])[:8]}  {fid:16} {state}")

    print(f"tickets creados: {created} · manifiesto: {MANIFEST.relative_to(REPO)}")

    from agents.agents import geas_backlog  # noqa: PLC0415 — tras escribir .env/geas.json

    try:
        changed = geas_backlog.write_mirror(REPO)
    except geas_backlog.GeasUnavailable as exc:
        print(f"AVISO: no se pudo regenerar el espejo local: {exc}")
    else:
        print("espejo local actualizado" if changed else "espejo local ya estaba al día")
    return 0


if __name__ == "__main__":
    sys.exit(main())
