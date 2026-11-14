"""
app.points — cargar y procesar los puntos navideños de Vigo.

Lee ``data/points.json`` y expone funciones para listar, filtrar y resumir
los puntos de decoracion navidenia de Vigo.

Uso::

    from app.points import load_points, summary

    pts = load_points()
    for p in summary(pts):
        print(p)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.paths import ROOT_DIR


def _points_path() -> Path:
    """Devuelve la ruta al fichero de puntos."""
    return ROOT_DIR / "data" / "points.json"


def load_points() -> list[dict[str, Any]]:
    """
    Carga los puntos navideños desde ``data/points.json``.

    Lanza ``FileNotFoundError`` si el fichero no existe y ``ValueError`` si
    el JSON no tiene la estructura esperada (``{"points": [...]}``).
    """
    path = _points_path()
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el fichero de puntos: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if "points" not in raw:
        raise ValueError("El JSON de puntos no tiene la clave 'points'")

    points: list[dict[str, Any]] = raw["points"]
    if not isinstance(points, list):
        raise ValueError("La clave 'points' debe ser una lista")

    return points


def summary(
    points: list[dict[str, Any]] | None = None,
    *,
    lang: str = "es",
) -> list[dict[str, Any]]:
    """
    Devuelve un resumen de cada punto: id, nombre, tipo y estado.

    Args:
        points: lista de puntos. Si es ``None`` se carga desde disco.
        lang: idioma del nombre ("es", "gl", "en").

    Returns:
        Lista de dicts con claves ``id``, ``name``, ``type``, ``status``.
    """
    if points is None:
        points = load_points()

    results: list[dict[str, Any]] = []
    for p in points:
        name_obj = p.get("name", {})
        name = name_obj.get(lang, name_obj.get("es", str(p.get("id", "?"))))
        results.append(
            {
                "id": p.get("id", ""),
                "name": name,
                "type": p.get("type", "unknown"),
                "status": p.get("status", "unknown"),
            }
        )

    return results


def count_by_type(points: list[dict[str, Any]] | None = None) -> dict[str, int]:
    """
    Cuenta los puntos por tipo.

    >>> pts = load_points()
    >>> counts = count_by_type(pts)
    >>> isinstance(counts, dict)
    True
    """
    if points is None:
        points = load_points()

    counts: dict[str, int] = {}
    for p in points:
        t = p.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1

    return counts
