"""Re-verificación semanal de los puntos de Navidad durante la temporada (R-05).

Cadencia: **cada lunes a las 06:00 Europe/Madrid** (cron en
`deploy/snapshot.cron`) y a mano tras cualquier noticia de cambios. Cada pasada:

1. descarga la capa del Concello (`christmas_layer.fetch_all`) y la compara con
   la última copia cruda guardada;
2. anota los cambios (altas, bajas, nombre, tipo, horario, posición > 15 m) en
   `data/raw/concello_navidad/changes.jsonl` — el registro no se reescribe nunca;
3. guarda la copia nueva y reconstruye `points.json` (el texto de horario y
   `last_verified` se actualizan solos);
4. si cambió el **horario** de un punto con programa estructurado
   (`data/programme_2026.json`, escrito a mano en R-04), lo lista en
   `needs_review`: alguien tiene que actualizar sus reglas.

`stale(points, today)` da los puntos con `last_verified` de hace más de 7 días:
la UI no los muestra como vigentes.

    python -m scripts.reverify

Stdlib pura.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime
from typing import Any

from scripts import christmas_layer as layer
from scripts import programme
from scripts.parkings import haversine_m

CHANGES = layer.RAW / "changes.jsonl"
MOVED_M = 15.0
MAX_AGE_DAYS = 7
WATCHED = {"nombre": "name", "tipologia": "type", "horario_atencion": "schedule"}


def _by_id(features: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(f["attributes"]["id"]): f for f in features}


def diff(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cambios entre dos copias crudas de la capa, por id del Concello."""
    a, b = _by_id(old), _by_id(new)
    out: list[dict[str, Any]] = []
    for pid in sorted(b.keys() - a.keys()):
        out.append({"id": pid, "change": "added", "name": b[pid]["attributes"].get("nombre")})
    for pid in sorted(a.keys() - b.keys()):
        out.append({"id": pid, "change": "removed", "name": a[pid]["attributes"].get("nombre")})
    for pid in sorted(a.keys() & b.keys()):
        fa, fb = a[pid], b[pid]
        for field, label in WATCHED.items():
            if (fa["attributes"].get(field) or "") != (fb["attributes"].get(field) or ""):
                out.append(
                    {
                        "id": pid,
                        "change": label,
                        "before": fa["attributes"].get(field),
                        "after": fb["attributes"].get(field),
                    }
                )
        ga, gb = fa.get("geometry") or {}, fb.get("geometry") or {}
        if ga and gb:
            moved = haversine_m(ga["y"], ga["x"], gb["y"], gb["x"])
            if moved > MOVED_M:
                out.append({"id": pid, "change": "moved", "meters": round(moved, 1)})
    return out


def needs_review(changes: list[dict[str, Any]], prog: dict[str, Any]) -> list[str]:
    """Puntos con programa estructurado cuyo horario oficial ha cambiado."""
    return sorted(
        f"concello-{c['id']}"
        for c in changes
        if c["change"] == "schedule" and f"concello-{c['id']}" in prog["points"]
    )


def stale(points: list[dict[str, Any]], today: date) -> list[str]:
    """Puntos con `last_verified` de hace más de 7 días (o sin fecha)."""
    out = []
    for p in points:
        lv = p.get("last_verified")
        if not lv or (today - date.fromisoformat(lv)).days > MAX_AGE_DAYS:
            out.append(p["id"])
    return out


def main() -> int:
    previous = layer.latest_raw()
    now = datetime.now(UTC)
    try:
        features = layer.fetch_all()
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de red deja la copia anterior
        print(f"capa no disponible ({exc}); no se re-verifica hoy", file=sys.stderr)
        return 1
    changes = diff(previous["features"], features) if previous else []
    layer.save_raw(features, now)
    with CHANGES.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps({"checked_at": now.isoformat(), "changes": changes}, ensure_ascii=False)
            + "\n"
        )
    layer.main(["--offline"])  # reconstruye points.json desde la copia recién guardada
    review = needs_review(changes, programme.load())
    print(f"{len(changes)} cambios; revisar programa de: {', '.join(review) or 'ninguno'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
