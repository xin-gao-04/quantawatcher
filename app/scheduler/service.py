from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import Settings
from app.storage.sqlite import SqliteStorage
from app.notifiers.factory import build_notifier
from app.connectors.brief_data_source import fetch_morning_brief_data
from app.connectors.akshare_snapshot import fetch_market_snapshot
from app.reports.brief_store import load_morning_brief_draft
from app.reports.morning_brief import build_morning_brief
from app.reports.brief_builder import build_brief_data
from app.core.watchlist import load_watchlist
from app.reports.brief_data import save_brief_data


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
        self._scheduler.add_job(
            self.refresh_morning_brief_data,
            "cron",
            hour=self._settings.morning_brief_refresh_hour,
            minute=self._settings.morning_brief_refresh_minute,
            id="morning_brief_refresh",
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
            draft = load_morning_brief_draft(
                self._settings.data_dir, self._settings.enable_morning_brief_draft
            )
            data = fetch_morning_brief_data(self._settings)
            brief = build_morning_brief(draft, data)
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

    def refresh_morning_brief_data(self) -> None:
        start_ts = datetime.now(timezone.utc)
        try:
            watchlist = load_watchlist(self._settings.watchlist_path)
            symbols = [item.get("symbol") for item in watchlist if item.get("symbol")]
            snapshot = fetch_market_snapshot(symbols, self._settings.morning_brief_top_n)
            snapshot_meta = snapshot.get("meta", {}) if isinstance(snapshot, dict) else {}
            payload = build_brief_data(
                watchlist_snapshot=snapshot.get("watchlist", []),
                top_gainers=snapshot.get("top_gainers", []),
                top_turnover=snapshot.get("top_turnover", []),
            )
            notes = payload.setdefault("notes", [])
            notes.append(f"source: {snapshot_meta.get('source', 'akshare')}")
            if snapshot_meta.get("fallback_used"):
                fallback_note = f"fallback: {snapshot_meta.get('source', 'unknown')}"
                if snapshot_meta.get("degraded"):
                    fallback_note += " (watchlist only)"
                cache_ts = snapshot_meta.get("cache_ts")
                if cache_ts:
                    fallback_note += f" (cache {cache_ts})"
                notes.append(fallback_note)
            save_brief_data(self._settings.morning_brief_data_path, payload)
            status = "success"
            error = None
        except Exception as exc:  # pragma: no cover - external dependency
            logger.exception("refresh_morning_brief_failed")
            status = "failed"
            error = str(exc)
        finally:
            end_ts = datetime.now(timezone.utc)
            self._storage.record_task_run(
                "refresh_morning_brief",
                start_ts.isoformat(),
                end_ts.isoformat(),
                status,
                error,
            )
