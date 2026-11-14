"""Agenda loader (D-03): eventos del Concello con historial propio.

El Concello solo publica `agenda-hoy.json` (no hay dataset de días futuros:
`agenda-semana`, `agenda-mes`, `agenda` dan 404 y CKAN solo lista `agenda-hoy`,
comprobado 2026-11-14). Así que el historial lo construimos nosotros: cada
snapshot diario de `scripts/snapshot.py agenda` se funde por `id` en
`data/agenda/events.json`, y un evento visto hoy con `fecha_fin` futura sigue
apareciendo los días siguientes aunque el feed lo retire.

La agenda trae fechas, no horas. Las horas salen de `points.json` (campo
`agenda_ids` de cada punto con sus `show_times`); si no hay, el evento sale con
`time: null` y la UI muestra «hora por confirmar».

    python scripts/agenda.py            # tras snapshot.py agenda (cron 07:30)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "data" / "snapshots" / "agenda"
OUT = ROOT / "data" / "agenda" / "events.json"
POINTS = ROOT / "data" / "points.json"
TIME_TBC = "time_tbc"  # clave i18n de «hora por confirmar»


def _times_by_agenda_id(points: list[dict[str, Any]]) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for point in points:
        for agenda_id in point.get("agenda_ids") or []:
            out[int(agenda_id)] = list(point.get("show_times") or [])
    return out


def normalise(raw: dict[str, Any], times: dict[int, list[str]], seen: str) -> dict[str, Any]:
    show_times = times.get(int(raw["id"]))
    return {
        "id": int(raw["id"]),
        "title": raw["titulo"],
        "start": raw.get("fecha_inicio"),
        "end": raw.get("fecha_fin"),
        "permanent": bool(raw.get("permanente")),
        "address": raw.get("direccion") or None,
        "venue_id": raw.get("instalacion"),
        "categories": [c for c in str(raw.get("subcategoria") or "").split(",") if c],
        "image": raw.get("imagen"),
        "time": show_times or None,
        "time_label": None if show_times else TIME_TBC,
        "last_seen": seen,
    }


def merge(
    history: list[dict[str, Any]], snapshot: dict[str, Any], points: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Funde el snapshot en el historial; lo nuevo gana, lo viejo se conserva."""
    times = _times_by_agenda_id(points)
    seen = str(snapshot["fetched_at"])
    by_id = {int(e["id"]): e for e in history}
    for raw in snapshot["data"]:
        by_id[int(raw["id"])] = normalise(raw, times, seen)
    return sorted(by_id.values(), key=lambda e: (e["start"] or "", e["id"]))


def on_day(events: list[dict[str, Any]], day: str) -> list[dict[str, Any]]:
    """Eventos activos un día `YYYY-MM-DD`: fechados que lo cubren + permanentes."""
    return [
        e
        for e in events
        if e["permanent"] or (e["start"] and e["end"] and e["start"] <= day <= e["end"])
    ]


def _load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main() -> int:
    snapshot = _load(SNAPSHOTS / "latest.json", None)
    if snapshot is None:
        print("sin snapshot de agenda: ejecuta antes `python scripts/snapshot.py agenda`")
        return 1
    events = merge(_load(OUT, []), snapshot, _load(POINTS, []))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(events)} eventos en {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
