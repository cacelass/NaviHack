"""Programa 2026-27 (R-04): horarios estructurados y «abierto ahora».

Lee `data/programme_2026.json` (estructurado a mano desde el texto oficial de
la capa del Concello) y responde, para un punto y una hora local de Madrid:

- `slots(entry, day)`: tramos abiertos ese día, como datetimes (un cierre a las
  01:00 o 03:00 cae al día siguiente; «toda la noche» llega a las 08:30).
- `is_open(entry, when)`: `True`/`False`, o `None` si no hay horario oficial.
- `attach(points, programme)`: mete el programa expandido en cada punto de
  `points.json` (lo llama `scripts/christmas_layer.py`).

Días: `mon..sun`, `eve` = víspera de festivo, `holiday` = festivo. La primera
regla que encaja gana; las fechas explícitas (`dates`) ganan a todas.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROGRAMME = ROOT / "data" / "programme_2026.json"
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAWN = time(8, 30)  # «hasta el amanecer»: en Vigo, a finales de diciembre, ~08:50


def load(path: Path = PROGRAMME) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def entry_for(programme: dict[str, Any], point_id: str) -> dict[str, Any] | None:
    """Programa de un punto con su plantilla ya fundida (el punto gana)."""
    own = programme["points"].get(point_id)
    if own is None:
        return None
    base = programme["templates"].get(own.get("template", ""), {})
    return {**base, **own, "holidays": programme["holidays"]}


def day_classes(day: date, holidays: list[str]) -> set[str]:
    classes = {DAYS[day.weekday()]}
    if day.isoformat() in holidays:
        classes.add("holiday")
    if (day + timedelta(days=1)).isoformat() in holidays:
        classes.add("eve")
    return classes


def _in_season(entry: dict[str, Any], day: date) -> bool:
    season = entry.get("season") or {}
    d = day.isoformat()
    return (not season.get("from") or d >= season["from"]) and (
        not season.get("to") or d <= season["to"]
    )


def _span(day: date, start: str, end: str) -> tuple[datetime, datetime]:
    s = datetime.combine(day, time.fromisoformat(start))
    e = datetime.combine(day, time.fromisoformat(end))
    return s, e if e > s else e + timedelta(days=1)


def slots(entry: dict[str, Any], day: date) -> list[tuple[datetime, datetime]]:
    """Tramos de apertura que **empiezan** ese día."""
    if not _in_season(entry, day):
        return []
    d = day.isoformat()
    if d in entry.get("dates", {}):
        return [_span(day, s, e) for s, e in entry["dates"][d]]
    classes = day_classes(day, entry["holidays"])
    for rule in entry.get("rules", []):
        if not classes & set(rule["days"]):
            continue
        if (rule.get("from") and d < rule["from"]) or (rule.get("to") and d > rule["to"]):
            continue
        pairs = rule.get("slots") or [[rule["open"], rule["close"]]]
        spans = [_span(day, s, e) for s, e in pairs]
        if d in entry.get("all_night", []):
            spans = [(spans[0][0], datetime.combine(day + timedelta(days=1), DAWN))]
        return spans
    return []


def departures(entry: dict[str, Any], day: date) -> list[str]:
    """Salidas a hora fija (Nadal Bus, barco) para ese día."""
    d = day.isoformat()
    classes = day_classes(day, entry["holidays"])
    for dep in entry.get("departures", []):
        if dep["from"] <= d <= dep["to"] and classes & set(dep["days"]):
            return list(dep["times"])
    return []


def is_open(entry: dict[str, Any] | None, when: datetime) -> bool | None:
    """¿Abierto/encendido en `when` (hora local)? `None` = sin horario oficial."""
    if entry is None or entry.get("hours_unknown"):
        return None
    if entry.get("departures") and not entry.get("rules"):
        return None  # actividad con salidas a hora fija: no tiene «abierto»
    today = when.date()
    spans = slots(entry, today - timedelta(days=1)) + slots(entry, today)
    return any(s <= when < e for s, e in spans)


def attach(points: list[dict[str, Any]], programme: dict[str, Any]) -> None:
    """Añade a cada punto su programa (o `null` si el Concello no publica horario)."""
    for p in points:
        entry = entry_for(programme, p["id"])
        if entry is None:
            p["programme"] = None
            continue
        p["programme"] = {k: v for k, v in entry.items() if k not in ("template", "holidays")}
        p["programme"][
            "closed_dates"
        ] = []  # el texto oficial no publica cierres fuera de temporada
        for show in entry.get("shows", []):
            p["show_times"] = sorted(set(p.get("show_times", [])) | set(show["times"]))
        p["programme"]["verified"] = programme["verified"]  # last_verified lo pone la capa (R-05)
