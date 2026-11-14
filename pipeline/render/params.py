"""Genera ``pipeline/render/render-params.json`` leyendo el renderer original.

Nada de constantes a mano: la cámara sale de ``original/render.html``, el
origen geográfico y la resolución de la ortofoto de ``original/fetch-area.mjs``,
y el lienzo del 3x3 de la propia constante ``SHOT`` del renderer. El lienzo de
la expansión sale del bloque mínimo de teselas que cubre los hitos de
``landmarks.json`` con medio tesela de margen.

    python3 -m pipeline.render.params          # escribe y resume
    python3 -m pipeline.render.params --check  # falla si el JSON está desfasado
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from pipeline.georef import TILE, Camera, Canvas, Geo, RenderParams, tile_block

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "original"
OUT = HERE / "render-params.json"

# Margen que se pide alrededor de los hitos antes de redondear a teselas.
MARGIN_PX = TILE / 2
EXTRA_EAST_COLS = 1


def _read(name: str) -> str:
    return (ORIGINAL / name).read_text(encoding="utf-8")


def _search(pattern: str, text: str, where: str) -> float:
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"no encuentro {pattern!r} en {where}: ¿ha cambiado el renderer?")
    return float(match.group(1))


def camera() -> tuple[Camera, int]:
    """``SC``, ``TILT``, ``HEAD`` y ``SHOT`` del renderer (px/m, grados, px)."""
    html = _read("render.html")
    sc = _search(r"const SC = ([\d.]+);", html, "render.html")
    tilt = _search(r"TILT = (-?[\d.]+) \* Math\.PI / 180", html, "render.html")
    head = _search(r"HEAD = (-?[\d.]+) \* Math\.PI / 180", html, "render.html")
    shot = int(_search(r"const SHOT = (\d+);", html, "render.html"))
    return Camera(sc, tilt, head), shot


def geo() -> Geo:
    """Origen (``cLat``/``cLon``) y metros por grado de ``fetch-area.mjs``."""
    js = _read("fetch-area.mjs")
    lat0 = _search(r"const cLat = (-?[\d.]+)", js, "fetch-area.mjs")
    lon0 = _search(r", cLon = (-?[\d.]+)", js, "fetch-area.mjs")
    m_lat = _search(r"const mLat = ([\d.]+)", js, "fetch-area.mjs")
    m_lon = m_lat * math.cos(math.radians(lat0))
    return Geo(lat0, lon0, m_lat, m_lon)


def ortho() -> dict[str, float]:
    """Extensión descargada de ortofoto y resolución (``HX``, ``HY``, ``RES``)."""
    js = _read("fetch-area.mjs")
    hx = _search(r"HX = ([\d.]+), HY = ([\d.]+), RES = ([\d.]+);", js, "fetch-area.mjs")
    hy = _search(r"HX = [\d.]+, HY = ([\d.]+), RES = ([\d.]+);", js, "fetch-area.mjs")
    res = _search(r"HX = [\d.]+, HY = [\d.]+, RES = ([\d.]+);", js, "fetch-area.mjs")
    s, w, n, e = (float(v) for v in _read("ortho.bbox").split())
    return {"half_m": [hx, hy], "res_m": res, "bbox": [s, w, n, e]}


def landmarks() -> list[dict[str, object]]:
    return json.loads((HERE / "landmarks.json").read_text(encoding="utf-8"))["landmarks"]


def build() -> dict[str, object]:
    cam, shot = camera()
    g = geo()
    flat = RenderParams(cam, g, {"3x3": Canvas(shot, shot, shot / 2, shot / 2)})
    shot_points = [flat.to_pixel(m["lat"], m["lon"]) for m in landmarks()]
    col0, row0, col1, row1 = tile_block(shot_points, MARGIN_PX)
    expansion = {
        "width": (col1 - col0 + 1) * TILE,
        "height": (row1 - row0 + 1) * TILE,
        # La esquina del lienzo ampliado cae en (col0, row0) de la malla global;
        # el origen de la cámara sigue siendo el mismo punto geográfico, así que
        # en píxeles locales se desplaza lo que ocupa el bloque nuevo.
        "origin_x": shot / 2 - col0 * TILE,
        "origin_y": shot / 2 - row0 * TILE,
        "tile_block": [col0, row0, col1, row1],
    }
    # Una columna más al este, con el mismo origen: la expansión queda pegada a Vialia y la noria
    # (x≈4276 px) cae a 180 px del borde de la expansión.
    wide = {**expansion, "width": expansion["width"] + EXTRA_EAST_COLS * TILE}
    wide["tile_block"] = [col0, row0, col1 + EXTRA_EAST_COLS, row1]
    return {
        "$comment": "Generado por `python3 -m pipeline.render.params` desde pipeline/render/original/. No lo edites a mano.",
        "camera": {"sc": cam.sc, "tilt_deg": cam.tilt_deg, "head_deg": cam.head_deg},
        "geo": {
            "lat0": g.lat0,
            "lon0": g.lon0,
            "m_per_deg_lat": g.m_per_deg_lat,
            "m_per_deg_lon": g.m_per_deg_lon,
        },
        "ortho": ortho(),
        "tile": TILE,
        "canvases": {
            "3x3": {
                "width": shot,
                "height": shot,
                "origin_x": shot / 2,
                "origin_y": shot / 2,
            },
            "expansion": expansion,
            "wide": wide,
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="no escribe; falla si el JSON no coincide")
    args = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("render-params.json está desfasado: ejecuta `python3 -m pipeline.render.params`")
            return 1
        print("render-params.json al día")
        return 0
    OUT.write_text(text, encoding="utf-8")
    exp = doc["canvases"]["expansion"]
    print(f"escrito {OUT.relative_to(HERE.parent.parent)}")
    print(f"  cámara   {doc['camera']}")
    print(f"  origen   {doc['geo']['lat0']}, {doc['geo']['lon0']}")
    print(f"  ortofoto {doc['ortho']['half_m']} m  a {doc['ortho']['res_m']} m/px")
    print(f"  teselas  {exp['tile_block']} -> lienzo {exp['width']}x{exp['height']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
