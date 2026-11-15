"""Datos de transporte para la web (X-04): `web/data/transit.json`.

Todo es **horario programado** (GTFS de Vitrasa, X-01, y Renfe AV/LD/MD,
X-02); la web lo etiqueta como tal y nunca dice «llega en».

- `stops`: paradas de Vitrasa (las del núcleo y cercanías de los puntos) con su
  marca de desvío de Navidad.
- `to_centre[stop_id]`: buses **directos** desde esa parada hasta el centro
  navideño (primera parada del viaje a ≤ `CENTRE_M` de una luz de Navidad):
  `[salida, línea, destino, servicio, minutos, parada_de_llegada]`.
- `near[point_id]`: parada más cercana (≤ `NEAR_M`) a cada punto, para las
  próximas salidas en la ficha.
- `services`: fechas de cada servicio, recortadas a la temporada.
- `trains`: estaciones y movimientos de Renfe en Vigo (`data/transit/renfe_vigo.json`).

    python -m scripts.build_transit_web
"""

from __future__ import annotations

import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts import gtfs_vitrasa
from scripts.parkings import haversine_m

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data" / "transit.json"
POINTS = ROOT / "data" / "points.json"
RENFE = ROOT / "data" / "transit" / "renfe_vigo.json"
CENTRE_M = 250.0
NEAR_M = 400.0
SEASON = ("20261101", "20270131")


def _minutes(hhmmss: str) -> int:
    h, m = hhmmss.split(":")[:2]
    return int(h) * 60 + int(m)


def centre_stops(stops: list[dict[str, Any]], lights: list[tuple[float, float]]) -> set[str]:
    return {
        s["id"]
        for s in stops
        if any(haversine_m(s["lat"], s["lon"], la, lo) <= CENTRE_M for la, lo in lights)
    }


def direct_to_centre(
    trips: dict[str, dict[str, str]],
    stop_times: dict[str, list[dict[str, str]]],
    routes: dict[str, str],
    centre: set[str],
) -> dict[str, list[list[Any]]]:
    """Por parada de origen, cada viaje que llega sin transbordo al centro y cuánto tarda."""
    out: dict[str, list[list[Any]]] = defaultdict(list)
    for trip_id, sts in stop_times.items():
        trip = trips.get(trip_id)
        if trip is None:
            continue
        seq = sorted(sts, key=lambda s: int(s["stop_sequence"]))
        arrive = next((i for i, s in enumerate(seq) if s["stop_id"] in centre), None)
        if not arrive:  # None o 0: no llega al centro, o ya sale de él
            continue
        target = seq[arrive]
        line = routes.get(trip["route_id"], trip["route_id"])
        for s in seq[:arrive]:
            if s["stop_id"] in centre or not s.get("departure_time"):
                continue
            mins = _minutes(target["arrival_time"]) - _minutes(s["departure_time"])
            out[s["stop_id"]].append(
                [
                    s["departure_time"][:5],
                    line,
                    trip.get("trip_headsign", ""),
                    trip["service_id"],
                    mins,
                    target["stop_id"],
                ]
            )
    for deps in out.values():
        deps.sort()
    return dict(out)


def compact_trips(
    trips: dict[str, dict[str, str]],
    stop_times: dict[str, list[dict[str, str]]],
    routes: dict[str, str],
    stop_index: dict[str, int],
    svc: dict[str, int],
) -> list[list[Any]]:
    """Viajes para el «cómo llegar» en bus (GO-01): `[línea, destino, servicio, [parada], [minuto]]`.

    Con esto la web encuentra un bus **directo** entre cualquier parada cercana al
    usuario y cualquier parada cercana al primer punto del tour.
    """
    out: list[list[Any]] = []
    for trip_id, sts in stop_times.items():
        trip = trips.get(trip_id)
        if trip is None or trip["service_id"] not in svc:
            continue
        seq = sorted(sts, key=lambda s: int(s["stop_sequence"]))
        seq = [s for s in seq if s["stop_id"] in stop_index and s.get("departure_time")]
        if len(seq) < 2:
            continue
        out.append(
            [
                routes.get(trip["route_id"], trip["route_id"]),
                trip.get("trip_headsign", ""),
                svc[trip["service_id"]],
                [stop_index[s["stop_id"]] for s in seq],
                [_minutes(s["departure_time"]) for s in seq],
            ]
        )
    out.sort(key=lambda t: t[4][0])
    return out


def daytime_served(departures: dict[str, list[list[Any]]], minimum: int = 30) -> set[str]:
    """Paradas con servicio de día (07–23 h). Las de Policarpo Sanz, cortadas por los desvíos de
    Navidad, solo conservan búhos nocturnos: recomendarlas en la ficha no sirve de nada."""
    return {
        sid
        for sid, deps in departures.items()
        if sum(1 for d in deps if "07:00" <= d[0] <= "23:00") >= minimum
    }


def nearest_stop(point: dict[str, Any], stops: list[dict[str, Any]]) -> dict[str, Any] | None:
    best = min(
        stops,
        key=lambda s: haversine_m(point["lat"], point["lon"], s["lat"], s["lon"]),
        default=None,
    )
    if best is None:
        return None
    d = haversine_m(point["lat"], point["lon"], best["lat"], best["lon"])
    return {"stop_id": best["id"], "distance_m": round(d)} if d <= NEAR_M else None


def build(
    gtfs: zipfile.ZipFile, points: list[dict[str, Any]], renfe: dict[str, Any] | None
) -> dict[str, Any]:
    base = gtfs_vitrasa.build(gtfs, {})
    stops = base["stops"]
    routes = {r["id"]: r["short"] for r in base["routes"]}
    trips = {t["trip_id"]: t for t in gtfs_vitrasa._rows(gtfs, "trips.txt")}
    stop_times: dict[str, list[dict[str, str]]] = defaultdict(list)
    for st in gtfs_vitrasa._rows(gtfs, "stop_times.txt"):
        stop_times[st["trip_id"]].append(st)
    lights = [(p["lat"], p["lon"]) for p in points if p["type"] == "light"]
    centre = centre_stops(stops, lights)
    to_centre = direct_to_centre(trips, stop_times, routes, centre)
    served = daytime_served(base["departures"])
    useful = [st for st in stops if st["id"] in served]
    near = {p["id"]: n for p in points if (n := nearest_stop(p, useful))}
    near_ids = {n["stop_id"] for n in near.values()}
    keep = {
        s["id"] for s in stops if s["id"] in centre or s["id"] in near_ids or s["id"] in to_centre
    }
    services = {
        sid: [d for d in dates if SEASON[0] <= d <= SEASON[1]]
        for sid, dates in base["services"].items()
    }
    active = {k: v for k, v in services.items() if v}
    svc_ids = sorted(active)
    svc = {k: i for i, k in enumerate(svc_ids)}
    # Compacto para el móvil: servicio por índice, minutos del día, sin campos repetidos.
    compact_to_centre = {
        stop: [[_minutes(d[0]), d[1], svc[d[3]], d[4]] for d in deps if d[3] in svc]
        for stop, deps in to_centre.items()
    }
    departures = {
        sid: [
            [_minutes(d[0]), d[1], d[2], svc[d[3]], d[4]]
            for d in base["departures"][sid]
            if d[3] in svc
        ]
        for sid in near_ids
        if sid in base["departures"]
    }
    all_stops = [[s["id"], s["name"], s["lat"], s["lon"]] for s in stops]
    stop_index = {s[0]: i for i, s in enumerate(all_stops)}
    return {
        "kind": "scheduled",
        "source": base["source"],
        "all_stops": all_stops,
        "trips": compact_trips(trips, stop_times, routes, stop_index, svc),
        "format": {
            "trips": ["línea", "destino", "servicio", "[índice en all_stops]", "[minuto_del_día]"],
            "to_centre": ["minuto_del_día", "línea", "servicio", "minutos_de_viaje"],
            "departures": ["minuto_del_día", "línea", "destino", "servicio", "desvío_navidad"],
        },
        "stops": [
            [s["id"], s["name"], s["lat"], s["lon"], int(s["christmas_detour"])]
            for s in stops
            if s["id"] in keep
        ],
        "centre_stops": sorted(centre),
        "to_centre": {k: v for k, v in compact_to_centre.items() if v},
        "near": near,
        "departures": departures,
        "services": [active[k] for k in svc_ids],
        "trains": renfe,
    }


def main() -> int:
    gtfs = zipfile.ZipFile(io.BytesIO(gtfs_vitrasa._download(gtfs_vitrasa.GTFS_URL)))
    points = json.loads(POINTS.read_text(encoding="utf-8"))["points"]
    renfe = json.loads(RENFE.read_text(encoding="utf-8")) if RENFE.exists() else None
    if renfe is None and OUT.exists():  # en CI no está data/transit/ (gitignored): se conservan los trenes publicados
        renfe = json.loads(OUT.read_text(encoding="utf-8")).get("trains")
    data = build(gtfs, points, renfe)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n = sum(len(v) for v in data["to_centre"].values())
    print(
        f"{len(data['stops'])} paradas, {len(data['centre_stops'])} en el centro, {n} salidas directas al "
        f"centro desde {len(data['to_centre'])} paradas, {len(data['near'])} puntos con parada cercana; "
        f"{OUT.stat().st_size // 1024} KB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
