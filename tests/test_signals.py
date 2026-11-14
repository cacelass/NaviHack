"""Señales del planner (D-12): noche e iluminación, pendiente y descansos, lluvia, señales ausentes."""

from __future__ import annotations

from datetime import date, datetime

from scripts import programme
from scripts.signals import Signals, is_dark, sunset

PORTA_DO_SOL = (42.23807, -8.72581)
LIGHTS_ENTRY = programme.entry_for(programme.load(), "concello-2552")
FAR = (42.2400, -8.7200)  # ~500 m de Porta do Sol


def test_puesta_de_sol_en_vigo_en_noviembre_y_verano() -> None:
    s = sunset(date(2026, 11, 14))
    assert s.hour == 18 and s.minute <= 20  # ~18:10 hora de Madrid
    assert sunset(date(2026, 6, 21)).hour == 22  # ~22:00 en verano (UTC+2)
    assert is_dark(datetime(2026, 11, 14, 19, 0)) and not is_dark(datetime(2026, 11, 14, 13, 0))


def test_after_dark_penaliza_tramos_sin_luces_encendidas() -> None:
    sig = Signals(lights=[(PORTA_DO_SOL, LIGHTS_ENTRY)])
    night = datetime(2026, 11, 16, 19, 0)
    lit, n1 = sig.leg_factor(PORTA_DO_SOL, (42.23830, -8.72560), night, "after_dark")
    dark, n2 = sig.leg_factor(FAR, (42.2410, -8.7190), night, "after_dark")
    assert lit == 1.0 and dark > 1.5 and "unlit" in n2
    # de día no hay penalización
    assert (
        sig.leg_factor(FAR, (42.2410, -8.7190), datetime(2026, 11, 16, 12, 0), "after_dark")[0]
        == 1.0
    )


def test_luces_apagadas_a_esa_hora_no_iluminan() -> None:
    sig = Signals(lights=[(PORTA_DO_SOL, LIGHTS_ENTRY)])
    late = datetime(2026, 11, 17, 2, 0)  # lunes→martes: apagan a la 01:00
    assert sig.lit_fraction(PORTA_DO_SOL, (42.23830, -8.72560), late) == 0.0


def test_easy_walk_recarga_tramo_largo_sin_bancos_ni_cafes() -> None:
    a, b = (42.2350, -8.7250), (42.2380, -8.7200)  # ~500 m
    sin = Signals(rest=[(42.30, -8.80)]).leg_factor(a, b, datetime(2026, 11, 16, 12), "easy_walk")
    con = Signals(rest=[(42.2365, -8.7225)]).leg_factor(
        a, b, datetime(2026, 11, 16, 12), "easy_walk"
    )
    assert "no_rest" in sin[1] and sin[0] > con[0]


def test_senales_ausentes_se_informan_y_no_rompen() -> None:
    sig = Signals()
    factor, notes = sig.leg_factor(
        (42.235, -8.725), (42.238, -8.720), datetime(2026, 11, 16, 20), "easy_walk"
    )
    assert factor == 1.0 and {"missing:elevation", "missing:rest_spots"} <= set(notes)
    assert sig.leg_factor(
        (42.235, -8.725), (42.238, -8.720), datetime(2026, 11, 16, 20), "after_dark"
    )[1] == ["missing:lights"]
    assert sig.rain_warning(datetime(2026, 11, 16, 17), datetime(2026, 11, 16, 19)) is None


def test_lluvia_avisa_y_favorece_paradas_cubiertas() -> None:
    hours = [f"2026-11-16T{h:02d}:00" for h in range(24)]
    weather = {
        "data": {
            "hourly": {
                "time": hours,
                "precipitation_probability": [80 if 17 <= h <= 19 else 10 for h in range(24)],
            }
        }
    }
    sig = Signals(weather=weather)
    warn = sig.rain_warning(datetime(2026, 11, 16, 17, 30), datetime(2026, 11, 16, 19, 0))
    assert warn == {"key": "planner.rain_warning", "probability": 80}
    assert sig.rain_warning(datetime(2026, 11, 16, 10), datetime(2026, 11, 16, 12)) is None
    assert sig.stop_factor({"covered": True}, raining=True) < sig.stop_factor(
        {"covered": False}, raining=True
    )
    assert sig.stop_factor({"covered": True}, raining=False) == 1.0


def test_carga_real_sin_romper() -> None:
    sig = Signals.load()
    assert sig.lights and sig.rest and sig.grid is not None
