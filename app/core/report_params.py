from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import Settings


DEFAULT_MOMENTUM_DAYS = [5, 20]


def default_params(settings: Settings) -> Dict[str, Any]:
    return {
        "momentum_days": DEFAULT_MOMENTUM_DAYS,
        "abnormal_pct": 3.0,
        "strong_pct": 2.0,
        "post_close_top_n": settings.morning_brief_top_n,
        "post_close_hour": settings.post_close_hour,
        "post_close_minute": settings.post_close_minute,
        "post_close_refresh_hour": settings.post_close_refresh_hour,
        "post_close_refresh_minute": settings.post_close_refresh_minute,
    }


def load_report_params(path: str, settings: Settings) -> Dict[str, Any]:
    file_path = Path(path)
    defaults = default_params(settings)
    if not file_path.exists():
        return defaults
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return defaults
    if not isinstance(raw, dict):
        return defaults
    merged = {**defaults, **raw}
    merged["momentum_days"] = _normalize_days(merged.get("momentum_days"), defaults["momentum_days"])
    return merged


def save_report_params(path: str, payload: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
    params = load_report_params(path, settings)
    for key, value in payload.items():
        params[key] = value
    params["momentum_days"] = _normalize_days(params.get("momentum_days"), DEFAULT_MOMENTUM_DAYS)
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
    return params


def _normalize_days(value: Any, fallback: List[int]) -> List[int]:
    if isinstance(value, list):
        items: List[int] = []
        for item in value:
            try:
                num = int(item)
            except Exception:
                continue
            if num > 0:
                items.append(num)
        if items:
            return sorted(set(items))
    return fallback
