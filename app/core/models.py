from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class Symbol(BaseModel):
    symbol: str
    name: Optional[str] = None
    tags: list[str] = []
    priority: int = 0
    enabled: bool = True


class Sector(BaseModel):
    sector_id: str
    name: str
    sector_type: str
    enabled: bool = True


class Snapshot(BaseModel):
    ts: datetime
    symbol: str
    last: float
    pct_chg: float
    volume: float
    amount: float
    extra: dict[str, Any] = {}


class Indicator(BaseModel):
    ts: datetime
    entity_type: str
    entity_id: str
    key: str
    value: float
    window: Optional[str] = None


class Event(BaseModel):
    ts: datetime
    event_type: str
    entity_type: str
    entity_id: str
    score: Optional[float] = None
    message: str
    payload: dict[str, Any] = {}
    dedup_key: str


class TaskRun(BaseModel):
    task_name: str
    start_ts: datetime
    end_ts: Optional[datetime] = None
    status: str
    error: Optional[str] = None
