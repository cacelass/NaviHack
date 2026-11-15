"""El medidor del origen del lienzo recupera un desfase que se le introduce a propósito.

``pipeline/render/calibrate_origin.py`` contrasta la georreferencia con el mar del MDT05. Si no fuese capaz de
encontrar un desplazamiento conocido, sus cifras sobre los renders reales no valdrían nada. Aquí el «agua del
render» es el propio mar del MDT05 proyectado con el origen del lienzo movido (dx, dy) píxeles: el estimador
tiene que devolver (dx, dy).

Necesita numpy y OpenCV (no están en el entorno base del proyecto): sin ellos el fichero se salta.
"""

from __future__ import annotations

from typing import Any

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("cv2")

from pipeline import georef  # noqa: E402
from pipeline.render import calibrate_origin as co  # noqa: E402
from scripts import elevation  # noqa: E402

CANVAS = "wide"
SEARCH = 16
# Caja del lienzo con costa de muelles y dársenas dentro del recorte del MDT05 (no cruza su borde norte).
INNER = (520, 840, 1180, 1260)
# numpy llega por importorskip, así que mypy no lo ve como tipo: el array del MDT va como Any
World = tuple[georef.RenderParams, elevation.Grid, Any]


def _moved(params: georef.RenderParams, dx: float, dy: float) -> georef.RenderParams:
    """El mismo renderer con el origen del lienzo desplazado (dx, dy) píxeles."""
    c = params.canvas(CANVAS)
    canvases = dict(params.canvases)
    canvases[CANVAS] = georef.Canvas(c.width, c.height, c.origin_x + dx, c.origin_y + dy)
    return georef.RenderParams(params.camera, params.geo, canvases)


@pytest.fixture(scope="module")
def world() -> World:
    grid = elevation.load()
    assert grid is not None, "falta data/elevation/mdt05_core.asc.gz"
    return georef.params(), grid, co.dem_array(grid)


@pytest.mark.parametrize(("dx", "dy"), [(0.0, 0.0), (7.0, -5.0), (-12.0, 9.0), (4.0, 11.0)])
def test_recupera_un_desfase_conocido(world: World, dx: float, dy: float) -> None:
    params, grid, dem = world
    x0, y0, x1, y1 = INNER
    sea, valid = co.sea_on_canvas(params, grid, dem, CANVAS, INNER)
    assert 0.1 < sea.mean() < 0.9, "la caja de prueba tiene que contener costa"
    outer = (x0 - SEARCH, y0 - SEARCH, x1 + SEARCH, y1 + SEARCH)
    water, _ = co.sea_on_canvas(_moved(params, dx, dy), grid, dem, CANVAS, outer)
    found = co.best_shift(sea, valid, water, SEARCH)
    assert found.dx == pytest.approx(dx, abs=0.75)
    assert found.dy == pytest.approx(dy, abs=0.75)
    assert found.iou_best > 0.97  # el mismo mar desplazado: coincide casi entero


def test_un_desfase_de_un_pixel_se_ve() -> None:
    """La resolución del método: 1 px del lienzo (0,5 m de suelo) se distingue de 0."""
    params = georef.params()
    grid = elevation.load()
    assert grid is not None
    dem = co.dem_array(grid)
    sea, valid = co.sea_on_canvas(params, grid, dem, CANVAS, INNER)
    x0, y0, x1, y1 = INNER
    outer = (x0 - SEARCH, y0 - SEARCH, x1 + SEARCH, y1 + SEARCH)
    water, _ = co.sea_on_canvas(_moved(params, 1.0, 0.0), grid, dem, CANVAS, outer)
    assert co.best_shift(sea, valid, water, SEARCH).dx == pytest.approx(1.0, abs=0.4)


def test_el_agua_con_el_tamano_equivocado_se_rechaza(world: World) -> None:
    params, grid, dem = world
    sea, valid = co.sea_on_canvas(params, grid, dem, CANVAS, INNER)
    with pytest.raises(ValueError, match="water debe medir"):
        co.best_shift(sea, valid, sea, SEARCH)
