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
    <title>QuantaWatcher 晨报控制台</title>
    <style>
      :root {
        --bg: #f6f4ef;
        --panel: #ffffff;
        --text: #1a1a1a;
        --muted: #666;
        --accent: #1c6e8c;
        --accent-2: #f2c14e;
      }
      body {
        margin: 0;
        font-family: "Source Han Serif SC", "Noto Serif SC", "SimSun", serif;
        background: linear-gradient(120deg, #f6f4ef 0%, #f1efe7 100%);
        color: var(--text);
      }
      header {
        padding: 24px 32px;
        border-bottom: 1px solid #e6e0d6;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      h1 { margin: 0; font-size: 22px; }
      .container { padding: 24px 32px; display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; }
      .card { background: var(--panel); border: 1px solid #e6e0d6; border-radius: 12px; padding: 16px; box-shadow: 0 6px 18px rgba(0,0,0,0.05); }
      .card h2 { margin: 0 0 12px 0; font-size: 18px; }
      textarea {
        width: 100%; min-height: 220px; resize: vertical; border: 1px solid #d9d2c6;
        border-radius: 10px; padding: 12px; font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
      }
      button {
        background: var(--accent);
        color: #fff; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer;
        margin-right: 8px;
      }
      button.secondary { background: var(--accent-2); color: #1a1a1a; }
      .row { margin-top: 12px; }
      pre {
        white-space: pre-wrap; background: #faf8f2; padding: 12px; border-radius: 10px; border: 1px solid #e6e0d6;
        max-height: 420px; overflow: auto;
      }
      .muted { color: var(--muted); font-size: 12px; }
      @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <header>
      <h1>QuantaWatcher 晨报控制台</h1>
      <div class="muted">本地界面，直接操作晨报内容与刷新</div>
    </header>
    <div class="container">
      <div class="card">
        <h2>晨报预览</h2>
        <pre id="preview">加载中...</pre>
        <div class="row">
          <button onclick="refreshBrief()">刷新晨报数据</button>
          <button class="secondary" onclick="sendBrief()">发送晨报</button>
        </div>
        <div class="muted">刷新会拉取 A 股行情（AkShare）。发送将走当前 notifier。</div>
      </div>
      <div class="card">
        <h2>手动编辑草稿</h2>
        <textarea id="draft"></textarea>
        <div class="row">
          <button onclick="saveDraft()">保存草稿</button>
          <button class="secondary" onclick="loadPreview()">重新加载预览</button>
        </div>
        <div class="muted">草稿优先于结构化数据。留空则使用结构化数据生成。</div>
      </div>
    </div>
    <script>
      async function loadPreview() {
        const resp = await fetch('/reports/morning-brief');
        const data = await resp.json();
        document.getElementById('preview').textContent = data.content || '';
      }
      async function saveDraft() {
        const content = document.getElementById('draft').value || '';
        if (!content.trim()) { alert('草稿不能为空'); return; }
        await fetch('/reports/morning-brief', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content })
        });
        await loadPreview();
      }
      async function refreshBrief() {
        await fetch('/reports/morning-brief/refresh', { method: 'POST' });
        await loadPreview();
      }
      async function sendBrief() {
        await fetch('/reports/morning-brief/send', { method: 'POST' });
        alert('已发送（如使用本地 notifier，请检查 data/outbox）');
      }
      loadPreview();
    </script>
  </body>
</html>
"""
