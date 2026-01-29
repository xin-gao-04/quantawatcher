from __future__ import annotations

from app.reports.brief_data import load_brief_data, save_brief_data


def test_save_and_load_brief_data(tmp_path) -> None:
    path = str(tmp_path / "brief.json")
    payload = {"highlights": ["X"]}
    save_brief_data(path, payload)
    loaded = load_brief_data(path)
    assert loaded == payload
