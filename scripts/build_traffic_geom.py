"""Forma de los tramos de tráfico pegada a la calle (TRAFFIC-02): `web/data/layers/trafico_geom.json`.

El Concello publica cada tramo con pocos vértices (a veces 2-3 para una avenida entera), así que
dibujado tal cual corta esquinas y cruza manzanas. Aquí cada tramo se encaja una vez sobre la red
de OpenStreetMap con el map-matching de OSRM; la web toma esta forma y solo el **estado** del feed
en vivo (`data/live/trafico.json`), que es lo que cambia. Clave: `nombre_tramo` (único en el feed).

Si el encaje no sale o se aleja mucho de la longitud original, el tramo se queda como viene.

    python -m scripts.build_traffic_geom
"""

from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data" / "layers" / "trafico_geom.json"
FEED = "https://datos.vigo.org/data/trafico/treal.geojson"
OSRM = "https://router.project-osrm.org/match/v1/driving/"
MAX_PTS = 10
UA = "NaviVigo/0.1 (+https://github.com/cacelass/NaviHack)"


def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers={"user-agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def length_m(line: list[list[float]]) -> float:
    total = 0.0
    for (lo1, la1), (lo2, la2) in zip(line, line[1:], strict=False):
        x = math.radians(lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2))
        y = math.radians(la2 - la1)
        total += 6371000 * math.hypot(x, y)
    return total


def densify(line: list[list[float]], step: float = 60.0) -> list[list[float]]:
    """Puntos cada ~`step` m: el map-matching necesita algo más que los dos extremos."""
    out = [line[0]]
    for a, b in zip(line, line[1:], strict=False):
        n = max(1, int(length_m([a, b]) // step))
        out += [
            [a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n] for i in range(1, n + 1)
        ]
    if len(out) <= MAX_PTS:
        return out
    # el servidor público no admite más de ~10 puntos por traza: se reparten a lo largo del tramo
    return [out[round(i * (len(out) - 1) / (MAX_PTS - 1))] for i in range(MAX_PTS)]


def match(line: list[list[float]]) -> list[list[float]] | None:
    pts = densify(line)
    coords = ";".join(f"{lo:.6f},{la:.6f}" for lo, la in pts)
    q = urllib.parse.urlencode(
        {
            "geometries": "geojson",
            "overview": "full",
            "tidy": "true",
            "radiuses": ";".join(["20"] * len(pts)),
        }
    )
    d = _get(OSRM + coords + "?" + q)
    if d.get("code") != "Ok" or len(d.get("matchings", [])) != 1:
        return None
    geom = d["matchings"][0]["geometry"]["coordinates"]
    ratio = length_m(geom) / max(1.0, length_m(line))
    return geom if 0.7 <= ratio <= 1.4 else None


def main() -> int:
    feats = _get(FEED)["features"]
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    out: dict[str, list[list[float]]] = {}
    fails = 0
    for f in feats:
        name, line = f["properties"]["nombre_tramo"], f["geometry"]["coordinates"]
        if name in old:  # la forma de la calle no cambia: solo se encaja lo nuevo
            out[name] = old[name]
            continue
        try:
            geom = match(line)
        except Exception:  # red o límite del servidor: el tramo se queda como viene
            geom = None
        time.sleep(1.1)  # servidor público de OSRM: una petición por segundo
        if geom is None:
            fails += 1
            continue
        out[name] = [[round(lo, 5), round(la, 5)] for lo, la in geom]
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"{len(out)} de {len(feats)} tramos encajados ({fails} sin encaje); {OUT.stat().st_size // 1024} KB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
