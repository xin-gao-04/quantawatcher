from __future__ import annotations

from app.reports.morning_brief import build_morning_brief


def test_morning_brief_has_header() -> None:
    brief = build_morning_brief()
    assert brief.startswith("# QuantaWatcher 晨报")
