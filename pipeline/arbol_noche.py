"""Night version of the Porta do Sol tree demo, entirely by code — no image call.

Per spec: the base map is painted unlit; night, light and brightness are code. So the tree is painted
switched OFF (see arbol_porta_sol.py) and this script adds the "on" state: a night tint over the whole
1024 px demo crop, measured from the pair that already exists for the base map (noche-antes.png vs
dia-antes.png, from before the tree — same multiply constant everywhere, see NIGHT_TINT), plus a light
layer built only from the tree's own silhouette (the mask from arbol_porta_sol.py, not a hand-drawn
shape): cyan/white strings over the body, a warm red glow at the star, and a soft bloom spilling onto
the plaza, matching the real Porta do Sol tree (metal lattice with cyan/white LED strips, red starburst
on top) instead of the discarded warm-gold fir-tree look.

    python3 pipeline/arbol_noche.py
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from arbol_porta_sol import HALF, OUT_DIR, build_mask, crop_box

# measured from web/ui/assets-prueba/{dia,noche}-antes.png (7 sample points, std < 0.01 per channel):
# noche = dia * NIGHT_TINT, a plain multiply blend with a fixed navy colour, everywhere but the glow.
NIGHT_TINT = np.array([0.292, 0.396, 0.696], np.float32)
DEMO = 1024  # the demo crop is the full canvas centre ± 512 px, same convention as dia-antes.png


def glow(mask: np.ndarray, sigma: float, gain: float) -> np.ndarray:
    return np.clip(cv2.GaussianBlur(mask, (0, 0), sigma) * gain, 0, 1)


def main() -> None:
    day = np.asarray(Image.open(OUT_DIR / "dia-despues-v2.png").convert("RGB")).astype(np.float32)
    night_base = day * NIGHT_TINT[None, None, :]

    # place the tree mask (computed at the model's 1024 px crop, see build_mask) into the 1024 px demo
    # crop's coordinate space: the plaza crop sits at `crop_box()` in canvas px, the demo crop is the
    # canvas centre ± 512 px, so the offset between the two is fixed geometry, not a guess.
    bx0, by0, bx1, by1 = crop_box()
    # the demo crop is canvas centre ± 512 px (same convention as arbol_porta_sol.main()); the canvas
    # centre is not CX,CY (that is the plaza centre), so read the real canvas size instead of guessing.
    full = Image.open(OUT_DIR / "canvas-con-arbol.png")
    cx, cy = full.size[0] // 2, full.size[1] // 2
    off_x, off_y = bx0 - (cx - DEMO // 2), by0 - (cy - DEMO // 2)

    src350 = np.asarray(Image.open(OUT_DIR / "arbol-ps-crop350.png").convert("RGB"))
    dst350 = np.asarray(Image.open(OUT_DIR / "arbol-ps-out350.png").convert("RGB"))
    mask1024 = build_mask(np.asarray(Image.open(OUT_DIR / "arbol-ps-in1024.png").convert("RGB")),
                           np.asarray(Image.open(OUT_DIR / "arbol-ps-out1024.png").convert("RGB")))
    mask350 = cv2.resize(mask1024, (2 * HALF, 2 * HALF), interpolation=cv2.INTER_AREA)

    mask_demo = np.zeros((DEMO, DEMO), np.float32)
    mask_demo[off_y:off_y + 2 * HALF, off_x:off_x + 2 * HALF] = mask350

    ys, xs = np.where(mask_demo > 0.5)
    y0, y1 = ys.min(), ys.max()
    star_cut = y0 + int((y1 - y0) * 0.16)  # top ~16 % of the silhouette is the starburst
    star_mask = mask_demo.copy(); star_mask[star_cut:] = 0
    body_mask = mask_demo.copy(); body_mask[:star_cut] = 0

    cyan_white = np.array([150, 230, 240], np.float32)
    red = np.array([255, 60, 45], np.float32)

    # the day paint is a silver-grey lattice (bright lines, dark gaps) on top of the plaza; use its own
    # luminance inside the mask as an emission map, so the lights follow the actual struts and strips
    # the model drew instead of flooding the whole silhouette into one flat glowing blob.
    day_l = cv2.cvtColor(day.astype(np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32) / 255
    strands = body_mask * np.clip((day_l - 0.35) / 0.5, 0, 1) ** 0.7

    def screen(base: np.ndarray, light: np.ndarray) -> np.ndarray:
        return 255 - (255 - base) * (255 - light) / 255

    bloom = glow(mask_demo, 34, 0.55)[..., None] * cyan_white[None, None, :]
    body_light = glow(strands, 1.6, 1.0)[..., None] * cyan_white[None, None, :]
    star_light = glow(star_mask, 3.0, 0.9)[..., None] * red[None, None, :]

    night = night_base.copy()
    night = screen(night, bloom)
    night = screen(night, body_light)
    night = screen(night, star_light)
    night = np.clip(night, 0, 255).astype(np.uint8)
    Image.fromarray(night).save(OUT_DIR / "noche-despues-v2.png")

    # standalone light layer: drop this PNG with CSS `mix-blend-mode: screen` over any night base and
    # animate `opacity` 0.85-1 on a ~2.2 s ease-in-out loop for the "parpadeo suave" — same recipe as
    # the existing .parpadeo rule in web/ui/assets-prueba.html, just driven by this sprite instead of
    # hand-drawn SVG dots, since the shape now comes from the mask, not from a guess.
    light_sprite = np.clip(bloom + body_light + star_light, 0, 255).astype(np.uint8)
    alpha = np.clip(glow(mask_demo, 6, 1.0) * 255, 0, 255).astype(np.uint8)
    sprite_rgba = np.dstack([light_sprite, alpha])
    Image.fromarray(sprite_rgba, "RGBA").save(OUT_DIR / "arbol-luz-sprite.png")
    print("saved", OUT_DIR / "noche-despues-v2.png", "and", OUT_DIR / "arbol-luz-sprite.png")
    print("tree bbox in demo crop:", xs.min(), xs.max(), ys.min(), ys.max())


if __name__ == "__main__":
    main()
