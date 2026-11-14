"""Draw a block of 1024 px render tiles one by one, centre outwards (Flash, p-7 neutral style).

    python3 pipeline/draw_block.py --tiles-dir ~/Downloads/vigo-bloque-3x3/tiles --out work/tiles \
        --prompt ~/Downloads/vigo-estilos/p-7-neutra.txt --centre ~/Downloads/vigo-estilos/s-7-neutra.png

Each call gets the render tile, a small crop (512 px) of the centre drawing as style swatch, and up to two narrow
strips (256 px) of already drawn neighbours. One call at a time (imggen.mjs waits on 429). Resumable: existing
drawings are skipped. Prompt, inputs and call count go to <out>/log.jsonl; the global ledger is in pipeline/ledger.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["r1c1", "r1c0", "r1c2", "r0c1", "r2c1", "r0c0", "r0c2", "r2c0", "r2c2"]
STRIP = 256
CONTEXT = (
    "\nThe FIRST image is the render to redraw. The SECOND image is only a small swatch of the target drawing style: "
    "copy its manner of drawing (pixel size, palette, line quality) and never its content, layout or objects. "
    "{strips}Do not copy anything from the swatch or the strips into places where the first image shows something else."
)
STRIP_TXT = (
    "The following image(s) are narrow strips of the neighbouring tile already drawn: continue its colours and pixel "
    "size across the shared edge only. "
)
FLAT_SEA = " Keep open water completely flat and empty: plain smooth uniform sea, no objects, no ships, no piers, no land."


def rc(name: str) -> tuple[int, int]:
    return int(name[1]), int(name[3])


def strip_of(neighbour: Image.Image, side: str) -> Image.Image:
    """Part of the neighbour that touches the current tile. side = where the neighbour is relative to the tile."""
    w, h = neighbour.size
    box = {"left": (w - STRIP, 0, w, h), "right": (0, 0, STRIP, h), "above": (0, h - STRIP, w, h), "below": (0, 0, w, STRIP)}[side]
    return neighbour.crop(box)


def drawn_neighbours(name: str, out: Path) -> list[tuple[str, str]]:
    r, c = rc(name)
    found = []
    for dr, dc, side in ((0, -1, "left"), (0, 1, "right"), (-1, 0, "above"), (1, 0, "below")):
        n = f"r{r + dr}c{c + dc}"
        if 0 <= r + dr <= 2 and 0 <= c + dc <= 2 and (out / f"draw_{n}.png").exists():
            found.append((n, side))
    return found[:2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--prompt", type=Path, required=True)
    ap.add_argument("--centre", type=Path, required=True, help="existing drawing of r1c1 (same render)")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--flat-sea", nargs="*", default=[], help="tiles to draw with the flat-sea sentence")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    base_prompt = args.prompt.read_text(encoding="utf-8").strip()

    centre = out / "draw_r1c1.png"
    if not centre.exists():
        Image.open(args.centre).convert("RGB").save(centre)
    swatch = out / "style-swatch.png"
    if not swatch.exists():
        Image.open(centre).crop((256, 256, 768, 768)).save(swatch)

    env = {**os.environ, "MODEL": "gemini-3.1-flash-image", "AR": "1:1"}
    env.pop("SIZE", None)
    for name in args.only or ORDER:
        dst = out / f"draw_{name}.png"
        if dst.exists() and not args.force:
            print("skip", name)
            continue
        strips = []
        for n, side in drawn_neighbours(name, out):
            p = out / f"strip_{name}_{n}.png"
            strip_of(Image.open(out / f"draw_{n}.png").convert("RGB"), side).save(p)
            strips.append(p)
        prompt = base_prompt + CONTEXT.format(strips=STRIP_TXT if strips else "")
        if name in args.flat_sea:
            prompt += FLAT_SEA
        pf = out / f"prompt_{name}.txt"
        pf.write_text(prompt, encoding="utf-8")
        cmd = ["node", str(ROOT / "pipeline" / "imggen.mjs"), str(dst), str(pf),
               str(args.tiles_dir / f"render_{name}.png"), str(swatch), *map(str, strips)]
        print("drawing", name, "strips:", [s.name for s in strips], flush=True)
        r = subprocess.run(cmd, env={**env, "LABEL": f"tile-{name}"})
        with open(out / "log.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"tile": name, "ok": r.returncode == 0, "strips": [s.name for s in strips], "flat_sea": name in args.flat_sea}) + "\n")
        if r.returncode != 0:
            print("stop: call failed for", name, "code", r.returncode)
            return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
