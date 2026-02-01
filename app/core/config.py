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
    morning_brief_refresh_hour: int = 8
    morning_brief_refresh_minute: int = 20

    notifier_kind: str = "wecom"
    wecom_webhook_url: Optional[str] = None
    outbox_dir: str = "data/outbox"
    morning_brief_data_path: str = "data/morning_brief_data.json"
    watchlist_path: str = "data/watchlist.json"
    morning_brief_top_n: int = 10
    enable_morning_brief_draft: bool = False
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    akshare_use_proxy: bool = True
    akshare_retries: int = 5
    akshare_backoff_sec: float = 2.0
    akshare_snapshot_timeout_sec: float = 12.0
    akshare_research_timeout_sec: float = 6.0
    akshare_spot_sources: str = "em,sina"
    market_snapshot_sources: str = "sina_market,cache,akshare,eastmoney_direct,tencent"
    market_snapshot_cache_path: str = "data/market_snapshot_cache.json"
    market_snapshot_cache_ttl_sec: int = 3600
    eastmoney_direct_enabled: bool = True
    eastmoney_hosts: str = (
        "https://82.push2.eastmoney.com,https://push2.eastmoney.com,"
        "http://82.push2.eastmoney.com,http://push2.eastmoney.com"
    )
    eastmoney_timeout_sec: float = 10.0
    eastmoney_page_size: int = 200
    eastmoney_max_pages: int = 50
    eastmoney_page_delay_sec: float = 0.2
    eastmoney_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    eastmoney_cookie: Optional[str] = None
    eastmoney_auto_cookie: bool = True
    eastmoney_force_cookie: bool = True
    eastmoney_cookie_verify: bool = True
    eastmoney_cookie_url: str = "https://quote.eastmoney.com/"
    eastmoney_cookie_path: str = "data/eastmoney_cookie.txt"
    eastmoney_cookie_ttl_sec: int = 21600
    sina_market_url: str = (
        "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "Market_Center.getHQNodeData"
    )
    sina_market_node: str = "hs_a"
    sina_market_page_size: int = 100
    sina_market_max_pages: int = 50
    sina_market_page_delay_sec: float = 0.2
    sina_market_timeout_sec: float = 10.0
    sina_market_retries: int = 3
    sina_market_backoff_sec: float = 0.5
    sina_market_concurrency: int = 5
    sina_market_min_rows: int = 3000
    sina_market_sort: str = "symbol"
    sina_market_asc: bool = True
    sina_market_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    tencent_timeout_sec: float = 8.0
    tencent_retries: int = 2
    tencent_backoff_sec: float = 0.5
    disable_fallback: bool = False
    refresh_status_path: str = "data/morning_brief_refresh_status.json"
    refresh_min_interval_sec: int = 60
    watchlist_fundamentals_path: str = "data/watchlist_fundamentals.json"
    watchlist_technicals_path: str = "data/watchlist_technicals.json"
    watchlist_refresh_path: str = "data/watchlist_refresh_status.json"
    research_enabled: bool = True
    research_max_symbols: int = 8

    disable_scheduler: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="QW_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
