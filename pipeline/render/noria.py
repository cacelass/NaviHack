"""Put the Christmas Ferris wheel of Vialia into the map, by code around one image call.

Same method as pipeline/arbol_porta_sol.py, but the box is given by --center and --half instead of
constants: crop a square of 2*half px around the centre, upscale it to 1024 px, ask the model to add
the wheel, and paste back only what changed (mask from the real pixel difference). Everything outside
that mask stays bit-identical to the source canvas.

    python3 pipeline/render/noria.py --canvas map.png --center 3000 1500 --call
    python3 pipeline/render/noria.py --canvas map.png --center 3000 1500 --from-file work/noria/respuesta1024.png
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

PIPELINE = Path(__file__).resolve().parents[1]
ROOT = PIPELINE.parent
sys.path.insert(0, str(PIPELINE))
from arbol_porta_sol import build_mask  # noqa: E402

MODEL_SIZE = 1024
PROMPT = ROOT / "pipeline/render/zona/noria-prompt.txt"
PHOTO = ROOT / "web/data/photos/concello-3494.webp"
OUT_DIR = ROOT / "work/noria"


def crop_box(
    center: tuple[int, int], half: int, size: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Square box of side 2*half around center as (x0, y0, x1, y1). size is the canvas (width, height)."""
    cx, cy = center
    w, h = size
    x0, y0, x1, y1 = cx - half, cy - half, cx + half, cy + half
    if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
        raise ValueError(
            f"la caja {x0},{y0}-{x1},{y1} se sale del lienzo {w}x{h} (centro {cx},{cy}, half {half})"
        )
    return x0, y0, x1, y1


def upscale(crop: np.ndarray) -> np.ndarray:
    return np.asarray(Image.fromarray(crop).resize((MODEL_SIZE, MODEL_SIZE), Image.LANCZOS))


def composite(
    canvas: np.ndarray, center: tuple[int, int], half: int, answer1024: np.ndarray
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Paste the model's 1024 px answer back into canvas, changing only what the mask says.

    canvas is an RGB uint8 array (H, W, 3). Returns (new canvas, mask at 1024 px, stats).
    """
    h, w = canvas.shape[:2]
    x0, y0, x1, y1 = crop_box(center, half, (w, h))
    side = 2 * half
    src = canvas[y0:y1, x0:x1]
    mask1024 = build_mask(upscale(src), answer1024)
    dst = np.asarray(Image.fromarray(answer1024).resize((side, side), Image.LANCZOS))
    mask = cv2.resize(mask1024, (side, side), interpolation=cv2.INTER_AREA)[..., None]
    blended = np.rint(src.astype(np.float32) * (1 - mask) + dst.astype(np.float32) * mask)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    out = canvas.copy()
    out[y0:y1, x0:x1] = blended
    full_mask = np.zeros((h, w), np.float32)
    full_mask[y0:y1, x0:x1] = mask[..., 0]
    untouched = full_mask < 0.002  # below this, rounding leaves every pixel as it was
    stats = {
        "box": (x0, y0, x1, y1),
        "changed_1024": int((mask1024 > 0.5).sum()),
        "changed_canvas": int(np.any(out != canvas, axis=2).sum()),
        "untouched": int(untouched.sum()),
        "bit_exact": bool(np.array_equal(out[untouched], canvas[untouched])),
    }
    return out, mask1024, stats


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--canvas", type=Path, required=True, help="PNG of the map (may be 5120x3072)")
    ap.add_argument(
        "--center", type=int, nargs=2, required=True, metavar=("X", "Y"), help="centre in canvas px"
    )
    ap.add_argument(
        "--half", type=int, default=175, help="half side of the crop; the box is 2*half px"
    )
    ap.add_argument("--prompt", type=Path, default=PROMPT)
    ap.add_argument("--photo", type=Path, default=PHOTO, help="real photo sent as picture 2")
    ap.add_argument("--no-photo", action="store_true", help="do not send the photo")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="full final map (default: <out-dir>/mapa-con-noria.png)",
    )
    ap.add_argument("--call", action="store_true", help="spend one image call")
    ap.add_argument(
        "--from-file", type=Path, default=None, help="reuse an existing model answer, no call"
    )
    a = ap.parse_args()

    if not a.call and not a.from_file:
        print("nada que hacer: pasa --call (gasta una llamada) o --from-file RESPUESTA.png")
        return
    if a.call and not a.no_photo and not a.photo.exists():
        sys.exit(f"error: no existe la foto {a.photo}")

    canvas = np.asarray(Image.open(a.canvas).convert("RGB"))
    h, w = canvas.shape[:2]
    center = (a.center[0], a.center[1])
    try:
        x0, y0, x1, y1 = crop_box(center, a.half, (w, h))
    except ValueError as e:
        sys.exit(f"error: {e}")

    a.out_dir.mkdir(parents=True, exist_ok=True)
    crop = canvas[y0:y1, x0:x1]
    Image.fromarray(crop).save(a.out_dir / "recorte.png")
    in1024 = a.out_dir / "entrada1024.png"
    Image.fromarray(upscale(crop)).save(in1024)

    answer_path = a.out_dir / "respuesta1024.png"
    if a.from_file:
        answer_path = a.from_file
    else:
        imgs = [str(in1024)] + ([] if a.no_photo else [str(a.photo)])
        cmd = ["node", str(ROOT / "pipeline/imggen.mjs"), str(answer_path), str(a.prompt), *imgs]
        env = {
            **os.environ,
            "MODEL": "gemini-3.1-flash-image",
            "AR": "1:1",
            "LABEL": "noria-vialia",
        }
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            sys.exit(r.returncode)

    answer = Image.open(answer_path).convert("RGB")
    if answer.size != (MODEL_SIZE, MODEL_SIZE):
        answer = answer.resize((MODEL_SIZE, MODEL_SIZE), Image.LANCZOS)
    out, mask1024, stats = composite(canvas, center, a.half, np.asarray(answer))

    Image.fromarray((mask1024 * 255).astype(np.uint8)).save(a.out_dir / "mascara1024.png")
    bx0, by0, bx1, by1 = stats["box"]
    Image.fromarray(out[by0:by1, bx0:bx1]).save(a.out_dir / "resultado-recorte.png")
    out_path = a.out or a.out_dir / "mapa-con-noria.png"
    Image.fromarray(out).save(out_path)

    print(
        f"caja {stats['box']}; cambian {stats['changed_1024']}/{MODEL_SIZE * MODEL_SIZE} px a 1024"
    )
    print(f"px del lienzo que cambian: {stats['changed_canvas']}/{h * w}")
    print(
        f"fuera de la mascara: {stats['untouched']} px, bit a bit identicos: {stats['bit_exact']}"
    )
    print("guardado", out_path)


if __name__ == "__main__":
    main()
