"""Mar por código para todo el mapa, de una sola vez.

El vídeo de Marcelo lo dice claro: el mar no se dibuja por teselas (cada una sale distinta y se ven los
cortes), se genera una vez por código y se colorea por la profundidad. Aquí:

* **Una sola capa** para todo el lienzo, a partir de la máscara de agua del render: no hay costuras
  entre teselas ni entre ventanas pintadas, ni el salto de tono que había en x=3072.
* **Color por distancia a la costa** (el sustituto de la profundidad real): verdoso y claro junto a
  tierra, azul profundo mar adentro. Sin las manchas de nube del ruido de valor anterior.
* **Ondas finas**: ruido alargado en horizontal (las crestas se ven como rayitas claras dispersas, que es
  como se lee el agua en un mapa isométrico) más una variación muy suave de gran escala.
* **Orilla limpia**: una línea fina de espuma y una sombra de contacto bajo los muelles, en lugar de la
  orilla de arena de 5 px que dejaba ``assemble_block`` y que se veía como una pegatina.

    python3 -m pipeline.render.sea --base work/este/v16.png --render work/render-wide/render.png \\
        --out work/este/v17.png

No llama a ningún modelo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from pipeline.render.port_fix import get_water

Image.MAX_IMAGE_PIXELS = None

# Colores del agua (RGB): junto a la costa y mar adentro.
NEAR = np.array([46, 88, 110], np.float32)
DEEP = np.array([27, 55, 84], np.float32)
DEPTH_PX = 140.0  # distancia (px) a la que el agua ya es «medio profunda»
FLOAT_MIN_DIST = 45  # px: un trozo de tierra tan lejos de la tierra firme es un resto flotando
FLOAT_MAX_AREA = 2000
SEED = 7


def _texture(shape: tuple[int, int]) -> np.ndarray:
    """Luminosidad del oleaje en unidades de L (media 0): crestas, rizado fino y variación suave."""
    rng = np.random.default_rng(SEED)
    h, w = shape

    def field(sx: float, sy: float) -> np.ndarray:
        f = cv2.GaussianBlur(
            rng.normal(size=(h, w)).astype(np.float32), (0, 0), sigmaX=sx, sigmaY=sy
        )
        return f / (f.std() + 1e-6)

    crest = np.clip((field(4.5, 1.1) - 1.75) / 0.9, 0, 1)  # rayitas claras escasas
    fine = field(2.2, 0.7) * 1.4  # rizado fino
    soft = field(110.0, 80.0) * 1.8  # variación suave de gran escala
    return soft + fine + crest * 13.0


def floaters(wm: np.ndarray) -> np.ndarray:
    """Trozos pequeños de «tierra» sueltos en mar abierto (boyas, cabezas de espigón, estelas).

    Son los mismos que quita ``port_fix.drop_floaters``; aquí pasan a ser mar para que no queden
    islotes con el mar viejo (más oscuro) dentro del mar nuevo. Los barcos junto a muelles se quedan.
    """
    land = (~wm).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(land, connectivity=8)
    big_ids = [i for i in range(1, n) if st[i, 4] > 20000]
    big = np.isin(lab, big_ids)
    dist = cv2.distanceTransform((~big).astype(np.uint8), cv2.DIST_L2, 3)
    drop = np.zeros(wm.shape, bool)
    for i in range(1, n):
        cx, cy = cen[i]
        if st[i, 4] > FLOAT_MAX_AREA or i in big_ids or dist[int(cy), int(cx)] < FLOAT_MIN_DIST:
            continue
        drop |= lab == i
    return drop


def speckles(wm: np.ndarray, max_side: int = 16) -> np.ndarray:
    """Agujeros cuadrados en el agua: las crestas blancas de las olas de la foto se leen como «tierra» y
    la apertura/cierre de la máscara los deja como cuadritos de 6-12 px. Un barco o una boya no son
    cuadrados perfectos, así que solo se quitan los compactos y pequeños."""
    land = (~wm).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(land, connectivity=8)
    drop = np.zeros(wm.shape, bool)
    for i in range(1, n):
        w, h, area = st[i, 2], st[i, 3], st[i, 4]
        if w <= max_side and h <= max_side and area >= 0.8 * w * h and area <= max_side * max_side:
            drop |= lab == i
    return drop


def painted_water(img: np.ndarray) -> np.ndarray:
    """Píxeles que en el DIBUJO se leen como agua (azul oscuro), para seguir la orilla que pintó el
    modelo en vez de los escalones de la máscara."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    blue = (lab[..., 2].astype(np.int16) - 128 < -10) & (lab[..., 0] < 140)
    return cv2.morphologyEx(blue.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0


def make_sea(wm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Capa de mar RGB (float32, 0-255) para todo el lienzo y distancia a tierra de cada píxel."""
    water = wm.astype(np.uint8)
    dist = cv2.distanceTransform(water, cv2.DIST_L2, 5)
    t = (1.0 - np.exp(-dist / DEPTH_PX))[..., None]
    sea = NEAR * (1 - t) + DEEP * t

    tex = _texture(wm.shape) * (0.55 + 0.45 * t[..., 0])  # junto a tierra el agua está más calmada
    sea += tex[..., None] * np.array([0.8, 1.0, 1.1], np.float32)

    foam = np.exp(-((dist / 1.3) ** 2))  # línea de espuma pegada a la costa
    contact = np.exp(-(((dist - 4.0) / 3.5) ** 2))  # sombra de contacto bajo muelles y diques
    sea += foam[..., None] * np.array([13, 14, 12], np.float32)
    sea -= contact[..., None] * np.array([6, 6, 5], np.float32) * (1 - foam[..., None])
    return np.clip(sea, 0, 255), dist


def apply_sea(
    img: np.ndarray,
    wm: np.ndarray,
    grow_px: int = 0,
    grow_zone: tuple[int, int, int, int] | None = None,
    soft: float = 0.8,
    band_px: int = 7,
) -> np.ndarray:
    """Sustituye el agua por el mar por código.

    * Dentro de ``grow_zone`` (x0, y0, x1, y1: el mapa antiguo) el mar se ensancha ``grow_px`` píxeles
      para comerse la orilla de arena que dejó el ensamblado viejo.
    * Fuera (las ventanas nuevas, sin orilla de arena) el grueso del agua sale de la máscara erosionada
      y, en una banda de ``band_px`` alrededor de su borde, solo se sustituye lo que el dibujo pinta
      como agua: así la costa sigue la línea del muelle dibujado y no los escalones de la máscara.
    """
    wm = wm | floaters(wm) | speckles(wm)
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2)  # noqa: E731
    w8 = wm.astype(np.uint8)
    grown = cv2.dilate(w8, k(grow_px)) if grow_px else w8
    band = (cv2.dilate(w8, k(band_px)) > 0) & (cv2.erode(w8, k(band_px)) == 0)
    fresh = (cv2.erode(w8, k(band_px)) > 0) | (band & painted_water(img))
    if grow_zone is None:
        region = grown > 0
    else:
        x0, y0, x1, y1 = grow_zone
        zone = np.zeros(wm.shape, bool)
        zone[y0:y1, x0:x1] = True
        region = np.where(zone, grown > 0, fresh)
    sea, _ = make_sea(region)
    alpha = cv2.GaussianBlur(region.astype(np.float32), (0, 0), soft)[..., None]
    out = img.astype(np.float32) * (1 - alpha) + sea * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--render", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--grow",
        type=int,
        default=2,
        help="px que se ensancha el mar para quitar la orilla de arena",
    )
    ap.add_argument(
        "--grow-zone",
        type=int,
        nargs=4,
        default=(0, 0, 3072, 3072),
        metavar=("X0", "Y0", "X1", "Y1"),
        help="zona del mapa antiguo, la única donde hay orilla de arena que quitar",
    )
    args = ap.parse_args(argv)
    base = np.asarray(Image.open(args.base).convert("RGB"))
    render = np.asarray(Image.open(args.render).convert("RGB"))
    wm = get_water(render)
    out = apply_sea(base, wm, args.grow, tuple(args.grow_zone))
    Image.fromarray(out).save(args.out)
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
