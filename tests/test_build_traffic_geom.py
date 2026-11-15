"""TRAFFIC-02: la traza que se manda al map-matching cabe en el servidor público y cubre el tramo."""

from scripts.build_traffic_geom import MAX_PTS, densify, length_m


def test_densify_long_section_keeps_ends_and_fits_server() -> None:
    # ~1,6 km en dos vértices, como los publica el Concello
    line = [[-8.7400, 42.2300], [-8.7200, 42.2300]]
    pts = densify(line)
    assert len(pts) == MAX_PTS
    assert pts[0] == line[0] and pts[-1] == line[-1]


def test_densify_short_section_adds_points_between_vertices() -> None:
    line = [[-8.7400, 42.2300], [-8.7380, 42.2300]]  # ~165 m
    pts = densify(line)
    assert 2 < len(pts) <= MAX_PTS
    assert abs(length_m(pts) - length_m(line)) < 1
