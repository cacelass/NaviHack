"""¿Respeta el dibujo la estructura del render? Correlación de bordes (0 = nada que ver, 1 = idéntico).
Uso: python3 fidelity.py render.png x0 y0 x1 y1 imagen1.png [imagen2.png ...]
Compara el mapa de bordes (Sobel del brillo, suavizado) de cada imagen con el del render en esa caja.
Un dibujo fiel al render tiene una correlación parecida a la del dibujo original; si cae mucho, el modelo
inventó calles o edificios.
"""

import sys

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def edges(path: str, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    g = np.asarray(Image.open(path).convert("L").crop(box)).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 1.6)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    m = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 2.5)
    return (m - m.mean()) / (m.std() + 1e-6)


if __name__ == "__main__":
    render = sys.argv[1]
    box = tuple(int(v) for v in sys.argv[2:6])
    r = edges(render, box)
    for p in sys.argv[6:]:
        e = edges(p, box)
        print(f"{float((r * e).mean()):5.3f}  {p}")
