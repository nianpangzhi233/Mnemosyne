# Web Dashboard 开发计划

## 目标

将 Streamlit Dashboard 的纸质感外观 + 功能迁移为纯 HTML + JS 静态页面，调 REST API 获取数据，部署到 GitHub Pages 供评委直接访问。

---

## 原子任务

### T1: 创建 HTML 骨架

- 新建 `scripts/dashboard/web/index.html`
- 复制 `v8_ui.py` 中的 `NOTEBOOK_CSS` 全部 CSS 到 `<style>` 内，零修改
- 搭建与现有 Dashboard 完全一致的 HTML 结构：topbar → hero → metrics → grid(6 sections) → footer
- 纯静态，无数据，手动填充 mock 数据验证外观一致
- **验收**：浏览器打开 index.html，外观与 Streamlit 截图一致

### T2: 数据层 — fetch 封装

- 新建 `scripts/dashboard/web/api.js`
- 封装 `fetchAPI(endpoint)` 函数，baseURL 可配置（默认 `http://127.0.0.1:8979/api/v8`）
- 封装 6 个数据获取函数：
  - `fetchHealth()` → `GET /api/v8/health`
  - `fetchEvents(limit)` → `GET /api/v8/records/raw_events?limit=N`
  - `fetchCandidates(limit)` → `GET /api/v8/records/candidates?limit=N`
  - `fetchEvidence(limit)` → `GET /api/v8/records/evidence?limit=N`
  - `fetchMemories(limit)` → `GET /api/v8/memories?limit=N`
  - `fetchContextPacks(limit)` → `GET /api/v8/records/context_pack_runs?limit=N`
- 错误处理：API 不可用时显示"API 未连接"提示，页面不白屏
- **验收**：启动 REST API 后，浏览器控制台调用 `fetchHealth()` 返回正确数据

### T3: 渲染层 — 数据绑定

- 新建 `scripts/dashboard/web/render.js`
- 将 `v8_ui.py` 中的 6 个 `_build_*` 函数翻译为 JS，输出 HTML 字符串
  - `_build_events` → `renderEvents(rows)`
  - `_build_candidates` → `renderCandidates(rows)`
  - `_build_evidence` → `renderEvidence(rows)`
  - `_build_memories` → `renderMemories(rows)`
  - `_build_contexts` → `renderContexts(rows)`
  - `_build_reasons` → `renderReasons(rows)`（从 context_pack_runs 的 rejected 中统计）
- `renderDashboard(data)` 主函数：拼 metrics HTML + 6 个 section HTML，注入 DOM
- 翻译辅助函数：`esc()`, `snip()`, `pill()`, `reasonLabel()`, `polarityLabel()`
- **验收**：数据加载后页面内容与 Streamlit 版本一致

### T4: 交互层 — 刷新 + 自动刷新

- 刷新按钮绑定 `loadAndRender()` 
- 页面加载时自动调用一次 `loadAndRender()`
- 可选：每 30 秒自动刷新（页面可见时才刷，用 `visibilitychange` 事件）
- **验收**：点刷新按钮数据更新；自动刷新不报错

### T5: 脱机模式 — 嵌入 mock 数据

- 当 REST API 不可用时，使用嵌入的 mock 数据渲染页面
- mock 数据来自 `v8/scripts/functional_smoke.py` 中的真实测试数据
- 页面顶部显示黄色提示条："演示数据 — 启动 REST API 查看实时数据"
- **验收**：不启动 API，直接打开 HTML 文件能看到完整 Dashboard（带提示条）

### T6: GitHub Pages 部署配置

- 创建 `.github/workflows/deploy-dashboard.yml`
- 触发条件：push to main 且 `scripts/dashboard/web/` 有变更
- 构建步骤：将 `scripts/dashboard/web/` 复制到 gh-pages 分支根目录
- README 中 Dashboard 截图旁加一行："在线演示：https://nianpangzhi233.github.io/Mnemosyne/"
- **验收**：push 后 https://nianpangzhi233.github.io/Mnemosyne/ 可访问，展示 mock 数据

### T7: README 更新

- 更新 Dashboard 段落：加在线 Demo 链接
- 更新截图（用 Web Dashboard 的新截图替换 Streamlit 截图）
- 保留 Streamlit 启动说明作为本地开发选项
- **验收**：README 中有在线链接 + 新截图 + Streamlit 备选说明

---

## 不在范围内

- 不做写操作（Dashboard 保持只读）
- 不做用户认证
- 不做响应式移动端适配（现有 CSS 已有基本 media query）
- 不做 WebSocket 实时推送（用轮询或手动刷新）

## 依赖

- T2 依赖 REST API 已运行（开发时用 mock）
- T3 依赖 T1 + T2
- T5 独立，可与 T3 并行
- T6 依赖 T1-T5 全部完成
- T7 依赖 T6

## 预估工作量

| 任务 | 时间 |
|------|------|
| T1: HTML 骨架 | 30 分钟 |
| T2: fetch 封装 | 20 分钟 |
| T3: 渲染层 | 1 小时（6 个函数翻译） |
| T4: 交互层 | 15 分钟 |
| T5: 脱机模式 | 30 分钟 |
| T6: GitHub Pages | 30 分钟 |
| T7: README 更新 | 15 分钟 |
| **合计** | **约 3 小时** |

## 关键文件

- `scripts/dashboard/web/index.html` — 主页面
- `scripts/dashboard/web/api.js` — API 封装
- `scripts/dashboard/web/render.js` — 渲染逻辑
- `.github/workflows/deploy-dashboard.yml` — 部署配置
- `scripts/dashboard/v8_ui.py` — 外观参考源（CSS + HTML 结构）
