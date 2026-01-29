from __future__ import annotations

from app.core.watchlist import load_watchlist, save_watchlist


def test_save_and_load_watchlist(tmp_path) -> None:
    path = str(tmp_path / "watchlist.json")
    items = [{"symbol": "000001", "name": "平安银行"}]
    save_watchlist(path, items)
    loaded = load_watchlist(path)
    assert loaded == items
