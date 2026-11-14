"""Elevación MDT05 (D-11): lectura ArcGrid, pendiente, tramos y huecos de datos."""

from __future__ import annotations

import math
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from scripts.elevation import (
    M_PER_DEG_LAT,
    Grid,
    dump_ascii_grid,
    easy_walk_factor,
    fetch,
    load,
    parse_ascii_grid,
)

LAT0, LON0 = 42.2350, -8.7220
D = 0.000045  # ≈ 5 m en latitud


def ramp(grade_pct: float, n: int = 20, nodata_at: tuple[int, int] | None = None) -> Grid:
    """Rampa que sube hacia el norte con la pendiente pedida."""
    step = D * M_PER_DEG_LAT * grade_pct / 100
    rows = []
    for i in range(n):  # i = 0 es la fila norte
        z = (n - 1 - i) * step
        rows.append(tuple(-9999.0 if (i, j) == nodata_at else z for j in range(n)))
    return Grid(n, n, LON0, LAT0, D, D, -9999.0, tuple(rows))


def test_lee_la_respuesta_multipart_del_wcs() -> None:
    body = (
        "--wcs\nContent-Type: application/asc\n\n"
        "ncols        3\nnrows        2\nxllcorner    -8.722\nyllcorner    42.235\n"
        "dx           0.0001\ndy           0.0001\n 1 2 3 \n 4 5 6 \n--wcs--\n"
    )
    grid = parse_ascii_grid(body)
    assert (grid.ncols, grid.nrows) == (3, 2)
    assert grid.rows == ((1, 2, 3), (4, 5, 6))
    assert grid.nodata is None


def test_rechaza_lo_que_no_es_un_arcgrid() -> None:
    with pytest.raises(ValueError):
        parse_ascii_grid("<ExceptionReport>fuera de cobertura</ExceptionReport>")


def test_pendiente_de_una_rampa_conocida() -> None:
    grid = ramp(8.0)
    centro = (LAT0 + 10 * D, LON0 + 10 * D)
    assert grid.slope_pct(*centro) == pytest.approx(8.0, rel=1e-6)


def test_tramo_cuesta_arriba_y_su_coste_easy_walk() -> None:
    grid = ramp(10.0)
    a = (LAT0 + 4 * D, LON0 + 10 * D)
    b = (LAT0 + 14 * D, LON0 + 10 * D)
    g = grid.grade(a, b, step_m=5)
    assert g is not None
    assert g["distance_m"] == pytest.approx(10 * D * M_PER_DEG_LAT)
    assert g["climb_m"] == pytest.approx(g["distance_m"] * 0.10, rel=1e-6)
    assert g["descent_m"] == pytest.approx(0)
    assert g["max_grade_pct"] == pytest.approx(10.0, rel=1e-6)
    assert 1.0 < easy_walk_factor(g) < 4.0
    # De vuelta es bajada: misma pendiente, sin subida.
    back = grid.grade(b, a, step_m=5)
    assert back is not None and back["climb_m"] == pytest.approx(0)


def test_llano_no_penaliza_y_muy_empinado_si() -> None:
    llano = ramp(0.0).grade((LAT0 + 4 * D, LON0 + 5 * D), (LAT0 + 14 * D, LON0 + 5 * D))
    assert llano is not None and easy_walk_factor(llano) == 1.0
    empinado = ramp(20.0).grade((LAT0 + 4 * D, LON0 + 5 * D), (LAT0 + 14 * D, LON0 + 5 * D))
    assert easy_walk_factor(empinado) == 4.0


def test_sin_datos_devuelve_none_y_no_penaliza() -> None:
    grid = ramp(8.0, nodata_at=(10, 10))
    fuera = (LAT0 - 1.0, LON0)
    assert grid.elevation(*fuera) is None
    assert grid.slope_pct(*fuera) is None
    hueco = (LAT0 + 9.5 * D, LON0 + 10.5 * D)
    assert grid.elevation(*hueco) is None
    tramo = grid.grade((LAT0 + 2 * D, LON0 + 10.5 * D), (LAT0 + 18 * D, LON0 + 10.5 * D))
    assert tramo is None
    assert easy_walk_factor(tramo) == 1.0


def test_load_sin_fichero_es_none(tmp_path: Path) -> None:
    assert load(tmp_path / "no-existe.asc.gz") is None


def test_fetch_pide_la_cobertura_de_5_m_y_guarda_lo_que_lee(tmp_path: Path) -> None:
    src = ramp(5.0, n=4)
    seen: list[str] = []

    def fake(url: str) -> str:
        seen.append(url)
        return "--wcs\n\n" + dump_ascii_grid(src) + "--wcs--\n"

    out = tmp_path / "mdt.asc.gz"
    grid = fetch((-8.73, 42.23, -8.71, 42.24), get=fake, out=out)
    q = parse_qs(urlparse(seen[0]).query)
    assert q["COVERAGEID"] == ["Elevacion4258_5"] and q["FORMAT"] == ["ArcGrid"]
    assert q["SUBSET"] == ["Lat(42.23,42.24)", "Long(-8.73,-8.71)"]
    again = load(out)
    assert again is not None and again.ncols == grid.ncols == 4
    for r0, r1 in zip(src.rows, again.rows, strict=True):
        assert all(math.isclose(x, y, abs_tol=0.01) for x, y in zip(r0, r1, strict=True))
