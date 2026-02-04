from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def build_post_close_report(data: Dict[str, Any]) -> str:
    today = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    rankings = data.get("rankings", {}) or {}
    abnormal = data.get("abnormal_moves", []) or []
    suggestions = data.get("suggestions", {}) or {}
    risk_notes = data.get("risk_notes", []) or []
    notes = data.get("notes", []) or []
    momentum = (data.get("indicators", {}) or {}).get("momentum", {}) or {}

    lines: List[str] = [f"# QuantaWatcher 盘后复盘 ({today})", ""]

    lines += ["## 盘后摘要"]
    lines += ["- 生成时间：" + datetime.now().strftime("%H:%M:%S")]
    lines += ["- watchlist 数量：" + str(len(data.get("watchlist", []) or []))]

    lines += ["", "## 风险提示"]
    lines += ["- 暂无"] if not risk_notes else [f"- {item}" for item in risk_notes]

    lines += ["", "## 涨幅榜"]
    lines += _format_table(rankings.get("top_gainers", []))

    lines += ["", "## 跌幅榜"]
    lines += _format_table(rankings.get("top_losers", []))

    lines += ["", "## 成交额榜"]
    lines += _format_table(rankings.get("top_turnover", []))

    lines += ["", "## 异常波动"]
    lines += _format_table(abnormal) if abnormal else ["- 暂无"]

    lines += ["", "## 复盘建议"]
    lines += ["- 关注"] + _format_table(suggestions.get("strong", []))
    lines += ["- 回避"] + _format_table(suggestions.get("weak", []))
    lines += ["- 观察"] + _format_table(suggestions.get("neutral", []))

    if momentum:
        lines += ["", "## 动量排行"]
        for label, items in momentum.items():
            if not items:
                continue
            lines.append(f"### {label}")
            lines += _format_table(items, key="momentum", suffix="%")

    if notes:
        lines += ["", "## 备注"] + [f"- {item}" for item in notes]

    return "\n".join(lines)


def _format_table(items: List[Dict[str, Any]], key: str = "pct_chg", suffix: str = "%") -> List[str]:
    if not items:
        return ["- 暂无"]
    lines = []
    for item in items[:10]:
        symbol = item.get("symbol") or "-"
        name = item.get("name") or ""
        value = item.get(key)
        if value is None:
            value_str = "-"
        else:
            try:
                value_str = f"{float(value):.2f}{suffix}"
            except Exception:
                value_str = str(value)
        amount = item.get("amount")
        amount_str = f" 成交额:{amount}" if amount is not None else ""
        lines.append(f"- {symbol} {name} {value_str}{amount_str}".strip())
    return lines
