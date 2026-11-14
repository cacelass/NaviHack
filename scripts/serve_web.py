"""Sirve `web/` en local y la abre en el navegador (`make website`).

La web es estática pero hace `fetch()` de los tiles, así que abrir
`web/index.html` con doble clic (file://) no funciona: hace falta un servidor.

    python -m scripts.serve_web               # http://127.0.0.1:8000
    python -m scripts.serve_web --port 8080 --no-open

Stdlib pura; solo escucha en 127.0.0.1.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import threading
import webbrowser
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true", help="no abrir el navegador")
    args = parser.parse_args(argv)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        print(f"TinyVigo en {url}  (Ctrl+C para parar)")
        if not args.no_open:
            threading.Timer(0.5, webbrowser.open, (url,)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nParado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
