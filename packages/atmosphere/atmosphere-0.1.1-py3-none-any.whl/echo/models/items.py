# ----------------------------------------------------------------------
# Dataclasses used across the repo.
# ----------------------------------------------------------------------
from dataclasses import dataclass
from typing import Any, List


@dataclass
class InventoryItem:
    """ATLAS-style inventory item."""

    sku: str
    name: str
    category: str
    quantity: int
    location: str
    min_stock: int = 0
    max_stock: int = 0
    created_at: str = ""
    updated_at: str = ""
    attributes: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "location": self.location,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "attributes": self.attributes or {},
        }


@dataclass
class Draft:
    """GLIMPSE draft for pre-flight processing."""

    input_text: str
    goal: str = ""
    constraints: str = ""
    session_id: str | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    result: Any
    error: str | None = None
    execution_time: float | None = None


@dataclass
class RAGResult:
    """Result from RAG search."""

    query: str
    results: List[dict[str, Any]]
    total_found: int
    search_time: float
    index_used: str
