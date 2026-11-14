"""La eval del backlog admite varias features en curso solo con GEAS (un ticket por actor)."""

from __future__ import annotations

from agents.evals.runner import _problemas_backlog

FEATS = [
    {
        "id": "A",
        "title": "a",
        "description": "d",
        "status": "in_progress",
        "acceptance_criteria": ["x"],
        "depends_on": [],
    },
    {
        "id": "B",
        "title": "b",
        "description": "d",
        "status": "in_progress",
        "acceptance_criteria": ["x"],
        "depends_on": [],
    },
]


def test_local_dos_en_curso_es_un_problema() -> None:
    assert any("in_progress a la vez" in p for p in _problemas_backlog(FEATS))


def test_geas_dos_en_curso_de_actores_distintos_es_normal() -> None:
    assert _problemas_backlog(FEATS, multi_actor=True) == []
