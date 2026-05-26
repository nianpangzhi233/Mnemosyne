from __future__ import annotations

from typing import Any

from .models import dumps, loads, normalize_scope
from .store import SQLiteV8Store


class AgentScopeManager:
    def __init__(self, store: SQLiteV8Store):
        self.store = store

    def list_agents(self, project_id: str | None = None) -> list[str]:
        agents: set[str] = set()
        for table in ("memories", "candidates", "raw_events"):
            for row in self.store.list_all(table):
                scope = loads(row.get("scope_json"))
                if not scope:
                    continue
                if project_id and str(scope.get("project_id")) != project_id:
                    continue
                agent_id = scope.get("agent_id")
                if agent_id:
                    agents.add(str(agent_id))
        return sorted(agents)

    def get_agent_memories(self, agent_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for row in self.store.list_all("memories"):
            scope = loads(row.get("scope_json"))
            if scope.get("agent_id") == agent_id:
                result.append(row)
        return result

    def share_memory(self, memory_id: str) -> None:
        memory = self.store.get("memories", memory_id)
        if not memory:
            raise ValueError("memory does not exist")
        scope = loads(memory["scope_json"])
        scope["visibility"] = "project"
        self.store.update("memories", memory_id, {"scope_json": dumps(scope)})
