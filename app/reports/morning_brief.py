from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def build_morning_brief(
    draft: Optional[str] = None, data: Optional[Dict[str, Any]] = None
) -> str:
    if draft:
        return draft

    today = datetime.now().strftime("%Y-%m-%d")
    data = data or {}
    highlights = data.get("highlights", [])
    sectors = data.get("sectors", [])
    symbols = data.get("symbols", [])
    risks = data.get("risks", [])
    notes = data.get("notes", [])
    top_gainers = data.get("top_gainers", [])
    top_turnover = data.get("top_turnover", [])

    lines = [f"# QuantaWatcher 晨报 ({today})", ""]
    lines += ["## 今日要点"] + (["- 暂无"] if not highlights else [f"- {item}" for item in highlights])
    lines += ["", "## 关注板块"] + (["- 暂无"] if not sectors else [f"- {item}" for item in sectors])
    lines += ["", "## 重点标的"] + (["- 暂无"] if not symbols else [f"- {item}" for item in symbols])
    lines += ["", "## 风险提示"] + (["- 暂无"] if not risks else [f"- {item}" for item in risks])
    lines += ["", "## 备注"] + (["- 暂无"] if not notes else [f"- {item}" for item in notes])
    if top_gainers:
        lines += ["", "## 涨幅榜"] + [_format_item(item) for item in top_gainers]
    if top_turnover:
        lines += ["", "## 成交额榜"] + [_format_item(item) for item in top_turnover]
    return "\n".join(lines)


def _format_item(item: Dict[str, Any]) -> str:
    symbol = item.get("symbol") or "-"
    name = item.get("name") or ""
    pct = item.get("pct_chg")
    amount = item.get("amount")
    parts = [symbol, name]
    if pct is not None:
        parts.append(f"{pct:.2f}%")
    if amount is not None:
        parts.append(f"成交额:{amount}")
    return "- " + " ".join([p for p in parts if p])
