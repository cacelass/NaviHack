"""Mezcla una ventana pintada centrada en una costura con el mapa publicado.
La ventana (1024 px) entra con una máscara suave: peso 1 a `--core` px de la costura, cae a 0 a `--fade` px;
en los extremos de la costura (`--taper-lo/--taper-hi`) también cae. Antes se ajusta su color (media y
desviación por canal) al mapa en la banda de la mascara. Fuera de la máscara el mapa no cambia ni un px.
Uso: python3 seam_window_blend.py base.png ventana.png out.png --origin X Y --axis v|h|x --core 48 --fade 200
     [--taper-lo N] [--taper-hi N]     (N = filas/columnas del borde de la ventana a fundir)
"""

import argparse

import numpy as np
from cv2 import GaussianBlur
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def ramp(n: int, centre: int, core: int, fade: int) -> np.ndarray:
    d = np.abs(np.arange(n) - centre).astype(np.float32)
    return np.clip((fade - d) / max(fade - core, 1), 0, 1)


def blend(base, win, ox, oy, axis, core, fade, t_lo, t_hi, clip=None):
    h, w = win.shape[:2]
    cx, cy = w // 2, h // 2
    if axis == "x":  # cruce de una costura V y una H: cruz con los cuatro bordes fundidos a t_lo px
        m = np.maximum(
            np.broadcast_to(ramp(w, cx, core, fade)[None, :], (h, w)),
            np.broadcast_to(ramp(h, cy, core, fade)[:, None], (h, w)),
        ).copy()
        e = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
        f = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
        m *= np.clip(np.minimum(e[None, :], f[:, None]) / max(t_lo, 1), 0, 1)
    elif axis == "v":
        m = np.broadcast_to(ramp(w, cx, core, fade)[None, :], (h, w)).copy()
        along = np.ones(h, np.float32)
        if t_lo:
            along[:t_lo] = np.linspace(0, 1, t_lo)
        if t_hi:
            along[h - t_hi :] = np.linspace(1, 0, t_hi)
        m *= along[:, None]
    else:
        m = np.broadcast_to(ramp(h, cy, core, fade)[:, None], (h, w)).copy()
        along = np.ones(w, np.float32)
        if t_lo:
            along[:t_lo] = np.linspace(0, 1, t_lo)
        if t_hi:
            along[w - t_hi :] = np.linspace(1, 0, t_hi)
        m *= along[None, :]
    if clip:  # (x0, y0, x1, y1) en el lienzo: la ventana solo cuenta dentro, con 40 px de fundido
        xs = np.arange(ox, ox + w)[None, :]
        ys = np.arange(oy, oy + h)[:, None]
        c = np.minimum(np.minimum(xs - clip[0], clip[2] - xs), np.minimum(ys - clip[1], clip[3] - ys))
        m *= np.clip(c / 40.0, 0, 1)
    m = GaussianBlur(m, (0, 0), 6)
    old = base[oy : oy + h, ox : ox + w]
    sel = m > 0.5
    mu_o, sd_o = old[sel].mean(0), old[sel].std(0) + 1e-3
    mu_w, sd_w = win[sel].mean(0), win[sel].std(0) + 1e-3
    adj = np.clip((win - mu_w) * (sd_o / sd_w) + mu_o, 0, 255)
    base[oy : oy + h, ox : ox + w] = old * (1 - m[..., None]) + adj * m[..., None]
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("window")
    ap.add_argument("out")
    ap.add_argument("--origin", type=int, nargs=2, required=True)
    ap.add_argument("--axis", choices=["v", "h", "x"], required=True)
    ap.add_argument("--core", type=int, default=48)
    ap.add_argument("--fade", type=int, default=200)
    ap.add_argument("--clip", type=int, nargs=4)
    ap.add_argument("--taper-lo", type=int, default=0)
    ap.add_argument("--taper-hi", type=int, default=0)
    o = ap.parse_args()
    base = np.asarray(Image.open(o.base).convert("RGB")).astype(np.float32)
    win = Image.open(o.window).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    m = blend(base, np.asarray(win).astype(np.float32), *o.origin, o.axis, o.core, o.fade, o.taper_lo, o.taper_hi, o.clip)
    Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(o.out)
    print("pixeles tocados:", int((m > 1e-3).sum()))
