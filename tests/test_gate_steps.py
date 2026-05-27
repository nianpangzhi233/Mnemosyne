import unittest
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "v8" / "src"))

from v8_memory.store import SQLiteV8Store
from v8_memory.services import EventWriter, CandidateWriter, EvidenceRecorder
from v8_memory.lifecycle import LifecycleManager
from v8_memory.gates import WriteGate
from v8_memory.gate_steps import check_duplicate_content, check_risk_keywords, register_default_steps


class GateStepsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = SQLiteV8Store(self.tmp / "test.db")
        self._seed()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed(self):
        evt_id = EventWriter(self.store).add("tool_error", "agent", "PS heredoc failed", {"project_id": "p1"})
        cand_id = CandidateWriter(self.store).add("claim", "PS no heredoc", [evt_id], {"project_id": "p1"}, "debug PS")
        EvidenceRecorder(self.store).add("candidate", cand_id, "task_success", "supports", "Fixed", [evt_id])
        self.mem_id = LifecycleManager(self.store).promote(cand_id)
        self.existing_cand = self.store.get("candidates", cand_id)
        self.evt_id = evt_id

    def _make_candidate(self, content: str) -> dict:
        cand_id = CandidateWriter(self.store).add("claim", content, [self.evt_id], {"project_id": "p1"}, "test")
        return self.store.get("candidates", cand_id)

    def test_duplicate_pass(self):
        cand = self._make_candidate("Something totally new and unique")
        passed, reason = check_duplicate_content(cand, self.store)
        self.assertTrue(passed)
        self.assertIsNone(reason)

    def test_duplicate_block(self):
        cand = self._make_candidate("PS no heredoc")
        passed, reason = check_duplicate_content(cand, self.store)
        self.assertFalse(passed)
        self.assertIn("duplicate", reason)

    def test_risk_keywords_pass(self):
        cand = self._make_candidate("Use pathlib.glob for file compilation")
        passed, reason = check_risk_keywords(cand, self.store)
        self.assertTrue(passed)
        self.assertIsNone(reason)

    def test_risk_keywords_block(self):
        cand = self._make_candidate("Store the password in environment variable")
        passed, reason = check_risk_keywords(cand, self.store)
        self.assertFalse(passed)
        self.assertIn("sensitive keyword", reason)

    def test_register_default_steps(self):
        gate = WriteGate(self.store)
        register_default_steps(gate)
        names = [name for name, _ in gate._extra_steps]
        self.assertIn("duplicate_check", names)
        self.assertIn("risk_keywords", names)

    def test_duplicate_empty_content_passes(self):
        cand_id = CandidateWriter(self.store).add("claim", "", [self.evt_id], {"project_id": "p1"}, "test")
        cand = self.store.get("candidates", cand_id)
        passed, reason = check_duplicate_content(cand, self.store)
        self.assertTrue(passed)

    def test_risk_keywords_chinese(self):
        cand = self._make_candidate("\u628a\u5bc6\u7801\u5b58\u5728\u73af\u5883\u53d8\u91cf\u91cc")
        passed, reason = check_risk_keywords(cand, self.store)
        self.assertFalse(passed)
        self.assertIn("sensitive keyword", reason)


if __name__ == "__main__":
    unittest.main()
