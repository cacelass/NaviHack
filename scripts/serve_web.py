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
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


class Handler(http.server.SimpleHTTPRequestHandler):
    # En Windows, copiar el fichero a trozos con varias conexiones a la vez deja algunas
    # respuestas colgadas a mitad (scripts de 150-250 KB): se envía de una sola vez.
    def copyfile(self, source, outputfile):  # type: ignore[no-untyped-def]
        outputfile.write(source.read())
        outputfile.flush()

    def log_message(self, format, *args):  # type: ignore[no-untyped-def]  # noqa: A002
        pass


class Server(http.server.ThreadingHTTPServer):
    # La cola por defecto (5) se desborda cuando el navegador pide scripts y teselas a la
    # vez: en Windows se rechazan conexiones y la primera carga queda en blanco.
    request_queue_size = 256
    daemon_threads = True


def main(argv: list[str] | None = None) -> int:
    # Con Node se usa scripts/serve_web.mjs: el http.server de Python en Windows deja
    # respuestas colgadas con varias conexiones a la vez (ver Handler).
    node = shutil.which("node")
    if node:
        return subprocess.call(
            [node, str(Path(__file__).with_name("serve_web.mjs")), *(argv or sys.argv[1:])]
        )  # noqa: S603
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true", help="no abrir el navegador")
    args = parser.parse_args(argv)

    handler = functools.partial(Handler, directory=str(WEB))
    with Server(("127.0.0.1", args.port), handler) as server:
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
