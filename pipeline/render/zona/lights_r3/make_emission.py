"""Luz de una asset (árbol, noria) a partir de la versión nocturna encendida que dibuja el modelo.

1. recorte de 400 px del mapa x NIGHT_TINT (multiplicado) = noche apagada; subido a 1024 px
2. modelo de imagen: mapa apagado + render + foto real -> mismo recorte con la luz encendida (prompt_*.txt)
3. este script: ajusta el color de la respuesta al de la noche apagada lejos del asset, se queda con la parte POSITIVA
   de la diferencia dentro de una región (elipses/cono del asset), la pasa por una rodilla suave (sin núcleos blancos),
   le suma el resplandor (dos desenfoques) y difumina 60 px los bordes del recorte. Negro = sin luz: se suma con «screen».

    python3 make_emission.py noche_base.png respuesta.png salida.png --far 205 235 150 150 --ellipse 204 215 78 102 --ellipse 215 265 125 70
"""
import argparse

import cv2
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("base"); ap.add_argument("reply"); ap.add_argument("out")
ap.add_argument("--far", type=float, nargs=4, metavar=("CX", "CY", "RX", "RY"), required=True)
ap.add_argument("--ellipse", type=float, nargs=4, action="append", metavar=("CX", "CY", "RX", "RY"), required=True)
ap.add_argument("--gate", type=float, default=16, help="diferencia mínima (canal máximo) para contar como luz")
ap.add_argument("--bloom", type=float, default=0.7)
o = ap.parse_args()
S = 400
base = np.asarray(Image.open(o.base).convert("RGB").resize((S, S), Image.LANCZOS)).astype(np.float32)
out = np.asarray(Image.open(o.reply).convert("RGB").resize((S, S), Image.LANCZOS)).astype(np.float32)
yy, xx = np.mgrid[0:S, 0:S]
cx, cy, rx, ry = o.far
far = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) > 1
for c in range(3):
    a, b = base[..., c][far], out[..., c][far]
    out[..., c] = (out[..., c] - b.mean()) * (a.std() / (b.std() + 1e-3)) + a.mean()
diff = np.clip(out - base, 0, 255)
reg = np.zeros((S, S), np.float32)
for ex, ey, erx, ery in o.ellipse:
    cv2.ellipse(reg, (int(ex), int(ey)), (int(erx), int(ery)), 0, 0, 360, 1, -1)
reg = cv2.GaussianBlur(reg, (0, 0), 6)
em = diff * (np.clip((diff.max(2) - o.gate) / 40, 0, 1) * reg)[..., None]
em = 255 * (1 - np.exp(-em / 140.0))
em = em + (cv2.GaussianBlur(em, (0, 0), 9) * 0.9 + cv2.GaussianBlur(em, (0, 0), 22) * 0.8) * 0.8 * o.bloom
e = np.minimum(np.arange(S), np.arange(S)[::-1]).astype(np.float32)
f = np.clip(np.minimum(e[None, :], e[:, None]) / 60.0, 0, 1)
em *= (f * f * (3 - 2 * f))[..., None]
Image.fromarray(np.clip(em, 0, 255).astype(np.uint8)).save(o.out, optimize=True)
