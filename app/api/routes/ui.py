from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def ui_index() -> str:
    return """
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>QuantaWatcher 控制台</title>
    <script src="https://unpkg.com/vue@3.4.31/dist/vue.global.prod.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
      :root {
        --bg: #f7f1e5;
        --panel: #ffffff;
        --text: #1f2328;
        --muted: #667084;
        --accent: #1b5f7a;
        --accent-soft: #e2f1f7;
        --accent-2: #f3b64a;
        --danger: #d64545;
        --success: #2f8f6b;
        --shadow: 0 20px 40px rgba(23, 31, 52, 0.08);
      }
      body {
        margin: 0;
        font-family: "Fira Sans", "HarmonyOS Sans", "Microsoft YaHei", sans-serif;
        background:
          radial-gradient(circle at 15% 10%, #fbf6ec, #f4ecdd 50%, #efe6d5 100%),
          linear-gradient(120deg, rgba(255,255,255,0.6), rgba(255,255,255,0));
        color: var(--text);
      }
      header {
        padding: 24px 32px 16px;
        border-bottom: 1px solid rgba(31,35,40,0.08);
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: center;
      }
      h1 {
        margin: 0;
        font-size: 24px;
        letter-spacing: 1px;
        font-family: "Source Han Serif SC", "Songti SC", "SimSun", serif;
      }
      .subhead { color: var(--muted); font-size: 13px; }
      .status-bar {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }
      .status-item {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(31,35,40,0.08);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 12px;
        display: inline-flex;
        gap: 8px;
        align-items: center;
      }
      .badge {
        padding: 2px 8px;
        border-radius: 999px;
        background: #eef2f5;
        color: #3a4757;
        font-weight: 600;
      }
      .badge.success { background: #e6f4ee; color: var(--success); }
      .badge.danger { background: #fde8e8; color: var(--danger); }
      .badge.running { background: #eaf2ff; color: #2f5fc0; }
      .container {
        padding: 22px 32px 32px;
        display: grid;
        grid-template-columns: 1.3fr 0.7fr;
        gap: 18px;
      }
      .card {
        background: var(--panel);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
        border: 1px solid rgba(31,35,40,0.06);
      }
      .card h2 {
        margin: 0 0 12px;
        font-size: 18px;
      }
      .toolbar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        align-items: center;
      }
      button {
        background: var(--accent);
        color: #fff;
        border: none;
        padding: 9px 14px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 13px;
      }
      button.secondary {
        background: var(--accent-2);
        color: #1a1a1a;
      }
      button.ghost {
        background: var(--accent-soft);
        color: var(--accent);
      }
      input {
        border: 1px solid rgba(31,35,40,0.1);
        border-radius: 10px;
        padding: 8px 10px;
        font-family: "Fira Sans", "HarmonyOS Sans", "Microsoft YaHei", sans-serif;
        font-size: 13px;
      }
      .muted { color: var(--muted); font-size: 12px; }
      .spinner {
        width: 14px; height: 14px; border: 2px solid #d9d2c6; border-top: 2px solid var(--accent);
        border-radius: 50%; display: inline-block; animation: spin 0.9s linear infinite; vertical-align: middle;
        margin-right: 6px;
      }
      .hidden { display: none; }
      @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid #f0f0f0; padding: 6px 4px; text-align: left; font-size: 13px; }
      th { color: #3a4757; font-weight: 600; }
      .markdown h1 { font-size: 20px; margin: 0 0 10px 0; }
      .markdown h2 { font-size: 16px; margin: 12px 0 6px 0; color: #234; }
      .markdown ul { margin: 6px 0 10px 18px; }
      .markdown li { margin: 4px 0; }
      .mono { font-family: Consolas, "Courier New", monospace; font-size: 12px; white-space: pre-wrap; }
      .pill {
        padding: 2px 8px;
        border-radius: 999px;
        background: #f1f4f8;
        font-size: 12px;
      }
      .pos { color: #d64545; font-weight: 600; }
      .neg { color: #2f5fc0; font-weight: 600; }
      .split {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
      @media (max-width: 1100px) { .container { grid-template-columns: 1fr; } }
      @media (max-width: 720px) {
        header { flex-direction: column; align-items: flex-start; }
        .split { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div id="app">
      <header>
        <div>
          <h1>QuantaWatcher 控制台</h1>
          <div class="subhead">晨报、行情速览与盘后提示词</div>
        </div>
        <div class="status-bar">
          <div class="status-item">
            <span>刷新状态</span>
            <span :class="['badge', statusBadge]">{{ statusLabel }}</span>
          </div>
          <div class="status-item">
            <span>数据源</span>
            <span class="pill">{{ status.source || '-' }}</span>
            <span v-if="status.cache_ts" class="pill">cache {{ status.cache_ts }}</span>
            <span v-if="status.degraded" class="pill">watchlist only</span>
            <span v-else-if="status.fallback_used" class="pill">fallback</span>
          </div>
          <div class="status-item">
            <span>研究数据</span>
            <span class="pill">{{ researchLabel }}</span>
          </div>
          <div class="status-item">
            <span>最后刷新</span>
            <span class="pill">{{ lastRefreshText }}</span>
          </div>
        </div>
      </header>
      <div class="container">
        <div class="card">
          <h2>晨报预览</h2>
          <div class="markdown" v-html="briefHtml"></div>
          <div class="muted">
            <span :class="['spinner', refreshing ? '' : 'hidden']"></span>
            {{ statusText }}
          </div>
          <div class="toolbar" style="margin-top:12px;">
            <button @click="refreshBrief" :disabled="refreshing">刷新晨报数据</button>
            <button class="secondary" @click="sendBrief">发送晨报</button>
            <button class="ghost" @click="loadPostClosePrompt">生成盘后提示词</button>
          </div>
          <div class="muted" style="margin-top:6px;">
            刷新优先拉取新浪全市场，其次缓存/AkShare/Eastmoney，最后才降级腾讯自选；研究数据可单独开关。
          </div>
          <div v-if="notes.length" style="margin-top:10px;">
            <div class="muted">数据提示：</div>
            <div class="muted" v-for="note in notes" :key="note">- {{ note }}</div>
          </div>
        </div>
        <div class="card">
          <h2>行情速览</h2>
          <div class="split">
            <div>
              <div class="muted" style="margin-bottom:6px;">涨幅榜</div>
              <table>
                <thead>
                  <tr><th>代码</th><th>名称</th><th>涨跌幅</th></tr>
                </thead>
                <tbody>
                  <tr v-if="!topGainers.length"><td colspan="3">暂无</td></tr>
                  <tr v-for="row in topGainers" :key="row.symbol">
                    <td>{{ row.symbol }}</td>
                    <td>{{ row.name || '-' }}</td>
                    <td :class="pctClass(row.pct_chg)">{{ fmtPct(row.pct_chg) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div>
              <div class="muted" style="margin-bottom:6px;">成交额榜</div>
              <table>
                <thead>
                  <tr><th>代码</th><th>名称</th><th>成交额</th></tr>
                </thead>
                <tbody>
                  <tr v-if="!topTurnover.length"><td colspan="3">暂无</td></tr>
                  <tr v-for="row in topTurnover" :key="row.symbol">
                    <td>{{ row.symbol }}</td>
                    <td>{{ row.name || '-' }}</td>
                    <td>{{ fmtAmount(row.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="card">
          <h2>自选内容</h2>
          <div class="toolbar" style="margin-bottom:10px;">
            <input v-model="symbolInput" placeholder="代码(如 000063)" />
            <input v-model="nameInput" placeholder="名称(可选)" />
            <button class="secondary" @click="addWatchlist">添加自选</button>
          </div>
          <table>
            <thead>
              <tr><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th><th>成交额</th></tr>
            </thead>
            <tbody>
              <tr v-if="!watchlist.length"><td colspan="5">暂无</td></tr>
              <tr v-for="row in watchlist" :key="row.symbol">
                <td>{{ row.symbol }}</td>
                <td>{{ row.name || '-' }}</td>
                <td>{{ fmt(row.last) }}</td>
                <td :class="pctClass(row.pct_chg)">{{ fmtPct(row.pct_chg) }}</td>
                <td>{{ fmtAmount(row.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card">
          <h2>盘后提示词</h2>
          <div class="mono">{{ postClosePrompt || '点击“生成盘后提示词”获取最新内容' }}</div>
          <div class="toolbar" style="margin-top:10px;">
            <button class="secondary" @click="copyPrompt">复制提示词</button>
          </div>
          <div class="muted">用于手动粘贴给大模型进行分析。</div>
        </div>
        <div class="card">
          <h2>盘后复盘</h2>
          <div class="markdown" v-html="postCloseHtml"></div>
          <div class="muted">
            <span :class="['spinner', postCloseRefreshing ? '' : 'hidden']"></span>
            {{ postCloseStatusText }}
          </div>
          <div class="toolbar" style="margin-top:12px;">
            <button @click="refreshPostClose" :disabled="postCloseRefreshing">刷新盘后数据</button>
            <button class="secondary" @click="sendPostClose">发送盘后复盘</button>
          </div>
        </div>
        <div class="card">
          <h2>报告参数</h2>
          <div class="toolbar" style="margin-bottom:10px; flex-wrap: wrap;">
            <input v-model="params.momentum_days" placeholder="动量窗口(如 5,20)" />
            <input v-model="params.abnormal_pct" placeholder="异常阈值(%)" />
            <input v-model="params.strong_pct" placeholder="强弱阈值(%)" />
            <input v-model="params.post_close_hour" placeholder="盘后小时(24h)" />
            <input v-model="params.post_close_minute" placeholder="盘后分钟" />
            <button class="secondary" @click="saveParams">保存参数</button>
          </div>
          <div class="muted">参数保存后会影响晨报/盘后复盘计算与定时。</div>
        </div>
      </div>
    </div>
    <script>
      const { createApp } = Vue;
      createApp({
        data() {
          return {
            briefHtml: '',
            statusText: '状态：未刷新',
            refreshing: false,
            watchlist: [],
            topGainers: [],
            topTurnover: [],
            notes: [],
            status: {},
            symbolInput: '',
            nameInput: '',
            postClosePrompt: '',
            postCloseHtml: '',
            postCloseStatus: {},
            postCloseRefreshing: false,
            postCloseStatusText: '状态：未刷新',
            params: {
              momentum_days: '5,20',
              abnormal_pct: '3',
              strong_pct: '2',
              post_close_hour: '15',
              post_close_minute: '30'
            }
          };
        },
        computed: {
          statusLabel() {
            const state = this.status.state || 'idle';
            if (state === 'running') return '运行中';
            if (state === 'success') return '成功';
            if (state === 'failed') return '失败';
            return '未刷新';
          },
          statusBadge() {
            const state = this.status.state || 'idle';
            if (state === 'running') return 'running';
            if (state === 'success') return 'success';
            if (state === 'failed') return 'danger';
            return '';
          },
          lastRefreshText() {
            const ts = this.status.ts;
            if (!ts) return '-';
            return ts.replace('T', ' ').replace('Z', '');
          },
          researchLabel() {
            const rs = this.status.research_state;
            if (!rs) return '-';
            if (rs === 'running') return '刷新中';
            if (rs === 'success') return '完成';
            if (rs === 'failed') return '失败';
            return '跳过';
          }
        },
        methods: {
          fmt(val) {
            if (val === null || val === undefined) return '-';
            const num = Number(val);
            if (Number.isFinite(num)) return num.toFixed(2);
            return String(val);
          },
          fmtPct(val) {
            if (val === null || val === undefined) return '-';
            const num = Number(val);
            if (Number.isFinite(num)) return num.toFixed(2) + '%';
            return String(val);
          },
          fmtAmount(val) {
            if (val === null || val === undefined) return '-';
            const num = Number(val);
            if (!Number.isFinite(num)) return String(val);
            if (num >= 1e8) return (num / 1e8).toFixed(2) + '亿';
            if (num >= 1e4) return (num / 1e4).toFixed(2) + '万';
            return num.toFixed(2);
          },
          pctClass(val) {
            const num = Number(val);
            if (!Number.isFinite(num)) return '';
            return num >= 0 ? 'pos' : 'neg';
          },
          async loadPreview() {
            try {
              const [briefResp, statusResp, paramsResp] = await Promise.all([
                fetch('/reports/morning-brief'),
                fetch('/reports/morning-brief/refresh/status'),
                fetch('/reports/params')
              ]);
              const data = await briefResp.json();
              this.briefHtml = marked.parse(data.content || '');
              const briefData = data.data || {};
              this.notes = briefData.notes || [];
              this.topGainers = briefData.top_gainers || [];
              this.topTurnover = briefData.top_turnover || [];
              if (briefData.watchlist && briefData.watchlist.length) {
                this.watchlist = briefData.watchlist;
              } else {
                const wl = await fetch('/watchlist');
                const wlData = await wl.json();
                this.watchlist = wlData.items || [];
              }
              if (statusResp.ok) {
                const statusData = await statusResp.json();
                this.status = statusData.status || {};
                this.statusText = this.status.state ? `状态：${this.status.state}` : '状态：未刷新';
              }
              if (paramsResp.ok) {
                const paramsData = await paramsResp.json();
                this.applyParams(paramsData.params || {});
              }
              await this.loadPostClose();
            } catch (err) {
              console.error(err);
              this.statusText = '状态：加载失败';
            }
          },
          async refreshBrief() {
            this.refreshing = true;
            this.statusText = '状态：刷新中...';
            try {
              const resp = await fetch('/reports/morning-brief/refresh', { method: 'POST' });
              const data = await resp.json();
              if (data.status === 'cached') {
                this.statusText = '状态：刷新过于频繁（使用缓存）';
                if (data.refresh_status) {
                  this.status = data.refresh_status;
                }
                await this.loadPreview();
                this.refreshing = false;
                return;
              }
              await this.pollStatus();
            } catch (err) {
              console.error(err);
              this.statusText = '状态：刷新失败';
              this.refreshing = false;
            }
          },
          async pollStatus() {
            let finished = false;
            for (let i = 0; i < 30; i++) {
              const resp = await fetch('/reports/morning-brief/refresh/status');
              const data = await resp.json();
              this.status = data.status || {};
              const state = this.status.state || 'idle';
              if (state === 'success') {
                this.statusText = `状态：已刷新 watchlist=${this.status.watchlist_count || 0} ` +
                  `涨幅榜=${this.status.top_gainers_count || 0} 成交额榜=${this.status.top_turnover_count || 0}`;
                await this.loadPreview();
                finished = true;
                break;
              }
              if (state === 'failed') {
                this.statusText = '状态：刷新失败';
                alert('刷新失败: ' + (this.status.error || 'unknown'));
                await this.loadPreview();
                finished = true;
                break;
              }
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
            if (!finished) {
              this.statusText = '状态：刷新超时（保留旧内容）';
              await this.loadPreview();
            }
            this.refreshing = false;
          },
          async sendBrief() {
            await fetch('/reports/morning-brief/send', { method: 'POST' });
            alert('已发送（如使用本地 notifier，请检查 data/outbox）');
          },
          async loadPostClosePrompt() {
            const resp = await fetch('/reports/post-close/prompt');
            const data = await resp.json();
            this.postClosePrompt = data.prompt || '';
          },
          async loadPostClose() {
            try {
              const resp = await fetch('/reports/post-close');
              const data = await resp.json();
              this.postCloseHtml = marked.parse(data.content || '');
            } catch (err) {
              console.error(err);
              this.postCloseStatusText = '状态：加载失败';
            }
          },
          async refreshPostClose() {
            this.postCloseRefreshing = true;
            this.postCloseStatusText = '状态：刷新中...';
            try {
              const resp = await fetch('/reports/post-close/refresh', { method: 'POST' });
              const data = await resp.json();
              if (data.status === 'cached') {
                this.postCloseStatusText = '状态：刷新过于频繁（使用缓存）';
                await this.loadPostClose();
                this.postCloseRefreshing = false;
                return;
              }
              await this.pollPostCloseStatus();
            } catch (err) {
              console.error(err);
              this.postCloseStatusText = '状态：刷新失败';
              this.postCloseRefreshing = false;
            }
          },
          async pollPostCloseStatus() {
            let finished = false;
            for (let i = 0; i < 30; i++) {
              const resp = await fetch('/reports/post-close/refresh/status');
              const data = await resp.json();
              this.postCloseStatus = data.status || {};
              const state = this.postCloseStatus.state || 'idle';
              if (state === 'success') {
                this.postCloseStatusText = `状态：已刷新 watchlist=${this.postCloseStatus.watchlist_count || 0}` +
                  ` 异常=${this.postCloseStatus.abnormal_count || 0}`;
                await this.loadPostClose();
                finished = true;
                break;
              }
              if (state === 'failed') {
                this.postCloseStatusText = '状态：刷新失败';
                alert('盘后刷新失败: ' + (this.postCloseStatus.error || 'unknown'));
                await this.loadPostClose();
                finished = true;
                break;
              }
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
            if (!finished) {
              this.postCloseStatusText = '状态：刷新超时（保留旧内容）';
              await this.loadPostClose();
            }
            this.postCloseRefreshing = false;
          },
          async sendPostClose() {
            await fetch('/reports/post-close/send', { method: 'POST' });
            alert('已发送（如使用本地 notifier，请检查 data/outbox）');
          },
          applyParams(params) {
            if (params.momentum_days) {
              this.params.momentum_days = Array.isArray(params.momentum_days)
                ? params.momentum_days.join(',')
                : String(params.momentum_days);
            }
            if (params.abnormal_pct !== undefined) this.params.abnormal_pct = String(params.abnormal_pct);
            if (params.strong_pct !== undefined) this.params.strong_pct = String(params.strong_pct);
            if (params.post_close_hour !== undefined) this.params.post_close_hour = String(params.post_close_hour);
            if (params.post_close_minute !== undefined) this.params.post_close_minute = String(params.post_close_minute);
          },
          async saveParams() {
            const payload = {
              momentum_days: String(this.params.momentum_days || '')
                .split(',')
                .map(item => item.trim())
                .filter(Boolean)
                .map(item => Number(item)),
              abnormal_pct: Number(this.params.abnormal_pct),
              strong_pct: Number(this.params.strong_pct),
              post_close_hour: Number(this.params.post_close_hour),
              post_close_minute: Number(this.params.post_close_minute)
            };
            await fetch('/reports/params', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            });
            alert('参数已保存');
          },
          async copyPrompt() {
            if (!this.postClosePrompt.trim()) {
              alert('没有可复制内容');
              return;
            }
            await navigator.clipboard.writeText(this.postClosePrompt);
            alert('已复制提示词');
          },
          async addWatchlist() {
            const symbol = this.symbolInput.trim();
            const name = this.nameInput.trim();
            if (!symbol) {
              alert('请输入代码');
              return;
            }
            await fetch('/watchlist', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ symbol, name })
            });
            this.symbolInput = '';
            this.nameInput = '';
            await this.loadPreview();
          }
        },
        mounted() {
          this.loadPreview();
        }
      }).mount('#app');
    </script>
  </body>
</html>
"""
