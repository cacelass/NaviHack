"""Agenda loader (D-03): historial propio, horas de points.json, «hora por confirmar»."""

from __future__ import annotations

from typing import Any

from scripts.agenda import TIME_TBC, merge, on_day


def _raw(id: int, start: str | None, end: str | None, permanent: bool = False) -> dict[str, Any]:
    return {
        "id": id,
        "titulo": f"evento {id}",
        "fecha_inicio": start,
        "fecha_fin": end,
        "permanente": permanent,
        "direccion": "Porta do Sol",
        "subcategoria": "16,33",
    }


def _snap(day: str, *rows: dict[str, Any]) -> dict[str, Any]:
    return {"fetched_at": f"{day}T06:30:00+00:00", "data": list(rows)}


def test_historial_conserva_eventos_que_el_feed_ya_no_trae() -> None:
    hist = merge([], _snap("2026-11-14", _raw(1, "2026-11-14", "2026-11-20")), [])
    hist = merge(hist, _snap("2026-11-15", _raw(2, "2026-11-15", "2026-11-15")), [])
    assert [e["id"] for e in hist] == [1, 2]
    assert [e["id"] for e in on_day(hist, "2026-11-18")] == [1]


def test_hora_sale_de_points_json_no_de_la_agenda() -> None:
    points = [{"id": "porta-do-sol", "agenda_ids": [336], "show_times": ["18:00", "20:00"]}]
    (ev,) = merge([], _snap("2026-11-14", _raw(336, "2026-11-14", "2026-11-14")), points)
    assert ev["time"] == ["18:00", "20:00"]
    assert ev["time_label"] is None


def test_evento_sin_hora_queda_por_confirmar() -> None:
    (ev,) = merge([], _snap("2026-11-14", _raw(9, "2026-11-14", "2026-11-14")), [])
    assert ev["time"] is None
    assert ev["time_label"] == TIME_TBC
    assert ev["categories"] == ["16", "33"]


def test_permanentes_salen_todos_los_dias() -> None:
    hist = merge([], _snap("2026-11-14", _raw(72, None, None, permanent=True)), [])
    assert [e["id"] for e in on_day(hist, "2026-12-24")] == [72]
