from __future__ import annotations

from typing import Any

from .models import loads, new_id, now_iso, normalize_scope
from .store import SQLiteV8Store


CLASH_PAIRS = [
    ("can ", "cannot "),
    ("can't ", "can "),
    ("works", "broken"),
    ("works", "does not work"),
    ("support", "not support"),
    ("supported", "unsupported"),
    ("safe", "unsafe"),
    ("stable", "unstable"),
]


class ConflictDetector:
    def __init__(self, store: SQLiteV8Store):
        self.store = store

    def scan(self, scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        memories = self._get_active_memories(scope)
        conflicts: list[dict[str, Any]] = []
        seen: set[frozenset[str]] = set()

        for i, m1 in enumerate(memories):
            for m2 in memories[i + 1:]:
                pair_key = frozenset({m1["id"], m2["id"]})
                if pair_key in seen:
                    continue
                conflict = self._check_pair(m1, m2)
                if conflict:
                    seen.add(pair_key)
                    conflicts.append(conflict)

        return conflicts

    def mark_conflicted(
        self,
        memory_id_1: str,
        memory_id_2: str,
        conflict_type: str,
        reason: str,
    ) -> str:
        conflict_id = new_id("conflict")
        self.store.insert(
            "memory_conflicts",
            {
                "id": conflict_id,
                "created_at": now_iso(),
                "memory_id_1": memory_id_1,
                "memory_id_2": memory_id_2,
                "conflict_type": conflict_type,
                "reason": reason,
            },
        )
        return conflict_id

    def list_conflicts(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.store.inspect_list("memory_conflicts", limit)

    def _get_active_memories(self, scope: dict[str, Any] | None) -> list[dict[str, Any]]:
        norm_scope = normalize_scope(scope)
        memories = self.store.list_all("memories")
        result: list[dict[str, Any]] = []
        for m in memories:
            if m["status"] not in ("validated", "promoted", "tentative"):
                continue
            if norm_scope:
                m_scope = loads(m["scope_json"])
                match = all(
                    str(m_scope.get(k)) == str(v)
                    for k, v in norm_scope.items()
                    if k in m_scope
                )
                if not match:
                    continue
            result.append(m)
        return result

    def _check_pair(self, m1: dict[str, Any], m2: dict[str, Any]) -> dict[str, Any] | None:
        c1 = m1["content"].strip().lower()
        c2 = m2["content"].strip().lower()

        if c1 == c2:
            return {
                "memory_id_1": m1["id"],
                "memory_id_2": m2["id"],
                "conflict_type": "duplicate",
                "reason": "identical content in same scope",
            }

        trigger1 = (m1.get("trigger") or "").lower()
        trigger2 = (m2.get("trigger") or "").lower()
        if trigger1 and trigger2 and trigger1 == trigger2:
            clash = self._find_keyword_clash(c1, c2)
            if clash:
                return {
                    "memory_id_1": m1["id"],
                    "memory_id_2": m2["id"],
                    "conflict_type": "keyword_clash",
                    "reason": f"conflicting keywords: '{clash[0]}' vs '{clash[1]}' on same trigger",
                }

        return None

    def _find_keyword_clash(self, c1: str, c2: str) -> tuple[str, str] | None:
        for pos_word, neg_word in CLASH_PAIRS:
            if (pos_word in c1 and neg_word in c2) or (neg_word in c1 and pos_word in c2):
                return (pos_word.strip(), neg_word.strip())
        return None
