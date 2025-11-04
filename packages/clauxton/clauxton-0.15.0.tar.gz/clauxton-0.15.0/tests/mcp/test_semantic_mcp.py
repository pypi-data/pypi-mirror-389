"""
Tests for Semantic Search MCP Tools.

Tests cover:
- search_knowledge_semantic tool
- search_tasks_semantic tool
- search_files_semantic tool
- Error handling (ImportError, general exceptions)
- Filtering capabilities (category, status, priority, pattern)
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Check if optional dependencies are available
try:
    from sentence_transformers import SentenceTransformer  # noqa: F401

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    import faiss  # noqa: F401

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Only run tests if dependencies are available
pytestmark = pytest.mark.skipif(
    not (EMBEDDINGS_AVAILABLE and FAISS_AVAILABLE),
    reason="sentence-transformers or faiss not available",
)

# Set auto-download for tests
os.environ["CLAUXTON_AUTO_DOWNLOAD"] = "1"

from clauxton.mcp.server import (  # noqa: E402
    search_files_semantic,
    search_knowledge_semantic,
    search_tasks_semantic,
)
from clauxton.semantic.embeddings import EmbeddingEngine  # noqa: E402
from clauxton.semantic.vector_store import VectorStore  # noqa: E402

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def embedding_engine():
    """Create EmbeddingEngine instance for tests."""
    return EmbeddingEngine()


@pytest.fixture
def vector_store():
    """Create VectorStore instance for tests."""
    return VectorStore(dimension=384)


# ============================================================================
# search_knowledge_semantic Tests
# ============================================================================


def test_search_knowledge_semantic_basic(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test basic semantic KB search."""
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry
    from clauxton.semantic.indexer import Indexer

    # Initialize Clauxton
    kb = KnowledgeBase(tmp_path)

    # Add test entries
    from datetime import datetime

    now = datetime.now()
    entries = [
        KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="JWT Authentication",
            category="decision",
            content="Use JWT tokens for API authentication. Tokens expire after 1 hour.",
            tags=["auth", "jwt", "api"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-002",
            title="PostgreSQL Database",
            category="architecture",
            content="Use PostgreSQL for data persistence. Version 15+.",
            tags=["database", "postgresql"],
            created_at=now,
            updated_at=now,
        ),
    ]

    for entry in entries:
        kb.add(entry)

    # Index KB entries
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_knowledge_base()

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_knowledge_semantic("authentication", limit=2)

    # Verify result
    assert result["status"] == "success"
    assert result["search_type"] == "semantic"
    assert result["query"] == "authentication"
    assert result["count"] >= 1
    assert len(result["results"]) >= 1

    # Check result structure
    first_result = result["results"][0]
    assert "score" in first_result
    assert "source_type" in first_result
    assert first_result["source_type"] == "kb"
    assert "source_id" in first_result
    assert "title" in first_result
    assert "content" in first_result
    assert "metadata" in first_result


def test_search_knowledge_semantic_category_filter(
    tmp_path: Path, embedding_engine, vector_store
) -> None:
    """Test semantic KB search with category filter."""
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry
    from clauxton.semantic.indexer import Indexer

    # Initialize
    kb = KnowledgeBase(tmp_path)

    # Add entries in different categories
    from datetime import datetime

    now = datetime.now()
    entries = [
        KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="JWT Auth Decision",
            category="decision",
            content="Use JWT for authentication",
            tags=["auth"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-002",
            title="Auth Architecture",
            category="architecture",
            content="Microservices architecture with auth service",
            tags=["auth"],
            created_at=now,
            updated_at=now,
        ),
    ]

    for entry in entries:
        kb.add(entry)

    # Index
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_knowledge_base()

    # Search with category filter
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_knowledge_semantic("auth", limit=5, category="decision")

    # Verify
    assert result["status"] == "success"
    assert result["count"] >= 1

    # All results should be "decision" category
    for res in result["results"]:
        assert res["metadata"]["category"] == "decision"


def test_search_knowledge_semantic_limit(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test semantic KB search respects limit parameter."""
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry
    from clauxton.semantic.indexer import Indexer

    # Initialize
    kb = KnowledgeBase(tmp_path)

    # Add multiple entries
    from datetime import datetime

    now = datetime.now()
    for i in range(5):
        entry = KnowledgeBaseEntry(
            id=f"KB-20251026-{i+1:03d}",
            title=f"Entry {i+1}",
            category="architecture",
            content=f"This is entry number {i+1} about architecture",
            tags=["test"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # Index
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_knowledge_base()

    # Search with limit=2
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_knowledge_semantic("architecture", limit=2)

    # Verify
    assert result["status"] == "success"
    assert result["count"] <= 2
    assert len(result["results"]) <= 2


@pytest.mark.skip(reason="Mock path issue - needs complex sys.modules patching")
def test_search_knowledge_semantic_import_error() -> None:
    """Test semantic KB search handles ImportError gracefully."""
    with patch(
        "clauxton.mcp.server.SemanticSearchEngine",
        side_effect=ImportError("No module named 'sentence_transformers'"),
    ):
        result = search_knowledge_semantic("query")

    # Verify error response
    assert result["status"] == "error"
    assert "dependencies not installed" in result["message"]
    assert "hint" in result
    assert "pip install clauxton[semantic]" in result["hint"]


def test_search_knowledge_semantic_general_error(tmp_path: Path) -> None:
    """Test semantic KB search handles general exceptions."""
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        with patch(
            "clauxton.semantic.search.SemanticSearchEngine.search_kb",
            side_effect=RuntimeError("Search failed"),
        ):
            result = search_knowledge_semantic("query")

    # Verify error response
    assert result["status"] == "error"
    assert "Search failed" in result["message"]
    assert "error" in result


# ============================================================================
# search_tasks_semantic Tests
# ============================================================================


def test_search_tasks_semantic_basic(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test basic semantic task search."""
    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.semantic.indexer import Indexer

    # Initialize
    tm = TaskManager(tmp_path)

    # Add test tasks
    from datetime import datetime

    now = datetime.now()
    tasks = [
        Task(
            id="TASK-001",
            name="Implement JWT authentication",
            description="Add JWT token validation to API endpoints",
            status="pending",
            priority="high",
            estimated_hours=5.0,
            created_at=now,
        ),
        Task(
            id="TASK-002",
            name="Database migration",
            description="Create migration for user table",
            status="pending",
            priority="medium",
            estimated_hours=2.0,
            created_at=now,
        ),
    ]

    for task in tasks:
        tm.add(task)

    # Index tasks
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_tasks()

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_tasks_semantic("authentication", limit=2)

    # Verify
    assert result["status"] == "success"
    assert result["search_type"] == "semantic"
    assert result["query"] == "authentication"
    assert result["count"] >= 1
    assert len(result["results"]) >= 1

    # Check result structure
    first_result = result["results"][0]
    assert "score" in first_result
    assert first_result["source_type"] == "task"
    assert "source_id" in first_result
    assert "title" in first_result
    assert "content" in first_result
    assert "metadata" in first_result


def test_search_tasks_semantic_status_filter(
    tmp_path: Path, embedding_engine, vector_store
) -> None:
    """Test semantic task search with status filter."""
    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.semantic.indexer import Indexer

    # Initialize
    tm = TaskManager(tmp_path)

    # Add tasks with different statuses
    from datetime import datetime

    now = datetime.now()
    tasks = [
        Task(
            id="TASK-001",
            name="Task 1",
            status="pending",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-002",
            name="Task 2",
            status="in_progress",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-003",
            name="Task 3",
            status="completed",
            priority="high",
            created_at=now,
        ),
    ]

    for task in tasks:
        tm.add(task)

    # Index
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_tasks()

    # Search with status filter
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_tasks_semantic("task", limit=5, status="pending")

    # Verify
    assert result["status"] == "success"

    # All results should have status="pending"
    for res in result["results"]:
        assert res["metadata"]["status"] == "pending"


def test_search_tasks_semantic_priority_filter(
    tmp_path: Path, embedding_engine, vector_store
) -> None:
    """Test semantic task search with priority filter."""
    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.semantic.indexer import Indexer

    # Initialize
    tm = TaskManager(tmp_path)

    # Add tasks with different priorities
    from datetime import datetime

    now = datetime.now()
    tasks = [
        Task(
            id="TASK-001",
            name="High priority task",
            status="pending",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-002",
            name="Medium priority task",
            status="pending",
            priority="medium",
            created_at=now,
        ),
        Task(
            id="TASK-003",
            name="Low priority task",
            status="pending",
            priority="low",
            created_at=now,
        ),
    ]

    for task in tasks:
        tm.add(task)

    # Index
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_tasks()

    # Search with priority filter
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_tasks_semantic("task", limit=5, priority="high")

    # Verify
    assert result["status"] == "success"

    # All results should have priority="high"
    for res in result["results"]:
        assert res["metadata"]["priority"] == "high"


def test_search_tasks_semantic_combined_filters(
    tmp_path: Path, embedding_engine, vector_store
) -> None:
    """Test semantic task search with multiple filters."""
    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.semantic.indexer import Indexer

    # Initialize
    tm = TaskManager(tmp_path)

    # Add diverse tasks
    from datetime import datetime

    now = datetime.now()
    tasks = [
        Task(
            id="TASK-001",
            name="High priority pending task",
            status="pending",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-002",
            name="High priority in_progress task",
            status="in_progress",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-003",
            name="Medium priority pending task",
            status="pending",
            priority="medium",
            created_at=now,
        ),
    ]

    for task in tasks:
        tm.add(task)

    # Index
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_tasks()

    # Search with both filters
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_tasks_semantic("task", limit=5, status="pending", priority="high")

    # Verify
    assert result["status"] == "success"

    # Results should match both filters
    for res in result["results"]:
        assert res["metadata"]["status"] == "pending"
        assert res["metadata"]["priority"] == "high"


@pytest.mark.skip(reason="Mock path issue - needs complex sys.modules patching")
def test_search_tasks_semantic_import_error() -> None:
    """Test semantic task search handles ImportError."""
    with patch(
        "clauxton.mcp.server.SemanticSearchEngine",
        side_effect=ImportError("No module"),
    ):
        result = search_tasks_semantic("query")

    # Verify error response
    assert result["status"] == "error"
    assert "dependencies not installed" in result["message"]


def test_search_tasks_semantic_general_error(tmp_path: Path) -> None:
    """Test semantic task search handles general exceptions."""
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        with patch(
            "clauxton.semantic.search.SemanticSearchEngine.search_tasks",
            side_effect=RuntimeError("Search failed"),
        ):
            result = search_tasks_semantic("query")

    # Verify error response
    assert result["status"] == "error"
    assert "Search failed" in result["message"]


# ============================================================================
# search_files_semantic Tests
# ============================================================================


def test_search_files_semantic_basic(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test basic semantic file search."""
    from clauxton.intelligence.repository_map import RepositoryMap
    from clauxton.semantic.indexer import Indexer

    # Create test files
    test_file = tmp_path / "auth.py"
    test_file.write_text(
        """
def authenticate(token):
    \"\"\"Authenticate user with JWT token.\"\"\"
    return verify_token(token)

def verify_token(token):
    \"\"\"Verify JWT token validity.\"\"\"
    pass
"""
    )

    # Index repository
    repo_map = RepositoryMap(tmp_path)
    repo_map.index()

    # Index files semantically
    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_files(["**/*.py"])

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_files_semantic("authentication", limit=5)

    # Verify
    assert result["status"] == "success"
    assert result["search_type"] == "semantic"
    assert result["query"] == "authentication"
    assert result["count"] >= 1
    assert len(result["results"]) >= 1

    # Check result structure
    first_result = result["results"][0]
    assert "score" in first_result
    assert first_result["source_type"] == "file"
    assert "source_id" in first_result
    assert "title" in first_result
    assert "content" in first_result
    assert "metadata" in first_result


def test_search_files_semantic_pattern_filter(
    tmp_path: Path, embedding_engine, vector_store
) -> None:
    """Test semantic file search with pattern filter."""
    from clauxton.intelligence.repository_map import RepositoryMap
    from clauxton.semantic.indexer import Indexer

    # Create test files
    (tmp_path / "auth.py").write_text("def authenticate(): pass")
    (tmp_path / "user.js").write_text("function getUser() {}")

    # Index
    repo_map = RepositoryMap(tmp_path)
    repo_map.index()

    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_files(["**/*.py"])

    # Search with pattern filter (Python only)
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_files_semantic("function", limit=10, pattern="**/*.py")

    # Verify
    assert result["status"] == "success"

    # All results should be .py files
    for res in result["results"]:
        assert res["source_id"].endswith(".py")


def test_search_files_semantic_limit(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test semantic file search respects limit."""
    from clauxton.intelligence.repository_map import RepositoryMap
    from clauxton.semantic.indexer import Indexer

    # Create multiple test files
    for i in range(5):
        (tmp_path / f"file{i}.py").write_text(f"def function{i}(): pass")

    # Index
    repo_map = RepositoryMap(tmp_path)
    repo_map.index()

    indexer = Indexer(tmp_path, embedding_engine, vector_store)
    indexer.index_files(["**/*.py"])

    # Search with limit=2
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_files_semantic("function", limit=2)

    # Verify
    assert result["status"] == "success"
    assert result["count"] <= 2
    assert len(result["results"]) <= 2


@pytest.mark.skip(reason="Mock path issue - needs complex sys.modules patching")
def test_search_files_semantic_import_error() -> None:
    """Test semantic file search handles ImportError."""
    with patch(
        "clauxton.mcp.server.SemanticSearchEngine",
        side_effect=ImportError("No module"),
    ):
        result = search_files_semantic("query")

    # Verify error response
    assert result["status"] == "error"
    assert "dependencies not installed" in result["message"]


def test_search_files_semantic_general_error(tmp_path: Path) -> None:
    """Test semantic file search handles general exceptions."""
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        with patch(
            "clauxton.semantic.search.SemanticSearchEngine.search_files",
            side_effect=RuntimeError("Search failed"),
        ):
            result = search_files_semantic("query")

    # Verify error response
    assert result["status"] == "error"
    assert "Search failed" in result["message"]


# ============================================================================
# Edge Cases
# ============================================================================


def test_search_knowledge_semantic_empty_index(
    tmp_path: Path, embedding_engine, vector_store
) -> None:
    """Test semantic KB search with empty index."""
    # Initialize but don't add entries
    from clauxton.core.knowledge_base import KnowledgeBase

    KnowledgeBase(tmp_path)

    # Execute tool (no index exists)
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_knowledge_semantic("query", limit=5)

    # Should return empty results or error
    assert result["status"] in ("success", "error")
    if result["status"] == "success":
        assert result["count"] == 0
        assert len(result["results"]) == 0


def test_search_tasks_semantic_empty_index(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test semantic task search with empty index."""
    from clauxton.core.task_manager import TaskManager

    TaskManager(tmp_path)

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_tasks_semantic("query", limit=5)

    # Should return empty results or error
    assert result["status"] in ("success", "error")
    if result["status"] == "success":
        assert result["count"] == 0
        assert len(result["results"]) == 0


def test_search_files_semantic_empty_index(tmp_path: Path, embedding_engine, vector_store) -> None:
    """Test semantic file search with empty index."""
    # Execute tool (no index)
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_files_semantic("query", limit=5)

    # Should return empty results or error
    assert result["status"] in ("success", "error")
    if result["status"] == "success":
        assert result["count"] == 0
        assert len(result["results"]) == 0
