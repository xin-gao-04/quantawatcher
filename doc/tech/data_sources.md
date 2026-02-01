# 数据源说明（当前实现）

本文档描述 QuantaWatcher 当前使用的数据源、调用入口与字段含义，便于后续扩展与替换。

## 1) AkShare（主数据源）

### 调用入口
- 连接器：`app/connectors/akshare_snapshot.py`
- 主要函数：
  - `fetch_market_snapshot(symbols, top_n)`：返回 watchlist + 榜单
  - `fetch_watchlist_snapshot(symbols)`：仅 watchlist 快照
  - `fetch_market_top_movers(top_n)`：仅榜单

### 具体调用的 AkShare 接口
- `stock_zh_a_spot_em()`（优先）
- `stock_zh_a_spot()`（备用）

### 当前抽取字段（统一字段名）
从 AkShare 返回表中抽取并统一为：
- `symbol`：股票代码（如 `000001`/`600519`）
- `name`：股票名称
- `last`：最新价
- `pct_chg`：涨跌幅（百分比）
- `amount`：成交额

### 数据输出形态（快照）
`fetch_market_snapshot` 返回：
```json
{
  "watchlist": [
    {"symbol": "000001", "name": "平安银行", "last": 12.3, "pct_chg": 1.2, "amount": 123456789}
  ],
  "top_gainers": [
    {"symbol": "600519", "name": "贵州茅台", "last": 1401.0, "pct_chg": 2.3, "amount": 987654321}
  ],
  "top_turnover": [
    {"symbol": "601899", "name": "紫金矿业", "last": 40.1, "pct_chg": -1.0, "amount": 27139836259}
  ]
}
```

### 相关配置（影响 AkShare 行为）
- `QW_HTTP_PROXY` / `QW_HTTPS_PROXY`：代理配置
- `QW_AKSHARE_RETRIES`：重试次数
- `QW_AKSHARE_BACKOFF_SEC`：重试退避
- `QW_AKSHARE_SPOT_SOURCES`：现货来源顺序（`em,sina`）
- `QW_AKSHARE_USE_PROXY`：AkShare 是否使用代理
- `QW_MARKET_SNAPSHOT_SOURCES`：快照来源优先级（`sina_market,cache,akshare,eastmoney_direct,tencent`）
- `QW_MARKET_SNAPSHOT_CACHE_PATH`：快照缓存文件
- `QW_MARKET_SNAPSHOT_CACHE_TTL_SEC`：快照缓存有效期（秒）
- `QW_DISABLE_FALLBACK`：禁用降级

### 文档在哪里
AkShare 是第三方库，官方文档与函数说明请参考其项目文档（搜索关键词：`AkShare stock_zh_a_spot_em`）。

### 代理说明
大陆环境通常无需代理；若外网被限制或 SSL 失败，可设置：
- `QW_HTTP_PROXY` / `QW_HTTPS_PROXY`

---

## 2) 腾讯行情（降级）

### 调用入口
- 连接器：`app/connectors/tencent_quote.py`
- 主要函数：`fetch_quotes(symbols)`

### 实际访问的接口
- `https://qt.gtimg.cn/q=...`

### 解析字段
当前从返回文本解析：
- `symbol`：股票代码
- `name`：股票名称
- `last`：最新价
- `pct_chg`：通过 `last` 与 `prev_close` 计算
- `amount`：当前不提供（为 `null`）

### 文档在哪里
腾讯行情接口为公开格式（文本响应），无正式文档。解析逻辑见 `app/connectors/tencent_quote.py` 中 `_parse_response`。

---

## 3) Eastmoney 直连（补全）

### 调用入口
- 连接器：`app/connectors/eastmoney_spot.py`
- 主要函数：`fetch_eastmoney_spot(settings)`

### 实际访问的接口
- `https://{host}/api/qt/clist/get`

### 说明
- 作为 AkShare 失败时的补全来源（分页抓取 + 限速）。
- 可通过 `QW_EASTMONEY_*` 配置请求头、分页大小与延迟。

### 相关配置
- `QW_EASTMONEY_DIRECT_ENABLED`
- `QW_EASTMONEY_HOSTS`
- `QW_EASTMONEY_TIMEOUT_SEC`
- `QW_EASTMONEY_PAGE_SIZE`
- `QW_EASTMONEY_MAX_PAGES`
- `QW_EASTMONEY_PAGE_DELAY_SEC`
- `QW_EASTMONEY_USER_AGENT`
- `QW_EASTMONEY_COOKIE`
- `QW_EASTMONEY_AUTO_COOKIE`
- `QW_EASTMONEY_FORCE_COOKIE`
- `QW_EASTMONEY_COOKIE_VERIFY`
- `QW_EASTMONEY_COOKIE_URL`
- `QW_EASTMONEY_COOKIE_PATH`
- `QW_EASTMONEY_COOKIE_TTL_SEC`

---

## 4) Sina 全市场（补全）

### 调用入口
- 连接器：`app/connectors/sina_market.py`
- 主要函数：`fetch_sina_market(settings)`

### 实际访问的接口
- `http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData`

### 说明
- 作为 Eastmoney 不可达时的补全来源。
- 使用分页抓取全市场行情。

### 相关配置
- `QW_SINA_MARKET_URL`
- `QW_SINA_MARKET_NODE`
- `QW_SINA_MARKET_PAGE_SIZE`
- `QW_SINA_MARKET_MAX_PAGES`
- `QW_SINA_MARKET_PAGE_DELAY_SEC`
- `QW_SINA_MARKET_TIMEOUT_SEC`
- `QW_SINA_MARKET_RETRIES`
- `QW_SINA_MARKET_BACKOFF_SEC`
- `QW_SINA_MARKET_CONCURRENCY`
- `QW_SINA_MARKET_MIN_ROWS`
- `QW_SINA_MARKET_SORT`
- `QW_SINA_MARKET_ASC`
- `QW_SINA_MARKET_USER_AGENT`

---

## 5) 结构化晨报数据

### 文件来源
`data/morning_brief_data.json`

### 生成逻辑
由 `app/reports/brief_builder.py` 结合行情快照写入，字段包括：
- `highlights` / `sectors` / `symbols` / `risks` / `notes`
- `watchlist`（自选列表行情）
- `top_gainers` / `top_turnover`（榜单）

### 文档在哪里
晨报生成逻辑见 `app/reports/brief_builder.py` 与 `app/reports/morning_brief.py`。

---

## 6) 自选研究数据（价值面 + 技术面）

### 文件来源
- 价值面：`data/watchlist_fundamentals.json`
- 技术面：`data/watchlist_technicals.json`

### 字段示例
价值面字段（示例）：
- `pe_ttm` / `pb` / `roe`
- `revenue_yoy` / `profit_yoy`
- `gross_margin` / `net_margin`
- `debt_ratio` / `cashflow_3y` / `moat_notes`

技术面字段（示例）：
- `trend` / `support` / `resistance`
- `ma20` / `ma60`
- `rsi14` / `macd` / `vol_ratio`

### 文档在哪里
提示词生成会读取上述文件，详见：
- `app/reports/watchlist_research.py`
- `app/reports/post_close_payload_builder.py`
