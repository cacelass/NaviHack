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
    """Agua por geometría, no por un umbral de color aislado: de la heurística de color (oscuro y
    azulado) nos quedamos con dos tipos de componente conectada:
    1. La que toca el borde norte (la ría abierta), que es el filtro original.
    2. Diques o dársenas cerradas que un barco o un muelle estrecho desconecta del mar abierto en el
       umbral de color: se identifican porque, a diferencia de una sombra de árbol o de edificio
       (textura moteada por el follaje, std de color 15-20), el agua es muy uniforme (std < 10) y
       claramente azulada (canal B bastante por encima de R). Medido en el bloque 3x3: la ría son
       std~6-7 y B-R~27-34; las sombras del Castro son std~13-20 y B-R~17-29 — el umbral de
       uniformidad separa ambos grupos, el matiz solo no basta (ver harness/progress o el commit)."""
    lum = render_rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    r, b = render_rgb[..., 0].astype(np.int32), render_rgb[..., 2].astype(np.int32)
    m = ((lum < 80) & (b >= r)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, dtype=bool)
    keep[np.unique(labels[0, :])] = True  # toca el borde norte: mar abierto
    for lbl in range(1, n):
        if keep[lbl] or stats[lbl, cv2.CC_STAT_AREA] < 1000:
            continue
        px = render_rgb[labels == lbl].astype(np.int32)
        if px.std(axis=0).mean() < 10 and (px[:, 2] - px[:, 0]).mean() > 15:
            keep[lbl] = True  # dique/dársena cerrada, no sombra: uniforme y azulada
    return keep[labels].astype(bool)


def devignette(tile_lab: np.ndarray) -> np.ndarray:
    """Flatten a large, slow lightness gradient baked into a single drawn tile — found in draw_r1c1.png:
    its top ~150 px are visibly paler/flatter than the rest, a vignette-like fade from the image model
    itself, not a seam or a colour-matching artefact (it survives --no-blend and is already there in the
    raw tile, see harness/progress or the commit for the before/after crop). A heavily blurred copy of L
    (sigma 180, a sixth of the tile) tracks only that slow trend, not the real local shading of streets
    and roofs; subtracting 80% of its deviation from the tile's own median flattens the fade and leaves
    local contrast alone."""
    L = tile_lab[..., 0]
    trend = cv2.GaussianBlur(L, (0, 0), 180)
    out = tile_lab.copy()
    out[..., 0] = np.clip(L - (trend - np.median(L)) * 0.8, 0, 255)
    return out


def water_texture(shape: tuple[int, int], seed: int = 3) -> np.ndarray:
    """Irregular sea surface, not the dead giveaway of a single sine ('rayas diagonales muy
    regulares', se ve generado): several octaves of value noise (random low-res field, blurred and
    upscaled, one call per octave) at falling amplitude and rising frequency, plus a sparse layer of
    small bright glints. No two patches of sea repeat the same way, same as real chop."""
    rng = np.random.default_rng(seed)
    h, w = shape
    wave = np.zeros((h, w), np.float32)
    for octave, (cells, amp) in enumerate(((6, 3.2), (14, 2.0), (30, 1.1), (70, 0.5))):
        small = rng.normal(0, 1, (cells, cells)).astype(np.float32)
        big = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
        big = cv2.GaussianBlur(big, (0, 0), max(w / cells / 6, 1.0))
        wave += big * amp
    glints = (rng.random((h, w)) > 0.9985).astype(np.float32)
    glints = cv2.GaussianBlur(glints, (0, 0), 0.6) * 40
    return wave + glints


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


def blend_corners(lab: np.ndarray, land: np.ndarray, radius: int = BAND) -> np.ndarray:
    """blend_seams runs the vertical and horizontal ramps separately, so right at a 4-tile crossing
    both ramps are near their weakest point and a faint cross survives ('la cruz tenue' at the corner
    where r1/r2 and c0/c1 meet — confirmed visible at zoom, not fixed by the two 1D passes). A local,
    radially feathered blur of the land pixels around each of the 4 interior corners finishes the job:
    strongest exactly at the crossing, fading to zero original edit at `radius` px out, so it only
    touches the small patch the two ramps could not reach."""
    out = lab.copy()
    for cy, cx in ((T, T), (T, 2 * T), (2 * T, T), (2 * T, 2 * T)):
        y0, y1, x0, x1 = cy - radius, cy + radius, cx - radius, cx + radius
        patch, lnd = lab[y0:y1, x0:x1], land[y0:y1, x0:x1].astype(np.float32)
        wb = np.maximum(cv2.GaussianBlur(lnd, (0, 0), 28), 1e-3)
        smooth = np.stack([cv2.GaussianBlur(patch[..., ch] * lnd, (0, 0), 28) / wb for ch in range(3)], axis=-1)
        yy, xx = np.mgrid[0:2 * radius, 0:2 * radius]
        feather = (np.clip(1 - np.hypot(yy - radius, xx - radius) / radius, 0, 1) ** 1.5)[..., None] * lnd[..., None]
        out[y0:y1, x0:x1] = patch * (1 - feather) + smooth * feather
    return out


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


def finish_filters(rgb: np.ndarray, contrast: float, sat: float) -> np.ndarray:
    """Filtros finales (el 'se ve plano' de Marcelo): contraste y saturación suaves sobre todo el mapa."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[..., 0]
    L = (L - L.mean()) * contrast + L.mean()
    lab[..., 1] = (lab[..., 1] - 128) * sat + 128
    lab[..., 2] = (lab[..., 2] - 128) * sat + 128
    lab[..., 0] = L
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--flat-sea", action="store_true")
    ap.add_argument("--no-blend", action="store_true")
    ap.add_argument("--finish", action="store_true", help="aplicar filtros finales (contraste + saturación)")
    ap.add_argument("--contrast", type=float, default=1.06)
    ap.add_argument("--sat", type=float, default=1.08)
    a = ap.parse_args()

    render = np.asarray(Image.open(a.render).convert("RGB"))
    wm = water_mask(render)
    canvas = np.zeros((3 * T, 3 * T, 3), np.float32)
    for r in range(3):
        for c in range(3):
            canvas[r * T:(r + 1) * T, c * T:(c + 1) * T] = devignette(to_lab(np.asarray(Image.open(f"{a.tiles}/draw_r{r}c{c}.png").convert("RGB").resize((T, T), Image.LANCZOS))))
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
        canvas = blend_corners(canvas, land)
    out = to_rgb(canvas)
    if a.flat_sea:
        # mar con gradiente (más claro junto a la costa, profundo al norte) y orilla de arena
        sea_deep = np.array([27, 41, 59], np.float32)
        sea_near = np.array([52, 78, 100], np.float32)
        dist = cv2.distanceTransform((~wm).astype(np.uint8), cv2.DIST_L2, 3)
        dmax = dist.max() + 1e-3
        t = np.clip(dist / (dmax * 0.5), 0, 1)[..., None]
        grad = sea_near[None, None, :] * (1 - t) + sea_deep[None, None, :] * t
        wave = water_texture(out.shape[:2])[..., None]
        grad = np.clip(grad + wave, 0, 255)
        erode = cv2.erode(wm.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)
        shore = cv2.dilate((wm.astype(np.uint8) - erode), np.ones((3, 3), np.uint8), iterations=2).astype(bool)
        sand = np.array([205, 188, 156], np.float32)
        soft = cv2.GaussianBlur(wm.astype(np.float32), (0, 0), 2.0)[..., None]
        out = (out * (1 - soft) + grad * soft).astype(np.float32)
        out = np.where(shore[..., None], sand * 0.9 + grad * 0.1, out)
        out = np.clip(out, 0, 255).astype(np.uint8)
    if a.finish:
        out = finish_filters(out, a.contrast, a.sat)
    Image.fromarray(out).save(a.out)
    print("saved", a.out, out.shape, alignment(out, render, wm))


if __name__ == "__main__":
    main()
