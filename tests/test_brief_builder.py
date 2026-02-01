from __future__ import annotations

from app.reports.brief_builder import build_brief_data


def test_build_brief_data() -> None:
    payload = build_brief_data(
        watchlist_snapshot=[
            {"symbol": "000001", "name": "平安银行", "pct_chg": 1.2}
        ],
        top_gainers=[
            {"symbol": "600519", "name": "贵州茅台", "pct_chg": 2.3}
        ],
        top_turnover=[
            {"symbol": "000002", "name": "万科A", "pct_chg": -0.5}
        ],
    )
    assert "highlights" in payload
    assert "symbols" in payload
    assert "watchlist" in payload
