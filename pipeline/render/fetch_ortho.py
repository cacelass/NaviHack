"""Baja la ortofoto PNOA que falta para la zona nueva y la deja en trozos.

El render del 3x3 salió de una ortofoto de 2200x2720 m a 0,4 m/px. Aquí no se
vuelve a bajar esa zona: se reutiliza la misma imagen (si se volviera a pedir,
el WMS remuestrearía y las teselas ya pintadas cambiarían de píxeles) y solo se
piden los trozos nuevos, alineados a la misma rejilla de 0,4 m para que la junta
no se note.

    python3 -m pipeline.render.fetch_ortho --out work/render-expansion/ortho \\
        --old ~/Downloads/vigo-bloque-3x3/work/ortho.jpg

Cada trozo se llama ``new_<x0>_<y0>.jpg`` (metros del borde noroeste) y lleva un
``.json`` con el bbox en grados, para poder repetir la petición.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from pipeline import georef

WMS = "https://www.ign.es/wms-inspire/pnoa-ma"
LAYER = "OI.OrthoimageCoverage"
ROWS = 3  # el WMS no sirve franjas muy altas de una vez
SOLAPE_M = 120.0  # la franja nueva empieza dentro de la vieja: la tapa el render


def params_json() -> dict:
    path = Path(georef.__file__).resolve().parent / "render" / "render-params.json"
    return json.loads(path.read_text(encoding="utf-8"))


def canvas_ground(params: georef.RenderParams, canvas: str = "expansion") -> tuple[float, ...]:
    """bbox en metros (x0, y0, x1, y1) del suelo que abarca el lienzo."""
    c = params.canvas(canvas)
    xs, ys = [], []
    for px in (0, c.width):
        for py in (0, c.height):
            x, y = params.to_metres(px, py, canvas=canvas)
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def pieces(
    params: georef.RenderParams, res: float, canvas: str = "expansion", from_x: float | None = None
) -> list[dict[str, float]]:
    """Franja nueva al este de la ortofoto vieja, en trozos de la misma rejilla."""
    old_half_x = float(params_json()["ortho"]["half_m"][0])
    gx0, gy0, gx1, gy1 = canvas_ground(params, canvas)
    start = old_half_x if from_x is None else from_x
    x0 = _snap(max(start - SOLAPE_M, gx0 - res), res)
    x1 = _snap(min(gx1 + 100.0, gx1 + 200.0), res)
    y0 = _snap(gy0 - 20.0, res)
    y1 = _snap(gy1 + 20.0, res)
    step = _snap((y1 - y0) / ROWS, res)
    out = []
    for i in range(ROWS):
        south, north = y0 + i * step, y1 if i == ROWS - 1 else y0 + (i + 1) * step
        out.append(
            {
                "x0": x0,
                "x1": x1,
                "y_south": south,
                "y_north": north,
                "w": round((x1 - x0) / res),
                "h": round((north - south) / res),
            }
        )
    return out


def north_cap(params: georef.RenderParams, res: float, canvas: str = "wide") -> dict[str, float]:
    """Franja que falta arriba del lienzo: el bloque de la ortofoto vieja y el primer trozo de la
    ampliación acaban en distintas filas, y entre los dos queda un hueco que el render rellena de gris.
    """
    _, _, gx1, gy1 = canvas_ground(params, canvas)
    old_half_x = float(params_json()["ortho"]["half_m"][0])
    x0 = _snap(old_half_x - SOLAPE_M, res)
    x1 = _snap(gx1 + 100.0, res)
    y_south = _snap(float(params_json()["ortho"]["half_m"][1]) - 40.0, res)
    y_north = _snap(gy1 + 60.0, res)
    return {
        "x0": x0,
        "x1": x1,
        "y_south": y_south,
        "y_north": y_north,
        "w": round((x1 - x0) / res),
        "h": round((y_north - y_south) / res),
    }


def _snap(value: float, res: float) -> float:
    """Borde en múltiplo exacto de la resolución, para no remuestrear al encajar."""
    return res * round(value / res)


def _url(params: georef.RenderParams, p: dict[str, float]) -> str:
    bbox = (
        params.geo.lat0 + p["y_south"] / params.geo.m_per_deg_lat,
        params.geo.lon0 + p["x0"] / params.geo.m_per_deg_lon,
        params.geo.lat0 + p["y_north"] / params.geo.m_per_deg_lat,
        params.geo.lon0 + p["x1"] / params.geo.m_per_deg_lon,
    )
    query = urllib.parse.urlencode(
        {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetMap",
            "LAYERS": LAYER,
            "STYLES": "",
            "CRS": "EPSG:4326",
            "BBOX": ",".join(f"{v:.9f}" for v in bbox),
            "WIDTH": int(p["w"]),
            "HEIGHT": int(p["h"]),
            "FORMAT": "image/jpeg",
        }
    )
    p["bbox"] = bbox  # se guarda junto al trozo, para trazabilidad
    return f"{WMS}?{query}"


def fetch(url: str, dest: Path, tries: int = 5) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  {dest.name}  ya estaba")
        return
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VigoPixelMap/1.0"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = resp.read()
            if body[:2] != b"\xff\xd8":
                raise RuntimeError(f"no es un JPEG: {body[:120]!r}")
            dest.write_bytes(body)
            print(f"  {dest.name}  {len(body) / 1024:.0f} kB")
            return
        except Exception as exc:  # red, 502 del WMS, lo que sea: se reintenta
            print(f"  fallo {dest.name} ({attempt + 1}/{tries}): {exc}")
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"no se pudo bajar {dest.name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True, help="carpeta donde dejar los trozos")
    ap.add_argument("--old", type=Path, help="ortho.jpg del 3x3 (se copia como old.jpg)")
    ap.add_argument("--res", type=float, default=0.4, help="metros por píxel de la ortofoto")
    ap.add_argument("--north-cap", action="store_true", help="añade la franja norte que falta")
    ap.add_argument("--canvas", default="expansion", help="lienzo a cubrir (expansion, wide)")
    ap.add_argument("--from-x", type=float, help="metros al este desde donde ya hay ortofoto")
    args = ap.parse_args(argv)

    params = georef.params()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.old and not (args.out / "old.jpg").exists():
        (args.out / "old.jpg").write_bytes(args.old.read_bytes())
        print(f"  old.jpg  {args.old.stat().st_size / 1024:.0f} kB (la del 3x3, sin tocar)")

    chunks = pieces(params, args.res, args.canvas, args.from_x)
    if args.north_cap:
        chunks.append(north_cap(params, args.res, args.canvas))
    for p in chunks:
        name = f"new_{p['x0']:+.0f}_{p['y_south']:+.0f}.jpg"
        url = _url(params, p)
        fetch(url, args.out / name)
        (args.out / name).with_suffix(".json").write_text(
            json.dumps(
                {
                    "x0": p["x0"],
                    "y0": p["y_north"],
                    "width": p["w"],
                    "height": p["h"],
                    "res": args.res,
                    "bbox_s_w_n_e": p["bbox"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
    total = sum(int(p["w"]) * int(p["h"]) for p in chunks)
    print(f"{len(chunks)} trozos, {total / 1e6:.1f} Mpx nuevos en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
