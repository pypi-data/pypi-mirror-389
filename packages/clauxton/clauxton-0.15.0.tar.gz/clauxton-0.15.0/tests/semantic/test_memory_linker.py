"""
Tests for Memory Relationship Detection (MemoryLinker).

Tests cover:
- Relationship detection by tags, content, category, temporal proximity
- Auto-linking all memories
- Merge candidate detection
- Similarity calculations (content, tags, temporal)
- Edge cases (empty lists, missing fields, self-linking)
- Performance with large datasets
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.core.memory import MemoryEntry
from clauxton.semantic.memory_linker import MemoryLinker


@pytest.fixture
def memory_linker(tmp_path: Path) -> MemoryLinker:
    """Create MemoryLinker with temporary project."""
    return MemoryLinker(tmp_path)


@pytest.fixture
def sample_memories() -> list[MemoryEntry]:
    """Create sample memories for testing."""
    now = datetime.now()
    return [
        MemoryEntry(
            id="MEM-20260127-001",
            type="knowledge",
            title="API Design Pattern",
            content="Use RESTful API design with versioning for all endpoints",
            category="architecture",
            tags=["api", "rest", "design"],
            created_at=now,
            updated_at=now,
            source="manual",
        ),
        MemoryEntry(
            id="MEM-20260127-002",
            type="knowledge",
            title="REST API Guidelines",
            content="Follow REST best practices including proper HTTP verbs and status codes",
            category="architecture",
            tags=["api", "rest", "guidelines"],
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
            source="manual",
        ),
        MemoryEntry(
            id="MEM-20260127-003",
            type="decision",
            title="Database Choice",
            content="Selected PostgreSQL for relational data storage with ACID guarantees",
            category="database",
            tags=["database", "postgresql", "decision"],
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3),
            source="manual",
        ),
        MemoryEntry(
            id="MEM-20260127-004",
            type="pattern",
            title="Authentication Pattern",
            content="Use JWT tokens for authentication with refresh token rotation",
            category="security",
            tags=["authentication", "jwt", "security"],
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=10),
            source="manual",
        ),
    ]


def test_find_relationships_by_tags(
    memory_linker: MemoryLinker, sample_memories: list[MemoryEntry]
) -> None:
    """Test finding relationships by shared tags."""
    # Add memories
    for mem in sample_memories:
        memory_linker.memory.add(mem)

    # Find relationships for first memory (has tags: api, rest, design)
    related_ids = memory_linker.find_relationships(sample_memories[0], threshold=0.2)

    # Should find memory 2 (shares "api" and "rest" tags)
    assert "MEM-20260127-002" in related_ids
    # Should not find memory 3 (no shared tags)
    assert "MEM-20260127-003" not in related_ids


def test_find_relationships_by_content(
    memory_linker: MemoryLinker, sample_memories: list[MemoryEntry]
) -> None:
    """Test finding relationships by content similarity."""
    # Add memories
    for mem in sample_memories:
        memory_linker.memory.add(mem)

    # Find relationships for first memory (about REST API)
    related_ids = memory_linker.find_relationships(sample_memories[0], threshold=0.2)

    # Should find memory 2 (similar content about REST API)
    assert "MEM-20260127-002" in related_ids


def test_find_relationships_by_category(
    memory_linker: MemoryLinker, sample_memories: list[MemoryEntry]
) -> None:
    """Test finding relationships by same category."""
    # Add memories
    for mem in sample_memories:
        memory_linker.memory.add(mem)

    # Find relationships for first memory (category: architecture)
    related_ids = memory_linker.find_relationships(sample_memories[0], threshold=0.15)

    # Should find memory 2 (same category: architecture)
    assert "MEM-20260127-002" in related_ids


def test_find_relationships_with_threshold(
    memory_linker: MemoryLinker, sample_memories: list[MemoryEntry]
) -> None:
    """Test threshold filtering in relationship detection."""
    # Add memories
    for mem in sample_memories:
        memory_linker.memory.add(mem)

    # High threshold (strict)
    strict_related = memory_linker.find_relationships(sample_memories[0], threshold=0.5)

    # Low threshold (lenient)
    lenient_related = memory_linker.find_relationships(sample_memories[0], threshold=0.1)

    # Lenient should find more or equal relationships
    assert len(lenient_related) >= len(strict_related)


def test_auto_link_all(memory_linker: MemoryLinker, sample_memories: list[MemoryEntry]) -> None:
    """Test auto-linking all memories."""
    # Add memories
    for mem in sample_memories:
        memory_linker.memory.add(mem)

    # Auto-link all memories
    links_created = memory_linker.auto_link_all(threshold=0.2)

    # Should create at least some links
    assert links_created > 0

    # Verify relationships were created
    entry1 = memory_linker.memory.get("MEM-20260127-001")
    assert entry1 is not None
    assert len(entry1.related_to) > 0


def test_auto_link_preserves_existing_relationships(memory_linker: MemoryLinker) -> None:
    """Test that auto-link preserves existing relationships."""
    now = datetime.now()

    # Create memories with existing relationship
    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
        related_to=["MEM-20260127-999"],  # Pre-existing relationship
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="API Guidelines",
        content="REST API best practices",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    memory_linker.memory.add(mem1)
    memory_linker.memory.add(mem2)

    # Auto-link
    memory_linker.auto_link_all(threshold=0.2)

    # Check that pre-existing relationship is preserved
    updated_mem1 = memory_linker.memory.get("MEM-20260127-001")
    assert updated_mem1 is not None
    assert "MEM-20260127-999" in updated_mem1.related_to


def test_suggest_merge_candidates_high_similarity(memory_linker: MemoryLinker) -> None:
    """Test merge candidate detection for near-duplicates."""
    now = datetime.now()

    # Create nearly identical memories
    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design Pattern",
        content="Use RESTful API design with versioning",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="API Design Patterns",  # Almost identical title
        content="Use RESTful API design with versioning for endpoints",  # Similar content
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    memory_linker.memory.add(mem1)
    memory_linker.memory.add(mem2)

    # Find merge candidates
    candidates = memory_linker.suggest_merge_candidates(threshold=0.7)

    # Should find these as merge candidates
    assert len(candidates) > 0
    assert any(
        (id1, id2)
        in [
            ("MEM-20260127-001", "MEM-20260127-002"),
            ("MEM-20260127-002", "MEM-20260127-001"),
        ]
        for id1, id2, _ in candidates
    )


def test_suggest_merge_candidates_different_types(memory_linker: MemoryLinker) -> None:
    """Test that merge candidates require same type."""
    now = datetime.now()

    # Create similar memories with different types
    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="decision",  # Different type
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    memory_linker.memory.add(mem1)
    memory_linker.memory.add(mem2)

    # Find merge candidates
    candidates = memory_linker.suggest_merge_candidates(threshold=0.7)

    # Should NOT suggest merge (different types)
    assert len(candidates) == 0


def test_temporal_similarity_within_window(memory_linker: MemoryLinker) -> None:
    """Test temporal similarity for memories within 7-day window."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=[],
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3),
        source="manual",
    )

    # Calculate temporal similarity
    temporal_sim = memory_linker._temporal_similarity(mem1, mem2)

    # Should be high (within 7-day window)
    assert temporal_sim > 0.4  # 3 days within 7-day window


def test_temporal_similarity_outside_window(memory_linker: MemoryLinker) -> None:
    """Test temporal similarity for memories outside 7-day window."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=[],
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=10),
        source="manual",
    )

    # Calculate temporal similarity
    temporal_sim = memory_linker._temporal_similarity(mem1, mem2)

    # Should be zero (outside 7-day window)
    assert temporal_sim == 0.0


def test_content_similarity_tfidf(memory_linker: MemoryLinker) -> None:
    """Test content similarity using TF-IDF."""
    now = datetime.now()

    # Similar content
    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="Use RESTful API design with proper HTTP verbs and status codes",
        category="architecture",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="REST Guidelines",
        content="Follow REST API best practices including HTTP methods and response codes",
        category="architecture",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    similarity = memory_linker._content_similarity(mem1, mem2)

    # Should have significant similarity
    assert similarity > 0.1


def test_content_similarity_different_content(memory_linker: MemoryLinker) -> None:
    """Test content similarity for completely different content."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="Use RESTful API design patterns",
        category="architecture",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Database Schema",
        content="PostgreSQL relational database with normalized tables",
        category="database",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    similarity = memory_linker._content_similarity(mem1, mem2)

    # Should have low similarity
    assert similarity < 0.3


def test_tag_similarity_jaccard(memory_linker: MemoryLinker) -> None:
    """Test tag similarity using Jaccard index."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=["api", "rest", "design"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=["api", "rest", "security"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    similarity = memory_linker._tag_similarity(mem1, mem2)

    # Jaccard = 2 (shared) / 4 (total unique) = 0.5
    assert similarity == 0.5


def test_tag_similarity_no_tags(memory_linker: MemoryLinker) -> None:
    """Test tag similarity when one or both have no tags."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Test",
        content="Content",
        category="test",
        tags=[],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    similarity = memory_linker._tag_similarity(mem1, mem2)

    # Should be zero (no overlap possible)
    assert similarity == 0.0


def test_self_linking_prevention(memory_linker: MemoryLinker) -> None:
    """Test that a memory doesn't link to itself."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    memory_linker.memory.add(mem1)

    # Find relationships
    related_ids = memory_linker.find_relationships(mem1, threshold=0.0)

    # Should NOT include itself
    assert "MEM-20260127-001" not in related_ids


def test_empty_memory_list(memory_linker: MemoryLinker) -> None:
    """Test relationship detection with empty memory list."""
    now = datetime.now()

    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    # Find relationships in empty list
    related_ids = memory_linker.find_relationships(mem1, existing_memories=[], threshold=0.2)

    # Should return empty list
    assert len(related_ids) == 0


def test_relationship_ranking(memory_linker: MemoryLinker) -> None:
    """Test that relationships are ranked by similarity."""
    now = datetime.now()

    # Create memories with varying similarity to target
    target = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns with versioning",
        category="architecture",
        tags=["api", "rest", "design"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    # Very similar
    mem_high = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="REST API Design",
        content="REST API design patterns with proper versioning",
        category="architecture",
        tags=["api", "rest", "design"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    # Somewhat similar
    mem_medium = MemoryEntry(
        id="MEM-20260127-003",
        type="knowledge",
        title="API Guidelines",
        content="General API best practices",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    # Less similar
    mem_low = MemoryEntry(
        id="MEM-20260127-004",
        type="knowledge",
        title="Database Schema",
        content="PostgreSQL database design",
        category="database",
        tags=["database"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    memory_linker.memory.add(target)
    memory_linker.memory.add(mem_high)
    memory_linker.memory.add(mem_medium)
    memory_linker.memory.add(mem_low)

    # Find relationships
    related_ids = memory_linker.find_relationships(target, threshold=0.1)

    # Most similar should be first
    if len(related_ids) > 0:
        assert related_ids[0] == "MEM-20260127-002"


def test_performance_large_dataset(memory_linker: MemoryLinker) -> None:
    """Test performance with 1000 memories."""
    now = datetime.now()

    # Create 1000 memories
    for i in range(1000):
        mem = MemoryEntry(
            id=f"MEM-20260127-{i+1:03d}",
            type="knowledge",
            title=f"Memory {i}",
            content=f"Content for memory {i} with some random text",
            category="test",
            tags=["test", f"tag{i % 10}"],
            created_at=now - timedelta(days=i % 30),
            updated_at=now - timedelta(days=i % 30),
            source="manual",
        )
        memory_linker.memory.add(mem)

    # Measure auto-link performance
    start_time = time.time()
    memory_linker.auto_link_all(threshold=0.3)
    elapsed_time = time.time() - start_time

    # Should complete in reasonable time (<30 seconds for 1000 entries)
    assert elapsed_time < 30.0


def test_threshold_behavior(memory_linker: MemoryLinker) -> None:
    """Test that higher thresholds return fewer results."""
    now = datetime.now()

    # Create target memory
    target = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    # Create related memories with varying similarity
    for i in range(2, 6):
        mem = MemoryEntry(
            id=f"MEM-20260127-{i:03d}",
            type="knowledge",
            title=f"Related Memory {i}",
            content="REST API design patterns" if i == 2 else f"Content {i}",
            category="architecture" if i <= 3 else "other",
            tags=["api"] if i <= 4 else ["other"],
            created_at=now,
            updated_at=now,
            source="manual",
        )
        memory_linker.memory.add(mem)

    memory_linker.memory.add(target)

    # Test with different thresholds
    low_threshold = memory_linker.find_relationships(target, threshold=0.1)
    high_threshold = memory_linker.find_relationships(target, threshold=0.5)

    # Higher threshold should return fewer or equal results
    assert len(high_threshold) <= len(low_threshold)


def test_different_memory_types(memory_linker: MemoryLinker) -> None:
    """Test relationship detection across different memory types."""
    now = datetime.now()

    # Create memories of different types
    mem_knowledge = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design Pattern",
        content="REST API design with versioning",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem_decision = MemoryEntry(
        id="MEM-20260127-002",
        type="decision",
        title="Use REST API",
        content="Decided to use REST API design for all endpoints",
        category="architecture",
        tags=["api"],
        created_at=now,
        updated_at=now,
        source="manual",
    )

    memory_linker.memory.add(mem_knowledge)
    memory_linker.memory.add(mem_decision)

    # Find relationships
    related_ids = memory_linker.find_relationships(mem_knowledge, threshold=0.2)

    # Should find relationship despite different types (same category, tags, content)
    assert "MEM-20260127-002" in related_ids


def test_normalized_levenshtein(memory_linker: MemoryLinker) -> None:
    """Test normalized Levenshtein distance calculation."""
    # Identical strings
    assert memory_linker._normalized_levenshtein("test", "test") == 1.0

    # Completely different
    assert memory_linker._normalized_levenshtein("abc", "xyz") < 0.3

    # Similar strings
    similarity = memory_linker._normalized_levenshtein("API Design Pattern", "API Design Patterns")
    assert similarity > 0.8  # Very similar (one letter difference)

    # Empty strings
    assert memory_linker._normalized_levenshtein("", "") == 0.0
    assert memory_linker._normalized_levenshtein("test", "") == 0.0


def test_weighted_scoring(memory_linker: MemoryLinker) -> None:
    """Test that weighted scoring combines all signals correctly."""
    now = datetime.now()

    # Create memories with known similarity signals
    mem1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",
        tags=["api", "rest"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    mem2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="API Design",
        content="REST API design patterns",
        category="architecture",  # Same category = 0.2 weight
        tags=["api", "rest"],     # Same tags = 0.3 weight (Jaccard = 1.0)
        created_at=now,           # Same time = 0.1 weight (temporal = 1.0)
        updated_at=now,
        source="manual",
    )

    # Calculate overall similarity
    similarity = memory_linker._calculate_similarity(mem1, mem2)

    # Should have high similarity (all signals match)
    # Content + Tags + Category + Temporal = high score
    assert similarity > 0.5
