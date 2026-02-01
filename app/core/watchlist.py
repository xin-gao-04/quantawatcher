from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_watchlist(path: str) -> List[Dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    return json.loads(file_path.read_text(encoding="utf-8"))


def save_watchlist(path: str, items: List[Dict[str, Any]]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def add_watchlist_item(path: str, item: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = load_watchlist(path)
    symbols = {i.get("symbol") for i in items}
    if item.get("symbol") not in symbols:
        items.append(item)
    save_watchlist(path, items)
    return items
