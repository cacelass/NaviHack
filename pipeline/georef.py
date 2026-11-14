"""Georreferencia del mapa isométrico de Vigo: (lat, lon) <-> píxel del lienzo.

El render es una cámara ortográfica: inclinación 45°, rumbo -15°, 2 px/m y el
centro del lienzo encima del origen geográfico. Con eso, un punto del suelo se
proyecta así (``pipeline/render/original/render.html``, función ``proj``)::

    px = ox + sc * (rx * x + ry * y)
    py = oy + sc * (-K * (fx * x + fy * y) - KZ * z)

donde ``x`` son metros al este del origen, ``y`` metros al norte, ``(fx, fy)``
es el vector de avance de la cámara, ``(rx, ry)`` el de la derecha en pantalla,
``K = sin(inclinación)`` y ``KZ = cos(inclinación)``. La altura ``z`` solo mueve
la fila: en una ortográfica, un edificio de 20 m ocupa el mismo ancho que su
huella.

Las constantes **no están escritas aquí**: ``pipeline/render/render-params.json``
se genera con ``python3 -m pipeline.render.params`` a partir del renderer
original y de la descarga de ortofoto. Si alguien cambia la cámara, cambia allí.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PARAMS_PATH = Path(__file__).resolve().parent / "render" / "render-params.json"
TILE = 1024


@dataclass(frozen=True)
class Camera:
    """Cámara ortográfica del renderer (`const SC`, `TILT`, `HEAD`)."""

    sc: float
    tilt_deg: float
    head_deg: float

    @property
    def k(self) -> float:
        return math.sin(math.radians(self.tilt_deg))

    @property
    def kz(self) -> float:
        return math.cos(math.radians(self.tilt_deg))

    @property
    def forward(self) -> tuple[float, float]:
        head = math.radians(self.head_deg)
        return math.sin(head), math.cos(head)

    @property
    def right(self) -> tuple[float, float]:
        head = math.radians(self.head_deg)
        return math.cos(head), -math.sin(head)


@dataclass(frozen=True)
class Geo:
    """Origen geográfico y conversión a metros del renderer (`fetch-area.mjs`)."""

    lat0: float
    lon0: float
    m_per_deg_lat: float
    m_per_deg_lon: float

    def metres(self, lat: float, lon: float) -> tuple[float, float]:
        return (lon - self.lon0) * self.m_per_deg_lon, (lat - self.lat0) * self.m_per_deg_lat

    def latlon(self, x: float, y: float) -> tuple[float, float]:
        return self.lat0 + y / self.m_per_deg_lat, self.lon0 + x / self.m_per_deg_lon


@dataclass(frozen=True)
class Canvas:
    """Lienzo en píxeles y la casilla global donde cae su esquina superior izquierda."""

    width: int
    height: int
    origin_x: float
    origin_y: float


@dataclass(frozen=True)
class RenderParams:
    camera: Camera
    geo: Geo
    canvases: dict[str, Canvas]

    def canvas(self, name: str = "3x3") -> Canvas:
        try:
            return self.canvases[name]
        except KeyError as exc:
            raise KeyError(f"lienzo desconocido: {name!r} (hay {sorted(self.canvases)})") from exc

    # ── proyección ──────────────────────────────────────────────────────────
    def to_pixel(
        self, lat: float, lon: float, z: float = 0.0, canvas: str = "3x3"
    ) -> tuple[float, float]:
        """(lat, lon, z) -> píxel del lienzo. z en metros sobre el suelo."""
        x, y = self.geo.metres(lat, lon)
        return self.to_pixel_m(x, y, z, canvas)

    def to_pixel_m(
        self, x: float, y: float, z: float = 0.0, canvas: str = "3x3"
    ) -> tuple[float, float]:
        """(x, y, z) en metros desde el origen -> píxel del lienzo."""
        c = self.canvas(canvas)
        fx, fy = self.camera.forward
        rx, ry = self.camera.right
        px = c.origin_x + self.camera.sc * (rx * x + ry * y)
        py = c.origin_y + self.camera.sc * (-self.camera.k * (fx * x + fy * y) - self.camera.kz * z)
        return px, py

    def to_latlon(
        self, px: float, py: float, z: float = 0.0, canvas: str = "3x3"
    ) -> tuple[float, float]:
        """Píxel del lienzo -> (lat, lon) del punto del suelo que hay debajo.

        Con ``z`` distinto de cero se deshace la altura: el píxel se interpreta
        como la cara superior de un edificio de esa altura.
        """
        x, y = self.to_metres(px, py, z, canvas)
        return self.geo.latlon(x, y)

    def to_metres(
        self, px: float, py: float, z: float = 0.0, canvas: str = "3x3"
    ) -> tuple[float, float]:
        c = self.canvas(canvas)
        fx, fy = self.camera.forward
        rx, ry = self.camera.right
        u = (px - c.origin_x) / self.camera.sc
        w = (py - c.origin_y) / self.camera.sc
        v = (-w - self.camera.kz * z) / self.camera.k
        return rx * u + fx * v, ry * u + fy * v

    def tile_of(self, px: float, py: float) -> tuple[int, int]:
        """Píxel -> (fila, columna) de tesela de 1024, contando desde el lienzo."""
        return int(py // TILE), int(px // TILE)


def tile_block(
    points: list[tuple[float, float]], margin: float = 512.0, tile: int = TILE
) -> tuple[int, int, int, int]:
    """Bloque mínimo de teselas que contiene los puntos con margen.

    Devuelve ``(col0, row0, col1, row1)`` inclusivos, alineados a la malla de
    teselas del lienzo (la misma del 3x3, que empieza en 0,0).
    """
    if not points:
        raise ValueError("hace falta al menos un punto")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    col0 = math.floor((min(xs) - margin) / tile)
    col1 = math.ceil((max(xs) + margin) / tile) - 1
    row0 = math.floor((min(ys) - margin) / tile)
    row1 = math.ceil((max(ys) + margin) / tile) - 1
    return col0, row0, col1, row1


def load(path: Path | None = None) -> RenderParams:
    raw = json.loads((path or PARAMS_PATH).read_text(encoding="utf-8"))
    cam = raw["camera"]
    geo = raw["geo"]
    canvases = {
        name: Canvas(int(c["width"]), int(c["height"]), float(c["origin_x"]), float(c["origin_y"]))
        for name, c in raw["canvases"].items()
    }
    return RenderParams(
        camera=Camera(float(cam["sc"]), float(cam["tilt_deg"]), float(cam["head_deg"])),
        geo=Geo(
            float(geo["lat0"]),
            float(geo["lon0"]),
            float(geo["m_per_deg_lat"]),
            float(geo["m_per_deg_lon"]),
        ),
        canvases=canvases,
    )


@lru_cache(maxsize=1)
def params() -> RenderParams:
    """Parámetros del proyecto (los del lienzo 3x3, que es el que ve la web)."""
    return load()


def to_pixel(lat: float, lon: float, z: float = 0.0) -> tuple[float, float]:
    return params().to_pixel(lat, lon, z)


def to_latlon(px: float, py: float, z: float = 0.0) -> tuple[float, float]:
    return params().to_latlon(px, py, z)
