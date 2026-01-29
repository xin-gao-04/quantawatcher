from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import Settings
from app.reports.brief_data import load_brief_data


def fetch_morning_brief_data(settings: Settings) -> Optional[Dict[str, Any]]:
    return load_brief_data(settings.morning_brief_data_path)
