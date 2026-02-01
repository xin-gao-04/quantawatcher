from __future__ import annotations

from app.reports.post_close_prompt import build_post_close_prompt


def test_prompt_schema_fields() -> None:
    prompt = build_post_close_prompt({})
    assert "data_quality_score" in prompt
    assert "\"evidence\"" in prompt
