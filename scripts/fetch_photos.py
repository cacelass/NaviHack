"""Fotos de los puntos, servidas desde la web: el servidor del Concello tarda segundos por foto.

Descarga la foto de cada punto (`image_url`, con la extensión corregida a .jpeg)
y la guarda reducida (480 px de ancho, WebP) en web/data/photos/<id>.webp.
`scripts/build_web_data.py` añade `photo` a cada punto si el fichero existe.

    uv run --no-project --with pillow python -m scripts.fetch_photos

Necesita Pillow solo aquí (no es dependencia del proyecto).
"""

from __future__ import annotations

import io
import json
import time
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
POINTS = ROOT / "data" / "points.json"
OUT = ROOT / "web" / "data" / "photos"
WIDTH = 480
USER_AGENT = "TinyVigo/0.1 (+https://github.com/cacelass/NaviHack)"


def main() -> int:
    doc = json.loads(POINTS.read_text(encoding="utf-8"))
    points = doc["points"] if isinstance(doc, dict) else doc
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    for p in points:
        url = (p.get("image_url") or "").replace("._lgjpeg", ".jpeg")
        target = OUT / f"{p['id']}.webp"
        if not url or target.exists():
            ok += target.exists()
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                img = Image.open(io.BytesIO(resp.read())).convert("RGB")
        except Exception as exc:  # noqa: BLE001 — una foto rota no para el resto
            print(f"sin foto {p['id']}: {exc}")
            continue
        img.thumbnail((WIDTH, WIDTH * 2))
        img.save(target, "WEBP", quality=72)
        ok += 1
        time.sleep(0.3)  # de una en una, con calma
    print(f"{ok} fotos en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
