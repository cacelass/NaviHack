"""Paint the 45 m Christmas tree of Porta do Sol inside the block, by code around one image call.

Fixes the broken attempt of f134bee: the call was fed the whole 512 m centre crop (1024 px), so the
45 m tree (60-90 px at 2 px/m) was lost in the frame and the model put a tree somewhere else (the big
paved square by the Concello); the mask then kept a repainted patch of roofs with no tree in it at all.

This script crops a small ~350 px square straight out of the geo-referenced centre of the canvas
(canvas centre = Porta do Sol, 42.23807 -8.72581, per Jose), upscales it to 1024 px before the call so
the model has room to draw fine light detail, downscales the answer back to 350 px, and composites it
with a mask built from the actual pixel difference (tree + its shadow only) — never a fixed region, so
it adapts to wherever the model really drew the tree. Buildings outside that footprint are bit-identical
to the source.

    python3 pipeline/arbol_porta_sol.py --call                 # spend one image call, then composite
    python3 pipeline/arbol_porta_sol.py --from work/assets/arbol-porta-sol-out.png   # reuse an answer, no call
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CANVAS = Path.home() / "proyectos/NaviHack/work/tiles-p3/ensamblado-v6.png"  # best current style (v6)
OUT_DIR = ROOT / "work/assets"
PROMPT = ROOT / "pipeline/prompts/arbol-add-full.txt"
# centre of the plaza, found by eye around the geo-referenced canvas centre (1536,1536) = Porta do Sol
CX, CY, HALF = 1608, 1518, 175  # box: (1433,1343)-(1783,1693), 350x350


def crop_box() -> tuple[int, int, int, int]:
    return (CX - HALF, CY - HALF, CX + HALF, CY + HALF)


def build_mask(src: np.ndarray, dst: np.ndarray, *, open_px: int = 5, dilate_px: int = 9, blur: float = 5.0) -> np.ndarray:
    """Soft mask of what the model actually changed, at the model's own 1024 px resolution (not after
    the lossy downscale to 350 px, where the tree and the round-trip resampling noise sit too close in
    magnitude to separate cleanly). OPEN before labelling drops the thin, scattered 1-2 px noise trail
    along streets and roof edges; the tree + its crowd stay one thick solid blob, always the biggest
    component after opening — nothing about its shape is assumed, so it follows wherever the model
    really drew the tree."""
    sl = cv2.cvtColor(src, cv2.COLOR_RGB2LAB).astype(np.float32)
    dl = cv2.cvtColor(dst, cv2.COLOR_RGB2LAB).astype(np.float32)
    d = np.linalg.norm(sl - dl, axis=2)
    h, w = d.shape
    opened = cv2.morphologyEx((d > 15).astype(np.uint8), cv2.MORPH_OPEN, np.ones((open_px, open_px), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    if n <= 1:
        return np.zeros((h, w), np.float32)
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    m = (labels == biggest).astype(np.uint8)
    m = cv2.dilate(m, np.ones((dilate_px, dilate_px), np.uint8), iterations=1)
    soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), blur)
    return np.clip(soft, 0, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--call", action="store_true", help="spend one image call")
    ap.add_argument("--from-file", dest="from_file", type=Path, default=None, help="reuse an existing model answer")
    ap.add_argument("--label", default="arbol-porta-sol-v2")
    a = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    canvas = Image.open(CANVAS).convert("RGB")
    box = crop_box()
    crop350 = canvas.crop(box)
    crop350.save(OUT_DIR / "arbol-ps-crop350.png")
    crop1024 = crop350.resize((1024, 1024), Image.LANCZOS)
    in1024 = OUT_DIR / "arbol-ps-in1024.png"
    crop1024.save(in1024)

    out1024 = OUT_DIR / "arbol-ps-out1024.png"
    if a.from_file:
        out1024 = a.from_file
    elif a.call:
        cmd = ["node", str(ROOT / "pipeline/imggen.mjs"), str(out1024), str(PROMPT), str(in1024)]
        env = {**os.environ, "MODEL": "gemini-3.1-flash-image", "AR": "1:1", "LABEL": a.label}
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            sys.exit(r.returncode)
    else:
        print("nothing to do: pass --call or --from-file <path>")
        return

    out350 = Image.open(out1024).convert("RGB").resize((350, 350), Image.LANCZOS)
    out350.save(OUT_DIR / "arbol-ps-out350.png")

    # the mask separates cleanly only at the model's own 1024 px resolution (see build_mask); shrink
    # just the (smooth, low-frequency) mask down to 350 px and blend there with the *original* 350 px
    # crop, never a resize round-trip of it — so every pixel the mask leaves alone is bit-identical to
    # the source canvas, buildings included.
    src1024 = np.asarray(Image.open(in1024).convert("RGB"))
    dst1024 = np.asarray(Image.open(out1024).convert("RGB"))
    mask1024 = build_mask(src1024, dst1024)
    Image.fromarray((mask1024 * 255).astype(np.uint8)).save(OUT_DIR / "arbol-ps-mask1024.png")
    print("changed px (mask>0.5) at 1024:", int((mask1024 > 0.5).sum()), "/", 1024 * 1024)
    mask350 = cv2.resize(mask1024, (350, 350), interpolation=cv2.INTER_AREA)[..., None]

    src = np.asarray(crop350)
    dst = np.asarray(out350)
    result = (src.astype(np.float32) * (1 - mask350) + dst.astype(np.float32) * mask350).astype(np.uint8)
    Image.fromarray(result).save(OUT_DIR / "arbol-ps-result350.png")
    unchanged = (mask350[..., 0] < 0.02)
    bit_exact = bool(np.array_equal(result[unchanged], src[unchanged]))
    print("pixels left untouched outside mask:", int(unchanged.sum()), "/", 350 * 350, "bit-exact:", bit_exact)

    full = np.asarray(canvas).copy()
    x0, y0, x1, y1 = box
    full[y0:y1, x0:x1] = result
    Image.fromarray(full).save(OUT_DIR / "canvas-con-arbol.png")

    w, h = canvas.size
    cx, cy = w // 2, h // 2
    demo = Image.fromarray(full).crop((cx - 512, cy - 512, cx + 512, cy + 512))
    demo.save(OUT_DIR / "dia-despues-v2.png")
    print("saved", OUT_DIR / "dia-despues-v2.png")


if __name__ == "__main__":
    main()
