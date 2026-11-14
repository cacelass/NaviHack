"""GTFS de Renfe (X-02): estaciones de Vigo, salidas/llegadas y calendario."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime

import pytest

from scripts.gtfs_renfe import board, build

PAD = "   "  # Renfe rellena cabeceras y celdas con espacios
FILES = {
    "stops.txt": f"stop_id,stop_name,stop_lat,wheelchair_boarding{PAD}\n"
    f"08223,Vigo Urzaiz,42.23,1{PAD}\n22308,Vigo-Guixar,42.24,1\n"
    "31412,Madrid-Chamartin,40.47,1\n20200,A Coruña,43.35,1\n",
    "routes.txt": f"route_id,route_short_name{PAD}\nR1,ALVIA{PAD}\nR2,Intercity\n",
    "trips.txt": "route_id,service_id,trip_id\nR1,S1,t1\nR2,S2,t2\nR2,S1,t3\n",
    "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
    "t1,07:00:00,07:00:00,08223,1\nt1,11:30:00,11:30:00,31412,2\n"
    "t2,09:00:00,09:00:00,20200,1\nt2,10:30:00,10:32:00,22308,2\n"
    "t3,08:00:00,08:00:00,31412,1\nt3,09:00:00,09:00:00,20200,2\n",
    "calendar.txt": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
    "start_date,end_date\nS1,1,1,1,1,1,0,0,20261101,20261231\nS2,1,1,1,1,1,1,1,20261101,20261231\n",
    "calendar_dates.txt": "service_id,date,exception_type\nS1,20261116,2\nS1,20261115,1\n",
}


def _gtfs(files: dict[str, str] = FILES) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, body in files.items():
            z.writestr(name, body)
    return zipfile.ZipFile(buf)


def test_solo_viajes_que_paran_en_vigo_y_las_dos_estaciones() -> None:
    data = build(_gtfs())
    assert {s["name"] for s in data["stations"]} == {"Vigo Urzaiz", "Vigo-Guixar"}
    assert {m["trip_id"] for m in data["movements"]} == {"t1", "t2"}
    assert data["kind"] == "scheduled"


def test_salidas_y_llegadas_con_origen_y_destino() -> None:
    by = {(m["trip_id"], m["type"]): m for m in build(_gtfs())["movements"]}
    assert (by[("t1", "departure")]["time"], by[("t1", "departure")]["to"]) == (
        "07:00",
        "Madrid-Chamartin",
    )
    assert (by[("t2", "arrival")]["station"], by[("t2", "arrival")]["from"]) == (
        "Vigo-Guixar",
        "A Coruña",
    )
    assert ("t2", "departure") not in by  # Guixar es final del t2: no sale de Vigo


def test_calendario_semanal_con_excepciones() -> None:
    data = build(_gtfs())
    tuesday = datetime(2026, 11, 17, 6, 0)
    monday_removed = datetime(2026, 11, 16, 6, 0)
    sunday_added = datetime(2026, 11, 15, 6, 0)
    assert [m["train"] for m in board(data, tuesday)] == ["ALVIA"]
    assert board(data, monday_removed) == []
    assert [m["trip_id"] for m in board(data, sunday_added)] == ["t1"]
    assert [m["trip_id"] for m in board(data, tuesday, kind="arrival", station="Vigo-Guixar")] == [
        "t2"
    ]


def test_falla_si_falta_una_estacion_de_vigo() -> None:
    files = {
        **FILES,
        "stops.txt": "stop_id,stop_name\n08223,Vigo Urzaiz\n31412,Madrid\n20200,Coruña\n",
    }
    with pytest.raises(ValueError, match="22308"):
        build(_gtfs(files))
