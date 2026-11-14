"""Calles de Vigo para la búsqueda de la web (WEB-03): nombre + punto central.

Una sola consulta a Overpass (OpenStreetMap, ODbL) sobre el municipio, agrupada por
nombre; escribe web/data/streets.json como [[nombre, lat, lon], ...]. Nominatim no
sirve desde el navegador (sin CORS) y así la búsqueda funciona sin red externa.

    python -m scripts.fetch_streets

Stdlib pura.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data" / "streets.json"
BBOX = (42.170, -8.800, 42.270, -8.640)  # sur, oeste, norte, este: Vigo
URL = "https://overpass-api.de/api/interpreter"
QUERY = (
    "[out:json][timeout:60];"
    'way["highway"]["name"]["highway"!~"motorway|trunk|service|track|path|cycleway"]'
    f"({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});out center tags;"
)
USER_AGENT = "TinyVigo-WEB03/0.1 (+https://github.com/cacelass/NaviHack)"


def group(elements: list[dict]) -> list[list]:
    """Un punto por nombre: el centro medio de sus tramos."""
    acc: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for e in elements:
        name = (e.get("tags") or {}).get("name")
        c = e.get("center")
        if name and c:
            acc[name].append((c["lat"], c["lon"]))
    return sorted(
        [[n, round(sum(p[0] for p in ps) / len(ps), 6), round(sum(p[1] for p in ps) / len(ps), 6)] for n, ps in acc.items()]
    )


def main() -> int:
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    req = urllib.request.Request(URL, data=data, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(req, timeout=90) as resp:  # noqa: S310
        elements = json.loads(resp.read())["elements"]
    streets = group(elements)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(streets, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(streets)} calles -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
