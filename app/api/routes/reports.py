from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.notifiers.factory import build_notifier
from app.connectors.brief_data_source import fetch_morning_brief_data
from app.connectors.akshare_snapshot import fetch_market_top_movers, fetch_watchlist_snapshot
from app.reports.brief_data import save_brief_data
from app.reports.brief_store import load_morning_brief_draft, save_morning_brief_draft
from app.reports.morning_brief import build_morning_brief
from app.reports.brief_builder import build_brief_data
from app.core.watchlist import load_watchlist


router = APIRouter(prefix="/reports", tags=["reports"])


class MorningBriefPayload(BaseModel):
    content: str


@router.get("/morning-brief")
def get_morning_brief() -> dict[str, str]:
    settings = get_settings()
    draft = load_morning_brief_draft(settings.data_dir)
    data = fetch_morning_brief_data(settings)
    brief = build_morning_brief(draft, data)
    return {"content": brief}


@router.post("/morning-brief")
def save_morning_brief(payload: MorningBriefPayload) -> dict[str, str]:
    settings = get_settings()
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="content_required")
    save_morning_brief_draft(settings.data_dir, payload.content)
    return {"status": "saved"}


@router.delete("/morning-brief")
def clear_morning_brief() -> dict[str, str]:
    settings = get_settings()
    save_morning_brief_draft(settings.data_dir, "")
    return {"status": "cleared"}


@router.post("/morning-brief/send")
def send_morning_brief() -> dict[str, str]:
    settings = get_settings()
    draft = load_morning_brief_draft(settings.data_dir)
    data = fetch_morning_brief_data(settings)
    brief = build_morning_brief(draft, data)
    notifier = build_notifier(settings)
    notifier.send(brief, severity="info", tags=["report", "morning", "manual"])
    return {"status": "sent"}


@router.get("/morning-brief/data")
def get_morning_brief_data() -> dict[str, object]:
    settings = get_settings()
    data = fetch_morning_brief_data(settings) or {}
    return {"data": data}


@router.post("/morning-brief/data")
def save_morning_brief_data(payload: dict) -> dict[str, str]:
    settings = get_settings()
    if not payload:
        raise HTTPException(status_code=400, detail="data_required")
    save_brief_data(settings.morning_brief_data_path, payload)
    return {"status": "saved"}


@router.post("/morning-brief/refresh")
def refresh_morning_brief_data() -> dict[str, str]:
    settings = get_settings()
    watchlist = load_watchlist(settings.watchlist_path)
    symbols = [item.get("symbol") for item in watchlist if item.get("symbol")]
    watchlist_snapshot = fetch_watchlist_snapshot(symbols)
    tops = fetch_market_top_movers(settings.morning_brief_top_n)
    payload = build_brief_data(
        watchlist_snapshot=watchlist_snapshot,
        top_gainers=tops.get("top_gainers", []),
        top_turnover=tops.get("top_turnover", []),
    )
    save_brief_data(settings.morning_brief_data_path, payload)
    return {"status": "refreshed"}
