from __future__ import annotations

from pathlib import Path

from app.notifiers.local import LocalNotifier


def test_local_notifier_writes_outbox(tmp_path: Path) -> None:
    notifier = LocalNotifier(str(tmp_path))
    notifier.send("hello", severity="info", tags=["test"])
    files = list(tmp_path.glob("*.md"))
    assert files
