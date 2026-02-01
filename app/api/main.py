from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.api.routes.reports import router as reports_router
from app.api.routes.watchlist import router as watchlist_router
from app.api.routes.ui import router as ui_router
from app.scheduler.service import SchedulerService


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    scheduler = None
    if not settings.disable_scheduler:
        scheduler = SchedulerService(settings)
        await scheduler.start()
        app.state.scheduler = scheduler
    yield
    if scheduler:
        await scheduler.stop()


app = FastAPI(title="QuantaWatcher", lifespan=lifespan)
app.include_router(reports_router)
app.include_router(ui_router)
app.include_router(watchlist_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
async def version() -> dict[str, str]:
    return {"version": "0.1.0"}
