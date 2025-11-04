"""
Tests for MCP Server.

Tests cover:
- Server instantiation
- Tool registration
- Tool execution (KB: search, add, list, get, update, delete)
- Tool execution (Tasks: add, list, get, update, next, delete)
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clauxton.mcp.server import (
    check_file_conflicts,
    detect_conflicts,
    index_repository,
    kb_add,
    kb_delete,
    kb_get,
    kb_list,
    kb_search,
    kb_update,
    mcp,
    recommend_safe_order,
    search_symbols,
    task_add,
    task_delete,
    task_get,
    task_list,
    task_next,
    task_update,
)

# ============================================================================
# Server Instantiation Tests
# ============================================================================


def test_mcp_server_created() -> None:
    """Test that MCP server instance is created."""
    assert mcp is not None
    assert mcp.name == "Clauxton"


def test_mcp_server_has_tools() -> None:
    """Test that MCP server has tools registered."""
    # FastMCP should have registered our tools
    # We can verify by checking that our functions are decorated
    # Knowledge Base tools
    assert callable(kb_search)
    assert callable(kb_add)
    assert callable(kb_list)
    assert callable(kb_get)
    assert callable(kb_update)
    assert callable(kb_delete)
    # Task Management tools
    assert callable(task_add)
    assert callable(task_list)
    assert callable(task_get)
    assert callable(task_update)
    assert callable(task_next)
    assert callable(task_delete)


# ============================================================================
# Tool Execution Tests (with mocked KB)
# ============================================================================


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_search_tool(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_search tool execution."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    # Mock search results
    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    mock_entry = KnowledgeBaseEntry(
        id="KB-20251019-001",
        title="Test Entry",
        category="architecture",
        content="Test content",
        tags=["test"],
        created_at=datetime(2025, 10, 19, 10, 0, 0),
        updated_at=datetime(2025, 10, 19, 10, 0, 0),
        author=None,
    )
    mock_kb.search.return_value = [mock_entry]

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        results = kb_search("test query")

    # Verify
    assert len(results) == 1
    assert results[0]["id"] == "KB-20251019-001"
    assert results[0]["title"] == "Test Entry"
    assert results[0]["category"] == "architecture"
    mock_kb.search.assert_called_once_with("test query", category=None, limit=10)


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_add_tool(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_add tool execution."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.list_all.return_value = []  # No existing entries
    mock_kb.add.return_value = "KB-20251019-001"

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_add(
            title="Test Entry",
            category="architecture",
            content="Test content",
            tags=["test"],
        )

    # Verify
    assert result["id"].startswith("KB-")
    assert "Successfully added" in result["message"]
    mock_kb.add.assert_called_once()


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_list_tool(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_list tool execution."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    mock_entries = [
        KnowledgeBaseEntry(
            id=f"KB-20251019-{i:03d}",
            title=f"Entry {i}",
            category="architecture",
            content=f"Content {i}",
            tags=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=None,
        )
        for i in range(1, 4)
    ]
    mock_kb.list_all.return_value = mock_entries

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        results = kb_list()

    # Verify
    assert len(results) == 3
    assert all("id" in r for r in results)
    assert all("title" in r for r in results)


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_list_with_category_filter(
    mock_kb_class: MagicMock, tmp_path: Path
) -> None:
    """Test kb_list tool with category filter."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    mock_entries = [
        KnowledgeBaseEntry(
            id="KB-20251019-001",
            title="Arch Entry",
            category="architecture",
            content="Content",
            tags=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=None,
        ),
        KnowledgeBaseEntry(
            id="KB-20251019-002",
            title="Dec Entry",
            category="decision",
            content="Content",
            tags=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=None,
        ),
    ]
    mock_kb.list_all.return_value = mock_entries

    # Execute tool with filter
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        results = kb_list(category="architecture")

    # Verify - should only return architecture entries
    assert len(results) == 1
    assert results[0]["category"] == "architecture"


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_get_tool(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_get tool execution."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    mock_entry = KnowledgeBaseEntry(
        id="KB-20251019-001",
        title="Test Entry",
        category="architecture",
        content="Test content",
        tags=["test"],
        created_at=datetime(2025, 10, 19, 10, 0, 0),
        updated_at=datetime(2025, 10, 19, 10, 0, 0),
        author=None,
        version=1,
    )
    mock_kb.get.return_value = mock_entry

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_get("KB-20251019-001")

    # Verify
    assert result["id"] == "KB-20251019-001"
    assert result["title"] == "Test Entry"
    assert result["version"] == 1
    mock_kb.get.assert_called_once_with("KB-20251019-001")


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_update_tool(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_update tool execution."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    # Mock updated entry (version 2)
    updated_entry = KnowledgeBaseEntry(
        id="KB-20251019-001",
        title="Updated Title",
        category="architecture",
        content="Updated content",
        tags=["updated"],
        created_at=datetime(2025, 10, 19, 10, 0, 0),
        updated_at=datetime(2025, 10, 19, 11, 0, 0),
        author=None,
        version=2,
    )
    mock_kb.update.return_value = updated_entry

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_update(
            entry_id="KB-20251019-001",
            title="Updated Title",
            content="Updated content",
        )

    # Verify
    assert result["id"] == "KB-20251019-001"
    assert result["title"] == "Updated Title"
    assert result["content"] == "Updated content"
    assert result["version"] == 2
    assert "Successfully updated" in result["message"]
    mock_kb.update.assert_called_once()
    # Check that update was called with correct dict
    call_args = mock_kb.update.call_args
    assert call_args[0][0] == "KB-20251019-001"
    assert "title" in call_args[0][1]
    assert "content" in call_args[0][1]


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_update_no_fields(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_update with no fields returns error."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    # Execute tool with no update fields
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_update(entry_id="KB-20251019-001")

    # Verify error response
    assert "error" in result
    assert "No fields to update" in result["error"]
    # Update should not have been called
    mock_kb.update.assert_not_called()


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_update_all_fields(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_update with all fields."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    updated_entry = KnowledgeBaseEntry(
        id="KB-20251019-001",
        title="New Title",
        category="decision",
        content="New content",
        tags=["new", "tags"],
        created_at=datetime(2025, 10, 19, 10, 0, 0),
        updated_at=datetime(2025, 10, 19, 11, 0, 0),
        author=None,
        version=2,
    )
    mock_kb.update.return_value = updated_entry

    # Execute tool with all fields
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_update(
            entry_id="KB-20251019-001",
            title="New Title",
            content="New content",
            category="decision",
            tags=["new", "tags"],
        )

    # Verify
    assert result["title"] == "New Title"
    assert result["category"] == "decision"
    assert result["content"] == "New content"
    assert result["tags"] == ["new", "tags"]
    assert result["version"] == 2


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_delete_tool(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_delete tool execution."""
    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb

    from datetime import datetime

    from clauxton.core.models import KnowledgeBaseEntry

    # Mock entry to be deleted
    entry_to_delete = KnowledgeBaseEntry(
        id="KB-20251019-001",
        title="Entry to Delete",
        category="architecture",
        content="Content",
        tags=[],
        created_at=datetime(2025, 10, 19, 10, 0, 0),
        updated_at=datetime(2025, 10, 19, 10, 0, 0),
        author=None,
    )
    mock_kb.get.return_value = entry_to_delete
    mock_kb.delete.return_value = None

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_delete(entry_id="KB-20251019-001")

    # Verify
    assert result["id"] == "KB-20251019-001"
    assert "Successfully deleted" in result["message"]
    assert "Entry to Delete" in result["message"]
    mock_kb.get.assert_called_once_with("KB-20251019-001")
    mock_kb.delete.assert_called_once_with("KB-20251019-001")


# ============================================================================
# Conflict Detection MCP Tool Tests
# ============================================================================


def test_detect_conflicts_tool_callable() -> None:
    """Test that detect_conflicts tool is callable."""
    assert callable(detect_conflicts)


def test_recommend_safe_order_tool_callable() -> None:
    """Test that recommend_safe_order tool is callable."""
    assert callable(recommend_safe_order)


def test_check_file_conflicts_tool_callable() -> None:
    """Test that check_file_conflicts tool is callable."""
    assert callable(check_file_conflicts)


def test_detect_conflicts_tool_input_validation(tmp_path: Path) -> None:
    """Test detect_conflicts tool with invalid task raises exception."""
    with patch("clauxton.mcp.server.TaskManager") as mock_tm:
        with patch("clauxton.mcp.server.ConflictDetector") as mock_cd:
            # Mock TaskManager to raise exception for invalid task
            mock_tm_instance = MagicMock()
            mock_tm.return_value = mock_tm_instance
            mock_tm_instance.get.side_effect = Exception("Task not found: TASK-999")

            mock_cd_instance = MagicMock()
            mock_cd.return_value = mock_cd_instance

            # Execute tool with invalid task_id - should raise exception
            with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
                with pytest.raises(Exception) as exc_info:
                    detect_conflicts(task_id="TASK-999")

                assert "Task not found" in str(exc_info.value)


def test_detect_conflicts_tool_output_format(tmp_path: Path) -> None:
    """Test detect_conflicts tool output matches expected schema."""
    from datetime import datetime

    from clauxton.core.models import ConflictReport

    with patch("clauxton.mcp.server.TaskManager") as mock_tm:
        with patch("clauxton.mcp.server.ConflictDetector") as mock_cd:
            # Mock TaskManager
            mock_tm_instance = MagicMock()
            mock_tm.return_value = mock_tm_instance
            mock_task = MagicMock()
            mock_task.id = "TASK-001"
            mock_task.name = "Test task"
            mock_tm_instance.get.return_value = mock_task

            # Mock ConflictDetector to return sample conflict
            mock_cd_instance = MagicMock()
            mock_cd.return_value = mock_cd_instance
            sample_conflict = ConflictReport(
                task_a_id="TASK-001",
                task_b_id="TASK-002",
                conflict_type="file_overlap",
                risk_level="medium",
                risk_score=0.5,
                overlapping_files=["file.py"],
                details="Test conflict",
                recommendation="Complete TASK-002 first",
                detected_at=datetime.now(),
            )
            mock_cd_instance.detect_conflicts.return_value = [sample_conflict]

            # Execute tool
            with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
                result = detect_conflicts(task_id="TASK-001")

            # Verify output structure
            assert "task_id" in result
            assert "conflicts" in result
            assert result["task_id"] == "TASK-001"
            assert len(result["conflicts"]) > 0
            # Verify conflict structure
            conflict = result["conflicts"][0]
            assert "task_b_id" in conflict
            assert "risk_level" in conflict
            assert "risk_score" in conflict
            assert "overlapping_files" in conflict


def test_recommend_safe_order_tool_handles_empty_list(tmp_path: Path) -> None:
    """Test recommend_safe_order tool with empty task list."""
    with patch("clauxton.mcp.server.TaskManager") as mock_tm:
        with patch("clauxton.mcp.server.ConflictDetector") as mock_cd:
            # Mock valid empty scenario
            mock_tm_instance = MagicMock()
            mock_tm.return_value = mock_tm_instance

            mock_cd_instance = MagicMock()
            mock_cd.return_value = mock_cd_instance
            mock_cd_instance.recommend_safe_order.return_value = []

            # Execute tool with empty list
            with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
                result = recommend_safe_order(task_ids=[])

            # Verify it handles empty list gracefully
            assert "task_count" in result
            assert result["task_count"] == 0


def test_recommend_safe_order_tool_output_format(tmp_path: Path) -> None:
    """Test recommend_safe_order tool output format."""
    with patch("clauxton.mcp.server.TaskManager") as mock_tm:
        with patch("clauxton.mcp.server.ConflictDetector") as mock_cd:
            # Mock TaskManager
            mock_tm_instance = MagicMock()
            mock_tm.return_value = mock_tm_instance

            # Mock ConflictDetector
            mock_cd_instance = MagicMock()
            mock_cd.return_value = mock_cd_instance
            mock_cd_instance.recommend_safe_order.return_value = [
                "TASK-001",
                "TASK-002",
                "TASK-003",
            ]

            # Execute tool
            with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
                result = recommend_safe_order(
                    task_ids=["TASK-001", "TASK-002", "TASK-003"]
                )

            # Verify output structure
            assert "task_ids" in result or "recommended_order" in result
            # Should contain ordered list
            if "recommended_order" in result:
                assert isinstance(result["recommended_order"], list)
                assert len(result["recommended_order"]) == 3


def test_check_file_conflicts_tool_output_format(tmp_path: Path) -> None:
    """Test check_file_conflicts tool output format."""
    with patch("clauxton.mcp.server.TaskManager") as mock_tm:
        with patch("clauxton.mcp.server.ConflictDetector") as mock_cd:
            # Mock TaskManager
            mock_tm_instance = MagicMock()
            mock_tm.return_value = mock_tm_instance

            # Mock ConflictDetector
            mock_cd_instance = MagicMock()
            mock_cd.return_value = mock_cd_instance
            mock_cd_instance.check_file_conflicts.return_value = ["TASK-001"]

            # Execute tool
            with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
                result = check_file_conflicts(files=["file.py"])

            # Verify output structure
            assert "files" in result or "conflicting_tasks" in result
            # Should contain list of conflicting tasks
            if "conflicting_tasks" in result:
                assert isinstance(result["conflicting_tasks"], list)


# ============================================================================
# task_import_yaml Tool Tests (v0.10.0)
# ============================================================================


def test_task_import_yaml_tool_callable(tmp_path: Path) -> None:
    """Test task_import_yaml tool is callable."""
    from clauxton.mcp.server import task_import_yaml

    assert callable(task_import_yaml)


def test_task_import_yaml_tool_basic(tmp_path: Path) -> None:
    """Test basic YAML import via MCP tool."""
    (tmp_path / ".clauxton").mkdir()

    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        from clauxton.mcp.server import task_import_yaml

        yaml_content = """
tasks:
  - name: "Task A"
    priority: high
  - name: "Task B"
    priority: medium
"""

        result = task_import_yaml(yaml_content=yaml_content)

        assert result["status"] == "success"
        assert result["imported"] == 2
        assert len(result["task_ids"]) == 2


def test_task_import_yaml_tool_dry_run(tmp_path: Path) -> None:
    """Test dry-run mode via MCP tool."""
    (tmp_path / ".clauxton").mkdir()

    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        from clauxton.mcp.server import task_import_yaml

        yaml_content = """
tasks:
  - name: "Task A"
"""

        result = task_import_yaml(yaml_content=yaml_content, dry_run=True)

        assert result["status"] == "success"
        assert result["imported"] == 0  # Nothing imported in dry-run
        assert len(result["task_ids"]) == 1  # But IDs are shown


def test_task_import_yaml_tool_validation_errors(tmp_path: Path) -> None:
    """Test validation errors via MCP tool."""
    (tmp_path / ".clauxton").mkdir()

    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        from clauxton.mcp.server import task_import_yaml

        yaml_content = """
tasks:
  - name: ""
"""

        result = task_import_yaml(yaml_content=yaml_content)

        assert result["status"] == "error"
        assert result["imported"] == 0
        assert len(result["errors"]) > 0


def test_task_import_yaml_tool_circular_dependency(tmp_path: Path) -> None:
    """Test circular dependency detection via MCP tool."""
    (tmp_path / ".clauxton").mkdir()

    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        from clauxton.mcp.server import task_import_yaml

        yaml_content = """
tasks:
  - id: TASK-001
    name: "Task A"
    depends_on:
      - TASK-002
  - id: TASK-002
    name: "Task B"
    depends_on:
      - TASK-001
"""

        result = task_import_yaml(yaml_content=yaml_content)

        assert result["status"] == "error"
        assert result["imported"] == 0
        assert "Circular dependency" in result["errors"][0]


def test_task_import_yaml_tool_skip_validation(tmp_path: Path) -> None:
    """Test skip_validation parameter via MCP tool."""
    (tmp_path / ".clauxton").mkdir()

    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        from clauxton.mcp.server import task_import_yaml

        yaml_content = """
tasks:
  - name: "Task A"
    depends_on:
      - TASK-999
"""

        # Without skip_validation, should fail
        result1 = task_import_yaml(yaml_content=yaml_content, skip_validation=False)
        assert result1["status"] == "error"

        # With skip_validation, should succeed
        result2 = task_import_yaml(yaml_content=yaml_content, skip_validation=True)
        assert result2["status"] == "success"
        assert result2["imported"] == 1


# ============================================================================
# KB Export Tool Tests
# ============================================================================


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_export_docs_success(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_export_docs tool with successful export."""
    from clauxton.mcp.server import kb_export_docs

    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.export_to_markdown.return_value = {
        "total_entries": 10,
        "files_created": 3,
        "categories": ["architecture", "decision", "constraint"],
    }

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_export_docs(output_dir="./docs/kb")

    # Verify
    assert result["status"] == "success"
    assert result["total_entries"] == 10
    assert result["files_created"] == 3
    assert result["categories"] == ["architecture", "decision", "constraint"]
    assert result["output_dir"] == "./docs/kb"
    assert len(result["files"]) == 3
    assert "Exported 10 entries" in result["message"]


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_export_docs_specific_category(
    mock_kb_class: MagicMock, tmp_path: Path
) -> None:
    """Test kb_export_docs tool with category filter."""
    from clauxton.mcp.server import kb_export_docs

    # Setup mock
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.export_to_markdown.return_value = {
        "total_entries": 3,
        "files_created": 1,
        "categories": ["decision"],
    }

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_export_docs(output_dir="./docs/adr", category="decision")

    # Verify
    assert result["status"] == "success"
    assert result["total_entries"] == 3
    assert result["files_created"] == 1
    assert result["categories"] == ["decision"]
    assert "Exported 3 decision entries" in result["message"]


@patch("clauxton.mcp.server.KnowledgeBase")
def test_kb_export_docs_error_handling(mock_kb_class: MagicMock, tmp_path: Path) -> None:
    """Test kb_export_docs tool error handling."""
    from clauxton.mcp.server import kb_export_docs

    # Setup mock to raise exception
    mock_kb = MagicMock()
    mock_kb_class.return_value = mock_kb
    mock_kb.export_to_markdown.side_effect = Exception("Export failed")

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = kb_export_docs(output_dir="./invalid/path")

    # Verify error response
    assert result["status"] == "error"
    assert "Export failed" in result["error"]
    assert "Failed to export KB" in result["message"]


# ============================================================================
# Repository Map Tests
# ============================================================================


@patch("clauxton.mcp.server.RepositoryMap")
def test_index_repository_default_path(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test index_repository tool with default path."""
    from datetime import datetime

    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_result = MagicMock()
    mock_result.files_indexed = 50
    mock_result.symbols_found = 200
    mock_result.by_type = {"source": 30, "test": 15, "config": 5}
    mock_result.by_language = {"python": 45, "yaml": 5}
    mock_result.indexed_at = datetime(2025, 10, 23, 10, 30, 0)
    mock_repo_map.index.return_value = mock_result

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = index_repository()

    # Verify
    assert result["status"] == "success"
    assert result["files_indexed"] == 50
    assert result["symbols_found"] == 200
    assert result["duration"] >= 0
    assert result["by_type"] == {"source": 30, "test": 15, "config": 5}
    assert result["by_language"] == {"python": 45, "yaml": 5}
    assert result["indexed_at"] == "2025-10-23T10:30:00"
    mock_repo_map_class.assert_called_once_with(tmp_path)
    mock_repo_map.index.assert_called_once()


@patch("clauxton.mcp.server.RepositoryMap")
def test_index_repository_custom_path(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test index_repository tool with custom path."""
    from datetime import datetime

    # Create custom directory
    custom_dir = tmp_path / "custom-repo"
    custom_dir.mkdir()

    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_result = MagicMock()
    mock_result.files_indexed = 100
    mock_result.symbols_found = 500
    mock_result.by_type = {"source": 80, "test": 20}
    mock_result.by_language = {"python": 100}
    mock_result.indexed_at = datetime(2025, 10, 23, 11, 0, 0)
    mock_repo_map.index.return_value = mock_result

    # Execute tool
    result = index_repository(root_path=str(custom_dir))

    # Verify
    assert result["status"] == "success"
    assert result["files_indexed"] == 100
    assert result["symbols_found"] == 500
    mock_repo_map_class.assert_called_once_with(custom_dir)


def test_index_repository_nonexistent_path() -> None:
    """Test index_repository tool with nonexistent path."""
    result = index_repository(root_path="/nonexistent/directory")

    # Verify error response
    assert result["status"] == "error"
    assert "Directory not found" in result["message"]


@patch("clauxton.mcp.server.RepositoryMap")
def test_index_repository_error_handling(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test index_repository tool error handling."""
    # Setup mock to raise exception
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map
    mock_repo_map.index.side_effect = Exception("Indexing failed")

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = index_repository()

    # Verify error response
    assert result["status"] == "error"
    assert "Indexing failed" in result["message"]


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_exact_mode(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols tool with exact mode."""
    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_symbol1 = MagicMock()
    mock_symbol1.name = "authenticate_user"
    mock_symbol1.type = "function"
    mock_symbol1.file_path = "/path/to/auth.py"
    mock_symbol1.line_start = 10
    mock_symbol1.line_end = 20
    mock_symbol1.docstring = "Authenticate user with credentials."
    mock_symbol1.signature = "def authenticate_user(username: str, password: str) -> bool"

    mock_symbol2 = MagicMock()
    mock_symbol2.name = "get_auth_token"
    mock_symbol2.type = "function"
    mock_symbol2.file_path = "/path/to/auth.py"
    mock_symbol2.line_start = 30
    mock_symbol2.line_end = 35
    mock_symbol2.docstring = "Get authentication token."
    mock_symbol2.signature = "def get_auth_token(user_id: int) -> str"

    mock_repo_map.search.return_value = [mock_symbol1, mock_symbol2]

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="auth", mode="exact", limit=10)

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 2
    assert len(result["symbols"]) == 2
    assert result["symbols"][0]["name"] == "authenticate_user"
    assert result["symbols"][0]["type"] == "function"
    assert result["symbols"][0]["docstring"] == "Authenticate user with credentials."
    assert result["symbols"][1]["name"] == "get_auth_token"
    mock_repo_map.search.assert_called_once_with("auth", search_type="exact", limit=10)


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_fuzzy_mode(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols tool with fuzzy mode."""
    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_symbol = MagicMock()
    mock_symbol.name = "authenticate_user"
    mock_symbol.type = "function"
    mock_symbol.file_path = "/path/to/auth.py"
    mock_symbol.line_start = 10
    mock_symbol.line_end = 20
    mock_symbol.docstring = "Authenticate user."
    mock_symbol.signature = "def authenticate_user(username: str) -> bool"

    mock_repo_map.search.return_value = [mock_symbol]

    # Execute tool (with typo)
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="authentcate", mode="fuzzy", limit=5)

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["symbols"][0]["name"] == "authenticate_user"
    mock_repo_map.search.assert_called_once_with("authentcate", search_type="fuzzy", limit=5)


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_semantic_mode(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols tool with semantic mode."""
    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_symbol1 = MagicMock()
    mock_symbol1.name = "authenticate_user"
    mock_symbol1.type = "function"
    mock_symbol1.file_path = "/path/to/auth.py"
    mock_symbol1.line_start = 10
    mock_symbol1.line_end = 20
    mock_symbol1.docstring = "Authenticate user with username and password."
    mock_symbol1.signature = "def authenticate_user(username: str, password: str) -> bool"

    mock_symbol2 = MagicMock()
    mock_symbol2.name = "verify_credentials"
    mock_symbol2.type = "function"
    mock_symbol2.file_path = "/path/to/auth.py"
    mock_symbol2.line_start = 30
    mock_symbol2.line_end = 40
    mock_symbol2.docstring = "Verify user login credentials."
    mock_symbol2.signature = "def verify_credentials(username: str, password: str) -> bool"

    mock_repo_map.search.return_value = [mock_symbol1, mock_symbol2]

    # Execute tool (semantic search)
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="user login", mode="semantic", limit=10)

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 2
    assert result["symbols"][0]["name"] == "authenticate_user"
    assert result["symbols"][1]["name"] == "verify_credentials"
    mock_repo_map.search.assert_called_once_with("user login", search_type="semantic", limit=10)


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_custom_path(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols tool with custom path."""
    # Create custom directory
    custom_dir = tmp_path / "custom-repo"
    custom_dir.mkdir()

    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map
    mock_repo_map.search.return_value = []

    # Execute tool
    result = search_symbols(query="test", mode="exact", root_path=str(custom_dir))

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 0
    mock_repo_map_class.assert_called_once_with(custom_dir)


def test_search_symbols_nonexistent_path() -> None:
    """Test search_symbols tool with nonexistent path."""
    result = search_symbols(query="test", root_path="/nonexistent/directory")

    # Verify error response
    assert result["status"] == "error"
    assert "Directory not found" in result["message"]


def test_search_symbols_invalid_mode(tmp_path: Path) -> None:
    """Test search_symbols tool with invalid search mode."""
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="test", mode="invalid_mode")

    # Verify error response
    assert result["status"] == "error"
    assert "Invalid search mode" in result["message"]
    assert "invalid_mode" in result["message"]


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_error_handling(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols tool error handling."""
    # Setup mock to raise exception
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map
    mock_repo_map.search.side_effect = Exception("Search failed")

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="test", mode="exact")

    # Verify error response
    assert result["status"] == "error"
    assert "Search failed" in result["message"]


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_empty_results(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols tool with no results."""
    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map
    mock_repo_map.search.return_value = []

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="nonexistent_function", mode="exact")

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["symbols"] == []


@patch("clauxton.mcp.server.RepositoryMap")
def test_index_repository_empty_directory(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test index_repository with empty directory."""
    from datetime import datetime

    # Setup mock for empty directory
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_result = MagicMock()
    mock_result.files_indexed = 0
    mock_result.symbols_found = 0
    mock_result.by_type = {}
    mock_result.by_language = {}
    mock_result.indexed_at = datetime(2025, 10, 23, 12, 0, 0)
    mock_repo_map.index.return_value = mock_result

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = index_repository()

    # Verify empty result
    assert result["status"] == "success"
    assert result["files_indexed"] == 0
    assert result["symbols_found"] == 0
    assert result["by_type"] == {}
    assert result["by_language"] == {}


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_no_index_exists(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols when no index exists yet."""
    # Setup mock - no symbols data
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map
    mock_repo_map.search.return_value = []

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="test", mode="exact")

    # Verify - should return empty results, not error
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["symbols"] == []


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_limit_validation(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols respects limit parameter."""
    # Setup mock with many symbols
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    # Create 20 mock symbols
    mock_symbols = []
    for i in range(20):
        mock_symbol = MagicMock()
        mock_symbol.name = f"test_function_{i}"
        mock_symbol.type = "function"
        mock_symbol.file_path = f"/path/to/file_{i}.py"
        mock_symbol.line_start = 10
        mock_symbol.line_end = 20
        mock_symbol.docstring = f"Test function {i}"
        mock_symbol.signature = f"def test_function_{i}()"
        mock_symbols.append(mock_symbol)

    # Mock should return only first 5 (respecting limit)
    mock_repo_map.search.return_value = mock_symbols[:5]

    # Execute tool with limit=5
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="test", mode="exact", limit=5)

    # Verify limit is respected
    assert result["status"] == "success"
    assert result["count"] == 5
    assert len(result["symbols"]) == 5
    mock_repo_map.search.assert_called_once_with("test", search_type="exact", limit=5)


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_special_characters(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols with special characters in query."""
    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_symbol = MagicMock()
    mock_symbol.name = "__init__"
    mock_symbol.type = "function"
    mock_symbol.file_path = "/path/to/module.py"
    mock_symbol.line_start = 1
    mock_symbol.line_end = 5
    mock_symbol.docstring = "Initialize module"
    mock_symbol.signature = "def __init__(self)"

    mock_repo_map.search.return_value = [mock_symbol]

    # Execute tool with special characters
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="__init__", mode="exact")

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["symbols"][0]["name"] == "__init__"


@patch("clauxton.mcp.server.RepositoryMap")
def test_search_symbols_unicode_names(mock_repo_map_class: MagicMock, tmp_path: Path) -> None:
    """Test search_symbols with Unicode characters in symbol names."""
    # Setup mock
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_symbol = MagicMock()
    mock_symbol.name = "処理_データ"  # Japanese characters
    mock_symbol.type = "function"
    mock_symbol.file_path = "/path/to/module.py"
    mock_symbol.line_start = 10
    mock_symbol.line_end = 20
    mock_symbol.docstring = "Process data"
    mock_symbol.signature = "def 処理_データ(data)"

    mock_repo_map.search.return_value = [mock_symbol]

    # Execute tool with Unicode query
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = search_symbols(query="処理", mode="exact")

    # Verify
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["symbols"][0]["name"] == "処理_データ"


@patch("clauxton.mcp.server.RepositoryMap")
def test_index_repository_statistics_accuracy(
    mock_repo_map_class: MagicMock, tmp_path: Path
) -> None:
    """Test index_repository returns accurate statistics."""
    from datetime import datetime

    # Setup mock with detailed statistics
    mock_repo_map = MagicMock()
    mock_repo_map_class.return_value = mock_repo_map

    mock_result = MagicMock()
    mock_result.files_indexed = 100
    mock_result.symbols_found = 500
    mock_result.by_type = {
        "source": 80,
        "test": 15,
        "config": 3,
        "docs": 2
    }
    mock_result.by_language = {
        "python": 85,
        "javascript": 10,
        "yaml": 3,
        "markdown": 2
    }
    mock_result.indexed_at = datetime(2025, 10, 23, 14, 30, 0)
    mock_repo_map.index.return_value = mock_result

    # Execute tool
    with patch("clauxton.mcp.server.Path.cwd", return_value=tmp_path):
        result = index_repository()

    # Verify statistics accuracy
    assert result["status"] == "success"
    assert result["files_indexed"] == 100
    assert result["symbols_found"] == 500

    # Verify by_type totals match files_indexed
    assert sum(result["by_type"].values()) == 100
    assert result["by_type"]["source"] == 80
    assert result["by_type"]["test"] == 15

    # Verify by_language totals match files_indexed
    assert sum(result["by_language"].values()) == 100
    assert result["by_language"]["python"] == 85

    # Verify timestamp
    assert result["indexed_at"] == "2025-10-23T14:30:00"
