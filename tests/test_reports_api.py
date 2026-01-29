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
    get_settings.cache_clear()

    with TestClient(app) as client:
        resp = client.post("/reports/morning-brief", json={"content": "# Draft"})
        assert resp.status_code == 200
        resp = client.get("/reports/morning-brief")
        assert resp.status_code == 200
        assert resp.json()["content"].startswith("# Draft")
        resp = client.post("/reports/morning-brief/send")
        assert resp.status_code == 200

        resp = client.post("/reports/morning-brief/data", json={"highlights": ["X"]})
        assert resp.status_code == 200
        resp = client.get("/reports/morning-brief/data")
        assert resp.status_code == 200
        assert resp.json()["data"]["highlights"] == ["X"]
