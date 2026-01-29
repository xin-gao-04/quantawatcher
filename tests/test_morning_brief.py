from __future__ import annotations

from app.reports.morning_brief import build_morning_brief


def test_morning_brief_has_header() -> None:
    brief = build_morning_brief()
    assert brief.startswith("# QuantaWatcher 晨报")


def test_morning_brief_with_data() -> None:
    data = {
        "highlights": ["A"],
        "sectors": ["S1"],
        "symbols": ["X1"],
        "risks": ["R1"],
        "notes": ["N1"],
    }
    brief = build_morning_brief(None, data)
    assert "- A" in brief
    assert "- S1" in brief
    assert "- X1" in brief
    assert "- R1" in brief
    assert "- N1" in brief
