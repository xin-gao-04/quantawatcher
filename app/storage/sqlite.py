from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class SqliteStorage:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def init_db(self) -> None:
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    score REAL,
                    message TEXT NOT NULL,
                    payload TEXT,
                    dedup_key TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS task_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    start_ts TEXT NOT NULL,
                    end_ts TEXT,
                    status TEXT NOT NULL,
                    error TEXT
                )
                """
            )
            conn.commit()

    def record_task_run(
        self,
        task_name: str,
        start_ts: str,
        end_ts: str,
        status: str,
        error: Optional[str],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO task_runs (task_name, start_ts, end_ts, status, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_name, start_ts, end_ts, status, error),
            )
            conn.commit()

    def record_event(
        self,
        ts: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        score: Optional[float],
        message: str,
        payload: str,
        dedup_key: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (ts, event_type, entity_type, entity_id, score, message, payload, dedup_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, event_type, entity_type, entity_id, score, message, payload, dedup_key),
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)
