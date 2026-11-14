"""Pixelate a drawn base image by code (no API): average-downscale, limited palette, contrast, nearest-neighbour upscale.

    python3 pipeline/pixelate.py in.png out.png --grid 1024 --colors 40 --out-size 3072

The output size must be a multiple of the grid so every art pixel is a square block (3072 = 1024 x 3 = 1536 x 2).
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def quantize_lab(rgb: np.ndarray, colors: int, seed: int = 7) -> np.ndarray:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    rng = np.random.default_rng(seed)
    sample = lab[rng.choice(len(lab), size=min(len(lab), 200_000), replace=False)]
    cv2.setRNGSeed(seed)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, centers = cv2.kmeans(sample, colors, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    d = ((lab[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2) if len(lab) < 300_000 else None
    if d is None:  # chunked nearest-centre search for big grids
        idx = np.empty(len(lab), dtype=np.int32)
        for i in range(0, len(lab), 200_000):
            blk = lab[i:i + 200_000]
            idx[i:i + 200_000] = ((blk[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
    else:
        idx = d.argmin(axis=1)
    out_lab = centers[idx].reshape(rgb.shape).astype(np.uint8)
    return cv2.cvtColor(out_lab, cv2.COLOR_LAB2RGB)


def enhance(rgb: np.ndarray, contrast: float, edges: float) -> np.ndarray:
    """Contrast on L (around its mean) and a gentle edge darkening so volumes read."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[..., 0]
    L = (L - L.mean()) * contrast + L.mean()
    if edges > 0:
        blur = cv2.GaussianBlur(L, (0, 0), 1.2)
        L = L + edges * (L - blur)  # unsharp: lifts lines, darkens the seam between roofs and walls
    lab[..., 0] = np.clip(L, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)


def pixelate(src: Image.Image, grid: int, colors: int, contrast: float, edges: float, out_size: int) -> Image.Image:
    if out_size % grid:
        raise SystemExit("out-size must be a multiple of grid")
    small = src.convert("RGB").resize((grid, grid), Image.BOX)  # average, not point-sample
    arr = enhance(np.asarray(small), contrast, edges)
    if colors:
        arr = quantize_lab(arr, colors)
    return Image.fromarray(arr).resize((out_size, out_size), Image.NEAREST)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--grid", type=int, default=1024)
    ap.add_argument("--colors", type=int, default=40, help="0 = no palette limit")
    ap.add_argument("--contrast", type=float, default=1.15)
    ap.add_argument("--edges", type=float, default=0.8)
    ap.add_argument("--out-size", type=int, default=3072)
    a = ap.parse_args()
    pixelate(Image.open(a.src), a.grid, a.colors, a.contrast, a.edges, a.out_size).save(a.dst)


if __name__ == "__main__":
    main()
