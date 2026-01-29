from __future__ import annotations

from app.connectors.brief_data_source import fetch_morning_brief_data
from app.core.config import Settings
from app.reports.brief_data import save_brief_data


def test_fetch_morning_brief_data(tmp_path) -> None:
    path = tmp_path / "brief.json"
    payload = {"highlights": ["X"]}
    save_brief_data(str(path), payload)

    settings = Settings(morning_brief_data_path=str(path))
    data = fetch_morning_brief_data(settings)
    assert data == payload
