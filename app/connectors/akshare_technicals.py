from __future__ import annotations

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
            df = _retry(
                lambda: ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq"),
                settings.akshare_retries,
                settings.akshare_backoff_sec,
                settings.akshare_research_timeout_sec,
            )
            if df is None or df.empty:
                results.append(_empty(symbol))
                continue
            closes = df["收盘"].astype(float).tolist()
            highs = df["最高"].astype(float).tolist()
            lows = df["最低"].astype(float).tolist()
            ma20 = _sma(closes, 20)
            ma60 = _sma(closes, 60)
            rsi14 = _rsi(closes, 14)
            macd_val = _macd(closes)
            support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
            resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)
            trend = _trend(ma20, ma60)
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
                    "vol_ratio": "NA",
                    "breakout_note": "NA",
                }
            )
        except Exception:
            results.append(_empty(symbol))
    return results


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
