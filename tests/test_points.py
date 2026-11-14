"""Tests para app.points."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase, main

from app.points import count_by_type, load_points, summary


class TestLoadPoints(TestCase):
    """Carga de puntos desde data/points.json."""

    def test_load_points_returns_list(self) -> None:
        pts = load_points()
        self.assertIsInstance(pts, list)
        self.assertGreater(len(pts), 0)

    def test_load_points_has_expected_keys(self) -> None:
        pts = load_points()
        # Cada punto debe tener al menos 'id' y 'name'
        for p in pts:
            self.assertIn("id", p)
            self.assertIn("name", p)

    def test_load_points_missing_file(self) -> None:
        from app import points as points_mod

        original = points_mod._points_path

        def fake_path() -> Path:
            return Path("/tmp/definitivamente_no_existe_12345.json")

        points_mod._points_path = fake_path
        try:
            with self.assertRaises(FileNotFoundError):
                load_points()
        finally:
            points_mod._points_path = original

    def test_load_points_invalid_structure(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
            json.dump({"not_points": []}, tmp)
            tmp_path = Path(tmp.name)

        from app import points as points_mod

        original = points_mod._points_path
        points_mod._points_path = lambda: tmp_path
        try:
            with self.assertRaises(ValueError):
                load_points()
        finally:
            points_mod._points_path = original
            tmp_path.unlink()


class TestSummary(TestCase):
    """Resumen de puntos."""

    def test_summary_returns_dicts(self) -> None:
        pts = load_points()
        s = summary(pts, lang="es")
        self.assertIsInstance(s, list)
        if s:
            self.assertIn("id", s[0])
            self.assertIn("name", s[0])
            self.assertIn("type", s[0])
            self.assertIn("status", s[0])

    def test_summary_language(self) -> None:
        pts = load_points()
        gl = summary(pts, lang="gl")
        es = summary(pts, lang="es")
        # Los nombres en gl y es pueden ser diferentes
        self.assertIsInstance(gl, list)
        self.assertIsInstance(es, list)
        self.assertEqual(len(gl), len(es))

    def test_summary_with_none_loads_from_disk(self) -> None:
        s = summary(None, lang="es")
        self.assertIsInstance(s, list)
        self.assertGreater(len(s), 0)


class TestCountByType(TestCase):
    """Conteo por tipo."""

    def test_count_by_type_returns_dict(self) -> None:
        pts = load_points()
        counts = count_by_type(pts)
        self.assertIsInstance(counts, dict)

    def test_count_by_type_total(self) -> None:
        pts = load_points()
        counts = count_by_type(pts)
        total = sum(counts.values())
        self.assertEqual(total, len(pts))


if __name__ == "__main__":
    main()
