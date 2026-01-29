from __future__ import annotations

from datetime import datetime
from typing import Optional


def build_morning_brief(draft: Optional[str] = None) -> str:
    if draft:
        return draft

    today = datetime.now().strftime("%Y-%m-%d")
    return "\n".join(
        [
            f"# QuantaWatcher 晨报 ({today})",
            "",
            "- 关注板块：待接入数据源",
            "- 热门板块：待接入数据源",
            "- 重点标的：待接入数据源",
            "- 风险提示：待接入数据源",
        ]
    )
