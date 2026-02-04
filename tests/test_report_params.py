from __future__ import annotations

import os

from app.core.config import get_settings
from app.core.report_params import load_report_params, save_report_params


def test_report_params_roundtrip(tmp_path) -> None:
    os.environ["QW_REPORT_PARAMS_PATH"] = str(tmp_path / "params.json")
    os.environ["QW_POST_CLOSE_HOUR"] = "15"
    os.environ["QW_POST_CLOSE_MINUTE"] = "30"
    get_settings.cache_clear()
    settings = get_settings()

    params = load_report_params(settings.report_params_path, settings)
    assert params["post_close_hour"] == 15
    assert params["post_close_minute"] == 30

    updated = save_report_params(
        settings.report_params_path,
        {"momentum_days": [3, 5, 5], "abnormal_pct": 4.5},
        settings,
    )
    assert updated["momentum_days"] == [3, 5]
    assert updated["abnormal_pct"] == 4.5
