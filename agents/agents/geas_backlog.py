"""Backlog del arnés respaldado por GEAS (MongoDB) con espejo local.

GEAS es la fuente de verdad: el ticket es el que se reclama de forma atómica y
el que impide que dos personas de la hackathon trabajen lo mismo. El fichero
``harness/featureslist.json`` sigue existiendo como **espejo de solo lectura**
para ``init.sh``, el RAG y cualquiera que abra el repo sin red.

Dos reglas:

  - **Fail-closed.** Si GEAS no responde, el arnés no inventa trabajo local:
    devuelve ``GeasUnavailable`` y el líder para. La única excepción es
    ``gate``, que es local por diseño.
  - **Sin heartbeat.** Reclamar es ``start_ticket`` y cerrar es
    ``complete_ticket``; no hay renovación periódica de locks.

Configuración (precedencia, de más a menos específica):

  1. variables de entorno ``GEAS_URL``, ``GEAS_TOKEN``, ``GEAS_ACTOR``,
     ``GEAS_ORG_ID``;
  2. ``.env`` en la raíz del repo;
  3. ``GEAS_CLIENT_CONFIG`` o ``~/.config/geas/client.env``;
  4. ``harness/geas.json`` para ``url``/``org_id``/``repository``/``repository_id``.

El token NUNCA se escribe en ``harness/geas.json`` ni se imprime.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from agents.tools.geas_client import GeasClient, GeasError

CRITERIA_HEADER = "Criterios de aceptación:"
LEGACY_CRITERIA_HEADER = "Criterios de aceptacion:"

FREE, CLAIMED, IN_PROGRESS, BLOCKED, REVIEW, DONE, CANCELLED = (
    "FREE",
    "CLAIMED",
    "IN_PROGRESS",
    "BLOCKED",
    "REVIEW",
    "DONE",
    "CANCELLED",
)
CLAIMABLE = {FREE}
BLOCKABLE = {CLAIMED, IN_PROGRESS, BLOCKED, REVIEW}

_STATUS = {
    FREE: "pending",
    CLAIMED: "pending",
    IN_PROGRESS: "in_progress",
    REVIEW: "in_progress",
    DONE: "done",
    BLOCKED: "blocked",
    CANCELLED: "blocked",
}

#: SCOPE-001, API-002, MIG-GEAS-001, ONBOARD-001...
_FEATURE_ID = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*-\d+)\s*:\s*(.*)$")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class GeasUnavailable(RuntimeError):
    """GEAS no está configurado, no responde o el actor no puede leer."""


def _read_env(path: Path) -> dict[str, str]:
    """Lee un .env/client.env sin dependencias. Ignora comentarios y `export`."""
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


def client_config_path() -> Path:
    return Path(
        os.environ.get("GEAS_CLIENT_CONFIG", Path.home() / ".config" / "geas" / "client.env")
    )


def config_path(root: Path) -> Path:
    return root / "harness" / "geas.json"


def read_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GeasUnavailable(f"{path} ilegible: {exc}") from exc
    if not isinstance(data, dict):
        raise GeasUnavailable(f"{path} debe ser un objeto JSON.")
    return data


def enabled(root: Path) -> bool:
    """¿Este checkout usa GEAS como fuente de verdad del backlog?"""
    if os.environ.get("HARNESS_BACKEND", "").lower() == "local":
        return False
    if os.environ.get("HARNESS_BACKEND", "").lower() == "geas":
        return True
    try:
        cfg = read_config(root)
    except GeasUnavailable:
        return True  # existe pero roto: que falle al usarlo, no en silencio
    return bool(cfg) and cfg.get("backend", "geas") == "geas" and cfg.get("enabled", True)


def _merged_env(root: Path) -> dict[str, str]:
    env = _read_env(client_config_path())
    env.update(_read_env(root / ".env"))
    for key in ("GEAS_URL", "GEAS_TOKEN", "GEAS_ACTOR", "GEAS_ACTOR_ID", "GEAS_ORG_ID"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def _config(root: Path) -> dict[str, Any]:
    cfg = read_config(root)
    env = _merged_env(root)
    url = env.get("GEAS_URL") or str(cfg.get("url") or "")
    token = env.get("GEAS_TOKEN", "")
    actor = env.get("GEAS_ACTOR") or env.get("GEAS_ACTOR_ID", "") or str(cfg.get("actor") or "")
    org = env.get("GEAS_ORG_ID") or str(cfg.get("org_id") or "")
    if not url:
        raise GeasUnavailable(
            "GEAS_NOT_CONFIGURED — pon la IP/URL en harness/geas.json (`url`) "
            "o en GEAS_URL dentro de .env."
        )
    if "<IP>" in url or "<ip>" in url:
        raise GeasUnavailable(
            "GEAS_NOT_CONFIGURED — harness/geas.json todavía tiene el comodín "
            "`<IP>`: sustitúyelo por la IP/URL real del servidor GEAS."
        )
    if not token and not actor:
        raise GeasUnavailable(
            "GEAS_NOT_CONFIGURED — falta GEAS_TOKEN (o GEAS_ACTOR si hablas "
            "directo con el servidor). Ponlo en .env; no se commitea."
        )
    return {"url": url, "token": token, "actor": actor, "org_id": org, "cfg": cfg}


def load(root: Path) -> GeasClient:
    conf = _config(root)
    return GeasClient(
        conf["url"],
        token=conf["token"],
        actor_id=conf["actor"] if not conf["token"] else "",
        org_id=conf["org_id"],
    )


def call(root: Path, tool: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return load(root).call(tool, params or {})
    except GeasError as exc:
        raise GeasUnavailable(f"{tool}: {exc}") from exc


def _uuid(value: str) -> bool:
    return bool(_UUID.match(value or ""))


def org_id(root: Path) -> str:
    """Id de la organización, preguntándoselo al servidor si no está en config."""
    conf = _config(root)
    if conf["org_id"]:
        return conf["org_id"]
    try:
        org = load(root).get_organization()
    except GeasError as exc:
        raise GeasUnavailable(f"get_organization: {exc}") from exc
    found = str(org.get("id") or "")
    if not found:
        raise GeasUnavailable("GEAS no devolvió el id de la organización.")
    return found


def actor_id(root: Path) -> str:
    """UUID del actor de este dispositivo. '' si no hay nombre configurado."""
    conf = _config(root)
    actor = conf["actor"].strip()
    if not actor:
        return ""
    if _uuid(actor):
        return actor
    try:
        actors = load(root).list_actors(org_id(root))
    except (GeasError, GeasUnavailable) as exc:
        raise GeasUnavailable(f"list_actors: {exc}") from exc
    for item in actors:
        if item.get("name") == actor:
            return str(item.get("id") or "")
    raise GeasUnavailable(f"El actor '{actor}' no aparece en list_actors.")


def tickets(root: Path) -> list[dict[str, Any]]:
    """Todos los tickets de la org con su detalle (descripción y dependencias).

    ``list_tickets`` no trae descripción ni dependencias, así que se pide
    ``get_ticket`` por cada uno. El backlog de una hackathon son decenas de
    tickets; si algún día son miles, esto se cambia por una herramienta que
    devuelva el detalle en lote.
    """
    client = load(root)
    oid = org_id(root)
    try:
        basic = client.list_tickets(org_id=oid)
    except GeasError as exc:
        raise GeasUnavailable(f"list_tickets: {exc}") from exc
    detailed: list[dict[str, Any]] = []
    for item in basic:
        tid = str(item.get("id") or "")
        if not tid:
            continue
        try:
            detail = client.ticket(tid)
        except GeasError as exc:
            raise GeasUnavailable(f"get_ticket({tid[:8]}): {exc}") from exc
        detailed.append({**item, **detail})
    return detailed


def available(root: Path) -> list[dict[str, Any]]:
    """Tickets que este actor puede reclamar ahora (FREE + deps + locks)."""
    client = load(root)
    try:
        items = client.available_tasks()
    except GeasError as exc:
        raise GeasUnavailable(f"get_available_tasks: {exc}") from exc
    detailed: list[dict[str, Any]] = []
    for item in items:
        tid = str(item.get("id") or "")
        if not tid:
            continue
        try:
            detail = client.ticket(tid)
        except GeasError:
            detail = {}
        detailed.append({**item, **detail})
    return detailed


def parse_criteria(description: str) -> list[str]:
    """Extrae los criterios numerados que escribe el importador."""
    text = description or ""
    for header in (CRITERIA_HEADER, LEGACY_CRITERIA_HEADER):
        if header in text:
            _, _, rest = text.partition(header)
            break
    else:
        return []
    criteria: list[str] = []
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped:
            if criteria:
                break
            continue
        if not stripped[0].isdigit():
            break
        _, _, body = stripped.partition(".")
        criteria.append(body.strip())
    return criteria


def split_title(title: str) -> tuple[str, str]:
    """``"SCOPE-001: Definir..."`` -> ``("SCOPE-001", "Definir...")``."""
    match = _FEATURE_ID.match((title or "").strip())
    if not match:
        return "", (title or "").strip()
    return match.group(1), match.group(2).strip()


def feature_id(ticket: dict[str, Any]) -> str:
    fid, _ = split_title(str(ticket.get("title") or ""))
    if fid:
        return fid
    return f"GEAS-{str(ticket.get('id') or '')[:8]}"


def status_of(ticket: dict[str, Any]) -> str:
    return _STATUS.get(str(ticket.get("status") or "").upper(), "pending")


def to_feature(
    ticket: dict[str, Any], by_ticket: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Traduce un ticket de GEAS al formato de feature del arnés."""
    by_ticket = by_ticket or {}
    fid = feature_id(ticket)
    _, title = split_title(str(ticket.get("title") or ""))
    depends: list[str] = []
    for dep in ticket.get("dependencies") or []:
        dep_ticket = by_ticket.get(str(dep))
        depends.append(feature_id(dep_ticket) if dep_ticket else f"GEAS-{str(dep)[:8]}")
    feature = {
        "id": fid,
        "title": title or str(ticket.get("title") or fid),
        "description": str(ticket.get("description") or ""),
        "acceptance_criteria": parse_criteria(str(ticket.get("description") or "")),
        "status": status_of(ticket),
        "depends_on": depends,
        "ticket_id": str(ticket.get("id") or ""),
        "raw_status": str(ticket.get("status") or ""),
    }
    if ticket.get("branch"):
        feature["branch"] = str(ticket["branch"])
    if ticket.get("assigned_actor_id"):
        feature["assigned_actor_id"] = str(ticket["assigned_actor_id"])
    return feature


def _existing_features(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "harness" / "featureslist.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    features = doc.get("features") if isinstance(doc, dict) else None
    if not isinstance(features, list):
        return {}
    return {str(f.get("id")): f for f in features if isinstance(f, dict) and f.get("id")}


def features(root: Path) -> list[dict[str, Any]]:
    """Backlog completo, en el orden que devuelve GEAS, con metadatos locales."""
    items = tickets(root)
    by_ticket = {str(t.get("id") or ""): t for t in items}
    previous = _existing_features(root)
    result: list[dict[str, Any]] = []
    for ticket in items:
        feature = to_feature(ticket, by_ticket)
        old = previous.get(feature["id"], {})
        for key in ("started", "closed", "blocked_reason", "review_rounds"):
            if key in old:
                feature[key] = old[key]
        result.append(feature)
    return result


def document(root: Path, features_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Documento con la misma forma que ``harness/featureslist.json``."""
    path = root / "harness" / "featureslist.json"
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        old = {}
    return {
        "$comment": old.get(
            "$comment",
            "ESPEJO de solo lectura de GEAS. La fuente de verdad es el ticket; "
            "no edites este fichero a mano: cámbialo con `harness add`.",
        ),
        "version": int(old.get("version", 1) or 1),
        "project": old.get("project", "NavaHack"),
        "features": features_list,
    }


def write_mirror(root: Path, features_list: list[dict[str, Any]] | None = None) -> bool:
    """Escribe el espejo solo si cambió. Devuelve True si lo reescribió."""
    features_list = features(root) if features_list is None else features_list
    target = root / "harness" / "featureslist.json"
    new = document(root, features_list)
    text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
    try:
        current = target.read_text(encoding="utf-8")
    except OSError:
        current = ""
    if current == text:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return True


def find(root: Path, identifier: str) -> dict[str, Any] | None:
    """Busca por id de feature (``SCOPE-001``) o por UUID de ticket."""
    items = tickets(root)
    by_ticket = {str(t.get("id") or ""): t for t in items}
    if _uuid(identifier):
        ticket = by_ticket.get(identifier)
        return to_feature(ticket, by_ticket) if ticket else None
    for ticket in items:
        if feature_id(ticket) == identifier:
            return to_feature(ticket, by_ticket)
    return None


def is_blockable(ticket: dict[str, Any]) -> bool:
    return str(ticket.get("status") or "").upper() in BLOCKABLE


def repository_id(root: Path) -> str:
    """Repo de este checkout, resuelto por ``.geas.yml`` o por el único visible."""
    cfg = _config(root)["cfg"]
    declared = str(cfg.get("repository_id") or "")
    if declared:
        return declared
    repo = str(cfg.get("repository") or "")
    if repo and not (root / ".geas.yml").is_file():
        (root / ".geas.yml").write_text(f"repository: {repo}\n", encoding="utf-8")
    try:
        return load(root).resolve_repository(root)
    except GeasError as exc:
        raise GeasUnavailable(f"resolve_repository: {exc}") from exc


def build_description(description: str, criteria: list[str]) -> str:
    parts = [(description or "").strip()]
    if criteria:
        parts.append(
            CRITERIA_HEADER + "\n" + "\n".join(f"  {i}. {c}" for i, c in enumerate(criteria, 1))
        )
    return "\n\n".join(p for p in parts if p)


def create_feature(
    root: Path,
    *,
    feature_id: str,
    title: str,
    description: str,
    criteria: list[str],
    depends_on: list[str],
    priority: int = 0,
) -> dict[str, Any]:
    """Crea un ticket en GEAS. Las dependencias deben existir ya (UUID)."""
    client = load(root)
    repo = repository_id(root)
    deps: list[str] = []
    for dep in depends_on:
        found = find(root, dep)
        if not found or not found.get("ticket_id"):
            raise GeasUnavailable(f"La dependencia '{dep}' no existe en GEAS.")
        deps.append(str(found["ticket_id"]))
    try:
        created = client.create_ticket(
            title=f"{feature_id}: {title}",
            description=build_description(description, criteria),
            repository_id=repo,
            dependencies=deps,
            priority=priority,
        )
    except GeasError as exc:
        raise GeasUnavailable(f"create_ticket: {exc}") from exc
    return {**created, "feature_id": feature_id}


def start(root: Path, identifier: str, commit_before: str = "") -> dict[str, Any]:
    found = find(root, identifier)
    if not found:
        raise GeasUnavailable(f"No existe la feature '{identifier}' en GEAS.")
    try:
        result = load(root).start_ticket(str(found["ticket_id"]), commit_before)
    except GeasError as exc:
        raise GeasUnavailable(f"start_ticket: {exc}") from exc
    return {**found, **result}


def complete(
    root: Path, identifier: str, commit_after: str = "", result_text: str = "OK"
) -> dict[str, Any]:
    found = find(root, identifier)
    if not found:
        raise GeasUnavailable(f"No existe la feature '{identifier}' en GEAS.")
    try:
        result = load(root).complete_ticket(
            str(found["ticket_id"]), commit_after=commit_after, result=result_text
        )
    except GeasError as exc:
        raise GeasUnavailable(f"complete_ticket: {exc}") from exc
    return {**found, **result}


def block(root: Path, identifier: str, reason: str = "") -> dict[str, Any]:
    found = find(root, identifier)
    if not found:
        raise GeasUnavailable(f"No existe la feature '{identifier}' en GEAS.")
    try:
        result = load(root).block_ticket(str(found["ticket_id"]), reason)
    except GeasError as exc:
        raise GeasUnavailable(f"block_ticket: {exc}") from exc
    return {**found, **result}
