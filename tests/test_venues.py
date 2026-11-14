"""Cruce de eventos con recintos (D-04): id, nombre, dirección y sin cruzar."""

from __future__ import annotations

from typing import Any

from scripts.venues import join, norm, venues_from_culture

CULTURE = [
    {
        "id": 180,
        "nombre": "Casa das Artes",
        "calle": "RUA POLICARPO SANZ",
        "numero": 15,
        "lat": 42.237,
        "lon": -8.721,
    },
    {
        "id": 190,
        "nombre": "Auditorio Mar de Vigo",
        "calle": "AVENIDA DE BEIRAMAR",
        "numero": 59,
        "lat": 42.24,
        "lon": -8.73,
    },
]
VENUES = venues_from_culture(CULTURE)


def _ev(id: int, venue_id: int | None = None, address: str | None = None) -> dict[str, Any]:
    return {"id": id, "title": f"evento {id}", "venue_id": venue_id, "address": address}


def test_norm_quita_tildes_y_puntuacion() -> None:
    assert norm("Rúa  Policarpo Sanz, 15.") == "rua policarpo sanz 15"


def test_por_nombre_y_aprende_el_id() -> None:
    events, unmatched, ids = join(
        [_ev(1, 1372, "Casa das Artes. Rúa Policarpo Sanz, 15, 3. 36202 Vigo.")], VENUES, {}
    )
    assert events[0]["venue"]["name"] == "Casa das Artes" and events[0]["venue_match"] == "name"
    assert ids == {"1372": "cultura-180"} and unmatched == []


def test_por_id_aprendido_aunque_no_traiga_direccion() -> None:
    events, _, _ = join([_ev(2, 1372)], VENUES, {"1372": "cultura-180"})
    assert events[0]["venue_match"] == "id" and events[0]["on_map"] is True


def test_por_calle_y_numero() -> None:
    events, _, _ = join([_ev(3, None, "Av. de Beiramar 59, Vigo")], VENUES, {})
    assert events[0]["venue"]["name"] == "Auditorio Mar de Vigo"
    assert events[0]["venue_match"] == "address"


def test_sin_cruzar_queda_registrado_y_fuera_del_mapa() -> None:
    events, unmatched, _ = join(
        [_ev(4, 3283), _ev(5, None, "Diversas localizaciones de la ciudad")], VENUES, {}
    )
    assert [e["on_map"] for e in events] == [False, False]
    assert [u["id"] for u in unmatched] == [4, 5]


def test_sin_ubicacion_solo_lista_y_no_se_registra() -> None:
    events, unmatched, _ = join([_ev(6)], VENUES, {})
    assert events[0]["on_map"] is False and unmatched == []
