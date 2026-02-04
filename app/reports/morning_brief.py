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
    risk_notes = data.get("risk_notes", [])
    notes = data.get("notes", [])
    top_gainers = data.get("top_gainers", [])
    top_turnover = data.get("top_turnover", [])
    rankings = data.get("rankings", {}) or {}
    indicators = data.get("indicators", {}) or {}
    momentum = indicators.get("momentum", {}) if isinstance(indicators, dict) else {}

    lines = [f"# QuantaWatcher 晨报 ({today})", ""]
    lines += ["## 今日要点"] + (["- 暂无"] if not highlights else [f"- {item}" for item in highlights])
    lines += ["", "## 关注板块"] + (["- 暂无"] if not sectors else [f"- {item}" for item in sectors])
    lines += ["", "## 重点标的"] + (["- 暂无"] if not symbols else [f"- {item}" for item in symbols])
    risk_lines = risk_notes or risks
    lines += ["", "## 风险提示"] + (["- 暂无"] if not risk_lines else [f"- {item}" for item in risk_lines])
    lines += ["", "## 备注"] + (["- 暂无"] if not notes else [f"- {item}" for item in notes])
    rank_gainers = rankings.get("top_gainers") or top_gainers
    rank_turnover = rankings.get("top_turnover") or top_turnover
    rank_losers = rankings.get("top_losers") or []
    if rank_gainers:
        lines += ["", "## 涨幅榜"] + [_format_item(item) for item in rank_gainers]
    if rank_losers:
        lines += ["", "## 跌幅榜"] + [_format_item(item) for item in rank_losers]
    if rank_turnover:
        lines += ["", "## 成交额榜"] + [_format_item(item) for item in rank_turnover]
    if isinstance(momentum, dict) and momentum:
        lines += ["", "## 动量排行"]
        for label, items in momentum.items():
            if not items:
                continue
            lines.append(f"### {label}")
            for item in items:
                lines.append(_format_momentum(item))
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


def _format_momentum(item: Dict[str, Any]) -> str:
    symbol = item.get("symbol") or "-"
    name = item.get("name") or ""
    momentum = item.get("momentum")
    span_from = item.get("from") or ""
    span_to = item.get("to") or ""
    parts = [symbol, name]
    if momentum is not None:
        parts.append(f"{momentum:.2f}%")
    if span_from and span_to:
        parts.append(f"({span_from}->{span_to})")
    return "- " + " ".join([p for p in parts if p])
