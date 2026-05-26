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
