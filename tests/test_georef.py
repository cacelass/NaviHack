"""La georreferencia del mapa: ida y vuelta, y que el render diga lo mismo."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from pipeline import georef
from pipeline.render import params as render_params
from pipeline.render import silhouette

FIXTURE = (
    Path(__file__).resolve().parents[1] / "pipeline" / "render" / "fixtures" / "points-3x3.json"
)


def test_los_parametros_salen_del_renderer_original() -> None:
    """Si alguien toca la cámara o la descarga, el JSON tiene que regenerarse."""
    assert render_params.main(["--check"]) == 0


def test_el_centro_del_lienzo_es_porta_do_sol() -> None:
    p = georef.params()
    assert p.to_pixel(p.geo.lat0, p.geo.lon0) == (1536.0, 1536.0)


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (42.23807, -8.72581),  # Porta do Sol
        (42.23931, -8.72242),  # Alameda
        (42.236867, -8.7155697),  # García Barbón
        (42.234, -8.7135),  # Vialia
        (42.2259, -8.7391),  # esquina suroeste de la ortofoto
    ],
)
@pytest.mark.parametrize("z", [0.0, 12.5, 46.4])
def test_ida_y_vuelta(lat: float, lon: float, z: float) -> None:
    p = georef.params()
    back_lat, back_lon = p.to_latlon(*p.to_pixel(lat, lon, z), z)
    assert back_lat == pytest.approx(lat, abs=1e-9)
    assert back_lon == pytest.approx(lon, abs=1e-9)


def test_la_altura_solo_mueve_la_fila() -> None:
    p = georef.params()
    ground = p.to_pixel(42.23807, -8.72581)
    tall = p.to_pixel(42.23807, -8.72581, 46.4)
    assert tall[0] == ground[0]
    # 1 px de pantalla por metro = sc * cos(45°)
    assert ground[1] - tall[1] == pytest.approx(46.4 * 2 * math.cos(math.radians(45)), abs=1e-9)


# Los cuatro hitos de la zona nueva, con el píxel que les toca en el lienzo 3x3.
# Calculados con la fórmula del renderer escrita a mano aquí, no con georef().
KNOWN = {
    "porta-do-sol": (42.238072, -8.725813, 1535.6, 1535.6),
    "alameda": (42.23931, -8.72242, 2147.2, 1449.7),
    "garcia-barbon": (42.236867, -8.7155697, 3097.1, 2027.9),
    "vialia": (42.234, -8.7135, 3261.4, 2526.3),
}


@pytest.mark.parametrize("name", sorted(KNOWN))
def test_puntos_conocidos(name: str) -> None:
    lat, lon, want_px, want_py = KNOWN[name]
    p = georef.params()
    x = (lon - p.geo.lon0) * p.geo.m_per_deg_lon
    y = (lat - p.geo.lat0) * p.geo.m_per_deg_lat
    head = math.radians(p.camera.head_deg)
    tilt = math.radians(p.camera.tilt_deg)
    px = 1536 + p.camera.sc * (math.cos(head) * x - math.sin(head) * y)
    py = 1536 + p.camera.sc * (-math.sin(tilt) * (math.sin(head) * x + math.cos(head) * y))
    assert (px, py) == (pytest.approx(want_px, abs=0.1), pytest.approx(want_py, abs=0.1))
    assert p.to_pixel(lat, lon) == (pytest.approx(px, abs=1e-6), pytest.approx(py, abs=1e-6))


def test_teselas_de_los_hitos() -> None:
    """Los hitos caen en estas teselas: es lo que decide el bloque de la zona nueva."""
    p = georef.params()
    tiles = {name: p.tile_of(*p.to_pixel(lat, lon)) for name, (lat, lon, *_) in KNOWN.items()}
    assert tiles == {
        "porta-do-sol": (1, 1),
        "alameda": (1, 2),
        "garcia-barbon": (1, 3),
        "vialia": (2, 3),
    }
    assert p.canvas("expansion").width == 4096
    assert p.canvas("expansion").height == 3072


def test_bloque_minimo_de_teselas_con_medio_de_margen() -> None:
    # Dos puntos en el centro de una misma tesela: el margen la amplía de 1 a 4.
    assert georef.tile_block([(1200, 1200)], 512) == (0, 0, 1, 1)
    # Un punto justo en el borde: el margen obliga a coger la tesela de al lado.
    assert georef.tile_block([(1024, 1024)], 512) == (0, 0, 1, 1)


def test_los_puntos_del_concello_caen_sobre_su_edificio_en_el_render() -> None:
    """Contra el mapa de alturas del render 3x3, no contra la fórmula.

    ``fixtures/points-3x3.json`` guarda, por punto, lo que predice la geometría
    (cámara + edificios del Concello) y lo que pinta el render. Este test vuelve
    a predecir con el código actual y exige que siga cuadrando con el render:
    si la proyección se mueve un píxel, el punto cae sobre otro edificio.
    """
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    p = georef.params()
    scene = silhouette.Scene(p, silhouette.load_buildings(p))
    inside = [row for row in doc["points"] if row["inside"]]
    assert len(inside) == 26, "el fixture tiene que cubrir los 26 puntos dentro del lienzo"

    failures = []
    for row in inside:
        px, py = p.to_pixel(row["lat"], row["lon"])
        assert (px, py) == (pytest.approx(row["px"], abs=0.01), pytest.approx(row["py"], abs=0.01))
        pred = scene.predict(px, py)
        seen = row["seen"]
        if pred.kind == "wall" or pred.edge <= doc["edge_px"]:
            ok = 0.0 <= seen <= pred.height + doc["tolerance_m"]
        else:
            ok = abs(seen - pred.height) <= doc["tolerance_m"]
        if not ok:
            failures.append((row["id"], pred.kind, pred.height, seen))
    assert not failures, failures
