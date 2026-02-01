from __future__ import annotations

import time
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings


def fetch_eastmoney_spot(settings: Settings) -> List[Dict[str, Any]]:
    if not settings.eastmoney_direct_enabled:
        return []
    hosts = _parse_hosts(settings.eastmoney_hosts)
    if not hosts:
        return []
    cookie = settings.eastmoney_cookie or ""
    if settings.eastmoney_auto_cookie:
        if settings.eastmoney_force_cookie or not cookie:
            fetched = _fetch_cookie(settings)
            if fetched:
                cookie = fetched
                _save_cookie(settings, cookie)
        if not cookie:
            cookie = _load_cookie(settings)
        if cookie and _cookie_expired(settings):
            fetched = _fetch_cookie(settings)
            if fetched:
                cookie = fetched
                _save_cookie(settings, cookie)
    headers = {
        "User-Agent": settings.eastmoney_user_agent,
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json, text/plain, */*",
    }
    if cookie:
        headers["Cookie"] = cookie
    proxy = _build_proxy(settings)
    timeout = settings.eastmoney_timeout_sec
    last_exc: Optional[Exception] = None
    for host in hosts:
        try:
            if settings.eastmoney_cookie_verify:
                verified = _verify_host(host, headers, proxy, timeout, settings)
                if not verified:
                    raise RuntimeError("eastmoney_verify_failed")
            rows = _fetch_host(host, headers, proxy, timeout, settings)
            if rows:
                return normalize_eastmoney_rows(rows)
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    return []


def normalize_eastmoney_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in rows:
        items.append(
            {
                "symbol": str(row.get("f12") or "").strip(),
                "name": str(row.get("f14") or "").strip(),
                "last": _to_float(row.get("f2")),
                "pct_chg": _to_float(row.get("f3")),
                "amount": _to_float(row.get("f6")),
            }
        )
    return [item for item in items if item.get("symbol")]


def _fetch_host(
    host: str,
    headers: Dict[str, str],
    proxy: Optional[str],
    timeout: float,
    settings: Settings,
) -> List[Dict[str, Any]]:
    base = host.strip()
    if base.startswith("http://") or base.startswith("https://"):
        url = f"{base}/api/qt/clist/get"
    else:
        url = f"https://{base}/api/qt/clist/get"
    params = _build_params(settings, settings.eastmoney_page_size)
    rows: List[Dict[str, Any]] = []
    with httpx.Client(timeout=timeout, proxy=proxy) as client:
        for page in range(1, settings.eastmoney_max_pages + 1):
            params["pn"] = str(page)
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            payload = data.get("data") or {}
            diff = payload.get("diff") or []
            if isinstance(diff, dict):
                diff_items = list(diff.values())
            else:
                diff_items = diff
            if not diff_items:
                break
            rows.extend(diff_items)
            total = payload.get("total")
            if total and len(rows) >= int(total):
                break
            time.sleep(settings.eastmoney_page_delay_sec)
    return rows


def _verify_host(
    host: str,
    headers: Dict[str, str],
    proxy: Optional[str],
    timeout: float,
    settings: Settings,
) -> bool:
    base = host.strip()
    if base.startswith("http://") or base.startswith("https://"):
        url = f"{base}/api/qt/clist/get"
    else:
        url = f"https://{base}/api/qt/clist/get"
    params = _build_params(settings, 1)
    params["pn"] = "1"
    with httpx.Client(timeout=timeout, proxy=proxy) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    payload = data.get("data") or {}
    diff = payload.get("diff") or []
    if isinstance(diff, dict):
        diff_items = list(diff.values())
    else:
        diff_items = diff
    return bool(diff_items)


def _build_params(settings: Settings, page_size: int) -> Dict[str, str]:
    return {
        "pn": "1",
        "pz": str(page_size),
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,"
        "f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
    }


def _parse_hosts(value: str) -> List[str]:
    if not value:
        return [
            "https://82.push2.eastmoney.com",
            "https://push2.eastmoney.com",
            "http://82.push2.eastmoney.com",
            "http://push2.eastmoney.com",
        ]
    items = [item.strip() for item in value.split(",") if item.strip()]
    return (
        items
        or [
            "https://82.push2.eastmoney.com",
            "https://push2.eastmoney.com",
            "http://82.push2.eastmoney.com",
            "http://push2.eastmoney.com",
        ]
    )


def _build_proxy(settings: Settings) -> Optional[str]:
    if settings.https_proxy:
        return settings.https_proxy
    if settings.http_proxy:
        return settings.http_proxy
    return None


def _fetch_cookie(settings: Settings) -> str:
    proxy = _build_proxy(settings)
    timeout = settings.eastmoney_timeout_sec
    headers = {"User-Agent": settings.eastmoney_user_agent}
    with httpx.Client(timeout=timeout, proxy=proxy) as client:
        resp = client.get(settings.eastmoney_cookie_url, headers=headers)
        resp.raise_for_status()
        cookie_from_jar = _cookie_from_jar(resp.cookies)
        if cookie_from_jar:
            return cookie_from_jar
        set_cookie_values = _get_set_cookie(resp)
        return _cookie_from_headers(set_cookie_values)


def _cookie_from_jar(jar: httpx.Cookies) -> str:
    items = [(key, jar.get(key)) for key in jar.keys()]
    items = [(k, v) for k, v in items if v]
    return "; ".join([f"{k}={v}" for k, v in items])


def _get_set_cookie(resp: httpx.Response) -> List[str]:
    if hasattr(resp.headers, "get_list"):
        return resp.headers.get_list("set-cookie")
    header = resp.headers.get("set-cookie")
    return [header] if header else []


def _cookie_from_headers(values: List[str]) -> str:
    cookie = SimpleCookie()
    for value in values:
        cookie.load(value)
    return "; ".join([f"{key}={morsel.value}" for key, morsel in cookie.items()])


def _load_cookie(settings: Settings) -> str:
    path = Path(settings.eastmoney_cookie_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _save_cookie(settings: Settings, cookie: str) -> None:
    path = Path(settings.eastmoney_cookie_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cookie, encoding="utf-8")


def _cookie_expired(settings: Settings) -> bool:
    if settings.eastmoney_cookie_ttl_sec <= 0:
        return False
    path = Path(settings.eastmoney_cookie_path)
    if not path.exists():
        return True
    age = time.time() - path.stat().st_mtime
    return age > settings.eastmoney_cookie_ttl_sec


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None
