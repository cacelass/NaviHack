"""Mide el origen geográfico del lienzo con una fuente independiente: el mar del MDT05 del IGN.

La georreferencia (`pipeline/georef.py`) toma el origen y la cámara del renderer. Eso no demuestra que estén
bien: el renderer pudo haberse montado con un origen equivocado. Aquí se contrasta con algo que no sale de
ningún render: el MDT05 (`data/elevation/mdt05_core.asc.gz`, paso de 5 m) pone el mar a 0,0 m exactos. Se
proyecta esa máscara de mar sobre el lienzo con nuestra transformación y se busca el desplazamiento que mejor
la hace coincidir con el agua del render.

* **Desplazamiento (dx, dy)**: cuánto hay que mover nuestra proyección, en píxeles del lienzo, para que caiga
  sobre el agua del render. Se convierte a metros de suelo (este, norte). Con una costa larga se obtiene
  precisión de una fracción de píxel aunque la celda del MDT05 mida 3,7 x 5 m (7 x 7 px).
* **Mitades**: se repite en la mitad oeste y en la este de la zona cubierta. Si el error es solo de origen, las
  dos mitades dan el mismo desplazamiento; si difieren, hay un error de escala o de giro de la cámara.
* **IoU** (intersección sobre unión del mar) con y sin el desplazamiento.

    python3 -m pipeline.render.calibrate_origin --render work/render-wide/render.png --canvas wide
    python3 -m pipeline.render.calibrate_origin --render ~/Downloads/vigo-bloque-3x3/render/render.png --canvas 3x3

No llama a ningún modelo. Necesita numpy y OpenCV.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from pipeline import georef
from pipeline.render.port_fix import get_water
from scripts import elevation

Image.MAX_IMAGE_PIXELS = None
SEA_M = 1.0  # m. El MDT05 marca el mar con 0,0 exactos; los muelles están a 2-3 m. 1,0 m pone el contorno a medio camino
SWEEP = (0.5, 1.0, 1.5, 2.0)  # umbrales para comprobar que el resultado no depende de esa elección
CHUNK = 256  # filas del lienzo que se procesan de una vez (memoria)


def dem_array(grid: elevation.Grid) -> np.ndarray:
    """La rejilla del MDT05 como array (fila 0 = norte). Sin NODATA en este recorte."""
    return np.array(
        [[np.nan if v is None else v for v in row] for row in grid.rows], dtype=np.float32
    )


def sea_on_canvas(
    params: georef.RenderParams,
    grid: elevation.Grid,
    dem: np.ndarray,
    canvas: str,
    box: tuple[int, int, int, int],
    threshold: float = SEA_M,
) -> tuple[np.ndarray, np.ndarray]:
    """(mar, válido) del MDT05 proyectados en la caja ``box`` = (x0, y0, x1, y1) del lienzo.

    Recorrido inverso: para cada píxel se calcula su (lat, lon) en el suelo (z = 0, como el renderer) y se
    interpola la cota del MDT05 (bilineal entre centros de celda, como ``Grid.elevation``): el contorno de
    ``threshold`` metros tiene precisión sub-celda, en vez de los escalones de 7 px de «la celda más cercana».
    «Válido» es lo que cae donde las cuatro celdas vecinas existen; fuera no se sabe si es mar.
    """
    x0, y0, x1, y1 = box
    sea = np.zeros((y1 - y0, x1 - x0), np.uint8)
    valid = np.zeros_like(sea)
    top = grid.yll + grid.nrows * grid.dy
    xs = np.arange(x0, x1, dtype=np.float64) + 0.5  # centros de píxel
    for r0 in range(y0, y1, CHUNK):
        r1 = min(r0 + CHUNK, y1)
        py = (np.arange(r0, r1, dtype=np.float64) + 0.5)[:, None]
        lat, lon = params.to_latlon(xs[None, :] + 0 * py, py + 0 * xs[None, :], 0.0, canvas)
        col = (lon - grid.xll) / grid.dx - 0.5
        row = (top - lat) / grid.dy - 0.5
        j0 = np.floor(col).astype(np.int64)
        i0 = np.floor(row).astype(np.int64)
        fx = (col - j0).astype(np.float32)
        fy = (row - i0).astype(np.float32)
        ok = (i0 >= 0) & (i0 + 1 < grid.nrows) & (j0 >= 0) & (j0 + 1 < grid.ncols)
        elev = np.full(lat.shape, np.inf, np.float32)
        i, j, u, v = i0[ok], j0[ok], fx[ok], fy[ok]
        elev[ok] = (
            dem[i, j] * (1 - u) * (1 - v)
            + dem[i, j + 1] * u * (1 - v)
            + dem[i + 1, j] * (1 - u) * v
            + dem[i + 1, j + 1] * u * v
        )
        sea[r0 - y0 : r1 - y0] = elev <= threshold
        valid[r0 - y0 : r1 - y0] = ok
    return sea.astype(bool), valid.astype(bool)


@dataclass(frozen=True)
class Shift:
    dx: float  # px del lienzo
    dy: float
    iou_zero: float
    iou_best: float
    n_sea: int


def best_shift(sea: np.ndarray, valid: np.ndarray, water: np.ndarray, search: int = 24) -> Shift:
    """Desplazamiento (dx, dy) de ``sea`` sobre ``water`` que maximiza el IoU dentro de la zona válida.

    ``water`` debe tener ``search`` px de margen alrededor de ``sea`` (misma caja ampliada). La correlación
    cruzada se hace con matchTemplate (DFT), y el IoU se calcula en todos los desplazamientos a la vez:
    inter = corr(agua, mar); unión = |mar| + corr(agua, válido) - inter. Con refinamiento parabólico.
    """
    h, w = sea.shape
    s = search
    if water.shape != (h + 2 * s, w + 2 * s):
        raise ValueError(f"water debe medir {(h + 2 * s, w + 2 * s)}, mide {water.shape}")
    img = water.astype(np.float32)
    inter = cv2.matchTemplate(img, sea.astype(np.float32), cv2.TM_CCORR)
    cover = cv2.matchTemplate(img, valid.astype(np.float32), cv2.TM_CCORR)
    union = float(sea.sum()) + cover - inter
    iou = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
    iy, ix = np.unravel_index(int(np.argmax(iou)), iou.shape)

    def refine(m1: float, m0: float, p1: float) -> float:
        den = m1 - 2 * m0 + p1
        return 0.0 if abs(den) < 1e-12 else 0.5 * (m1 - p1) / den

    fx = refine(iou[iy, ix - 1], iou[iy, ix], iou[iy, ix + 1]) if 0 < ix < iou.shape[1] - 1 else 0.0
    fy = refine(iou[iy - 1, ix], iou[iy, ix], iou[iy + 1, ix]) if 0 < iy < iou.shape[0] - 1 else 0.0
    return Shift(
        dx=float(ix - s + fx),
        dy=float(iy - s + fy),
        iou_zero=float(iou[s, s]),
        iou_best=float(iou[iy, ix]),
        n_sea=int(sea.sum()),
    )


def ground_metres(
    params: georef.RenderParams, canvas: str, at: tuple[float, float], d: Shift
) -> tuple[float, float]:
    """Un desplazamiento de píxeles del lienzo, en metros de suelo (este, norte)."""
    x0, y0 = params.to_metres(at[0], at[1], 0.0, canvas)
    x1, y1 = params.to_metres(at[0] + d.dx, at[1] + d.dy, 0.0, canvas)
    return float(x1 - x0), float(y1 - y0)


def measure(
    params: georef.RenderParams,
    grid: elevation.Grid,
    water_full: np.ndarray,
    canvas: str,
    search: int = 24,
    threshold: float = SEA_M,
) -> dict:
    """Todo el contraste sobre un lienzo: global y por mitades (oeste/este) de la zona cubierta."""
    c = params.canvas(canvas)
    dem = dem_array(grid)
    # caja del lienzo que cubre el MDT05: se proyectan las cuatro esquinas del recorte
    top = grid.yll + grid.nrows * grid.dy
    east = grid.xll + grid.ncols * grid.dx
    px = []
    py = []
    for lat in (grid.yll, top):
        for lon in (grid.xll, east):
            x, y = params.to_pixel(lat, lon, 0.0, canvas)
            px.append(x)
            py.append(y)
    box = (
        max(int(min(px)) - 4, search),
        max(int(min(py)) - 4, search),
        min(int(max(px)) + 4, c.width - search),
        min(int(max(py)) + 4, c.height - search),
    )
    sea, valid = sea_on_canvas(params, grid, dem, canvas, box, threshold)
    x0, y0, x1, y1 = box
    out: dict = {"canvas": canvas, "box": list(box), "search_px": search, "threshold_m": threshold}

    def run(mask_sea: np.ndarray, mask_valid: np.ndarray, bx: tuple[int, int, int, int]) -> dict:
        a, b, e, f = bx
        w = water_full[b - search : f + search, a - search : e + search]
        r = best_shift(mask_sea, mask_valid, w, search)
        centre = ((a + e) / 2, (b + f) / 2)
        east_m, north_m = ground_metres(params, canvas, centre, r)
        return {
            "dx_px": round(r.dx, 2),
            "dy_px": round(r.dy, 2),
            "east_m": round(east_m, 2),
            "north_m": round(north_m, 2),
            "error_m": round(float(np.hypot(east_m, north_m)), 2),
            "iou_without_shift": round(r.iou_zero, 4),
            "iou_with_shift": round(r.iou_best, 4),
            "sea_px": r.n_sea,
            # si el máximo cae en el borde de la búsqueda, el desplazamiento no está determinado
            # (costa demasiado recta: el problema de la apertura)
            "determinate": bool(abs(r.dx) < search - 1 and abs(r.dy) < search - 1),
        }

    out["all"] = run(sea, valid, box)
    xm = (x0 + x1) // 2
    out["west"] = run(sea[:, : xm - x0], valid[:, : xm - x0], (x0, y0, xm, y1))
    out["east"] = run(sea[:, xm - x0 :], valid[:, xm - x0 :], (xm, y0, x1, y1))
    out["halves_disagree_px"] = round(
        float(
            np.hypot(
                out["west"]["dx_px"] - out["east"]["dx_px"],
                out["west"]["dy_px"] - out["east"]["dy_px"],
            )
        ),
        2,
    )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--render", type=Path, required=True, help="render del lienzo (PNG)")
    ap.add_argument(
        "--canvas", default="wide", help="3x3, expansion o wide: el que corresponde al PNG"
    )
    ap.add_argument("--search", type=int, default=24, help="px de búsqueda a cada lado")
    ap.add_argument("--sweep", action="store_true", help="repite con varios umbrales de mar")
    ap.add_argument("--json", type=Path, help="guarda el resultado")
    args = ap.parse_args(argv)

    params = georef.params()
    grid = elevation.load()
    if grid is None:
        raise SystemExit("falta data/elevation/mdt05_core.asc.gz")
    render = np.asarray(Image.open(args.render).convert("RGB"))
    c = params.canvas(args.canvas)
    if render.shape[:2] != (c.height, c.width):
        raise SystemExit(
            f"el render mide {render.shape[1]}x{render.shape[0]} y el lienzo {args.canvas} {c.width}x{c.height}"
        )
    water = get_water(render)
    runs = [
        measure(params, grid, water, args.canvas, args.search, th)
        for th in (SWEEP if args.sweep else (SEA_M,))
    ]
    for res in runs:
        print(f"-- umbral de mar {res['threshold_m']} m")
        for k in ("all", "west", "east"):
            r = res[k]
            flag = "" if r["determinate"] else "   (INDETERMINADO: toca el límite de búsqueda)"
            print(
                f"{k:5s} ({r['dx_px']:+6.2f}, {r['dy_px']:+6.2f}) px = {r['east_m']:+5.2f} m este, "
                f"{r['north_m']:+5.2f} m norte (error {r['error_m']:.2f} m) | IoU {r['iou_without_shift']:.3f} -> {r['iou_with_shift']:.3f}{flag}"
            )
    res = {"render": args.render.name, "runs": runs}
    if args.json:
        args.json.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
        print(f"escrito {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
