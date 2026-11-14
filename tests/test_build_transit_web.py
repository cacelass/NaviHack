"""Datos de transporte para la web (X-04): directos al centro y parada cercana."""

from __future__ import annotations

from scripts.build_transit_web import centre_stops, daytime_served, direct_to_centre, nearest_stop

STOPS = [
    {"id": "C", "lat": 42.23807, "lon": -8.72581},  # Porta do Sol
    {"id": "A", "lat": 42.2105, "lon": -8.7745},  # Samil
    {"id": "B", "lat": 42.2200, "lon": -8.7400},
]


def _st(trip: str, stop: str, seq: int, t: str) -> dict[str, str]:
    return {
        "trip_id": trip,
        "stop_id": stop,
        "stop_sequence": str(seq),
        "arrival_time": t,
        "departure_time": t,
    }


def test_parada_del_centro_es_la_cercana_a_las_luces() -> None:
    assert centre_stops(STOPS, [(42.23807, -8.72581)]) == {"C"}


def test_directos_al_centro_con_minutos_de_viaje() -> None:
    stop_times = {
        "t1": [
            _st("t1", "A", 1, "18:23:00"),
            _st("t1", "B", 2, "18:30:00"),
            _st("t1", "C", 3, "18:40:00"),
        ],
        "t2": [
            _st("t2", "C", 1, "19:00:00"),
            _st("t2", "A", 2, "19:20:00"),
        ],  # sale del centro: no cuenta
    }
    trips = {
        "t1": {"route_id": "r", "service_id": "LAB", "trip_headsign": "PRAZA"},
        "t2": {"route_id": "r", "service_id": "LAB"},
    }
    out = direct_to_centre(trips, stop_times, {"r": "15B"}, {"C"})
    assert out == {
        "A": [["18:23", "15B", "PRAZA", "LAB", 17, "C"]],
        "B": [["18:30", "15B", "PRAZA", "LAB", 10, "C"]],
    }


def test_parada_cercana_solo_si_esta_a_menos_de_400_m() -> None:
    assert nearest_stop({"lat": 42.2382, "lon": -8.7260}, STOPS) == {
        "stop_id": "C",
        "distance_m": 21,
    }
    assert nearest_stop({"lat": 42.30, "lon": -8.60}, STOPS) is None


def test_paradas_solo_con_buhos_no_cuentan_como_servidas() -> None:
    day = [[f"{h:02d}:00", "C1", "X", "S", False] for h in range(7, 23)] * 2
    night = [["00:03", "N4", "X", "S", False], ["25:27", "N4", "X", "S", False]]
    assert daytime_served({"diurna": day, "buho": night}) == {"diurna"}
