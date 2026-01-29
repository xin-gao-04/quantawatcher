from __future__ import annotations

from typing import Any, Dict, List


def _require_akshare():
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("akshare_not_installed") from exc
    return ak


def fetch_watchlist_snapshot(symbols: List[str]) -> List[Dict[str, Any]]:
    if not symbols:
        return []
    ak = _require_akshare()
    df = ak.stock_zh_a_spot_em()
    if df is None or df.empty:
        return []
    records = df.to_dict("records")
    lookup = {item.get("代码"): item for item in records}
    results: List[Dict[str, Any]] = []
    for code in symbols:
        row = lookup.get(code)
        if not row:
            continue
        results.append(
            {
                "symbol": code,
                "name": row.get("名称"),
                "last": row.get("最新价"),
                "pct_chg": row.get("涨跌幅"),
                "amount": row.get("成交额"),
            }
        )
    return results


def fetch_market_top_movers(top_n: int) -> Dict[str, List[Dict[str, Any]]]:
    ak = _require_akshare()
    df = ak.stock_zh_a_spot_em()
    if df is None or df.empty:
        return {"top_gainers": [], "top_turnover": []}
    df = df.fillna(0)
    df_top_gainers = df.sort_values("涨跌幅", ascending=False).head(top_n)
    df_top_turnover = df.sort_values("成交额", ascending=False).head(top_n)
    return {
        "top_gainers": _normalize_rows(df_top_gainers),
        "top_turnover": _normalize_rows(df_top_turnover),
    }


def _normalize_rows(df) -> List[Dict[str, Any]]:
    rows = df.to_dict("records")
    return [
        {
            "symbol": row.get("代码"),
            "name": row.get("名称"),
            "last": row.get("最新价"),
            "pct_chg": row.get("涨跌幅"),
            "amount": row.get("成交额"),
        }
        for row in rows
    ]
