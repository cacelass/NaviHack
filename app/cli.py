"""
app.cli — punto de entrada del proyecto: ``python -m app`` o ``make run``.

Un esqueleto, no un framework: argparse de la stdlib y un subcomando de
ejemplo. Si tu proyecto no es una CLI, borra este fichero y ``__main__.py`` —
el arnes no los necesita.

Subcomandos:

* ``hello`` — ejemplo basico: saluda y sale.
* ``points`` — lista los puntos navidenos de Vigo desde ``data/points.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from app import __version__
from app.points import count_by_type, load_points, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app",
        description="TinyVigo: mapa web de Vigo en Navidad.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # -- hello ---------------------------------------------------------------
    hello_p = sub.add_parser("hello", help="Saluda y sale.")
    hello_p.add_argument("--name", default="mundo", help="A quien saludar.")

    # -- points --------------------------------------------------------------
    points_p = sub.add_parser("points", help="Lista los puntos navidenos.")
    points_p.add_argument(
        "--lang",
        choices=["es", "gl", "en"],
        default="es",
        help="Idioma del nombre (es, gl, en).",
    )
    points_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Formato de salida.",
    )
    points_p.add_argument(
        "--by-type",
        action="store_true",
        help="Muestra el conteo por tipo.",
    )

    return parser


def hello(name: str) -> str:
    return f"Hola, {name}."


def _cmd_points(args: argparse.Namespace) -> int:
    """Ejecuta el subcomando ``points``."""
    try:
        points = load_points()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.by_type:
        counts = count_by_type(points)
        print(f"Puntos por tipo ({len(points)} total):")
        for t, c in sorted(counts.items()):
            print(f"  {t}: {c}")
        return 0

    if args.format == "json":
        data = summary(points, lang=args.lang)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    # text format
    print(f"Puntos navidenos de Vigo ({len(points)}):")
    for p in summary(points, lang=args.lang):
        status_tag = f" [{p['status']}]" if p["status"] != "official" else ""
        print(f"  {p['id']}: {p['name']}{status_tag} ({p['type']})")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "hello":
        print(hello(args.name))
        return 0
    if args.command == "points":
        return _cmd_points(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
