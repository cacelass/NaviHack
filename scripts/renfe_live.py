"""Retrasos en vivo de Renfe para Vigo (X-03): go para retrasos, no-go para posiciones.

Comprobado 2026-11-14 17:33 (ver vault/01_PROYECTO/fuentes_datos.md, «Renfe en vivo»):

- `https://gtfsrt.renfe.com/trip_updates_LD.json` — GTFS-RT de AV/LD/MD **en JSON**
  (no hace falta decodificar protobuf), cabecera al día (15 s de retraso) y con
  viajes que paran en Vigo-Urzaiz/Guixar (12 de 12 viajes del día cruzan con el
  GTFS estático de X-02). Da `delay` en segundos por viaje → **GO**.
- `https://gtfsrt.renfe.com/vehicle_positions_LD.json` — cabecera **1 h atrasada**
  y entidades de viajes del día anterior → **NO-GO** para mover trenes en el mapa.
- `trip_updates.json` / `vehicle_positions.json` son Cercanías: **sin cobertura en Vigo**.

    python -m scripts.renfe_live      # retrasos de los trenes de Vigo, ahora

Stdlib pura.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TRIP_UPDATES = "https://gtfsrt.renfe.com/trip_updates_LD.json"
STATIC = ROOT / "data" / "transit" / "renfe_vigo.json"
USER_AGENT = "TinyVigo-X03/0.1 (+https://github.com/cacelass/NaviHack)"
MAX_HEADER_AGE_S = 300


def delays(feed: dict[str, Any], vigo_trip_ids: set[str], now_s: float) -> dict[str, Any]:
    """`{trip_id: minutos de retraso}` para los viajes de Vigo; vacío si el feed está viejo."""
    age = now_s - int(feed.get("header", {}).get("timestamp", 0))
    if age > MAX_HEADER_AGE_S:
        return {"fresh": False, "age_s": int(age), "delays": {}}
    out: dict[str, int] = {}
    for e in feed.get("entity", []):
        tu = e.get("tripUpdate") or {}
        tid = (tu.get("trip") or {}).get("tripId")
        if tid in vigo_trip_ids and tu.get("delay") is not None:
            out[tid] = round(int(tu["delay"]) / 60)
    return {"fresh": True, "age_s": int(age), "delays": out}


def main() -> int:
    import time

    req = urllib.request.Request(TRIP_UPDATES, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        feed = json.loads(resp.read())
    static = json.loads(STATIC.read_text(encoding="utf-8"))
    ids = {m["trip_id"] for m in static["movements"]}
    res = delays(feed, ids, time.time())
    print(f"feed {'al día' if res['fresh'] else 'VIEJO'} ({res['age_s']} s); {len(res['delays'])} trenes de Vigo con retraso:")
    for tid, mins in sorted(res["delays"].items()):
        print(f"  {tid}: +{mins} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
