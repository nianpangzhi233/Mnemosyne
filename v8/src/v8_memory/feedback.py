from __future__ import annotations

from typing import Any

from .lifecycle import LifecycleManager
from .models import dumps, new_id, now_iso
from .store import SQLiteV8Store


SUCCESS_DELTA = 0.05
FAILURE_DELTA = 0.1
STALE_THRESHOLD = 0.15
DEPRECATE_CONSECUTIVE_FAILURES = 3


class FeedbackLoop:
    def __init__(self, store: SQLiteV8Store, lifecycle: LifecycleManager | None = None):
        self.store = store
        self.lifecycle = lifecycle or LifecycleManager(store)

    def record(
        self,
        run_id: str,
        memory_id: str,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if outcome not in ("success", "failure", "neutral"):
            raise ValueError(f"invalid outcome: {outcome}")
        memory = self.store.get("memories", memory_id)
        if not memory:
            raise ValueError("memory does not exist")

        confidence_before = float(memory["confidence"])
        confidence_after = self._compute_confidence(confidence_before, outcome)

        log_id = new_id("fb")
        self.store.insert(
            "usage_log",
            {
                "id": log_id,
                "created_at": now_iso(),
                "run_id": run_id,
                "memory_id": memory_id,
                "outcome": outcome,
                "confidence_before": confidence_before,
                "confidence_after": confidence_after,
                "metadata_json": dumps(metadata or {}),
            },
        )

        self.lifecycle.update_confidence(memory_id, confidence_after)

        auto_action = None
        updated_memory = self.store.get("memories", memory_id)
        if confidence_after <= STALE_THRESHOLD and updated_memory["status"] not in ("stale", "deprecated"):
            consecutive = self._count_consecutive_failures(memory_id)
            if consecutive >= DEPRECATE_CONSECUTIVE_FAILURES:
                self.lifecycle.deprecate(memory_id)
                auto_action = "deprecated"
            else:
                self.lifecycle.stale(memory_id)
                auto_action = "stale"

        return {
            "id": log_id,
            "memory_id": memory_id,
            "outcome": outcome,
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "auto_action": auto_action,
        }

    def get_history(self, memory_id: str, limit: int = 50) -> list[dict[str, Any]]:
        conn = self.store.connect()
        try:
            rows = conn.execute(
                "SELECT * FROM usage_log WHERE memory_id=? ORDER BY created_at DESC LIMIT ?",
                (memory_id, limit),
            ).fetchall()
        finally:
            conn.close()
        return [self._decode_row(dict(row)) for row in rows]

    def _compute_confidence(self, current: float, outcome: str) -> float:
        if outcome == "success":
            return min(1.0, current + SUCCESS_DELTA)
        if outcome == "failure":
            return max(0.0, current - FAILURE_DELTA)
        return current

    def _count_consecutive_failures(self, memory_id: str) -> int:
        conn = self.store.connect()
        try:
            rows = conn.execute(
                "SELECT outcome FROM usage_log WHERE memory_id=? ORDER BY created_at DESC",
                (memory_id,),
            ).fetchall()
        finally:
            conn.close()
        count = 0
        for row in rows:
            if row["outcome"] == "failure":
                count += 1
            else:
                break
        return count

    def _decode_row(self, row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        for key in list(decoded.keys()):
            if key.endswith("_json"):
                from .models import loads
                decoded[key[:-5]] = loads(decoded.pop(key))
        return decoded
