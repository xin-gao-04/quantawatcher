from __future__ import annotations

from app.connectors.tencent_quote import _parse_response


def test_parse_response() -> None:
    raw = 'v_sz000001="51~平安银行~000001~12.34~12.00~12.50~12.60~11.90~0~0";'
    items = _parse_response(raw)
    assert items
    assert items[0]["symbol"] == "000001"
    assert items[0]["name"] == "平安银行"
    assert items[0]["last"] == 12.34
