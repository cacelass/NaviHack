"""Capa navideña del Concello (R-06): paginación, mapeo a points.json y overrides."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from scripts.christmas_layer import apply_overrides, build, fetch_all, text, to_point


def _feature(i: int, tipologia: str = "Elementos lumínicos") -> dict[str, Any]:
    return {
        "attributes": {
            "id": str(i),
            "nombre": f"Punto {i}",
            "nombre_gl": f"Punto {i} gl",
            "tipologia": tipologia,
            "descripcion_corta": "<p>Árbol de&nbsp;luces</p>",
            "horario_atencion": "<ul>\n<li>Encendido: 18:00 h.</li>\n<li>Apagado: 00:00 h.</li></ul>",
            "dir_nombre_via": "Praza da Porta do Sol",
            "dir_numero": 12,
        },
        "geometry": {"x": -8.72581284971326, "y": 42.23807222394629},
    }


def test_pagina_hasta_que_no_hay_mas() -> None:
    offsets: list[int] = []

    def fake_get(url: str) -> dict[str, Any]:
        q = parse_qs(urlparse(url).query)
        assert q["outSR"] == ["4326"] and int(q["resultRecordCount"][0]) <= 2000
        offset = int(q["resultOffset"][0])
        offsets.append(offset)
        rows = [_feature(offset + i) for i in range(2000 if offset == 0 else 35)]
        return {"features": rows, "exceededTransferLimit": offset == 0}

    assert len(fetch_all(fake_get)) == 2035
    assert offsets == [0, 2000]


def test_mapea_campos_del_concello() -> None:
    p = to_point(_feature(2552))
    assert p["id"] == "concello-2552" and p["type"] == "light"
    assert p["name"] == {"es": "Punto 2552", "gl": "Punto 2552 gl"}
    assert p["short"]["es"] == "Árbol de luces"
    assert p["schedule_text"]["es"] == "Encendido: 18:00 h.\nApagado: 00:00 h."
    assert (p["lat"], p["lon"]) == (42.238072, -8.725813)
    assert p["address"] == "Praza da Porta do Sol 12"
    assert p["status"] == "official"


def test_tipologia_desconocida_es_other() -> None:
    assert to_point(_feature(1, "Algo nuevo"))["type"] == "other"


def test_overrides_parchean_anaden_y_quitan() -> None:
    base = [to_point(_feature(1)), to_point(_feature(2))]
    out = apply_overrides(
        base,
        [
            {"id": "concello-1", "lat": 42.0},
            {"id": "concello-2", "remove": True},
            {"id": "press-noria-vialia", "name": {"es": "Noria"}},
        ],
    )
    by_id = {p["id"]: p for p in out}
    assert by_id["concello-1"]["lat"] == 42.0 and by_id["concello-1"]["status"] == "official"
    assert "concello-2" not in by_id
    assert by_id["press-noria-vialia"]["status"] == "not_confirmed"


def test_build_guarda_fetched_at_de_la_copia() -> None:
    out = build({"fetched_at": "2026-11-14T12:00:00+00:00", "features": [_feature(1)]}, [])
    assert out["fetched_at"] == "2026-11-14T12:00:00+00:00" and len(out["points"]) == 1


def test_text_vacio() -> None:
    assert text(None) is None and text("<p>&nbsp;</p>") is None
