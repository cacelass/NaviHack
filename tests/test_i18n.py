"""Textos de la interfaz (I18N-01): mismos textos y mismos huecos en gl/es/en/pt."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

I18N = Path(__file__).resolve().parent.parent / "i18n"
LANGS = ("gl", "es", "en", "pt")
HOLE = re.compile(r"\{(\w+)\}")


def catalog(lang: str) -> dict[str, str]:
    data: dict[str, str] = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
    return data


def test_los_tres_idiomas_tienen_las_mismas_claves() -> None:
    es = set(catalog("es"))
    for lang in ("gl", "en", "pt"):
        keys = set(catalog(lang))
        assert keys == es, f"{lang}: faltan {sorted(es - keys)} · sobran {sorted(keys - es)}"


@pytest.mark.parametrize("lang", ["gl", "en", "pt"])
def test_mismos_huecos_que_en_espanol(lang: str) -> None:
    es, other = catalog("es"), catalog(lang)
    for key, text in es.items():
        assert set(HOLE.findall(other[key])) == set(HOLE.findall(text)), key


@pytest.mark.parametrize("lang", LANGS)
def test_ningun_texto_vacio_ni_con_guion_largo(lang: str) -> None:
    for key, text in catalog(lang).items():
        assert text.strip(), f"{lang}:{key} vacío"
        assert "—" not in text, f"{lang}:{key} usa guion largo (regla de prosa de la UI)"


def test_el_gallego_no_es_una_copia_del_espanol() -> None:
    # Hay textos que se escriben igual en los dos idiomas («Buscar un punto»),
    # pero si la mayoría coincide es que el catálogo no se tradujo.
    es, gl = catalog("es"), catalog("gl")
    same = [k for k in es if es[k] == gl[k]]
    assert len(same) / len(es) < 0.3, f"demasiados textos iguales al español: {same}"


def test_el_helper_lee_los_tres_catalogos() -> None:
    src = (I18N / "i18n.ts").read_text(encoding="utf-8")
    for lang in LANGS:
        assert f'from "./{lang}.json"' in src


def test_el_portugues_no_es_una_copia_del_espanol() -> None:
    es, pt = catalog("es"), catalog("pt")
    same = [k for k in es if es[k] == pt[k]]
    assert len(same) / len(es) < 0.3, f"demasiados textos iguales al español: {same}"
