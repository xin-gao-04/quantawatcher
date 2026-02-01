from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def load_refresh_status(path: str) -> Optional[Dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def save_refresh_status(path: str, payload: Dict[str, Any]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def new_status(state: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "state": state,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload
