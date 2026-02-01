from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def build_post_close_prompt(payload: Dict[str, Any]) -> str:
    date = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    horizon = payload.get("horizon", "短线(1-5天) / 中线(1-4周)")
    watchlist = payload.get("watchlist", [])
    fundamentals = payload.get("fundamentals", [])
    technicals = payload.get("technicals", [])
    top_gainers = payload.get("top_gainers", [])
    top_turnover = payload.get("top_turnover", [])
    events = payload.get("events", [])
    sectors = payload.get("sectors", [])
    market = payload.get("market", {})
    constraints = payload.get("constraints", [])
    risk_flags = payload.get("risk_flags", [])
    notes = payload.get("notes", [])

    return "\n".join(
        [
            "你是投研助手，请基于以下盘后数据输出不同投资计划的盈利置信度。",
            "核心目标：在价值面 + 技术面合力下给出可执行的多计划方案。",
            "",
            "输出要求：",
            "1) 仅输出 JSON，不要附加解释或正文。",
            "2) 给出三类计划：保守 / 平衡 / 进取。",
            "3) 每类计划给出：目标品种清单、仓位建议、风险控制、盈利置信度(0-100)。",
            "4) 每个目标必须给出 evidence：fundamental/technical/market/events/data_gaps。",
            "5) 所有判断必须引用下方数据证据；缺数据必须写“依据不足”。",
            "6) 若风险显著，允许给出“建议观望”的计划（targets 可为空数组）。",
            "7) 输出最后给出：总体市场风险等级(低/中/高)与主要依据。",
            "",
            "输出必须严格符合以下 JSON Schema：",
            _json_schema(),
            "",
            "评分与证据提示：",
            "- 价值面：PE/PB/ROE/成长/利润率/负债率等。",
            "- 技术面：趋势/支撑/压力/均线/RSI/MACD/量比。",
            "- 若仅有行情快照/榜单，置信度应下调。",
            "- 置信度需体现证据覆盖度：缺少价值面或技术面时，单标的置信度不超过40。",
            "- data_quality_score 取 0-1，衡量整体数据覆盖度（缺失越多越低）。",
            "",
            f"日期：{date}",
            f"关注周期：{horizon}",
            "",
            "【市场概况】",
            *(_format_kv(market) if market else ["- 无"]),
            "",
            "【watchlist】",
            *_format_items(watchlist),
            "",
            "【价值面（基本面）】",
            *_format_fundamentals(fundamentals),
            "",
            "【技术面（技术指标）】",
            *_format_technicals(technicals),
            "",
            "【板块/主题】",
            *_format_items(sectors),
            "",
            "【涨幅榜】",
            *_format_items(top_gainers),
            "",
            "【成交额榜】",
            *_format_items(top_turnover),
            "",
            "【事件】",
            *_format_items(events),
            "",
            "【风险标记】",
            *([f"- {n}" for n in risk_flags] if risk_flags else ["- 无"]),
            "",
            "【约束条件】",
            *([f"- {n}" for n in constraints] if constraints else ["- 无"]),
            "",
            "【备注】",
            *([f"- {n}" for n in notes] if notes else ["- 无"]),
            "",
            "【输出格式要求】",
            "计划: 保守|平衡|进取",
            "- 目标品种清单: [代码 名称 理由(价值/技术证据) + evidence]",
            "- 仓位建议: 数字区间(%)",
            "- 风险控制: 止损/止盈/触发条件",
            "- 盈利置信度: 0-100",
        ]
    )


def _format_items(items: List[Dict[str, Any]]) -> List[str]:
    if not items:
        return ["- 无"]
    lines: List[str] = []
    for item in items:
        symbol = item.get("symbol", "-")
        name = item.get("name", "")
        last = item.get("last")
        pct = item.get("pct_chg")
        amount = item.get("amount")
        lines.append(
            "- {symbol} {name} last={last} pct={pct} amount={amount}".format(
                symbol=symbol,
                name=name,
                last=_fmt(last),
                pct=_fmt(pct),
                amount=_fmt(amount),
            )
        )
    return lines


def _format_kv(data: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for key, value in data.items():
        lines.append(f"- {key}: {_fmt(value)}")
    return lines


def _format_fundamentals(items: List[Dict[str, Any]]) -> List[str]:
    if not items:
        return ["- 无"]
    lines: List[str] = []
    for item in items:
        lines.append(
            "- {symbol} {name} PE(TTM)={pe} PB={pb} ROE={roe} 收入YoY={rev} 利润YoY={profit} 毛利={gm} 净利={nm} 负债率={debt}".format(
                symbol=item.get("symbol", "-"),
                name=item.get("name", ""),
                pe=_fmt(item.get("pe_ttm")),
                pb=_fmt(item.get("pb")),
                roe=_fmt(item.get("roe")),
                rev=_fmt(item.get("revenue_yoy")),
                profit=_fmt(item.get("profit_yoy")),
                gm=_fmt(item.get("gross_margin")),
                nm=_fmt(item.get("net_margin")),
                debt=_fmt(item.get("debt_ratio")),
            )
        )
    return lines


def _format_technicals(items: List[Dict[str, Any]]) -> List[str]:
    if not items:
        return ["- 无"]
    lines: List[str] = []
    for item in items:
        lines.append(
            "- {symbol} {name} 趋势={trend} 支撑={support} 压力={resistance} MA20={ma20} MA60={ma60} RSI14={rsi} MACD={macd} 量比={vol}".format(
                symbol=item.get("symbol", "-"),
                name=item.get("name", ""),
                trend=_fmt(item.get("trend")),
                support=_fmt(item.get("support")),
                resistance=_fmt(item.get("resistance")),
                ma20=_fmt(item.get("ma20")),
                ma60=_fmt(item.get("ma60")),
                rsi=_fmt(item.get("rsi14")),
                macd=_fmt(item.get("macd")),
                vol=_fmt(item.get("vol_ratio")),
            )
        )
    return lines


def _json_schema() -> str:
    return (
        "{\n"
        "  \"type\": \"object\",\n"
        "  \"required\": [\"plans\", \"overall_risk_level\", \"overall_rationale\", \"missing_data\", \"data_quality_score\"],\n"
        "  \"properties\": {\n"
        "    \"data_quality_score\": {\"type\": \"number\", \"minimum\": 0, \"maximum\": 1},\n"
        "    \"plans\": {\n"
        "      \"type\": \"array\",\n"
        "      \"minItems\": 3,\n"
        "      \"maxItems\": 3,\n"
        "      \"items\": {\n"
        "        \"type\": \"object\",\n"
        "        \"required\": [\"plan_type\", \"targets\", \"position_range\", \"risk_control\", \"confidence\", \"confidence_basis\"],\n"
        "        \"properties\": {\n"
        "          \"plan_type\": {\"type\": \"string\", \"enum\": [\"保守\", \"平衡\", \"进取\"]},\n"
        "          \"targets\": {\n"
        "            \"type\": \"array\",\n"
        "            \"items\": {\n"
        "              \"type\": \"object\",\n"
        "              \"required\": [\"symbol\", \"name\", \"reason\", \"confidence\", \"evidence\"],\n"
        "              \"properties\": {\n"
        "                \"symbol\": {\"type\": \"string\"},\n"
        "                \"name\": {\"type\": \"string\"},\n"
        "                \"reason\": {\"type\": \"string\"},\n"
        "                \"confidence\": {\"type\": \"number\", \"minimum\": 0, \"maximum\": 100},\n"
        "                \"evidence\": {\n"
        "                  \"type\": \"object\",\n"
        "                  \"required\": [\"fundamental\", \"technical\", \"market\", \"events\", \"data_gaps\"],\n"
        "                  \"properties\": {\n"
        "                    \"fundamental\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
        "                    \"technical\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
        "                    \"market\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
        "                    \"events\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
        "                    \"data_gaps\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}\n"
        "                  }\n"
        "                }\n"
        "              }\n"
        "            }\n"
        "          },\n"
        "          \"position_range\": {\"type\": \"string\"},\n"
        "          \"risk_control\": {\"type\": \"string\"},\n"
        "          \"confidence\": {\"type\": \"number\", \"minimum\": 0, \"maximum\": 100},\n"
        "          \"confidence_basis\": {\n"
        "            \"type\": \"object\",\n"
        "            \"required\": [\"data_coverage\", \"key_evidence\", \"key_risks\"],\n"
        "            \"properties\": {\n"
        "              \"data_coverage\": {\"type\": \"string\"},\n"
        "              \"key_evidence\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
        "              \"key_risks\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}\n"
        "            }\n"
        "          }\n"
        "        }\n"
        "      }\n"
        "    },\n"
        "    \"overall_risk_level\": {\"type\": \"string\", \"enum\": [\"低\", \"中\", \"高\"]},\n"
        "    \"overall_rationale\": {\"type\": \"string\"},\n"
        "    \"missing_data\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}\n"
        "  }\n"
        "}\n"
    )


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
