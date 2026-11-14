"""Qué debería verse en cada píxel del render, según los edificios y la cámara.

El renderer pinta de más lejos a más cerca y, por cada edificio, las paredes que
miran a cámara y la cara superior. En una ortográfica eso equivale, en pantalla,
a barrer la huella del edificio hacia arriba: la altura sube el píxel
``sc * cos(inclinación)`` px por metro (1,41 px/m con la cámara actual).

Con eso se predice, sin mirar el PNG, qué altura tiene que tener el mapa de
alturas en un píxel cualquiera. Sirve para comprobar que la georreferencia y el
render cuentan la misma historia: si la proyección estuviera desplazada, el
píxel caería sobre otro edificio y la altura no cuadraría.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.georef import RenderParams

ORIGINAL = Path(__file__).resolve().parent / "original"


@dataclass(frozen=True)
class Building:
    h: float
    ring: list[tuple[float, float]]  # metros (x al este, y al norte)


def load_buildings(
    params: RenderParams, source: Path = ORIGINAL / "edificios_concello.json"
) -> list[Building]:
    """Los mismos edificios que vio el render, con los mismos redondeos.

    Copia la regla de ``original/build-data.mjs``: entra el edificio si algún
    vértice cae dentro de la mitad descargada de ortofoto, los metros van
    redondeados a 2 decimales y la altura nunca baja de 3 m.
    """
    half = json.loads(
        (Path(__file__).resolve().parent / "render-params.json").read_text(encoding="utf-8")
    )["ortho"]["half_m"]
    half_x, half_y = float(half[0]), float(half[1])
    out: list[Building] = []
    for raw in json.loads(source.read_text(encoding="utf-8")):
        ring = [
            (
                _js_round((lon - params.geo.lon0) * params.geo.m_per_deg_lon),
                _js_round((lat - params.geo.lat0) * params.geo.m_per_deg_lat),
            )
            for lon, lat in raw["rings"][0]
        ]
        if not any(abs(x) < half_x and abs(y) < half_y for x, y in ring):
            continue
        out.append(Building(max(3.0, raw.get("h") or 6.0), ring))
    return out


def _js_round(value: float) -> float:
    """``+v.toFixed(2)`` de JavaScript: 2 decimales y sin ``-0``."""
    out = float(f"{value:.2f}") + 0.0
    return 0.0 if out == 0 else out


@dataclass(frozen=True)
class Prediction:
    height: float  # altura del edificio visible bajo ese píxel (0 = suelo)
    building: int  # índice del edificio visible, -1 si es suelo
    kind: str  # "ground" | "roof" | "wall"
    seen: float  # altura que muestra el render en ese píxel (pared: continua)
    edge: float  # px hasta el borde más cercano de cualquier silueta (antialias)

    @property
    def covered(self) -> bool:
        return self.building >= 0


class Scene:
    """Los edificios ya proyectados, listos para preguntar píxel a píxel."""

    def __init__(self, params: RenderParams, buildings: list[Building], canvas: str = "3x3"):
        self.params = params
        self.canvas = canvas
        self.rise = params.camera.sc * params.camera.kz  # px de pantalla por metro de altura
        fx, fy = params.camera.forward
        # De más lejos a más cerca es el orden de pintado; de más cerca a más
        # lejos es el orden en que el primero que tapa es el que se ve.
        self.buildings = sorted(
            (
                (
                    sum(fx * x + fy * y for x, y in b.ring) / len(b.ring),
                    b,
                    [params.to_pixel_m(x, y, 0.0, canvas) for x, y in b.ring],
                )
                for b in buildings
            ),
            key=lambda item: item[0],
        )

    def predict(self, px: float, py: float) -> Prediction:
        edge = float("inf")
        found = Prediction(0.0, -1, "ground", 0.0, edge)
        for idx, (_, b, ring) in enumerate(self.buildings):
            xs = [p[0] for p in ring]
            if px < min(xs) or px > max(xs):
                continue
            hits = _column_hits(ring, px)
            lift = self.rise * b.h
            for k in range(0, len(hits) - 1, 2):
                y_near, y_far = hits[k], hits[k + 1]
                edge = min(
                    edge, abs(py - (y_near - lift)), abs(py - y_far), abs(py - (y_far - lift))
                )
                if found.building >= 0 or not (y_near - lift <= py <= y_far):
                    continue
                # La cara superior se pinta después de las paredes: manda.
                if y_near - lift <= py <= y_far - lift:
                    found = Prediction(b.h, idx, "roof", b.h, edge)
                else:
                    found = Prediction(b.h, idx, "wall", (y_near - py) / self.rise, edge)
        return Prediction(found.height, found.building, found.kind, found.seen, edge)


def _column_hits(ring: list[tuple[float, float]], x: float) -> list[float]:
    """Alturas (y) donde la vertical x corta el polígono, ya ordenadas."""
    hits: list[float] = []
    for i, (x0, y0) in enumerate(ring):
        x1, y1 = ring[(i + 1) % len(ring)]
        if (x0 > x) != (x1 > x):
            hits.append(y0 + (x - x0) * (y1 - y0) / (x1 - x0))
    return sorted(hits)
