"""Puntos sobre el mapa isométrico (GEO-01): proyección y datos para la web."""

from __future__ import annotations

from typing import Any

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
