"""Ingesta del GTFS estático de Renfe AV/LD/MD (X-02), recortado a Vigo.

Fuente: `https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip`
(Renfe Operadora, licencia **CC BY 4.0** → crédito en `D-17`). Se republica a
diario (~00:08 UTC). Vigo tiene dos estaciones en el fichero: `Vigo Urzaiz`
(`08223`) y `Vigo-Guixar` (`22308`). Cercanías no va en este fichero (spec v4).

Solo guardamos los viajes que paran en Vigo: salidas y llegadas con su
origen/destino, para el planner («llego a Vigo-Urzáiz») y X-04. Todo va como
`"kind": "scheduled"`.

    python -m scripts.gtfs_renfe       # → data/transit/renfe_vigo.json (git-ignored)

Stdlib pura.
"""

from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
GTFS_URL = "https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip"
OUT = ROOT / "data" / "transit" / "renfe_vigo.json"
VIGO_STOPS = {"08223": "Vigo Urzaiz", "22308": "Vigo-Guixar"}
USER_AGENT = "TinyVigo-X02/0.1 (+https://github.com/cacelass/NaviHack)"
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _rows(z: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    # Las cabeceras y celdas de Renfe vienen rellenas de espacios: se recortan.
    with z.open(name) as fh:
        reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def build(gtfs: zipfile.ZipFile) -> dict[str, Any]:
    stop_names = {s["stop_id"]: s["stop_name"] for s in _rows(gtfs, "stops.txt")}
    missing = set(VIGO_STOPS) - stop_names.keys()
    if missing:
        raise ValueError(f"faltan estaciones de Vigo en el GTFS: {sorted(missing)}")
    by_trip: dict[str, list[dict[str, str]]] = defaultdict(list)
    for st in _rows(gtfs, "stop_times.txt"):
        by_trip[st["trip_id"]].append(st)
    vigo_trips = {t for t, sts in by_trip.items() if any(s["stop_id"] in VIGO_STOPS for s in sts)}
    trips = {t["trip_id"]: t for t in _rows(gtfs, "trips.txt") if t["trip_id"] in vigo_trips}
    routes = {r["route_id"]: r for r in _rows(gtfs, "routes.txt")}
    used_services = {t["service_id"] for t in trips.values()}

    calendar = {
        c["service_id"]: {
            "days": [d for d in WEEKDAYS if c.get(d) == "1"],
            "start": c["start_date"],
            "end": c["end_date"],
        }
        for c in _rows(gtfs, "calendar.txt")
        if c["service_id"] in used_services
    }
    added: dict[str, list[str]] = defaultdict(list)
    removed: dict[str, list[str]] = defaultdict(list)
    for c in _rows(gtfs, "calendar_dates.txt"):
        if c["service_id"] in used_services:
            (added if c["exception_type"] == "1" else removed)[c["service_id"]].append(c["date"])

    movements: list[dict[str, Any]] = []
    for trip_id, trip in trips.items():
        sts = sorted(by_trip[trip_id], key=lambda s: int(s["stop_sequence"]))
        origin, dest = stop_names[sts[0]["stop_id"]], stop_names[sts[-1]["stop_id"]]
        route = routes.get(trip["route_id"], {})
        for i, s in enumerate(sts):
            if s["stop_id"] not in VIGO_STOPS:
                continue
            base = {
                "station": VIGO_STOPS[s["stop_id"]],
                "train": route.get("route_short_name") or trip["route_id"],
                "trip_id": trip_id,
                "service_id": trip["service_id"],
                "kind": "scheduled",
            }
            if i < len(sts) - 1:
                movements.append(
                    {**base, "type": "departure", "time": s["departure_time"][:5], "to": dest}
                )
            if i > 0:
                movements.append(
                    {**base, "type": "arrival", "time": s["arrival_time"][:5], "from": origin}
                )
    movements.sort(key=lambda m: (m["time"], m["station"]))
    return {
        "kind": "scheduled",
        "source": "Renfe Operadora GTFS AV/LD/MD (CC BY 4.0)",
        "stations": [
            {"id": sid, "name": name, "gtfs_name": stop_names[sid]}
            for sid, name in VIGO_STOPS.items()
        ],
        "calendar": calendar,
        "added": dict(added),
        "removed": dict(removed),
        "movements": movements,
    }


def runs_on(data: dict[str, Any], service_id: str, day: datetime) -> bool:
    d = day.strftime("%Y%m%d")
    if d in data["removed"].get(service_id, []):
        return False
    if d in data["added"].get(service_id, []):
        return True
    cal = data["calendar"].get(service_id)
    return bool(cal and cal["start"] <= d <= cal["end"] and WEEKDAYS[day.weekday()] in cal["days"])


def board(
    data: dict[str, Any],
    now: datetime,
    kind: str = "departure",
    station: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Próximas salidas (o llegadas) programadas en Vigo a partir de `now` (hora local)."""
    hhmm = now.strftime("%H:%M")
    out = []
    for m in data["movements"]:
        if m["type"] != kind or m["time"] < hhmm or (station and m["station"] != station):
            continue
        if runs_on(data, m["service_id"], now):
            out.append(m)
            if len(out) == limit:
                break
    return out


def main() -> int:
    req = urllib.request.Request(GTFS_URL, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
        gtfs = zipfile.ZipFile(io.BytesIO(resp.read()))
    data = build(gtfs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    deps = sum(m["type"] == "departure" for m in data["movements"])
    print(
        f"{len(data['movements'])} movimientos en Vigo ({deps} salidas) en {OUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
