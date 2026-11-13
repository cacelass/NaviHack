"""Cliente HTTP de GEAS (stdlib pura).

Habla con `geas serve` a través del proxy con token. El proxy traduce
``Authorization: Bearer <token>`` a ``X-Geas-Actor``, así que el cliente nunca
necesita conocer el UUID del actor ni abrir la base de datos.

    from agents.tools.geas_client import GeasClient
    c = GeasClient("http://127.0.0.1:8790", token=mi_token)
    for t in c.available_tasks():
        print(t["id"][:8], t["title"])
    c.start_ticket(t["id"], commit_before=sha)

El arnés usa este cliente a través de ``agents.agents.geas_backlog``; los
scripts de arranque pueden usarlo directamente.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class GeasError(RuntimeError):
    """La API respondió ``success=false`` (FORBIDDEN, RESOURCE_UNAVAILABLE...)."""


def _repo_declarado(root: str | Path | None = None) -> tuple[str, str]:
    """(repository, repository_id) declarados en el ``.geas.yml`` del checkout."""
    raiz = Path(root) if root is not None else Path.cwd()
    fichero = raiz / ".geas.yml"
    if not fichero.is_file():
        return "", ""
    nombre = ""
    declarado = ""
    for linea in fichero.read_text(encoding="utf-8").splitlines():
        clave, sep, valor = linea.partition(":")
        if not sep:
            continue
        clave = clave.strip()
        if clave == "repository":
            nombre = valor.strip()
        elif clave == "repository_id":
            declarado = valor.strip()
    return nombre, declarado


class GeasClient:
    def __init__(
        self,
        base_url: str,
        token: str = "",
        actor_id: str = "",
        org_id: str = "",
        timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.actor_id = actor_id
        self.org_id = org_id
        self.timeout = timeout

    # ── transporte ──────────────────────────────────────────────────────

    def call(self, tool: str, params: dict[str, Any] | None = None) -> dict:
        """Invoca una herramienta MCP por HTTP. Levanta GeasError si falla."""
        url = f"{self.base_url}/api/tools/{tool}"
        body = json.dumps(params or {}).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.token:
            # El proxy lo convierte en X-Geas-Actor.
            req.add_header("Authorization", f"Bearer {self.token}")
        if self.actor_id:
            # Acceso directo (esta máquina, sin proxy).
            req.add_header("X-Geas-Actor", self.actor_id)
        if self.org_id:
            req.add_header("X-Geas-Organization", self.org_id)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                raise GeasError(f"HTTP {exc.code}: {raw[:200]!r}") from exc
        except urllib.error.URLError as exc:
            raise GeasError(
                f"No se pudo contactar con GEAS en {self.base_url}: {exc.reason}"
            ) from exc
        else:
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError as exc:
                # Un 200 con HTML (un proxy o un wifi cautivo) no puede subir
                # como JSONDecodeError: para el cliente es una respuesta
                # inválida y debe salir por GeasError como cualquier otro fallo.
                raise GeasError(
                    f"{tool}: respuesta no-JSON de {self.base_url} ({raw[:200]!r})"
                ) from exc
        if not payload.get("success"):
            raise GeasError(
                f"{tool}: {payload.get('error', 'error desconocido')}"
                f" {payload.get('data', '')}".strip()
            )
        return payload.get("data") or {}

    def try_call(self, tool: str, params: dict | None = None) -> dict:
        """Como call() pero devuelve ``{"ok": bool, ...}`` en vez de levantar."""
        try:
            return {"ok": True, **self.call(tool, params)}
        except GeasError as exc:
            return {"ok": False, "error": str(exc)}

    def health(self) -> dict:
        url = f"{self.base_url}/health"
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return json.loads(resp.read() or b"{}")

    # ── tickets (§17, §24, §26) ─────────────────────────────────────────

    def available_tasks(self) -> list[dict]:
        """Tickets que este actor puede coger ahora mismo."""
        return self.call("get_available_tasks").get("available_tasks", [])

    def list_tickets(self, org_id: str = "", status: str = "") -> list[dict]:
        params: dict[str, Any] = {}
        if org_id:
            params["org_id"] = org_id
        if status:
            params["status"] = status
        return self.call("list_tickets", params).get("tickets", [])

    def ticket(self, ticket_id: str) -> dict:
        return self.call("get_ticket", {"ticket_id": ticket_id})

    def create_ticket(
        self,
        title: str,
        description: str = "",
        repository_id: str = "",
        resources: list[str] | None = None,
        dependencies: list[str] | None = None,
        priority: int = 0,
    ) -> dict:
        return self.call(
            "create_ticket",
            {
                "title": title,
                "description": description,
                "repository_id": repository_id,
                "resources": resources or [],
                "dependencies": dependencies or [],
                "priority": priority,
            },
        )

    def update_ticket(self, ticket_id: str, fields: dict[str, Any]) -> dict:
        return self.call("update_ticket", {"ticket_id": ticket_id, "fields": fields})

    def start_ticket(self, ticket_id: str, commit_before: str = "") -> dict:
        """Claim atómico: valida dependencias y recursos, adquiere los locks."""
        return self.call(
            "start_ticket",
            {"ticket_id": ticket_id, "commit_before": commit_before},
        )

    def complete_ticket(self, ticket_id: str, commit_after: str = "", result: str = "OK") -> dict:
        """commit_after + liberación de locks + DONE."""
        return self.call(
            "complete_ticket",
            {"ticket_id": ticket_id, "commit_after": commit_after, "result": result},
        )

    def block_ticket(self, ticket_id: str, reason: str = "") -> dict:
        return self.call("block_ticket", {"ticket_id": ticket_id, "reason": reason})

    def cancel_ticket(self, ticket_id: str, reason: str = "") -> dict:
        """Cancela un ticket.

        OJO: ``reason`` se sigue mandando, pero el servidor hoy la descarta.
        Se deja en el cliente para que, cuando el servidor la acepte, no haya
        que tocar los scripts.
        """
        return self.call("cancel_ticket", {"ticket_id": ticket_id, "reason": reason})

    def report_commit(self, ticket_id: str, commit: str, message: str = "") -> dict:
        """Registra un commit del ticket.

        El parámetro se llama ``commit_sha``, no ``commit``: el dispatch del
        servidor hace ``params["commit_sha"]`` y con ``commit`` responde
        "Falta parámetro: 'commit_sha'". ``message`` tampoco lo lee el servidor
        hoy; se manda igual.
        """
        return self.call(
            "report_commit",
            {"ticket_id": ticket_id, "commit_sha": commit, "message": message},
        )

    def get_organization(self, organization_id: str = "") -> dict:
        params = {"organization_id": organization_id} if organization_id else {}
        return self.call("get_organization", params)

    def list_repositories(self, org_id: str = "") -> list[dict]:
        params = {"organization_id": org_id} if org_id else {}
        return self.call("list_repositories", params).get("repositories", [])

    def resolve_repository(self, root: str | Path | None = None) -> str:
        """Id del repositorio de este checkout, sin hardcodear su nombre.

        Orden: nombre declarado en ``.geas.yml`` -> ``repository_id`` declarado
        (si sigue siendo visible) -> único repositorio visible -> GeasError
        (fail-closed) nombrando los visibles. Nunca coge "el primero" a ciegas.
        """
        nombre, declarado = _repo_declarado(root)
        repos = self.list_repositories()
        if not repos:
            raise GeasError(f"El actor no ve ningún repositorio en GEAS (repository={nombre!r}).")
        if nombre:
            hallado = next((r for r in repos if r.get("name") == nombre), None)
            if hallado:
                return hallado["id"]
        if declarado:
            hallado = next((r for r in repos if r.get("id") == declarado), None)
            if hallado:
                return hallado["id"]
        if len(repos) == 1:
            return repos[0]["id"]
        visibles = ", ".join(f"{r.get('name')}({str(r.get('id') or '')[:8]})" for r in repos)
        raise GeasError(
            "Ningún repositorio visible coincide con .geas.yml "
            f"(repository={nombre!r}); visibles: {visibles}"
        )

    def list_actors(self, org_id: str = "") -> list[dict]:
        """Actores de la org (users + agents) — tool GEAS-007."""
        params = {"organization_id": org_id} if org_id else {}
        return self.call("list_actors", params).get("actors", [])

    def list_resources(self, repository_id: str) -> list[dict]:
        """Recursos bloqueables de un repo — tool GEAS-007."""
        return self.call("list_resources", {"repository_id": repository_id}).get("resources", [])
