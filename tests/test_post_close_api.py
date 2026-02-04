from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def test_post_close_refresh_flow(tmp_path, monkeypatch) -> None:
    os.environ["QW_DISABLE_SCHEDULER"] = "true"
    os.environ["QW_DATA_DIR"] = str(tmp_path)
    os.environ["QW_NOTIFIER_KIND"] = "local"
    os.environ["QW_OUTBOX_DIR"] = str(tmp_path / "outbox")
    os.environ["QW_POST_CLOSE_DATA_PATH"] = str(tmp_path / "post_close.json")
    os.environ["QW_POST_CLOSE_REFRESH_STATUS_PATH"] = str(tmp_path / "post_close_status.json")
    os.environ["QW_WATCHLIST_PATH"] = str(tmp_path / "watchlist.json")
    os.environ["QW_REPORT_PARAMS_PATH"] = str(tmp_path / "params.json")
    os.environ["QW_WATCHLIST_HISTORY_PATH"] = str(tmp_path / "history.json")
    get_settings.cache_clear()

    import app.api.routes.reports as reports_module

    def fake_fetch_market_snapshot(symbols, top_n: int):
        return {
            "watchlist": [{"symbol": "000001", "name": "平安银行", "pct_chg": 1.0, "amount": 100}],
            "top_gainers": [],
            "top_turnover": [],
        }

    monkeypatch.setattr(reports_module, "fetch_market_snapshot", fake_fetch_market_snapshot)

    with TestClient(app) as client:
        resp = client.post("/reports/post-close/refresh")
        assert resp.status_code == 200
        status = client.get("/reports/post-close/refresh/status")
        assert status.status_code == 200
        data_resp = client.get("/reports/post-close/data")
        assert data_resp.status_code == 200
        report_resp = client.get("/reports/post-close")
        assert report_resp.status_code == 200
