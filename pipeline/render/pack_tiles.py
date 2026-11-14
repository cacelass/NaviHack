"""Deja listas las entradas de pintura de unas teselas, con el formato de ``draw_block.py``.

Por cada tesela, una carpeta con lo que el pintor pasa al modelo:

    render.png               la tesela del render (la imagen 1: qué hay y dónde)
    estilo-512.png           recorte de 512 px de una tesela central ya dibujada (solo estilo)
    vecina-<lado>-256.png    tira de 256 px de cada vecina ya dibujada, en el borde que comparten

Las tiras salen del mapa final (``--final``, el que ve la web) y no de la tesela cruda:
la cruda trae el mar verde-turquesa y el final lo lleva azul marino por código, y el
modelo copia lo que ve. Donde el mapa final está roto (``PORT_PATCH``, el parche del
puerto que inventó una ciudad) se usa la tesela cruda.

No llama a ningún modelo. Recortes pequeños y no la tesela entera a propósito: el
informe del 3x3 vio que con la referencia completa el modelo copia su contenido.

    python3 -m pipeline.render.pack_tiles --render work/render-expansion/render.png \\
        --drawn ~/proyectos/NaviHack/work/tiles-p3 --final work/render-expansion/v6-actual.png \\
        --out work/render-expansion/pack r0c1 r0c3 r1c3 r2c3
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image

TILE = 1024
STRIP = 256
SWATCH_FROM = "r1c1"  # la tesela central, la referencia de estilo de todo el bloque
SWATCH_BOX = (256, 256, 768, 768)  # el mismo recorte que usa draw_block.py
# Zona del mapa final (x0, y0, x1, y1) rota por `seam-h-r1c1`: ahí no se copia del final.
PORT_PATCH = (1024, 512, 2048, 1536)


def parse(name: str) -> tuple[int, int]:
    match = re.fullmatch(r"r(\d+)c(\d+)", name)
    if not match:
        raise SystemExit(f"nombre de tesela no válido: {name!r} (r<fila>c<columna>)")
    return int(match[1]), int(match[2])


def strip(neighbour: Image.Image, side: str) -> Image.Image:
    """Parte de la vecina que toca la tesela. ``side``: dónde está la vecina respecto a ella."""
    w, h = neighbour.size
    box = {
        "izquierda": (w - STRIP, 0, w, h),
        "derecha": (0, 0, STRIP, h),
        "arriba": (0, h - STRIP, w, h),
        "abajo": (0, 0, w, STRIP),
    }[side]
    return neighbour.crop(box)


def overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def neighbour_strip(
    drawn: Path, final: Image.Image | None, row: int, col: int, side: str
) -> Image.Image | None:
    """Tira de la vecina (r{row}c{col}) del lado ``side``: del mapa final si es fiable, si no de la cruda."""
    if final is not None and 0 <= row <= 2 and 0 <= col <= 2:
        whole = Image.new("RGB", (TILE, TILE))
        whole.paste(final.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE)))
        piece = strip(whole, side)
        w, h = piece.size
        x0 = col * TILE + (TILE - STRIP if side == "izquierda" else 0)
        y0 = row * TILE + (TILE - STRIP if side == "arriba" else 0)
        if not overlaps((x0, y0, x0 + w, y0 + h), PORT_PATCH):
            return piece
    raw = drawn / f"draw_r{row}c{col}.png"
    return strip(Image.open(raw).convert("RGB"), side) if raw.exists() else None


def pack(
    render: Image.Image, drawn: Path, final: Image.Image | None, out: Path, name: str
) -> list[str]:
    row, col = parse(name)
    folder = out / name
    folder.mkdir(parents=True, exist_ok=True)
    made = []

    render.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE)).save(
        folder / "render.png"
    )
    made.append("render.png")

    centre = drawn / f"draw_{SWATCH_FROM}.png"
    Image.open(centre).convert("RGB").crop(SWATCH_BOX).save(folder / "estilo-512.png")
    made.append("estilo-512.png")

    for d_row, d_col, side in (
        (0, -1, "izquierda"),
        (0, 1, "derecha"),
        (-1, 0, "arriba"),
        (1, 0, "abajo"),
    ):
        piece = neighbour_strip(drawn, final, row + d_row, col + d_col, side)
        if piece is not None:
            piece.save(folder / f"vecina-{side}-256.png")
            made.append(f"vecina-{side}-256.png")
    return made


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--render", type=Path, required=True, help="render del lienzo (4096x3072)")
    ap.add_argument("--drawn", type=Path, required=True, help="carpeta con draw_rXcY.png")
    ap.add_argument("--final", type=Path, help="mapa final 3072x3072 (el que sirve la web)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("tiles", nargs="+", help="teselas, p. ej. r0c1 r1c3")
    args = ap.parse_args(argv)

    Image.MAX_IMAGE_PIXELS = None
    render = Image.open(args.render).convert("RGB")
    final = Image.open(args.final).convert("RGB") if args.final else None
    for name in args.tiles:
        made = pack(render, args.drawn, final, args.out, name)
        print(f"{name}: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
