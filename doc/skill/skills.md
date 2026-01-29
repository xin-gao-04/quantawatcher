# QuantaWatcher 技术栈与技能图谱

## 核心目标
- 本地常驻服务：定时采集、指标计算、事件检测、推送到指定通道，支持插件化扩展。

## 技术栈 Skills
- Backend/API：Python 3.11+，FastAPI（API + Web 控制台），Uvicorn/Gunicorn 运行。
- 调度与并发：APScheduler/自研调度，异步 I/O (asyncio)；任务隔离与冷却窗口控制。
- 存储：SQLite 起步，PostgreSQL/TimescaleDB 生产；Redis 用于缓存、队列、分布式锁。
- 数据采集：HTTP/SDK 拉取行情与基础数据；请求重试、超时、降级与幂等写入。
- 指标与规则：指标计算引擎（板块热度、动量、量能突变、区间突破、风险过滤）；规则/事件引擎（阈值触发、去重、聚合、冷却）。
- 插件体系：Collector/Indicator/Strategy/Notifier/Report 插件接口；init/run 生命周期；元信息声明（name/version/deps/schedule/permissions）。
- 推送通道：Notifier 抽象 send(message, severity, tags)；至少实现企业微信 Webhook/邮件/桌面通知之一，含重试与失败告警。
- Web 控制台：运行状态、事件列表、配置面板（watchlist/板块/阈值/通道），日志入口。

## 工程与运维 Skills
- 配置管理：.env + config.example.env（gitignore）；区分本地/生产；密钥不入库。
- 可靠性：超时/重试/退避，限流，任务级隔离，崩溃自恢复；结构化日志与关键指标（采集耗时、失败率、事件/推送量、队列积压）。
- 测试：pytest 覆盖指标/规则单测，存储与 Notifier 集成测试使用 fake/mocker；测试数据隔离。
- 部署：Windows Service 或 systemd 托管；本地单机（API+worker）与服务器版（PostgreSQL+Redis+多 worker）。
- 安全与合规：外部数据源权限与条款审查；网络访问白名单；最小权限访问令牌。
