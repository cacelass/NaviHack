"""Quita la viñeta que el modelo deja a veces en el borde derecho del lienzo.

En una ventana pintada (la del muelle norte) los últimos ~70 px del borde derecho salen mucho más
oscuros y azulados que el render: brillo al 60 % en los 16 px del borde, al 90 % a 60 px. No es contenido,
es el modelo. Aquí se mide ese desvío y se deshace:

* Se compara, por distancia al borde, el brillo (L) y el azul (b*) del dibujo con los del **render** (la
  misma escena, así que el contenido se cancela) solo con píxeles de tierra y relativos a una franja
  interior sin problema.
* La corrección es solo hacia arriba (nunca oscurece) y monótona con la distancia: más fuerte en el borde.
* Se aplica a las filas ``rows`` con un fundido vertical para no dejar una línea horizontal.

    python3 -m pipeline.render.edge_fix --base work/estilo/v17.png --render work/render-wide/render.png \\
        --rows 0 1000 --out work/estilo/v17c.png

No llama a ningún modelo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from pipeline.render.port_fix import get_water

Image.MAX_IMAGE_PIXELS = None
STEP = 8  # px por tramo de distancia al borde
MAX_GAIN = 1.9
MAX_SHIFT_B = 40.0
STRENGTH = 0.8


def _lab(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)


def measure(
    paint: np.ndarray,
    render: np.ndarray,
    land: np.ndarray,
    rows: tuple[int, int],
    width: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(distancias, ganancia de L, desplazamiento de a*, desplazamiento de b*) por tramos de ``STEP`` px."""
    p, r = _lab(paint), _lab(render)
    w = land.shape[1]
    y0, y1 = rows

    def band(d0: int, d1: int) -> tuple[float, ...] | None:
        sl = (slice(y0, y1), slice(w - d1, w - d0))
        m = land[sl]
        if m.sum() < 400:
            return None
        return (
            float(p[sl][m][:, 0].mean()),
            float(r[sl][m][:, 0].mean()),
            float(p[sl][m][:, 2].mean()) - 128,
            float(r[sl][m][:, 2].mean()) - 128,
            float(p[sl][m][:, 1].mean()) - 128,
            float(r[sl][m][:, 1].mean()) - 128,
        )

    ref = band(width + 40, width + 160)
    if ref is None:
        raise ValueError("no hay tierra suficiente en la franja de referencia")
    centres, gain, shift, shift_a = [], [], [], []
    for d0 in range(0, width, STEP):
        b = band(d0, d0 + STEP)
        centres.append(d0 + STEP / 2)
        if b is None:
            gain.append(1.0)
            shift.append(0.0)
            shift_a.append(0.0)
            continue
        ratio = (b[0] / b[1]) / (ref[0] / ref[1])
        gain.append(float(np.clip(1.0 / ratio, 1.0, MAX_GAIN)))
        shift.append(float(np.clip(-((b[2] - b[3]) - (ref[2] - ref[3])), 0.0, MAX_SHIFT_B)))
        shift_a.append(
            float(np.clip(-((b[4] - b[5]) - (ref[4] - ref[5])), -MAX_SHIFT_B, MAX_SHIFT_B))
        )
    # monótono: nunca menos corrección más cerca del borde que más lejos, y suavizado
    g = np.maximum.accumulate(np.array(gain)[::-1])[::-1]
    s = np.maximum.accumulate(np.array(shift)[::-1])[::-1]
    k = np.ones(3) / 3
    g = np.convolve(np.pad(g, 1, mode="edge"), k, mode="valid")
    s = np.convolve(np.pad(s, 1, mode="edge"), k, mode="valid")
    sa = np.convolve(np.pad(np.array(shift_a), 1, mode="edge"), k, mode="valid")
    return np.array(centres), g, sa, s


def fix_right_edge(
    img: np.ndarray,
    render: np.ndarray,
    land: np.ndarray,
    rows: tuple[int, int],
    width: int = 110,
    y_fade: int = 80,
    measure_rows: tuple[int, int] | None = None,
    strength: float = STRENGTH,
) -> tuple[np.ndarray, dict]:
    """Devuelve (imagen corregida, perfil medido)."""
    mr = measure_rows or (rows[0] + 60, rows[1] - 70)
    d, g, sa, s = measure(img, render, land, mr, width)
    g = (
        1 + (g - 1) * strength
    )  # no se corrige del todo: un borde algo más oscuro es natural, uno hundido no
    sa, s = sa * strength, s * strength
    h, w = img.shape[:2]
    y0, y1 = rows
    out = _lab(img)
    xs = np.arange(w - width, w)
    dist = (w - 1 - xs).astype(np.float32)
    gain = np.interp(dist, d, g, right=1.0)[None, :]
    shift = np.interp(dist, d, s, right=0.0)[None, :]
    shift_a = np.interp(dist, d, sa, right=0.0)[None, :]
    wy = np.clip((y1 - np.arange(y0, y1)) / max(y_fade, 1), 0.0, 1.0)[:, None]
    region = out[y0:y1, w - width :]
    region[..., 0] = region[..., 0] * (1 + (gain - 1) * wy)
    region[..., 1] = region[..., 1] + shift_a * wy
    region[..., 2] = region[..., 2] + shift * wy
    fixed = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    return fixed, {
        "dist": d.tolist(),
        "gain": g.tolist(),
        "shift_a": sa.tolist(),
        "shift_b": s.tolist(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--render", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rows", type=int, nargs=2, default=(0, 1000), metavar=("Y0", "Y1"))
    ap.add_argument("--width", type=int, default=110)
    args = ap.parse_args(argv)
    img = np.asarray(Image.open(args.base).convert("RGB"))
    render = np.asarray(Image.open(args.render).convert("RGB"))
    out, prof = fix_right_edge(img, render, ~get_water(render), tuple(args.rows), args.width)
    Image.fromarray(out).save(args.out)
    print("distancia (px) -> ganancia L / desplazamiento a* / desplazamiento b*:")
    for d, g, a, s in zip(
        prof["dist"], prof["gain"], prof["shift_a"], prof["shift_b"], strict=True
    ):
        if g > 1.01 or abs(a) > 0.5 or s > 0.5:
            print(f"  {d:5.0f}   x{g:4.2f}   {a:+5.1f}   {s:+5.1f}")
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
