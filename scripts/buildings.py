"""Edificios 3D del Concello → huella + altura para el render (X-05).

Fuente: FeatureServer «Edificios 3D de Vigo en vectorial» (item ArcGIS
`1196c4f7cdfa478eb9ac09b1fffc2576`, dueño `concellovigo`), capa 0 `EDIFICIOS`,
41 289 edificios, geometría **MultiPatch** en EPSG:25829 (ETRS89 / UTM 29N).

- Se lee por páginas (`resultOffset`, ≤2000 por petición) y recortado a la zona
  (envolvente WGS84; por defecto el núcleo navideño, a afinar en ZONE-01).
- Reproyección: la hace el servidor (`outSR=4326`); `utm29n_to_wgs84` la
  comprueba de forma independiente (test < 0,5 m).
- MultiPatch **no sobrevive** a la consulta: tanto `f=geojson` como `f=json`
  (con `returnZ=true`) devuelven la huella 2D como anillos con z = 0. El volumen
  se reconstruye en RENDER-01 extruyendo la huella `height_m` sobre `base_z`.
  El volumen real (tejados) solo está en el SceneServer (I3S), fuera de v1.
- Salida: `data/render/buildings.geojson`, un Polygon/MultiPolygon WGS84 por
  edificio con `refcat, height_m, base_z, year_built, year_reformed, use`.
  Fallback si el servicio desaparece: huellas de Catastro unidas por `refcat`
  (vault/01_PROYECTO/fuentes_datos.md).

    python -m scripts.buildings                       # núcleo navideño
    python -m scripts.buildings --bbox -8.74,42.22,-8.70,42.25

Stdlib pura.
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LAYER_URL = (
    "https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/"
    "Edificios_3D_de_Vigo_en_vectorial/FeatureServer/0"
)
OUT = ROOT / "data" / "render" / "buildings.geojson"
# Porta do Sol, Alameda, García Barbón con margen. ZONE-01 fija la definitiva.
CORE_BBOX = (-8.7320, 42.2310, -8.7080, 42.2430)
PAGE = 2000
FIELDS = "refcat,altura,z,ano_antiguedade,ano_reforma,uso_principal_superficie,barrio"
USER_AGENT = "TinyVigo-X05/0.1 (+https://github.com/cacelass/NaviHack)"


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        data: dict[str, Any] = json.loads(resp.read())
    if "error" in data:
        raise RuntimeError(f"ArcGIS: {data['error']}")
    return data


def fetch(
    bbox: tuple[float, float, float, float], get: Callable[[str], dict[str, Any]] = _get_json
) -> list[dict[str, Any]]:
    """Edificios que tocan `bbox` (lon/lat), todas las páginas, en WGS84."""
    xmin, ymin, xmax, ymax = bbox
    envelope = {
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
        "spatialReference": {"wkid": 4326},
    }
    features: list[dict[str, Any]] = []
    while True:
        query = urllib.parse.urlencode(
            {
                "where": "1=1",
                "geometry": json.dumps(envelope),
                "geometryType": "esriGeometryEnvelope",
                "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
                "outSR": 4326,
                "outFields": FIELDS,
                "orderByFields": "OBJECTID",
                "resultOffset": len(features),
                "resultRecordCount": PAGE,
                "f": "json",
            }
        )
        page = get(f"{LAYER_URL}/query?{query}")
        features += page.get("features", [])
        if not page.get("exceededTransferLimit"):
            return features


def _ring_area(ring: list[list[float]]) -> float:
    return (
        sum(x1 * y2 - x2 * y1 for (x1, y1, *_), (x2, y2, *_) in zip(ring, ring[1:], strict=False))
        / 2
    )


def to_feature(f: dict[str, Any]) -> dict[str, Any] | None:
    """Esri rings → GeoJSON. Exteriores en sentido horario (Esri), huecos antihorario."""
    rings = [[[round(p[0], 7), round(p[1], 7)] for p in r] for r in f["geometry"].get("rings", [])]
    if not rings:
        return None
    polygons: list[list[list[list[float]]]] = []
    for ring in rings:
        if _ring_area(ring) <= 0 or not polygons:  # horario (área negativa) = exterior
            polygons.append([ring])
        else:
            polygons[-1].append(ring)
    a = f["attributes"]
    height = a.get("altura")
    geometry: dict[str, Any] = (
        {"type": "Polygon", "coordinates": polygons[0]}
        if len(polygons) == 1
        else {"type": "MultiPolygon", "coordinates": polygons}
    )
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "refcat": a.get("refcat"),
            "height_m": round(height, 2) if height and height > 0 else None,
            "base_z": round(a["z"] - height, 2) if a.get("z") is not None and height else None,
            "year_built": a.get("ano_antiguedade") or None,
            "year_reformed": a.get("ano_reforma") or None,
            "use": a.get("uso_principal_superficie"),
            "barrio": a.get("barrio"),
        },
    }


def stats(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Completitud de altura y año más reciente por barrio (para zonas desactualizadas)."""
    props = [f["properties"] for f in features]
    by_barrio: dict[str, list[int]] = defaultdict(list)
    for p in props:
        year = max(p["year_built"] or 0, p["year_reformed"] or 0)
        if year:
            by_barrio[p["barrio"] or "?"].append(year)
    with_height = sum(p["height_m"] is not None for p in props)
    return {
        "buildings": len(props),
        "height_complete": round(with_height / len(props), 4) if props else None,
        "newest_year_by_barrio": {b: max(ys) for b, ys in sorted(by_barrio.items())},
    }


def utm29n_to_wgs84(e: float, n: float) -> tuple[float, float]:
    """ETRS89/UTM 29N → (lon, lat). GRS80 ≈ WGS84 a escala de metro. Serie de Krüger."""
    a, f = 6378137.0, 1 / 298.257222101
    k0, e0, lon0 = 0.9996, 500000.0, math.radians(-9.0)
    n_ = f / (2 - f)
    big_a = a / (1 + n_) * (1 + n_**2 / 4 + n_**4 / 64)
    beta = (
        n_ / 2 - 2 * n_**2 / 3 + 37 * n_**3 / 96,
        n_**2 / 48 + n_**3 / 15,
        17 * n_**3 / 480,
    )
    delta = (2 * n_ - 2 * n_**2 / 3 - 2 * n_**3, 7 * n_**2 / 3 - 8 * n_**3 / 5, 56 * n_**3 / 15)
    xi = n / (k0 * big_a)
    eta = (e - e0) / (k0 * big_a)
    xi_p = xi - sum(
        b * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j, b in enumerate(beta, 1)
    )
    eta_p = eta - sum(
        b * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j, b in enumerate(beta, 1)
    )
    chi = math.asin(math.sin(xi_p) / math.cosh(eta_p))
    lat = chi + sum(d * math.sin(2 * j * chi) for j, d in enumerate(delta, 1))
    lon = lon0 + math.atan2(math.sinh(eta_p), math.cos(xi_p))
    return math.degrees(lon), math.degrees(lat)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bbox", help="xmin,ymin,xmax,ymax en lon/lat", default=None)
    args = ap.parse_args(argv)
    bbox = tuple(float(v) for v in args.bbox.split(",")) if args.bbox else CORE_BBOX
    raw = fetch(bbox)  # type: ignore[arg-type]
    features = [g for g in (to_feature(f) for f in raw) if g]
    summary = stats(features)
    doc = {"type": "FeatureCollection", "bbox": list(bbox), "stats": summary, "features": features}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"{summary['buildings']} edificios, altura completa {summary['height_complete']:.1%}, "
        f"en {OUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
