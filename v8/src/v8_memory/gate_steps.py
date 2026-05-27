from __future__ import annotations

from typing import Any, Callable

from .store import SQLiteV8Store

RISK_KEYWORDS = [
    "password", "secret", "api_key", "apikey",
    "token", "private_key", "credential",
    "\u5bc6\u7801", "\u5bc6\u94a5", "\u51ed\u8bc1",
]


def check_duplicate_content(candidate: dict[str, Any], store: SQLiteV8Store) -> tuple[bool, str | None]:
    content = (candidate.get("content") or "").strip().lower()
    if not content:
        return True, None
    for memory in store.list_all("memories"):
        if memory["status"] not in ("validated", "promoted", "tentative"):
            continue
        if (memory.get("content") or "").strip().lower() == content:
            return False, f"duplicate of memory {memory['id'][:8]}"
    return True, None


def check_risk_keywords(candidate: dict[str, Any], store: SQLiteV8Store) -> tuple[bool, str | None]:
    content = (candidate.get("content") or "").lower()
    for keyword in RISK_KEYWORDS:
        if keyword in content:
            return False, f"contains sensitive keyword: {keyword}"
    return True, None


def register_default_steps(gate: Any) -> None:
    gate.register_step("duplicate_check", check_duplicate_content)
    gate.register_step("risk_keywords", check_risk_keywords)
