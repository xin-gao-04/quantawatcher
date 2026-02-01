from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from pydantic import BaseModel

from app.core.config import get_settings
from app.notifiers.factory import build_notifier
from app.connectors.brief_data_source import fetch_morning_brief_data
from app.connectors.akshare_snapshot import fetch_market_snapshot
from app.reports.brief_data import save_brief_data, load_brief_data
from app.reports.brief_store import load_morning_brief_draft, save_morning_brief_draft
from app.reports.morning_brief import build_morning_brief
from app.reports.brief_builder import build_brief_data
from app.core.watchlist import load_watchlist
from app.reports.refresh_status import load_refresh_status, save_refresh_status, new_status
from datetime import datetime, timezone
import time
from pathlib import Path
from app.reports.post_close_payload_builder import build_post_close_payload
from app.reports.post_close_prompt import build_post_close_prompt
from app.connectors.akshare_fundamentals import fetch_fundamentals
from app.connectors.akshare_technicals import fetch_technicals
from app.reports.watchlist_research import save_research_data


router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


class MorningBriefPayload(BaseModel):
    content: str


@router.get("/morning-brief")
def get_morning_brief() -> dict[str, object]:
    settings = get_settings()
    draft = load_morning_brief_draft(settings.data_dir, settings.enable_morning_brief_draft)
    data = fetch_morning_brief_data(settings) or {}
    brief = build_morning_brief(draft, data)
    return {"content": brief, "data": data}


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
    draft = load_morning_brief_draft(settings.data_dir, settings.enable_morning_brief_draft)
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
def refresh_morning_brief_data(background_tasks: BackgroundTasks) -> dict[str, object]:
    settings = get_settings()
    status = load_refresh_status(settings.refresh_status_path) or {}
    last_ts = status.get("ts")
    if last_ts:
        try:
            last_dt = datetime.fromisoformat(last_ts)
            delta = datetime.now(timezone.utc) - last_dt
            if delta.total_seconds() < settings.refresh_min_interval_sec:
                return {"status": "cached", "detail": "too_frequent", "refresh_status": status}
        except Exception:
            pass
    save_refresh_status(settings.refresh_status_path, new_status("running", {"stage": "snapshot"}))
    background_tasks.add_task(_run_refresh, settings)
    return {"status": "queued"}


def _run_refresh(settings) -> None:
    start_ts = time.monotonic()
    try:
        cached_brief = load_brief_data(settings.morning_brief_data_path) or {}
        cached_ts = _file_mtime_iso(settings.morning_brief_data_path)
        watchlist = load_watchlist(settings.watchlist_path)
        symbols = [item.get("symbol") for item in watchlist if item.get("symbol")]
        logger.info("refresh_snapshot_start", extra={"symbols": len(symbols)})
        snapshot = fetch_market_snapshot(symbols, settings.morning_brief_top_n)
        snapshot_meta = snapshot.get("meta", {}) if isinstance(snapshot, dict) else {}
        source = snapshot_meta.get("source", "akshare")
        fallback_used = bool(snapshot_meta.get("fallback_used"))
        degraded = bool(snapshot_meta.get("degraded"))
        cache_ts = snapshot_meta.get("cache_ts")
        logger.info(
            "refresh_snapshot_done",
            extra={
                "source": source,
                "watchlist_count": len(snapshot.get("watchlist", [])),
                "top_gainers_count": len(snapshot.get("top_gainers", [])),
                "top_turnover_count": len(snapshot.get("top_turnover", [])),
                "fallback_used": fallback_used,
            },
        )
        payload = build_brief_data(
            watchlist_snapshot=snapshot.get("watchlist", []),
            top_gainers=snapshot.get("top_gainers", []),
            top_turnover=snapshot.get("top_turnover", []),
        )
        notes = payload.setdefault("notes", [])
        notes.append(f"source: {source}")
        if fallback_used:
            fallback_note = f"fallback: {source}"
            if degraded:
                fallback_note += " (watchlist only)"
            if cache_ts:
                fallback_note += f" (cache {cache_ts})"
            notes.append(fallback_note)
        if snapshot.get("watchlist") and not snapshot.get("top_gainers") and not snapshot.get("top_turnover"):
            notes.append("snapshot: top lists empty")
            if cached_brief.get("top_gainers") or cached_brief.get("top_turnover"):
                payload["top_gainers"] = cached_brief.get("top_gainers", [])
                payload["top_turnover"] = cached_brief.get("top_turnover", [])
                if cached_ts:
                    notes.append(f"top lists cached from {cached_ts}")
            elif payload.get("watchlist"):
                payload["top_gainers"] = _top_by_key(payload["watchlist"], "pct_chg", settings.morning_brief_top_n)
                payload["top_turnover"] = _top_by_key(payload["watchlist"], "amount", settings.morning_brief_top_n)
                notes.append("top lists derived from watchlist only")
        save_brief_data(settings.morning_brief_data_path, payload)
        status_payload = new_status(
            "success",
            {
                "watchlist_count": len(snapshot.get("watchlist", [])),
                "top_gainers_count": len(payload.get("top_gainers", [])),
                "top_turnover_count": len(payload.get("top_turnover", [])),
                "source": source,
                "fallback_used": fallback_used,
                "degraded": degraded,
                "cache_ts": cache_ts,
                "snapshot_duration_ms": int((time.monotonic() - start_ts) * 1000),
            },
        )
        if snapshot_meta.get("error"):
            status_payload["snapshot_error"] = snapshot_meta.get("error")
        if settings.research_enabled and symbols:
            status_payload["research_state"] = "running"
            status_payload["research_symbols"] = min(len(symbols), settings.research_max_symbols)
            status_payload["stage"] = "research"
        else:
            status_payload["research_state"] = "skipped"
        save_refresh_status(settings.refresh_status_path, status_payload)

        _run_research_refresh(settings, symbols)
    except Exception as exc:
        save_brief_data(
            settings.morning_brief_data_path,
            {"highlights": [], "notes": [f"refresh_failed: {exc}"]},
        )
        save_refresh_status(
            settings.refresh_status_path, new_status("failed", {"error": str(exc), "stage": "snapshot"})
        )


def _run_research_refresh(settings, symbols) -> None:
    if not settings.research_enabled:
        return
    if not symbols:
        status_payload = load_refresh_status(settings.refresh_status_path) or {}
        status_payload.update({"research_state": "skipped", "research_symbols": 0})
        save_refresh_status(settings.refresh_status_path, status_payload)
        return
    start_ts = time.monotonic()
    limited = symbols[: settings.research_max_symbols]
    try:
        status_payload = load_refresh_status(settings.refresh_status_path) or {}
        status_payload.update({"research_state": "running", "stage": "research"})
        save_refresh_status(settings.refresh_status_path, status_payload)
        fundamentals = fetch_fundamentals(limited)
        technicals = fetch_technicals(limited)
        save_research_data(settings, {"items": fundamentals}, {"items": technicals})
        status_payload = load_refresh_status(settings.refresh_status_path) or {}
        status_payload.update(
            {
                "research_state": "success",
                "research_symbols": len(limited),
                "research_duration_ms": int((time.monotonic() - start_ts) * 1000),
                "stage": "done",
            }
        )
        save_refresh_status(settings.refresh_status_path, status_payload)
    except Exception as exc:
        status_payload = load_refresh_status(settings.refresh_status_path) or {}
        status_payload.update(
            {
                "research_state": "failed",
                "research_symbols": len(limited),
                "research_error": str(exc),
                "research_duration_ms": int((time.monotonic() - start_ts) * 1000),
                "stage": "done",
            }
        )
        save_refresh_status(settings.refresh_status_path, status_payload)


@router.get("/morning-brief/refresh/status")
def refresh_status() -> dict[str, object]:
    settings = get_settings()
    status = load_refresh_status(settings.refresh_status_path) or {"state": "idle"}
    return {"status": status}


@router.get("/post-close/prompt")
def post_close_prompt() -> dict[str, object]:
    settings = get_settings()
    payload = build_post_close_payload(settings)
    prompt = build_post_close_prompt(payload)
    return {"prompt": prompt, "payload": payload}


def _file_mtime_iso(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    ts = file_path.stat().st_mtime
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def _top_by_key(items, key: str, limit: int):
    def _num(value):
        try:
            return float(value)
        except Exception:
            return float("-inf")

    if not items:
        return []
    return sorted(items, key=lambda item: _num(item.get(key)), reverse=True)[:limit]
