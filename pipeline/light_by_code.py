"""Light an UNLIT drawing by code, using the height map of the same render (LIGHT-02 experiment, also the base of LIGHT-01).

Geometry (from the render script): orthographic camera, tilt 45 deg, heading 15 deg west of north, 2 px per metre,
canvas centre = world origin. The red channel of the height map is height * 4 (metres).

    python3 pipeline/light_by_code.py --unlit s-7-neutra.png --heights-dir tiles --tile r1c1 --out lit.png \
        --azimuth 235 --elevation 25

Steps: unproject every pixel to (x, y, z); scatter the heights into a ground height field (0.5 m cells);
ray-march towards the sun for cast shadows; estimate the surface normal (roof = up, wall = horizontal from the
height-field gradient); horizon-based ambient occlusion; combine warm sun, cool sky and AO over the unlit colours.
Every term can be switched off (--no-shadow, --no-ao, --no-sun) for the comparison sheets.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
SC = 2.0                      # px per metre
TILT = math.radians(45)
HEAD = math.radians(-15)
K, KZ = math.sin(TILT), math.cos(TILT)
FX, FY = math.sin(HEAD), math.cos(HEAD)      # forward
RX, RY = math.cos(HEAD), -math.sin(HEAD)     # screen right
T = 1024
CELL = 0.5                    # ground grid cell, metres


def unproject(px_x: np.ndarray, px_y: np.ndarray, z: np.ndarray, canvas: int = 3072):
    """Canvas pixel + height -> world (x east, y north) in metres."""
    u = (px_x - canvas / 2) / SC
    v = (px_y - canvas / 2) / SC
    d = -(v + KZ * z) / K                      # distance along forward
    return RX * u + FX * d, RY * u + FY * d


def load_heights(heights_dir: Path) -> np.ndarray:
    full = np.zeros((3 * T, 3 * T), np.float32)
    for r in range(3):
        for c in range(3):
            h = np.asarray(Image.open(heights_dir / f"height_r{r}c{c}.png").convert("RGB"))[..., 0].astype(np.float32) / 4.0
            full[r * T:(r + 1) * T, c * T:(c + 1) * T] = h
    return full


def height_field(full_h: np.ndarray, extent: float = 1150.0):
    n = int(2 * extent / CELL)
    ys, xs = np.mgrid[0:full_h.shape[0], 0:full_h.shape[1]]
    wx, wy = unproject(xs.astype(np.float32), ys.astype(np.float32), full_h)
    gx = ((wx + extent) / CELL).astype(np.int32)
    gy = ((wy + extent) / CELL).astype(np.int32)
    ok = (gx >= 0) & (gx < n) & (gy >= 0) & (gy < n)
    H = np.zeros((n, n), np.float32)
    np.maximum.at(H, (gy[ok], gx[ok]), full_h[ok])
    H = cv2.dilate(H, np.ones((3, 3), np.uint8))   # close sampling gaps (grows buildings by one cell at most)
    return H, extent


def sample(H: np.ndarray, extent: float, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    gx = np.clip(((x + extent) / CELL).astype(np.int32), 0, H.shape[1] - 1)
    gy = np.clip(((y + extent) / CELL).astype(np.int32), 0, H.shape[0] - 1)
    return H[gy, gx]


def shade(unlit: np.ndarray, tile_h: np.ndarray, origin: tuple[int, int], H, extent, az: float, el: float,
          sun: bool, shadow: bool, ao: bool, strength: float, contrast: float, ambient: float = 0.80, ao_amount: float = 0.35) -> tuple[np.ndarray, dict]:
    h, w = tile_h.shape
    ys, xs = np.mgrid[0:h, 0:w]
    wx, wy = unproject((xs + origin[0]).astype(np.float32), (ys + origin[1]).astype(np.float32), tile_h)
    top = sample(H, extent, wx, wy)
    # normal: wall pixels sit below the field height of their ground cell; horizontal normal from the field gradient
    Hs = cv2.GaussianBlur(H, (0, 0), 2.0)
    gxg = cv2.Sobel(Hs, cv2.CV_32F, 1, 0) / (8 * CELL)
    gyg = cv2.Sobel(Hs, cv2.CV_32F, 0, 1) / (8 * CELL)
    nx = -sample(gxg, extent, wx, wy)
    ny = -sample(gyg, extent, wx, wy)
    nl = np.hypot(nx, ny) + 1e-6
    is_wall = (tile_h < top - 0.6) | (nl > 0.9)
    nz = np.where(is_wall, 0.0, 1.0)
    hnx = np.where(is_wall, nx / nl, 0.0)
    hny = np.where(is_wall, ny / nl, 0.0)
    az_r, el_r = math.radians(az), math.radians(el)
    sx, sy = math.sin(az_r), math.cos(az_r)
    lam = np.clip(hnx * sx * math.cos(el_r) + hny * sy * math.cos(el_r) + nz * math.sin(el_r), 0, 1)
    vis = np.ones((h, w), np.float32)
    if shadow:
        tan_el = math.tan(el_r)
        for d in np.arange(1.0, 90.0, 1.0):
            hit = sample(H, extent, wx + sx * d, wy + sy * d) > (tile_h + 0.4 + d * tan_el)
            vis = np.where(hit, 0.0, vis)
        vis = cv2.GaussianBlur(vis, (0, 0), 0.8)
    occ = np.zeros((h, w), np.float32)
    if ao:
        for a in range(0, 360, 45):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            for r in (3.0, 6.0, 10.0):
                occ += np.clip((sample(H, extent, wx + ca * r, wy + sa * r) - tile_h) / (r * 1.2), 0, 1)
        occ = np.clip(occ / (8 * 3) * 1.8, 0, 1)
    amb = (1 - ao_amount * occ)[..., None]
    sky = np.array([0.90, 0.93, 1.00], np.float32) * ambient   # cool ambient (shadow colour)
    sunc = np.array([1.00, 0.84, 0.58], np.float32) * 0.70     # warm sun, added on top of the ambient
    direct = (lam * vis)[..., None] * (1.0 if sun else 0.0)
    light = sky[None, None, :] * amb + sunc[None, None, :] * direct * strength
    out = unlit.astype(np.float32) / 255.0 * light * 1.1
    lum = out.mean(axis=2, keepdims=True)
    out = np.clip((out - lum.mean()) * contrast + lum.mean() * 1.0 + (out - lum) * 0.15, 0, 1)
    stats = {"wall_share": float(is_wall.mean()), "shadow_share": float((vis < 0.5).mean()), "mean_occ": float(occ.mean())}
    return (out * 255).astype(np.uint8), stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unlit", required=True)
    ap.add_argument("--heights-dir", required=True, type=Path)
    ap.add_argument("--tile", default="r1c1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--azimuth", type=float, default=235.0, help="degrees clockwise from north")
    ap.add_argument("--elevation", type=float, default=25.0)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--contrast", type=float, default=1.25)
    ap.add_argument("--ambient", type=float, default=0.80)
    ap.add_argument("--ao-amount", type=float, default=0.35)
    ap.add_argument("--no-sun", action="store_true")
    ap.add_argument("--no-shadow", action="store_true")
    ap.add_argument("--no-ao", action="store_true")
    a = ap.parse_args()
    r, c = int(a.tile[1]), int(a.tile[3])
    full_h = load_heights(a.heights_dir)
    H, extent = height_field(full_h)
    tile_h = full_h[r * T:(r + 1) * T, c * T:(c + 1) * T]
    unlit = np.asarray(Image.open(a.unlit).convert("RGB").resize((T, T), Image.LANCZOS))
    out, stats = shade(unlit, tile_h, (c * T, r * T), H, extent, a.azimuth, a.elevation,
                       not a.no_sun, not a.no_shadow, not a.no_ao, a.strength, a.contrast, a.ambient, a.ao_amount)
    Image.fromarray(out).save(a.out)
    print("saved", a.out, stats)


if __name__ == "__main__":
    main()
