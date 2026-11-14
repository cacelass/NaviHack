"""Salto de color en cada costura frente a lo normal dentro de una tesela. Solo lectura.
Uso: python3 seam_metric.py imagen.png [imagen2.png ...]   (imprime una tabla por imagen)
Salto = diferencia media (suma RGB) entre 3 px a cada lado; base = el mismo salto a +-40 y +-60 px.
Ratio 1.0 = la costura no se nota; el 3x3 original tenia 2-3.4x.
"""

import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

SEAMS = [  # (nombre, eje, posicion, desde, hasta)
    ("H y=1024 col0", "h", 1024, 0, 1024),
    ("H y=1024 col1", "h", 1024, 1024, 2048),
    ("H y=1024 col2", "h", 1024, 2048, 3072),
    ("H y=2048 col0", "h", 2048, 0, 1024),
    ("H y=2048 col1", "h", 2048, 1024, 2048),
    ("H y=2048 col2", "h", 2048, 2048, 3072),
    ("V x=1024 fila1", "v", 1024, 1024, 2048),
    ("V x=1024 fila2", "v", 1024, 2048, 3072),
    ("V x=2048 fila1", "v", 2048, 1024, 2048),
    ("V x=2048 fila2", "v", 2048, 2048, 3072),
]


def jump(a: np.ndarray, kind: str, pos: int, lo: int, hi: int) -> float:
    if kind == "h":
        t = a[pos - 3 : pos, lo:hi].mean(0)
        b = a[pos : pos + 3, lo:hi].mean(0)
    else:
        t = a[lo:hi, pos - 3 : pos].mean(1)
        b = a[lo:hi, pos : pos + 3].mean(1)
    return float(np.abs(t - b).sum(1).mean())


def table(path: str) -> dict[str, float]:
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    out = {}
    print(f"\n{path}")
    print(f"{'costura':18s} {'salto':>7s} {'base':>7s} {'ratio':>6s}")
    for name, kind, pos, lo, hi in SEAMS:
        j = jump(a, kind, pos, lo, hi)
        b = float(np.mean([jump(a, kind, pos + o, lo, hi) for o in (-60, -40, 40, 60)]))
        out[name] = j / b
        print(f"{name:18s} {j:7.1f} {b:7.1f} {j / b:5.2f}x")
    print(f"{'media':18s} {'':7s} {'':7s} {np.mean(list(out.values())):5.2f}x")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        table(p)
