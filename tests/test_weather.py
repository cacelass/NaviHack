"""Tiempo de Open-Meteo (D-10): tira de 6 h, lluvia para el planner, se oculta si falla."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.snapshot import WEATHER_HOURLY, publish, rain_probability, weather_strip

NOW = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
HOURS = [f"2026-11-14T{h:02d}:00" for h in range(24)]
PAYLOAD = {
    "current": {"time": "2026-11-14T13:15", "temperature_2m": 16.0, "weather_code": 3},
    "hourly": {
        "time": HOURS,
        "temperature_2m": [10.0 + h / 2 for h in range(24)],
        "precipitation_probability": [h * 3 for h in range(24)],
        "weather_code": [3] * 24,
        **{
            v: [0.0] * 24
            for v in WEATHER_HOURLY
            if v not in ("temperature_2m", "precipitation_probability", "weather_code")
        },
    },
}


def _snap(tmp_path: Path) -> dict[str, Any]:
    publish("weather", json.dumps(PAYLOAD).encode(), None, out=tmp_path, now=NOW)
    snap: dict[str, Any] = json.loads((tmp_path / "weather" / "latest.json").read_text("utf-8"))
    return snap


def test_tira_muestra_ahora_y_las_proximas_6_horas(tmp_path: Path) -> None:
    strip = weather_strip(_snap(tmp_path), NOW + timedelta(minutes=10))
    assert strip is not None
    assert strip["now"]["temperature_2m"] == 16.0
    assert [h["time"][11:13] for h in strip["next_hours"]] == ["13", "14", "15", "16", "17", "18"]
    assert strip["age_s"] == 600.0


def test_probabilidad_de_lluvia_en_la_ventana_de_ruta(tmp_path: Path) -> None:
    assert rain_probability(_snap(tmp_path), "2026-11-14T17:00", "2026-11-14T19:30") == 57


def test_tira_se_oculta_sin_datos_o_caducada(tmp_path: Path) -> None:
    snap = _snap(tmp_path)
    assert weather_strip(None) is None
    assert weather_strip(snap, NOW + timedelta(hours=4)) is None


def test_payload_malo_mantiene_el_ultimo_bueno_con_su_edad(tmp_path: Path) -> None:
    _snap(tmp_path)
    row = publish("weather", b'{"error": true}', None, out=tmp_path, now=NOW + timedelta(hours=1))
    assert row["ok"] is False
    snap = json.loads((tmp_path / "weather" / "latest.json").read_text("utf-8"))
    strip = weather_strip(snap, NOW + timedelta(hours=1))
    assert strip is not None and strip["age_s"] == 3600.0


def test_falta_una_variable_horaria_se_rechaza(tmp_path: Path) -> None:
    bad = {**PAYLOAD, "hourly": {k: v for k, v in PAYLOAD["hourly"].items() if k != "visibility"}}
    row = publish("weather", json.dumps(bad).encode(), None, out=tmp_path, now=NOW)
    assert row["ok"] is False and "visibility" in str(row["error"])
