---
name: quantawatcher
description: Build or extend the QuantaWatcher local always-on A-share monitoring service (FastAPI + scheduler + indicators + event rules + notifiers + plugin system). Use for architecture, PRDs, implementation plans, scaffolding code, and safe productionization steps.
metadata:
  short-description: QuantaWatcher engineering workflow and templates
---

# QuantaWatcher Skill

## When to use this skill
Use this skill when the user asks to design, implement, refactor, or productionize any part of QuantaWatcher, including:
- data connectors, polling, retry/timeout/backoff, rate limiting
- indicators, rule/event engine, dedup/cooldown/aggregation
- plugin interfaces and loading, plugin isolation strategy
- storage schema, migrations, config/versioning
- morning brief, post-close reports, replay/evals
- post-close prompt generation for LLM analysis
- deployment (Windows service/systemd), observability, alerting

Do NOT use this skill for general stock recommendations or discretionary trading advice. This system outputs signals and operational telemetry, not investment guarantees.

## Operating assumptions (must state if changed)
- Python 3.11+, FastAPI for API + local web console
- MVP: SQLite; Production: PostgreSQL/TimescaleDB; Redis optional for cache/locks/queues
- Real-time granularity is snapshot-based (seconds to minutes), not exchange-level streaming
- No auto-trading; signals only

If the user’s requirements conflict with these, propose minimal changes and call out tradeoffs.

## Clarify-first checklist (ask only if missing)
1) Intraday sampling interval: 5s / 15s / 60s
2) Primary notification channel: WeCom webhook / email / desktop / Telegram
3) Priority indicator groups: sector heat / flow(资金) / valuation / news-events
4) Data source constraints: free vs paid, stability requirements, legal/compliance constraints

If not provided, default to 60s + WeCom + sector heat first.

## System blueprint (target architecture)
Implement these layers with strict boundaries:
1) Data Connectors: fetch market snapshots/bars/fundamentals/calendar; normalize to internal models
2) Storage: snapshots, bars, indicators, events, config versions, task runs; ensure idempotent writes
3) Indicator Engine: pure functions; deterministic outputs; unit-testable
4) Event & Rule Engine: threshold rules, dedup keys, cooldown, aggregation; produce Event objects
5) Scheduler/Workers: trading-session aware scheduling; isolate slow tasks; optional queue workers
6) Notifiers: send(message, severity, tags) + retry and failure alert
7) Web Console/API: manage watchlist/sectors/rules/schedules; view events; health endpoints
8) Plugin System: Collector/Indicator/Strategy/Notifier/Report plugins with lifecycle init/run

## Data semantics (must implement early)
- Trading calendar and session windows: pre-open, open, lunch break, close, post-close
- Market state filters: index drop/risk-off mode can suppress or raise thresholds
- Event dedup: (event_type, entity_id, rule_id, window_bucket) -> dedup_key
- Cooldown: per entity + per rule; prevent spam

## Minimum viable deliverables (MVP definition of done)
MVP is done when all are true:
1) Runs as a long-lived service with restart safety
2) Produces a daily morning brief (Markdown) and sends it
3) During trading session, polls watchlist snapshots and emits at least two event types
4) Every push maps to a persisted Event record with trigger explanation and key metric values
5) Web console can edit watchlist and rule thresholds; changes take effect predictably

## Implementation workflow (Codex should follow)
Step 1: Write a short plan
- Identify which layer(s) are touched
- List new/changed data models and migrations
- List APIs/endpoints and configuration keys
- Definition of done + test strategy
- Create or update phase deliverable doc under `doc/phases/` and append to `doc/tech/tech_log.md`

Step 2: Scaffold or modify code incrementally
- Prefer small commits and keep functions pure in Indicator layer
- Add schema migrations (Alembic if Postgres) when tables change
- Add structured logging and metrics for new jobs

Step 3: Add tests
- Unit tests: indicator functions and rule evaluation with fixed fixtures
- Integration tests: storage writes and notifier via fake/mocker
- Include at least one replay test for a fixed time window

Step 4: Run and validate
- Provide commands to run locally (dev) and in service mode
- Validate: dedup/cooldown works, no push spam, failures are visible

## Documentation outputs (required)
- Each phase must produce a short deliverable in `doc/phases/` with scope, defaults, and verifiable exits
- Append technical accumulation notes to `doc/tech/tech_log.md`

## Templates (reuse, do not reinvent)
### Suggested repository structure
- app/
  - api/ (FastAPI routes, web console)
  - core/ (models, calendar, config, logging)
  - connectors/ (data sources)
  - indicators/ (pure computations)
  - rules/ (event detection, dedup, cooldown, aggregation)
  - plugins/ (interfaces + loader)
  - notifiers/ (channels)
  - scheduler/ (jobs, triggers, queues)
  - storage/ (db models, repositories, migrations)
  - reports/ (morning brief, post-close)
- tests/
- scripts/ (optional operational CLI helpers)
- .env.example

### Plugin interfaces (contract)
CollectorPlugin:
- init(config, services)
- run(context) -> emits normalized data or external events

IndicatorPlugin:
- init(config, services)
- compute(context, data) -> indicator records

StrategyPlugin:
- init(config, services)
- evaluate(context, indicators, data) -> Event list

NotifierPlugin:
- init(config, services)
- send(message, severity, tags) -> delivery result

ReportPlugin:
- init(config, services)
- generate(context) -> markdown/html artifact + optional events

All plugins must declare:
- name, version, api_version, deps, schedule, permissions (network/db/files)

## Non-functional requirements (must enforce)
Reliability:
- timeout/retry/backoff; rate limiting; graceful degradation
- task isolation: slow connector must not block API
- crash recovery: service manager + safe startup checks

Observability:
- structured logs with task_id, plugin, symbol/sector, duration_ms, error
- metrics: fetch latency, failure rate, event count, push count, queue depth
- health: /health includes db, redis, connectors, notifier reachability

Security/compliance:
- secrets via env or local secret store; never commit tokens
- network whitelist for outbound requests
- document data source terms and operational constraints

## Output style
When producing implementation output:
- Provide a short “what changed” summary
- Provide commands to run/tests
- Provide config keys and defaults
- Avoid long speculative market commentary

## Post-close prompt guidance
- Collect data for LLM prompts as structured JSON
- Prompt should request three plans (conservative/balanced/aggressive) with confidence scores (0-100)

## Trigger examples (for better auto-invocation)
- “为 QuantaWatcher 加一个盘中异动规则：量能突变 + 冷却窗口”
- “把 SQLite 切到 Postgres 并加 Alembic 迁移”
- “设计插件系统接口并给出加载器实现”
- “加一个晨报插件，输出 Markdown 并推送到企业微信”
