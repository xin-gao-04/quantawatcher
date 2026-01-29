from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.sqlite import SqliteStorage


def test_init_db_creates_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "qw.db"
    storage = SqliteStorage(str(db_path))
    storage.init_db()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "events" in tables
    assert "task_runs" in tables


def test_record_task_run_writes_row(tmp_path: Path) -> None:
    db_path = tmp_path / "qw.db"
    storage = SqliteStorage(str(db_path))
    storage.init_db()

    storage.record_task_run(
        "collect_snapshots",
        "2026-01-28T00:00:00Z",
        "2026-01-28T00:01:00Z",
        "success",
        None,
    )

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT task_name, status FROM task_runs")
    row = cursor.fetchone()
    assert row == ("collect_snapshots", "success")
