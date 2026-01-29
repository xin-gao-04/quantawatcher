from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import Settings
from app.storage.sqlite import SqliteStorage
from app.notifiers.factory import build_notifier
from app.reports.brief_store import load_morning_brief_draft
from app.reports.morning_brief import build_morning_brief


logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._scheduler = AsyncIOScheduler(timezone=settings.timezone)
        self._storage = SqliteStorage(settings.db_path)
        self._notifier = build_notifier(settings)

    async def start(self) -> None:
        self._storage.init_db()
        self._scheduler.add_job(
            self.collect_snapshots,
            "interval",
            seconds=self._settings.poll_interval_sec,
            id="collect_snapshots",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )
        self._scheduler.add_job(
            self.send_morning_brief,
            "cron",
            hour=self._settings.morning_brief_hour,
            minute=self._settings.morning_brief_minute,
            id="morning_brief",
        )
        self._scheduler.start()
        logger.info("scheduler_started")

    async def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")

    def collect_snapshots(self) -> None:
        start_ts = datetime.now(timezone.utc)
        try:
            logger.info("collect_snapshots_started")
            # TODO: wire connectors + indicators + rules
            status = "success"
            error = None
        except Exception as exc:  # pragma: no cover - placeholder
            logger.exception("collect_snapshots_failed")
            status = "failed"
            error = str(exc)
        finally:
            end_ts = datetime.now(timezone.utc)
            self._storage.record_task_run(
                "collect_snapshots",
                start_ts.isoformat(),
                end_ts.isoformat(),
                status,
                error,
            )

    def send_morning_brief(self) -> None:
        start_ts = datetime.now(timezone.utc)
        try:
            draft = load_morning_brief_draft(self._settings.data_dir)
            brief = build_morning_brief(draft)
            self._notifier.send(brief, severity="info", tags=["report", "morning"])
            status = "success"
            error = None
        except Exception as exc:  # pragma: no cover - placeholder
            logger.exception("send_morning_brief_failed")
            status = "failed"
            error = str(exc)
        finally:
            end_ts = datetime.now(timezone.utc)
            self._storage.record_task_run(
                "send_morning_brief",
                start_ts.isoformat(),
                end_ts.isoformat(),
                status,
                error,
            )
