"""
Tests for semantic indexer.

This module tests the Indexer class for KB/Tasks/Files indexing.
"""

from datetime import datetime, timedelta

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry, Task
from clauxton.core.task_manager import TaskManager
from clauxton.semantic.embeddings import EmbeddingEngine
from clauxton.semantic.indexer import Indexer
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
def indexer(tmp_path, embedding_engine, vector_store):
    """Create Indexer instance with temp project root."""
    return Indexer(tmp_path, embedding_engine, vector_store)


@pytest.fixture
def kb_with_entries(tmp_path):
    """Create KnowledgeBase with test entries."""
    kb = KnowledgeBase(tmp_path)

    # Add test entries
    now = datetime.now()
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
            title="Database Choice",
            category="decision",
            content="PostgreSQL for production database.",
            tags=["database", "postgres"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20251026-003",
            title="Coding Style",
            category="convention",
            content="Use Google-style docstrings for all Python code.",
            tags=["python", "style"],
            created_at=now,
            updated_at=now,
        ),
    ]

    for entry in entries:
        kb.add(entry)

    return kb


@pytest.fixture
def task_manager_with_tasks(tmp_path):
    """Create TaskManager with test tasks."""
    tm = TaskManager(tmp_path)

    # Add test tasks
    now = datetime.now()
    tasks = [
        Task(
            id="TASK-001",
            name="Setup FastAPI project",
            description="Initialize FastAPI project with basic structure",
            status="completed",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-002",
            name="Design database schema",
            description="Create PostgreSQL schema for the application",
            status="in_progress",
            priority="high",
            created_at=now,
        ),
        Task(
            id="TASK-003",
            name="Write unit tests",
            description="Add comprehensive unit tests",
            status="pending",
            priority="medium",
            created_at=now,
        ),
    ]

    for task in tasks:
        tm.add(task)

    return tm


@pytest.fixture
def project_with_files(tmp_path):
    """Create project with test Python files."""
    # Create directory structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create test files
    (src_dir / "main.py").write_text(
        "# Main application\n"
        "def main():\n"
        "    print('Hello, World!')\n"
    )

    (src_dir / "utils.py").write_text(
        "# Utility functions\n"
        "def helper():\n"
        "    return 'helper'\n"
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_main.py").write_text(
        "# Test main\n"
        "def test_main():\n"
        "    assert True\n"
    )

    return tmp_path


# ============================================================================
# Test Indexer Initialization
# ============================================================================


class TestIndexerInitialization:
    """Test Indexer initialization."""

    def test_init_creates_kb_and_task_manager(self, tmp_path, embedding_engine, vector_store):
        """Test that initialization creates KB and TaskManager instances."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        assert isinstance(indexer.kb, KnowledgeBase)
        assert isinstance(indexer.task_manager, TaskManager)

    def test_init_with_string_path(self, tmp_path, embedding_engine, vector_store):
        """Test initialization with string path."""
        indexer = Indexer(str(tmp_path), embedding_engine, vector_store)

        assert indexer.project_root == tmp_path

    def test_init_stores_dependencies(self, tmp_path, embedding_engine, vector_store):
        """Test that initialization stores engine and store."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        assert indexer.embedding_engine is embedding_engine
        assert indexer.vector_store is vector_store


# ============================================================================
# Test Knowledge Base Indexing
# ============================================================================


class TestIndexKnowledgeBase:
    """Test Knowledge Base indexing."""

    def test_index_kb_empty(self, indexer):
        """Test indexing with no KB entries."""
        count = indexer.index_knowledge_base()

        assert count == 0
        assert indexer.vector_store.size() == 0

    def test_index_kb_single_entry(self, tmp_path, embedding_engine, vector_store, kb_with_entries):
        """Test indexing a single KB entry."""
        # Create indexer with existing KB
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        count = indexer.index_knowledge_base()

        assert count == 3  # All 3 entries indexed
        assert indexer.vector_store.size() == 3

        # Check metadata
        metadata = indexer.vector_store.metadata
        assert len(metadata) == 3
        assert all(m["source_type"] == "kb" for m in metadata)

    def test_index_kb_incremental_no_changes(
        self, tmp_path, embedding_engine, vector_store, kb_with_entries
    ):
        """Test incremental indexing with no changes."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        count1 = indexer.index_knowledge_base()
        assert count1 == 3

        # Index second time (no changes)
        count2 = indexer.index_knowledge_base()
        assert count2 == 0  # No reindexing

    def test_index_kb_incremental_with_update(self, tmp_path, embedding_engine, vector_store):
        """Test incremental indexing with updated entry."""
        kb = KnowledgeBase(tmp_path)
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Add first entry
        now = datetime.now()
        entry1 = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test Entry",
            category="architecture",
            content="Original content",
            tags=["test"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry1)

        # Index
        count1 = indexer.index_knowledge_base()
        assert count1 == 1

        # Update entry
        later = now + timedelta(seconds=10)
        kb.update(
            "KB-20251026-001",
            {
                "title": "Test Entry Updated",
                "content": "Updated content",
                "tags": ["test", "updated"],
                "updated_at": later,
            },
        )

        # Reindex (should detect change)
        count2 = indexer.index_knowledge_base()
        assert count2 == 1  # Reindexed due to timestamp change

    def test_index_kb_force_reindex(
        self, tmp_path, embedding_engine, vector_store, kb_with_entries
    ):
        """Test force reindex."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        count1 = indexer.index_knowledge_base()
        assert count1 == 3

        # Force reindex
        count2 = indexer.index_knowledge_base(force=True)
        assert count2 == 3  # All reindexed


# ============================================================================
# Test Task Indexing
# ============================================================================


class TestIndexTasks:
    """Test task indexing."""

    def test_index_tasks_empty(self, indexer):
        """Test indexing with no tasks."""
        count = indexer.index_tasks()

        assert count == 0

    def test_index_tasks_single(
        self, tmp_path, embedding_engine, vector_store, task_manager_with_tasks
    ):
        """Test indexing tasks."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        count = indexer.index_tasks()

        assert count == 3  # All 3 tasks indexed
        assert indexer.vector_store.size() == 3

        # Check metadata
        metadata = indexer.vector_store.metadata
        assert all(m["source_type"] == "task" for m in metadata)
        source_ids = {"TASK-001", "TASK-002", "TASK-003"}
        assert set(m["source_id"] for m in metadata) == source_ids

    def test_index_tasks_incremental_no_changes(
        self, tmp_path, embedding_engine, vector_store, task_manager_with_tasks
    ):
        """Test incremental indexing with no changes."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        count1 = indexer.index_tasks()
        assert count1 == 3

        # Index second time (no changes)
        count2 = indexer.index_tasks()
        assert count2 == 0

    def test_index_tasks_incremental_with_new_task(self, tmp_path, embedding_engine, vector_store):
        """Test incremental indexing with new task."""
        tm = TaskManager(tmp_path)
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Add first task
        now = datetime.now()
        task1 = Task(
            id="TASK-001",
            name="First task",
            description="First task description",
            status="pending",
            created_at=now,
        )
        tm.add(task1)

        # Index
        count1 = indexer.index_tasks()
        assert count1 == 1

        # Add second task
        task2 = Task(
            id="TASK-002",
            name="Second task",
            description="Second task description",
            status="pending",
            created_at=now,
        )
        tm.add(task2)

        # Reindex (should detect new task)
        count2 = indexer.index_tasks()
        assert count2 == 1  # Only new task indexed

        assert indexer.vector_store.size() == 2

    def test_index_tasks_force(
        self, tmp_path, embedding_engine, vector_store, task_manager_with_tasks
    ):
        """Test force reindex of tasks."""
        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        count1 = indexer.index_tasks()
        assert count1 == 3

        # Force reindex
        count2 = indexer.index_tasks(force=True)
        assert count2 == 3


# ============================================================================
# Test File Indexing
# ============================================================================


class TestIndexFiles:
    """Test file indexing."""

    def test_index_files_single_pattern(
        self, tmp_path, embedding_engine, vector_store, project_with_files
    ):
        """Test indexing files with single pattern."""
        indexer = Indexer(project_with_files, embedding_engine, vector_store)

        count = indexer.index_files(["**/*.py"])

        assert count == 3  # main.py, utils.py, test_main.py
        assert indexer.vector_store.size() == 3

        # Check metadata
        metadata = indexer.vector_store.metadata
        assert all(m["source_type"] == "file" for m in metadata)
        assert all(m["extension"] == ".py" for m in metadata)

    def test_index_files_multiple_patterns(self, tmp_path, embedding_engine, vector_store):
        """Test indexing with multiple patterns."""
        # Create files with different extensions
        (tmp_path / "file.py").write_text("# Python file")
        (tmp_path / "file.js").write_text("// JavaScript file")
        (tmp_path / "file.ts").write_text("// TypeScript file")

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        count = indexer.index_files(["**/*.py", "**/*.js", "**/*.ts"])

        assert count == 3

    def test_index_files_skip_clauxton_dir(self, tmp_path, embedding_engine, vector_store):
        """Test that .clauxton directory is skipped."""
        # Create files in .clauxton
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()
        (clauxton_dir / "test.py").write_text("# Should be skipped")

        # Create file outside .clauxton
        (tmp_path / "included.py").write_text("# Should be indexed")

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        count = indexer.index_files(["**/*.py"])

        assert count == 1  # Only included.py
        metadata = indexer.vector_store.metadata
        assert metadata[0]["source_id"] == "included.py"

    def test_index_files_skip_empty_files(self, tmp_path, embedding_engine, vector_store):
        """Test that empty files are skipped."""
        (tmp_path / "empty.py").write_text("")
        (tmp_path / "non_empty.py").write_text("# Not empty")

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        count = indexer.index_files(["**/*.py"])

        assert count == 1  # Only non_empty.py

    def test_index_files_incremental(self, tmp_path, embedding_engine, vector_store):
        """Test incremental file indexing."""
        # Create initial file
        file_path = tmp_path / "test.py"
        file_path.write_text("# Original content")

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        count1 = indexer.index_files(["**/*.py"])
        assert count1 == 1

        # Index second time (no changes)
        count2 = indexer.index_files(["**/*.py"])
        assert count2 == 0

        # Modify file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        file_path.write_text("# Modified content")

        # Reindex (should detect change)
        count3 = indexer.index_files(["**/*.py"])
        assert count3 == 1


# ============================================================================
# Test Index All
# ============================================================================


class TestIndexAll:
    """Test index_all method."""

    def test_index_all_default(self, tmp_path, embedding_engine, vector_store):
        """Test indexing all sources with defaults."""
        # Create KB entry
        kb = KnowledgeBase(tmp_path)
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test",
            category="architecture",
            content="Test content",
            tags=[],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        # Create task
        tm = TaskManager(tmp_path)
        task = Task(
            id="TASK-001",
            name="Test task",
            status="pending",
            created_at=now,
        )
        tm.add(task)

        # Create file
        (tmp_path / "test.py").write_text("# Test file")

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index all
        counts = indexer.index_all()

        assert counts["kb"] == 1
        assert counts["tasks"] == 1
        assert counts["files"] == 1
        assert indexer.vector_store.size() == 3

    def test_index_all_custom_patterns(self, tmp_path, embedding_engine, vector_store):
        """Test index_all with custom file patterns."""
        (tmp_path / "file.py").write_text("# Python")
        (tmp_path / "file.js").write_text("// JavaScript")

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        counts = indexer.index_all(file_patterns=["**/*.py", "**/*.js"])

        assert counts["files"] == 2

    def test_index_all_force(self, tmp_path, embedding_engine, vector_store):
        """Test index_all with force=True."""
        kb = KnowledgeBase(tmp_path)
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test",
            category="architecture",
            content="Test",
            tags=[],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        indexer = Indexer(tmp_path, embedding_engine, vector_store)

        # Index first time
        counts1 = indexer.index_all()
        assert counts1["kb"] == 1

        # Force reindex
        counts2 = indexer.index_all(force=True)
        assert counts2["kb"] == 1


# ============================================================================
# Test Clear Index
# ============================================================================


class TestClearIndex:
    """Test clear_index method."""

    def test_clear_index_specific_type(self, tmp_path, embedding_engine, vector_store):
        """Test clearing specific source type."""
        # Add KB entry
        kb = KnowledgeBase(tmp_path)
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test",
            category="architecture",
            content="Test",
            tags=[],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        # Add task
        tm = TaskManager(tmp_path)
        task = Task(
            id="TASK-001",
            name="Test",
            status="pending",
            created_at=now,
        )
        tm.add(task)

        indexer = Indexer(tmp_path, embedding_engine, vector_store)
        indexer.index_all()

        assert indexer.vector_store.size() == 2

        # Clear only KB entries
        removed = indexer.clear_index("kb")

        assert removed == 1
        # Note: size() may not be accurate after selective removal
        # Check metadata instead
        metadata = indexer.vector_store.metadata
        task_metadata = [m for m in metadata if m.get("source_type") == "task"]
        assert len(task_metadata) == 1

    def test_clear_index_all(self, tmp_path, embedding_engine, vector_store):
        """Test clearing all indices."""
        kb = KnowledgeBase(tmp_path)
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test",
            category="architecture",
            content="Test",
            tags=[],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        indexer = Indexer(tmp_path, embedding_engine, vector_store)
        indexer.index_all()

        assert indexer.vector_store.size() == 1

        # Clear all
        removed = indexer.clear_index()

        assert removed == 1
        assert indexer.vector_store.size() == 0


# ============================================================================
# Test Helper Methods
# ============================================================================


class TestHelperMethods:
    """Test helper methods."""

    def test_get_existing_metadata(self, tmp_path, embedding_engine, vector_store):
        """Test _get_existing_metadata."""
        kb = KnowledgeBase(tmp_path)
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test",
            category="architecture",
            content="Test",
            tags=[],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        indexer = Indexer(tmp_path, embedding_engine, vector_store)
        indexer.index_knowledge_base()

        # Get existing metadata
        existing = indexer._get_existing_metadata("kb")

        assert "KB-20251026-001" in existing
        assert existing["KB-20251026-001"]["source_type"] == "kb"

    def test_needs_reindex_newer_timestamp(self, indexer):
        """Test _needs_reindex with newer timestamp."""
        old_time = datetime(2025, 10, 25)
        new_time = datetime(2025, 10, 26)

        existing_meta = {"updated_at": old_time.isoformat()}

        assert indexer._needs_reindex(existing_meta, new_time) is True

    def test_needs_reindex_same_timestamp(self, indexer):
        """Test _needs_reindex with same timestamp."""
        same_time = datetime(2025, 10, 26)

        existing_meta = {"updated_at": same_time.isoformat()}

        assert indexer._needs_reindex(existing_meta, same_time) is False

    def test_hash_content(self, indexer):
        """Test _hash_content."""
        text = "Test content"
        hash1 = indexer._hash_content(text)
        hash2 = indexer._hash_content(text)

        # Same text should produce same hash
        assert hash1 == hash2

        # Different text should produce different hash
        hash3 = indexer._hash_content("Different content")
        assert hash1 != hash3

    def test_extract_kb_text(self, indexer):
        """Test _extract_kb_text."""
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id="KB-20251026-001",
            title="Test Title",
            category="architecture",
            content="Test content",
            tags=["tag1", "tag2"],
            created_at=now,
            updated_at=now,
        )

        text = indexer._extract_kb_text(entry)

        assert "Test Title" in text
        assert "Test content" in text
        assert "tag1" in text
        assert "tag2" in text

    def test_extract_task_text(self, indexer):
        """Test _extract_task_text."""
        now = datetime.now()
        task = Task(
            id="TASK-001",
            name="Test Task",
            description="Test description",
            status="pending",
            created_at=now,
        )

        text = indexer._extract_task_text(task)

        assert "Test Task" in text
        assert "Test description" in text

    def test_extract_task_text_no_description(self, indexer):
        """Test _extract_task_text with no description."""
        now = datetime.now()
        task = Task(
            id="TASK-001",
            name="Test Task",
            status="pending",
            created_at=now,
        )

        text = indexer._extract_task_text(task)

        assert "Test Task" in text
        assert text.strip() == "Test Task"
