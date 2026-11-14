"""Capa de cámaras de tráfico del Concello (X-09): enlaces, sin proxy.

Fuente: `https://datos.vigo.org/data/trafico/camaras-trafico.json` (dataset
CKAN `t-camaras`, ODC-BY): 61 cámaras con `id, nombre, lat, lon, url`. El
dataset indica «para obtener la imagen de la cámara acceda a la dirección web
del campo url».

Términos (comprobado 2026-11-14): la licencia ODC-BY cubre el **dataset**
(posiciones y URLs), no las imágenes, que sirve `camaras.vigo.org` sin licencia
de redistribución declarada. Por eso **no se hace proxy ni se guardan copias**:
la app carga la imagen en directo desde el Concello (`<img src>`; su CSP es
`img-src *` y no hace falta CORS para mostrarla) y enlaza a la fuente, con
crédito «Imagen: Concello de Vigo». Las URLs del dataset son `http://` y se
reescriben a `https://` (mismo servidor; en una web HTTPS el `http://` se
bloquearía como contenido mixto).

Hay cámaras que a ratos devuelven 0 bytes: la UI debe mostrar «sin imagen»
cuando la imagen no carga (`onerror`). `--probe` lo mide, una petición por
segundo.

    python -m scripts.cameras            # → data/layers/cameras.geojson (git-ignored)
    python -m scripts.cameras --probe    # además, anota qué cámaras responden

Stdlib pura.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FEED = "https://datos.vigo.org/data/trafico/camaras-trafico.json"
OUT = ROOT / "data" / "layers" / "cameras.geojson"
USER_AGENT = "TinyVigo-X09/0.1 (+https://github.com/cacelass/NaviHack)"
CREDIT = "Imagen: Concello de Vigo (camaras.vigo.org) · datos: datos.vigo.org (ODC-BY)"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        data: bytes = resp.read()
    return data


def https(url: str) -> str:
    return "https://" + url.removeprefix("http://") if url.startswith("http://") else url


def layer(rows: list[dict[str, Any]], status: dict[str, bool] | None = None) -> dict[str, Any]:
    features = []
    for r in rows:
        if r.get("lat") is None or r.get("lon") is None:
            continue
        image = https(str(r["url"]))
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
                "properties": {
                    "id": str(r["id"]),
                    "name": r["nombre"],
                    "image_url": image,  # cargar en directo; añadir ?t=<epoch> para refrescar
                    "link": image,
                    "credit": CREDIT,
                    "online": None if status is None else status.get(str(r["id"])),
                },
            }
        )
    return {"type": "FeatureCollection", "source": FEED, "credit": CREDIT, "features": features}


def probe(features: list[dict[str, Any]], get: Any = _get, pause_s: float = 1.0) -> dict[str, bool]:
    """¿Qué cámaras devuelven imagen ahora? Una petición por segundo, sin guardar imágenes."""
    status: dict[str, bool] = {}
    for f in features:
        p = f["properties"]
        try:
            status[p["id"]] = len(get(p["image_url"])) > 0
        except OSError:
            status[p["id"]] = False
        time.sleep(pause_s)
    return status


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args(argv)
    rows = json.loads(_get(FEED))
    geo = layer(rows)
    if args.probe:
        geo = layer(rows, probe(geo["features"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
    online = sum(bool(f["properties"]["online"]) for f in geo["features"])
    extra = f", {online} con imagen ahora" if args.probe else ""
    print(f"{len(geo['features'])} cámaras{extra} en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
