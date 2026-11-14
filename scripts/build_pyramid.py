"""Build a versioned 512 px WebP tile pyramid from one base image.

    python3 scripts/build_pyramid.py --image base.png --version v0-placeholder
    python3 scripts/build_pyramid.py --image better.png --version v1 --set-current

Output: web/tiles/<version>/{manifest.json, <level>/<x>_<y>.webp}. A published
version is never overwritten: building an existing version fails. The web reads
web/tiles/current.json, so swapping the image is another run with a new version
and --set-current, with no change to the web code. Needs Pillow.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image

TILE = 512
Image.MAX_IMAGE_PIXELS = None


def build(image: Path, out_root: Path, version: str, quality: int = 85, set_current: bool = False,
          canvas: tuple[int, int] | None = None, offset: tuple[int, int] = (0, 0)) -> Path:
    dest = out_root / version
    if dest.exists():
        raise SystemExit(f"version '{version}' already exists at {dest}; never overwritten, pick a new version")
    img = Image.open(image).convert("RGB")
    width, height = img.size
    max_level = math.ceil(math.log2(max(width, height)))
    min_level = max_level
    while max(width, height) / 2 ** (max_level - min_level) > TILE:
        min_level -= 1
    levels = {}
    for level in range(min_level, max_level + 1):
        scale = 2 ** (level - max_level)
        w, h = max(1, math.ceil(width * scale)), max(1, math.ceil(height * scale))
        resized = img if level == max_level else img.resize((w, h), Image.LANCZOS)
        cols, rows = math.ceil(w / TILE), math.ceil(h / TILE)
        ldir = dest / str(level)
        ldir.mkdir(parents=True)
        for y in range(rows):
            for x in range(cols):
                tile = resized.crop((x * TILE, y * TILE, min(w, (x + 1) * TILE), min(h, (y + 1) * TILE)))
                tile.save(ldir / f"{x}_{y}.webp", "WEBP", quality=quality, method=6)
        levels[str(level)] = {"width": w, "height": h, "cols": cols, "rows": rows}
    manifest = {
        "version": version,
        "source": image.name,
        "width": width,
        "height": height,
        "tile_size": TILE,
        "format": "webp",
        "min_level": min_level,
        "max_level": max_level,
        "levels": levels,
    }
    if canvas:  # the image covers only part of the georeferenced canvas (e.g. one tile of the 3x3 block)
        manifest["canvas"] = {"width": canvas[0], "height": canvas[1]}
        manifest["offset"] = {"x": offset[0], "y": offset[1]}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if set_current:
        (out_root / "current.json").write_text(json.dumps({"version": version}) + "\n", encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", required=True, type=Path)
    ap.add_argument("--version", required=True)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "web" / "tiles")
    ap.add_argument("--quality", type=int, default=85)
    ap.add_argument("--canvas", type=int, nargs=2, metavar=("W", "H"), help="size of the georeferenced canvas the image sits in")
    ap.add_argument("--offset", type=int, nargs=2, metavar=("X", "Y"), default=(0, 0), help="top-left of the image in that canvas")
    ap.add_argument("--set-current", action="store_true", help="point web/tiles/current.json at this version")
    args = ap.parse_args(argv)
    dest = build(args.image, args.out, args.version, args.quality, args.set_current,
                 tuple(args.canvas) if args.canvas else None, tuple(args.offset))
    n = sum(1 for _ in dest.rglob("*.webp"))
    print(f"built {dest} ({n} tiles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
