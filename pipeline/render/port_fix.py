"""Pone una ventana pintada del puerto en el mapa final, sin tocar el resto.

El puerto de v6 está roto (ver harness/progress/zona-vialia-hallazgo-puerto.md): la tesela r0c1 casi
no tiene tierra, así que pintada sola el modelo hace zoom e inventa. Se pinta en cambio una ventana
de 1024 px a caballo entre las filas 0 y 1 (muelle y dársena arriba, ciudad abajo) y esto la integra:

1. Colores: la ventana se lleva a la media y desviación (LAB, solo tierra) de una zona limpia del mapa.
2. Mar por código: el agua de la ventana, la del render, se sustituye por el mismo mar que genera
   ``assemble_block`` (degradado por distancia a la costa + ruido), ajustado al mar limpio del mapa.
   Lo que no es agua (muelles, barcos, espigones) se conserva del dibujo.
3. Fundido: la ventana entra con un degradado en los bordes, que es donde luego se rehacen costuras.

    python3 -m pipeline.render.port_fix --base work/tiles-p3/ensamblado-v10.png \\
        --render ~/Downloads/vigo-bloque-3x3/render/render.png \\
        --window work/puerto/draw_ventana_1.png --out work/puerto/v11.png

No llama a ningún modelo.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemble_block import to_lab, to_rgb, water_mask, water_texture  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
SIZE = 1024
CACHE = Path("/tmp/opencode/port_fix_cache")
SEA_DEEP = np.array([27, 41, 59], np.float32)  # los de assemble_block --flat-sea
SEA_NEAR = np.array([52, 78, 100], np.float32)
# Zona limpia del mapa para medir color de tierra (centro del bloque, debajo del parche roto).
REF_LAND = (1024, 1700, 2048, 2500)
# Mar limpio del mapa (arriba a la izquierda, lejos de cualquier costa) para ajustar el mar por código.
REF_SEA = (60, 60, 700, 560)


def get_water(render: np.ndarray) -> np.ndarray:
    """``water_mask`` con caché en disco (clave: contenido del render), porque pesa y se repite."""
    key = hashlib.md5(render.tobytes()).hexdigest()[:16]
    path = CACHE / f"agua_{key}.npy"
    if path.exists():
        return np.load(path)
    wm = water_mask(render)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(path, wm)
    return wm


def sea_layer(wm: np.ndarray) -> np.ndarray:
    """El mar de ``assemble_block --flat-sea`` (sin orilla de arena), para todo el lienzo."""
    dist = cv2.distanceTransform((~wm).astype(np.uint8), cv2.DIST_L2, 3)
    t = np.clip(dist / (dist.max() * 0.5 + 1e-3), 0, 1)[..., None]
    grad = SEA_NEAR * (1 - t) + SEA_DEEP * t
    return np.clip(grad + water_texture(wm.shape)[..., None], 0, 255)


def fit_to_base(layer: np.ndarray, base: np.ndarray) -> np.ndarray:
    """Ajusta el mar por código al que ya tiene el mapa (que pasó por los filtros finales)."""
    x0, y0, x1, y1 = REF_SEA
    out = np.empty_like(layer)
    for ch in range(3):
        a, b = np.polyfit(layer[y0:y1, x0:x1, ch].ravel(), base[y0:y1, x0:x1, ch].ravel(), 1)
        out[..., ch] = layer[..., ch] * a + b
    return np.clip(out, 0, 255)


def extend(base: np.ndarray, render: np.ndarray) -> np.ndarray:
    """Amplía el mapa hasta el tamaño del render; lo nuevo empieza siendo mar por código."""
    h, w = render.shape[:2]
    if base.shape[:2] == (h, w):
        return base
    sea = fit_to_base(sea_layer(get_water(render)), base.astype(np.float32))
    out = np.clip(sea, 0, 255).astype(np.uint8)
    out[: base.shape[0], : base.shape[1]] = base
    return out


def match_land(
    window: np.ndarray, base: np.ndarray, wm: np.ndarray, origin: tuple[int, int]
) -> np.ndarray:
    """Lleva el color de tierra de la ventana al del mapa (media y desviación en LAB)."""
    ox, oy = origin
    x0, y0, x1, y1 = REF_LAND
    ref = to_lab(base[y0:y1, x0:x1])[~wm[y0:y1, x0:x1]]
    lab = to_lab(window)
    own = lab[~wm[oy : oy + SIZE, ox : ox + SIZE]]
    gain = np.clip((ref.std(axis=0)) / (own.std(axis=0) + 1e-3), 0.8, 1.25)
    return to_rgb((lab - own.mean(axis=0)) * gain + ref.mean(axis=0))


def feather(
    feather_px: int,
    oy: int,
    fade: tuple[int, int],
    cut_top: int = 0,
    hard_right: bool = False,
    hard_left: bool = False,
) -> np.ndarray:
    """1 dentro, bajando a 0 en los bordes de la ventana.

    Izquierda, derecha y arriba usan ``feather_px``. Abajo el degradado va de la fila ``fade[0]`` a la
    ``fade[1]`` del lienzo (no del borde de la ventana): tiene que acabar por encima del árbol de Porta
    do Sol, que está pintado en el mapa y la ventana no tiene.
    """
    ramp = np.clip(np.arange(SIZE) / feather_px, 0, 1)
    if hard_left and hard_right:
        across = np.ones(SIZE, np.float32)
    elif hard_left:
        across = ramp[::-1]
    elif hard_right:
        across = ramp
    else:
        across = np.minimum(ramp, ramp[::-1])
    rows = np.arange(oy, oy + SIZE)
    down = np.clip((fade[1] - rows) / max(fade[1] - fade[0], 1), 0, 1)
    top = np.clip((np.arange(SIZE) - cut_top) / feather_px, 0, 1)
    return np.minimum.outer(np.minimum(top, down), across)


def compose(
    base: np.ndarray,
    render: np.ndarray,
    window: np.ndarray,
    origin: tuple[int, int],
    feather_px: int,
    edge_soft: float,
    fade: tuple[int, int],
    cut_top: int = 0,
    hard_right: bool = False,
    hard_left: bool = False,
) -> np.ndarray:
    ox, oy = origin
    wm = get_water(render)
    win = np.asarray(Image.fromarray(window).resize((SIZE, SIZE), Image.LANCZOS))
    win = match_land(win, base, wm, origin).astype(np.float32)

    sea = fit_to_base(sea_layer(wm), base.astype(np.float32))[oy : oy + SIZE, ox : ox + SIZE]
    water = cv2.GaussianBlur(
        wm[oy : oy + SIZE, ox : ox + SIZE].astype(np.float32), (0, 0), edge_soft
    )[..., None]
    piece = win * (1 - water) + sea * water

    alpha = feather(feather_px, oy, fade, cut_top, hard_right, hard_left)[..., None]
    out = base.astype(np.float32).copy()
    region = out[oy : oy + SIZE, ox : ox + SIZE]
    out[oy : oy + SIZE, ox : ox + SIZE] = region * (1 - alpha) + piece * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def drop_floaters(
    base: np.ndarray, render: np.ndarray, min_dist: int = 45, max_area: int = 2000
) -> tuple[np.ndarray, list[tuple[int, int, int]]]:
    """Quita trozos sueltos de tierra que flotan en el mar y devuelve cuáles (cx, cy, área).

    Un trozo es «suelto» si en el render su tierra es pequeña (``max_area``) y queda a más de
    ``min_dist`` px de la tierra firme. Se pintan con el mismo mar por código, con borde suave.
    """
    wm = get_water(render)
    land = (~wm).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(land, connectivity=8)
    big = np.isin(lab, [i for i in range(1, n) if st[i, 4] > 20000])
    dist = cv2.distanceTransform((~big).astype(np.uint8), cv2.DIST_L2, 3)
    drop = np.zeros(wm.shape, np.uint8)
    found = []
    for i in range(1, n):
        cx, cy = cen[i]
        if st[i, 4] > max_area or big[lab == i].any() or dist[int(cy), int(cx)] < min_dist:
            continue
        drop[lab == i] = 1
        found.append((int(cx), int(cy), int(st[i, 4])))
    if not found:
        return base, found
    # el hueco incluye el halo de arena del mapa, por eso se agranda
    soft = cv2.GaussianBlur(
        cv2.dilate(drop, np.ones((15, 15), np.uint8)).astype(np.float32), (0, 0), 2.0
    )
    sea = fit_to_base(sea_layer(wm | (drop > 0)), base.astype(np.float32))
    out = base.astype(np.float32) * (1 - soft[..., None]) + sea * soft[..., None]
    return np.clip(out, 0, 255).astype(np.uint8), found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--base", type=Path, required=True, help="mapa final 3072x3072")
    ap.add_argument("--render", type=Path, required=True, help="render del 3x3 (3072x3072)")
    ap.add_argument("--window", type=Path, required=True, help="ventana pintada de 1024 px")
    ap.add_argument("--origin", type=int, nargs=2, default=(1024, 640), metavar=("X", "Y"))
    ap.add_argument("--feather", type=int, default=64)
    ap.add_argument(
        "--fade",
        type=int,
        nargs=2,
        default=(1180, 1340),
        metavar=("Y0", "Y1"),
        help="filas del lienzo donde la ventana se funde por abajo",
    )
    ap.add_argument(
        "--edge-soft", type=float, default=1.0, help="desenfoque (px) de la orilla del agua"
    )
    ap.add_argument(
        "--cut-top", type=int, default=0, help="filas de la ventana (desde arriba) que NO se usan"
    )
    ap.add_argument(
        "--hard-right",
        action="store_true",
        help="sin degradado en el borde derecho (borde del lienzo)",
    )
    ap.add_argument(
        "--hard-left",
        action="store_true",
        help="sin degradado en el borde izquierdo (borde del lienzo)",
    )
    ap.add_argument(
        "--extend", action="store_true", help="amplía el mapa al tamaño del render (4096x3072)"
    )
    ap.add_argument(
        "--drop-floaters", action="store_true", help="quita trozos de tierra sueltos en el mar"
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    base = np.asarray(Image.open(args.base).convert("RGB"))
    render = np.asarray(Image.open(args.render).convert("RGB"))
    if not args.extend:
        render = render[:3072, :3072]
    base = extend(base, render)
    window = np.asarray(Image.open(args.window).convert("RGB"))
    out = compose(
        base,
        render,
        window,
        tuple(args.origin),
        args.feather,
        args.edge_soft,
        tuple(args.fade),
        args.cut_top,
        args.hard_right,
        args.hard_left,
    )
    if args.drop_floaters:
        out, found = drop_floaters(out, render)
        print(f"quitados {len(found)} trozos sueltos: {found}")
    Image.fromarray(out).save(args.out)
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
