# ----------------------------------------------------------------------
# Knowledge Manager wrapper.
# ----------------------------------------------------------------------
from __future__ import annotations

from typing import Any

from echoes.utils.import_helpers import safe_import

# Try to import the real KnowledgeManager
knowledge_mod, KNOWLEDGE_AVAILABLE = safe_import("echoes.core.knowledge")

if KNOWLEDGE_AVAILABLE:
    KnowledgeManager = knowledge_mod.KnowledgeManager  # type: ignore[attr-defined]
else:

    class KnowledgeManager:
        """Minimal fallback knowledge manager."""

        def __init__(self):
            self.knowledge_base = {}

        def add_knowledge(
            self, key: str, value: Any, metadata: dict[str, Any] = None
        ) -> bool:
            """Add knowledge to the knowledge base."""
            try:
                self.knowledge_base[key] = {
                    "value": value,
                    "metadata": metadata or {},
                    "added_at": str(__import__("datetime").datetime.now()),
                }
                return True
            except Exception:
                return False

        def get_knowledge(self, key: str) -> Any | None:
            """Retrieve knowledge by key."""
            if key in self.knowledge_base:
                return self.knowledge_base[key]["value"]
            return None

        def search_knowledge(self, query: str) -> list[dict[str, Any]]:
            """Search knowledge base."""
            results = []
            query_lower = query.lower()

            for key, data in self.knowledge_base.items():
                if (
                    query_lower in key.lower()
                    or query_lower in str(data["value"]).lower()
                ):
                    results.append(
                        {
                            "key": key,
                            "value": data["value"],
                            "metadata": data["metadata"],
                        }
                    )

            return results

        def list_knowledge(self) -> list[str]:
            """List all knowledge keys."""
            return list(self.knowledge_base.keys())

        def delete_knowledge(self, key: str) -> bool:
            """Delete knowledge by key."""
            if key in self.knowledge_base:
                del self.knowledge_base[key]
                return True
            return False

        def get_stats(self) -> dict[str, Any]:
            """Get knowledge base statistics."""
            return {
                "total_items": len(self.knowledge_base),
                "keys": list(self.knowledge_base.keys()),
                "last_updated": max(
                    (data["added_at"] for data in self.knowledge_base.values()),
                    default="Never",
                ),
            }
