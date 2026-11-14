"""Cámaras (X-09): 61 con posición, enlaces https sin proxy, sondeo de disponibilidad."""

from __future__ import annotations

from typing import Any

from scripts.cameras import CREDIT, https, layer, probe

ROWS: list[dict[str, Any]] = [
    {
        "id": "05",
        "nombre": "Castelao - Grove",
        "lat": 42.21836,
        "lon": -8.74407,
        "url": "http://camaras.vigo.org/webcam/camv2.php?id=05",
    },
    {
        "id": "61",
        "nombre": "Sin posición",
        "lat": None,
        "lon": None,
        "url": "http://camaras.vigo.org/webcam/camv2.php?id=61",
    },
]


def test_https_reescribe_solo_http() -> None:
    assert https("http://camaras.vigo.org/x?id=1") == "https://camaras.vigo.org/x?id=1"
    assert https("https://a/b") == "https://a/b"


def test_capa_con_posicion_enlace_y_credito() -> None:
    geo = layer(ROWS)
    assert len(geo["features"]) == 1  # sin posición no se pinta
    p = geo["features"][0]["properties"]
    assert p["image_url"].startswith("https://camaras.vigo.org/") and p["link"] == p["image_url"]
    assert p["credit"] == CREDIT and p["online"] is None
    assert geo["features"][0]["geometry"]["coordinates"] == [-8.74407, 42.21836]


def test_sondeo_marca_las_que_no_devuelven_imagen() -> None:
    answers = {"https://camaras.vigo.org/webcam/camv2.php?id=05": b""}

    def fake(url: str) -> Any:
        return answers[url]

    status = probe(layer(ROWS)["features"], fake, pause_s=0)
    assert status == {"05": False}
    assert layer(ROWS, status)["features"][0]["properties"]["online"] is False
