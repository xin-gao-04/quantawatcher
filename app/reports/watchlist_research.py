from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.core.config import Settings


def load_research_data(settings: Settings) -> Dict[str, Any]:
    fundamentals = _load_json(settings.watchlist_fundamentals_path)
    technicals = _load_json(settings.watchlist_technicals_path)
    return {
        "fundamentals": fundamentals.get("items", []),
        "technicals": technicals.get("items", []),
    }


def save_research_data(settings: Settings, fundamentals: Dict[str, Any], technicals: Dict[str, Any]) -> None:
    _save_json(settings.watchlist_fundamentals_path, fundamentals)
    _save_json(settings.watchlist_technicals_path, technicals)


def _load_json(path: str) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text(encoding="utf-8"))


def _save_json(path: str, payload: Dict[str, Any]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
