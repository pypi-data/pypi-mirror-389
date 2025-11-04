"""
Tests for semantic search engine.

This module tests the SemanticSearchEngine class for KB/Tasks/Files searching.
"""

import os
from datetime import datetime

import pytest

# Auto-approve model downloads for tests
os.environ["CLAUXTON_AUTO_DOWNLOAD"] = "1"

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry, Task
from clauxton.core.task_manager import TaskManager
from clauxton.semantic.embeddings import EmbeddingEngine
from clauxton.semantic.indexer import Indexer
from clauxton.semantic.search import SearchResult, SemanticSearchEngine
from clauxton.semantic.vector_store import VectorStore

# Check if sentence-transformers is available
try:
    import sentence_transformers  # noqa: F401

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

# Check if FAISS is available
try:
    import faiss  # noqa: F401

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Skip all tests if dependencies not available
pytestmark = pytest.mark.skipif(
    not (EMBEDDINGS_AVAILABLE and FAISS_AVAILABLE),
    reason="sentence-transformers or faiss not available",
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def embedding_engine():
    """Create EmbeddingEngine instance."""
    return EmbeddingEngine()


@pytest.fixture
def vector_store():
    """Create VectorStore instance."""
    return VectorStore(dimension=384)


@pytest.fixture
def search_engine(tmp_path, embedding_engine, vector_store):
    """Create SemanticSearchEngine instance."""
    return SemanticSearchEngine(tmp_path, embedding_engine, vector_store)


@pytest.fixture
def indexed_kb(tmp_path, embedding_engine, vector_store):
    """Create indexed Knowledge Base."""
    # Create KB
    kb = KnowledgeBase(tmp_path)
    now = datetime.now()

    # Add test entries
    entries = [
        KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="FastAPI Architecture",
            category="architecture",
            content="Use FastAPI for all backend APIs with async endpoints.",
            tags=["backend", "api"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-002",
            title="PostgreSQL Database",
            category="decision",
            content="Chose PostgreSQL for relational data storage with JSONB support.",
            tags=["database", "postgresql"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-003",
            title="JWT Authentication",
            category="architecture",
            content="Implement JWT-based authentication for API endpoints.",
            tags=["auth", "security"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-004",
            title="Snake Case Naming",
            category="convention",
            content="Use snake_case for all Python functions and variables.",
            tags=["style", "python"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-005",
            title="React Frontend",
            category="architecture",
            content="Use React with TypeScript for frontend development.",
            tags=["frontend", "react"],
            created_at=now,
            updated_at=now,
        ),
    ]

    for entry in entries:
        kb.add(entry)

    # Index KB
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_knowledge_base()

    return kb


@pytest.fixture
def indexed_tasks(tmp_path, embedding_engine, vector_store):
    """Create indexed tasks."""
    # Create TaskManager
    tm = TaskManager(tmp_path)

    # Add test tasks
    tasks = [
        Task(
            id="TASK-001",
            name="Implement user authentication",
            description="Add JWT authentication to API endpoints",
            priority="high",
            status="pending",
            created_at=datetime.now(),
        ),
        Task(
            id="TASK-002",
            name="Setup PostgreSQL database",
            description="Configure PostgreSQL with proper schemas",
            priority="critical",
            status="in_progress",
            created_at=datetime.now(),
        ),
        Task(
            id="TASK-003",
            name="Build React components",
            description="Create reusable React components for UI",
            priority="medium",
            status="pending",
            created_at=datetime.now(),
        ),
        Task(
            id="TASK-004",
            name="Write API documentation",
            description="Document all API endpoints with examples",
            priority="low",
            status="completed",
            created_at=datetime.now(),
        ),
        Task(
            id="TASK-005",
            name="Fix authentication bug",
            description="Resolve token expiration issue",
            priority="high",
            status="pending",
            created_at=datetime.now(),
        ),
    ]

    for task in tasks:
        tm.add(task)

    # Index tasks
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_tasks()

    return tm


@pytest.fixture
def indexed_files(tmp_path, embedding_engine, vector_store):
    """Create indexed files."""
    # Create test files
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    files = {
        "auth.py": "def authenticate(token):\n    # JWT authentication logic\n    pass",
        "database.py": "class DatabaseConnection:\n    # PostgreSQL connection\n    pass",
        "api.py": "from fastapi import FastAPI\napp = FastAPI()",
    }

    for filename, content in files.items():
        file_path = src_dir / filename
        file_path.write_text(content)

    # Index files
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_files(["**/*.py"])

    return src_dir


# ============================================================================
# Test: Initialization
# ============================================================================


class TestSearchEngineInitialization:
    """Test SemanticSearchEngine initialization."""

    def test_initialization_default(self, tmp_path):
        """Test initialization with default components."""
        engine = SemanticSearchEngine(tmp_path)

        assert engine.project_root == tmp_path
        assert engine.semantic_dir == tmp_path / ".clauxton" / "semantic"
        assert isinstance(engine.embedding_engine, EmbeddingEngine)
        assert isinstance(engine.vector_store, VectorStore)

    def test_initialization_custom_components(
        self, tmp_path, embedding_engine, vector_store
    ):
        """Test initialization with custom components."""
        engine = SemanticSearchEngine(tmp_path, embedding_engine, vector_store)

        assert engine.project_root == tmp_path
        assert engine.embedding_engine is embedding_engine
        assert engine.vector_store is vector_store


# ============================================================================
# Test: Search Knowledge Base
# ============================================================================


class TestSearchKnowledgeBase:
    """Test KB search functionality."""

    def test_search_kb_basic(self, search_engine, indexed_kb):
        """Test basic KB search."""
        results = search_engine.search_kb("database", limit=5)

        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all("score" in r for r in results)
        assert all("source_type" in r for r in results)

        # Top result should be about PostgreSQL
        top_result = results[0]
        assert top_result["source_type"] == "kb"
        assert "PostgreSQL" in top_result["title"] or "database" in top_result["title"].lower()

    def test_search_kb_with_category_filter(self, search_engine, indexed_kb):
        """Test KB search with category filter."""
        results = search_engine.search_kb("API", limit=5, category="architecture")

        assert len(results) > 0
        # All results should be architecture category
        for result in results:
            assert result["metadata"]["category"] == "architecture"

    def test_search_kb_empty_category(self, search_engine, indexed_kb):
        """Test KB search with non-matching category filter."""
        results = search_engine.search_kb("API", limit=5, category="nonexistent")

        # Should return empty or very few results
        assert len(results) == 0

    def test_search_kb_no_index(self, search_engine):
        """Test KB search when no index exists."""
        results = search_engine.search_kb("anything", limit=5)

        assert results == []

    def test_search_kb_limit(self, search_engine, indexed_kb):
        """Test KB search respects limit."""
        results = search_engine.search_kb("architecture", limit=2)

        assert len(results) <= 2


# ============================================================================
# Test: Search Tasks
# ============================================================================


class TestSearchTasks:
    """Test task search functionality."""

    def test_search_tasks_basic(self, search_engine, indexed_tasks):
        """Test basic task search."""
        results = search_engine.search_tasks("authentication", limit=5)

        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all("score" in r for r in results)
        assert all("source_type" in r for r in results)

        # Top result should be about authentication
        top_result = results[0]
        assert top_result["source_type"] == "task"
        assert (
            "authentication" in top_result["title"].lower()
            or "auth" in top_result["title"].lower()
        )

    def test_search_tasks_with_status_filter(self, search_engine, indexed_tasks):
        """Test task search with status filter."""
        results = search_engine.search_tasks("", limit=10, status="pending")

        assert len(results) > 0
        # All results should have pending status
        for result in results:
            assert result["metadata"]["status"] == "pending"

    def test_search_tasks_with_priority_filter(self, search_engine, indexed_tasks):
        """Test task search with priority filter."""
        results = search_engine.search_tasks("", limit=10, priority="high")

        assert len(results) > 0
        # All results should have high priority
        for result in results:
            assert result["metadata"]["priority"] == "high"

    def test_search_tasks_with_both_filters(self, search_engine, indexed_tasks):
        """Test task search with both status and priority filters."""
        results = search_engine.search_tasks(
            "authentication",
            limit=5,
            status="pending",
            priority="high",
        )

        # Should find authentication tasks that are pending and high priority
        for result in results:
            assert result["metadata"]["status"] == "pending"
            assert result["metadata"]["priority"] == "high"

    def test_search_tasks_empty_results(self, search_engine, indexed_tasks):
        """Test task search with filters that match nothing."""
        results = search_engine.search_tasks(
            "authentication",
            limit=5,
            status="completed",  # Auth tasks are pending
        )

        # Should return empty or non-matching results
        assert len(results) == 0 or all("authentication" not in r["title"].lower() for r in results)


# ============================================================================
# Test: Search Files
# ============================================================================


class TestSearchFiles:
    """Test file search functionality."""

    def test_search_files_basic(self, search_engine, indexed_files):
        """Test basic file search."""
        results = search_engine.search_files("authentication", limit=10)

        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all("score" in r for r in results)
        assert all("source_type" in r for r in results)

        # Top result should be auth.py
        top_result = results[0]
        assert top_result["source_type"] == "file"
        assert "auth" in top_result["title"].lower()

    def test_search_files_with_pattern(self, search_engine, indexed_files):
        """Test file search with pattern filter."""
        results = search_engine.search_files("database", limit=10, pattern="**/*.py")

        assert len(results) > 0
        # All results should be .py files
        for result in results:
            assert result["metadata"]["file_path"].endswith(".py")

    def test_search_files_no_match_pattern(self, search_engine, indexed_files):
        """Test file search with non-matching pattern."""
        results = search_engine.search_files("database", limit=10, pattern="**/*.ts")

        # Should return empty (no TypeScript files)
        assert len(results) == 0


# ============================================================================
# Test: Unified Search
# ============================================================================


class TestSearchAll:
    """Test unified search across all sources."""

    def test_search_all_default_sources(
        self, search_engine, indexed_kb, indexed_tasks, indexed_files
    ):
        """Test search across all sources."""
        results = search_engine.search_all("authentication", limit=10)

        assert len(results) > 0

        # Should have results from multiple sources
        source_types = {r["source_type"] for r in results}
        assert len(source_types) > 1  # At least 2 different source types

    def test_search_all_specific_sources(
        self, search_engine, indexed_kb, indexed_tasks
    ):
        """Test search with specific sources only."""
        results = search_engine.search_all(
            "authentication",
            limit=10,
            sources=["kb", "task"],
        )

        assert len(results) > 0

        # Should only have KB and task results
        source_types = {r["source_type"] for r in results}
        assert source_types.issubset({"kb", "task"})
        assert "file" not in source_types

    def test_search_all_ranking(
        self, search_engine, indexed_kb, indexed_tasks, indexed_files
    ):
        """Test that results are properly ranked."""
        results = search_engine.search_all("authentication", limit=10)

        # Scores should be in descending order
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ============================================================================
# Test: Helper Methods
# ============================================================================


class TestHelperMethods:
    """Test helper methods."""

    def test_rank_results(self, search_engine):
        """Test result ranking."""
        results: list[SearchResult] = [
            {
                "score": 0.5,
                "source_type": "kb",
                "source_id": "KB-1",
                "title": "Low",
                "content": "Low score",
                "metadata": {},
            },
            {
                "score": 0.9,
                "source_type": "kb",
                "source_id": "KB-2",
                "title": "High",
                "content": "High score",
                "metadata": {},
            },
            {
                "score": 0.7,
                "source_type": "kb",
                "source_id": "KB-3",
                "title": "Medium",
                "content": "Medium score",
                "metadata": {},
            },
        ]

        ranked = search_engine._rank_results(results)

        assert ranked[0]["score"] == 0.9
        assert ranked[1]["score"] == 0.7
        assert ranked[2]["score"] == 0.5

    def test_truncate_content_short(self, search_engine):
        """Test truncate with short content."""
        content = "Short content"
        truncated = search_engine._truncate_content(content, max_length=200)

        assert truncated == content

    def test_truncate_content_long(self, search_engine):
        """Test truncate with long content."""
        content = "a" * 500
        truncated = search_engine._truncate_content(content, max_length=200)

        assert len(truncated) == 203  # 200 + "..."
        assert truncated.endswith("...")
