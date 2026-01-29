from __future__ import annotations

import logging

import httpx

from app.core.config import Settings


logger = logging.getLogger(__name__)


class WecomNotifier:
    def __init__(self, settings: Settings) -> None:
        self._webhook_url = settings.wecom_webhook_url

    def send(self, message: str, severity: str, tags: list[str]) -> None:
        if not self._webhook_url:
            logger.warning("wecom_webhook_missing")
            return
        payload = {"msgtype": "markdown", "markdown": {"content": message}}
        response = httpx.post(self._webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
