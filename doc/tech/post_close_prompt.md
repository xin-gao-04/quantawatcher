# 盘后复盘提示词（草案）

目标：用盘后数据生成 LLM 提示词，让模型输出三类投资计划的盈利置信度（0-100），并明确价值/技术/市场证据链与数据覆盖度。

## 数据来源与形态
输入建议使用结构化 JSON（示例见 `data/post_close_payload.json`），关键字段：
- `date`：交易日期
- `horizon`：关注周期（短线/中线）
- `market`：市场概况（指数/流动性/风险偏好）
- `watchlist`：自选行情（symbol/name/last/pct_chg/amount）
- `fundamentals`：价值面字段（PE/PB/ROE/成长/利润率/负债）
- `technicals`：技术面字段（趋势/支撑/压力/均线/RSI/MACD/量比）
- `top_gainers` / `top_turnover`：涨幅榜/成交额榜
- `sectors`：板块/主题摘要
- `events`：盘中事件摘要
- `risk_flags`：风险标记（宏观/情绪/监管）
- `constraints`：交易约束（仓位/风险限制）
- `notes`：备注（如数据源/降级说明）

## 自选补充数据（建议手工维护或脚本写入）
- `data/watchlist_fundamentals.json`：价值面字段
- `data/watchlist_technicals.json`：技术面字段

## 自动填充流程（当前实现）
- 刷新晨报时自动调用 AkShare 获取技术面与价值面数据
- 结果写入上述两个 JSON 文件，并用于提示词生成

## 提示词生成逻辑
使用 `app/reports/post_close_prompt.py` 中 `build_post_close_prompt(payload)` 生成文本：
- 输出严格为 JSON（无额外文本）
- 缺失字段用 `NA` 或 “无”，并汇总到 `missing_data`
- 三类计划：保守/平衡/进取，允许 targets 为空（建议观望）
- 每个目标必须包含 evidence（fundamental/technical/market/events/data_gaps）
- 置信度要求与证据覆盖度挂钩，并输出 `data_quality_score`
- 输出必须符合 JSON Schema（见下方）

## 输出 JSON Schema
```
{
  "type": "object",
  "required": ["plans", "overall_risk_level", "overall_rationale", "missing_data", "data_quality_score"],
  "properties": {
    "data_quality_score": { "type": "number", "minimum": 0, "maximum": 1 },
    "plans": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {
        "type": "object",
        "required": ["plan_type", "targets", "position_range", "risk_control", "confidence", "confidence_basis"],
        "properties": {
          "plan_type": { "type": "string", "enum": ["保守", "平衡", "进取"] },
          "targets": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["symbol", "name", "reason", "confidence", "evidence"],
              "properties": {
                "symbol": { "type": "string" },
                "name": { "type": "string" },
                "reason": { "type": "string" },
                "confidence": { "type": "number", "minimum": 0, "maximum": 100 },
                "evidence": {
                  "type": "object",
                  "required": ["fundamental", "technical", "market", "events", "data_gaps"],
                  "properties": {
                    "fundamental": { "type": "array", "items": { "type": "string" } },
                    "technical": { "type": "array", "items": { "type": "string" } },
                    "market": { "type": "array", "items": { "type": "string" } },
                    "events": { "type": "array", "items": { "type": "string" } },
                    "data_gaps": { "type": "array", "items": { "type": "string" } }
                  }
                }
              }
            }
          },
          "position_range": { "type": "string" },
          "risk_control": { "type": "string" },
          "confidence": { "type": "number", "minimum": 0, "maximum": 100 },
          "confidence_basis": {
            "type": "object",
            "required": ["data_coverage", "key_evidence", "key_risks"],
            "properties": {
              "data_coverage": { "type": "string" },
              "key_evidence": { "type": "array", "items": { "type": "string" } },
              "key_risks": { "type": "array", "items": { "type": "string" } }
            }
          }
        }
      }
    },
    "overall_risk_level": { "type": "string", "enum": ["低", "中", "高"] },
    "overall_rationale": { "type": "string" },
    "missing_data": { "type": "array", "items": { "type": "string" } }
  }
}
```

## 示例：生成提示词
```
python - <<'PY'
from app.reports.post_close_prompt import build_post_close_prompt
import json
payload = json.load(open('data/post_close_payload.json', 'r', encoding='utf-8'))
print(build_post_close_prompt(payload))
PY
```

## 示例：提示词片段（截取）
```
输出要求：
1) 仅输出 JSON，不要附加解释或正文。
2) 给出三类计划：保守 / 平衡 / 进取。
3) 每类计划给出：目标品种清单、仓位建议、风险控制、盈利置信度(0-100)。
4) 每个目标必须给出 evidence：fundamental/technical/market/events/data_gaps。
5) 所有判断必须引用下方数据证据；缺数据必须写“依据不足”。
6) 若风险显著，允许给出“建议观望”的计划（targets 可为空数组）。
7) 输出最后给出：总体市场风险等级(低/中/高)与主要依据。
```

## 下一步扩展建议
- 引入板块强弱与资金流
- 引入个股历史区间（近 5/10/20 日）
- 事件触发原因与回测命中率摘要
