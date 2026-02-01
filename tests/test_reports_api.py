from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def test_morning_brief_roundtrip(tmp_path) -> None:
    os.environ["QW_DISABLE_SCHEDULER"] = "true"
    os.environ["QW_DATA_DIR"] = str(tmp_path)
    os.environ["QW_NOTIFIER_KIND"] = "local"
    os.environ["QW_OUTBOX_DIR"] = str(tmp_path / "outbox")
    os.environ["QW_MORNING_BRIEF_DATA_PATH"] = str(tmp_path / "brief.json")
    os.environ["QW_WATCHLIST_PATH"] = str(tmp_path / "watchlist.json")
    os.environ["QW_ENABLE_MORNING_BRIEF_DRAFT"] = "true"
    get_settings.cache_clear()

    with TestClient(app) as client:
        resp = client.post("/reports/morning-brief", json={"content": "# Draft"})
        assert resp.status_code == 200
        resp = client.get("/reports/morning-brief")
        assert resp.status_code == 200
        assert resp.json()["content"].startswith("# Draft")
        resp = client.delete("/reports/morning-brief")
        assert resp.status_code == 200
        resp = client.post("/reports/morning-brief/send")
        assert resp.status_code == 200

        resp = client.post("/reports/morning-brief/data", json={"highlights": ["X"]})
        assert resp.status_code == 200
        resp = client.get("/reports/morning-brief/data")
        assert resp.status_code == 200
        assert resp.json()["data"]["highlights"] == ["X"]


def test_morning_brief_refresh(tmp_path, monkeypatch) -> None:
    os.environ["QW_DISABLE_SCHEDULER"] = "true"
    os.environ["QW_DATA_DIR"] = str(tmp_path)
    os.environ["QW_NOTIFIER_KIND"] = "local"
    os.environ["QW_OUTBOX_DIR"] = str(tmp_path / "outbox")
    os.environ["QW_MORNING_BRIEF_DATA_PATH"] = str(tmp_path / "brief.json")
    os.environ["QW_WATCHLIST_PATH"] = str(tmp_path / "watchlist.json")
    get_settings.cache_clear()

    import app.api.routes.reports as reports_module

    def fake_fetch_market_snapshot(symbols, top_n: int):
        return {
            "watchlist": [{"symbol": "000001", "name": "平安银行", "pct_chg": 1.0}],
            "top_gainers": [],
            "top_turnover": [],
        }

    monkeypatch.setattr(reports_module, "fetch_market_snapshot", fake_fetch_market_snapshot)

    with TestClient(app) as client:
        resp = client.post("/reports/morning-brief/refresh")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("queued", "cached")
        status = client.get("/reports/morning-brief/refresh/status")
        assert status.status_code == 200
        resp = client.get("/reports/morning-brief/data")
        assert resp.status_code == 200
