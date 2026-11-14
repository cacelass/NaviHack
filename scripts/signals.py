"""Señales y pesos del planner (D-12).

El planner (PLANNER-01) pide, para cada tramo a pie entre dos paradas, un
multiplicador de coste según la opción elegida, y para cada parada una
bonificación. Este módulo junta las señales que ya tenemos y **nunca falla por
falta de una**: si no hay datos, el factor es neutro (1.0) y la señal aparece en
`Signals.missing`, que el planner enseña en el resumen.

- **After dark** (`after_dark`): de noche (tras la puesta de sol en Vigo) un
  tramo cuesta más cuanto más parte de él queda lejos (> `LIT_M`) de una luz
  de Navidad **encendida a esa hora** (horario de R-04).
- **Easy walk** (`easy_walk`): pendiente máxima del tramo (MDT05, D-11, vía
  `elevation.easy_walk_factor`) y un recargo si un tramo largo no pasa cerca de
  ningún banco o café (OSM, `data/osm/rest_core.json`).
- **Lluvia**: `rain_warning` avisa si la probabilidad máxima de lluvia en la
  ventana de la ruta llega a `RAIN_PCT` (Open-Meteo, D-10), y `stop_factor`
  abarata las paradas cubiertas o bajo techo (`covered: true`) cuando llueve.
- **Aparcamiento:** fuera hasta que el equipo lo confirme (no está en el spec v4).

Todas las horas son locales de Europe/Madrid (naive).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts import elevation, programme
from scripts.parkings import haversine_m
from scripts.snapshot import rain_probability

ROOT = Path(__file__).resolve().parent.parent
POINTS = ROOT / "data" / "points.json"
WEATHER = ROOT / "data" / "snapshots" / "weather" / "latest.json"
REST = ROOT / "data" / "osm" / "rest_core.json"
VIGO = (42.2376, -8.7247)
LIT_M = 40.0  # a menos de esto de una luz encendida, el tramo cuenta como iluminado
REST_M = 60.0
LONG_LEG_M = 150.0
SAMPLE_M = 25.0
UNLIT_PENALTY = 0.6  # tramo 100 % a oscuras cuesta ×1,6
NO_REST_PENALTY = 0.15
RAIN_PCT = 50
COVERED_RAIN_FACTOR = 0.7

LatLon = tuple[float, float]


def sunset(day: date, lat: float = VIGO[0], lon: float = VIGO[1]) -> datetime:
    """Puesta de sol (hora local Madrid, naive). Algoritmo NOAA simplificado, ±10 min (de sobra para «es de noche»)."""
    n = day.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eqt = 229.18 * (
        0.000075
        + 0.001868 * math.cos(g)
        - 0.032077 * math.sin(g)
        - 0.014615 * math.cos(2 * g)
        - 0.040849 * math.sin(2 * g)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(g)
        + 0.070257 * math.sin(g)
        - 0.006758 * math.cos(2 * g)
        + 0.000907 * math.sin(2 * g)
        - 0.002697 * math.cos(3 * g)
        + 0.00148 * math.sin(3 * g)
    )
    phi = math.radians(lat)
    ha = math.degrees(
        math.acos(
            math.cos(math.radians(90.833)) / (math.cos(phi) * math.cos(decl))
            - math.tan(phi) * math.tan(decl)
        )
    )
    utc_min = 720 - 4 * (lon - ha) - eqt
    # Madrid: UTC+1 en invierno, UTC+2 del último domingo de marzo al último de octubre.
    offset = 2 if _summer_time(day) else 1
    return datetime.combine(day, datetime.min.time()) + timedelta(minutes=utc_min + 60 * offset)


def _summer_time(day: date) -> bool:
    def last_sunday(month: int) -> date:
        d = date(day.year, month, 31)
        return d - timedelta(days=(d.weekday() + 1) % 7)

    return last_sunday(3) <= day < last_sunday(10)


def is_dark(when: datetime) -> bool:
    # Antes del amanecer también es de noche; para la temporada basta con 08:30.
    return when >= sunset(when.date()) or when.time() < datetime.strptime("08:30", "%H:%M").time()


def _samples(a: LatLon, b: LatLon) -> list[LatLon]:
    n = max(1, int(haversine_m(*a, *b) // SAMPLE_M))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def _near(p: LatLon, spots: list[LatLon], radius: float) -> bool:
    return any(haversine_m(p[0], p[1], s[0], s[1]) <= radius for s in spots)


@dataclass
class Signals:
    lights: list[tuple[LatLon, dict[str, Any] | None]] = field(default_factory=list)
    grid: elevation.Grid | None = None
    rest: list[LatLon] = field(default_factory=list)
    weather: dict[str, Any] | None = None
    missing: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> Signals:
        s = cls()
        try:
            prog = programme.load()
            pts = json.loads(POINTS.read_text(encoding="utf-8"))["points"]
            s.lights = [
                ((p["lat"], p["lon"]), programme.entry_for(prog, p["id"]))
                for p in pts
                if p["type"] == "light"
            ]
        except (OSError, KeyError, json.JSONDecodeError):
            s.missing.append("lights")
        s.grid = elevation.load()
        if s.grid is None:
            s.missing.append("elevation")
        try:
            raw = json.loads(REST.read_text(encoding="utf-8"))
            s.rest = [(e["lat"], e["lon"]) for e in raw["elements"]]
        except (OSError, KeyError, json.JSONDecodeError):
            s.missing.append("rest_spots")
        try:
            s.weather = json.loads(WEATHER.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            s.missing.append("weather")
        return s

    def lit_fraction(self, a: LatLon, b: LatLon, when: datetime) -> float | None:
        on = [pos for pos, entry in self.lights if programme.is_open(entry, when)]
        if not self.lights:
            return None
        pts = _samples(a, b)
        return sum(_near(p, on, LIT_M) for p in pts) / len(pts)

    def leg_factor(
        self, a: LatLon, b: LatLon, when: datetime, mode: str
    ) -> tuple[float, list[str]]:
        """Multiplicador de coste del tramo a→b y por qué. `mode`: fastest | after_dark | easy_walk."""
        notes: list[str] = []
        factor = 1.0
        if mode == "after_dark" and is_dark(when):
            lit = self.lit_fraction(a, b, when)
            if lit is None:
                notes.append("missing:lights")
            else:
                factor *= 1 + UNLIT_PENALTY * (1 - lit)
                if lit < 0.5:
                    notes.append("unlit")
        if mode == "easy_walk":
            grade = self.grid.grade(a, b) if self.grid else None
            if grade is None:
                notes.append("missing:elevation")
            factor *= elevation.easy_walk_factor(grade)
            if grade and grade["max_grade_pct"] > elevation.EASY_GRADE_PCT:
                notes.append("steep")
            if not self.rest:
                notes.append("missing:rest_spots")
            elif haversine_m(*a, *b) > LONG_LEG_M and not any(
                _near(p, self.rest, REST_M) for p in _samples(a, b)
            ):
                factor *= 1 + NO_REST_PENALTY
                notes.append("no_rest")
        return factor, notes

    def rain_warning(self, start: datetime, end: datetime) -> dict[str, Any] | None:
        """Aviso para el resumen de la ruta, o None. Sin tiempo = None (y 'weather' en missing)."""
        if not self.weather:
            return None
        p = rain_probability(
            self.weather, start.strftime("%Y-%m-%dT%H:%M"), end.strftime("%Y-%m-%dT%H:%M")
        )
        if p is not None and p >= RAIN_PCT:
            return {"key": "planner.rain_warning", "probability": p}
        return None

    def stop_factor(self, stop: dict[str, Any], raining: bool) -> float:
        """Con lluvia, una parada cubierta o bajo techo cuesta menos (el planner la prefiere)."""
        return COVERED_RAIN_FACTOR if raining and stop.get("covered") else 1.0


def save_rest(elements: list[dict[str, Any]], path: Path = REST) -> None:
    """Guarda bancos/cafés de OSM (Overpass) para el núcleo. ODbL: © OpenStreetMap contributors."""
    path.parent.mkdir(parents=True, exist_ok=True)
    keep = [
        {"lat": e["lat"], "lon": e["lon"], "amenity": e["tags"].get("amenity")} for e in elements
    ]
    doc = {"source": "© OpenStreetMap contributors (ODbL)", "elements": keep}
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
