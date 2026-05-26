from __future__ import annotations

import os
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

scripts_dir = Path(__file__).resolve().parent.parent
v8_src_dir = Path(__file__).resolve().parent.parent.parent / "v8" / "src"
for path in (scripts_dir, v8_src_dir):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from v8_memory.store import SQLiteV8Store


def _default_db_path() -> Path:
    env_path = os.environ.get("MNEMOSYNE_V8_DB")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent.parent.parent / "v8" / "data" / "v8.db"


@lru_cache(maxsize=1)
def get_v8_store(db_path: str | None = None) -> SQLiteV8Store:
    path = Path(db_path) if db_path else _default_db_path()
    return SQLiteV8Store(path)


def v8_health(store: SQLiteV8Store | None = None) -> dict[str, Any]:
    store = store or get_v8_store()
    path = store.db_path
    return {
        "db_path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "tables": sorted(store.TABLES),
    }


def v8_counts(store: SQLiteV8Store | None = None) -> dict[str, int]:
    store = store or get_v8_store()
    return {table: len(store.list_all(table)) for table in sorted(store.TABLES)}


def v8_recent(store: SQLiteV8Store | None, table: str, limit: int = 10) -> list[dict[str, Any]]:
    store = store or get_v8_store()
    return store.inspect_list(table, limit)


def v8_reason_summary(store: SQLiteV8Store | None = None, limit: int = 50) -> list[dict[str, Any]]:
    store = store or get_v8_store()
    reasons = Counter()
    for run in store.inspect_list("context_pack_runs", limit):
        for rejected in run.get("rejected", []):
            reason = rejected.get("reason") or "unknown"
            reasons[reason] += 1
    return [
        {"reason": reason, "count": count}
        for reason, count in reasons.most_common()
    ]


def v8_snapshot(store: SQLiteV8Store | None = None, recent_limit: int = 8) -> dict[str, Any]:
    store = store or get_v8_store()
    return {
        "health": v8_health(store),
        "counts": v8_counts(store),
        "recent": {
            table: v8_recent(store, table, recent_limit)
            for table in ("raw_events", "candidates", "evidence", "memories", "context_pack_runs")
        },
        "reason_summary": v8_reason_summary(store),
    }
