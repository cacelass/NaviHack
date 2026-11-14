"""Baja los edificios del Concello que faltan para el lienzo ampliado.

El fichero del 3x3 (``original/edificios_concello.json``) se descargó con una
caja que solo cubría el 3x3: fuera de ella apenas hay 15 edificios, así que la
zona nueva salía como foto plana sin volúmenes. Aquí se pide la misma capa
(FeatureServer «Edificios 3D de Vigo en vectorial», la de ``scripts/buildings.py``)
para el borde este, con los mismos campos y el mismo formato de registro que el
fichero original, y se deja aparte para no tocar lo que ya se renderizó.

    python3 -m pipeline.render.fetch_buildings

Escribe ``original/edificios_este.json``. ``scene.py`` suma los dos ficheros y
descarta los repetidos por referencia catastral.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "original" / "edificios_este.json"
LAYER = (
    "https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/"
    "Edificios_3D_de_Vigo_en_vectorial/FeatureServer/0/query"
)
FIELDS = "refcat,altura,z,ano_antiguedade,ano_reforma,uso_principal_superficie,interes_turismo,superficie_total,habitantes"
# Caja WGS84 (oeste, sur, este, norte): del borde de la ortofoto vieja hasta pasada
# la esquina este del lienzo ampliado (suelo hasta x = 1517 m y y = -1248 m).
BBOX = (-8.7150, 42.2255, -8.7050, 42.2515)
PAGE = 1000


def _get(params: dict[str, str], tries: int = 5) -> dict:
    url = f"{LAYER}?{urllib.parse.urlencode(params)}"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "VigoPixelMap/1.0 (hackathon)"}
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                doc = json.loads(resp.read())
            if "error" not in doc:
                return doc
            print(f"  error del servidor: {doc['error']}")
        except Exception as exc:  # red, 5xx, JSON cortado: se reintenta
            print(f"  fallo ({attempt + 1}/{tries}): {exc}")
        time.sleep(2 * (attempt + 1))
    raise SystemExit("el servicio de edificios no responde")


def fetch(bbox: tuple[float, float, float, float] = BBOX) -> list[dict]:
    envelope = ",".join(str(v) for v in bbox)
    out: list[dict] = []
    offset = 0
    while True:
        doc = _get(
            {
                "where": "1=1",
                "geometry": envelope,
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outSR": "4326",
                "outFields": FIELDS,
                "returnGeometry": "true",
                "resultOffset": str(offset),
                "resultRecordCount": str(PAGE),
                "orderByFields": "OBJECTID",
                "f": "json",
            }
        )
        feats = doc.get("features", [])
        for f in feats:
            rings = (f.get("geometry") or {}).get("rings")
            if not rings:
                continue
            a = f["attributes"]
            out.append(
                {
                    "r": a.get("refcat"),
                    "h": a.get("altura"),
                    "y": a.get("ano_antiguedade"),
                    "ry": a.get("ano_reforma"),
                    "u": a.get("uso_principal_superficie"),
                    "t": a.get("interes_turismo"),
                    "s": a.get("superficie_total"),
                    "rings": [[[round(p[0], 7), round(p[1], 7)] for p in ring] for ring in rings],
                }
            )
        print(f"  {len(out)} edificios")
        if not doc.get("exceededTransferLimit") and len(feats) < PAGE:
            return out
        offset += PAGE


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    buildings = fetch()
    args.out.write_text(json.dumps(buildings, separators=(",", ":")), encoding="utf-8")
    known = {
        b["r"] for b in json.loads((HERE / "original" / "edificios_concello.json").read_text())
    }
    new = [b for b in buildings if b["r"] not in known]
    print(f"{len(buildings)} edificios en la franja; {len(new)} no estaban en el fichero del 3x3")
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
