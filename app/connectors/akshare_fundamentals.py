from __future__ import annotations

from datetime import datetime
import math
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
                lambda: ak.stock_value_em(symbol=symbol),
                settings.akshare_retries,
                settings.akshare_backoff_sec,
                settings.akshare_research_timeout_sec,
            )
            if df is not None and not df.empty:
                row = df.iloc[-1].to_dict()
                pe_ttm = row.get("PE(TTM)", row.get("PE(TTM) ", "NA"))
                pb = row.get("市净率", "NA")
                market_cap = row.get("总市值", "NA")
        except Exception:
            pass
        try:
            df2 = _fetch_financial_indicator(ak, settings, symbol)
            if df2 is not None and not df2.empty:
                row2 = df2.iloc[-1].to_dict()
                revenue_yoy = row2.get("主营业务收入增长率(%)", row2.get("营业收入同比增长率(%)", "NA"))
                profit_yoy = row2.get("净利润增长率(%)", row2.get("净利润同比增长率(%)", "NA"))
                gross_margin = row2.get("销售毛利率(%)", row2.get("毛利率", "NA"))
                net_margin = row2.get("销售净利率(%)", row2.get("净利率", "NA"))
                debt_ratio = row2.get("资产负债率(%)", row2.get("负债率", "NA"))
                roe = row2.get("净资产收益率(%)", row2.get("加权净资产收益率(%)", roe))
        except Exception:
            pass
        results.append(
            {
                "symbol": symbol,
                "name": "",
                "market_cap": _norm(market_cap),
                "pe_ttm": _norm(pe_ttm),
                "pb": _norm(pb),
                "roe": _norm(roe),
                "revenue_yoy": _norm(revenue_yoy),
                "profit_yoy": _norm(profit_yoy),
                "gross_margin": _norm(gross_margin),
                "net_margin": _norm(net_margin),
                "debt_ratio": _norm(debt_ratio),
                "cashflow_3y": "NA",
                "moat_notes": "NA",
            }
        )
    return results


def _fetch_financial_indicator(ak, settings: Settings, symbol: str):
    year = datetime.now().year
    for candidate in [year, year - 1, year - 2, 2020, 2015, 2010]:
        df = _retry(
            lambda: ak.stock_financial_analysis_indicator(
                symbol=symbol, start_year=str(candidate)
            ),
            settings.akshare_retries,
            settings.akshare_backoff_sec,
            settings.akshare_research_timeout_sec,
        )
        if df is not None and not df.empty:
            return df
    return None


def _norm(value: Any) -> Any:
    if value is None:
        return "NA"
    if isinstance(value, float) and math.isnan(value):
        return "NA"
    return value
