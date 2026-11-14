"""Datos para la web: puntos de Navidad sobre el mapa isométrico + textos (GEO-01).

El render del mapa es ortográfico (inclinación 45°, rumbo 15° al oeste del
norte, 2 px/m, lienzo 3072 px) y su centro es el **Árbol de Porta do Sol**:
calibrado proyectando el mar del MDT05 sobre el agua del mapa dibujado, el
origen sale a 1 m del árbol (42.238082, -8.725818 frente a 42.238072, -8.725813).
La cota de cada punto sale del MDT05 (D-11); sin cota se usa la del origen.

    python -m scripts.build_web_data      # escribe web/data/points.json y web/data/i18n/

Stdlib pura.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

from scripts import elevation

try:  # GEO-01: la transformación oficial del render (pipeline/georef.py)
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
    import georef as _georef  # type: ignore[import-not-found]
except Exception:  # noqa: BLE001 — sin el módulo se usan las constantes de abajo
    _georef = None

ROOT = Path(__file__).resolve().parent.parent
POINTS = ROOT / "data" / "points.json"
PROGRAMME = ROOT / "data" / "programme_2026.json"
OUT = ROOT / "web" / "data"

ORIGIN = (42.23807, -8.72581)  # Árbol de Porta do Sol = centro del lienzo (render-params de GEO-01)
CANVAS = 3072


def _drawn() -> tuple[float, float]:
    """Tamaño del dibujo publicado (web/tiles/current.json): el bloque puede crecer hacia Vialia."""
    try:
        tiles = ROOT / "web" / "tiles"
        version = json.loads((tiles / "current.json").read_text(encoding="utf-8"))["version"]
        m = json.loads((tiles / version / "manifest.json").read_text(encoding="utf-8"))
        ox, oy = (m.get("offset") or {}).get("x", 0), (m.get("offset") or {}).get("y", 0)
        return ox + m["width"], oy + m["height"]
    except (OSError, KeyError, ValueError):
        return CANVAS, CANVAS


DRAWN = _drawn()
SCALE = 2.0  # px por metro
TILT = math.radians(45)
HEAD = math.radians(-15)
M_PER_DEG_LAT = 111_320.0


def project(lat: float, lon: float, z: float = 0.0) -> tuple[float, float]:
    """(lat, lon, cota m) -> píxel del lienzo 3072 del render.

    Usa pipeline/georef.py (GEO-01, parámetros del renderer original) si está; si no,
    la misma cámara con constantes (coinciden a < 0,5 px en los cuatro puntos de control).
    """
    if _georef is not None:
        return _georef.to_pixel(lat, lon, z)
    x = (lon - ORIGIN[1]) * M_PER_DEG_LAT * math.cos(math.radians(ORIGIN[0]))
    y = (lat - ORIGIN[0]) * M_PER_DEG_LAT
    u = math.cos(HEAD) * x - math.sin(HEAD) * y
    d = math.sin(HEAD) * x + math.cos(HEAD) * y
    v = -math.sin(TILT) * d - math.cos(TILT) * z
    return CANVAS / 2 + SCALE * u, CANVAS / 2 + SCALE * v


def web_points(
    points: list[dict[str, Any]], holidays: list[str], grid: elevation.Grid | None
) -> list[dict[str, Any]]:
    origin_z = (grid.elevation(*ORIGIN) if grid else None) or 0.0
    out = []
    for p in points:
        if p.get("lat") is None or p.get("lon") is None:
            continue
        z = (grid.elevation(p["lat"], p["lon"]) if grid else None) or origin_z
        cx, cy = project(p["lat"], p["lon"], z - origin_z)
        programme = p.get("programme")
        out.append(
            {
                "id": p["id"],
                "type": p["type"],
                "name": p["name"],
                "short": p.get("short"),
                "long": p.get("long"),
                "schedule_text": p.get("schedule_text"),
                "address": p.get("address"),
                "image_url": p.get("image_url"),
                "photo": f"data/photos/{p['id']}.webp"
                if (OUT / "photos" / f"{p['id']}.webp").exists()
                else None,
                "lat": p["lat"],
                "lon": p["lon"],
                "x": round(cx / CANVAS, 5),
                "y": round(cy / CANVAS, 5),
                "on_map": 0 <= cx <= DRAWN[0] and 0 <= cy <= DRAWN[1],
                "programme": {**programme, "holidays": holidays} if programme else None,
                "last_verified": p.get("last_verified"),
                "status": p.get("status"),  # official | not_confirmed (D-18)
            }
        )
    return out


def elevation_grid(grid: elevation.Grid, step: int = 4) -> dict[str, Any]:
    """Rejilla reducida (~20 m) para proyectar rutas en el navegador."""
    rows = [
        [round(grid.rows[i][j]) for j in range(0, grid.ncols, step)]
        for i in range(0, grid.nrows, step)
    ]
    return {
        "west": grid.xll,
        "north": grid.yll + grid.nrows * grid.dy,
        "dx": grid.dx * step,
        "dy": grid.dy * step,
        "rows": rows,
        "origin_z": grid.elevation(*ORIGIN),
    }


def main() -> int:
    doc = json.loads(POINTS.read_text(encoding="utf-8"))
    points = doc["points"] if isinstance(doc, dict) else doc
    holidays = json.loads(PROGRAMME.read_text(encoding="utf-8"))["holidays"]
    grid = elevation.load()
    result = web_points(points, holidays, grid)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "points.json").write_text(
        json.dumps({"points": result}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    if grid:
        (OUT / "elevation.json").write_text(
            json.dumps(elevation_grid(grid), separators=(",", ":")), encoding="utf-8"
        )
    shutil.copyfile(ROOT / "data" / "venues_ids.json", OUT / "venues.json")
    (OUT / "i18n").mkdir(exist_ok=True)
    for lang in ("gl", "es", "en"):
        shutil.copyfile(ROOT / "i18n" / f"{lang}.json", OUT / "i18n" / f"{lang}.json")
    shown = sum(p["on_map"] for p in result)
    print(f"{len(result)} puntos, {shown} dentro del mapa -> web/data/points.json")
    # MAP-01: el primer vistazo lleva sus datos dentro de la página.
    from scripts.bake_first_view import main as bake

    bake()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
