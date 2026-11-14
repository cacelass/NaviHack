"""Assemble a 3x3 block of drawn 1024 px tiles into one exact 3072x3072 image, by code (no AI on the joins).

    python3 pipeline/assemble_block.py --tiles work/tiles-p3 --render ~/Downloads/vigo-bloque-3x3/render/render.png \
        --out work/base/p3-assembled.png [--flat-sea]

1. Colour matching: each tile is moved towards the centre tile in LAB (mean and std over built-up pixels).
2. Join blending: per seam, the colour step is measured along the seam and spread over BAND px on both sides
   as a smooth offset (structure is not moved, only the colour step is hidden).
3. Sea (optional): water pixels, taken from the render, are replaced by one flat colour with a soft edge.
4. Alignment check against the render: phase correlation of edge maps (offset in px) and water-mask IoU.
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
T = 1024
BAND = 96


def water_mask(render_rgb: np.ndarray) -> np.ndarray:
    """Agua por geometría, no por color: de la heurística de color nos quedamos solo
    con las componentes conectadas que tocan el borde superior (la ría al norte).
    Así las sombras de árboles y edificios, que son oscuras pero no tocan el mar,
    no cuentan como agua. El mar real es la componente conectada que llega al norte."""
    lum = render_rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    r, b = render_rgb[..., 0].astype(np.int32), render_rgb[..., 2].astype(np.int32)
    m = ((lum < 80) & (b >= r)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, labels = cv2.connectedComponents(m, connectivity=8)
    keep = np.zeros(n, dtype=bool)
    for lbl in np.unique(labels[0, :]):  # componentes que tocan el borde norte (mar abierto)
        if lbl > 0:
            keep[lbl] = True
    return keep[labels].astype(bool)


def to_lab(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)


def to_rgb(lab: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)


def match_colour(tile_lab: np.ndarray, tile_land: np.ndarray, ref_mean: np.ndarray, ref_std: np.ndarray) -> np.ndarray:
    if tile_land.sum() < 0.05 * tile_land.size:
        return tile_lab  # mostly sea: not enough built-up pixels to measure
    px = tile_lab[tile_land]
    mean, std = px.mean(axis=0), px.std(axis=0) + 1e-3
    gain = np.clip(ref_std / std, 0.8, 1.25)  # never stretch more than 25 %
    return (tile_lab - mean) * gain + ref_mean


def blend_seams(lab: np.ndarray, land: np.ndarray) -> np.ndarray:
    h, w, _ = lab.shape
    ramp = np.linspace(1, 0, BAND, dtype=np.float32)
    for axis in (1, 0):  # vertical seams first, then horizontal
        arr = lab if axis == 1 else lab.transpose(1, 0, 2)
        lnd = land if axis == 1 else land.T
        for k in (1, 2):
            x = k * T
            a = arr[:, x - 8:x].astype(np.float32)
            b = arr[:, x:x + 8].astype(np.float32)
            ok = (lnd[:, x - 8:x].all(axis=1) & lnd[:, x:x + 8].all(axis=1)).astype(np.float32)
            delta = b.mean(axis=1) - a.mean(axis=1)  # (rows, 3)
            wgt = cv2.GaussianBlur(ok[:, None], (0, 0), 24)
            delta = cv2.GaussianBlur(delta * ok[:, None], (0, 0), 24) / np.maximum(wgt, 1e-3)
            delta *= np.clip(wgt * 2, 0, 1)  # fade out where the seam runs over sea
            arr[:, x - BAND:x] += 0.5 * delta[:, None, :] * ramp[::-1][None, :, None]
            arr[:, x:x + BAND] -= 0.5 * delta[:, None, :] * ramp[None, :, None]
        if axis == 0:
            lab = arr.transpose(1, 0, 2)
    return lab


def edge_map(rgb: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.GaussianBlur(g, (0, 0), 2)
    return np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))


def alignment(out_rgb: np.ndarray, render_rgb: np.ndarray, wm: np.ndarray) -> dict:
    a, b = edge_map(render_rgb), edge_map(out_rgb)
    win = cv2.createHanningWindow(a.shape[::-1], cv2.CV_32F)
    (dx, dy), resp = cv2.phaseCorrelate(a.astype(np.float32), b.astype(np.float32), win)
    ow = water_mask(out_rgb)
    iou = float((ow & wm).sum() / max((ow | wm).sum(), 1))
    return {"offset_px": [round(float(dx), 2), round(float(dy), 2)], "phase_response": round(float(resp), 3), "water_mask_iou": round(iou, 3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--flat-sea", action="store_true")
    ap.add_argument("--no-blend", action="store_true")
    a = ap.parse_args()

    render = np.asarray(Image.open(a.render).convert("RGB"))
    wm = water_mask(render)
    canvas = np.zeros((3 * T, 3 * T, 3), np.float32)
    for r in range(3):
        for c in range(3):
            canvas[r * T:(r + 1) * T, c * T:(c + 1) * T] = to_lab(np.asarray(Image.open(f"{a.tiles}/draw_r{r}c{c}.png").convert("RGB").resize((T, T), Image.LANCZOS)))
    land = ~wm
    centre = (slice(T, 2 * T), slice(T, 2 * T))
    px = canvas[centre][land[centre]]
    ref_mean, ref_std = px.mean(axis=0), px.std(axis=0)
    for r in range(3):
        for c in range(3):
            if (r, c) == (1, 1):
                continue
            s = (slice(r * T, (r + 1) * T), slice(c * T, (c + 1) * T))
            canvas[s] = match_colour(canvas[s], land[s], ref_mean, ref_std)
    if not a.no_blend:
        canvas = blend_seams(canvas, land)
    out = to_rgb(canvas)
    if a.flat_sea:
        # mar con gradiente (más claro junto a la costa, profundo al norte) y orilla de arena
        sea_deep = np.array([27, 41, 59], np.float32)
        sea_near = np.array([52, 78, 100], np.float32)
        dist = cv2.distanceTransform((~wm).astype(np.uint8), cv2.DIST_L2, 3)
        dmax = dist.max() + 1e-3
        t = np.clip(dist / (dmax * 0.5), 0, 1)[..., None]
        grad = sea_near[None, None, :] * (1 - t) + sea_deep[None, None, :] * t
        ripple = (np.sin(np.arange(out.shape[0])[:, None] * 0.02) * 3).astype(np.float32)[..., None]
        grad = np.clip(grad + ripple, 0, 255)
        erode = cv2.erode(wm.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)
        shore = cv2.dilate((wm.astype(np.uint8) - erode), np.ones((3, 3), np.uint8), iterations=2).astype(bool)
        sand = np.array([205, 188, 156], np.float32)
        soft = cv2.GaussianBlur(wm.astype(np.float32), (0, 0), 2.0)[..., None]
        out = (out * (1 - soft) + grad * soft).astype(np.float32)
        out = np.where(shore[..., None], sand * 0.9 + grad * 0.1, out)
        out = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(a.out)
    print("saved", a.out, out.shape, alignment(out, render, wm))


if __name__ == "__main__":
    main()
