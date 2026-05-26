import unittest
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "v8" / "src"))

from v8_memory.store import SQLiteV8Store
from v8_memory.services import EventWriter, CandidateWriter, EvidenceRecorder
from v8_memory.lifecycle import LifecycleManager
from v8_memory.feedback import FeedbackLoop
from v8_memory.conflict import ConflictDetector
from v8_memory.agent_scope import AgentScopeManager
from v8_memory.context import ContextPackBuilder
from v8_memory.gates import WriteGate


class FeedbackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SQLiteV8Store(self.tmp / "test.db")
        self.lifecycle = LifecycleManager(self.store)
        self.feedback = FeedbackLoop(self.store, self.lifecycle)
        self._seed_memory()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed_memory(self):
        evt_id = EventWriter(self.store).add("tool_error", "agent", "PowerShell heredoc failed", {"project_id": "p1", "session_id": "s1"})
        cand_id = CandidateWriter(self.store).add("claim", "PS no heredoc", [evt_id], {"project_id": "p1", "session_id": "s1"}, "debug PS")
        EvidenceRecorder(self.store).add("candidate", cand_id, "task_success", "supports", "Fixed it", [evt_id])
        self.mem_id = self.lifecycle.promote(cand_id)

    def test_success_increases_confidence(self):
        result = self.feedback.record("run_1", self.mem_id, "success")
        self.assertAlmostEqual(result["confidence_after"], 0.75)
        self.assertIsNone(result["auto_action"])

    def test_failure_decreases_confidence(self):
        result = self.feedback.record("run_1", self.mem_id, "failure")
        self.assertAlmostEqual(result["confidence_after"], 0.6)
        self.assertIsNone(result["auto_action"])

    def test_neutral_does_not_change_confidence(self):
        result = self.feedback.record("run_1", self.mem_id, "neutral")
        self.assertAlmostEqual(result["confidence_after"], 0.7)

    def test_auto_stale_on_low_confidence(self):
        for i in range(5):
            self.feedback.record(f"run_{i}", self.mem_id, "failure")
        mem = self.store.get("memories", self.mem_id)
        self.assertEqual(mem["status"], "validated")
        self.feedback.record("run_5", self.mem_id, "failure")
        mem = self.store.get("memories", self.mem_id)
        self.assertIn(mem["status"], ("stale", "deprecated"))

    def test_auto_deprecate_on_consecutive_failures(self):
        for i in range(7):
            self.feedback.record(f"run_{i}", self.mem_id, "failure")
        mem = self.store.get("memories", self.mem_id)
        self.assertEqual(mem["status"], "deprecated")

    def test_history_records_feedback(self):
        self.feedback.record("run_1", self.mem_id, "success")
        self.feedback.record("run_2", self.mem_id, "failure")
        history = self.feedback.get_history(self.mem_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["outcome"], "failure")

    def test_invalid_outcome_raises(self):
        with self.assertRaises(ValueError):
            self.feedback.record("run_1", self.mem_id, "maybe")


class TentativePromoteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SQLiteV8Store(self.tmp / "test.db")
        self.lifecycle = LifecycleManager(self.store)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_tentative_promote_without_evidence(self):
        evt_id = EventWriter(self.store).add("obs", "agent", "saw something", {"project_id": "p1"})
        cand_id = CandidateWriter(self.store).add("claim", "something happened", [evt_id], {"project_id": "p1"}, "observe")
        mem_id = self.lifecycle.tentative_promote(cand_id)
        mem = self.store.get("memories", mem_id)
        self.assertEqual(mem["status"], "tentative")
        self.assertAlmostEqual(float(mem["confidence"]), 0.3)

    def test_tentative_promote_needs_source(self):
        with self.assertRaises(ValueError):
            CandidateWriter(self.store).add("claim", "no source", [], {"project_id": "p1"}, "test")

    def test_tentative_memory_visible_in_context(self):
        evt_id = EventWriter(self.store).add("obs", "agent", "X is true", {"project_id": "p1"})
        cand_id = CandidateWriter(self.store).add("claim", "X is true", [evt_id], {"project_id": "p1"}, "check truth")
        self.lifecycle.tentative_promote(cand_id)
        ctx = ContextPackBuilder(self.store).build("check truth", {"project_id": "p1"})
        self.assertEqual(len(ctx["items"]), 1)
        self.assertEqual(ctx["items"][0]["status"], "tentative")

    def test_tentative_filtered_by_high_confidence_policy(self):
        evt_id = EventWriter(self.store).add("obs", "agent", "X is true", {"project_id": "p1"})
        cand_id = CandidateWriter(self.store).add("claim", "X is true", [evt_id], {"project_id": "p1"}, "check truth")
        self.lifecycle.tentative_promote(cand_id)
        ctx = ContextPackBuilder(self.store).build("check truth", {"project_id": "p1"}, policy={"min_confidence": 0.7})
        self.assertEqual(len(ctx["items"]), 0)
        self.assertEqual(len(ctx["rejected"]), 1)
        self.assertEqual(ctx["rejected"][0]["reason"], "low_confidence")


class ConflictTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SQLiteV8Store(self.tmp / "test.db")
        self.detector = ConflictDetector(self.store)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _add_validated_memory(self, content, trigger="debug", scope=None):
        scope = scope or {"project_id": "p1"}
        evt_id = EventWriter(self.store).add("obs", "agent", content, scope)
        cand_id = CandidateWriter(self.store).add("claim", content, [evt_id], scope, trigger)
        EvidenceRecorder(self.store).add("candidate", cand_id, "task_success", "supports", "verified", [evt_id])
        return LifecycleManager(self.store).promote(cand_id)

    def test_detects_duplicate(self):
        self._add_validated_memory("Python 3.10 is required")
        self._add_validated_memory("Python 3.10 is required")
        conflicts = self.detector.scan()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["conflict_type"], "duplicate")

    def test_detects_keyword_clash(self):
        self._add_validated_memory("torch works on Windows", trigger="install torch")
        self._add_validated_memory("torch broken on Windows", trigger="install torch")
        conflicts = self.detector.scan()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["conflict_type"], "keyword_clash")

    def test_no_conflict_different_triggers(self):
        self._add_validated_memory("torch works on Windows", trigger="install torch")
        self._add_validated_memory("torch broken on Windows", trigger="debug error")
        conflicts = self.detector.scan()
        self.assertEqual(len(conflicts), 0)

    def test_mark_conflicted(self):
        m1 = self._add_validated_memory("A")
        m2 = self._add_validated_memory("B")
        conflict_id = self.detector.mark_conflicted(m1, m2, "manual", "test conflict")
        self.assertTrue(conflict_id.startswith("conflict_"))


class AgentScopeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SQLiteV8Store(self.tmp / "test.db")
        self.manager = AgentScopeManager(self.store)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _add_memory_with_agent(self, agent_id, project_id="p1"):
        scope = {"project_id": project_id, "agent_id": agent_id}
        evt_id = EventWriter(self.store).add("obs", agent_id, f"obs by {agent_id}", scope)
        cand_id = CandidateWriter(self.store).add("claim", f"learned by {agent_id}", [evt_id], scope, "test")
        EvidenceRecorder(self.store).add("candidate", cand_id, "task_success", "supports", "ok", [evt_id])
        return LifecycleManager(self.store).promote(cand_id)

    def test_list_agents(self):
        self._add_memory_with_agent("agent-a")
        self._add_memory_with_agent("agent-b")
        agents = self.manager.list_agents()
        self.assertIn("agent-a", agents)
        self.assertIn("agent-b", agents)

    def test_list_agents_filtered_by_project(self):
        self._add_memory_with_agent("agent-a", "p1")
        self._add_memory_with_agent("agent-b", "p2")
        agents = self.manager.list_agents("p1")
        self.assertEqual(agents, ["agent-a"])

    def test_get_agent_memories(self):
        self._add_memory_with_agent("agent-a")
        self._add_memory_with_agent("agent-b")
        mems = self.manager.get_agent_memories("agent-a")
        self.assertEqual(len(mems), 1)

    def test_share_memory(self):
        mem_id = self._add_memory_with_agent("agent-a")
        self.manager.share_memory(mem_id)
        mem = self.store.get("memories", mem_id)
        import json
        scope = json.loads(mem["scope_json"])
        self.assertEqual(scope["visibility"], "project")


class WriteGateCustomStepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SQLiteV8Store(self.tmp / "test.db")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_custom_step_rejects(self):
        gate = WriteGate(self.store)
        gate.register_step("must_mention_python", lambda cand, store: ("python" in cand["content"].lower(), "not_about_python"))
        evt_id = EventWriter(self.store).add("obs", "agent", "JS is great", {"project_id": "p1"})
        cand_id = CandidateWriter(self.store).add("claim", "JS is great", [evt_id], {"project_id": "p1"}, "test")
        EvidenceRecorder(self.store).add("candidate", cand_id, "task_success", "supports", "verified", [evt_id])
        cand = self.store.get("candidates", cand_id)
        ok, reasons = gate.check_promote(cand)
        self.assertFalse(ok)
        self.assertIn("not_about_python", reasons)

    def test_custom_step_passes(self):
        gate = WriteGate(self.store)
        gate.register_step("must_mention_python", lambda cand, store: ("python" in cand["content"].lower(), "not_about_python"))
        evt_id = EventWriter(self.store).add("obs", "agent", "Python works", {"project_id": "p1"})
        cand_id = CandidateWriter(self.store).add("claim", "Python works", [evt_id], {"project_id": "p1"}, "test")
        EvidenceRecorder(self.store).add("candidate", cand_id, "task_success", "supports", "verified", [evt_id])
        cand = self.store.get("candidates", cand_id)
        ok, reasons = gate.check_promote(cand)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
