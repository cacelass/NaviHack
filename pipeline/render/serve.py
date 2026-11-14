"""Servidor mínimo para dejar que el navegador guarde los PNG que pinta.

Las páginas del render dibujan en un canvas y mandan el PNG por POST a
``/save?name=...``; aquí se escribe tal cual en la carpeta servida. Sirve además
los ficheros estáticos (páginas, data.js, ortofoto).

    python3 -m pipeline.render.serve work/render-expansion --port 8099

Uso pensado para un navegador headless: se abre la página, se espera a que el
``document.title`` sea READY y se cierra.
"""

from __future__ import annotations

import argparse
import http.server
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".json": "application/json",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    root: Path

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.root), **kwargs)

    def do_POST(self) -> None:  # noqa: N802 (nombre que impone http.server)
        url = urlparse(self.path)
        if url.path != "/save":
            self.send_error(404)
            return
        name = Path(unquote(url.query.removeprefix("name="))).name
        if not name or name.startswith("."):
            self.send_error(400, "nombre de fichero no válido")
            return
        size = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(size)
        (self.root / name).write_bytes(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
        print(f"guardado {name} ({size / 1024:.0f} kB)", flush=True)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}", flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--port", type=int, default=8099)
    args = ap.parse_args(argv)
    Handler.root = args.root.resolve()
    if not Handler.root.is_dir():
        raise SystemExit(f"no existe {Handler.root}")
    os.chdir(Handler.root)
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"sirviendo {Handler.root} en http://127.0.0.1:{args.port}", flush=True)
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
