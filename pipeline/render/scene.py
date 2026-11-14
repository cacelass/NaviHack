"""Prepara la escena del render ampliado: edificios, capas de ortofoto y páginas.

Escribe en una carpeta de trabajo todo lo que necesita el navegador para pintar
el lienzo de la expansión con el mismo renderer del 3x3:

    work/render-expansion/
      params.js    lienzo, cámara y capas de ortofoto (metros, sin grados)
      data.js      edificios del Concello en metros desde Porta do Sol
      render.html  el render
      height.html  mapa de alturas
      ids.html     qué edificio se ve en cada píxel

    python3 -m pipeline.render.scene --out work/render-expansion

Los edificios se filtran igual que en ``original/build-data.mjs`` (regla y
redondeos) pero con una caja algo mayor, así que los que ya estaban salen
idénticos y los nuevos se añaden al final del recorrido del fichero fuente.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from pipeline import georef
from pipeline.render import fetch_ortho

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
MARGIN_M = 30.0


def buildings(params: georef.RenderParams, bounds: tuple[float, float, float, float]) -> list[dict]:
    """Los edificios que tocan el lienzo, en metros y con los redondeos del 3x3."""
    x_min, y_min, x_max, y_max = bounds
    source = json.loads((HERE / "original" / "edificios_concello.json").read_text(encoding="utf-8"))
    east = HERE / "original" / "edificios_este.json"
    if east.exists():
        # Los del 3x3 van primero y en su orden: así la zona ya pintada sale igual.
        seen = {b["r"] for b in source if b.get("r")}
        source += [
            b
            for b in json.loads(east.read_text(encoding="utf-8"))
            if not b.get("r") or b["r"] not in seen
        ]
    out: list[dict] = []
    for raw in source:
        ring = [
            [
                _js_round((lon - params.geo.lon0) * params.geo.m_per_deg_lon),
                _js_round((lat - params.geo.lat0) * params.geo.m_per_deg_lat),
            ]
            for lon, lat in raw["rings"][0]
        ]
        if not any(x_min <= x <= x_max and y_min <= y <= y_max for x, y in ring):
            continue
        out.append({"h": max(3, raw.get("h") or 6), "p": ring})
    return out


def _js_round(value: float) -> float:
    """``+v.toFixed(2)`` de JavaScript: 2 decimales, entero y sin ``-0``."""
    out = float(f"{value:.2f}") + 0.0
    if out == int(out):
        return int(out)
    return 0.0 if out == 0 else out


def layers(out: Path) -> list[dict]:
    """Capas de ortofoto en orden de dibujo: primero las nuevas, la vieja encima."""
    ortho = out / "ortho"
    old_half = json.loads((HERE / "render-params.json").read_text(encoding="utf-8"))["ortho"][
        "half_m"
    ]
    result = []
    for sidecar in sorted(ortho.glob("new_*.json")):
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        result.append(
            {
                "src": f"ortho/{sidecar.with_suffix('.jpg').name}",
                "x0": meta["x0"],
                "y0": meta["y0"],
                "dx": meta["res"],
                "dy": meta["res"],
                "w": meta["width"],
                "h": meta["height"],
            }
        )
    result.append(
        {
            "src": "ortho/old.jpg",
            "x0": -float(old_half[0]),
            "y0": float(old_half[1]),
            "dx": 2 * float(old_half[0]) / 5500,
            "dy": 2 * float(old_half[1]) / 6800,
            "w": 5500,
            "h": 6800,
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    params = georef.params()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    gx0, gy0, gx1, gy1 = fetch_ortho.canvas_ground(params)
    # La caja del 3x3 se mantiene entera: si se recortara a lo que se ve, un
    # edificio alto de fuera del borde podría dejar de tapar lo que tapaba.
    old_half = json.loads((HERE / "render-params.json").read_text(encoding="utf-8"))["ortho"][
        "half_m"
    ]
    bounds = (
        min(-float(old_half[0]), gx0 - MARGIN_M),
        min(-float(old_half[1]), gy0 - MARGIN_M),
        max(float(old_half[0]), gx1 + MARGIN_M),
        max(float(old_half[1]), gy1 + MARGIN_M),
    )
    bs = buildings(params, bounds)

    canvas = params.canvas("expansion")
    scene = {
        "width": canvas.width,
        "height": canvas.height,
        "ox": canvas.origin_x,
        "oy": canvas.origin_y,
        "sc": params.camera.sc,
        "tiltDeg": params.camera.tilt_deg,
        "headDeg": params.camera.head_deg,
        "layers": layers(out),
    }
    (out / "params.js").write_text(
        "const SCENE=" + json.dumps(scene, separators=(",", ":")) + ";\n", encoding="utf-8"
    )
    (out / "data.js").write_text(
        "const DATA=" + json.dumps({"B": bs}, separators=(",", ":")) + ";\n", encoding="utf-8"
    )
    for name in ("render", "height", "ids"):
        shutil.copyfile(TEMPLATES / f"{name}.html", out / f"{name}.html")

    old = _old_buildings_count(params)
    print(f"{len(bs)} edificios ({len(bs) - old} nuevos respecto al 3x3)")
    print(f"lienzo {canvas.width}x{canvas.height} · {len(scene['layers'])} capas de ortofoto")
    print(f"escena en {out}")
    return 0


def _old_buildings_count(params: georef.RenderParams) -> int:
    from pipeline.render import silhouette

    return len(silhouette.load_buildings(params))


if __name__ == "__main__":
    sys.exit(main())
