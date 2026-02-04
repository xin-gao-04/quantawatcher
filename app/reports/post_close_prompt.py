from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, List


def build_post_close_prompt(payload: Dict[str, Any]) -> str:
    date = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    watchlist = payload.get("watchlist", [])
    fundamentals = payload.get("fundamentals", [])
    technicals = payload.get("technicals", [])
    top_gainers = payload.get("top_gainers", [])
    top_turnover = payload.get("top_turnover", [])
    events = payload.get("events", [])
    sectors = payload.get("sectors", [])
    market = payload.get("market", {})
    risk_flags = payload.get("risk_flags", [])
    notes = payload.get("notes", [])

    prompt_payload = {
        "task": f"盘后复盘({date})",
        "output": {
            "style": "human_readable_chinese",
            "structure": ["市场概况", "机会(关注/观察)", "风险(回避/谨慎)", "明日行动建议"],
            "rules": [
                "只使用提供的数据",
                "缺数据写“依据不足”",
                "不要输出JSON，只输出自然语言要点",
                "尽量精简",
            ],
        },
        "data": {
            "market": _compact_kv(market),
            "watchlist": _compact_items(watchlist),
            "fundamentals": _compact_fundamentals(fundamentals),
            "technicals": _compact_technicals(technicals),
            "sectors": _compact_items(sectors),
            "top_gainers": _compact_items(top_gainers),
            "top_turnover": _compact_items(top_turnover),
            "events": _compact_items(events),
            "risk_flags": [n for n in risk_flags if n],
            "notes": [n for n in notes if n],
        },
    }
    return json.dumps(prompt_payload, ensure_ascii=False, separators=(",", ":"))


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _compact_kv(data: Dict[str, Any]) -> Dict[str, Any]:
    if not data:
        return {}
    result: Dict[str, Any] = {}
    for key, value in data.items():
        val = _fmt(value)
        if val != "":
            result[key] = val
    return result


def _compact_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not items:
        return []
    results: List[Dict[str, Any]] = []
    keys = ("symbol", "name", "last", "pct_chg", "amount")
    for item in items:
        compact: Dict[str, Any] = {}
        for key in keys:
            val = item.get(key)
            val = _fmt(val)
            if val != "":
                compact[key] = val
        if compact:
            results.append(compact)
    return results


def _compact_fundamentals(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not items:
        return []
    keys = (
        "symbol",
        "name",
        "pe_ttm",
        "pb",
        "roe",
        "revenue_yoy",
        "profit_yoy",
        "gross_margin",
        "net_margin",
        "debt_ratio",
    )
    results: List[Dict[str, Any]] = []
    for item in items:
        compact: Dict[str, Any] = {}
        for key in keys:
            val = _fmt(item.get(key))
            if val != "":
                compact[key] = val
        if compact:
            results.append(compact)
    return results


def _compact_technicals(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not items:
        return []
    keys = (
        "symbol",
        "name",
        "trend",
        "support",
        "resistance",
        "ma20",
        "ma60",
        "rsi14",
        "macd",
        "vol_ratio",
    )
    results: List[Dict[str, Any]] = []
    for item in items:
        compact: Dict[str, Any] = {}
        for key in keys:
            val = _fmt(item.get(key))
            if val != "":
                compact[key] = val
        if compact:
            results.append(compact)
    return results
