"""Cargador de la capa navideña del Concello (R-06): base de `points.json`.

Capa: item ArcGIS Online `41caae2067564a92a79d91f5a08c00f6`, título «Puntos
interés Navidad 2026 2027», dueño `concellovigo`, público. El servicio conserva
el nombre de una edición vieja (`Puntos_interés_Navidad_2023_2024`): el Concello
reutiliza el mismo FeatureServer cada temporada y solo cambia el título y los
datos (detalle en `vault/01_PROYECTO/fuentes_datos.md`).

Pasos: descarga todas las páginas (`resultOffset`, ≤2000 por petición) en
WGS84, guarda la copia cruda con `fetched_at` en `data/raw/concello_navidad/`,
mapea los campos a `data/points.json` y aplica `data/points_overrides.json`
(cambios de 2026 sacados de prensa hasta que el Concello los publique). Si la
capa desaparece o falla, se reconstruye desde la última copia cruda guardada.

    python -m scripts.christmas_layer            # descarga + points.json
    python -m scripts.christmas_layer --offline  # solo desde la última copia cruda

Stdlib pura.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ITEM_ID = "41caae2067564a92a79d91f5a08c00f6"
LAYER_URL = (
    "https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/"
    "Puntos_inter%C3%A9s_Navidad_2023_2024/FeatureServer/0"
)
RAW = ROOT / "data" / "raw" / "concello_navidad"
POINTS = ROOT / "data" / "points.json"
OVERRIDES = ROOT / "data" / "points_overrides.json"
PAGE = 2000
USER_AGENT = "TinyVigo-R06/0.1 (+https://github.com/cacelass/NaviHack)"

TYPES = {  # tipologia del Concello → tipo de TinyVigo (spec F2)
    "Atracciones": "attraction",
    "Elementos expositivos": "exhibit",
    "Elementos lumínicos": "light",
    "Galerías de fotos": "photo_gallery",
    "Mercados navideños": "market",
    "Papa Noel - Reyes Magos": "santa_kings",
    "Photocalls": "photocall",
}


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        data: dict[str, Any] = json.loads(resp.read())
    if "error" in data:
        raise RuntimeError(f"ArcGIS: {data['error']}")
    return data


def fetch_all(get: Callable[[str], dict[str, Any]] = _get_json) -> list[dict[str, Any]]:
    """Todas las features, página a página, en WGS84."""
    features: list[dict[str, Any]] = []
    while True:
        query = urllib.parse.urlencode(
            {
                "where": "1=1",
                "outFields": "*",
                "outSR": 4326,
                "resultOffset": len(features),
                "resultRecordCount": PAGE,
                "orderByFields": "id",
                "f": "json",
            }
        )
        page = get(f"{LAYER_URL}/query?{query}")
        features += page.get("features", [])
        if not page.get("exceededTransferLimit"):
            return features


def text(value: Any) -> str | None:
    """HTML del Concello → texto plano (listas a líneas, entidades decodificadas)."""
    if not value:
        return None
    s = re.sub(r"<\s*(br|/p|/li)\s*/?>", "\n", str(value), flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in s.splitlines()]
    return "\n".join(line for line in lines if line) or None


VAGUE_ADDRESS = ("por toda la ciudad", "diversas localizaciones", "varias ubicaciones")
ITEM_URL = f"https://www.arcgis.com/home/item.html?id={ITEM_ID}"


def switch_on_times(schedule: str | None) -> list[str]:
    """Horas de «Encendido: … 18:00 h» del horario oficial → ["18:00"] (para la agenda y la noche)."""
    if not schedule:
        return []
    times = []
    for line in schedule.splitlines():
        if re.match(r"\s*(encendido|acendido|aceso)\b", line, re.I):
            times += [f"{int(h):02d}:{m}" for h, m in re.findall(r"(\d{1,2})[:.](\d{2})", line)]
    return sorted(set(times))


def to_point(feature: dict[str, Any], fetched_at: str = "") -> dict[str, Any]:
    a = feature["attributes"]
    g = feature.get("geometry") or {}
    lon = g.get("x", a.get("lon"))
    lat = g.get("y", a.get("lat"))
    address = a.get("dir_txt_alternativo") or " ".join(
        str(p) for p in (a.get("dir_nombre_via"), a.get("dir_numero")) if p
    )
    schedule_es = text(a.get("horario_atencion"))
    vague = any(v in (address or "").lower() for v in VAGUE_ADDRESS)
    return {
        "id": f"concello-{a['id']}",
        "concello_id": str(a["id"]),
        "type": TYPES.get(a.get("tipologia") or "", "other"),
        "name": {"es": a.get("nombre"), "gl": a.get("nombre_gl")},
        "short": {
            "es": text(a.get("descripcion_corta")),
            "gl": text(a.get("descripcion_corta_gl")),
        },
        "long": {"es": text(a.get("descripcion_larga")), "gl": text(a.get("descripcion_larga_gl"))},
        "schedule_text": {
            "es": schedule_es,
            "gl": text(a.get("horario_atencion_gl")),
        },
        "lat": round(float(lat), 6),
        "lon": round(float(lon), 6),
        "address": address or None,
        "image_url": a.get("image_url"),
        "web": a.get("web") or None,
        "source": "concello_arcgis",
        "sources": [
            {
                "name": "Concello de Vigo — capa ArcGIS Navidad 2026-27",
                "url": ITEM_URL,
                "date": fetched_at[:10],
            }
        ],
        "last_verified": fetched_at[:10] or None,
        # «Por toda la ciudad»: el Concello pone un punto genérico; no es una ubicación real.
        "position": "approximate" if vague else "address",
        "status": "official",
        "agenda_ids": [],
        "show_times": switch_on_times(schedule_es),
    }


def apply_overrides(points: list[dict[str, Any]], overrides: list[dict[str, Any]]) -> list[dict]:
    """`{"id": ..., ...campos}` parchea un punto; un id nuevo lo añade como «de prensa».

    `{"id": ..., "remove": true}` lo quita (p. ej. una atracción que este año no viene).
    """
    by_id = {p["id"]: p for p in points}
    for o in overrides:
        if o.get("remove"):
            by_id.pop(o["id"], None)
        elif o["id"] in by_id:
            by_id[o["id"]] = {**by_id[o["id"]], **o}
        else:
            # Sin respaldo del Concello: la UI lo marca «aún sin confirmar por el Concello».
            by_id[o["id"]] = {"source": "press", "status": "not_confirmed", **o}
    return sorted(by_id.values(), key=lambda p: p["id"])


def save_raw(features: list[dict[str, Any]], now: datetime) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    doc = {
        "fetched_at": now.isoformat(),
        "item_id": ITEM_ID,
        "url": LAYER_URL,
        "features": features,
    }
    path = RAW / f"{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path


def latest_raw() -> dict[str, Any] | None:
    copies = sorted(RAW.glob("*.json"))
    return json.loads(copies[-1].read_text(encoding="utf-8")) if copies else None


def build(raw: dict[str, Any], overrides: list[dict[str, Any]]) -> dict[str, Any]:
    points = apply_overrides([to_point(f, raw["fetched_at"]) for f in raw["features"]], overrides)
    return {"fetched_at": raw["fetched_at"], "source_item": ITEM_ID, "points": points}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="no descargar: usar la última copia")
    args = ap.parse_args(argv)
    if not args.offline:
        try:
            save_raw(fetch_all(), datetime.now(UTC))
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            print(f"capa no disponible ({exc}); sigo con la última copia cruda", file=sys.stderr)
    raw = latest_raw()
    if raw is None:
        print("sin copia cruda: no hay de dónde construir points.json", file=sys.stderr)
        return 1
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else []
    out = build(raw, overrides)
    POINTS.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out['points'])} puntos (copia del {raw['fetched_at']}) en data/points.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
