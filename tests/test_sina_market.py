from __future__ import annotations

from app.connectors.sina_market import _parse_sina_text


def test_parse_sina_text() -> None:
    raw = '[{symbol:"sh600000",code:"600000",name:"浦发银行",trade:"11.99",changepercent:"0.33",amount:"12345"}]'
    items = _parse_sina_text(raw)
    assert items
    assert items[0]["symbol"] == "sh600000"
    assert items[0]["code"] == "600000"
