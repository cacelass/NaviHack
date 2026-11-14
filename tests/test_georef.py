"""La georreferencia del mapa: ida y vuelta, y que el render diga lo mismo."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
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


def test_geometria_y_render_cuentan_lo_mismo() -> None:
    """Coherencia interna: la altura que predice la geometría es la que pinta el render.

    OJO con lo que prueba y lo que no. ``fixtures/points-3x3.json`` guarda, por
    punto, lo que predice la cámara con los edificios del Concello y lo que pinta
    el mapa de alturas del render 3x3. Si la proyección se moviera un píxel, el
    punto caería sobre otro edificio y esto fallaría. Pero no dice nada sobre si
    las coordenadas del punto son buenas: eso lo miran los tests de OSM de abajo.
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


# ── Comprobaciones con una fuente independiente: OpenStreetMap ───────────────
# Coordenadas de OSM (Nominatim, 2026-11-14), no del Concello ni nuestras.
OSM_PORTA_DO_SOL = (42.2379083, -8.7251412)  # vía peatonal «Porta do Sol»
OSM_ESTACION_URZAIZ = (42.2349579, -8.7114407)  # edificio de la estación Vigo-Urzáiz
CONCELLO_ARBOL = (42.238072, -8.725813)  # punto 2552 de data/points.json


def _footprints() -> list[silhouette.Building]:
    return silhouette.load_buildings(georef.params(), east=True)


def test_porta_do_sol_de_osm_cae_en_espacio_abierto() -> None:
    """Un hito conocido tiene que caer en la plaza, no dentro de un edificio."""
    p = georef.params()
    x, y = p.geo.metres(*OSM_PORTA_DO_SOL)
    assert silhouette.contains(_footprints(), x, y) is None
    assert p.tile_of(*p.to_pixel(*OSM_PORTA_DO_SOL)) == (1, 1)


def test_estacion_urzaiz_de_osm_cae_en_la_tesela_de_vialia() -> None:
    """Contraste de la zona nueva: la estación cae en la tesela (2, 3), en suelo."""
    p = georef.params()
    x, y = p.geo.metres(*OSM_ESTACION_URZAIZ)
    assert silhouette.contains(_footprints(), x, y) is None
    assert p.tile_of(*p.to_pixel(*OSM_ESTACION_URZAIZ, canvas="expansion")) == (2, 3)


def test_el_punto_del_concello_del_arbol_esta_lejos_de_la_plaza() -> None:
    """Discrepancia conocida: no coloques el árbol con la coordenada del Concello.

    Dista unos 58 m de la vía peatonal de Porta do Sol en OSM; el árbol pintado en
    el mapa (v6) está a ~20 m de esa vía. Si el Concello corrige el punto, este
    test avisa para que se revise.
    """
    p = georef.params()
    a = p.geo.metres(*CONCELLO_ARBOL)
    b = p.geo.metres(*OSM_PORTA_DO_SOL)
    assert 40 < math.dist(a, b) < 80


def test_osd_normaliza_por_el_ancho() -> None:
    p = georef.params()
    x, y = p.to_osd(p.geo.lat0, p.geo.lon0)
    assert (x, y) == (0.5, 0.5)  # el centro del lienzo cuadrado
    # En el lienzo ancho la y también se divide por el ANCHO: 1536 / 4096.
    x, y = p.to_osd(p.geo.lat0, p.geo.lon0, canvas="expansion")
    assert (x, y) == (pytest.approx(1536 / 4096), pytest.approx(1536 / 4096))


@pytest.mark.skipif(shutil.which("node") is None, reason="hace falta node para el helper TS")
def test_el_helper_ts_da_lo_mismo_que_python() -> None:
    """georef.ts es un espejo: mismos números que el módulo Python en los cuatro hitos."""
    p = georef.params()
    cases = [(lat, lon, z) for lat, lon, *_ in KNOWN.values() for z in (0.0, 30.0)]
    script = (
        "import { toPixel, toLatLon, toOsd } from './pipeline/georef.ts';"
        f"const cases = {json.dumps(cases)};"
        "console.log(JSON.stringify(cases.map(([lat, lon, z]) => {"
        "const p = toPixel(lat, lon, z, 'expansion');"
        "return [p.x, p.y, ...Object.values(toLatLon(p.x, p.y, z, 'expansion')),"
        "...Object.values(toOsd(lat, lon, z, 'expansion'))]; })));"
    )
    root = Path(__file__).resolve().parents[1]
    run = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            "--input-type=module",
            "-e",
            script,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    for (lat, lon, z), got in zip(cases, json.loads(run.stdout), strict=True):
        px, py = p.to_pixel(lat, lon, z, "expansion")
        ox, oy = p.to_osd(lat, lon, z, "expansion")
        assert got == pytest.approx([px, py, lat, lon, ox, oy], abs=1e-9)
