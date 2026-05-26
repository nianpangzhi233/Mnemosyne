import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "v8", "src"))

from v8_memory.store import V8Store

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "v8", "data", "quick_start.db")


def main():
    store = V8Store(DB_PATH)

    evt = store.add_event(
        event_type="tool_error",
        actor="agent",
        content="PowerShell rejected Bash heredoc syntax.",
        scope={"project_id": "demo", "session_id": "quick_start"},
    )
    print(f"1. RawEvent created: {evt.id}")

    cand = store.add_candidate(
        candidate_type="claim",
        content="PowerShell does not support Bash heredoc.",
        source_event_ids=[evt.id],
        scope={"project_id": "demo", "session_id": "quick_start"},
        trigger="debug PowerShell inline command",
    )
    print(f"2. Candidate created: {cand.id}")

    evi = store.add_evidence(
        target_id=cand.id,
        target_type="candidate",
        evidence_type="task_success",
        polarity="supports",
        content="Using a PowerShell-compatible command fixed the issue.",
        source_event_ids=[evt.id],
    )
    print(f"3. Evidence attached: {evi.id}")

    mem = store.promote_candidate(cand.id)
    if mem:
        print(f"4. Promoted to ValidatedMemory: {mem.id}")
    else:
        gate_result = store.check_write_gate(cand.id)
        print(f"4. WriteGate blocked: {[r.value for r in gate_result.reasons]}")
        return

    ctx = store.build_context_pack(
        task="debug PowerShell inline command",
        scope={"project_id": "demo", "session_id": "quick_start"},
    )
    print(f"5. ContextPack built: {len(ctx.items)} items, {len(ctx.rejected)} rejected")
    for item in ctx.items:
        print(f"   - {item.content[:60]}... (status: {item.status})")

    print("\nDone! Full lifecycle completed in 5 steps.")


if __name__ == "__main__":
    main()
