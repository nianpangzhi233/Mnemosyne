import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V8_SRC = ROOT / "v8" / "src"
SCRIPTS = ROOT / "scripts"
if str(V8_SRC) not in sys.path:
    sys.path.insert(0, str(V8_SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dashboard.v8_store import v8_counts, v8_recent, v8_reason_summary, v8_snapshot
from v8_memory.lifecycle import LifecycleManager
from v8_memory.services import CandidateWriter, EvidenceRecorder, EventWriter
from v8_memory.store import SQLiteV8Store


class V8DashboardStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mnemosyne-v8-dashboard-"))
        self.db = self.tmp / "v8.db"
        self.store = SQLiteV8Store(self.db)
        self.events = EventWriter(self.store)
        self.candidates = CandidateWriter(self.store)
        self.evidence = EvidenceRecorder(self.store)
        self.lifecycle = LifecycleManager(self.store)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed_memory(self):
        first = self.events.add(
            event_type="tool_note",
            actor="agent",
            content="First note for the dashboard.",
            scope={"project_id": "memory-evolution", "session_id": "dash"},
        )
        second = self.events.add(
            event_type="tool_error",
            actor="agent",
            content="Second note with the actual lesson.",
            scope={"project_id": "memory-evolution", "session_id": "dash"},
        )
        cand_id = self.candidates.add(
            candidate_type="claim",
            content="The dashboard should read from V8 only.",
            source_event_ids=[second],
            scope={"project_id": "memory-evolution", "session_id": "dash"},
            trigger="dashboard redesign",
        )
        self.evidence.add(
            target_type="candidate",
            target_id=cand_id,
            evidence_type="task_success",
            polarity="supports",
            content="The V8 store and helpers successfully powered the view.",
            source_event_ids=[second],
        )
        memory_id = self.lifecycle.promote(cand_id)
        return first, second, cand_id, memory_id

    def test_counts_recent_summary_and_snapshot(self):
        _, latest_event, _, memory_id = self._seed_memory()
        self.store.insert_context_run(
            "ctx_1",
            "2026-05-21T00:00:00+00:00",
            "debug dashboard read path",
            {"project_id": "memory-evolution", "session_id": "dash"},
            selected=[{"id": memory_id, "type": "claim"}],
            rejected=[
                {"id": "mem_x", "reason": "scope_mismatch"},
                {"id": "mem_y", "reason": "scope_mismatch"},
                {"id": "mem_z", "reason": "stale"},
            ],
            warnings=["demo"],
            budget={"limit": 8},
        )

        counts = v8_counts(self.store)
        self.assertEqual(counts["raw_events"], 2)
        self.assertEqual(counts["candidates"], 1)
        self.assertEqual(counts["evidence"], 1)
        self.assertEqual(counts["memories"], 1)
        self.assertEqual(counts["context_pack_runs"], 1)

        recent_events = v8_recent(self.store, "raw_events", 1)
        self.assertEqual(recent_events[0]["id"], latest_event)

        reasons = v8_reason_summary(self.store)
        self.assertEqual(reasons[0]["reason"], "scope_mismatch")
        self.assertEqual(reasons[0]["count"], 2)
        self.assertEqual(reasons[1]["reason"], "stale")
        self.assertEqual(reasons[1]["count"], 1)

        snapshot = v8_snapshot(self.store, recent_limit=1)
        self.assertEqual(snapshot["counts"]["memories"], 1)
        self.assertIn("raw_events", snapshot["recent"])
        self.assertIn("reason_summary", snapshot)


if __name__ == "__main__":
    unittest.main()
