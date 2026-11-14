"""Regenera TODO `web/data/` de una vez (WEB-05).

1. snapshots de los feeds (parkings, agenda, tiempo, centros) — `scripts/snapshot.py`;
2. puntos, programa y textos — `scripts/build_web_data.py`;
3. bus y tren — `scripts/build_transit_web.py` (necesita los GTFS de X-01/X-02);
4. datos en vivo para la web — `scripts/build_web_live.py`.

    python -m scripts.build_web            # todo
    python -m scripts.build_web --live     # solo 1 y 4 (lo que cambia cada pocos minutos)

Un paso que falla no tumba los demás: se informa y se sigue con el último bueno.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

LIVE = [
    ["scripts/snapshot.py", "parkings"],
    ["scripts/snapshot.py", "agenda"],
    ["scripts/snapshot.py", "weather"],
    ["scripts/snapshot.py", "centros"],
]
STATIC = [
    ["-m", "scripts.build_web_data"],
    ["-m", "scripts.gtfs_renfe"],
    ["-m", "scripts.build_transit_web"],
]
PUBLISH = [["-m", "scripts.build_web_live"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="solo los datos en vivo")
    args = ap.parse_args(argv)
    steps = LIVE + ([] if args.live else STATIC) + PUBLISH
    failed = 0
    for step in steps:
        proc = subprocess.run(
            [sys.executable, *step], capture_output=True, text=True, encoding="utf-8"
        )
        ok = proc.returncode == 0
        failed += not ok
        print(
            ("ok   " if ok else "FALLO")
            + " "
            + " ".join(step)
            + (
                " — " + (proc.stdout or proc.stderr).strip().splitlines()[-1]
                if (proc.stdout or proc.stderr).strip()
                else ""
            )
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
