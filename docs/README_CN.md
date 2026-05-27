# Mnemosyne V8

**AI 的原生记忆系统 — 每次都会记得你。本地运行，开箱即用。**

证据治理的记忆引擎：GraphRAG、向量搜索、反馈驱动置信度、冲突检测、多 Agent 共享。

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-purple?style=flat-square)](https://modelcontextprotocol.io/)
[![Version](https://img.shields.io/badge/version-8.3.0-black?style=flat-square)](../CHANGELOG.md)
[![CI](https://github.com/nianpangzhi233/Mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/nianpangzhi233/Mnemosyne/actions/workflows/ci.yml)
[![Pages](https://github.com/nianpangzhi233/Mnemosyne/actions/workflows/deploy-dashboard.yml/badge.svg)](https://github.com/nianpangzhi233/Mnemosyne/actions/workflows/deploy-dashboard.yml)

[English](../README.md) · [V8 README](../v8/README.md) · [architecture](architecture.md) · [Dashboard](https://nianpangzhi233.github.io/Mnemosyne/) · [FAQ](faq.md) · [Releases](https://github.com/nianpangzhi233/Mnemosyne/releases)

</div>

<p align="center">
  <img src="../assets/banner.png" alt="Mnemosyne banner" width="100%" />
</p>

<p align="center">
  <strong>给 AI 一个真正会记、有证据、能进化的长期记忆系统。</strong>
</p>

<p align="center">
  <a href="https://nianpangzhi233.github.io/Mnemosyne/">在线 Dashboard</a> ·
  <a href="#5-分钟上手">快速开始</a> ·
  <a href="#v8-核心概念">V8 核心理念</a>
</p>

---

## 它到底是什么

Mnemosyne 是一个给开发者用的本地优先 AI 记忆系统。它基于**证据治理**（evidence-governed）理念设计——记忆不是 LLM 概率输出的结果，而是验证过的事实。

## 你的 AI 有个问题

AI 助手有个致命缺陷：**它记不住事。**

你花了半小时解释项目架构，第二天它全忘了。你纠正了 3 次"用 const 不要用 var"，第 4 次它还是写 var。

这不是 bug，是设计——每次对话都是一张白纸。

**Mnemosyne 解决这个问题。** 不是文件存储，不是日记本，不是关键词匹配。是一套**证据治理的记忆管道**——原始事件→提炼→证据→记忆，每一步都可审计。

### 适用场景

- 记住团队偏好、架构决策和重复踩坑。
- 不用每次都重新解释项目背景。
- 记忆置信度随反馈自动调整——用对了加分，用错了降分。
- 自动检测重复/冲突记忆。

### 和常见方案有什么不一样

- **不是单纯 RAG。** 它有证据链、置信度演化和冲突检测。
- **不是简单数据库。** 记忆有完整生命周期：tentative → validated → stale → deprecated。
- **不是黑盒。** 每条记忆都可追溯到原始事件和证据。
- **不是纯后端库。** 有 MCP、REST API、CLI、Dashboard。

---

## 5 分钟上手

```bash
git clone https://github.com/nianpangzhi233/Mnemosyne.git
cd Mnemosyne
python setup.py
```

Windows 下一键启动 V8 API 和 Dashboard：

```bash
start-v8-api.cmd
start-dashboard.cmd
```

手动启动也可以：

```bash
python scripts/api/start_api.py --port 8979
python scripts/dashboard/web/index.html   # 直接用浏览器打开
```

V8 Demo 演示：

```bash
python demo/run_v8_demo.py
```

---

## V8 核心概念

### 记忆 ≠ 上下文

LLM 概率输出的东西不是记忆，验证过的事实才是。V8 通过四步管道确保每条记忆可审计：

```
v8_event_add    → 原始事实（不可变）
v8_candidate_add → 提炼为待验证 Claim
v8_evidence_add  → 附上证据（真实事件，不是 LLM 自述）
v8_lifecycle_tentative_promote → 写入记忆（confidence=0.3）
```

### 反馈驱动置信度

记忆不是写进去就不变了：

```
v8_feedback_record(run_id, memory_id, "success")  → confidence +0.05
v8_feedback_record(run_id, memory_id, "failure")  → confidence -0.1
```

confidence ≤ 0.15 → 自动 stale。连续 3 次 failure → 自动 deprecate。

### 冲突检测

```
v8_conflict_scan → 扫描重复记忆 + 关键词矛盾（"可以用" vs "不能用"）
```

### 多 Agent 共享

```
v8_scope_agents(project_id) → 列出项目中所有 Agent
v8_scope_share(memory_id)   → 跨 Agent 共享记忆
```

---

## 接入方式

### MCP（推荐）

V8 MCP Server 提供 19 个 v8_* 工具：

```json
{
  "mcpServers": {
    "mnemosyne": {
      "command": "python",
      "args": ["scripts/mcp_server/serve_mcp.py"],
      "env": {
        "MCP_V8_DB": "v8/data/v8.db"
      }
    }
  }
}
```

写入工具：`v8_event_add`、`v8_candidate_add`、`v8_evidence_add`、`v8_lifecycle_promote`、`v8_lifecycle_tentative_promote`

读取工具：`v8_context_build`、`v8_memory_get`、`v8_memory_list`、`v8_record_get`、`v8_record_list`

治理工具：`v8_feedback_record`、`v8_feedback_history`、`v8_conflict_scan`、`v8_conflict_list`、`v8_scope_agents`、`v8_scope_share`

生命周期：`v8_lifecycle_demote`、`v8_lifecycle_stale`、`v8_lifecycle_deprecate`

### REST API

```bash
python scripts/api/start_api.py --port 8979
# Swagger 文档: http://localhost:8979/docs

curl http://localhost:8979/api/health
# → {"status":"ok"}

curl "http://localhost:8979/api/v8/memories?limit=10"
```

### CLI

```bash
python -m v8_memory.cli event-add --type task_completed --actor agent --content "..."
python -m v8_memory.cli context-build --task "调试 API 网关"
python -m v8_memory.cli feedback --run-id xxx --memory-id yyy --outcome success
python -m v8_memory.cli conflict-scan
```

---

## Web Dashboard

在线地址：[https://nianpangzhi233.github.io/Mnemosyne/](https://nianpangzhi233.github.io/Mnemosyne/)

本地打开：

```bash
start-v8-api.cmd
# 浏览器打开 scripts/dashboard/web/index.html
```

展示记忆统计、最近记录、置信度分布、拒绝原因、反馈历史。

---

## 项目结构

```
v8/
├── src/v8_memory/
│   ├── store.py         # SQLiteV8Store（usage_log + memory_conflicts 表）
│   ├── context.py        # ContextPackBuilder（ReadGate 治理）
│   ├── lifecycle.py      # LifecycleManager（promote/demote/stale/tentative）
│   ├── feedback.py       # FeedbackLoop（confidence 自动更新）
│   ├── conflict.py       # ConflictDetector（重复 + 关键词冲突）
│   ├── agent_scope.py    # AgentScopeManager（多 Agent 共享）
│   ├── gates.py          # WriteGate + ReadGate（可扩展 callable）
│   ├── gate_steps.py     # WriteGate 自定义步骤示例
│   └── services.py       # EventWriter / CandidateWriter / EvidenceRecorder
├── tests/
│   ├── test_v8_mvp.py    # 15 个核心测试
│   ├── test_v8_feedback.py # 21 个新功能测试
│   └── test_gate_steps.py  # 7 个 gate_steps 测试
scripts/
├── mcp_server/           # MCP Server（19 个 v8_* 工具，stdio）
├── api/                  # FastAPI REST API（含 /api/v8 端点）
├── dashboard/web/        # Web Dashboard（纯 HTML + JS）
└── core/                 # 底层存储/嵌入抽象层
docs/
├── agent-integration.md  # 7 平台 Agent 接入指南
├── v8-agent-system-prompt.md # Agent 系统提示词片段
└── archive/              # V6/V7 历史文档归档
```

---

## 设计理念

### V8 治理优先

| 概念 | 含义 |
|------|------|
| RawEvent | 不可变原始事实——地基 |
| Candidate | LLM 提炼的 Claim——待验证 |
| Evidence | 支持/反驳/削弱证据——从真实事件来 |
| Memory | 验证后的记忆——confidence + status |
| WriteGate | 写入前质量检查（可扩展 callable） |
| ReadGate | 读取时 confidence 过滤 + task 匹配 |
| ContextPack | 受治理的记忆包（accepted + rejected） |

### 类比人脑

| 人脑 | Mnemosyne V8 |
|------|-------------|
| 经历被编码 | `v8_event_add` 写入原始事件 |
| 海马体提炼 | `v8_candidate_add` 提炼规律 |
| 前额叶验证 | `v8_evidence_add` 附证据 |
| 记忆巩固 | `v8_lifecycle_promote` 写入 |
| 遗忘曲线 | confidence 衰减 + stale 机制 |
| 睡眠修剪 | `v8_lifecycle_deprecate` 废弃 |
| 回忆检索 | `v8_context_build` 受治理提取 |

---

## 系统要求

- Python 3.10+
- ~2GB 磁盘空间（嵌入模型）
- 纯本地运行，不依赖外部服务

## 许可证

[MIT](LICENSE)

## 致谢

脑科学基础：
- **CLS 理论**（Complementary Learning Systems）— 快/慢双记忆
- **Reconsolidation**（再巩固）— 提取时重编码
- **Ebbinghaus 遗忘曲线** — 指数衰减 + 间隔重复

灵感来源：[OpenViking](https://github.com/bytedance/OpenViking)（L0/L1/L2 分层上下文）

---

<div align="center">

**[V8 README →](../v8/README.md)** · **[Dashboard →](https://nianpangzhi233.github.io/Mnemosyne/)** · **[Architecture →](architecture.md)** · **[FAQ →](faq.md)** · **[Changelog →](../CHANGELOG.md)**

**[Agent 接入指南 →](agent-integration.md)** · **[历史文档归档 →](archive/)**

</div>
