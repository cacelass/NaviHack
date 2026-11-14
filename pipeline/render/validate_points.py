"""Comprueba la georreferencia contra el render y deja la evidencia en un JSON.

Para cada punto del Concello se predice —solo con la cámara y los edificios—
qué altura tiene que mostrar el mapa de alturas del render en su píxel, y se
compara con lo que muestra de verdad. Si la proyección estuviera desplazada, el
píxel caería sobre otro edificio y no cuadraría.

Necesita PIL, igual que `pipeline/assemble_block.py`; el test no, porque lee el
JSON que esto genera:

    python3 -m pipeline.render.validate_points \\
        --height ~/Downloads/vigo-bloque-3x3/render/height.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

from pipeline import georef
from pipeline.render import silhouette

ROOT = Path(__file__).resolve().parents[2]
POINTS = ROOT / "data" / "points.json"
DEFAULT_OUT = Path(__file__).resolve().parent / "fixtures" / "points-3x3.json"

# Un píxel a menos de estos px de un borde de silueta mezcla dos colores por
# antialias y no sirve para comparar alturas.
EDGE_PX = 1.5
TOLERANCE_M = 0.5  # el mapa de alturas va en pasos de 0,25 m


def sample_height(image: Image.Image, px: float, py: float) -> float:
    """Altura que pinta el mapa de alturas: el canal rojo es ``h * 4``."""
    return image.getpixel((int(px), int(py)))[0] / 4.0


def check(params: georef.RenderParams, height_path: Path) -> dict[str, object]:
    image = Image.open(height_path).convert("RGB")
    if image.size != (params.canvas("3x3").width, params.canvas("3x3").height):
        raise SystemExit(f"{height_path} mide {image.size}, se esperaba 3072x3072")
    scene = silhouette.Scene(params, silhouette.load_buildings(params))
    canvas = params.canvas("3x3")
    raw = json.loads(POINTS.read_text(encoding="utf-8"))["points"]

    rows: list[dict[str, object]] = []
    for q in raw:
        px, py = params.to_pixel(q["lat"], q["lon"])
        inside = 0 <= px < canvas.width - 1 and 0 <= py < canvas.height - 1
        row: dict[str, object] = {
            "id": q["id"],
            "lat": q["lat"],
            "lon": q["lon"],
            "px": round(px, 3),
            "py": round(py, 3),
            "inside": inside,
        }
        if inside:
            pred = scene.predict(px, py)
            seen = sample_height(image, px, py)
            row |= {
                "kind": pred.kind,
                "height": round(pred.height, 3),
                "seen": round(seen, 3),
                "edge_px": round(min(pred.edge, 999.0), 2),
                "ok": agrees(pred, seen),
            }
        rows.append(row)
    return {
        "$comment": "Evidencia de GEO-01: lo que predice la geometría frente a lo que pinta el mapa de alturas del render 3x3. Generado por pipeline/render/validate_points.py.",
        "height_map": height_path.name,
        "edge_px": EDGE_PX,
        "tolerance_m": TOLERANCE_M,
        "points": rows,
    }


def agrees(pred: silhouette.Prediction, seen: float) -> bool:
    """¿Cuadra lo que se ve con lo que la geometría dice que hay que ver?"""
    if pred.kind == "wall":
        # Una pared es un degradado: cualquier valor entre suelo y tejado vale.
        return 0.0 <= seen <= pred.height + TOLERANCE_M
    if pred.edge <= EDGE_PX:
        return 0.0 <= seen <= pred.height + TOLERANCE_M
    return abs(seen - pred.height) <= TOLERANCE_M


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--height", type=Path, required=True, help="mapa de alturas del render")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    doc = check(georef.params(), args.height)
    rows = [r for r in doc["points"] if r["inside"]]
    bad = [r for r in rows if not r["ok"]]
    counts: dict[str, int] = {}
    for r in rows:
        counts[str(r["kind"])] = counts.get(str(r["kind"]), 0) + 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{len(rows)} de {len(doc['points'])} puntos caen dentro del lienzo 3x3: {counts}")
    print(f"cuadran con el mapa de alturas: {len(rows) - len(bad)}/{len(rows)}")
    for r in bad:
        print(f"  FALLA {r['id']}: predice {r['height']} m y el render muestra {r['seen']} m")
    print(f"escrito {args.out}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
