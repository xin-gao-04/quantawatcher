from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.core.config import Settings
from app.reports.brief_data import load_brief_data
from app.reports.watchlist_research import load_research_data


def build_post_close_payload(settings: Settings) -> Dict[str, Any]:
    brief = load_brief_data(settings.morning_brief_data_path) or {}
    research = load_research_data(settings)
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "horizon": "短线(1-5天) / 中线(1-4周)",
        "market": {
            "index_summary": "NA",
            "liquidity": "NA",
            "risk_on_off": "NA",
        },
        "watchlist": brief.get("watchlist", []),
        "fundamentals": research.get("fundamentals", []),
        "technicals": research.get("technicals", []),
        "top_gainers": brief.get("top_gainers", []),
        "top_turnover": brief.get("top_turnover", []),
        "sectors": brief.get("sectors", []),
        "events": brief.get("events", []),
        "risk_flags": brief.get("risk_flags", []),
        "constraints": [
            "仅A股",
            "单票不超20%仓位",
            "控制回撤",
        ],
        "notes": brief.get("notes", []),
    }
