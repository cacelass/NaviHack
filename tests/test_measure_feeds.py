"""El medidor de feeds del Concello (D-00) calcula bien sin tocar la red."""

from __future__ import annotations

from scripts.measure_feeds import FeedLog, intervals, source_timestamp, summary


def test_intervals_ignora_el_arranque_y_mide_los_huecos() -> None:
    assert intervals([0.0, 120.0, 240.0, 420.0]) == [120.0, 120.0, 180.0]
    assert intervals([5.0]) == []
    assert intervals([]) == []


def test_source_timestamp_lee_fechahora_de_parkings() -> None:
    payload = [{"fechahora": "2026-11-14 12:55:00", "nombre": "Parking Urzáiz"}]
    assert source_timestamp(payload) == "2026-11-14 12:55:00"


def test_source_timestamp_sin_campo_devuelve_none() -> None:
    assert source_timestamp([{"titulo": "Contemplar unha posta de sol"}]) is None
    assert source_timestamp([]) is None
    assert source_timestamp({"x": 1}) is None


def test_summary_calcula_disponibilidad_y_mediana() -> None:
    log = FeedLog("https://example.org/f.json", polls=10, errors=1)
    log.changes = [0.0, 120.0, 240.0]
    out = summary({"f": log})["f"]
    assert isinstance(out, dict)
    assert out["availability"] == 0.9
    assert out["changes_seen"] == 2
    assert out["interval_s"] == {"median": 120.0, "min": 120.0, "max": 120.0}
