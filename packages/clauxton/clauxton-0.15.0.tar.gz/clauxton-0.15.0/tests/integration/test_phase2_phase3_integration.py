"""
Integration tests for Phase 2 ↔ Phase 3 interaction.

Tests the complete workflow between:
- Memory extraction (Phase 2) → Question answering (Phase 3)
- Memory linking (Phase 2) → Graph visualization (Phase 3)
- Memory extraction (Phase 2) → Summarization (Phase 3)
"""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.memory import Memory, MemoryEntry
from clauxton.semantic.memory_linker import MemoryLinker
from clauxton.semantic.memory_qa import MemoryQA
from clauxton.semantic.memory_summarizer import MemorySummarizer
from clauxton.visualization.memory_graph import MemoryGraph


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create temporary project with .clauxton directory."""
    project = tmp_path / "test_project"
    project.mkdir()
    (project / ".clauxton").mkdir()
    return project


def test_extract_and_ask(temp_project: Path) -> None:
    """Test memory extraction → question answering flow."""
    # Phase 2: Add some memories manually (simulating extraction)
    memory = Memory(temp_project)
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20251103-001",
        type="decision",
        title="Switch to PostgreSQL",
        content=(
            "Migrate from MySQL to PostgreSQL for better JSONB support "
            "and improved performance with complex queries"
        ),
        category="database",
        tags=["postgresql", "migration", "database"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )
    mem2 = MemoryEntry(
        id="MEM-20251103-002",
        type="pattern",
        title="Use Connection Pooling",
        content=(
            "Implement connection pooling with PostgreSQL using pgbouncer "
            "for better resource management"
        ),
        category="database",
        tags=["postgresql", "performance", "connection-pooling"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )
    memory.add(mem1)
    memory.add(mem2)

    # Phase 3: Ask questions
    qa = MemoryQA(temp_project)
    answer, confidence, sources = qa.answer_question("Why did we switch to PostgreSQL?")

    # Assertions
    assert "PostgreSQL" in answer or "JSONB" in answer or "performance" in answer
    assert confidence > 0.5
    assert "MEM-20251103-001" in sources


def test_link_and_visualize(temp_project: Path) -> None:
    """Test memory linking → graph visualization flow."""
    # Phase 2: Create related memories
    memory = Memory(temp_project)
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20251103-001",
        type="decision",
        title="Switch to PostgreSQL",
        content="Use PostgreSQL for database management with JSONB support",
        category="database",
        tags=["postgresql", "database"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20251103-002",
        type="pattern",
        title="Database Connection Pool",
        content="Use connection pooling with PostgreSQL for better performance",
        category="database",
        tags=["postgresql", "performance"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem3 = MemoryEntry(
        id="MEM-20251103-003",
        type="knowledge",
        title="Maximum Connection Limit",
        content="PostgreSQL connection pool should not exceed 100 connections",
        category="database",
        tags=["postgresql", "limits"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    memory.add(mem1)
    memory.add(mem2)
    memory.add(mem3)

    # Phase 2: Link memories
    linker = MemoryLinker(temp_project)
    linker.auto_link_all(threshold=0.3)  # Lower threshold to ensure links

    # Phase 3: Generate graph
    graph = MemoryGraph(temp_project)
    graph_data = graph.generate_graph_data()

    # Assertions
    assert len(graph_data["nodes"]) == 3
    assert len(graph_data["edges"]) >= 1  # Should have at least one link

    # Check that nodes have correct structure
    for node in graph_data["nodes"]:
        assert "id" in node
        assert "title" in node
        assert "type" in node

    # Check that edges have correct structure
    for edge in graph_data["edges"]:
        assert "source" in edge
        assert "target" in edge
        assert "weight" in edge


def test_extract_and_summarize(temp_project: Path) -> None:
    """Test memory extraction → summarization flow."""
    # Phase 2: Add multiple memories
    memory = Memory(temp_project)
    now = datetime.now()

    memories = [
        MemoryEntry(
            id=f"MEM-20251103-{i:03d}",
            type="decision" if i % 2 == 0 else "pattern",
            title=f"Decision {i}" if i % 2 == 0 else f"Pattern {i}",
            content=(
                f"Content describing decision {i}"
                if i % 2 == 0
                else f"Content describing pattern {i}"
            ),
            category="api" if i % 3 == 0 else "database" if i % 3 == 1 else "frontend",
            tags=["tag1", "tag2"],
            created_at=now,
            updated_at=now,
            source="git-commit",
        )
        for i in range(1, 11)
    ]

    for mem in memories:
        memory.add(mem)

    # Phase 3: Generate summary
    summarizer = MemorySummarizer(temp_project)
    summary = summarizer.summarize_project()

    # Assertions
    assert "architecture_decisions" in summary
    assert "active_patterns" in summary
    assert "statistics" in summary
    assert summary["statistics"]["total"] == 10
    # Check by_type counts
    assert "by_type" in summary["statistics"]
    assert summary["statistics"]["by_type"]["decision"] == 5
    assert summary["statistics"]["by_type"]["pattern"] == 5


def test_qa_with_linked_memories(temp_project: Path) -> None:
    """Test question answering with linked memories for better context."""
    # Phase 2: Create and link related memories
    memory = Memory(temp_project)
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20251103-001",
        type="decision",
        title="Use JWT Authentication",
        content="Implement JWT-based authentication with RS256 algorithm for API security",
        category="authentication",
        tags=["jwt", "auth", "security"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )
    mem2 = MemoryEntry(
        id="MEM-20251103-002",
        type="pattern",
        title="Token Refresh Pattern",
        content=(
            "Use short-lived access tokens (15 min) with long-lived "
            "refresh tokens for JWT authentication"
        ),
        category="authentication",
        tags=["jwt", "refresh-token", "security"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )
    mem3 = MemoryEntry(
        id="MEM-20251103-003",
        type="knowledge",
        title="Token Storage Security",
        content="JWT tokens must be stored in httpOnly cookies to prevent XSS attacks",
        category="authentication",
        tags=["jwt", "security", "cookies"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )

    memory.add(mem1)
    memory.add(mem2)
    memory.add(mem3)

    # Link memories
    linker = MemoryLinker(temp_project)
    linker.auto_link_all(threshold=0.3)

    # Phase 3: Ask question
    qa = MemoryQA(temp_project)
    answer, confidence, sources = qa.answer_question("How does our authentication system work?")

    # Assertions
    assert confidence > 0.5
    assert len(sources) >= 2  # Should reference multiple related memories
    assert "JWT" in answer or "authentication" in answer


def test_graph_export_formats(temp_project: Path) -> None:
    """Test graph visualization in multiple export formats."""
    # Phase 2: Create memories
    memory = Memory(temp_project)
    now = datetime.now()

    for i in range(1, 4):
        mem = MemoryEntry(
            id=f"MEM-20251103-{i:03d}",
            type="decision",
            title=f"Decision {i}",
            content=f"Decision content {i}",
            category="api",
            tags=["api", "rest"],
            created_at=now,
            updated_at=now,
            source="manual",
        )
        memory.add(mem)

    # Link memories
    linker = MemoryLinker(temp_project)
    linker.auto_link_all(threshold=0.3)

    # Phase 3: Export to different formats
    graph = MemoryGraph(temp_project)

    # Test Mermaid export
    mermaid_file = temp_project / "graph.md"
    graph.export_to_mermaid(mermaid_file)
    assert mermaid_file.exists()
    mermaid_content = mermaid_file.read_text()
    assert "graph TD" in mermaid_content or "graph LR" in mermaid_content
    # Mermaid format replaces hyphens, so check for the node ID without hyphens
    assert "MEM20251103001" in mermaid_content or "Decision 1" in mermaid_content

    # Test DOT export
    dot_file = temp_project / "graph.dot"
    graph.export_to_dot(dot_file)
    assert dot_file.exists()
    dot_content = dot_file.read_text()
    assert "digraph" in dot_content
    assert "MEM-20251103-001" in dot_content

    # Test JSON export
    json_file = temp_project / "graph.json"
    graph.export_to_json(json_file)
    assert json_file.exists()
    import json
    json_data = json.loads(json_file.read_text())
    assert "nodes" in json_data
    assert "edges" in json_data
    assert len(json_data["nodes"]) == 3


def test_summarizer_with_knowledge_gaps(temp_project: Path) -> None:
    """Test summarizer's ability to detect knowledge gaps."""
    # Phase 2: Add memories with incomplete coverage
    memory = Memory(temp_project)
    now = datetime.now()

    # Add only API and database decisions, no frontend
    mem1 = MemoryEntry(
        id="MEM-20251103-001",
        type="decision",
        title="REST API Design",
        content="Use RESTful API design with proper HTTP methods",
        category="api",
        tags=["api", "rest"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )
    mem2 = MemoryEntry(
        id="MEM-20251103-002",
        type="decision",
        title="Database Choice",
        content="Use PostgreSQL for the database",
        category="database",
        tags=["postgresql", "database"],
        created_at=now,
        updated_at=now,
        source="git-commit",
    )
    memory.add(mem1)
    memory.add(mem2)

    # Phase 3: Detect knowledge gaps
    summarizer = MemorySummarizer(temp_project)
    gaps = summarizer.generate_knowledge_gaps()

    # Assertions
    # Knowledge gaps returns a list of gap dictionaries
    assert isinstance(gaps, list)
    assert len(gaps) > 0  # Should detect some gaps
    # Each gap should have category, gap description, and severity
    if len(gaps) > 0:
        assert "category" in gaps[0]
        assert "gap" in gaps[0]
