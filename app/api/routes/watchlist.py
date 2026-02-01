from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.watchlist import load_watchlist, add_watchlist_item, save_watchlist


router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistItem(BaseModel):
    symbol: str
    name: Optional[str] = None


@router.get("")
def get_watchlist() -> dict[str, object]:
    settings = get_settings()
    return {"items": load_watchlist(settings.watchlist_path)}


@router.post("")
def add_watchlist(payload: WatchlistItem) -> dict[str, object]:
    if not payload.symbol:
        raise HTTPException(status_code=400, detail="symbol_required")
    settings = get_settings()
    items = add_watchlist_item(
        settings.watchlist_path,
        {"symbol": payload.symbol, "name": payload.name or ""},
    )
    return {"items": items}


@router.delete("/{symbol}")
def remove_watchlist(symbol: str) -> dict[str, object]:
    settings = get_settings()
    items = [i for i in load_watchlist(settings.watchlist_path) if i.get("symbol") != symbol]
    save_watchlist(settings.watchlist_path, items)
    return {"items": items}
