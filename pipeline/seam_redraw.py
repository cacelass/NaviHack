"""Repaint a seam or a 4-tile corner by the tinygyn method (half+half, red context, redraw the centre,
blend back) — for the seams that a pure colour fix cannot reach (content disagrees, not just light; see
docs/investigacion/auditoria-bloque.md §2 and §6). Operates on the already-assembled canvas, not the raw
tiles, so each redraw only has to fix what is still visibly wrong after the code-only pass.

    python3 pipeline/seam_redraw.py --canvas work/tiles-p3/ensamblado-v9.png --kind h --row 1 --col 1 --call
    python3 pipeline/seam_redraw.py --canvas work/tiles-p3/ensamblado-v9.png --kind corner --cy 2048 --cx 1536 --call

--call spends exactly one image call; without it the script only builds and saves the red-tinted input
for a look before paying for anything. `--out` controls where the patched canvas is written (never the
input file, so nothing is overwritten without a new name).
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
OUT_DIR = ROOT / "work/assets/seams"
PROMPT = ROOT / "pipeline/prompts/seam-redraw.txt"
RED = np.array([200, 30, 20], np.float32)
FADE = 48  # px, ramp at the edge of the blended-back centre (tinygyn notes, 32-64 px)


def tint(img: np.ndarray, mask: np.ndarray, alpha: float = 0.42) -> np.ndarray:
    out = img.astype(np.float32)
    out[mask] = out[mask] * (1 - alpha) + RED * alpha
    return out.astype(np.uint8)


def box_and_mask(kind: str, row: int, col: int, cy: int, cx: int) -> tuple[tuple[int, int, int, int], np.ndarray]:
    """Returns (box in canvas px, red_mask 1024x1024 local)."""
    red = np.zeros((1024, 1024), bool)
    if kind == "v":
        x = col * 1024
        box = (x - 512, row * 1024, x + 512, (row + 1) * 1024)
        red[:, :256] = True
        red[:, 768:] = True
    elif kind == "h":
        y = row * 1024
        box = (col * 1024, y - 512, (col + 1) * 1024, y + 512)
        red[:256, :] = True
        red[768:, :] = True
    elif kind == "corner":
        box = (cx - 512, cy - 512, cx + 512, cy + 512)
        red[:256, :256] = red[:256, 768:] = red[768:, :256] = red[768:, 768:] = True
    else:
        raise ValueError(kind)
    return box, red


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canvas", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--kind", choices=["v", "h", "corner"], required=True)
    ap.add_argument("--row", type=int, default=0)
    ap.add_argument("--col", type=int, default=0)
    ap.add_argument("--cy", type=int, default=0)
    ap.add_argument("--cx", type=int, default=0)
    ap.add_argument("--call", action="store_true")
    ap.add_argument("--from-file", type=Path, default=None)
    ap.add_argument("--label", default=None)
    a = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"{a.kind}-r{a.row}c{a.col}" if a.kind != "corner" else f"corner-{a.cy}-{a.cx}"

    canvas = Image.open(a.canvas).convert("RGB")
    box, red_mask = box_and_mask(a.kind, a.row, a.col, a.cy, a.cx)
    strip = np.asarray(canvas.crop(box))
    tinted = tint(strip, red_mask)
    in_path = OUT_DIR / f"{tag}-in.png"
    Image.fromarray(tinted).save(in_path)

    out_path = OUT_DIR / f"{tag}-out.png"
    if a.from_file:
        out_path = a.from_file
    elif a.call:
        cmd = ["node", str(ROOT / "pipeline/imggen.mjs"), str(out_path), str(PROMPT), str(in_path)]
        env = {**os.environ, "MODEL": "gemini-3.1-flash-image", "AR": "1:1", "LABEL": a.label or f"seam-{tag}"}
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            sys.exit(r.returncode)
    else:
        print("saved", in_path, "(no --call: nothing spent)")
        return

    redrawn = np.asarray(Image.open(out_path).convert("RGB")).astype(np.float32)
    clean = (~red_mask).astype(np.float32)
    # fade the clean region's own edge inward by FADE px so the blended patch melts into the strip
    # instead of trading the old sharp seam for a new sharp patch boundary.
    ramp = cv2.distanceTransform(clean.astype(np.uint8), cv2.DIST_L2, 3)
    weight = np.clip(ramp / FADE, 0, 1)[..., None]

    full = np.asarray(canvas).copy().astype(np.float32)
    x0, y0, x1, y1 = box
    patch = full[y0:y1, x0:x1]
    full[y0:y1, x0:x1] = patch * (1 - weight) + redrawn * weight
    out_canvas = np.clip(full, 0, 255).astype(np.uint8)

    out_file = a.out or a.canvas.with_name(a.canvas.stem + f"-{tag}.png")
    Image.fromarray(out_canvas).save(out_file)
    print("saved", out_file, "patched px:", int((weight[..., 0] > 0.5).sum()))


if __name__ == "__main__":
    main()
