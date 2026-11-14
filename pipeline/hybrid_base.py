"""Land from one drawing, sea by code: keep drawn pixels where the render is land, flat sea colour where it is water.

    python3 pipeline/hybrid_base.py --drawing big.png --render render.png --sea-from other.png --out out.png
Output is exactly the render size (3072x3072), no shift. Also prints the alignment against the render.
"""
import argparse, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from assemble_block import water_mask, alignment
Image.MAX_IMAGE_PIXELS = None
ap = argparse.ArgumentParser()
ap.add_argument("--drawing", required=True); ap.add_argument("--render", required=True)
ap.add_argument("--sea-from", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--sea-colour", default="")
a = ap.parse_args()
render = np.asarray(Image.open(a.render).convert("RGB")); S = render.shape[0]
wm = water_mask(render)
draw = np.asarray(Image.open(a.drawing).convert("RGB").resize((S, S), Image.LANCZOS))
seaimg = np.asarray(Image.open(a.sea_from).convert("RGB").resize((S, S), Image.LANCZOS))
sea = np.array([int(x) for x in a.sea_colour.split(",")]) if a.sea_colour else np.median(seaimg[wm & (np.arange(S)[:, None] < 700)], axis=0)
soft = cv2.GaussianBlur(wm.astype(np.float32), (0, 0), 2.0)[..., None]
out = (draw * (1 - soft) + sea[None, None, :] * soft).astype(np.uint8)
Image.fromarray(out).save(a.out)
top = slice(1100, S)
print("sea colour", sea.astype(int).tolist(), "size", out.shape)
print("alignment (lower part)", alignment(out[top], render[top], wm[top]))
