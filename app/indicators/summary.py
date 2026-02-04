from __future__ import annotations

from typing import Any, Dict, List

from app.indicators.history import get_momentum


def compute_rankings(watchlist: List[Dict[str, Any]], top_n: int) -> Dict[str, List[Dict[str, Any]]]:
    top_gainers = _top_by_key(watchlist, "pct_chg", top_n, reverse=True)
    top_losers = _top_by_key(watchlist, "pct_chg", top_n, reverse=False)
    top_turnover = _top_by_key(watchlist, "amount", top_n, reverse=True)
    return {
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "top_turnover": top_turnover,
    }


def compute_risk_notes(watchlist: List[Dict[str, Any]]) -> List[str]:
    if not watchlist:
        return ["watchlist 为空，无法评估风险"]
    pct_values = [item.get("pct_chg") for item in watchlist]
    pct_nums = [v for v in pct_values if isinstance(v, (int, float))]
    if not pct_nums:
        return ["缺少涨跌幅数据，风险评估降级"]
    neg_ratio = sum(1 for v in pct_nums if v < 0) / max(len(pct_nums), 1)
    avg_pct = sum(pct_nums) / len(pct_nums)
    notes: List[str] = []
    if neg_ratio >= 0.6:
        notes.append(f"watchlist 下跌占比偏高：{neg_ratio:.0%}")
    if avg_pct <= -1.0:
        notes.append(f"watchlist 平均涨跌幅偏弱：{avg_pct:.2f}%")
    if not notes:
        notes.append("watchlist 整体波动可控")
    return notes


def compute_momentum_indicators(
    history_payload: Dict[str, Any],
    days_list: List[int],
    top_n: int,
) -> Dict[str, List[Dict[str, Any]]]:
    momentum: Dict[str, List[Dict[str, Any]]] = {}
    for days in days_list:
        results = get_momentum(history_payload, days)
        momentum[f"{days}d"] = results[:top_n]
    return momentum


def compute_abnormal_moves(
    watchlist: List[Dict[str, Any]],
    threshold_pct: float,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in watchlist:
        pct = item.get("pct_chg")
        if pct is None:
            continue
        try:
            pct_val = float(pct)
        except Exception:
            continue
        if abs(pct_val) >= threshold_pct:
            results.append(item)
    results.sort(key=lambda item: abs(_safe_num(item.get("pct_chg"))), reverse=True)
    return results


def classify_strength(
    watchlist: List[Dict[str, Any]],
    strong_pct: float,
) -> Dict[str, List[Dict[str, Any]]]:
    strong: List[Dict[str, Any]] = []
    weak: List[Dict[str, Any]] = []
    neutral: List[Dict[str, Any]] = []
    for item in watchlist:
        pct = _safe_num(item.get("pct_chg"))
        if pct is None:
            neutral.append(item)
        elif pct >= strong_pct:
            strong.append(item)
        elif pct <= -strong_pct:
            weak.append(item)
        else:
            neutral.append(item)
    return {"strong": strong, "weak": weak, "neutral": neutral}


def _top_by_key(items: List[Dict[str, Any]], key: str, limit: int, reverse: bool) -> List[Dict[str, Any]]:
    fallback = float("-inf") if reverse else float("inf")
    return sorted(items, key=lambda item: _safe_num(item.get(key), fallback), reverse=reverse)[:limit]


def _safe_num(value: Any, fallback: float = float("-inf")) -> float:
    try:
        return float(value)
    except Exception:
        return fallback
