# ----------------------------------------------------------------------
# Knowledge graph wrapper.
# ----------------------------------------------------------------------
from __future__ import annotations

from typing import Any

from echoes.utils.import_helpers import safe_import

# Try to import the real knowledge graph
kg_mod, KG_AVAILABLE = safe_import("echoes.core.knowledge_graph")

if KG_AVAILABLE:
    KnowledgeGraph = kg_mod.KnowledgeGraph  # type: ignore[attr-defined]
else:

    class KnowledgeGraph:
        """Minimal fallback knowledge graph."""

        def __init__(self):
            self.nodes = {}  # node_id -> node_data
            self.edges = {}  # edge_id -> edge_data
            self.adjacency = {}  # node_id -> set of connected node_ids

        def add_node(
            self, node_id: str, node_type: str, properties: dict[str, Any] = None
        ) -> bool:
            """Add a node to the graph."""
            try:
                self.nodes[node_id] = {
                    "id": node_id,
                    "type": node_type,
                    "properties": properties or {},
                    "created_at": str(__import__("datetime").datetime.now()),
                }
                if node_id not in self.adjacency:
                    self.adjacency[node_id] = set()
                return True
            except Exception:
                return False

        def add_edge(
            self,
            edge_id: str,
            source_id: str,
            target_id: str,
            relationship: str = "related",
            properties: dict[str, Any] = None,
        ) -> bool:
            """Add an edge to the graph."""
            try:
                if source_id not in self.nodes or target_id not in self.nodes:
                    return False

                self.edges[edge_id] = {
                    "id": edge_id,
                    "source": source_id,
                    "target": target_id,
                    "relationship": relationship,
                    "properties": properties or {},
                    "created_at": str(__import__("datetime").datetime.now()),
                }

                # Update adjacency
                self.adjacency[source_id].add(target_id)
                self.adjacency[target_id].add(source_id)

                return True
            except Exception:
                return False

        def get_node(self, node_id: str) -> dict[str, Any] | None:
            """Get node by ID."""
            return self.nodes.get(node_id)

        def get_edge(self, edge_id: str) -> dict[str, Any] | None:
            """Get edge by ID."""
            return self.edges.get(edge_id)

        def find_neighbors(self, node_id: str, depth: int = 1) -> list[str]:
            """Find neighboring nodes within specified depth."""
            if node_id not in self.adjacency:
                return []

            visited = set()
            queue = [(node_id, 0)]
            neighbors = []

            while queue:
                current_id, current_depth = queue.pop(0)

                if current_id in visited or current_depth > depth:
                    continue

                visited.add(current_id)

                for neighbor_id in self.adjacency[current_id]:
                    if neighbor_id not in visited and neighbor_id != node_id:
                        neighbors.append(neighbor_id)
                        if current_depth < depth:
                            queue.append((neighbor_id, current_depth + 1))

            return neighbors

        def search_nodes(
            self, query: str, node_type: str | None = None
        ) -> list[dict[str, Any]]:
            """Search nodes by query and optional type."""
            results = []
            query_lower = query.lower()

            for node_id, node_data in self.nodes.items():
                if node_type and node_data.get("type") != node_type:
                    continue

                # Search in ID, type, and properties
                searchable_text = f"{node_id} {node_data.get('type', '')} {str(node_data.get('properties', ''))}"
                if query_lower in searchable_text.lower():
                    results.append(node_data)

            return results

        def get_graph_stats(self) -> dict[str, Any]:
            """Get graph statistics."""
            return {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": list({node.get("type") for node in self.nodes.values()}),
                "edge_types": list(
                    {edge.get("relationship") for edge in self.edges.values()}
                ),
                "connected_components": self._count_connected_components(),
            }

        def _count_connected_components(self) -> int:
            """Count connected components in the graph."""
            visited = set()
            components = 0

            for node_id in self.nodes:
                if node_id not in visited:
                    components += 1
                    # BFS to mark all nodes in this component
                    queue = [node_id]
                    while queue:
                        current = queue.pop(0)
                        if current not in visited:
                            visited.add(current)
                            queue.extend(self.adjacency[current] - visited)

            return components

        def export_graph(self, format: str = "dict") -> dict[str, Any]:
            """Export graph in specified format."""
            if format == "dict":
                return {
                    "nodes": list(self.nodes.values()),
                    "edges": list(self.edges.values()),
                }
            else:
                raise ValueError(f"Unsupported export format: {format}")
