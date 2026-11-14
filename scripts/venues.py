"""Cruce de eventos de la agenda con recintos (D-04).

La agenda trae `instalacion` (id interno del Concello) y/o `direccion` (texto
libre), pero los ids **no** coinciden con ningún dataset público de recintos
(`cultura/centros`, `deportes/centros`, `educacion/centros`; comprobado
2026-11-14). Así que el cruce va en cascada:

1. **id**: `data/venues_ids.json` (id → recinto). Se aprende solo: cuando un
   evento trae id y una dirección que cruza por 2 o 3, se guarda el par.
   A mano se pueden añadir ids en el mismo fichero.
2. **nombre**: el nombre de un recinto conocido aparece en `direccion`
   («Casa das Artes. Rúa Policarpo Sanz, 15…»).
3. **dirección**: calle + número de un recinto aparecen en `direccion`.

Recintos conocidos: centros culturales del Concello (`cultura/centros.json`)
más los puntos de Navidad (`data/points.json`). Lo que no cruza va a
`unmatched` y el evento sale **solo en la lista**, nunca en el mapa.

    python -m scripts.venues     # tras scripts/agenda.py → data/agenda/events_geo.json
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "data" / "agenda" / "events.json"
POINTS = ROOT / "data" / "points.json"
IDS = ROOT / "data" / "venues_ids.json"
OUT = ROOT / "data" / "agenda" / "events_geo.json"
CULTURE_URL = "https://datos.vigo.org/data/cultura/centros.json"
USER_AGENT = "TinyVigo-D04/0.1 (+https://github.com/cacelass/NaviHack)"
STREET_WORDS = r"\b(rua|r|avenida|avda|av|praza|plaza|pza|calle|c|paseo|rúa|estrada|camino)\b\.?"


def norm(text: str | None) -> str:
    """Minúsculas, sin tildes, sin puntuación, espacios simples."""
    s = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def _street_key(street: str | None, number: Any) -> str | None:
    street_n = re.sub(STREET_WORDS, " ", norm(street)).strip()
    street_n = re.sub(r"\s+", " ", street_n)
    return f"{street_n} {number}".strip() if street_n and number else None


def venues_from_culture(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "venue_id": f"cultura-{r['id']}",
            "name": r["nombre"],
            "lat": r["lat"],
            "lon": r["lon"],
            "street_key": _street_key(r.get("calle"), r.get("numero")),
        }
        for r in rows
        if r.get("lat") and r.get("lon")
    ]


def venues_from_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "venue_id": p["id"],
            "name": p["name"].get("es") or p["name"].get("gl"),
            "lat": p["lat"],
            "lon": p["lon"],
            "street_key": None,
        }
        for p in points
    ]


def _by_text(direccion: str | None, venues: list[dict[str, Any]]) -> tuple[dict | None, str | None]:
    d = norm(direccion)
    if not d:
        return None, None
    named = [v for v in venues if len(norm(v["name"])) >= 6 and norm(v["name"]) in d]
    if named:  # el nombre más largo gana: «Teatro Afundación» antes que «Teatro»
        return max(named, key=lambda v: len(norm(v["name"]))), "name"
    d_street = " " + re.sub(r"\s+", " ", re.sub(STREET_WORDS, " ", d)) + " "
    for v in venues:
        if v["street_key"] and f" {v['street_key']} " in d_street:
            return v, "address"
    return None, None


def join(
    events: list[dict[str, Any]], venues: list[dict[str, Any]], ids: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Devuelve (eventos con venue o sin él, no cruzados, ids aprendidos/actualizados)."""
    by_venue = {v["venue_id"]: v for v in venues}
    learned = dict(ids)
    out, unmatched = [], []
    for e in events:
        venue, how = None, None
        vid = str(e["venue_id"]) if e.get("venue_id") is not None else None
        if vid and learned.get(vid) in by_venue:
            venue, how = by_venue[learned[vid]], "id"
        if venue is None:
            venue, how = _by_text(e.get("address"), venues)
            if venue and vid:
                learned[vid] = venue["venue_id"]
        if venue:
            place = {k: venue[k] for k in ("venue_id", "name", "lat", "lon")}
            out.append({**e, "venue": place, "venue_match": how, "on_map": True})
        else:
            out.append({**e, "venue": None, "venue_match": None, "on_map": False})
            if vid or e.get("address"):
                unmatched.append(
                    {
                        "id": e["id"],
                        "title": e["title"],
                        "venue_id": vid,
                        "address": e.get("address"),
                    }
                )
    return out, unmatched, learned


def _load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main() -> int:
    req = urllib.request.Request(CULTURE_URL, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        culture = json.loads(resp.read())
    venues = venues_from_culture(culture) + venues_from_points(
        _load(POINTS, {"points": []})["points"]
    )
    events, unmatched, learned = join(_load(EVENTS, []), venues, _load(IDS, {}))
    IDS.write_text(
        json.dumps(learned, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
    )
    OUT.write_text(
        json.dumps({"events": events, "unmatched": unmatched}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    on_map = sum(e["on_map"] for e in events)
    print(f"{len(events)} eventos: {on_map} en el mapa, {len(unmatched)} sin cruzar (en unmatched)")
    for u in unmatched:
        print(f"  sin cruzar: [{u['venue_id']}] {u['title'][:50]} — {u['address']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
