"""Capa de parkings (D-05): GeoJSON para el mapa + parking más cercano a un punto.

Lee el snapshot de `scripts/snapshot.py parkings` y escribe
`data/layers/parkings.geojson`: un Feature por parking con plazas libres,
porcentaje libre, hora de actualización y `stale` (sin datos). Un parking está
«sin datos» si el snapshot entero está caducado (D-00: 10 min) **o** si su
propia `fechahora` se queda atrás respecto al resto (el Concello a veces deja
un parking congelado mientras actualiza los demás).

    python scripts/parkings.py          # tras snapshot.py parkings (cron */2)

Stdlib pura.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.snapshot import age

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshots" / "parkings" / "latest.json"
OUT = ROOT / "data" / "layers" / "parkings.geojson"
LAG_STALE_S = 10 * 60  # un parking con fechahora 10 min por detrás del resto: sin datos


def _ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")  # hora local Madrid, sin zona


def layer(snapshot: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """FeatureCollection de parkings con estado de frescura por parking."""
    _, snapshot_stale = age(snapshot, now or datetime.now(UTC))
    rows = snapshot["data"]
    newest = max(_ts(r["fechahora"]) for r in rows)
    features = []
    for r in rows:
        lag = (newest - _ts(r["fechahora"])).total_seconds()
        stale = snapshot_stale or lag > LAG_STALE_S
        total = int(r["totalplazas"])
        free = int(r["plazaslibres"])
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
                "properties": {
                    "id": r.get("id_parking", r.get("id")),
                    "name": r["nombre"],
                    "free": None if stale else free,
                    "total": total,
                    "free_pct": None if stale or not total else round(100 * free / total),
                    "updated": r["fechahora"],
                    "stale": stale,
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "fetched_at": snapshot["fetched_at"],
        "source": "Concello de Vigo — datos.vigo.org (ODC-BY)",
    }


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest(geojson: dict[str, Any], lat: float, lon: float) -> dict[str, Any] | None:
    """El parking con datos más cercano a (lat, lon), con distancia, para el panel del punto.

    Uno «sin datos» solo sale si no queda ninguno con datos: de poco sirve
    recomendar un parking del que no sabemos si hay sitio.
    """
    fresh = [f for f in geojson["features"] if not f["properties"]["stale"]]
    best: dict[str, Any] | None = None
    for f in fresh or geojson["features"]:
        flon, flat = f["geometry"]["coordinates"]
        d = haversine_m(lat, lon, flat, flon)
        if best is None or d < best["distance_m"]:
            best = {**f["properties"], "distance_m": round(d)}
    return best


def main() -> int:
    if not SNAPSHOT.exists():
        print("sin snapshot: ejecuta antes `python scripts/snapshot.py parkings`")
        return 1
    geo = layer(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
    fresh = sum(not f["properties"]["stale"] for f in geo["features"])
    print(f"{len(geo['features'])} parkings ({fresh} con datos) en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
