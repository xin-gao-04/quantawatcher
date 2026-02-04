from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.indicators.summary import (
    compute_abnormal_moves,
    classify_strength,
    compute_momentum_indicators,
    compute_rankings,
    compute_risk_notes,
)


def build_post_close_data(
    watchlist_snapshot: List[Dict[str, Any]],
    history_payload: Dict[str, Any] | None,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    top_n = int(params.get("post_close_top_n", 10))
    abnormal_pct = float(params.get("abnormal_pct", 3.0))
    strong_pct = float(params.get("strong_pct", 2.0))
    rankings = compute_rankings(watchlist_snapshot, top_n)
    abnormal_moves = compute_abnormal_moves(watchlist_snapshot, abnormal_pct)
    suggestions = classify_strength(watchlist_snapshot, strong_pct)
    risk_notes = compute_risk_notes(watchlist_snapshot)
    indicators: Dict[str, Any] = {}
    if history_payload:
        momentum_days = params.get("momentum_days", [5, 20])
        indicators["momentum"] = compute_momentum_indicators(history_payload, momentum_days, top_n)
    return {
        "date": today,
        "watchlist": watchlist_snapshot,
        "rankings": rankings,
        "abnormal_moves": abnormal_moves,
        "suggestions": suggestions,
        "risk_notes": risk_notes,
        "indicators": indicators,
        "notes": [],
    }
