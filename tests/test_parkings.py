"""Capa de parkings (D-05): plazas, %, actualización, «sin datos» y el más cercano."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from scripts.parkings import layer, nearest

NOW = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)


def _row(name: str, lat: float, lon: float, free: int, total: int, ts: str) -> dict[str, Any]:
    return {
        "nombre": name,
        "lat": lat,
        "lon": lon,
        "plazaslibres": free,
        "totalplazas": total,
        "fechahora": ts,
    }


SNAP = {
    "fetched_at": NOW.isoformat(),
    "stale_after_s": 600,
    "data": [
        _row("Urzáiz", 42.23542, -8.71871, 102, 463, "2026-11-14 12:55:00"),
        _row("Independencia", 42.22373, -8.73014, 101, 193, "2026-11-14 12:55:00"),
        _row("Congelado", 42.24051, -8.72513, 5, 180, "2026-11-14 12:20:00"),
    ],
}


def _props(geo: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["properties"]["name"]: f["properties"] for f in geo["features"]}


def test_plazas_libres_porcentaje_y_hora() -> None:
    p = _props(layer(SNAP, NOW))["Urzáiz"]
    assert (p["free"], p["total"], p["free_pct"]) == (102, 463, 22)
    assert p["updated"] == "2026-11-14 12:55:00"
    assert p["stale"] is False


def test_parking_congelado_sale_sin_datos() -> None:
    p = _props(layer(SNAP, NOW))["Congelado"]
    assert p["stale"] is True and p["free"] is None and p["free_pct"] is None


def test_snapshot_caducado_deja_todo_sin_datos() -> None:
    geo = layer(SNAP, NOW + timedelta(minutes=11))
    assert all(f["properties"]["stale"] for f in geo["features"])


def test_mas_cercano_para_el_panel_del_punto() -> None:
    porta_do_sol = (42.2376, -8.7247)
    near = nearest(layer(SNAP, NOW), *porta_do_sol)
    assert near is not None
    assert near["name"] == "Urzáiz"
    assert 400 < near["distance_m"] < 700


def test_si_todos_estan_sin_datos_devuelve_el_mas_cercano_igualmente() -> None:
    near = nearest(layer(SNAP, NOW + timedelta(hours=1)), 42.2376, -8.7247)
    assert near is not None and near["stale"] is True
