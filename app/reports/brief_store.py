from __future__ import annotations

from pathlib import Path
from typing import Optional


def load_morning_brief_draft(data_dir: str) -> Optional[str]:
    draft_path = Path(data_dir) / "morning_brief.md"
    if not draft_path.exists():
        return None
    content = draft_path.read_text(encoding="utf-8")
    return content if content.strip() else None


def save_morning_brief_draft(data_dir: str, content: str) -> None:
    draft_path = Path(data_dir) / "morning_brief.md"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(content, encoding="utf-8")
