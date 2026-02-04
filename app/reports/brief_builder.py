from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.indicators.history import get_latest_date
from app.indicators.summary import compute_momentum_indicators, compute_rankings, compute_risk_notes


def build_brief_data(
    watchlist_snapshot: List[Dict[str, Any]],
    top_gainers: List[Dict[str, Any]],
    top_turnover: List[Dict[str, Any]],
    history_payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    highlights = [f"{today} 晨报自动生成"]
    sectors: List[str] = []
    symbols = [_format_symbol(item) for item in watchlist_snapshot[:10]]
    risks: List[str] = []
    notes: List[str] = []

    top_gainers_lines = [_format_symbol(item) for item in top_gainers]
    top_turnover_lines = [_format_symbol(item) for item in top_turnover]

    if top_gainers_lines:
        highlights.append("涨幅榜：" + "，".join(top_gainers_lines[:5]))
    if top_turnover_lines:
        highlights.append("成交额榜：" + "，".join(top_turnover_lines[:5]))

    rankings = compute_rankings(watchlist_snapshot, len(top_gainers) or 10)
    risk_notes = compute_risk_notes(watchlist_snapshot)
    indicators: Dict[str, Any] = {}
    if history_payload and params:
        momentum_days = params.get("momentum_days", [5, 20])
        top_n = params.get("post_close_top_n", len(top_gainers) or 10)
        indicators["momentum"] = compute_momentum_indicators(history_payload, momentum_days, top_n)
        indicators["history_latest_date"] = get_latest_date(history_payload)

    return {
        "highlights": highlights,
        "sectors": sectors,
        "symbols": symbols,
        "risks": risks,
        "risk_notes": risk_notes,
        "notes": notes,
        "watchlist": watchlist_snapshot,
        "top_gainers": top_gainers,
        "top_turnover": top_turnover,
        "rankings": rankings,
        "indicators": indicators,
    }


def _format_symbol(item: Dict[str, Any]) -> str:
    symbol = item.get("symbol") or "-"
    name = item.get("name") or ""
    pct = item.get("pct_chg")
    if pct is None:
        return f"{symbol} {name}".strip()
    return f"{symbol} {name} {pct:.2f}%".strip()
