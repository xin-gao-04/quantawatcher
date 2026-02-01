from __future__ import annotations

import concurrent.futures
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import Settings

_SINA_PAGE_SIZE_CAP = 100


def fetch_sina_market(settings: Settings) -> List[Dict[str, Any]]:
    url = settings.sina_market_url
    headers = {
        "User-Agent": settings.sina_market_user_agent,
        "Referer": "https://finance.sina.com.cn/",
    }
    timeout = settings.sina_market_timeout_sec
    proxy = _build_proxy(settings)
    rows: List[Dict[str, Any]] = []
    page_size = settings.sina_market_page_size
    effective_page_size = min(page_size, _SINA_PAGE_SIZE_CAP)
    max_pages = settings.sina_market_max_pages
    concurrency = max(1, settings.sina_market_concurrency)

    if concurrency <= 1:
        for page in range(1, max_pages + 1):
            try:
                _, items = _fetch_page_items(
                    page,
                    url,
                    effective_page_size,
                    headers,
                    proxy,
                    timeout,
                    settings,
                )
            except Exception:
                if rows:
                    break
                raise
            if not items:
                break
            rows.extend(items)
            if len(items) < effective_page_size:
                break
            time.sleep(settings.sina_market_page_delay_sec)
    else:
        page_map: Dict[int, List[Dict[str, Any]]] = {}
        errors: List[Tuple[int, Exception]] = []
        pages = list(range(1, max_pages + 1))
        for offset in range(0, len(pages), concurrency):
            batch = pages[offset : offset + concurrency]
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = {
                    executor.submit(
                        _fetch_page_items,
                        page,
                        url,
                        effective_page_size,
                        headers,
                        proxy,
                        timeout,
                        settings,
                    ): page
                    for page in batch
                }
                for future in concurrent.futures.as_completed(futures):
                    page = futures[future]
                    try:
                        _, items = future.result()
                        if items:
                            page_map[page] = items
                    except Exception as exc:
                        errors.append((page, exc))
            if settings.sina_market_page_delay_sec:
                time.sleep(settings.sina_market_page_delay_sec)
        for page in range(1, max_pages + 1):
            items = page_map.get(page, [])
            if not items:
                break
            rows.extend(items)
            if len(items) < effective_page_size:
                break
        if not rows and errors:
            raise errors[0][1]

    normalized = _normalize_sina_rows(rows)
    min_rows = settings.sina_market_min_rows
    if min_rows > 0 and len(normalized) < min_rows:
        raise RuntimeError(f"sina_market_incomplete:{len(normalized)}")
    return normalized


def _fetch_page(
    url: str,
    params: Dict[str, str],
    headers: Dict[str, str],
    proxy: Optional[str],
    timeout: float,
) -> str:
    try:
        with httpx.Client(timeout=timeout, proxy=proxy) as client:
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text.strip()
            if text and not text.startswith("[") and text != "null":
                raise ValueError("sina_invalid_payload")
            return text
    except Exception:
        if proxy:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                text = resp.text.strip()
                if text and not text.startswith("[") and text != "null":
                    raise ValueError("sina_invalid_payload")
                return text
        raise


def _fetch_page_with_retry(
    url: str,
    params: Dict[str, str],
    headers: Dict[str, str],
    proxy: Optional[str],
    timeout: float,
    retries: int,
    backoff_sec: float,
) -> str:
    last_exc: Optional[Exception] = None
    attempts = max(1, retries)
    for idx in range(attempts):
        try:
            return _fetch_page(url, params, headers, proxy, timeout)
        except Exception as exc:
            last_exc = exc
            if idx < attempts - 1:
                time.sleep(backoff_sec * (2**idx))
    if last_exc:
        raise last_exc
    raise RuntimeError("sina_fetch_failed")


def _fetch_page_items(
    page: int,
    url: str,
    page_size: int,
    headers: Dict[str, str],
    proxy: Optional[str],
    timeout: float,
    settings: Settings,
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        "page": str(page),
        "num": str(page_size),
        "sort": settings.sina_market_sort,
        "asc": "1" if settings.sina_market_asc else "0",
        "node": settings.sina_market_node,
        "symbol": "",
        "_s_r_a": "init",
    }
    text = _fetch_page_with_retry(
        url,
        params,
        headers,
        proxy,
        timeout,
        settings.sina_market_retries,
        settings.sina_market_backoff_sec,
    )
    return page, _parse_sina_text(text)


def _parse_sina_text(text: str) -> List[Dict[str, Any]]:
    if not text or text == "null":
        return []
    text = text.strip()
    if not text.startswith("["):
        return []
    json_text = re.sub(r'([{,])([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return []


def _normalize_sina_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in rows:
        code = row.get("code") or row.get("symbol") or ""
        code = str(code)
        if code.startswith(("sh", "sz")):
            code = code[2:]
        items.append(
            {
                "symbol": code,
                "name": row.get("name") or "",
                "last": _to_float(row.get("trade") or row.get("price")),
                "pct_chg": _to_float(row.get("changepercent")),
                "amount": _to_float(row.get("amount")),
            }
        )
    return [item for item in items if item.get("symbol")]


def _build_proxy(settings: Settings) -> Optional[str]:
    if settings.https_proxy:
        return settings.https_proxy
    if settings.http_proxy:
        return settings.http_proxy
    return None


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None
