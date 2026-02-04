from __future__ import annotations

from app.reports.post_close_prompt import build_post_close_prompt


def test_prompt_compact_output() -> None:
    prompt = build_post_close_prompt({"date": "2026-01-01", "watchlist": [{"symbol": "000001"}]})
    assert "盘后复盘" in prompt
    assert "\"watchlist\"" in prompt
