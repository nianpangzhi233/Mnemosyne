# V8 记忆系统 — Agent 接入指南

## MCP 用户（推荐）

MCP 客户端（Claude Code、VS Code、OpenCode 等）连接后自动加载 `instructions`，无需手动配置。

## 非 MCP 用户

将以下内容粘贴到系统提示词中：

```
## V8 Memory System

You have V8 memory tools (v8_* prefix). Use them to store and retrieve verified experience.

When to write: You solved a non-trivial problem, learned a reusable lesson, or the user explicitly asks to remember something.

Write flow (4 calls):
1. v8_event_add — record the raw fact (what happened, what was the result)
2. v8_candidate_add — extract a one-line reusable claim from the event
3. v8_evidence_add — attach the original event as supporting proof (polarity="supports")
4. v8_lifecycle_tentative_promote — promote with confidence=0.3 (unverified)

When to read: Starting a task that might benefit from past experience.
- v8_context_build(task="what you're doing", scope={"project_id": "..."})

After using a memory: Report the result.
- v8_feedback_record(run_id, memory_id, outcome="success"|"failure"|"neutral")
- success → confidence +0.05, failure → confidence -0.1
- Auto-stale at 0.15, auto-deprecate after 3 consecutive failures

Conflict detection: v8_conflict_scan(scope) finds duplicates and contradictions.
Multi-agent: v8_scope_agents(project_id), v8_scope_share(memory_id)

Rules:
- Never skip the event→candidate→evidence pipeline. No direct memory writes.
- Evidence must come from real events, not LLM self-verification.
- Sensitive data (passwords, keys, tokens) must not be stored.
```

## Cheat Sheet

```text
Write: event_add → candidate_add → evidence_add → tentative_promote
Read:  context_build
Feedback: feedback_record
```
