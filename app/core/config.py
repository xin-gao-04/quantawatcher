from __future__ import annotations

from functools import lru_cache

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QuantaWatcher"
    env: str = "dev"
    log_level: str = "INFO"
    timezone: str = "Asia/Shanghai"

    data_dir: str = "data"
    db_path: str = "data/quanta_watcher.db"

    poll_interval_sec: int = 60
    morning_brief_hour: int = 8
    morning_brief_minute: int = 30

    notifier_kind: str = "wecom"
    wecom_webhook_url: Optional[str] = None
    outbox_dir: str = "data/outbox"

    disable_scheduler: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="QW_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
