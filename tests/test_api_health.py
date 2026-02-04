from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def test_health() -> None:
    os.environ["QW_DISABLE_SCHEDULER"] = "true"
    os.environ["QW_WATCHLIST_PATH"] = "data/watchlist.json"
    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "watchlist_count" in payload
