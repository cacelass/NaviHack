"""Ingesta del GTFS de Vitrasa (X-01): paradas, líneas y horarios **programados**.

Fuente oficial: `https://datos.vigo.org/data/transporte/gtfs_vigo.zip` (dataset
CKAN `gtfs-vitrasa`, ODC-BY). No hay feed oficial en tiempo real de Vitrasa y no
usamos wrappers no oficiales: todo lo que sale de aquí va etiquetado
`"kind": "scheduled"` y la UI debe decir «horario programado», nunca «llega en».

Cruce de Navidad: el aviso oficial «DESVÍOS NADAL 2026 / 2027»
(`avisos_transporte_es.json`) lista las líneas desviadas y la zona restringida
(Policarpo Sanz). Las paradas de esa zona salen con `christmas_detour: true` y
las salidas de líneas afectadas con `detour: true`, para avisar en la UI.

    python -m scripts.gtfs_vitrasa     # → data/transit/vitrasa.json (git-ignored)

Stdlib pura.
"""

from __future__ import annotations

import csv
import html
import io
import json
import re
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
GTFS_URL = "https://datos.vigo.org/data/transporte/gtfs_vigo.zip"
NOTICES_URL = "https://datos.vigo.org/data/avisos/avisos_transporte_es.json"
OUT = ROOT / "data" / "transit" / "vitrasa.json"
USER_AGENT = "TinyVigo-X01/0.1 (+https://github.com/cacelass/NaviHack)"
RESTRICTED_STREETS = ("policarpo sanz",)  # zona restringida del aviso de Navidad


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
        data: bytes = resp.read()
    return data


def _rows(z: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with z.open(name) as fh:
        reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def christmas_detours(notices: list[dict[str, Any]]) -> dict[str, Any]:
    """Líneas desviadas y periodo del aviso de Navidad vigente (vacío si no hay)."""
    for n in notices:
        if (
            "NADAL" in str(n.get("titulo", "")).upper()
            and "DESV" in str(n.get("titulo", "")).upper()
        ):
            lines = [
                x.strip() for x in str(n.get("lineas_afectadas") or "").split(",") if x.strip()
            ]
            summary = html.unescape(re.sub(r"<[^>]+>", " ", str(n.get("resumen") or "")))
            return {
                "notice_id": n.get("id"),
                "title": n["titulo"],
                "from": n.get("fecha_inicio"),
                "to": n.get("fecha_fin"),
                "lines": sorted(lines),
                "summary": re.sub(r"\s+", " ", summary).strip(),
            }
    return {}


def build(gtfs: zipfile.ZipFile, detours: dict[str, Any]) -> dict[str, Any]:
    routes = {
        r["route_id"]: {
            "id": r["route_id"],
            "short": r.get("route_short_name") or r["route_id"],
            "name": r.get("route_long_name", ""),
            "color": r.get("route_color") or None,
        }
        for r in _rows(gtfs, "routes.txt")
    }
    detour_lines = set(detours.get("lines", []))
    stops = {}
    for s in _rows(gtfs, "stops.txt"):
        name = s["stop_name"]
        stops[s["stop_id"]] = {
            "id": s["stop_id"],
            "code": s.get("stop_code") or None,
            "name": name,
            "lat": round(float(s["stop_lat"]), 6),
            "lon": round(float(s["stop_lon"]), 6),
            "christmas_detour": any(st in name.lower() for st in RESTRICTED_STREETS),
        }
    services: dict[str, list[str]] = defaultdict(list)
    for c in _rows(gtfs, "calendar_dates.txt"):
        if c["exception_type"] == "1":
            services[c["service_id"]].append(c["date"])
    # calendar.txt viene vacío en el GTFS de Vitrasa: todo va por calendar_dates.
    trips = {t["trip_id"]: t for t in _rows(gtfs, "trips.txt")}
    departures: dict[str, list[list[Any]]] = defaultdict(list)
    for st in _rows(gtfs, "stop_times.txt"):
        trip = trips.get(st["trip_id"])
        if trip is None or not st.get("departure_time"):
            continue
        short = routes.get(trip["route_id"], {}).get("short", trip["route_id"])
        departures[st["stop_id"]].append(
            [
                st["departure_time"][:5],  # HH:MM; puede pasar de 24:00 (servicio nocturno)
                short,
                trip.get("trip_headsign", ""),
                trip["service_id"],
                short in detour_lines,
            ]
        )
    for deps in departures.values():
        deps.sort()
    return {
        "kind": "scheduled",
        "source": "Vitrasa GTFS — datos.vigo.org (ODC-BY)",
        "routes": sorted(routes.values(), key=lambda r: r["short"]),
        "stops": sorted(stops.values(), key=lambda s: s["id"]),
        "services": {k: sorted(v) for k, v in services.items()},
        "departures": departures,
        "christmas_detours": detours,
    }


def next_departures(
    data: dict[str, Any], stop_id: str, now: datetime, limit: int = 5
) -> list[dict[str, Any]]:
    """Próximas salidas **programadas** de una parada (hora local de Madrid, sin zona)."""
    day = now.strftime("%Y%m%d")
    hhmm = now.strftime("%H:%M")
    active = {sid for sid, dates in data["services"].items() if day in dates}
    out = []
    for time, line, headsign, service, detour in data["departures"].get(stop_id, []):
        if service in active and time >= hhmm:
            out.append(
                {
                    "time": time,
                    "line": line,
                    "headsign": headsign,
                    "kind": "scheduled",
                    "detour": detour,
                }
            )
            if len(out) == limit:
                break
    return out


def main() -> int:
    gtfs = zipfile.ZipFile(io.BytesIO(_download(GTFS_URL)))
    notices = json.loads(_download(NOTICES_URL))
    data = build(gtfs, christmas_detours(notices))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_dep = sum(len(v) for v in data["departures"].values())
    flagged = sum(s["christmas_detour"] for s in data["stops"])
    print(
        f"{len(data['stops'])} paradas, {len(data['routes'])} líneas, {n_dep} salidas; "
        f"{flagged} paradas en zona restringida; aviso: {data['christmas_detours'].get('title')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
