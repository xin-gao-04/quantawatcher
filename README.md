以下是一份可直接用于立项与推进的“需求与开发文档”（偏 PRD + 技术方案合并版）。内容基于你当前描述与我前一轮给出的架构思路整理而成，默认以“本地常驻服务 + 分层架构 + 插件化扩展”为主线。

需求开发文档
项目名称：A 股板块与标的监控推送系统（本地常驻，插件化）
版本：v0.1
作者：Xin
日期：2026-01-28（America/Los_Angeles）

1. 背景与问题陈述
   你作为 A 股投资者，希望随时随地获取关注板块、热门板块的有效指标与盘中异动信息，用于辅助决策。当前痛点主要是信息分散、人工筛选成本高、盘中异动难以及时捕捉、无法形成可复盘的信号体系。
   目标是建设一个长期运行在本地电脑或服务器上的服务，利用定时器与事件检测机制主动推送关键信息，并通过插件化方式持续扩展功能，例如晨报汇总、重点标的收集、盘中异动提示等。

2. 目标与范围
   2.1 目标（必须达成）
   A. 常驻运行：在 Windows 本地或服务器上长期稳定运行，支持开机自启与崩溃自恢复。
   B. 指标体系：对“关注板块 + 热门板块 + 关注标的”持续产出可解释的核心指标。
   C. 事件驱动推送：交易时段捕捉异动并推送，非交易时段产出晨报与复盘摘要。
   D. 插件化扩展：允许通过插件新增数据源、指标、扫描器、推送通道与策略规则，而不修改核心服务。
   E. 可追溯：所有推送与计算结果可落库可回放，支持复盘与误报率评估。

2.2 非目标（本期明确不做）
A. 自动交易与下单接口（只做信号与提醒，不做交易执行）。
B. 交易所直连超低延迟行情（秒级以下、Level2 等），第一阶段按分钟级或数秒级快照实现。
C. 重型桌面客户端（第一阶段以本地 Web 控制台为主，后续可再做桌面 UI）。

3. 用户画像与使用场景
   3.1 用户画像
   核心用户：个人 A 股投资者，愿意基于数据与信号做决策，能接受系统部署与轻度配置。

3.2 核心场景
S1 晨间（开盘前）：自动推送晨报，包含昨日板块强弱、重点标的表现与当日关注提示。
S2 盘中（交易时段）：对关注标的、板块共振、热门板块异常变化做实时提示，避免错过关键窗口。
S3 盘后（收盘后）：生成当日事件回放与信号命中初步统计，帮助优化阈值与规则。
S4 临时关注：用户临时添加某只股票或板块进入观察列表，立即纳入监控与推送。

4. 功能需求
   4.1 基础模块
   4.1.1 Watchlist 管理

* 支持管理关注标的列表：股票代码、名称、标签（例如 AI、商业航天）、优先级、监控开关。
* 支持管理关注板块列表：行业板块、概念板块、自定义板块。
* 支持临时观察列表：带 TTL（过期自动移除），用于热门板块成分股自动加入观察。

验收：

* 能通过 Web 控制台增删改查标的与板块。
* 变更立即生效或在下个调度周期生效（可选）。

4.1.2 数据采集（行情与基础数据）

* 交易时段快照采集：按设定频率拉取 watchlist 与重点板块成分股的行情快照。
* 日线与复权数据：用于趋势与波动计算。
* 财务与估值（慢数据）：收盘后或每日一次刷新。

验收：

* 支持至少一个可用数据源完成闭环。
* 对数据源异常有重试与降级策略，不能拖垮主进程。

4.1.3 指标计算（第一阶段指标集）
第一阶段建议最小可用指标（可配置开关）：
A. 板块热度类

* 板块涨跌幅、领涨股数量、跌幅股数量
* 板块成交额变化（相对前一交易日、相对 N 日均值）
  B. 动量与异动类
* 1 分钟、5 分钟涨跌速率
* 量能突变（成交额/量比相对短窗均值偏离）
* 区间突破（短窗价格突破最近区间上沿）
  C. 风险提示类
* 盘中急跌/大盘状态过滤（基础版：指数跌幅阈值）

验收：

* 指标计算结果可落库，且每条推送能引用对应指标值与触发原因。

4.1.4 事件检测与规则引擎

* 将指标转化为事件 Event，并按规则决定是否推送。
* 规则能力（第一阶段）：
  1）阈值触发（例如 1 分钟涨幅超过 X）
  2）去重（同一标的同类事件在冷却窗口内只推一次）
  3）聚合（板块内触发比例超过 Y 才推“板块共振”事件）
* 事件类型（第一阶段）：

  * PriceSpike（价格异动）
  * VolumeSpike（量能异动）
  * SectorResonance（板块共振）
  * HotSectorUpdate（热门板块变更）

验收：

* 在模拟或真实盘中数据下，事件能稳定产生且推送不刷屏。
* 事件日志可查询，可回放。

4.1.5 推送通道

* 推送通道抽象为 Notifier：send(message, severity, tags)
* 第一阶段至少落地一种通道：企业微信 webhook 或邮件或桌面通知（三选一先完成闭环）。
* 推送内容必须包含：标的/板块、触发原因、关键指标数值、发生时间、建议关注点（简短）。

验收：

* 盘中事件可在 1 个调度周期内到达用户端。
* 推送失败可重试，连续失败可告警。

4.1.6 本地 Web 控制台

* 状态面板：服务运行状态、最近任务执行情况、数据源健康、推送计数。
* 事件面板：事件列表、筛选、查看详情（包含原始指标与触发规则）。
* 配置面板：watchlist、板块列表、规则阈值、调度频率、推送通道配置。
* 运维面板：日志查看入口、导出配置、备份与恢复（可后置）。

验收：

* 能完成日常配置与排障的基本入口，不依赖修改代码。

4.2 插件化需求
4.2.1 插件类型
A. CollectorPlugin：新增数据源或新增外部事件源。
B. IndicatorPlugin：新增指标计算模块。
C. StrategyPlugin：新增事件检测策略与规则组合。
D. NotifierPlugin：新增推送通道（企业微信、Telegram、短信等）。
E. ReportPlugin：新增晨报/盘后报表生成器。

4.2.2 插件接口规范（示例）

* init(config)
* run(context) 或 on_schedule(trigger)
* 输出必须写入统一的数据模型或事件模型
* 需要声明插件元信息：name, version, dependencies, schedule, permissions（访问外网、文件、数据库等）

验收：

* 核心服务不改代码即可加载新插件并生效（热加载可后置，先支持重启加载）。

4.3 晨报与盘后报表
4.3.1 晨报（开盘前）
内容建议：

* 昨日板块强弱榜（关注板块 + 热门板块）
* 关注标的昨日表现与触发事件回放
* 今日风险提示（大盘环境摘要，基于前一日与隔夜信息的基础信号）
  输出：Markdown/HTML，推送到同一通道

验收：

* 每个交易日固定时间产出，缺数据时给出降级版本，不空白。

4.3.2 盘后复盘

* 当日事件统计（按类型、按标的、按板块）
* 粗粒度命中评估（事件后 30/60/240 分钟收益方向统计，作为迭代依据）
  说明：评估口径必须可配置，避免被单一指标误导。

5. 非功能需求
   5.1 稳定性与容错

* 数据源失败不影响主服务，任务级隔离。
* 重试与退避策略，限流与缓存。
* 崩溃自恢复（服务托管方式支持自动重启）。
* 数据落库采用事务或幂等写入，避免重复事件。

5.2 性能与延迟

* 第一阶段目标：分钟级或数秒级快照即可，端到端推送延迟小于一个采集周期。
* 采集与计算应分离线程或异步任务，避免阻塞 Web 控制台。

5.3 可观测性

* 日志：结构化日志，包含 task_id、plugin、symbol、duration、error。
* 指标：采集耗时、失败率、推送量、事件量、队列积压。
* 健康检查：/health，包含数据库、数据源、推送通道状态。

5.4 安全与合规

* 凭据管理：API token、webhook 密钥不得明文硬编码，使用环境变量或本地加密存储。
* 网络访问可配置开关与白名单。
* 对数据源条款与使用许可保持关注，生产化尽量采用稳定合规的数据服务。

6. 技术架构与模块划分
   6.1 总体架构（分层）

* Data Connectors：对接多数据源，统一数据模型
* Storage：行情、指标、事件、配置
* Indicator Engine：指标计算
* Event/Rule Engine：事件生成、去重、聚合、过滤
* Scheduler/Worker：定时任务与队列任务
* Notifiers：推送通道
* Web Console：配置与观测
* Plugin Loader：插件注册与生命周期管理

6.2 部署形态
A. 本地单机版：一个进程或少量进程（API + worker），SQLite 起步。
B. 服务器版：PostgreSQL/TimescaleDB + Redis + worker 扩展，多进程更稳定。
托管方式：Windows Service 或使用进程守护工具；Linux 可用 systemd。

7. 数据模型（最小集合）

* symbols：symbol, name, tags, priority, enabled
* sectors：sector_id, name, type(industry/concept/custom), enabled
* snapshots：ts, symbol, last, pct_chg, volume, amount, extra
* bars：ts, symbol, ohlcv, amount, timeframe
* fundamentals：symbol, report_date, pe_ttm, pb, rev_yoy, profit_yoy
* indicators：ts, entity_type(symbol/sector), entity_id, key, value, window
* events：ts, type, entity, score, message, payload, dedup_key
* tasks_runs：task_name, start_ts, end_ts, status, error
* config_versions：version, content, updated_ts

8. 开发计划与里程碑（按可交付闭环推进）
   M0 规格冻结（1 到 2 天）

* 确定实时粒度、首批指标清单、首个推送通道
* 确定首个数据源组合
  交付：v0.0 需求冻结文档与配置草案

M1 MVP 常驻服务 + 晨报（约 1 周量级，视工程熟练度）

* FastAPI + Scheduler + Storage（SQLite 或 Postgres）
* 数据采集跑通（至少一个源）
* 晨报插件跑通并推送
  交付：每日可稳定产出晨报，系统可长期运行

M2 盘中异动引擎（约 1 周量级）

* watchlist 快照轮询
* 异动规则 v1 + 去重冷却
* 事件落库 + 推送闭环
  交付：盘中能稳定提示异动，且可复盘

M3 热门板块自动发现（约 1 周量级）

* 板块热度排行
* 临时观察列表 TTL
  交付：能提示你未关注但突然走强的板块与代表性标的

M4 插件体系固化 + 运维观测（约 1 周量级）

* 插件加载与规范
* 指标、日志、健康检查完善
  交付：可持续扩展而不重构

9. 风险清单与应对
   R1 数据源不稳定或规则限制

* 应对：Connector 抽象 + 缓存限流 + 多源可切换；关键数据考虑商业数据源。
  R2 异动推送噪声过高
* 应对：冷却、聚合、市场状态过滤；盘后评估迭代阈值。
  R3 维护成本上升
* 应对：插件化隔离，统一数据模型与事件模型；强制可观测性。
  R4 用户真实需求漂移
* 应对：先用最小指标闭环交付，再按复盘数据迭代，不做一次性大全。

10. 验收标准（v0.1）

* 服务可连续运行 5 个交易日，无需人工干预即可产出晨报。
* 盘中对 watchlist 能产出并推送至少 2 类异动事件，且同一标的不会在冷却窗口内重复刷屏。
* 每条推送都能在控制台中找到对应 event 记录，包含触发指标与阈值。
* 插件至少实现晨报插件与异动插件两种，且通过配置可启停。

11. 待确认问题（你只要回答这三项就能进入 M0 规格冻结）
    Q1 盘中实时粒度：5 秒、15 秒、60 秒三选一。
    Q2 指标优先级：板块热度、资金、估值、新闻事件，按重要性排序。
    Q3 首个推送通道：企业微信 webhook、邮件、桌面通知、Telegram 四选一。

如果你愿意，我可以在你回答 Q1 到 Q3 后，直接把 M0 规格冻结落到“具体指标清单 + 事件阈值默认值 + 数据源选择 + 数据表字段细化 + 插件接口签名”，形成 v0.2 版本文档，工程师可以按它拆任务开干。

---

## 工程化落地（从 M0 开始）

### 阶段成果与技术积累
- 阶段文档：`doc/phases/M0.md`、`doc/phases/M1.md`、`doc/phases/M1.1.md`、`doc/phases/M1.2.md`、`doc/phases/M1.3.md`、`doc/phases/M2.md`、`doc/phases/M2.1.md`、`doc/phases/M3.md`
- 技术积累：`doc/tech/tech_log.md`
- 数据源说明：`doc/tech/data_sources.md`
- 盘后复盘提示词：`doc/tech/post_close_prompt.md`

### 本地开发命令（happy path）
- 安装依赖：`pip install -r requirements.txt`
- 若遇到代理/SSL 问题：`$env:NO_PROXY='*'; pip install -r requirements.txt`
- 启动服务：`python -m uvicorn app.api.main:app --reload`
- Windows 快捷启动：`powershell -File scripts/dev.ps1`
- 网络诊断：`powershell -File scripts/diagnose_network.ps1`
- 运行测试：`PYTHONPATH=. python -m pytest -q`

### 晨报手动流程（可立即使用）
- 保存晨报草稿：`POST /reports/morning-brief`
- 获取晨报内容：`GET /reports/morning-brief`
- 手动发送晨报：`POST /reports/morning-brief/send`
- 清空草稿（使用结构化数据）：`DELETE /reports/morning-brief`
- 脚本发送：`powershell -File scripts/send_morning_brief.ps1 -File data/morning_brief.md`

### 盘后复盘流程（结构化）
- 生成盘后数据：`POST /reports/post-close/refresh`
- 获取盘后报告：`GET /reports/post-close`
- 获取盘后数据：`GET /reports/post-close/data`
- 发送盘后报告：`POST /reports/post-close/send`
- 刷新状态：`GET /reports/post-close/refresh/status`

### Web 界面（无需 API 工具）
- 访问：`http://127.0.0.1:8000/` 或 `http://127.0.0.1:8000/ui`
- 若不需要草稿：设置 `QW_ENABLE_MORNING_BRIEF_DRAFT=false`（默认）
 - 刷新后状态会显示 watchlist/榜单数量，如失败会提示原因
- 盘后提示词：点击“生成盘后提示词”可直接复制
- 盘后复盘：点击“刷新盘后数据 / 发送盘后复盘”
- 参数设置：在“报告参数”面板调整动量窗口、异常阈值与盘后时间

### 晨报结构化数据（可选）
- 数据文件：`data/morning_brief_data.json`
- 读取数据：`GET /reports/morning-brief/data`
- 保存数据：`POST /reports/morning-brief/data`
- 当前数据源：本地 JSON 文件（后续可替换为外部数据源）
 - 晨报正文会输出：涨幅榜 / 成交额榜（若有数据）

### 盘后结构化数据（可选）
- 数据文件：`data/post_close_report_data.json`
- 读取数据：`GET /reports/post-close/data`

### A股行情数据源（最快路径）
- 数据源：AkShare（`pip install akshare`）
- watchlist：`data/watchlist.json`
- 刷新晨报数据：`POST /reports/morning-brief/refresh`
- 脚本刷新：`powershell -File scripts/refresh_morning_brief.ps1`
- 如访问外网需要代理：设置 `QW_HTTP_PROXY` / `QW_HTTPS_PROXY`（例如 `http://127.0.0.1:6275`）
- AkShare 是否使用代理：`QW_AKSHARE_USE_PROXY=true`（若 AkShare 接口被代理阻断可设为 false）
- 若 AkShare 失败：自动降级为腾讯行情（仅 watchlist）
- AkShare 重试：`QW_AKSHARE_RETRIES` 与 `QW_AKSHARE_BACKOFF_SEC` 可调大
- AkShare 超时：`QW_AKSHARE_SNAPSHOT_TIMEOUT_SEC` / `QW_AKSHARE_RESEARCH_TIMEOUT_SEC`
- AkShare 现货来源顺序：`QW_AKSHARE_SPOT_SOURCES=em,sina`（按顺序尝试）
- 市场快照来源优先级：`QW_MARKET_SNAPSHOT_SOURCES=sina_market,cache,akshare,eastmoney_direct,tencent`
- 快照缓存：`QW_MARKET_SNAPSHOT_CACHE_PATH` / `QW_MARKET_SNAPSHOT_CACHE_TTL_SEC`（秒，0 表示不过期）
- Eastmoney 直连开关：`QW_EASTMONEY_DIRECT_ENABLED=true`
- Eastmoney 主机：`QW_EASTMONEY_HOSTS=82.push2.eastmoney.com,push2.eastmoney.com`
- Eastmoney 分页/限速：`QW_EASTMONEY_PAGE_SIZE` / `QW_EASTMONEY_MAX_PAGES` / `QW_EASTMONEY_PAGE_DELAY_SEC`
- Eastmoney 请求头：`QW_EASTMONEY_USER_AGENT` / `QW_EASTMONEY_COOKIE`
- Eastmoney 自动 Cookie：`QW_EASTMONEY_AUTO_COOKIE` / `QW_EASTMONEY_FORCE_COOKIE` / `QW_EASTMONEY_COOKIE_VERIFY` / `QW_EASTMONEY_COOKIE_URL` / `QW_EASTMONEY_COOKIE_PATH` / `QW_EASTMONEY_COOKIE_TTL_SEC`
- Sina 全市场源：`QW_SINA_MARKET_URL` / `QW_SINA_MARKET_NODE` / `QW_SINA_MARKET_PAGE_SIZE` / `QW_SINA_MARKET_MAX_PAGES` / `QW_SINA_MARKET_PAGE_DELAY_SEC`
- Sina 请求头：`QW_SINA_MARKET_USER_AGENT`
- Sina 重试：`QW_SINA_MARKET_RETRIES` / `QW_SINA_MARKET_BACKOFF_SEC`
- Sina 并发与完整性：`QW_SINA_MARKET_CONCURRENCY` / `QW_SINA_MARKET_MIN_ROWS`
- 腾讯行情超时/重试：`QW_TENCENT_TIMEOUT_SEC` / `QW_TENCENT_RETRIES` / `QW_TENCENT_BACKOFF_SEC`
- 禁用降级：`QW_DISABLE_FALLBACK=true`（失败则返回错误）
- 研究数据刷新开关：`QW_RESEARCH_ENABLED`（关闭可显著降低慢网络影响）
- 研究数据抽样数量：`QW_RESEARCH_MAX_SYMBOLS`

### 报告参数与排程
- 报告参数文件：`QW_REPORT_PARAMS_PATH`（默认 `data/report_params.json`）
- 盘后报告时间：`QW_POST_CLOSE_HOUR` / `QW_POST_CLOSE_MINUTE`
- 盘后数据刷新时间：`QW_POST_CLOSE_REFRESH_HOUR` / `QW_POST_CLOSE_REFRESH_MINUTE`
- 盘后数据文件：`QW_POST_CLOSE_DATA_PATH`
- 盘后刷新状态：`QW_POST_CLOSE_REFRESH_STATUS_PATH`
- watchlist 历史缓存：`QW_WATCHLIST_HISTORY_PATH`
- 刷新状态：`GET /reports/morning-brief/refresh/status`
- watchlist 示例：
  ```json
  [
    {"symbol": "000001", "name": "平安银行"},
    {"symbol": "600519", "name": "贵州茅台"}
  ]
  ```

### 环境变量与配置
- 示例：`.env.example`
- 统一前缀：`QW_`

### 自选研究补充数据
- 价值面：`data/watchlist_fundamentals.json`
- 技术面：`data/watchlist_technicals.json`

### 自选管理（Web）
- 在页面“自选内容”处输入代码/名称可添加
- API：`GET /watchlist`, `POST /watchlist`, `DELETE /watchlist/{symbol}`
