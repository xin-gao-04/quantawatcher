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

    lines = [f"# QuantaWatcher 晨报 ({today})", ""]
    lines += ["## 今日要点"] + (["- 暂无"] if not highlights else [f"- {item}" for item in highlights])
    lines += ["", "## 关注板块"] + (["- 暂无"] if not sectors else [f"- {item}" for item in sectors])
    lines += ["", "## 重点标的"] + (["- 暂无"] if not symbols else [f"- {item}" for item in symbols])
    lines += ["", "## 风险提示"] + (["- 暂无"] if not risks else [f"- {item}" for item in risks])
    lines += ["", "## 备注"] + (["- 暂无"] if not notes else [f"- {item}" for item in notes])
    return "\n".join(lines)
