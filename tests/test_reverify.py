"""Re-verificación semanal (R-05): diff de la capa, horarios a revisar y puntos caducados."""

from __future__ import annotations

from datetime import date
from typing import Any

from scripts.reverify import diff, needs_review, stale


def _f(
    pid: str, horario: str = "Encendido 18:00", x: float = -8.7258, y: float = 42.2381, **a: Any
) -> dict[str, Any]:
    attrs = {
        "id": pid,
        "nombre": f"P{pid}",
        "tipologia": "Elementos lumínicos",
        "horario_atencion": horario,
        **a,
    }
    return {"attributes": attrs, "geometry": {"x": x, "y": y}}


def test_detecta_altas_bajas_y_cambios() -> None:
    old = [_f("1"), _f("2"), _f("3")]
    new = [_f("1", horario="Encendido 18:30"), _f("3", y=42.2384), _f("9")]
    changes = {(c["id"], c["change"]) for c in diff(old, new)}
    assert changes == {("9", "added"), ("2", "removed"), ("1", "schedule"), ("3", "moved")}


def test_movimiento_pequeno_no_cuenta() -> None:
    assert diff([_f("1")], [_f("1", y=42.23811)]) == []


def test_horario_cambiado_con_programa_pide_revision() -> None:
    prog = {"points": {"concello-1": {"template": "lights"}}}
    changes = [
        {"id": "1", "change": "schedule"},
        {"id": "2", "change": "schedule"},
        {"id": "1", "change": "name"},
    ]
    assert needs_review(changes, prog) == ["concello-1"]


def test_puntos_sin_verificar_en_7_dias() -> None:
    points: list[dict[str, Any]] = [
        {"id": "a", "last_verified": "2026-11-14"},
        {"id": "b", "last_verified": "2026-11-06"},
        {"id": "c", "last_verified": None},
    ]
    assert stale(points, date(2026, 11, 21)) == ["b", "c"]
