from __future__ import annotations

from app.reports.brief_store import load_morning_brief_draft, save_morning_brief_draft


def test_save_and_load_brief(tmp_path) -> None:
    data_dir = str(tmp_path)
    content = "# Test Brief"
    save_morning_brief_draft(data_dir, content)
    loaded = load_morning_brief_draft(data_dir)
    assert loaded == content
