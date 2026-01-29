from __future__ import annotations

from app.core.config import Settings
from app.notifiers.local import LocalNotifier
from app.notifiers.wecom import WecomNotifier


def build_notifier(settings: Settings):
    kind = settings.notifier_kind.lower()
    if kind == "wecom":
        return WecomNotifier(settings)
    if kind == "local":
        return LocalNotifier(settings.outbox_dir)
    raise ValueError(f"Unknown notifier kind: {settings.notifier_kind}")
