"""Elevación MDT05 → pendiente para la opción «Easy walk» del planner (D-11).

Fuente: WCS INSPIRE de elevaciones del IGN (`servicios.idee.es/wcs-inspire/mdt`),
cobertura `Elevacion4258_5` = MDT05 (paso 5 m) en ETRS89 geográficas, que a
esta escala coincide con WGS84. Licencia **CC BY 4.0 scne.es** («© Instituto
Geográfico Nacional»). Formato `ArcGrid` (ASCII): se lee con la stdlib.

- `fetch` descarga el recorte de la zona (por defecto el núcleo navideño, el
  mismo de `scripts.buildings`) y lo guarda comprimido en
  `data/elevation/mdt05_core.asc.gz` para que el planner no dependa de la red.
- `Grid.elevation` interpola bilinealmente; `Grid.slope_pct` es la pendiente
  del terreno en un punto; `Grid.grade` la de un tramo a pie entre dos puntos
  (subida, pendiente media y máxima, muestreando cada `step_m`).
- **Sin datos no es un error:** fuera del recorte o en celdas `NODATA` todo
  devuelve `None`, y `easy_walk_factor(None)` = 1.0 (el tramo cuenta como
  llano y el planner lo informa como señal ausente, D-12).

    python -m scripts.elevation                       # núcleo navideño
    python -m scripts.elevation --bbox -8.74,42.22,-8.70,42.25

Stdlib pura.
"""

from __future__ import annotations

import argparse
import gzip
import math
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from scripts.buildings import CORE_BBOX

ROOT = Path(__file__).resolve().parent.parent
WCS_URL = "https://servicios.idee.es/wcs-inspire/mdt"
COVERAGE = "Elevacion4258_5"
OUT = ROOT / "data" / "elevation" / "mdt05_core.asc.gz"
USER_AGENT = "TinyVigo-D11/0.1 (+https://github.com/cacelass/NaviHack)"
ATTRIBUTION = "MDT05 © Instituto Geográfico Nacional (CC BY 4.0 scne.es)"
M_PER_DEG_LAT = 111_320.0
# Por encima de esto un tramo «cuesta» a pie; >12 % se evita en Easy walk.
EASY_GRADE_PCT = 6.0
STEEP_GRADE_PCT = 12.0


@dataclass(frozen=True)
class Grid:
    """Rejilla ArcGrid: `rows[0]` es la fila norte, como en el fichero."""

    ncols: int
    nrows: int
    xll: float
    yll: float
    dx: float
    dy: float
    nodata: float | None
    rows: tuple[tuple[float, ...], ...]

    def _cell(self, i: int, j: int) -> float | None:
        if not (0 <= i < self.nrows and 0 <= j < self.ncols):
            return None
        v = self.rows[i][j]
        if self.nodata is not None and v == self.nodata:
            return None
        return v

    def elevation(self, lat: float, lon: float) -> float | None:
        """Cota en metros (bilineal entre centros de celda) o None."""
        col = (lon - self.xll) / self.dx - 0.5
        row = (self.yll + self.nrows * self.dy - lat) / self.dy - 0.5
        j0, i0 = math.floor(col), math.floor(row)
        fx, fy = col - j0, row - i0
        corners = [self._cell(i0 + a, j0 + b) for a in (0, 1) for b in (0, 1)]
        if any(c is None for c in corners):
            return None
        z00, z01, z10, z11 = (c for c in corners if c is not None)
        top = z00 * (1 - fx) + z01 * fx
        bottom = z10 * (1 - fx) + z11 * fx
        return top * (1 - fy) + bottom * fy

    def slope_pct(self, lat: float, lon: float) -> float | None:
        """Pendiente del terreno (%) por diferencias centrales a ±1 celda."""
        mx = M_PER_DEG_LAT * math.cos(math.radians(lat))
        e = self.elevation(lat, lon + self.dx)
        w = self.elevation(lat, lon - self.dx)
        n = self.elevation(lat + self.dy, lon)
        s = self.elevation(lat - self.dy, lon)
        if None in (e, w, n, s):
            return None
        assert e is not None and w is not None and n is not None and s is not None
        gx = (e - w) / (2 * self.dx * mx)
        gy = (n - s) / (2 * self.dy * M_PER_DEG_LAT)
        return 100 * math.hypot(gx, gy)

    def grade(
        self, a: tuple[float, float], b: tuple[float, float], step_m: float = 10.0
    ) -> dict[str, float] | None:
        """Tramo a pie de `a` a `b` ((lat, lon)): subida, pendiente media y máxima.

        None si falta la cota en cualquier muestra: el planner no debe tratar
        un hueco de datos como llano sin decirlo.
        """
        dist = _distance_m(a, b)
        n = max(1, math.ceil(dist / step_m))
        zs: list[float] = []
        for k in range(n + 1):
            t = k / n
            z = self.elevation(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if z is None:
                return None
            zs.append(z)
        seg = dist / n if dist else 0.0
        steps = [zs[k + 1] - zs[k] for k in range(n)]
        max_pct = max((abs(d) / seg * 100 for d in steps), default=0.0) if seg else 0.0
        return {
            "distance_m": dist,
            "climb_m": sum(d for d in steps if d > 0),
            "descent_m": -sum(d for d in steps if d < 0),
            "mean_grade_pct": abs(zs[-1] - zs[0]) / dist * 100 if dist else 0.0,
            "max_grade_pct": max_pct,
        }


def easy_walk_factor(grade: dict[str, float] | None) -> float:
    """Multiplicador de coste del tramo para «Easy walk». Sin datos = 1.0."""
    if grade is None:
        return 1.0
    worst = grade["max_grade_pct"]
    if worst <= EASY_GRADE_PCT:
        return 1.0
    if worst <= STEEP_GRADE_PCT:
        return 1.0 + (worst - EASY_GRADE_PCT) / (STEEP_GRADE_PCT - EASY_GRADE_PCT)
    return 4.0


def _distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    mx = M_PER_DEG_LAT * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot((b[1] - a[1]) * mx, (b[0] - a[0]) * M_PER_DEG_LAT)


def parse_ascii_grid(text: str) -> Grid:
    """ArcGrid ASCII, también dentro de la respuesta multipart del WCS."""
    lines = text.splitlines()
    start = next(
        (k for k, line in enumerate(lines) if line.strip().lower().startswith("ncols")), None
    )
    if start is None:
        raise ValueError("La respuesta no contiene un ArcGrid (falta 'ncols').")
    header: dict[str, float] = {}
    k = start
    while k < len(lines):
        parts = lines[k].split()
        if len(parts) == 2 and parts[0][0].isalpha():
            header[parts[0].lower()] = float(parts[1])
            k += 1
        else:
            break
    ncols, nrows = int(header["ncols"]), int(header["nrows"])
    cell = header.get("cellsize")
    dx = header.get("dx", cell or 0.0)
    dy = header.get("dy", cell or 0.0)
    values: list[float] = []
    for line in lines[k:]:
        if line.startswith("--"):
            break
        values.extend(float(v) for v in line.split())
    if len(values) < ncols * nrows:
        raise ValueError(f"ArcGrid incompleto: {len(values)} de {ncols * nrows} celdas.")
    rows = tuple(tuple(values[r * ncols : (r + 1) * ncols]) for r in range(nrows))
    return Grid(
        ncols=ncols,
        nrows=nrows,
        xll=header.get("xllcorner", header.get("xllcenter", 0.0)),
        yll=header.get("yllcorner", header.get("yllcenter", 0.0)),
        dx=dx,
        dy=dy,
        nodata=header.get("nodata_value"),
        rows=rows,
    )


def coverage_url(bbox: tuple[float, float, float, float]) -> str:
    west, south, east, north = bbox
    query = urllib.parse.urlencode(
        [
            ("SERVICE", "WCS"),
            ("VERSION", "2.0.1"),
            ("REQUEST", "GetCoverage"),
            ("COVERAGEID", COVERAGE),
            ("FORMAT", "ArcGrid"),
            ("SUBSET", f"Lat({south},{north})"),
            ("SUBSET", f"Long({west},{east})"),
        ]
    )
    return f"{WCS_URL}?{query}"


def _get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 — https fijo
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
        return str(resp.read().decode("ascii", errors="replace"))


def fetch(
    bbox: tuple[float, float, float, float] = CORE_BBOX,
    get: Callable[[str], str] = _get_text,
    out: Path = OUT,
) -> Grid:
    """Descarga el recorte, lo valida y lo guarda como ArcGrid comprimido."""
    grid = parse_ascii_grid(get(coverage_url(bbox)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="ascii", newline="\n") as fh:
        fh.write(dump_ascii_grid(grid))
    return grid


def dump_ascii_grid(grid: Grid) -> str:
    head = [
        f"ncols {grid.ncols}",
        f"nrows {grid.nrows}",
        f"xllcorner {grid.xll:.12f}",
        f"yllcorner {grid.yll:.12f}",
        f"dx {grid.dx:.12f}",
        f"dy {grid.dy:.12f}",
    ]
    if grid.nodata is not None:
        head.append(f"NODATA_value {grid.nodata:g}")
    body = [" ".join(f"{v:.2f}".rstrip("0").rstrip(".") for v in row) for row in grid.rows]
    return "\n".join(head + body) + "\n"


def load(path: Path = OUT) -> Grid | None:
    """La rejilla guardada, o None si no existe: el planner sigue sin pendiente."""
    try:
        with gzip.open(path, "rt", encoding="ascii") as fh:
            return parse_ascii_grid(fh.read())
    except (OSError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bbox", help="oeste,sur,este,norte en grados WGS84")
    args = parser.parse_args(argv)
    bbox = CORE_BBOX
    if args.bbox:
        w, s, e, n = (float(v) for v in args.bbox.split(","))
        bbox = (w, s, e, n)
    grid = fetch(bbox)
    zs = [v for row in grid.rows for v in row if v != grid.nodata]
    print(
        f"{grid.ncols}x{grid.nrows} celdas, cota {min(zs):.1f}–{max(zs):.1f} m → "
        f"{OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
