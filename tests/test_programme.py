"""Programa 2026-27 (R-04): «abierto ahora», cierres tras medianoche, vísperas y excepciones."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

from scripts.programme import attach, day_classes, departures, entry_for, is_open, load, slots

PROG = load()


def _e(point: str) -> dict:
    entry = entry_for(PROG, point)
    assert entry is not None
    return entry


def test_cada_punto_de_la_capa_tiene_programa_o_esta_listado_sin_horario() -> None:
    import json
    from pathlib import Path

    points = json.loads(Path("data/points.json").read_text(encoding="utf-8"))["points"]
    ids = {p["id"] for p in points}
    covered = set(PROG["points"]) | set(PROG["no_schedule"])
    assert ids == covered


def test_vispera_y_festivo() -> None:
    assert day_classes(date(2026, 12, 7), PROG["holidays"]) == {"mon", "eve"}
    assert day_classes(date(2026, 12, 8), PROG["holidays"]) == {"tue", "holiday"}


@pytest.mark.parametrize(
    ("when", "expected"),
    [
        (datetime(2026, 11, 16, 17, 59), False),  # lunes antes del encendido
        (datetime(2026, 11, 16, 18, 0), True),
        (datetime(2026, 11, 17, 0, 59), True),  # dom–mié apaga a la 01:00 (del día siguiente)
        (datetime(2026, 11, 17, 1, 0), False),
        (datetime(2026, 11, 20, 2, 30), True),  # noche de jueves: hasta las 03:00
        (datetime(2026, 12, 8, 2, 0), True),  # lunes 7 es víspera de festivo: 03:00
        (datetime(2026, 12, 25, 7, 0), True),  # noche del 24: toda la noche
        (datetime(2026, 11, 13, 20, 0), False),  # antes de la temporada
    ],
)
def test_luces_del_arbol(when: datetime, expected: bool) -> None:
    assert is_open(_e("concello-2552"), when) is expected


def test_noria_horario_de_vacaciones_y_fechas_especiales() -> None:
    noria = _e("concello-3494")
    assert is_open(noria, datetime(2026, 11, 17, 22, 45)) is False  # laborable normal: 22:30
    assert is_open(noria, datetime(2026, 12, 22, 23, 15)) is True  # vacaciones: 23:30
    assert is_open(noria, datetime(2026, 11, 21, 0, 15)) is True  # viernes noche: 00:30
    assert is_open(noria, datetime(2026, 12, 24, 20, 30)) is False  # 24-dic cierra a las 20:00


def test_cartero_real_solo_en_su_temporada_y_dos_tramos() -> None:
    cartero = _e("concello-3502")
    assert is_open(cartero, datetime(2026, 12, 20, 12, 0)) is False
    assert is_open(cartero, datetime(2026, 12, 27, 12, 0)) is True
    assert is_open(cartero, datetime(2026, 12, 27, 15, 0)) is False
    assert len(slots(cartero, date(2026, 12, 31))) == 2


def test_sin_horario_oficial_es_none() -> None:
    assert is_open(entry_for(PROG, "concello-3527"), datetime(2026, 12, 1, 19, 0)) is None
    assert (
        is_open(_e("concello-3503"), datetime(2026, 12, 10, 19, 0)) is None
    )  # circo: taquilla externa


def test_salidas_del_nadal_bus() -> None:
    bus = _e("concello-3534")
    assert departures(bus, date(2026, 11, 22)) == ["18:30"]  # domingo de noviembre
    assert departures(bus, date(2026, 12, 7)) == ["18:30", "19:30", "20:30"]  # víspera de festivo


def test_attach_mete_programa_y_horas_de_espectaculo() -> None:
    points: list[dict[str, Any]] = [
        {"id": "concello-2552", "show_times": ["18:00"]},
        {"id": "concello-3527"},
    ]
    attach(points, PROG)
    assert points[0]["programme"]["rules"] and points[0]["last_verified"] == PROG["verified"]
    assert points[0]["show_times"] == ["18:00", "19:00", "20:00", "21:00", "21:50"]
    assert points[1]["programme"] is None
