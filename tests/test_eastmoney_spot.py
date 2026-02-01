from __future__ import annotations

from app.connectors.eastmoney_spot import normalize_eastmoney_rows, _cookie_from_headers


def test_normalize_eastmoney_rows() -> None:
    rows = [
        {"f12": "000001", "f14": "平安银行", "f2": 12.3, "f3": 1.2, "f6": 123456.0},
        {"f12": "", "f14": "无效", "f2": None},
    ]
    items = normalize_eastmoney_rows(rows)
    assert items
    assert items[0]["symbol"] == "000001"
    assert items[0]["name"] == "平安银行"
    assert items[0]["last"] == 12.3


def test_cookie_from_headers() -> None:
    values = [
        "ab=1; Path=/; HttpOnly",
        "cid=xyz; Path=/",
    ]
    cookie = _cookie_from_headers(values)
    assert "ab=1" in cookie
    assert "cid=xyz" in cookie
