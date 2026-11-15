"""Pega en el mapa solo lo que cambió una llamada del modelo sobre un recorte (receta de v14-v18).

El recorte (`--box`, 350-512 px del mapa) se subió a 1024 px y se pidió al modelo con el render al lado.
Aquí se baja la respuesta a ese tamaño y se mezcla con máscara suave: fuera de la máscara el mapa no cambia.

    python3 paste_patch.py mapa.png respuesta1024.png salida.png --box 3190 870 3540 1220 \
        [--thr 30] [--limit X0 Y0 X1 Y1 ...] [--color-match]

--thr          umbral de diferencia (suma RGB) para que un píxel cuente como cambiado (30 líneas finas, 45 costa)
--limit        cajas en coordenadas del RECORTE (0-350) fuera de las cuales no se pega nada; repetible
--color-match  ajusta media y desviación de la respuesta a las de la parte que apenas cambió (el modelo desvía el tono)
"""

import argparse

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("reply")
    ap.add_argument("out")
    ap.add_argument("--box", type=int, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--thr", type=float, default=30)
    ap.add_argument("--limit", type=int, nargs=4, action="append", metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--color-match", action="store_true")
    o = ap.parse_args()

    x0, y0, x1, y1 = o.box
    w, h = x1 - x0, y1 - y0
    base = np.asarray(Image.open(o.base).convert("RGB")).copy()
    old = base[y0:y1, x0:x1].astype(np.float32)
    new = np.asarray(Image.open(o.reply).convert("RGB").resize((w, h), Image.LANCZOS)).astype(np.float32)

    limit = np.zeros((h, w), np.uint8)
    for lx0, ly0, lx1, ly1 in o.limit or [(0, 0, w, h)]:
        limit[ly0:ly1, lx0:lx1] = 1
    if o.color_match:  # estadísticas de color solo en los píxeles que apenas cambian y quedan fuera de las cajas
        d0 = np.abs(new - old).sum(2)
        quiet = (d0 < np.percentile(d0, 60)) & (limit == 0 if o.limit else True)
        for c in range(3):
            a, b = old[..., c][quiet], new[..., c][quiet]
            new[..., c] = (new[..., c] - b.mean()) * (a.std() / (b.std() + 1e-3)) + a.mean()
        new = np.clip(new, 0, 255)

    m = ((np.abs(new - old).sum(2) > o.thr) & (limit > 0)).astype(np.uint8)
    m = cv2.morphologyEx(cv2.dilate(m, np.ones((7, 7), np.uint8)), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = m.astype(np.float32)
    edge = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :], np.minimum(np.arange(h), np.arange(h)[::-1])[:, None]
    fade = np.clip(np.minimum(*edge) / 20.0, 0, 1)  # el borde del recorte se funde a 20 px
    m = np.clip(cv2.GaussianBlur(m, (0, 0), 1.5) * 1.3, 0, 1) * fade
    base[y0:y1, x0:x1] = np.clip(old * (1 - m[..., None]) + new * m[..., None] + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(base).save(o.out)
    print(f"píxeles cambiados: {int((m > 0.5).sum())} de {w * h}")


if __name__ == "__main__":
    main()
