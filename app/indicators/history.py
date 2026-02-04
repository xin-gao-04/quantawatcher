from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_history(path: str) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {"dates": {}}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return {"dates": {}}
    if not isinstance(payload, dict):
        return {"dates": {}}
    payload.setdefault("dates", {})
    return payload


def save_history(path: str, payload: Dict[str, Any]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def update_history(path: str, date_key: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = load_history(path)
    dates = payload.setdefault("dates", {})
    if not isinstance(dates, dict):
        dates = {}
        payload["dates"] = dates
    dates[date_key] = {
        item.get("symbol"): {
            "symbol": item.get("symbol"),
            "name": item.get("name"),
            "last": _safe_num(item.get("last")),
            "pct_chg": _safe_num(item.get("pct_chg")),
            "amount": _safe_num(item.get("amount")),
        }
        for item in items
        if item.get("symbol")
    }
    save_history(path, payload)
    return payload


def list_dates(payload: Dict[str, Any]) -> List[str]:
    dates = payload.get("dates", {})
    if not isinstance(dates, dict):
        return []
    return sorted(dates.keys())


def get_latest_date(payload: Dict[str, Any]) -> str:
    dates = list_dates(payload)
    return dates[-1] if dates else ""


def normalize_date(value: str | None) -> str:
    if value:
        return value
    return datetime.now().strftime("%Y-%m-%d")


def _safe_num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def get_momentum(
    payload: Dict[str, Any],
    days: int,
) -> List[Dict[str, Any]]:
    dates = list_dates(payload)
    if len(dates) <= days:
        return []
    latest_key = dates[-1]
    prev_key = dates[-(days + 1)]
    latest = payload["dates"].get(latest_key, {})
    prev = payload["dates"].get(prev_key, {})
    results: List[Dict[str, Any]] = []
    for symbol, latest_row in latest.items():
        prev_row = prev.get(symbol)
        if not prev_row:
            continue
        latest_price = latest_row.get("last")
        prev_price = prev_row.get("last")
        if latest_price is None or prev_price in (None, 0):
            continue
        momentum = (latest_price / prev_price - 1) * 100
        results.append(
            {
                "symbol": symbol,
                "name": latest_row.get("name") or "",
                "momentum": round(momentum, 2),
                "from": prev_key,
                "to": latest_key,
            }
        )
    results.sort(key=lambda item: item.get("momentum", -9999), reverse=True)
    return results
