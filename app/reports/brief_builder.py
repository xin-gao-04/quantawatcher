from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def build_brief_data(
    watchlist_snapshot: List[Dict[str, Any]],
    top_gainers: List[Dict[str, Any]],
    top_turnover: List[Dict[str, Any]],
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

    return {
        "highlights": highlights,
        "sectors": sectors,
        "symbols": symbols,
        "risks": risks,
        "notes": notes,
        "watchlist": watchlist_snapshot,
        "top_gainers": top_gainers,
        "top_turnover": top_turnover,
    }


def _format_symbol(item: Dict[str, Any]) -> str:
    symbol = item.get("symbol") or "-"
    name = item.get("name") or ""
    pct = item.get("pct_chg")
    if pct is None:
        return f"{symbol} {name}".strip()
    return f"{symbol} {name} {pct:.2f}%".strip()
