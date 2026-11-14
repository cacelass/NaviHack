"""Snapshot publisher de los feeds del Concello (D-01).

Una pasada: descarga el feed, valida el payload y, si es bueno, escribe
`data/snapshots/<feed>/latest.json` (+ copia con timestamp) con `fetched_at` y
el timestamp de origen, y añade una fila a `history.jsonl`. Si el payload es
malo o la red falla, **no toca** `latest.json`: el último bueno se queda.

    python scripts/snapshot.py parkings     # cron: */2 * * * *  (ver fuentes_datos.md, A7)
    python scripts/snapshot.py agenda       # cron: 30 7,9 * * * (Europe/Madrid)

La app lee `latest.json` y calcula la edad con `age()`; pasado `stale_after_s`
muestra «sin datos» (umbrales medidos en D-00).

Stdlib pura.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "snapshots"
USER_AGENT = "TinyVigo-snapshot/0.1 (+https://github.com/cacelass/NaviHack)"


def _valid_parkings(payload: object) -> str | None:
    if not isinstance(payload, list) or not payload:
        return "se esperaba una lista no vacía"
    keys = {"nombre", "plazaslibres", "totalplazas", "lat", "lon", "fechahora"}
    for row in payload:
        if not isinstance(row, dict) or not keys <= row.keys():
            return f"registro sin campos {sorted(keys)}"
    return None


def _valid_agenda(payload: object) -> str | None:
    if not isinstance(payload, list):
        return "se esperaba una lista"
    if any(not isinstance(r, dict) or "titulo" not in r for r in payload):
        return "registro sin 'titulo'"
    return None


def _ts_parkings(payload: list[dict[str, object]], last_modified: str | None) -> str | None:
    # `fechahora` es hora local de Madrid sin zona (D-00): se guarda tal cual.
    return max(str(r["fechahora"]) for r in payload)


def _ts_header(payload: list[dict[str, object]], last_modified: str | None) -> str | None:
    return last_modified


@dataclass(frozen=True)
class Feed:
    url: str
    validate: Callable[[object], str | None]
    source_ts: Callable[[list[dict[str, object]], str | None], str | None]
    stale_after_s: int


FEEDS = {
    "parkings": Feed(
        "https://datos.vigo.org/data/trafico/parkings-ocupacion.json",
        _valid_parkings,
        _ts_parkings,
        stale_after_s=10 * 60,
    ),
    "agenda": Feed(
        "https://datos.vigo.org/data/axenda/agenda-hoy.json",
        _valid_agenda,
        _ts_header,
        stale_after_s=36 * 3600,
    ),
}


def fetch(url: str) -> tuple[bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 — URL fija https
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        return resp.read(), resp.headers.get("Last-Modified")


def publish(
    name: str,
    body: bytes,
    last_modified: str | None,
    out: Path = OUT,
    now: datetime | None = None,
) -> dict[str, object]:
    """Valida y escribe el snapshot. Devuelve la fila de histórico."""
    feed = FEEDS[name]
    now = now or datetime.now(UTC)
    folder = out / name
    folder.mkdir(parents=True, exist_ok=True)
    row: dict[str, object] = {"fetched_at": now.isoformat(), "ok": False}
    try:
        payload = json.loads(body)
        error = feed.validate(payload)
    except json.JSONDecodeError as exc:
        error = f"JSON inválido: {exc.msg}"
    if error:
        row["error"] = error
    else:
        snap = {
            "feed": name,
            "source_url": feed.url,
            "fetched_at": now.isoformat(),
            "source_timestamp": feed.source_ts(payload, last_modified),
            "stale_after_s": feed.stale_after_s,
            "data": payload,
        }
        text = json.dumps(snap, ensure_ascii=False)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        (folder / f"{stamp}.json").write_text(text, encoding="utf-8")
        tmp = folder / "latest.json.tmp"
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(folder / "latest.json")  # atómico: la app nunca lee medio fichero
        row.update(ok=True, source_timestamp=snap["source_timestamp"], records=len(payload))
    with (folder / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def age(snapshot: dict[str, object], now: datetime | None = None) -> tuple[float, bool]:
    """Edad en segundos del snapshot y si ya cuenta como «sin datos»."""
    now = now or datetime.now(UTC)
    fetched = datetime.fromisoformat(str(snapshot["fetched_at"]))
    seconds = (now - fetched).total_seconds()
    return seconds, seconds > float(str(snapshot["stale_after_s"]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("feed", choices=sorted(FEEDS))
    args = ap.parse_args(argv)
    now = datetime.now(UTC)
    try:
        body, last_modified = fetch(FEEDS[args.feed].url)
    except (urllib.error.URLError, TimeoutError) as exc:
        body, last_modified = b"", None
        print(f"red: {exc}", file=sys.stderr)
    row = publish(args.feed, body, last_modified, now=now)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if row["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
