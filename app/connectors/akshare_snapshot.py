from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Callable, TypeVar, Optional, Tuple

from app.connectors.tencent_quote import fetch_quotes
from app.connectors.eastmoney_spot import fetch_eastmoney_spot
from app.connectors.sina_market import fetch_sina_market
from app.core.config import Settings

logger = logging.getLogger(__name__)
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _require_akshare():
    qw_http_proxy = os.getenv("QW_HTTP_PROXY")
    qw_https_proxy = os.getenv("QW_HTTPS_PROXY")
    if qw_http_proxy or qw_https_proxy:
        if qw_http_proxy:
            os.environ["HTTP_PROXY"] = qw_http_proxy
        if qw_https_proxy:
            os.environ["HTTPS_PROXY"] = qw_https_proxy
        os.environ.pop("NO_PROXY", None)
    else:
        os.environ.setdefault("NO_PROXY", "*")
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        os.environ.pop("ALL_PROXY", None)
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("akshare_not_installed") from exc
    return ak


def fetch_watchlist_snapshot(symbols: List[str]) -> List[Dict[str, Any]]:
    if not symbols:
        return []
    ak = _require_akshare()
    settings = Settings()
    sources = _parse_sources(settings.akshare_spot_sources)
    df, _ = _retry(
        lambda: _fetch_spot_df(ak, sources, settings.akshare_snapshot_timeout_sec),
        settings.akshare_retries,
        settings.akshare_backoff_sec,
    )
    if df is None or df.empty:
        return []
    records = _normalize_rows(df)
    lookup = {item.get("symbol"): item for item in records}
    results: List[Dict[str, Any]] = []
    for code in symbols:
        row = lookup.get(code)
        if not row:
            continue
        results.append(
            {
                "symbol": code,
                "name": row.get("name"),
                "last": row.get("last"),
                "pct_chg": row.get("pct_chg"),
                "amount": row.get("amount"),
            }
        )
    return results


def fetch_market_top_movers(top_n: int) -> Dict[str, List[Dict[str, Any]]]:
    settings = Settings()
    try:
        items, _ = _fetch_market_items(settings, symbols=[])
        snapshot = _build_snapshot_from_items(items, [], top_n)
        return {
            "top_gainers": snapshot.get("top_gainers", []),
            "top_turnover": snapshot.get("top_turnover", []),
        }
    except Exception:
        if settings.disable_fallback:
            raise
        return {"top_gainers": [], "top_turnover": []}


def fetch_market_snapshot(symbols: List[str], top_n: int) -> Dict[str, List[Dict[str, Any]]]:
    settings = Settings()
    items, meta = _fetch_market_items(settings, symbols=symbols)
    snapshot = _build_snapshot_from_items(items, symbols, top_n)
    snapshot["meta"] = meta
    return snapshot


def _normalize_rows(df) -> List[Dict[str, Any]]:
    rows = df.to_dict("records")
    return [
        {
            "symbol": _pick_first(row, ["代码", "symbol", "code"]),
            "name": _pick_first(row, ["名称", "name"]),
            "last": _pick_first(row, ["最新价", "last", "trade", "现价"]),
            "pct_chg": _pick_first(row, ["涨跌幅", "pct_chg", "涨跌幅%", "changepercent"]),
            "amount": _pick_first(row, ["成交额", "amount", "成交额(元)", "turnover"]),
        }
        for row in rows
    ]


T = TypeVar("T")


def _retry(
    fn: Callable[[], T],
    attempts: int = 3,
    backoff_sec: float = 1.0,
    timeout_sec: Optional[float] = None,
) -> T:
    last_exc: Optional[Exception] = None
    for idx in range(attempts):
        try:
            if timeout_sec:
                return _call_with_timeout(fn, timeout_sec)
            return fn()
        except Exception as exc:  # pragma: no cover - external dependency
            last_exc = exc
            time.sleep(backoff_sec * (2 ** idx))
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_failed")


def _fetch_spot_df(ak, sources: List[str], timeout_sec: Optional[float] = None):
    last_exc: Optional[Exception] = None
    for source in sources:
        try:
            if source == "em":
                return _call_with_timeout(lambda: ak.stock_zh_a_spot_em(), timeout_sec), source
            if source == "sina" and hasattr(ak, "stock_zh_a_spot"):
                return _call_with_timeout(lambda: ak.stock_zh_a_spot(), timeout_sec), source
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    raise RuntimeError("spot_source_unavailable")


def _call_with_timeout(fn: Callable[[], T], timeout_sec: Optional[float]) -> T:
    if not timeout_sec or timeout_sec <= 0:
        return fn()
    future = _EXECUTOR.submit(fn)
    try:
        return future.result(timeout=timeout_sec)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        logger.warning("akshare_call_timeout", extra={"timeout_sec": timeout_sec})
        raise TimeoutError("akshare_timeout") from exc


def _pick_first(row: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _find_col(df, keys: List[str]) -> Optional[str]:
    for key in keys:
        if key in df.columns:
            return key
    return None


def _parse_sources(value: str) -> List[str]:
    if not value:
        return ["em", "sina"]
    items = [item.strip().lower() for item in value.split(",") if item.strip()]
    return items or ["em", "sina"]


def _parse_market_sources(value: str) -> List[str]:
    if not value:
        return ["sina_market", "cache", "akshare", "eastmoney_direct", "tencent"]
    raw_items = [item.strip().lower() for item in value.split(",") if item.strip()]
    mapping = {
        "em": "eastmoney_direct",
        "eastmoney": "eastmoney_direct",
        "sina": "sina_market",
        "ak": "akshare",
    }
    items = [mapping.get(item, item) for item in raw_items]
    return items or ["sina_market", "cache", "akshare", "eastmoney_direct", "tencent"]


def _build_snapshot_from_items(
    items: List[Dict[str, Any]],
    symbols: List[str],
    top_n: int,
) -> Dict[str, List[Dict[str, Any]]]:
    lookup = {item.get("symbol"): item for item in items}
    watchlist = [lookup[s] for s in symbols if s in lookup] if symbols else []
    top_gainers = sorted(
        items,
        key=lambda item: _safe_num(item.get("pct_chg")),
        reverse=True,
    )[:top_n]
    top_turnover = sorted(
        items,
        key=lambda item: _safe_num(item.get("amount")),
        reverse=True,
    )[:top_n]
    return {
        "watchlist": watchlist or items[:top_n],
        "top_gainers": top_gainers,
        "top_turnover": top_turnover,
    }


def _fetch_market_items(settings: Settings, symbols: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    sources = _parse_market_sources(settings.market_snapshot_sources)
    if settings.disable_fallback and sources:
        sources = sources[:1]
    logger.info("market_snapshot_start", extra={"sources": sources})
    last_exc: Optional[Exception] = None
    for idx, source in enumerate(sources):
        fallback_used = idx > 0
        if source == "sina_market":
            try:
                logger.info("market_snapshot_try", extra={"source": source, "fallback": fallback_used})
                items = fetch_sina_market(settings)
                if items:
                    _save_market_cache(settings, items)
                    logger.info(
                        "market_snapshot_success",
                        extra={"source": source, "count": len(items), "fallback": fallback_used},
                    )
                    return items, {
                        "source": "sina_market",
                        "fallback_used": fallback_used,
                        "error": _exc_text(last_exc),
                    }
            except Exception as exc:
                logger.warning("market_snapshot_failed", extra={"source": source, "error": str(exc)})
                last_exc = exc
                continue
        if source == "eastmoney_direct":
            try:
                logger.info("market_snapshot_try", extra={"source": source, "fallback": fallback_used})
                em_rows = fetch_eastmoney_spot(settings)
                if em_rows:
                    _save_market_cache(settings, em_rows)
                    logger.info(
                        "market_snapshot_success",
                        extra={"source": source, "count": len(em_rows), "fallback": fallback_used},
                    )
                    return em_rows, {
                        "source": "eastmoney_direct",
                        "fallback_used": fallback_used,
                        "error": _exc_text(last_exc),
                    }
            except Exception as exc:
                logger.warning("market_snapshot_failed", extra={"source": source, "error": str(exc)})
                last_exc = exc
                continue
        if source == "akshare":
            try:
                logger.info("market_snapshot_try", extra={"source": source, "fallback": fallback_used})
                items, ak_source = _fetch_akshare_items(settings)
                if items:
                    _save_market_cache(settings, items)
                    logger.info(
                        "market_snapshot_success",
                        extra={"source": f"akshare_{ak_source}", "count": len(items), "fallback": fallback_used},
                    )
                    return items, {
                        "source": f"akshare_{ak_source}",
                        "fallback_used": fallback_used,
                        "error": _exc_text(last_exc),
                    }
            except Exception as exc:
                logger.warning("market_snapshot_failed", extra={"source": source, "error": str(exc)})
                last_exc = exc
                continue
        if source == "cache":
            cached, cache_ts = _load_market_cache(settings)
            if cached and not _cache_expired(settings, cache_ts):
                logger.info(
                    "market_snapshot_success",
                    extra={"source": "cache", "count": len(cached), "fallback": True},
                )
                return cached, {
                    "source": "cache",
                    "fallback_used": True,
                    "cache_ts": cache_ts,
                    "error": _exc_text(last_exc),
                }
        if source == "tencent":
            if not symbols:
                continue
            try:
                logger.info("market_snapshot_try", extra={"source": source, "fallback": True})
                items = fetch_quotes(symbols, settings=settings)
                logger.info(
                    "market_snapshot_success",
                    extra={"source": "tencent_watchlist", "count": len(items), "fallback": True},
                )
                return items, {
                    "source": "tencent_watchlist",
                    "fallback_used": True,
                    "degraded": True,
                    "error": _exc_text(last_exc),
                }
            except Exception as exc:
                logger.warning("market_snapshot_failed", extra={"source": source, "error": str(exc)})
                last_exc = exc
                continue
    if last_exc:
        raise last_exc
    return [], {"source": "none", "fallback_used": True, "error": None}


def _fetch_akshare_items(settings: Settings) -> Tuple[List[Dict[str, Any]], str]:
    ak = _require_akshare()
    sources = _parse_sources(settings.akshare_spot_sources)
    df, source = _retry(
        lambda: _fetch_spot_df(ak, sources, settings.akshare_snapshot_timeout_sec),
        settings.akshare_retries,
        settings.akshare_backoff_sec,
    )
    if df is None or df.empty:
        raise RuntimeError("spot_df_empty")
    return _normalize_rows(df), source


def _save_market_cache(settings: Settings, items: List[Dict[str, Any]]) -> None:
    path = Path(settings.market_snapshot_cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def _load_market_cache(settings: Settings) -> Tuple[List[Dict[str, Any]], str]:
    path = Path(settings.market_snapshot_cache_path)
    if not path.exists():
        return [], ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [], ""
    items = payload.get("items") if isinstance(payload, dict) else []
    ts = payload.get("ts") if isinstance(payload, dict) else ""
    if not isinstance(items, list):
        items = []
    if not isinstance(ts, str):
        ts = ""
    min_rows = settings.sina_market_min_rows
    if min_rows > 0 and len(items) < min_rows:
        return [], ts
    return items, ts


def _cache_expired(settings: Settings, ts: str) -> bool:
    ttl = settings.market_snapshot_cache_ttl_sec
    if ttl <= 0:
        return False
    if not ts:
        return True
    try:
        parsed = datetime.fromisoformat(ts)
    except Exception:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
    return age.total_seconds() > ttl


def _exc_text(exc: Optional[Exception]) -> Optional[str]:
    if exc is None:
        return None
    return str(exc)


def _safe_num(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return float("-inf")
