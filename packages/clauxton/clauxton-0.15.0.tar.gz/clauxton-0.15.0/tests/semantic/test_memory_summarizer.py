"""
Tests for MemorySummarizer (Phase 3: Memory Intelligence).

Tests cover:
- Project summarization
- Architecture decision extraction
- Pattern extraction
- Tech stack detection
- Constraint extraction
- Recent changes tracking
- Statistics calculation
- Task prediction from patterns
- Task prediction from task memories
- Task prediction from trends
- Knowledge gap detection
- Edge cases
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.core.memory import Memory, MemoryEntry
from clauxton.semantic.memory_summarizer import MemorySummarizer


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create temporary project directory."""
    clauxton_dir = tmp_path / ".clauxton"
    clauxton_dir.mkdir()
    return tmp_path


@pytest.fixture
def summarizer(
    temp_project: Path, sample_memories: list[MemoryEntry]
) -> MemorySummarizer:
    """
    Create MemorySummarizer instance.

    Depends on sample_memories to ensure they're loaded first.
    """
    # Explicitly depend on sample_memories by referencing it
    # This ensures pytest runs sample_memories fixture first
    _ = sample_memories  # noqa: F841
    return MemorySummarizer(temp_project)


@pytest.fixture
def sample_memories(temp_project: Path) -> list[MemoryEntry]:
    """Create sample memories for testing."""
    memory = Memory(temp_project)
    now = datetime.now()

    memories = [
        # Decision memories
        MemoryEntry(
            id="MEM-20251103-001",
            type="decision",
            title="Switch to PostgreSQL",
            content="Migrate from MySQL to PostgreSQL for better JSON support and performance",
            category="database",
            tags=["postgresql", "migration", "database"],
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5),
            source="manual",
        ),
        MemoryEntry(
            id="MEM-20251103-002",
            type="decision",
            title="Use JWT for authentication",
            content=(
                "Implement JWT-based authentication with refresh tokens. "
                "Must use RS256 algorithm"
            ),
            category="authentication",
            tags=["jwt", "auth", "security"],
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3),
            source="git-commit",
        ),
        # Pattern memories
        MemoryEntry(
            id="MEM-20251103-003",
            type="pattern",
            title="API changes in 5 files",
            content="Pattern detected: api\nFiles affected: 5",
            category="api",
            tags=["api", "auto-detected"],
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2),
            source="code-analysis",
        ),
        MemoryEntry(
            id="MEM-20251103-004",
            type="pattern",
            title="UI changes in 8 files",
            content="Pattern detected: ui\nFiles affected: 8",
            category="ui",
            tags=["ui", "auto-detected"],
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
            source="code-analysis",
        ),
        # Knowledge memory
        MemoryEntry(
            id="MEM-20251103-005",
            type="knowledge",
            title="API Design Pattern",
            content="Use RESTful API design with versioning. Python FastAPI framework required",
            category="architecture",
            tags=["api", "rest", "design"],
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=10),
            source="manual",
        ),
        # Task memory
        MemoryEntry(
            id="MEM-20251103-006",
            type="task",
            title="Implement user registration endpoint",
            content="Create /api/v1/users/register endpoint with validation",
            category="api",
            tags=["pending", "api", "backend"],
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
            source="manual",
        ),
        # Code memory
        MemoryEntry(
            id="MEM-20251103-007",
            type="code",
            title="UserService class",
            content="User management service with CRUD operations. Uses PostgreSQL",
            category="backend",
            tags=["service", "user", "crud"],
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=4),
            source="code-analysis",
        ),
    ]

    for mem in memories:
        memory.add(mem)

    return memories


def test_summarizer_initialization(temp_project: Path) -> None:
    """Test MemorySummarizer initialization."""
    summarizer = MemorySummarizer(temp_project)

    assert summarizer.project_root == temp_project
    assert summarizer.memory is not None
    assert isinstance(summarizer.memory, Memory)


def test_summarize_project(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test comprehensive project summarization."""
    summary = summarizer.summarize_project()

    # Check all sections exist
    assert "architecture_decisions" in summary
    assert "active_patterns" in summary
    assert "tech_stack" in summary
    assert "constraints" in summary
    assert "recent_changes" in summary
    assert "statistics" in summary

    # Check decisions
    decisions = summary["architecture_decisions"]
    assert len(decisions) == 2  # 2 decision memories
    assert any(d["title"] == "Switch to PostgreSQL" for d in decisions)
    assert any(d["title"] == "Use JWT for authentication" for d in decisions)

    # Check patterns
    patterns = summary["active_patterns"]
    assert len(patterns) == 2  # 2 pattern memories
    assert any(p["category"] == "api" for p in patterns)
    assert any(p["category"] == "ui" for p in patterns)

    # Check tech stack
    tech_stack = summary["tech_stack"]
    assert "PostgreSQL" in tech_stack
    assert "FastAPI" in tech_stack

    # Check statistics
    stats = summary["statistics"]
    assert stats["total"] == 7  # 7 total memories
    assert stats["by_type"]["decision"] == 2
    assert stats["by_type"]["pattern"] == 2
    assert stats["by_type"]["task"] == 1


def test_extract_decisions(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test architecture decision extraction."""
    decisions = summarizer._extract_decisions(sample_memories)

    assert len(decisions) == 2
    assert all(isinstance(d, dict) for d in decisions)
    assert all("id" in d for d in decisions)
    assert all("title" in d for d in decisions)
    assert all("content" in d for d in decisions)
    assert all("date" in d for d in decisions)

    # Check first decision
    first = decisions[0]  # Most recent (sorted by created_at desc)
    assert first["title"] == "Use JWT for authentication"
    assert len(first["content"]) <= 200  # Truncated


def test_extract_patterns(summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]) -> None:
    """Test active pattern extraction."""
    patterns = summarizer._extract_patterns(sample_memories)

    assert len(patterns) == 2
    assert all(isinstance(p, dict) for p in patterns)
    assert all("id" in p for p in patterns)
    assert all("title" in p for p in patterns)
    assert all("category" in p for p in patterns)

    # Check categories
    categories = [p["category"] for p in patterns]
    assert "api" in categories
    assert "ui" in categories


def test_extract_tech_stack(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test tech stack extraction from memories."""
    tech_stack = summarizer._extract_tech_stack(sample_memories)

    assert isinstance(tech_stack, list)
    assert len(tech_stack) > 0
    assert "PostgreSQL" in tech_stack
    assert "FastAPI" in tech_stack
    assert "Python" in tech_stack

    # Check it's sorted
    assert tech_stack == sorted(tech_stack)


def test_extract_tech_stack_with_various_technologies(temp_project: Path) -> None:
    """Test tech stack extraction with various technologies."""
    memory = Memory(temp_project)
    now = datetime.now()

    # Add memory with various tech keywords
    memory.add(
        MemoryEntry(
            id="MEM-20251103-100",
            type="knowledge",
            title="Tech Stack Overview",
            content=(
                "Using React for frontend with TypeScript. "
                "Backend uses Node.js with Express. "
                "Database is MongoDB with Redis for caching. "
                "Deployed on AWS with Docker and Kubernetes."
            ),
            category="architecture",
            tags=["tech-stack"],
            created_at=now,
            updated_at=now,
            source="manual",
        )
    )

    summarizer = MemorySummarizer(temp_project)
    tech_stack = summarizer._extract_tech_stack(summarizer.memory.list_all())

    assert "React" in tech_stack
    assert "Typescript" in tech_stack
    assert "Node.js" in tech_stack
    assert "Express" in tech_stack
    assert "MongoDB" in tech_stack
    assert "Redis" in tech_stack
    assert "AWS" in tech_stack
    assert "Docker" in tech_stack
    assert "Kubernetes" in tech_stack


def test_extract_constraints(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test project constraint extraction."""
    constraints = summarizer._extract_constraints(sample_memories)

    assert isinstance(constraints, list)
    assert len(constraints) <= 5  # Limited to 5

    # Should find JWT constraint
    assert any("JWT" in c or "required" in c.lower() for c in constraints)


def test_extract_recent_changes(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test recent changes extraction."""
    recent = summarizer._extract_recent_changes(sample_memories, days=7)

    assert isinstance(recent, list)
    assert len(recent) > 0
    assert all(isinstance(r, dict) for r in recent)
    assert all("id" in r for r in recent)
    assert all("title" in r for r in recent)
    assert all("type" in r for r in recent)
    assert all("date" in r for r in recent)

    # Should be sorted by date descending (most recent first)
    if len(recent) >= 2:
        dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in recent]
        assert dates[0] >= dates[1]


def test_extract_recent_changes_with_cutoff(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test recent changes with different cutoff periods."""
    # 3 days: should get fewer memories
    recent_3 = summarizer._extract_recent_changes(sample_memories, days=3)
    # 30 days: should get all memories
    recent_30 = summarizer._extract_recent_changes(sample_memories, days=30)

    assert len(recent_3) < len(recent_30)
    assert len(recent_30) == len(sample_memories)


def test_calculate_statistics(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test memory statistics calculation."""
    stats = summarizer._calculate_statistics(sample_memories)

    assert isinstance(stats, dict)
    assert "total" in stats
    assert "by_type" in stats
    assert "by_category" in stats
    assert "with_relationships" in stats

    assert stats["total"] == 7
    assert stats["by_type"]["decision"] == 2
    assert stats["by_type"]["pattern"] == 2
    assert stats["by_type"]["knowledge"] == 1
    assert stats["by_type"]["task"] == 1
    assert stats["by_type"]["code"] == 1


def test_predict_from_patterns(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test task prediction from pattern analysis."""
    predictions = summarizer._predict_from_patterns(sample_memories)

    assert isinstance(predictions, list)
    assert len(predictions) > 0
    assert all(isinstance(p, dict) for p in predictions)
    assert all("title" in p for p in predictions)
    assert all("reason" in p for p in predictions)
    assert all("priority" in p for p in predictions)
    assert all("confidence" in p for p in predictions)

    # Should suggest authentication tests (auth pattern without tests)
    assert any("test" in p["title"].lower() for p in predictions)


def test_predict_from_tasks(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test task prediction from existing task memories."""
    predictions = summarizer._predict_from_tasks(sample_memories)

    assert isinstance(predictions, list)
    # Should find the pending task
    assert any("registration" in p["title"].lower() for p in predictions)
    # Should have high confidence for pending tasks
    assert all(p["confidence"] >= 0.8 for p in predictions)


def test_predict_from_trends(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test task prediction from recent activity trends."""
    predictions = summarizer._predict_from_trends(sample_memories)

    assert isinstance(predictions, list)
    assert len(predictions) > 0

    # Should identify most active category
    assert all("confidence" in p for p in predictions)
    assert all(0.0 <= p["confidence"] <= 1.0 for p in predictions)


def test_predict_next_tasks(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test comprehensive next task prediction."""
    predictions = summarizer.predict_next_tasks(limit=5)

    assert isinstance(predictions, list)
    assert len(predictions) <= 5
    assert all(isinstance(p, dict) for p in predictions)
    assert all("title" in p for p in predictions)
    assert all("reason" in p for p in predictions)
    assert all("priority" in p for p in predictions)
    assert all("confidence" in p for p in predictions)

    # Should be sorted by confidence descending
    if len(predictions) >= 2:
        confidences = [p["confidence"] for p in predictions]
        assert confidences[0] >= confidences[1]


def test_predict_next_tasks_with_context(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test task prediction with context filter."""
    # Predict with "api" context
    api_predictions = summarizer.predict_next_tasks(context="api", limit=5)

    assert isinstance(api_predictions, list)
    # Should only suggest API-related tasks
    # (or tasks from memories that mention "api")


def test_predict_next_tasks_no_duplicates(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test that predictions don't contain duplicate titles."""
    predictions = summarizer.predict_next_tasks(limit=10)

    titles = [p["title"].lower() for p in predictions]
    assert len(titles) == len(set(titles))  # No duplicates


def test_generate_knowledge_gaps(
    summarizer: MemorySummarizer, sample_memories: list[MemoryEntry]
) -> None:
    """Test knowledge gap detection."""
    gaps = summarizer.generate_knowledge_gaps()

    assert isinstance(gaps, list)
    assert len(gaps) > 0
    assert all(isinstance(g, dict) for g in gaps)
    assert all("category" in g for g in gaps)
    assert all("gap" in g for g in gaps)
    assert all("severity" in g for g in gaps)

    # Should detect missing testing category
    assert any(g["category"] == "testing" for g in gaps)

    # Should detect missing deployment category
    assert any(g["category"] == "deployment" for g in gaps)

    # Check severity levels
    severities = {g["severity"] for g in gaps}
    assert severities.issubset({"high", "medium", "low"})


def test_generate_knowledge_gaps_with_complete_project(temp_project: Path) -> None:
    """Test knowledge gap detection with complete project."""
    memory = Memory(temp_project)
    now = datetime.now()

    # Add memories for all expected categories
    categories = ["authentication", "api", "database", "testing", "deployment"]

    for i, category in enumerate(categories):
        memory.add(
            MemoryEntry(
                id=f"MEM-20251103-{i+200:03d}",
                type="knowledge",
                title=f"{category.capitalize()} Guide",
                content=f"Documentation for {category} with error handling and security",
                category=category,
                tags=[category],
                created_at=now,
                updated_at=now,
                source="manual",
            )
        )

    summarizer = MemorySummarizer(temp_project)
    gaps = summarizer.generate_knowledge_gaps()

    # Should have fewer gaps since we added all expected categories
    # But may still have gaps for specific topics like performance
    assert isinstance(gaps, list)


def test_summarize_empty_project(temp_project: Path) -> None:
    """Test summarization with no memories."""
    summarizer = MemorySummarizer(temp_project)
    summary = summarizer.summarize_project()

    assert summary["architecture_decisions"] == []
    assert summary["active_patterns"] == []
    assert summary["tech_stack"] == []
    assert summary["constraints"] == []
    assert summary["recent_changes"] == []
    assert summary["statistics"]["total"] == 0


def test_predict_next_tasks_empty_project(temp_project: Path) -> None:
    """Test task prediction with no memories."""
    summarizer = MemorySummarizer(temp_project)
    predictions = summarizer.predict_next_tasks(limit=5)

    assert isinstance(predictions, list)
    assert len(predictions) == 0  # No predictions without data


def test_knowledge_gaps_empty_project(temp_project: Path) -> None:
    """Test knowledge gap detection with no memories."""
    summarizer = MemorySummarizer(temp_project)
    gaps = summarizer.generate_knowledge_gaps()

    assert isinstance(gaps, list)
    assert len(gaps) > 0  # Should detect all missing categories

    # Should detect all expected categories as missing
    expected = ["authentication", "api", "database", "testing", "deployment"]
    gap_categories = {g["category"] for g in gaps}
    for category in expected:
        assert category in gap_categories


def test_summarize_project_with_relationships(temp_project: Path) -> None:
    """Test summarization with memories that have relationships."""
    memory = Memory(temp_project)
    now = datetime.now()

    # Add memories with relationships
    mem1 = MemoryEntry(
        id="MEM-20251103-300",
        type="decision",
        title="Database Choice",
        content="Use PostgreSQL",
        category="database",
        tags=["database"],
        created_at=now,
        updated_at=now,
        source="manual",
    )
    memory.add(mem1)

    mem2 = MemoryEntry(
        id="MEM-20251103-301",
        type="pattern",
        title="Database Migration Pattern",
        content="Migration pattern for PostgreSQL",
        category="database",
        tags=["database", "migration"],
        related_to=["MEM-20251103-300"],
        created_at=now,
        updated_at=now,
        source="code-analysis",
    )
    memory.add(mem2)

    summarizer = MemorySummarizer(temp_project)
    summary = summarizer.summarize_project()

    # Check statistics include relationship count
    assert summary["statistics"]["with_relationships"] == 1


def test_performance_large_project(temp_project: Path) -> None:
    """Test performance with large number of memories."""
    import time

    memory = Memory(temp_project)
    now = datetime.now()

    # Add 100 memories
    for i in range(100):
        memory.add(
            MemoryEntry(
                id=f"MEM-20251103-{i+400:03d}",
                type="knowledge",
                title=f"Memory {i}",
                content=f"Content for memory {i} with various keywords like python, api, database",
                category="general",
                tags=["test"],
                created_at=now - timedelta(days=i % 30),
                updated_at=now - timedelta(days=i % 30),
                source="manual",
            )
        )

    summarizer = MemorySummarizer(temp_project)

    # Test summarization performance (should be <1s)
    start = time.time()
    summary = summarizer.summarize_project()
    duration = time.time() - start

    assert duration < 1.0  # Should complete in under 1 second
    assert summary["statistics"]["total"] == 100

    # Test prediction performance
    start = time.time()
    summarizer.predict_next_tasks(limit=5)
    duration = time.time() - start

    assert duration < 1.0  # Should complete in under 1 second
