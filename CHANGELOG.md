# Changelog

All notable changes to Mnemosyne will be documented in this file.

## [8.0.0] — 2026-05-26

### Added
- V8 lifecycle pipeline: RawEvent → Candidate → Evidence → ValidatedMemory → ContextPack
- WriteGate with 5 rejection checks (missing_source, missing_scope, missing_supporting_evidence, contradicting_evidence, missing_procedural_evidence)
- ReadGate with 5 rejection checks (stale, status_blocked, risk_blocked, scope_mismatch, no_task_match)
- Lifecycle commands: promote, demote, stale, deprecate
- CLI with PowerShell-friendly `--scope-item key=value` flags
- MCP Server with `v8_` prefixed tools
- REST API under `/api/v8`
- Notebook-style Streamlit dashboard
- ContextPack output with source events, evidence snippets, and rejection reasons
- Functional smoke test using real V8 implementation issue

### Changed
- Complete architecture redesign from V7 graph-based model to governance-first pipeline
- No longer trusts LLM-generated content as memory; all LLM output starts as Candidate

## [8.1.0] — 2026-05-26

### Added

#### Feedback-driven Confidence Evolution
- `FeedbackLoop.record(run_id, memory_id, outcome)` — report success/failure/neutral after using a memory
- Automatic confidence update: success +0.05, failure -0.1
- Auto-stale when confidence drops below 0.15
- Auto-deprecate after 3+ consecutive failures
- `feedback.get_history(memory_id)` — inspect feedback trail
- `usage_log` table for persistent feedback records
- CLI: `feedback record`, `feedback history`

#### Tentative Promote (Async Verification)
- `LifecycleManager.tentative_promote(candidate_id)` — promote with only source+scope, no evidence required
- Creates memory with status="tentative", confidence=0.3
- Tentative memories are visible through ReadGate by default (min_confidence=0.3)
- CLI: `lifecycle tentative-promote`

#### Memory Conflict Detection
- `ConflictDetector.scan(scope)` — detect duplicate and keyword-clash conflicts
- Keyword clash pairs: can/cannot, works/broken, support/not support, yes/no, true/false, enable/disable, should/should not, must/must not
- `memory_conflicts` table for persistent conflict tracking
- CLI: `conflict scan`, `conflict list`

#### Multi-Agent Shared Memory
- `AgentScopeManager.list_agents(project_id)` — list all agents in a project
- `AgentScopeManager.get_agent_memories(agent_id)` — get memories created by a specific agent
- `AgentScopeManager.share_memory(memory_id)` — mark memory as project-visible
- Sharing by project_id, agent_id for traceability only (no access control)
- CLI: `scope agents`, `scope share`

#### Extensible WriteGate
- `WriteGate.register_step(name, fn)` — register custom Python callable validation steps
- `WriteGate.check_tentative()` — lightweight check for tentative promotion
- No YAML dependency; validation logic is pure Python

#### ReadGate Confidence Filtering
- New rejection reason: `low_confidence` — blocks memories below configurable threshold
- Default `min_confidence=0.3` (tentative memories visible by default)
- Configurable via policy parameter
- `tentative` added to DEFAULT_ALLOWED_STATUS

#### ContextPack Enhancement
- ContextPack items now include `confidence` and `agent_id` fields

### Tests
- 36 tests passing (15 MVP + 21 new feature)
- `test_v8_feedback.py` covers feedback/stale/deprecate/tentative/conflict/scope/gate-custom-step
