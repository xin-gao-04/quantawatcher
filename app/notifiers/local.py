from __future__ import annotations

from datetime import datetime
from pathlib import Path


class LocalNotifier:
    def __init__(self, outbox_dir: str) -> None:
        self._outbox_dir = Path(outbox_dir)

    def send(self, message: str, severity: str, tags: list[str]) -> None:
        self._outbox_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{severity}.md"
        (self._outbox_dir / filename).write_text(message, encoding="utf-8")
