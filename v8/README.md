# Mnemosyne V8

This is the clean project space for Mnemosyne V8.

Current status: MVP memory kernel + feedback/conflict/multi-agent/tentative features implemented and tested.

Rules:

- Do not import V7 graph databases.
- Do not reuse V7 node/edge schema as the V8 core model.
- Do not add architecture decisions here until the V8 design discussion is settled.
- Raw diaries and logs may later be used as source material for rebuilding V8 cognition from scratch.

## MVP Shape

V8 MVP proves this loop:

```text
RawEvent -> Candidate -> Evidence -> ValidatedMemory -> ContextPack
```

The point is not to store more text. The point is to prevent unsupported summaries from becoming trusted memory.

## Current MVP Capabilities

- SQLite-backed RawEvent, Candidate, Evidence, Memory, and ContextPack run storage.
- Evidence-required promotion from Candidate to ValidatedMemory.
- ReadGate filtering by scope, freshness, status, risk, task match, and confidence threshold.
- Lifecycle commands for promote, tentative-promote, demote, stale, and deprecate.
- Feedback-driven confidence evolution: auto-stale at 0.15, auto-deprecate after 3+ failures.
- Memory conflict detection: duplicate and keyword-clash scanning.
- Multi-agent shared memory: project-level sharing with agent traceability.
- Extensible WriteGate with custom Python callable validation steps.
- ContextPack output with original source event snippets and supporting evidence snippets.
- Inspection commands for events, candidates, evidence, memories, and context runs.
- PowerShell-friendly `--scope-item key=value` flags.
- Real-scenario functional smoke using the PowerShell wildcard compile issue.

## Dashboard

The default dashboard launcher now points at the V8 notebook-style Streamlit app:

```powershell
streamlit run scripts/dashboard/app_v8.py --server.port 8501 --server.headless=true --browser.gatherUsageStats=false
```

The V8 dashboard is intentionally hand-drawn in tone: paper background, taped labels, sketchy cards, and no V7 graph controls. The old `scripts/dashboard/app.py` remains as a legacy archive view.

Validated by:

- `python -m unittest tests.test_v8_mvp`
- `python -m unittest tests.test_v8_feedback`
- `python -m unittest tests.test_gate_steps`
- `python -m unittest discover tests` (43 tests total)
- `python "v8/scripts/functional_smoke.py" --db <temp-db>`

## CLI Demo

Run commands from the repository root.

```powershell
$env:PYTHONPATH = "v8/src"
python -m v8_memory.cli --db "v8/data/v8.db" event add --type tool_error --actor agent --content "PowerShell rejected Bash heredoc syntax." --scope-item project_id=memory-evolution --scope-item session_id=demo
```

Use the returned event ID as the source for a candidate:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" candidate add --type claim --content "PowerShell does not support Bash heredoc." --sources <event_id> --scope-item project_id=memory-evolution --scope-item session_id=demo --trigger "debug PowerShell inline command"
```

Attach evidence before promotion:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" evidence add --target <candidate_id> --type task_success --polarity supports --content "Using a PowerShell-compatible command fixed the issue." --sources <event_id>
```

`--sources` on evidence is optional, but use it when the evidence came from a RawEvent. This keeps both the candidate and the supporting evidence grounded in inspectable source material.

Promote only after evidence exists:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" lifecycle promote --candidate <candidate_id>
```

Build a scoped ContextPack:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" context build --task "debug PowerShell inline command" --scope-item project_id=memory-evolution --pretty
```

ContextPack items include the selected memory, original source events, and supporting evidence snippets, so callers can see what is trusted and why it is trusted:

```json
{
  "items": [
    {
      "id": "mem_...",
      "type": "claim",
      "content": "PowerShell does not support Bash heredoc.",
      "status": "validated",
      "scope": {"project_id": "memory-evolution", "session_id": "demo"},
      "source_events": [
        {
          "id": "evt_...",
          "event_type": "tool_error",
          "actor": "agent",
          "trust": "local",
          "content": "PowerShell rejected Bash heredoc syntax.",
          "scope": {"project_id": "memory-evolution", "session_id": "demo"}
        }
      ],
      "evidence": [
        {
          "id": "ev_...",
          "type": "task_success",
          "polarity": "supports",
          "content": "Using a PowerShell-compatible command fixed the issue.",
          "source_event_ids": ["evt_..."]
        }
      ]
    }
  ],
  "rejected": [],
  "warnings": []
}
```

`--scope` still accepts JSON, but `--scope-item key=value` is safer in PowerShell and can be repeated.

Lifecycle commands can also remove a memory from default injection:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" lifecycle demote --memory <memory_id>
python -m v8_memory.cli --db "v8/data/v8.db" lifecycle stale --memory <memory_id>
python -m v8_memory.cli --db "v8/data/v8.db" lifecycle deprecate --memory <memory_id>
```

`demote` and `deprecate` block injection by status. `stale` also sets freshness to zero and is reported as a freshness rejection.

### Tentative Promote

Promote a candidate that has source and scope but no evidence yet. The resulting memory gets status `tentative` and confidence 0.3 — visible through ReadGate but clearly marked as unverified:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" lifecycle tentative-promote --candidate <candidate_id>
```

Tentative memories can be promoted to full `validated` status later once evidence is attached and the standard WriteGate passes.

### Feedback

After using a memory in a real task, report whether it helped:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" feedback record --run <run_id> --memory <memory_id> --outcome success
python -m v8_memory.cli --db "v8/data/v8.db" feedback record --run <run_id> --memory <memory_id> --outcome failure
```

Confidence auto-updates: success +0.05, failure -0.1. When confidence drops to 0.15 or below the memory is auto-staled. Three or more consecutive failures trigger auto-deprecation.

View feedback history:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" feedback history --memory <memory_id>
```

### Conflict Detection

Scan for duplicate and keyword-clash conflicts within a scope:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" conflict scan --scope-item project_id=myproject
python -m v8_memory.cli --db "v8/data/v8.db" conflict list
```

Duplicate detection finds identical content across memories. Keyword clash finds opposing pairs (can/cannot, works/broken, support/not support, yes/no, true/false, enable/disable, should/should not, must/must not) in the same scope.

### Multi-Agent Scope

List agents in a project and share memories across them:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" scope agents --project myproject
python -m v8_memory.cli --db "v8/data/v8.db" scope share --memory <memory_id>
```

Memories are shared by project_id. agent_id is recorded for traceability but does not control access.

## Gate Reason Codes

WriteGate checks whether a Candidate may become ValidatedMemory:

| Reason | Meaning |
| --- | --- |
| `missing_source` | Candidate has no RawEvent source IDs. |
| `missing_scope` | Candidate has no normalized scope. |
| `missing_supporting_evidence` | Candidate has no supporting Evidence. |
| `contradicting_evidence` | Candidate has at least one contradicting Evidence row. |
| `missing_procedural_evidence` | Procedure/workflow/skill candidate lacks `test_result` or `control_flow_trace` support. |

ReadGate checks whether a Memory may enter the current ContextPack:

| Reason | Meaning |
| --- | --- |
| `stale` | Memory freshness is below the policy threshold. |
| `status_blocked` | Memory status is not `validated` or `promoted`. |
| `risk_blocked` | Memory risk is outside the policy's allowed risk set. |
| `scope_mismatch` | Memory scope conflicts with the requested scope. |
| `no_task_match` | MVP keyword match found no overlap between task and memory trigger/content. |
| `low_confidence` | Memory confidence is below the policy threshold (default 0.3). |

The current MVP reports only the first ReadGate rejection reason, while WriteGate returns all promotion blockers found for a Candidate.

Inspect stored records with list/get commands:

```powershell
python -m v8_memory.cli --db "v8/data/v8.db" event list --pretty
python -m v8_memory.cli --db "v8/data/v8.db" candidate get --id <candidate_id> --pretty
python -m v8_memory.cli --db "v8/data/v8.db" evidence list --target-type candidate --target <candidate_id> --pretty
python -m v8_memory.cli --db "v8/data/v8.db" memory get --id <memory_id> --pretty
python -m v8_memory.cli --db "v8/data/v8.db" context list --pretty
```

## MCP Tools

The existing Mnemosyne MCP server also exposes the V8 kernel. The V8 tools are prefixed with `v8_` so they do not conflict with the V7 graph-memory tools.

Stable V8 MCP tools:

| Tool | Purpose |
| --- | --- |
| `v8_event_add` | Append a RawEvent. |
| `v8_candidate_add` | Create a Candidate from RawEvent source IDs. |
| `v8_evidence_add` | Attach Evidence to a Candidate or Memory. |
| `v8_lifecycle_promote` | Promote a Candidate if WriteGate passes. |
| `v8_lifecycle_tentative_promote` | Promote with source+scope only, confidence=0.3. |
| `v8_lifecycle_demote` | Demote a Memory so ReadGate blocks it. |
| `v8_lifecycle_stale` | Mark a Memory stale and set freshness to zero. |
| `v8_lifecycle_deprecate` | Deprecate a Memory. |
| `v8_context_build` | Build a governed ContextPack. |
| `v8_memory_get` / `v8_memory_list` | Inspect Memories. |
| `v8_record_get` / `v8_record_list` | Inspect raw V8 tables. |
| `v8_lifecycle_tentative_promote` | Promote with source+scope only, confidence=0.3. |
| `v8_feedback_record` | Report feedback on a memory (success/failure/neutral). Auto-updates confidence. |
| `v8_feedback_history` | Get feedback trail for a memory. |
| `v8_conflict_scan` | Scan for duplicate and keyword-clash conflicts. |
| `v8_conflict_list` | List all detected conflicts. |
| `v8_scope_agents` | List agents in a project. |
| `v8_scope_share` | Share a memory across agents in its project. |

Minimal MCP flow:

```text
v8_event_add -> v8_candidate_add -> v8_evidence_add -> v8_lifecycle_promote -> v8_context_build
```

`v8_context_build` returns the same auditable shape as the CLI: selected memories include `source_events`, supporting `evidence`, and `evidence.source_event_ids`; rejected memories include reason codes.

By default the MCP server writes V8 state to `v8/data/v8.db`. Tests and local experiments can override this with `MCP_V8_DB=<path>`.

## REST API

The V8 REST surface is mounted on the existing FastAPI app under `/api/v8`. It is a thin wrapper over the same V8 services used by CLI and MCP.

Stable V8 REST endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v8/health` | Check V8 store health. |
| `POST /api/v8/events` | Append a RawEvent. |
| `POST /api/v8/candidates` | Create a Candidate from RawEvent source IDs. |
| `POST /api/v8/evidence` | Attach Evidence to a Candidate or Memory. |
| `POST /api/v8/lifecycle/promote` | Promote a Candidate if WriteGate passes. |
| `POST /api/v8/lifecycle/tentative-promote` | Promote with source+scope only, confidence=0.3. |
| `POST /api/v8/feedback/record` | Report feedback on a memory. |
| `GET /api/v8/feedback/history/{memory_id}` | Get feedback trail for a memory. |
| `POST /api/v8/conflicts/scan` | Scan for conflicts. |
| `GET /api/v8/conflicts` | List detected conflicts. |
| `POST /api/v8/scope/agents` | List agents in a project. |
| `POST /api/v8/scope/share` | Share a memory across agents. |
| `POST /api/v8/lifecycle/demote` | Demote a Memory. |
| `POST /api/v8/lifecycle/stale` | Mark a Memory stale. |
| `POST /api/v8/lifecycle/deprecate` | Deprecate a Memory. |
| `POST /api/v8/context-packs` | Build a governed ContextPack. |
| `GET /api/v8/memories` | List Memories. |
| `GET /api/v8/memories/{id}` | Inspect one Memory. |
| `GET /api/v8/records/{table}` | List raw V8 table records. |
| `GET /api/v8/records/{table}/{id}` | Inspect one raw V8 table record. |

Minimal REST flow:

```powershell
start-v8-api.cmd

curl -X POST http://127.0.0.1:8979/api/v8/events `
  -H "Content-Type: application/json" `
  -d '{"event_type":"tool_error","actor":"agent","content":"PowerShell rejected Bash heredoc syntax.","scope":{"project_id":"memory-evolution","session_id":"demo"}}'
```

Then call `candidates`, `evidence`, `lifecycle/promote`, and `context-packs` with the returned IDs. REST returns the same auditable fields as CLI and MCP: `source_events`, `evidence`, `evidence.source_event_ids`, and `rejected.reason`.

By default REST writes V8 state to `v8/data/v8.db`. Tests and local experiments can override this with `MNEMOSYNE_V8_DB=<path>` or `V8_DB=<path>`.

## Custom WriteGate Steps

V8 ships with two example custom steps in `gate_steps.py`:

```python
from v8_memory.gates import WriteGate
from v8_memory.gate_steps import register_default_steps

gate = WriteGate(store)
register_default_steps(gate)
```

This registers two checks that run on every `promote` call:

| Step | What it does |
| --- | --- |
| `duplicate_check` | Blocks candidates whose content matches an existing validated/tentative memory |
| `risk_keywords` | Blocks candidates containing sensitive keywords (password, secret, api_key, token, 密码, 密钥, etc.) |

To register a single step:

```python
from v8_memory.gate_steps import check_duplicate_content
gate.register_step("duplicate_check", check_duplicate_content)
```

To write a custom step, create a callable with signature `(candidate: dict, store: SQLiteV8Store) -> tuple[bool, str | None]`:

```python
def my_check(candidate, store):
    if "bad word" in candidate.get("content", ""):
        return False, "contains bad word"
    return True, None

gate.register_step("my_check", my_check)
```

All registered steps run after the built-in WriteGate checks.

## Functional Smoke

Run the real-scenario smoke test with a temporary or explicit database:

```powershell
$env:PYTHONPATH = "v8/src"
python "v8/scripts/functional_smoke.py" --db "v8/data/functional-smoke.db"
```

The smoke uses a real issue from V8 implementation: PowerShell did not expand `*.py` for `python -m py_compile`, while a Python `pathlib.glob('*.py')` compile command worked. It records that as RawEvent, Candidate, Evidence, ValidatedMemory, and then builds a ContextPack.

For a user-facing V8-only demo, run `python demo/run_v8_demo.py` from the repository root.

For the current handover status and next-step notes, see `../V8_HANDOVER.md`.

## Runtime Files

Runtime databases live under `v8/data/` and are ignored by git.
