from __future__ import annotations

from app.reports.post_close_report import build_post_close_report


def test_post_close_report_render() -> None:
    payload = {
        "date": "2026-02-04",
        "watchlist": [{"symbol": "000001", "name": "平安银行", "pct_chg": 1.2, "amount": 100}],
        "rankings": {
            "top_gainers": [{"symbol": "000001", "name": "平安银行", "pct_chg": 1.2}],
            "top_losers": [],
            "top_turnover": [{"symbol": "000001", "name": "平安银行", "amount": 100}],
        },
        "abnormal_moves": [{"symbol": "000001", "name": "平安银行", "pct_chg": 5.1}],
        "suggestions": {
            "strong": [{"symbol": "000001", "name": "平安银行", "pct_chg": 1.2}],
            "weak": [],
            "neutral": [],
        },
        "risk_notes": ["watchlist 整体波动可控"],
        "indicators": {"momentum": {"5d": [{"symbol": "000001", "name": "平安银行", "momentum": 2.5}]}},
        "notes": ["source: mock"],
    }
    report = build_post_close_report(payload)
    assert "盘后复盘" in report
    assert "涨幅榜" in report
    assert "异常波动" in report
