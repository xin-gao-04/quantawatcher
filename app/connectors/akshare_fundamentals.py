from __future__ import annotations

from typing import Any, Dict, List

from app.connectors.akshare_snapshot import _require_akshare, _retry
from app.core.config import Settings


def fetch_fundamentals(symbols: List[str]) -> List[Dict[str, Any]]:
    if not symbols:
        return []
    ak = _require_akshare()
    settings = Settings()
    results: List[Dict[str, Any]] = []
    for symbol in symbols:
        pe_ttm = pb = roe = "NA"
        revenue_yoy = profit_yoy = "NA"
        gross_margin = net_margin = "NA"
        debt_ratio = "NA"
        market_cap = "NA"
        try:
            df = _retry(
                lambda: ak.stock_a_indicator_lg(symbol=symbol),
                settings.akshare_retries,
                settings.akshare_backoff_sec,
                settings.akshare_research_timeout_sec,
            )
            if df is not None and not df.empty:
                row = df.iloc[-1].to_dict()
                pe_ttm = row.get("pe_ttm", row.get("pe", "NA"))
                pb = row.get("pb", "NA")
                roe = row.get("roe", "NA")
        except Exception:
            pass
        try:
            df2 = _retry(
                lambda: ak.stock_financial_analysis_indicator(symbol=symbol),
                settings.akshare_retries,
                settings.akshare_backoff_sec,
                settings.akshare_research_timeout_sec,
            )
            if df2 is not None and not df2.empty:
                row2 = df2.iloc[-1].to_dict()
                revenue_yoy = row2.get("营业收入同比增长率(%)", row2.get("营业收入同比", "NA"))
                profit_yoy = row2.get("净利润同比增长率(%)", row2.get("净利润同比", "NA"))
                gross_margin = row2.get("销售毛利率(%)", row2.get("毛利率", "NA"))
                net_margin = row2.get("销售净利率(%)", row2.get("净利率", "NA"))
                debt_ratio = row2.get("资产负债率(%)", row2.get("负债率", "NA"))
        except Exception:
            pass
        results.append(
            {
                "symbol": symbol,
                "name": "",
                "market_cap": "NA",
                "pe_ttm": pe_ttm,
                "pb": pb,
                "roe": roe,
                "revenue_yoy": revenue_yoy,
                "profit_yoy": profit_yoy,
                "gross_margin": gross_margin,
                "net_margin": net_margin,
                "debt_ratio": debt_ratio,
                "cashflow_3y": "NA",
                "moat_notes": "NA",
            }
        )
    return results
