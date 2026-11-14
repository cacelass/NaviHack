"""Mide cada cuánto cambian de verdad los feeds del Concello (D-00).

Sondea cada feed con GET condicional (If-None-Match) a intervalo fijo y anota
cada cambio de ETag/Last-Modified y, si el payload lo trae, el timestamp de
origen. Al final imprime un resumen en JSON: intervalos entre cambios, tamaño,
CORS y disponibilidad.

    python scripts/measure_feeds.py --minutes 30 --every 30 > muestras.json

Stdlib pura: corre sin instalar nada.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime

FEEDS = {
    "parkings-ocupacion": "https://datos.vigo.org/data/trafico/parkings-ocupacion.json",
    "agenda-hoy": "https://datos.vigo.org/data/axenda/agenda-hoy.json",
}
USER_AGENT = "TinyVigo-D00/0.1 (+https://github.com/cacelass/NaviHack)"


@dataclass
class FeedLog:
    url: str
    etag: str | None = None
    polls: int = 0
    errors: int = 0
    size: int | None = None
    cors: str | None = None
    last_modified: str | None = None
    changes: list[float] = field(default_factory=list)  # epoch de cada cambio visto
    source_ts: list[str] = field(default_factory=list)  # timestamp de origen por cambio


def source_timestamp(payload: object) -> str | None:
    """El timestamp que trae el propio dato (parkings: `fechahora`)."""
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        value = payload[0].get("fechahora")
        return str(value) if value is not None else None
    return None


def intervals(changes: list[float]) -> list[float]:
    """Segundos entre cambios consecutivos. El primero no cuenta: es el arranque."""
    return [b - a for a, b in zip(changes, changes[1:], strict=False)]


def poll(log: FeedLog) -> None:
    headers = {"User-Agent": USER_AGENT, "Origin": "https://tinyvigo.example"}
    if log.etag:
        headers["If-None-Match"] = log.etag
    req = urllib.request.Request(log.url, headers=headers)  # noqa: S310 — URL fija https
    log.polls += 1
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            body = resp.read()
            log.etag = resp.headers.get("ETag")
            log.last_modified = resp.headers.get("Last-Modified")
            log.cors = resp.headers.get("Access-Control-Allow-Origin")
            log.size = len(body)
            log.changes.append(time.time())
            ts = source_timestamp(json.loads(body))
            if ts:
                log.source_ts.append(ts)
    except urllib.error.HTTPError as exc:
        if exc.code != 304:
            log.errors += 1
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        log.errors += 1


def summary(logs: dict[str, FeedLog]) -> dict[str, object]:
    out: dict[str, object] = {"measured_at": datetime.now(UTC).isoformat()}
    for name, log in logs.items():
        gaps = intervals(log.changes)
        out[name] = {
            "url": log.url,
            "polls": log.polls,
            "errors": log.errors,
            "availability": round(1 - log.errors / log.polls, 3) if log.polls else None,
            "size_bytes": log.size,
            "cors_allow_origin": log.cors,
            "last_modified": log.last_modified,
            "changes_seen": max(len(log.changes) - 1, 0),
            "interval_s": {
                "median": statistics.median(gaps) if gaps else None,
                "min": min(gaps) if gaps else None,
                "max": max(gaps) if gaps else None,
            },
            "source_timestamps": log.source_ts,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--every", type=float, default=30, help="segundos entre sondeos")
    args = ap.parse_args(argv)
    logs = {name: FeedLog(url) for name, url in FEEDS.items()}
    end = time.time() + args.minutes * 60
    while True:
        for log in logs.values():
            poll(log)
        if time.time() + args.every > end:
            break
        time.sleep(args.every)
    json.dump(summary(logs), sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
