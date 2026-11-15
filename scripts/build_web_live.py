"""Datos en vivo para la web, servidos como ficheros propios (WEB-05).

La web no pide datos a APIs de terceros desde el navegador: lee `web/data/live/<feed>.json`,
que este script copia desde los snapshots validados de `scripts/snapshot.py` (D-01) con su
`fetched_at`, la fuente y el umbral de «sin datos». Si un snapshot falta o no es válido, el
fichero publicado anterior se conserva (último bueno) y la web muestra su edad (D-18).

    python -m scripts.build_web_live      # tras snapshot.py (cron, ver deploy/snapshot.cron)

Quedan fuera, a propósito, los SERVICIOS que no son datos: el enrutado a pie/coche (OSRM) y las
teselas de OpenStreetMap del mapa de calles.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "data" / "snapshots"
OUT = ROOT / "web" / "data" / "live"
FEEDS = ("parkings", "agenda", "weather", "centros", "trafico")


def publish(name: str, snapshots: Path = SNAPSHOTS, out: Path = OUT) -> dict[str, Any] | None:
    """Copia el snapshot válido de `name` a la web. Devuelve lo publicado o None si no había."""
    src = snapshots / name / "latest.json"
    if not src.exists():
        return None
    snap = json.loads(src.read_text(encoding="utf-8"))
    data = snap.get("data")
    if data is None or (isinstance(data, list) and not data):
        return None
    doc = {
        "feed": name,
        "fetched_at": snap["fetched_at"],
        "source_url": snap.get("source_url"),
        "source_timestamp": snap.get("source_timestamp"),
        "stale_after_s": snap.get("stale_after_s"),
        "data": data,
    }
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / f"{name}.json.tmp"
    tmp.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(out / f"{name}.json")  # atómico: la web nunca lee medio fichero
    return doc


def main() -> int:
    done = {name: publish(name) is not None for name in FEEDS}
    print(
        ", ".join(
            f"{k}: {'ok' if v else 'sin snapshot (se conserva el anterior)'}"
            for k, v in done.items()
        )
    )
    return 0 if all(done.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
