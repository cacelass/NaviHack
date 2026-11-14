"""Edificios 3D (X-05): paginación, reproyección, huella+altura y completitud."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from scripts.buildings import fetch, stats, to_feature, utm29n_to_wgs84
from scripts.parkings import haversine_m

# Mismo vértice pedido al servidor en EPSG:25829 y en EPSG:4326 (refcat 2565705NG2726N).
UTM = (522485.5039, 4676300.1544)
WGS = (-8.72747353231821, 42.2385634755964)


def test_reproyeccion_coincide_con_el_servidor_a_menos_de_medio_metro() -> None:
    lon, lat = utm29n_to_wgs84(*UTM)
    assert haversine_m(lat, lon, WGS[1], WGS[0]) < 0.5


def test_pagina_de_2000_en_2000() -> None:
    seen: list[int] = []

    def fake(url: str) -> dict[str, Any]:
        q = parse_qs(urlparse(url).query)
        assert q["outSR"] == ["4326"] and q["resultRecordCount"] == ["2000"]
        off = int(q["resultOffset"][0])
        seen.append(off)
        n = 2000 if off < 4000 else 7
        return {"features": [{}] * n, "exceededTransferLimit": off < 4000}

    assert len(fetch((-8.73, 42.23, -8.70, 42.24), fake)) == 4007
    assert seen == [0, 2000, 4000]


def _esri(rings: list[list[list[float]]], **attrs: Any) -> dict[str, Any]:
    base = {"refcat": "X", "altura": 19.0, "z": 25.0, "ano_antiguedade": 1975, "ano_reforma": 0}
    return {"geometry": {"rings": rings}, "attributes": {**base, **attrs}}


CW = [[0.0, 0.0, 0], [0.0, 1.0, 0], [1.0, 1.0, 0], [1.0, 0.0, 0], [0.0, 0.0, 0]]  # exterior Esri
HOLE = [[0.2, 0.2, 0], [0.8, 0.2, 0], [0.8, 0.8, 0], [0.2, 0.8, 0], [0.2, 0.2, 0]]


def test_huella_con_altura_y_cota_base() -> None:
    f = to_feature(_esri([CW, HOLE]))
    assert f is not None
    assert f["geometry"]["type"] == "Polygon" and len(f["geometry"]["coordinates"]) == 2
    assert f["properties"]["height_m"] == 19.0 and f["properties"]["base_z"] == 6.0
    assert f["properties"]["year_reformed"] is None


def test_dos_exteriores_son_multipolygon() -> None:
    other = [[x + 5, y, z] for x, y, z in CW]
    f = to_feature(_esri([CW, other]))
    assert f is not None and f["geometry"]["type"] == "MultiPolygon"


def test_completitud_de_altura_y_anio_por_barrio() -> None:
    feats = [
        to_feature(_esri([CW], barrio="CENTRO", ano_reforma=2010)),
        to_feature(_esri([CW], barrio="CENTRO", altura=None)),
        to_feature(_esri([CW], barrio="BERBES", ano_antiguedade=1890)),
    ]
    s = stats([f for f in feats if f])
    assert s["height_complete"] == round(2 / 3, 4)
    assert s["newest_year_by_barrio"] == {"BERBES": 1890, "CENTRO": 2010}


def test_sin_geometria_se_descarta() -> None:
    assert to_feature({"geometry": {}, "attributes": {}}) is None
