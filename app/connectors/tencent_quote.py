from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings


def fetch_quotes(symbols: List[str], settings: Optional[Settings] = None) -> List[Dict[str, Any]]:
    if not symbols:
        return []
    settings = settings or Settings()
    codes = [_to_tencent_code(sym) for sym in symbols]
    results: List[Dict[str, Any]] = []
    proxy = _build_proxy(settings)
    timeout = settings.tencent_timeout_sec
    with httpx.Client(timeout=timeout, proxy=proxy) as client:
        for chunk in _chunks(codes, 50):
            url = "https://qt.gtimg.cn/q=" + ",".join(chunk)
            results.extend(_fetch_chunk(client, url, settings))
    return results


def _parse_response(text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for line in text.split(";"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        _, raw = line.split("=", 1)
        raw = raw.strip().strip('"')
        parts = raw.split("~")
        if len(parts) < 5:
            continue
        name = parts[1]
        code = parts[2]
        last = _to_float(parts[3])
        prev_close = _to_float(parts[4])
        pct_chg = None
        if last is not None and prev_close:
            pct_chg = (last - prev_close) / prev_close * 100
        items.append(
            {
                "symbol": code,
                "name": name,
                "last": last,
                "pct_chg": pct_chg,
                "amount": None,
            }
        )
    return items


def _to_tencent_code(symbol: str) -> str:
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith("6"):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _to_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _chunks(items: List[str], size: int) -> List[List[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _fetch_chunk(client: httpx.Client, url: str, settings: Settings) -> List[Dict[str, Any]]:
    last_exc: Optional[Exception] = None
    for idx in range(settings.tencent_retries):
        try:
            resp = client.get(url)
            resp.raise_for_status()
            return _parse_response(resp.text)
        except Exception as exc:
            last_exc = exc
            if idx < settings.tencent_retries - 1:
                time.sleep(settings.tencent_backoff_sec * (2 ** idx))
    if last_exc:
        raise last_exc
    return []


def _build_proxy(settings: Settings) -> Optional[str]:
    if settings.https_proxy:
        return settings.https_proxy
    if settings.http_proxy:
        return settings.http_proxy
    return None
