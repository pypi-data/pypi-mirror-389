"""
Memory graph visualization for Clauxton v0.15.0.

This module provides graph visualization capabilities for memory relationships:
- Generate graph data structures (nodes and edges)
- Export to Graphviz DOT format (for rendering with Graphviz)
- Export to Mermaid diagram format (for Markdown documentation)
- Export to JSON format (for web visualization)

Key Features:
- Node sizing based on number of relationships
- Edge weighting based on relationship strength
- Memory type filtering
- Color-coded nodes by memory type
- Performance optimized for large graphs (max 100 nodes default)

Example:
    >>> from pathlib import Path
    >>> from clauxton.visualization.memory_graph import MemoryGraph
    >>> graph = MemoryGraph(Path("."))
    >>> graph.export_to_mermaid(Path("graph.md"))
    >>> graph.export_to_dot(Path("graph.dot"))
    >>> graph.export_to_json(Path("graph.json"))
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from clauxton.core.memory import Memory, MemoryEntry


class MemoryGraph:
    """
    Generate graph visualizations of memory relationships.

    The MemoryGraph class creates visual representations of the memory system,
    showing how memories are connected through relationships. It supports
    multiple export formats for different use cases:
    - DOT: For Graphviz rendering (high-quality images)
    - Mermaid: For Markdown documentation (GitHub-compatible)
    - JSON: For web-based interactive visualizations

    Attributes:
        project_root: Project root directory
        memory: Memory system instance

    Example:
        >>> graph = MemoryGraph(Path("."))
        >>> graph_data = graph.generate_graph_data(memory_type="knowledge")
        >>> graph.export_to_mermaid(Path("knowledge_graph.md"))
    """

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize graph generator.

        Args:
            project_root: Project root directory (Path or str)

        Example:
            >>> graph = MemoryGraph(Path("."))
            >>> graph = MemoryGraph(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.memory = Memory(self.project_root)

    def generate_graph_data(
        self,
        memory_type: Optional[str] = None,
        max_nodes: int = 100,
    ) -> Dict[str, Any]:
        """
        Generate graph data structure.

        Creates a graph representation with nodes (memories) and edges (relationships).
        Node size is calculated based on the number of relationships (more connections
        = larger node). Memories can be filtered by type, and the number of nodes can
        be limited for performance.

        Args:
            memory_type: Filter by type (knowledge, decision, code, task, pattern)
            max_nodes: Maximum number of nodes (default: 100)

        Returns:
            Dictionary with nodes, edges, and metadata:
            {
                "nodes": [
                    {"id": "MEM-001", "type": "knowledge", "title": "...", "size": 10},
                    ...
                ],
                "edges": [
                    {"source": "MEM-001", "target": "MEM-002", "weight": 0.8},
                    ...
                ],
                "metadata": {
                    "total_nodes": 10,
                    "total_edges": 15,
                    "memory_type": "knowledge"
                }
            }

        Example:
            >>> graph_data = graph.generate_graph_data(memory_type="knowledge", max_nodes=50)
            >>> print(f"Nodes: {len(graph_data['nodes'])}")
            >>> print(f"Edges: {len(graph_data['edges'])}")
        """
        # Get memories
        memories = self.memory.list_all()

        if memory_type:
            memories = [m for m in memories if m.type == memory_type]

        # Limit nodes (sort by importance: number of relationships)
        if len(memories) > max_nodes:
            memories.sort(key=lambda m: len(m.related_to or []), reverse=True)
            memories = memories[:max_nodes]

        # Generate nodes
        nodes = self._generate_nodes(memories)

        # Generate edges from relationships
        edges = self._generate_edges(memories)

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "memory_type": memory_type or "all",
            },
        }

    def export_to_dot(
        self,
        output_file: Path | str,
        memory_type: Optional[str] = None,
        max_nodes: int = 100,
    ) -> None:
        """
        Export graph to Graphviz DOT format.

        Creates a DOT file that can be rendered with Graphviz tools (dot, neato, etc.)
        to produce high-quality graph images (PNG, SVG, PDF).

        Args:
            output_file: Output file path (.dot)
            memory_type: Filter by type
            max_nodes: Maximum number of nodes

        Example output:
            digraph memory_graph {
                rankdir=LR;
                node [shape=box, style=rounded];

                "MEM-001" [label="API Design", color=blue, penwidth=2.0];
                "MEM-002" [label="Database Schema", color=green, penwidth=1.5];
                "MEM-001" -> "MEM-002" [penwidth=2.4];
            }

        Usage:
            >>> graph.export_to_dot(Path("graph.dot"))
            >>> # Render with: dot -Tpng graph.dot -o graph.png

        Example:
            >>> graph.export_to_dot(Path("memory.dot"), memory_type="knowledge")
        """
        output_path = Path(output_file) if isinstance(output_file, str) else output_file
        graph_data = self.generate_graph_data(memory_type, max_nodes)

        dot_content = "digraph memory_graph {\n"
        dot_content += "  rankdir=LR;\n"
        dot_content += "  node [shape=box, style=rounded];\n\n"

        # Add nodes
        for node in graph_data["nodes"]:
            color = self._get_node_color(node["type"])
            size = node["size"]
            label = node["title"][:30]  # Limit length for readability

            dot_content += (
                f'  "{node["id"]}" [label="{label}", color={color}, penwidth={size / 5:.1f}];\n'
            )

        dot_content += "\n"

        # Add edges
        for edge in graph_data["edges"]:
            weight = edge["weight"]
            penwidth = max(1.0, weight * 3)  # Scale weight to line width

            source = edge["source"]
            target = edge["target"]
            dot_content += f'  "{source}" -> "{target}" [penwidth={penwidth:.1f}];\n'

        dot_content += "}\n"

        output_path.write_text(dot_content)

    def export_to_mermaid(
        self,
        output_file: Path | str,
        memory_type: Optional[str] = None,
        max_nodes: int = 100,
    ) -> None:
        """
        Export graph to Mermaid diagram format.

        Creates a Mermaid diagram that can be embedded in Markdown files and
        rendered on GitHub, GitLab, and other platforms that support Mermaid.

        Args:
            output_file: Output file path (.md)
            memory_type: Filter by type
            max_nodes: Maximum number of nodes

        Example output:
            ```mermaid
            graph LR
                MEM20251103001["API Design"]
                MEM20251103002["Database Schema"]
                MEM20251103003["Auth Pattern"]

                MEM20251103001 --> MEM20251103002
                MEM20251103002 --> MEM20251103003
            ```

        Usage:
            >>> graph.export_to_mermaid(Path("graph.md"))
            >>> # Include in README or docs

        Example:
            >>> graph.export_to_mermaid(Path("knowledge.md"), memory_type="knowledge")
        """
        output_path = Path(output_file) if isinstance(output_file, str) else output_file
        graph_data = self.generate_graph_data(memory_type, max_nodes)

        mermaid_content = "```mermaid\ngraph LR\n"

        # Create node ID map (remove hyphens for Mermaid)
        id_map = {node["id"]: node["id"].replace("-", "") for node in graph_data["nodes"]}

        # Add nodes with labels
        for node in graph_data["nodes"]:
            mermaid_id = id_map[node["id"]]
            label = node["title"][:20]  # Limit length for readability
            # Escape quotes in label
            label = label.replace('"', "'")
            mermaid_content += f'    {mermaid_id}["{label}"]\n'

        mermaid_content += "\n"

        # Add edges
        for edge in graph_data["edges"]:
            source_id = id_map[edge["source"]]
            target_id = id_map[edge["target"]]

            mermaid_content += f"    {source_id} --> {target_id}\n"

        mermaid_content += "```\n"

        output_path.write_text(mermaid_content)

    def export_to_json(
        self,
        output_file: Path | str,
        memory_type: Optional[str] = None,
        max_nodes: int = 100,
    ) -> None:
        """
        Export graph to JSON format.

        Creates a JSON file with the complete graph data structure, suitable for
        web-based interactive visualizations (D3.js, Cytoscape.js, etc.).

        Args:
            output_file: Output file path (.json)
            memory_type: Filter by type
            max_nodes: Maximum number of nodes

        Example output:
            {
              "nodes": [
                {
                  "id": "MEM-20251103-001",
                  "type": "knowledge",
                  "title": "API Design Pattern",
                  "category": "architecture",
                  "size": 10,
                  "tags": ["api", "rest"]
                }
              ],
              "edges": [
                {
                  "source": "MEM-20251103-001",
                  "target": "MEM-20251103-002",
                  "weight": 0.8
                }
              ],
              "metadata": {
                "total_nodes": 5,
                "total_edges": 8,
                "memory_type": "all"
              }
            }

        Example:
            >>> graph.export_to_json(Path("graph.json"), memory_type="knowledge")
        """
        output_path = Path(output_file) if isinstance(output_file, str) else output_file
        graph_data = self.generate_graph_data(memory_type, max_nodes)

        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)

    def _generate_nodes(self, memories: List[MemoryEntry]) -> List[Dict[str, Any]]:
        """
        Generate node data from memories.

        Node size is calculated based on the number of relationships:
        - Base size: 5
        - +2 per relationship
        - Max size: 20

        Args:
            memories: List of MemoryEntry objects

        Returns:
            List of node dictionaries

        Example:
            >>> nodes = graph._generate_nodes(memories)
            >>> nodes[0]["size"]  # 5 + (2 * num_relationships)
            9
        """
        nodes = []

        for mem in memories:
            # Calculate node size based on relationships
            num_relationships = len(mem.related_to or [])
            size = min(5 + num_relationships * 2, 20)  # Size 5-20

            nodes.append(
                {
                    "id": mem.id,
                    "type": mem.type,
                    "title": mem.title,
                    "category": mem.category,
                    "size": size,
                    "tags": mem.tags,
                }
            )

        return nodes

    def _generate_edges(self, memories: List[MemoryEntry]) -> List[Dict[str, Any]]:
        """
        Generate edge data from memory relationships.

        Edges are created from the related_to field of each memory. Only edges
        where both source and target exist in the filtered memory set are included.

        Args:
            memories: List of MemoryEntry objects

        Returns:
            List of edge dictionaries

        Example:
            >>> edges = graph._generate_edges(memories)
            >>> edges[0]
            {'source': 'MEM-001', 'target': 'MEM-002', 'weight': 0.8}
        """
        edges = []
        memory_ids = {m.id for m in memories}

        for mem in memories:
            if not mem.related_to:
                continue

            for related_id in mem.related_to:
                # Only add edge if target exists in filtered memories
                if related_id in memory_ids:
                    edges.append(
                        {
                            "source": mem.id,
                            "target": related_id,
                            "weight": 0.8,  # Default weight (could use similarity from linker)
                        }
                    )

        return edges

    def _get_node_color(self, memory_type: str) -> str:
        """
        Get color for node based on memory type.

        Color scheme:
        - knowledge: blue (informational)
        - decision: green (important choices)
        - code: orange (technical)
        - task: red (action items)
        - pattern: purple (recurring themes)

        Args:
            memory_type: Memory type

        Returns:
            Color name for Graphviz

        Example:
            >>> graph._get_node_color("knowledge")
            'blue'
        """
        colors = {
            "knowledge": "blue",
            "decision": "green",
            "code": "orange",
            "task": "red",
            "pattern": "purple",
        }
        return colors.get(memory_type, "gray")
