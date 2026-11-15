"""Calles con farolas para la noche del mapa (LIGHT-03): `web/data/street-lamps.json`.

La web enciende las farolas al anochecer dibujando un brillo cada pocos metros a lo largo de las
calles (`web/js/lights.js`). Aquí solo se guardan las líneas de las calles que caen dentro del
mapa ilustrado, sacadas de OpenStreetMap con Overpass (© colaboradores de OpenStreetMap, ODbL):
vías con coche y calles peatonales, sin túneles ni autopistas (no se ven o no llevan esa luz).

    python -m scripts.street_lamps

Formato: `{"source", "fetched_at", "lines": [[[lat, lon], ...], ...]}` con 5 decimales (~1 m).
Stdlib pura.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data" / "street-lamps.json"
OVERPASS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")  # 2.º: espejo
USER_AGENT = "NaviVigo-LIGHT03/0.1 (+https://github.com/cacelass/NaviHack)"
# límites del mapa ilustrado (esquinas del lienzo 5120×3072 con la proyección de web/js/tour.js)
BBOX = (42.2268, -8.7383, 42.2517, -8.7013)  # s, w, n, e
KINDS = (
    "trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link"
    "|unclassified|residential|living_street|pedestrian"
)


def query(bbox: tuple[float, float, float, float] = BBOX) -> str:
    s, w, n, e = bbox
    return (
        "[out:json][timeout:90];"
        f'way["highway"~"^({KINDS})$"]["tunnel"!~"yes"]({s},{w},{n},{e});'
        "out geom;"
    )


def lines(payload: dict) -> list[list[list[float]]]:
    out = []
    for el in payload.get("elements", []):
        geom = el.get("geometry") or []
        if len(geom) >= 2:
            out.append([[round(p["lat"], 5), round(p["lon"], 5)] for p in geom])
    return out


def main() -> int:
    body = urllib.parse.urlencode({"data": query()}).encode()
    payload = None
    for url in OVERPASS:  # Overpass da 502/504 a ratos: se prueba el espejo
        req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 — URL fija https
                payload = json.loads(resp.read())
            break
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"{url}: {exc}")
    if payload is None:
        return 1
    doc = {
        "source": "OpenStreetMap (Overpass) · © colaboradores de OpenStreetMap, ODbL",
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "lines": lines(payload),
    }
    OUT.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    pts = sum(len(x) for x in doc["lines"])
    print(f"{len(doc['lines'])} calles, {pts} vértices en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
