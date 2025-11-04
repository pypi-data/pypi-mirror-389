"""
Tests for Memory MCP Server Tools (v0.15.0).

Tests cover:
- memory_add: Add memory entries
- memory_search: Search with TF-IDF ranking
- memory_get: Get memory by ID
- memory_list: List with filters
- memory_update: Update memory fields
- memory_find_related: Find related memories
- Deprecation warnings for old tools
"""

import warnings
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clauxton.core.memory import MemoryEntry
from clauxton.mcp.server import (
    kb_add,
    kb_delete,
    kb_get,
    kb_list,
    kb_search,
    kb_update,
    memory_add,
    memory_find_related,
    memory_get,
    memory_list,
    memory_search,
    memory_update,
    task_add,
    task_delete,
    task_get,
    task_list,
    task_next,
    task_update,
)


# ============================================================================
# memory_add Tests (5 tests)
# ============================================================================


@patch("clauxton.mcp.server.Memory")
def test_memory_add_valid(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_add with valid input."""
    # Setup mock
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory._generate_memory_id.return_value = "MEM-20260127-001"
    mock_memory.add.return_value = "MEM-20260127-001"

    # Execute
    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_add(
            type="knowledge",
            title="Test Memory",
            content="Test content",
            category="architecture",
            tags=["test"],
        )

    # Verify
    assert result["id"] == "MEM-20260127-001"
    assert "Successfully added memory" in result["message"]
    mock_memory.add.assert_called_once()


@patch("clauxton.mcp.server.Memory")
def test_memory_add_all_types(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_add with all memory types."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory._generate_memory_id.return_value = "MEM-20260127-001"
    mock_memory.add.return_value = "MEM-20260127-001"

    types = ["knowledge", "decision", "code", "task", "pattern"]
    for mem_type in types:
        with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
            result = memory_add(
                type=mem_type,
                title=f"Test {mem_type}",
                content="Test content",
                category="test",
            )
        assert result["id"] == "MEM-20260127-001"


@patch("clauxton.mcp.server.Memory")
def test_memory_add_with_related_to(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_add with related_to links."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory._generate_memory_id.return_value = "MEM-20260127-002"
    mock_memory.add.return_value = "MEM-20260127-002"

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_add(
            type="knowledge",
            title="Related Memory",
            content="Test content",
            category="architecture",
            related_to=["MEM-20260127-001"],
        )

    assert result["id"] == "MEM-20260127-002"
    call_args = mock_memory.add.call_args[0][0]
    assert "MEM-20260127-001" in call_args.related_to


@patch("clauxton.mcp.server.Memory")
def test_memory_add_error_handling(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_add error handling."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.add.side_effect = Exception("Test error")

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_add(
            type="knowledge",
            title="Test",
            content="Test",
            category="test",
        )

    assert "error" in result
    assert "Failed to add memory" in result["error"]


@patch("clauxton.mcp.server.Memory")
def test_memory_add_with_tags(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_add with multiple tags."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory._generate_memory_id.return_value = "MEM-20260127-001"
    mock_memory.add.return_value = "MEM-20260127-001"

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_add(
            type="knowledge",
            title="Test",
            content="Test",
            category="architecture",
            tags=["api", "rest", "design"],
        )

    assert result["id"] == "MEM-20260127-001"
    call_args = mock_memory.add.call_args[0][0]
    assert call_args.tags == ["api", "rest", "design"]


# ============================================================================
# memory_search Tests (5 tests)
# ============================================================================


@patch("clauxton.mcp.server.Memory")
def test_memory_search_with_query(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_search with query."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory

    # Mock search results
    mock_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="API Design",
        content="REST API design pattern",
        category="architecture",
        tags=["api"],
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 10, 0, 0),
        source="manual",
    )
    mock_memory.search.return_value = [mock_entry]

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_search("api design")

    assert len(results) == 1
    assert results[0]["id"] == "MEM-20260127-001"
    assert results[0]["title"] == "API Design"


@patch("clauxton.mcp.server.Memory")
def test_memory_search_with_type_filter(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_search with type filter."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.search.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_search("test", type_filter=["knowledge", "decision"])

    assert results == []
    mock_memory.search.assert_called_once_with(
        "test", type_filter=["knowledge", "decision"], limit=10
    )


@patch("clauxton.mcp.server.Memory")
def test_memory_search_no_results(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_search with no results."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.search.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_search("nonexistent")

    assert results == []


@patch("clauxton.mcp.server.Memory")
def test_memory_search_with_limit(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_search with custom limit."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.search.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_search("test", limit=5)

    mock_memory.search.assert_called_once_with("test", type_filter=None, limit=5)


@patch("clauxton.mcp.server.Memory")
def test_memory_search_error_handling(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_search error handling."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.search.side_effect = Exception("Test error")

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_search("test")

    assert results == []


# ============================================================================
# memory_get Tests (3 tests)
# ============================================================================


@patch("clauxton.mcp.server.Memory")
def test_memory_get_existing(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_get with existing memory."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory

    mock_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Test Memory",
        content="Test content",
        category="architecture",
        tags=["test"],
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 10, 0, 0),
        source="manual",
    )
    mock_memory.get.return_value = mock_entry

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_get("MEM-20260127-001")

    assert result["id"] == "MEM-20260127-001"
    assert result["title"] == "Test Memory"
    assert result["type"] == "knowledge"


@patch("clauxton.mcp.server.Memory")
def test_memory_get_nonexistent(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_get with non-existent memory."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.get.return_value = None

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_get("MEM-99999999-999")

    assert "error" in result
    assert "Memory not found" in result["error"]


@patch("clauxton.mcp.server.Memory")
def test_memory_get_error_handling(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_get error handling."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.get.side_effect = Exception("Test error")

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_get("MEM-20260127-001")

    assert "error" in result
    assert "Failed to get memory" in result["error"]


# ============================================================================
# memory_list Tests (5 tests)
# ============================================================================


@patch("clauxton.mcp.server.Memory")
def test_memory_list_all(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_list without filters."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory

    mock_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Test",
        content="Test",
        category="test",
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 10, 0, 0),
        source="manual",
    )
    mock_memory.list_all.return_value = [mock_entry]

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_list()

    assert len(results) == 1
    assert results[0]["id"] == "MEM-20260127-001"


@patch("clauxton.mcp.server.Memory")
def test_memory_list_with_type_filter(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_list with type filter."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.list_all.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_list(type_filter=["knowledge"])

    mock_memory.list_all.assert_called_once_with(
        type_filter=["knowledge"], category_filter=None, tag_filter=None
    )


@patch("clauxton.mcp.server.Memory")
def test_memory_list_with_category_filter(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_list with category filter."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.list_all.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_list(category_filter="architecture")

    mock_memory.list_all.assert_called_once_with(
        type_filter=None, category_filter="architecture", tag_filter=None
    )


@patch("clauxton.mcp.server.Memory")
def test_memory_list_empty(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_list with empty results."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.list_all.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_list()

    assert results == []


@patch("clauxton.mcp.server.Memory")
def test_memory_list_error_handling(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_list error handling."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.list_all.side_effect = Exception("Test error")

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_list()

    assert results == []


# ============================================================================
# memory_update Tests (5 tests)
# ============================================================================


@patch("clauxton.mcp.server.Memory")
def test_memory_update_single_field(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_update with single field."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.update.return_value = True

    updated_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Updated Title",
        content="Test",
        category="test",
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 11, 0, 0),
        source="manual",
    )
    mock_memory.get.return_value = updated_entry

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_update("MEM-20260127-001", title="Updated Title")

    assert result["title"] == "Updated Title"
    assert "Successfully updated" in result["message"]


@patch("clauxton.mcp.server.Memory")
def test_memory_update_multiple_fields(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_update with multiple fields."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.update.return_value = True

    updated_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="New Title",
        content="New Content",
        category="new-category",
        tags=["new", "tags"],
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 11, 0, 0),
        source="manual",
    )
    mock_memory.get.return_value = updated_entry

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_update(
            "MEM-20260127-001",
            title="New Title",
            content="New Content",
            category="new-category",
            tags=["new", "tags"],
        )

    assert result["title"] == "New Title"
    assert result["category"] == "new-category"


@patch("clauxton.mcp.server.Memory")
def test_memory_update_nonexistent(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_update with non-existent memory."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.update.return_value = False

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_update("MEM-99999999-999", title="Test")

    assert "error" in result
    assert "Memory not found" in result["error"]


@patch("clauxton.mcp.server.Memory")
def test_memory_update_no_fields(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_update with no fields provided."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_update("MEM-20260127-001")

    assert "error" in result
    assert "No fields to update" in result["error"]


@patch("clauxton.mcp.server.Memory")
def test_memory_update_error_handling(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_update error handling."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.update.side_effect = Exception("Test error")

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        result = memory_update("MEM-20260127-001", title="Test")

    assert "error" in result
    assert "Failed to update memory" in result["error"]


# ============================================================================
# memory_find_related Tests (3 tests)
# ============================================================================


@patch("clauxton.mcp.server.Memory")
def test_memory_find_related(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_find_related."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory

    related_entry = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Related Memory",
        content="Test",
        category="architecture",
        tags=["api"],
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 10, 0, 0),
        source="manual",
    )
    mock_memory.find_related.return_value = [related_entry]

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_find_related("MEM-20260127-001")

    assert len(results) == 1
    assert results[0]["id"] == "MEM-20260127-002"


@patch("clauxton.mcp.server.Memory")
def test_memory_find_related_no_related(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_find_related with no related memories."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.find_related.return_value = []

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_find_related("MEM-20260127-001")

    assert results == []


@patch("clauxton.mcp.server.Memory")
def test_memory_find_related_error_handling(mock_memory_class: MagicMock, tmp_path: Path) -> None:
    """Test memory_find_related error handling."""
    mock_memory = MagicMock()
    mock_memory_class.return_value = mock_memory
    mock_memory.find_related.side_effect = Exception("Test error")

    with patch("clauxton.mcp.server._get_project_root", return_value=tmp_path):
        results = memory_find_related("MEM-20260127-001")

    assert results == []


# ============================================================================
# Deprecation Warning Tests (8 tests)
# ============================================================================


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_add_deprecation_warning(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_add shows deprecation warning."""
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.list_all.return_value = []
    mock_kb.add.return_value = None

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            kb_add("Test", "architecture", "Test content")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_add" in str(w[0].message)


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_search_deprecation_warning(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_search shows deprecation warning."""
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.search.return_value = []

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            kb_search("test")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_search" in str(w[0].message)


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_list_deprecation_warning(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_list shows deprecation warning."""
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.list_all.return_value = []

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            kb_list()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_list" in str(w[0].message)


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_get_deprecation_warning(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_get shows deprecation warning."""
    from clauxton.core.models import KnowledgeBaseEntry

    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    mock_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Test",
        category="architecture",
        content="Test",
        tags=[],
        created_at=datetime(2026, 1, 27, 10, 0, 0),
        updated_at=datetime(2026, 1, 27, 10, 0, 0),
        author=None,
    )
    mock_kb.get.return_value = mock_entry

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            kb_get("KB-20260127-001")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_get" in str(w[0].message)


@patch("clauxton.mcp.server.TaskManager")
def test_task_add_deprecation_warning(mock_tm_class: MagicMock, tmp_path: Path) -> None:
    """Test task_add shows deprecation warning."""
    mock_tm = MagicMock()
    mock_tm_class.return_value = mock_tm
    mock_tm.generate_task_id.return_value = "TASK-001"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            task_add("Test Task")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_add" in str(w[0].message)


@patch("clauxton.mcp.server.TaskManager")
def test_task_list_deprecation_warning(mock_tm_class: MagicMock, tmp_path: Path) -> None:
    """Test task_list shows deprecation warning."""
    mock_tm = MagicMock()
    mock_tm_class.return_value = mock_tm
    mock_tm.list_all.return_value = []

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            task_list()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_list" in str(w[0].message)


@patch("clauxton.mcp.server.TaskManager")
def test_task_get_deprecation_warning(mock_tm_class: MagicMock, tmp_path: Path) -> None:
    """Test task_get shows deprecation warning."""
    from clauxton.core.models import Task

    mock_tm = MagicMock()
    mock_tm_class.return_value = mock_tm

    mock_task = Task(
        id="TASK-001",
        name="Test",
        description=None,
        status="pending",
        priority="medium",
        created_at=datetime(2026, 1, 27, 10, 0, 0),
    )
    mock_tm.get.return_value = mock_task

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            task_get("TASK-001")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_get" in str(w[0].message)


@patch("clauxton.mcp.server.TaskManager")
def test_task_update_deprecation_warning(mock_tm_class: MagicMock, tmp_path: Path) -> None:
    """Test task_update shows deprecation warning."""
    mock_tm = MagicMock()
    mock_tm_class.return_value = mock_tm

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
            task_update("TASK-001", status="completed")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "memory_update" in str(w[0].message)
