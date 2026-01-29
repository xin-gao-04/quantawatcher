from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.notifiers.factory import build_notifier
from app.reports.brief_store import load_morning_brief_draft, save_morning_brief_draft
from app.reports.morning_brief import build_morning_brief


router = APIRouter(prefix="/reports", tags=["reports"])


class MorningBriefPayload(BaseModel):
    content: str


@router.get("/morning-brief")
def get_morning_brief() -> dict[str, str]:
    settings = get_settings()
    draft = load_morning_brief_draft(settings.data_dir)
    brief = build_morning_brief(draft)
    return {"content": brief}


@router.post("/morning-brief")
def save_morning_brief(payload: MorningBriefPayload) -> dict[str, str]:
    settings = get_settings()
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="content_required")
    save_morning_brief_draft(settings.data_dir, payload.content)
    return {"status": "saved"}


@router.post("/morning-brief/send")
def send_morning_brief() -> dict[str, str]:
    settings = get_settings()
    draft = load_morning_brief_draft(settings.data_dir)
    brief = build_morning_brief(draft)
    notifier = build_notifier(settings)
    notifier.send(brief, severity="info", tags=["report", "morning", "manual"])
    return {"status": "sent"}
