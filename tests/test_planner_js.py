"""PLANNER-01: los tests del planificador JS (tests/js/planner.test.cjs) corren con Node."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="sin Node")
def test_planificador_js() -> None:
    proc = subprocess.run(
        ["node", str(ROOT / "tests" / "js" / "planner.test.cjs")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
