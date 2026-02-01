from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def test_watchlist_add_get(tmp_path) -> None:
    os.environ["QW_DISABLE_SCHEDULER"] = "true"
    os.environ["QW_WATCHLIST_PATH"] = str(tmp_path / "watchlist.json")
    get_settings.cache_clear()
    with TestClient(app) as client:
        resp = client.post("/watchlist", json={"symbol": "000063", "name": "中兴通讯"})
        assert resp.status_code == 200
        resp = client.get("/watchlist")
        assert resp.status_code == 200
        assert resp.json()["items"][0]["symbol"] == "000063"
