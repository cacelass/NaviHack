"""El snapshot publisher (D-01) guarda el último bueno y rechaza basura."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.snapshot import age, publish

NOW = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
GOOD = json.dumps(
    [
        {
            "nombre": "Parking Urzáiz",
            "plazaslibres": 102,
            "totalplazas": 463,
            "lat": 42.2,
            "lon": -8.7,
            "fechahora": "2026-11-14 12:55:00",
        }
    ]
).encode()


def _latest(tmp_path: Path) -> dict[str, object]:
    snap: dict[str, object] = json.loads(
        (tmp_path / "parkings" / "latest.json").read_text(encoding="utf-8")
    )
    return snap


def test_payload_bueno_escribe_snapshot_con_timestamps(tmp_path: Path) -> None:
    row = publish("parkings", GOOD, "Sat, 14 Nov 2026 11:55:04 GMT", out=tmp_path, now=NOW)
    assert row["ok"] is True
    snap = _latest(tmp_path)
    assert snap["fetched_at"] == NOW.isoformat()
    assert snap["source_timestamp"] == "2026-11-14 12:55:00"
    assert len(list((tmp_path / "parkings").glob("2026*.json"))) == 1


def test_payload_malo_no_pisa_el_ultimo_bueno(tmp_path: Path) -> None:
    publish("parkings", GOOD, None, out=tmp_path, now=NOW)
    for bad in (b"<html>502</html>", b"[]", b'[{"nombre": "x"}]', b""):
        row = publish("parkings", bad, None, out=tmp_path, now=NOW + timedelta(minutes=2))
        assert row["ok"] is False and row["error"]
    assert _latest(tmp_path)["fetched_at"] == NOW.isoformat()


def test_historico_anade_una_fila_por_pasada(tmp_path: Path) -> None:
    publish("parkings", GOOD, None, out=tmp_path, now=NOW)
    publish("parkings", b"nope", None, out=tmp_path, now=NOW)
    lines = (tmp_path / "parkings" / "history.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["ok"] for x in lines] == [True, False]


def test_agenda_usa_last_modified_como_timestamp_de_origen(tmp_path: Path) -> None:
    body = json.dumps([{"titulo": "Contemplar unha posta de sol", "permanente": True}]).encode()
    publish("agenda", body, "Sat, 14 Nov 2026 06:05:45 GMT", out=tmp_path, now=NOW)
    snap = json.loads((tmp_path / "agenda" / "latest.json").read_text(encoding="utf-8"))
    assert snap["source_timestamp"] == "Sat, 14 Nov 2026 06:05:45 GMT"


def test_age_marca_sin_datos_pasado_el_umbral(tmp_path: Path) -> None:
    publish("parkings", GOOD, None, out=tmp_path, now=NOW)
    snap = _latest(tmp_path)
    assert age(snap, NOW + timedelta(minutes=5)) == (300.0, False)
    assert age(snap, NOW + timedelta(minutes=11))[1] is True
