"""GTFS de Vitrasa (X-01): ingesta, etiqueta «scheduled» y cruce con los desvíos de Navidad."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import Any

from scripts.gtfs_vitrasa import build, christmas_detours, next_departures

FILES = {
    "routes.txt": "route_id,route_short_name,route_long_name,route_type,route_color\n"
    "1,C1,Circular 1,3,FF0000\n2,4A,Coia - Teis,3,\n",
    "stops.txt": "stop_id,stop_code,stop_name,stop_lat,stop_lon\n"
    "100,P1,Rúa de Policarpo Sanz 25,42.2370,-8.7215\n200,P2,Praza de América,42.2230,-8.7320\n",
    "calendar_dates.txt": "service_id,date,exception_type\nLAB,20261116,1\nLAB,20261117,1\n"
    "FES,20261115,1\nLAB,20261115,2\n",
    "trips.txt": "route_id,service_id,trip_id,trip_headsign\n1,LAB,t1,PRAZA AMÉRICA\n"
    "2,LAB,t2,TEIS\n1,FES,t3,PRAZA AMÉRICA\n",
    "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
    "t1,08:00:00,08:00:00,100,1\nt1,08:10:00,08:10:00,200,2\n"
    "t2,08:05:00,08:05:00,100,1\nt3,10:00:00,10:00:00,100,1\n",
}
NOTICES: list[dict[str, Any]] = [
    {"titulo": "CORTE TRÁFICO MEDIA MARATÓN", "lineas_afectadas": "A"},
    {
        "id": 4033,
        "titulo": "DESVÍOS NADAL 2026 / 2027",
        "fecha_inicio": "2026-11-11",
        "fecha_fin": "2027-01-10",
        "lineas_afectadas": "15B,C1,4C",
        "resumen": "<strong>zona centro</strong> restringida (Policarpo Sanz)",
    },
]


def _gtfs() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, body in FILES.items():
            z.writestr(name, body)
    return zipfile.ZipFile(buf)


def _data() -> dict:
    return build(_gtfs(), christmas_detours(NOTICES))


def test_ingesta_paradas_lineas_y_horarios() -> None:
    data = _data()
    assert [r["short"] for r in data["routes"]] == ["4A", "C1"]
    assert {s["id"] for s in data["stops"]} == {"100", "200"}
    assert data["services"] == {"LAB": ["20261116", "20261117"], "FES": ["20261115"]}
    assert [d[0] for d in data["departures"]["100"]] == ["08:00", "08:05", "10:00"]


def test_todo_va_etiquetado_como_programado() -> None:
    data = _data()
    assert data["kind"] == "scheduled"
    deps = next_departures(data, "100", datetime(2026, 11, 16, 7, 30))
    assert [(d["time"], d["line"]) for d in deps] == [("08:00", "C1"), ("08:05", "4A")]
    assert all(d["kind"] == "scheduled" for d in deps)


def test_servicio_solo_los_dias_de_su_calendario() -> None:
    deps = next_departures(_data(), "100", datetime(2026, 11, 15, 7, 0))
    assert [d["time"] for d in deps] == ["10:00"]


def test_cruce_con_los_desvios_de_navidad() -> None:
    data = _data()
    assert data["christmas_detours"]["lines"] == ["15B", "4C", "C1"]
    assert data["christmas_detours"]["to"] == "2027-01-10"
    stops = {s["id"]: s for s in data["stops"]}
    assert stops["100"]["christmas_detour"] is True
    assert stops["200"]["christmas_detour"] is False
    deps = next_departures(data, "100", datetime(2026, 11, 16, 7, 30))
    assert [d["detour"] for d in deps] == [True, False]


def test_sin_aviso_de_navidad_no_marca_nada() -> None:
    assert christmas_detours([NOTICES[0]]) == {}
