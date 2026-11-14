"""Incrusta los datos del primer vistazo en web/index.html (MAP-01).

El criterio dice que los datos del mapa que necesita el primer vistazo van
dentro de la página, no en una petición más. Este script lee
``web/data/points.json`` y lo escribe entre los marcadores
``<!-- tv-baked-points -->`` y ``<!-- /tv-baked-points -->`` de
``web/index.html``. Idempotente: se puede ejecutar tantas veces como quieras.

    python -m scripts.bake_first_view
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "web" / "index.html"
POINTS = ROOT / "web" / "data" / "points.json"

START = "<!-- tv-baked-points -->"
END = "<!-- /tv-baked-points -->"


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")
    if START not in html or END not in html:
        raise SystemExit(f"faltan los marcadores {START} / {END} en {INDEX}")

    data = json.loads(POINTS.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    block = (
        f'{START}\n<script type="application/json" id="tv-baked-points">{payload}</script>\n{END}'
    )
    head, rest = html.split(START, 1)
    _, tail = rest.split(END, 1)
    INDEX.write_text(head + block + tail, encoding="utf-8")
    print(f"primer vistazo incrustado: {len(payload)} bytes de puntos en {INDEX.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
