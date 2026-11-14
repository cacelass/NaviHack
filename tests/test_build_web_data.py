"""Puntos sobre el mapa isométrico (GEO-01): proyección y datos para la web."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts import build_web_data
from scripts.build_web_data import CANVAS, ORIGIN, project, web_points


def test_el_arbol_de_porta_do_sol_es_el_centro_del_lienzo() -> None:
    assert project(*ORIGIN) == (CANVAS / 2, CANVAS / 2)


def test_este_va_a_la_derecha_norte_hacia_arriba_y_altura_sube() -> None:
    x, _ = project(ORIGIN[0], ORIGIN[1] + 0.001)
    _, y_n = project(ORIGIN[0] + 0.001, ORIGIN[1])
    _, y_z = project(*ORIGIN, 10.0)
    assert x > CANVAS / 2 and y_n < CANVAS / 2 and y_z < CANVAS / 2
    # 2 px/m: 100 m al este son ~193 px en pantalla (rumbo 15°)
    assert 185 < project(ORIGIN[0], ORIGIN[1] + 100 / 82_500)[0] - CANVAS / 2 < 200


def test_puntos_fuera_del_lienzo_y_sin_programa() -> None:
    pts: list[dict[str, Any]] = [
        {"id": "a", "type": "light", "name": {"es": "A"}, "lat": ORIGIN[0], "lon": ORIGIN[1]},
        {"id": "b", "type": "market", "name": {"es": "B"}, "lat": 42.20, "lon": -8.77},
        {"id": "c", "type": "light", "name": {"es": "C"}, "lat": None, "lon": None},
    ]
    out = web_points(pts, ["2026-12-25"], None)
    assert [p["id"] for p in out] == ["a", "b"]
    assert out[0]["on_map"] and (out[0]["x"], out[0]["y"]) == (0.5, 0.5)
    assert not out[1]["on_map"] and out[1]["programme"] is None


NORIA = {
    "id": "n",
    "type": "attraction",
    "name": {"es": "Noria"},
    "lat": 42.236839,
    "lon": -8.708156,
}


def test_la_noria_entra_si_el_dibujo_publicado_es_mas_ancho(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La noria cae en x≈1,39 del lienzo: fuera del 3x3 viejo y de v7 (4096), dentro de v8 (5120)."""
    monkeypatch.setattr(build_web_data, "DRAWN", (float(CANVAS), float(CANVAS)))
    viejo = web_points([NORIA], [], None)[0]
    monkeypatch.setattr(build_web_data, "DRAWN", (5120.0, float(CANVAS)))
    ancho = web_points([NORIA], [], None)[0]
    assert 1.38 < ancho["x"] < 1.40 and ancho["x"] == viejo["x"]  # x sigue normalizada por 3072
    assert not viejo["on_map"] and ancho["on_map"]


def test_drawn_lee_el_manifest_publicado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tiles = tmp_path / "web" / "tiles"
    (tiles / "v9").mkdir(parents=True)
    (tiles / "current.json").write_text(json.dumps({"version": "v9"}))
    (tiles / "v9" / "manifest.json").write_text(
        json.dumps({"width": 5120, "height": 3072, "offset": {"x": 0, "y": 0}})
    )
    monkeypatch.setattr(build_web_data, "ROOT", tmp_path)
    assert build_web_data._drawn() == (5120, 3072)


def test_drawn_sin_manifest_es_el_lienzo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_web_data, "ROOT", tmp_path)
    assert build_web_data._drawn() == (CANVAS, CANVAS)
