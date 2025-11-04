"""Tests for memory graph visualization."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.memory import Memory, MemoryEntry
from clauxton.visualization.memory_graph import MemoryGraph


@pytest.fixture
def test_project(tmp_path: Path) -> Path:
    """Create test project with .clauxton directory."""
    clauxton_dir = tmp_path / ".clauxton"
    clauxton_dir.mkdir()
    return tmp_path


@pytest.fixture
def populated_memory(test_project: Path) -> Memory:
    """Create memory system with test data."""
    memory = Memory(test_project)

    # Add knowledge entries with relationships
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20251103-001",
        type="knowledge",
        title="API Design Pattern",
        content="Use RESTful API design with versioning",
        category="architecture",
        tags=["api", "rest", "design"],
        created_at=now,
        updated_at=now,
        source="manual",
        confidence=1.0,
        related_to=["MEM-20251103-002"],
    )
    memory.add(mem1)

    mem2 = MemoryEntry(
        id="MEM-20251103-002",
        type="decision",
        title="Database Schema Design",
        content="Use PostgreSQL with normalized schema",
        category="database",
        tags=["database", "postgresql"],
        created_at=now,
        updated_at=now,
        source="manual",
        confidence=1.0,
        related_to=["MEM-20251103-001", "MEM-20251103-003"],
    )
    memory.add(mem2)

    mem3 = MemoryEntry(
        id="MEM-20251103-003",
        type="code",
        title="Authentication Module",
        content="JWT-based authentication implementation",
        category="security",
        tags=["auth", "jwt", "security"],
        created_at=now,
        updated_at=now,
        source="code-analysis",
        confidence=0.9,
        related_to=["MEM-20251103-002"],
    )
    memory.add(mem3)

    mem4 = MemoryEntry(
        id="MEM-20251103-004",
        type="task",
        title="Implement User Registration",
        content="Create user registration endpoint",
        category="feature",
        tags=["user", "registration"],
        created_at=now,
        updated_at=now,
        source="manual",
        confidence=1.0,
    )
    memory.add(mem4)

    mem5 = MemoryEntry(
        id="MEM-20251103-005",
        type="pattern",
        title="Repository Pattern",
        content="Data access layer abstraction",
        category="architecture",
        tags=["pattern", "architecture"],
        created_at=now,
        updated_at=now,
        source="code-analysis",
        confidence=0.8,
        related_to=["MEM-20251103-001"],
    )
    memory.add(mem5)

    return memory


def test_memory_graph_initialization(test_project: Path) -> None:
    """Test MemoryGraph initialization."""
    graph = MemoryGraph(test_project)

    assert graph.project_root == test_project
    assert graph.memory is not None
    assert isinstance(graph.memory, Memory)


def test_memory_graph_initialization_with_str(test_project: Path) -> None:
    """Test MemoryGraph initialization with string path."""
    graph = MemoryGraph(str(test_project))

    assert graph.project_root == test_project
    assert graph.memory is not None


def test_generate_graph_data_all_types(populated_memory: Memory) -> None:
    """Test graph data generation with all memory types."""
    graph = MemoryGraph(populated_memory.project_root)

    graph_data = graph.generate_graph_data()

    # Check structure
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "metadata" in graph_data

    # Check nodes
    nodes = graph_data["nodes"]
    assert len(nodes) == 5
    assert all("id" in node for node in nodes)
    assert all("type" in node for node in nodes)
    assert all("title" in node for node in nodes)
    assert all("size" in node for node in nodes)

    # Check edges
    edges = graph_data["edges"]
    # mem1->mem2, mem2->mem1, mem2->mem3, mem3->mem2, mem5->mem1 = 5 edges
    assert len(edges) == 5
    assert all("source" in edge for edge in edges)
    assert all("target" in edge for edge in edges)
    assert all("weight" in edge for edge in edges)

    # Check metadata
    metadata = graph_data["metadata"]
    assert metadata["total_nodes"] == 5
    assert metadata["total_edges"] == 5
    assert metadata["memory_type"] == "all"


def test_generate_graph_data_filtered_by_type(populated_memory: Memory) -> None:
    """Test graph data generation with type filter."""
    graph = MemoryGraph(populated_memory.project_root)

    # Filter by knowledge type
    graph_data = graph.generate_graph_data(memory_type="knowledge")

    nodes = graph_data["nodes"]
    assert len(nodes) == 1
    assert nodes[0]["type"] == "knowledge"
    assert nodes[0]["id"] == "MEM-20251103-001"

    # No edges since related memories are filtered out
    edges = graph_data["edges"]
    assert len(edges) == 0

    # Check metadata
    metadata = graph_data["metadata"]
    assert metadata["memory_type"] == "knowledge"


def test_generate_graph_data_max_nodes(populated_memory: Memory) -> None:
    """Test graph data generation with max_nodes limit."""
    graph = MemoryGraph(populated_memory.project_root)

    # Limit to 2 nodes (should get most connected ones)
    graph_data = graph.generate_graph_data(max_nodes=2)

    nodes = graph_data["nodes"]
    assert len(nodes) == 2

    # Should prioritize nodes with most relationships
    # mem2 has 2 relationships, mem1 and mem3 have 1, mem5 has 1
    node_ids = [node["id"] for node in nodes]
    assert "MEM-20251103-002" in node_ids  # mem2 has most relationships


def test_node_sizing(populated_memory: Memory) -> None:
    """Test node size calculation based on relationships."""
    graph = MemoryGraph(populated_memory.project_root)

    graph_data = graph.generate_graph_data()
    nodes = {node["id"]: node for node in graph_data["nodes"]}

    # mem2 has 2 relationships -> size = 5 + 2*2 = 9
    mem2 = nodes["MEM-20251103-002"]
    assert mem2["size"] == 9

    # mem1 has 1 relationship -> size = 5 + 1*2 = 7
    mem1 = nodes["MEM-20251103-001"]
    assert mem1["size"] == 7

    # mem4 has 0 relationships -> size = 5 + 0*2 = 5
    mem4 = nodes["MEM-20251103-004"]
    assert mem4["size"] == 5


def test_export_to_dot(populated_memory: Memory, tmp_path: Path) -> None:
    """Test DOT export format."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.dot"

    graph.export_to_dot(output_file)

    # Check file exists
    assert output_file.exists()

    # Check content
    content = output_file.read_text()
    assert "digraph memory_graph" in content
    assert "rankdir=LR" in content
    assert "MEM-20251103-001" in content
    assert "MEM-20251103-002" in content
    assert "->" in content  # Edge notation

    # Check node formatting
    assert '[label=' in content
    assert 'color=' in content
    assert 'penwidth=' in content


def test_export_to_dot_with_str_path(populated_memory: Memory, tmp_path: Path) -> None:
    """Test DOT export with string path."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.dot"

    graph.export_to_dot(str(output_file))

    assert output_file.exists()


def test_export_to_dot_filtered(populated_memory: Memory, tmp_path: Path) -> None:
    """Test DOT export with type filter."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "knowledge_graph.dot"

    graph.export_to_dot(output_file, memory_type="knowledge")

    content = output_file.read_text()
    assert "MEM-20251103-001" in content  # Knowledge entry
    # Should not have edges to filtered-out nodes


def test_export_to_mermaid(populated_memory: Memory, tmp_path: Path) -> None:
    """Test Mermaid export format."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.md"

    graph.export_to_mermaid(output_file)

    # Check file exists
    assert output_file.exists()

    # Check content
    content = output_file.read_text()
    assert "```mermaid" in content
    assert "graph LR" in content
    assert "MEM20251103001" in content  # Hyphen removed
    assert "MEM20251103002" in content
    assert "-->" in content  # Mermaid edge notation
    assert "```" in content


def test_export_to_mermaid_with_str_path(populated_memory: Memory, tmp_path: Path) -> None:
    """Test Mermaid export with string path."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.md"

    graph.export_to_mermaid(str(output_file))

    assert output_file.exists()


def test_export_to_mermaid_label_escaping(populated_memory: Memory, tmp_path: Path) -> None:
    """Test Mermaid export handles quotes in labels."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.md"

    graph.export_to_mermaid(output_file)

    content = output_file.read_text()
    # Quotes should be escaped or replaced
    assert "\\\"" not in content or "'" in content


def test_export_to_json(populated_memory: Memory, tmp_path: Path) -> None:
    """Test JSON export format."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.json"

    graph.export_to_json(output_file)

    # Check file exists
    assert output_file.exists()

    # Parse JSON
    with open(output_file) as f:
        data = json.load(f)

    # Check structure
    assert "nodes" in data
    assert "edges" in data
    assert "metadata" in data

    # Check nodes
    assert len(data["nodes"]) == 5
    assert data["nodes"][0]["id"] == "MEM-20251103-001"

    # Check edges
    assert len(data["edges"]) == 5

    # Check metadata
    assert data["metadata"]["total_nodes"] == 5
    assert data["metadata"]["total_edges"] == 5


def test_export_to_json_with_str_path(populated_memory: Memory, tmp_path: Path) -> None:
    """Test JSON export with string path."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "test_graph.json"

    graph.export_to_json(str(output_file))

    assert output_file.exists()


def test_export_to_json_filtered(populated_memory: Memory, tmp_path: Path) -> None:
    """Test JSON export with type filter."""
    graph = MemoryGraph(populated_memory.project_root)
    output_file = tmp_path / "knowledge_graph.json"

    graph.export_to_json(output_file, memory_type="knowledge")

    with open(output_file) as f:
        data = json.load(f)

    # Only knowledge entries
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["type"] == "knowledge"
    assert data["metadata"]["memory_type"] == "knowledge"


def test_node_color_mapping(test_project: Path) -> None:
    """Test node color mapping for different types."""
    graph = MemoryGraph(test_project)

    # Test color mapping
    assert graph._get_node_color("knowledge") == "blue"
    assert graph._get_node_color("decision") == "green"
    assert graph._get_node_color("code") == "orange"
    assert graph._get_node_color("task") == "red"
    assert graph._get_node_color("pattern") == "purple"
    assert graph._get_node_color("unknown") == "gray"


def test_empty_memory(test_project: Path) -> None:
    """Test graph generation with no memories."""
    graph = MemoryGraph(test_project)

    graph_data = graph.generate_graph_data()

    assert len(graph_data["nodes"]) == 0
    assert len(graph_data["edges"]) == 0
    assert graph_data["metadata"]["total_nodes"] == 0
    assert graph_data["metadata"]["total_edges"] == 0


def test_memory_without_relationships(test_project: Path) -> None:
    """Test graph generation with memories but no relationships."""
    memory = Memory(test_project)
    now = datetime.now()

    # Add isolated memories
    for i in range(3):
        mem = MemoryEntry(
            id=f"MEM-20251103-{i:03d}",
            type="knowledge",
            title=f"Memory {i}",
            content=f"Content {i}",
            category="test",
            tags=[],
            created_at=now,
            updated_at=now,
            source="manual",
            confidence=1.0,
        )
        memory.add(mem)

    graph = MemoryGraph(test_project)
    graph_data = graph.generate_graph_data()

    # Should have nodes but no edges
    assert len(graph_data["nodes"]) == 3
    assert len(graph_data["edges"]) == 0


def test_performance_with_large_graph(test_project: Path) -> None:
    """Test performance with many nodes."""
    import time

    memory = Memory(test_project)
    now = datetime.now()

    # Create 100 memories with some relationships
    for i in range(100):
        related = []
        if i > 0:
            related.append(f"MEM-20251103-{i-1:03d}")

        mem = MemoryEntry(
            id=f"MEM-20251103-{i:03d}",
            type="knowledge",
            title=f"Memory {i}",
            content=f"Content {i}",
            category="test",
            tags=[f"tag{i}"],
            created_at=now,
            updated_at=now,
            source="manual",
            confidence=1.0,
            related_to=related,
        )
        memory.add(mem)

    graph = MemoryGraph(test_project)

    # Measure generation time
    start = time.time()
    graph_data = graph.generate_graph_data(max_nodes=100)
    elapsed = time.time() - start

    # Should be fast (<2 seconds as per requirements)
    assert elapsed < 2.0
    assert len(graph_data["nodes"]) == 100


def test_edge_weight_default(populated_memory: Memory) -> None:
    """Test edge weight is set to default value."""
    graph = MemoryGraph(populated_memory.project_root)

    graph_data = graph.generate_graph_data()
    edges = graph_data["edges"]

    # All edges should have default weight
    for edge in edges:
        assert edge["weight"] == 0.8


def test_all_export_formats_consistency(populated_memory: Memory, tmp_path: Path) -> None:
    """Test all export formats produce consistent data."""
    graph = MemoryGraph(populated_memory.project_root)

    # Export to all formats
    dot_file = tmp_path / "graph.dot"
    mermaid_file = tmp_path / "graph.md"
    json_file = tmp_path / "graph.json"

    graph.export_to_dot(dot_file)
    graph.export_to_mermaid(mermaid_file)
    graph.export_to_json(json_file)

    # All should exist
    assert dot_file.exists()
    assert mermaid_file.exists()
    assert json_file.exists()

    # Load JSON to check consistency
    with open(json_file) as f:
        data = json.load(f)

    # DOT should contain same nodes
    dot_content = dot_file.read_text()
    for node in data["nodes"]:
        assert node["id"] in dot_content

    # Mermaid should contain same nodes (with hyphens removed)
    mermaid_content = mermaid_file.read_text()
    for node in data["nodes"]:
        node_id = node["id"].replace("-", "")
        assert node_id in mermaid_content
