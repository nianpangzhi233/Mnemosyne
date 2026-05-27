#!/usr/bin/env python3
"""Mnemosyne V8 MCP Server — stdio transport

Zero-dependency MCP protocol (JSON-RPC over stdin/stdout).
Provides V8 governance-first memory tools only.
"""

import json
import sys
import os

from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stdin.reconfigure(encoding='utf-8', errors='replace')

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
ROOT_DIR = SCRIPTS_DIR.parent
V8_SRC_DIR = ROOT_DIR / "v8" / "src"
if V8_SRC_DIR.exists():
    sys.path.insert(0, str(V8_SRC_DIR))

from core.utils import fix_windows_encoding, ensure_hf_offline

fix_windows_encoding()
ensure_hf_offline()

from v8_memory.context import ContextPackBuilder
from v8_memory.feedback import FeedbackLoop
from v8_memory.conflict import ConflictDetector
from v8_memory.agent_scope import AgentScopeManager
from v8_memory.lifecycle import LifecycleManager
from v8_memory.services import CandidateWriter, EventWriter, EvidenceRecorder
from v8_memory.store import SQLiteV8Store

_v8_store = None


def _get_v8_store():
    global _v8_store
    if _v8_store is None:
        db_path = os.environ.get("MCP_V8_DB", str(ROOT_DIR / "v8" / "data" / "v8.db"))
        _v8_store = SQLiteV8Store(db_path)
    return _v8_store


def _clean_surrogates(obj):
    if isinstance(obj, str):
        return obj.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {k: _clean_surrogates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_surrogates(i) for i in obj]
    return obj


def _send(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _send_error(msg_id, code, message):
    _send({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    })


scope_schema = {
    "type": "object",
    "description": "Scope object, e.g. {project_id, user_id, agent_id, session_id, task_id, source_id}",
}


def _tools_list():
    return [
        {
            "name": "v8_event_add",
            "description": "V8: append an immutable RawEvent source record.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                    "actor": {"type": "string"},
                    "content": {"type": "string"},
                    "scope": scope_schema,
                    "trust": {"type": "string", "default": "local"},
                    "content_ref": {"type": "string"},
                    "metadata": {"type": "object"},
                },
                "required": ["event_type", "actor", "content"],
            },
        },
        {
            "name": "v8_candidate_add",
            "description": "V8: create an untrusted Candidate from RawEvent source IDs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "candidate_type": {"type": "string"},
                    "content": {"type": "string"},
                    "source_event_ids": {"type": "array", "items": {"type": "string"}},
                    "scope": scope_schema,
                    "trigger": {"type": "string"},
                    "risk": {"type": "string", "default": "low"},
                    "preconditions": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"},
                },
                "required": ["candidate_type", "content", "source_event_ids", "scope", "trigger"],
            },
        },
        {
            "name": "v8_evidence_add",
            "description": "V8: attach Evidence to a Candidate or Memory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target_type": {"type": "string", "default": "candidate"},
                    "target_id": {"type": "string"},
                    "evidence_type": {"type": "string"},
                    "polarity": {"type": "string", "enum": ["supports", "weakens", "contradicts", "neutral"]},
                    "content": {"type": "string"},
                    "source_event_ids": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"},
                },
                "required": ["target_id", "evidence_type", "polarity", "content"],
            },
        },
        {
            "name": "v8_lifecycle_promote",
            "description": "V8: promote a Candidate to ValidatedMemory if WriteGate passes.",
            "inputSchema": {"type": "object", "properties": {"candidate_id": {"type": "string"}}, "required": ["candidate_id"]},
        },
        {
            "name": "v8_lifecycle_demote",
            "description": "V8: demote a Memory so ReadGate blocks default injection.",
            "inputSchema": {"type": "object", "properties": {"memory_id": {"type": "string"}}, "required": ["memory_id"]},
        },
        {
            "name": "v8_lifecycle_stale",
            "description": "V8: mark a Memory stale and set freshness to zero.",
            "inputSchema": {"type": "object", "properties": {"memory_id": {"type": "string"}}, "required": ["memory_id"]},
        },
        {
            "name": "v8_lifecycle_deprecate",
            "description": "V8: deprecate a Memory so ReadGate blocks default injection.",
            "inputSchema": {"type": "object", "properties": {"memory_id": {"type": "string"}}, "required": ["memory_id"]},
        },
        {
            "name": "v8_context_build",
            "description": "V8: build a governed ContextPack for a task and scope.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "scope": scope_schema,
                    "budget": {"type": "object"},
                    "policy": {"type": "object"},
                },
                "required": ["task"],
            },
        },
        {
            "name": "v8_memory_get",
            "description": "V8: inspect one Memory by ID.",
            "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
        },
        {
            "name": "v8_memory_list",
            "description": "V8: list Memories.",
            "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}, "required": []},
        },
        {
            "name": "v8_record_get",
            "description": "V8: inspect a raw table record for events, candidates, evidence, memories, or context_pack_runs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "enum": ["raw_events", "candidates", "evidence", "memories", "context_pack_runs"]},
                    "id": {"type": "string"},
                },
                "required": ["table", "id"],
            },
        },
        {
            "name": "v8_record_list",
            "description": "V8: list raw table records for events, candidates, evidence, memories, or context_pack_runs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "enum": ["raw_events", "candidates", "evidence", "memories", "context_pack_runs"]},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["table"],
            },
        },
        {
            "name": "v8_lifecycle_tentative_promote",
            "description": "V8: promote a Candidate to tentative Memory (confidence=0.3) with only source+scope, no evidence required.",
            "inputSchema": {"type": "object", "properties": {"candidate_id": {"type": "string"}}, "required": ["candidate_id"]},
        },
        {
            "name": "v8_feedback_record",
            "description": "V8: report feedback on a memory usage. Updates confidence: success +0.05, failure -0.1. Auto-stale at 0.15, auto-deprecate after 3+ consecutive failures.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "memory_id": {"type": "string"},
                    "outcome": {"type": "string", "enum": ["success", "failure", "neutral"]},
                },
                "required": ["run_id", "memory_id", "outcome"],
            },
        },
        {
            "name": "v8_feedback_history",
            "description": "V8: get feedback history for a memory.",
            "inputSchema": {"type": "object", "properties": {"memory_id": {"type": "string"}}, "required": ["memory_id"]},
        },
        {
            "name": "v8_conflict_scan",
            "description": "V8: scan for memory conflicts (duplicates and keyword clashes like can/cannot, works/broken) within a scope.",
            "inputSchema": {
                "type": "object",
                "properties": {"scope": scope_schema},
                "required": ["scope"],
            },
        },
        {
            "name": "v8_conflict_list",
            "description": "V8: list all detected memory conflicts.",
            "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}},
        },
        {
            "name": "v8_scope_agents",
            "description": "V8: list all agents in a project. Use for multi-agent shared memory scenarios.",
            "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]},
        },
        {
            "name": "v8_scope_share",
            "description": "V8: share a memory across all agents in its project.",
            "inputSchema": {"type": "object", "properties": {"memory_id": {"type": "string"}}, "required": ["memory_id"]},
        },
    ]


def _v8_json(result):
    return _clean_surrogates(json.dumps(result, ensure_ascii=False, indent=2))


def _handle_v8_event_add(args):
    store = _get_v8_store()
    event_id = EventWriter(store).add(
        event_type=args["event_type"],
        actor=args["actor"],
        content=args["content"],
        scope=args.get("scope"),
        trust=args.get("trust", "local"),
        content_ref=args.get("content_ref"),
        metadata=args.get("metadata"),
    )
    return _v8_json({"id": event_id})


def _handle_v8_candidate_add(args):
    store = _get_v8_store()
    candidate_id = CandidateWriter(store).add(
        candidate_type=args["candidate_type"],
        content=args["content"],
        source_event_ids=args["source_event_ids"],
        scope=args.get("scope") or {},
        trigger=args["trigger"],
        risk=args.get("risk", "low"),
        preconditions=args.get("preconditions"),
        metadata=args.get("metadata"),
    )
    return _v8_json({"id": candidate_id})


def _handle_v8_evidence_add(args):
    store = _get_v8_store()
    evidence_id = EvidenceRecorder(store).add(
        target_type=args.get("target_type", "candidate"),
        target_id=args["target_id"],
        evidence_type=args["evidence_type"],
        polarity=args["polarity"],
        content=args["content"],
        source_event_ids=args.get("source_event_ids"),
        metadata=args.get("metadata"),
    )
    return _v8_json({"id": evidence_id})


def _handle_v8_lifecycle_promote(args):
    memory_id = LifecycleManager(_get_v8_store()).promote(args["candidate_id"])
    return _v8_json({"id": memory_id})


def _handle_v8_lifecycle_demote(args):
    memory_id = LifecycleManager(_get_v8_store()).demote(args["memory_id"])
    return _v8_json({"id": memory_id})


def _handle_v8_lifecycle_stale(args):
    memory_id = LifecycleManager(_get_v8_store()).stale(args["memory_id"])
    return _v8_json({"id": memory_id})


def _handle_v8_lifecycle_deprecate(args):
    memory_id = LifecycleManager(_get_v8_store()).deprecate(args["memory_id"])
    return _v8_json({"id": memory_id})


def _handle_v8_context_build(args):
    pack = ContextPackBuilder(_get_v8_store()).build(
        task=args["task"],
        scope=args.get("scope"),
        budget=args.get("budget"),
        policy=args.get("policy"),
    )
    return _v8_json(pack)


def _handle_v8_memory_get(args):
    return _v8_json(_get_v8_store().inspect_get("memories", args["id"]))


def _handle_v8_memory_list(args):
    return _v8_json({"items": _get_v8_store().inspect_list("memories", args.get("limit", 20))})


def _handle_v8_record_get(args):
    return _v8_json(_get_v8_store().inspect_get(args["table"], args["id"]))


def _handle_v8_record_list(args):
    return _v8_json({"items": _get_v8_store().inspect_list(args["table"], args.get("limit", 20))})


def _handle_v8_lifecycle_tentative_promote(args):
    memory_id = LifecycleManager(_get_v8_store()).tentative_promote(args["candidate_id"])
    return _v8_json({"id": memory_id})


def _handle_v8_feedback_record(args):
    result = FeedbackLoop(_get_v8_store()).record(
        run_id=args["run_id"],
        memory_id=args["memory_id"],
        outcome=args["outcome"],
    )
    return _v8_json(result)


def _handle_v8_feedback_history(args):
    history = FeedbackLoop(_get_v8_store()).get_history(args["memory_id"])
    return _v8_json({"items": history})


def _handle_v8_conflict_scan(args):
    scope = args["scope"] if "scope" in args else args.get("scope")
    conflicts = ConflictDetector(_get_v8_store()).scan(scope=scope)
    return _v8_json({"conflicts": conflicts})


def _handle_v8_conflict_list(args):
    conflicts = ConflictDetector(_get_v8_store()).list_conflicts(limit=args.get("limit", 20))
    return _v8_json({"items": conflicts})


def _handle_v8_scope_agents(args):
    agents = AgentScopeManager(_get_v8_store()).list_agents(project_id=args["project_id"])
    return _v8_json({"agents": agents})


def _handle_v8_scope_share(args):
    AgentScopeManager(_get_v8_store()).share_memory(args["memory_id"])
    return _v8_json({"shared": True, "memory_id": args["memory_id"]})


_HANDLERS = {
    "v8_event_add": _handle_v8_event_add,
    "v8_candidate_add": _handle_v8_candidate_add,
    "v8_evidence_add": _handle_v8_evidence_add,
    "v8_lifecycle_promote": _handle_v8_lifecycle_promote,
    "v8_lifecycle_demote": _handle_v8_lifecycle_demote,
    "v8_lifecycle_stale": _handle_v8_lifecycle_stale,
    "v8_lifecycle_deprecate": _handle_v8_lifecycle_deprecate,
    "v8_context_build": _handle_v8_context_build,
    "v8_memory_get": _handle_v8_memory_get,
    "v8_memory_list": _handle_v8_memory_list,
    "v8_record_get": _handle_v8_record_get,
    "v8_record_list": _handle_v8_record_list,
    "v8_lifecycle_tentative_promote": _handle_v8_lifecycle_tentative_promote,
    "v8_feedback_record": _handle_v8_feedback_record,
    "v8_feedback_history": _handle_v8_feedback_history,
    "v8_conflict_scan": _handle_v8_conflict_scan,
    "v8_conflict_list": _handle_v8_conflict_list,
    "v8_scope_agents": _handle_v8_scope_agents,
    "v8_scope_share": _handle_v8_scope_share,
}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            _send({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "prompts": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "logging": {},
                    },
                    "serverInfo": {"name": "mnemosyne", "version": "8.3.0"},
                    "instructions": (
                        "Mnemosyne V8 — governance-first memory.\n\n"
                        "MANDATORY WRITE PIPELINE — never skip steps:\n"
                        "  v8_event_add → v8_candidate_add → v8_evidence_add → v8_lifecycle_tentative_promote\n\n"
                        "SESSION START — call v8_context_build first to load relevant memories.\n\n"
                        "WHEN TO WRITE:\n"
                        "  - Task completed → full pipeline with event_type='task_completed'\n"
                        "  - Corrected by user → full pipeline with candidate_type='correction'\n"
                        "  - Non-obvious technical insight → full pipeline with candidate_type='experience'\n\n"
                        "AFTER USING A MEMORY → always v8_feedback_record (success or failure).\n\n"
                        "NEVER:\n"
                        "  - Skip the event→candidate→evidence pipeline\n"
                        "  - Use LLM output as evidence (only real events/results)\n"
                        "  - Store passwords, keys, or tokens"
                    )
                }
            })

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            _send({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"tools": _tools_list()}
            })

        elif method == "prompts/list":
            _send({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"prompts": []}
            })

        elif method == "resources/list":
            _send({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"resources": []}
            })

        elif method == "resources/templates/list":
            _send({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"resourceTemplates": []}
            })

        elif method == "prompts/get":
            _send_error(msg_id, -32602, "No prompts are available")

        elif method == "resources/read":
            _send_error(msg_id, -32602, "No resources are available")

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            handler = _HANDLERS.get(tool_name)

            if handler:
                try:
                    result = handler(tool_args)
                    _send({
                        "jsonrpc": "2.0", "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": str(result)}],
                            "isError": False
                        }
                    })
                except Exception as e:
                    _send({
                        "jsonrpc": "2.0", "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {e}"}],
                            "isError": True
                        }
                    })
            else:
                _send({
                    "jsonrpc": "2.0", "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                        "isError": True
                    }
                })

        elif method == "shutdown":
            _send({"jsonrpc": "2.0", "id": msg_id, "result": None})
            break

        elif msg_id is not None:
            _send_error(msg_id, -32601, f"Unknown method: {method}")


if __name__ == "__main__":
    main()
