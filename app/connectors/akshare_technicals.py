from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.connectors.akshare_snapshot import _require_akshare, _retry
from app.core.config import Settings


def fetch_technicals(symbols: List[str]) -> List[Dict[str, Any]]:
    if not symbols:
        return []
    ak = _require_akshare()
    settings = Settings()
    results: List[Dict[str, Any]] = []
    for symbol in symbols:
        try:
            df = _fetch_hist(ak, settings, symbol)
            if df is None or df.empty:
                results.append(_empty(symbol))
                continue
            closes, highs, lows, amounts = _extract_ohlc(df)
            ma20 = _sma(closes, 20)
            ma60 = _sma(closes, 60)
            rsi14 = _rsi(closes, 14)
            macd_val = _macd(closes)
            support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
            resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)
            trend = _trend(ma20, ma60)
            vol_ratio = _vol_ratio(amounts, 20)
            results.append(
                {
                    "symbol": symbol,
                    "name": "",
                    "trend": trend,
                    "support": support,
                    "resistance": resistance,
                    "ma20": ma20,
                    "ma60": ma60,
                    "rsi14": rsi14,
                    "macd": macd_val,
                    "vol_ratio": vol_ratio,
                    "breakout_note": "NA",
                }
            )
        except Exception:
            results.append(_empty(symbol))
    return results


def _fetch_hist(ak, settings: Settings, symbol: str):
    try:
        return _retry(
            lambda: ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq"),
            settings.akshare_retries,
            settings.akshare_backoff_sec,
            settings.akshare_research_timeout_sec,
        )
    except Exception:
        tx_symbol = _to_tx_symbol(symbol)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=420)
        return _retry(
            lambda: ak.stock_zh_a_hist_tx(
                symbol=tx_symbol,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
                timeout=settings.akshare_research_timeout_sec,
            ),
            settings.akshare_retries,
            settings.akshare_backoff_sec,
            settings.akshare_research_timeout_sec,
        )


def _extract_ohlc(df):
    if "收盘" in df.columns:
        closes = df["收盘"].astype(float).tolist()
        highs = df["最高"].astype(float).tolist()
        lows = df["最低"].astype(float).tolist()
        amounts = df["成交额"].astype(float).tolist() if "成交额" in df.columns else []
        return closes, highs, lows, amounts
    closes = df["close"].astype(float).tolist() if "close" in df.columns else []
    highs = df["high"].astype(float).tolist() if "high" in df.columns else []
    lows = df["low"].astype(float).tolist() if "low" in df.columns else []
    amounts = df["amount"].astype(float).tolist() if "amount" in df.columns else []
    return closes, highs, lows, amounts


def _to_tx_symbol(symbol: str) -> str:
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith("6") or symbol.startswith("5") or symbol.startswith("9"):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _vol_ratio(amounts: List[float], window: int) -> Any:
    if not amounts:
        return "NA"
    if len(amounts) < window + 1:
        return amounts[-1] / (sum(amounts) / len(amounts)) if amounts else "NA"
    avg = sum(amounts[-window:]) / window
    if avg == 0:
        return "NA"
    return amounts[-1] / avg


def _empty(symbol: str) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "name": "",
        "trend": "NA",
        "support": "NA",
        "resistance": "NA",
        "ma20": "NA",
        "ma60": "NA",
        "rsi14": "NA",
        "macd": "NA",
        "vol_ratio": "NA",
        "breakout_note": "NA",
    }


def _sma(series: List[float], window: int) -> float:
    if len(series) < window:
        return series[-1]
    return sum(series[-window:]) / window


def _rsi(series: List[float], period: int) -> float:
    if len(series) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(-period, 0):
        delta = series[i] - series[i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(-delta)
    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _ema(series: List[float], span: int) -> float:
    if not series:
        return 0.0
    alpha = 2 / (span + 1)
    ema = series[0]
    for value in series[1:]:
        ema = alpha * value + (1 - alpha) * ema
    return ema


def _macd(series: List[float]) -> float:
    if len(series) < 26:
        return 0.0
    ema12 = _ema(series, 12)
    ema26 = _ema(series, 26)
    return ema12 - ema26


def _trend(ma20: float, ma60: float) -> str:
    if ma20 > ma60:
        return "UP"
    if ma20 < ma60:
        return "DOWN"
    return "FLAT"
