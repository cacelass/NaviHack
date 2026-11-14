"""Renfe en vivo (X-03): retrasos de los trenes de Vigo, ignorando un feed viejo."""

from __future__ import annotations

from scripts.renfe_live import delays

FEED = {
    "header": {"timestamp": "1000"},
    "entity": [
        {"tripUpdate": {"trip": {"tripId": "VIGO1"}, "delay": 1200}},
        {"tripUpdate": {"trip": {"tripId": "OTRO"}, "delay": 60}},
        {"tripUpdate": {"trip": {"tripId": "VIGO2"}}},
    ],
}


def test_retrasos_solo_de_trenes_de_vigo_en_minutos() -> None:
    res = delays(FEED, {"VIGO1", "VIGO2"}, now_s=1015)
    assert res == {"fresh": True, "age_s": 15, "delays": {"VIGO1": 20}}


def test_feed_viejo_no_da_retrasos() -> None:
    res = delays(FEED, {"VIGO1"}, now_s=1000 + 3600)
    assert res["fresh"] is False and res["delays"] == {}
