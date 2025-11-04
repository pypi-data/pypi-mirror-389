"""
CLI integration tests for memory commands (v0.15.0).

Tests the full CLI workflow for unified memory management:
- clauxton memory add
- clauxton memory search
- clauxton memory list
- clauxton memory get
- clauxton memory update
- clauxton memory delete
- clauxton memory related
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from clauxton.cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def initialized_project(tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create and initialize a test project."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    return project_dir


# ============================================================================
# memory add Tests
# ============================================================================


def test_memory_add_with_all_options(runner: CliRunner, initialized_project: Path) -> None:
    """Test adding memory with all options."""
    result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Design Pattern",
            "--content",
            "Use RESTful API design",
            "--category",
            "architecture",
            "--tags",
            "api,rest,design",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "✓ Memory added:" in result.output
    assert "MEM-" in result.output
    assert "knowledge" in result.output
    assert "API Design Pattern" in result.output


def test_memory_add_knowledge_type(runner: CliRunner, initialized_project: Path) -> None:
    """Test adding knowledge type memory."""
    result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Database Schema",
            "--content",
            "Use PostgreSQL for production",
            "--category",
            "database",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "✓ Memory added:" in result.output


def test_memory_add_decision_type(runner: CliRunner, initialized_project: Path) -> None:
    """Test adding decision type memory."""
    result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "decision",
            "--title",
            "Use JWT for Auth",
            "--content",
            "Decided to use JWT tokens",
            "--category",
            "security",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "✓ Memory added:" in result.output


def test_memory_add_missing_required_fields(runner: CliRunner, initialized_project: Path) -> None:
    """Test adding memory with missing required fields."""
    result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Incomplete",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Missing required fields" in result.output


def test_memory_add_without_init(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test memory add fails without initialization."""
    project_dir = tmp_path / "uninit"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Test",
            "--content",
            "Test content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert ".clauxton/ not found" in result.output


def test_memory_add_with_tags(runner: CliRunner, initialized_project: Path) -> None:
    """Test adding memory with multiple tags."""
    result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "pattern",
            "--title",
            "Factory Pattern",
            "--content",
            "Use factory pattern for object creation",
            "--category",
            "design-patterns",
            "--tags",
            "pattern,factory,oop",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "✓ Memory added:" in result.output
    assert "pattern, factory, oop" in result.output


def test_memory_add_all_memory_types(runner: CliRunner, initialized_project: Path) -> None:
    """Test adding all memory types."""
    types = ["knowledge", "decision", "code", "task", "pattern"]

    for mem_type in types:
        result = runner.invoke(
            cli,
            [
                "memory",
                "add",
                "--type",
                mem_type,
                "--title",
                f"{mem_type} entry",
                "--content",
                f"Content for {mem_type}",
                "--category",
                "test",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "✓ Memory added:" in result.output


# ============================================================================
# memory search Tests
# ============================================================================


def test_memory_search_basic(runner: CliRunner, initialized_project: Path) -> None:
    """Test basic memory search."""
    # Add a memory first
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Design",
            "--content",
            "Use RESTful API design",
            "--category",
            "architecture",
        ],
        catch_exceptions=False,
    )

    # Search for it
    result = runner.invoke(cli, ["memory", "search", "API"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "API Design" in result.output
    assert "Found 1 matches" in result.output


def test_memory_search_with_type_filter(runner: CliRunner, initialized_project: Path) -> None:
    """Test search with type filter."""
    # Add knowledge memory
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Knowledge",
            "--content",
            "REST API",
            "--category",
            "api",
        ],
        catch_exceptions=False,
    )

    # Add decision memory
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "decision",
            "--title",
            "API Decision",
            "--content",
            "Use REST API",
            "--category",
            "api",
        ],
        catch_exceptions=False,
    )

    # Search with type filter
    result = runner.invoke(
        cli, ["memory", "search", "API", "--type", "knowledge"], catch_exceptions=False
    )

    assert result.exit_code == 0
    assert "API Knowledge" in result.output
    assert "API Decision" not in result.output


def test_memory_search_no_results(runner: CliRunner, initialized_project: Path) -> None:
    """Test search with no results."""
    result = runner.invoke(cli, ["memory", "search", "nonexistent"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "No memories found" in result.output


def test_memory_search_with_limit(runner: CliRunner, initialized_project: Path) -> None:
    """Test search with limit option."""
    # Add multiple memories
    for i in range(5):
        runner.invoke(
            cli,
            [
                "memory",
                "add",
                "--type",
                "knowledge",
                "--title",
                f"API Design {i}",
                "--content",
                "REST API content",
                "--category",
                "api",
            ],
            catch_exceptions=False,
        )

    # Search with limit
    result = runner.invoke(
        cli, ["memory", "search", "API", "--limit", "3"], catch_exceptions=False
    )

    assert result.exit_code == 0
    # Should find at most 3 results
    assert result.output.count("MEM-") <= 3


# ============================================================================
# memory list Tests
# ============================================================================


def test_memory_list_empty(runner: CliRunner, initialized_project: Path) -> None:
    """Test listing memories when none exist."""
    result = runner.invoke(cli, ["memory", "list"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "No memories found" in result.output


def test_memory_list_all(runner: CliRunner, initialized_project: Path) -> None:
    """Test listing all memories."""
    # Add multiple memories
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Memory 1",
            "--content",
            "Content 1",
            "--category",
            "cat1",
        ],
        catch_exceptions=False,
    )

    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "decision",
            "--title",
            "Memory 2",
            "--content",
            "Content 2",
            "--category",
            "cat2",
        ],
        catch_exceptions=False,
    )

    result = runner.invoke(cli, ["memory", "list"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Memories (2)" in result.output
    assert "Memory 1" in result.output
    assert "Memory 2" in result.output


def test_memory_list_with_type_filter(runner: CliRunner, initialized_project: Path) -> None:
    """Test listing memories with type filter."""
    # Add different types
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Knowledge Entry",
            "--content",
            "Content",
            "--category",
            "cat",
        ],
        catch_exceptions=False,
    )

    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "decision",
            "--title",
            "Decision Entry",
            "--content",
            "Content",
            "--category",
            "cat",
        ],
        catch_exceptions=False,
    )

    result = runner.invoke(
        cli, ["memory", "list", "--type", "knowledge"], catch_exceptions=False
    )

    assert result.exit_code == 0
    assert "Knowledge Entry" in result.output
    assert "Decision Entry" not in result.output


def test_memory_list_with_category_filter(runner: CliRunner, initialized_project: Path) -> None:
    """Test listing memories with category filter."""
    # Add different categories
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Entry",
            "--content",
            "Content",
            "--category",
            "api",
        ],
        catch_exceptions=False,
    )

    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "DB Entry",
            "--content",
            "Content",
            "--category",
            "database",
        ],
        catch_exceptions=False,
    )

    result = runner.invoke(
        cli, ["memory", "list", "--category", "api"], catch_exceptions=False
    )

    assert result.exit_code == 0
    assert "API Entry" in result.output
    assert "DB Entry" not in result.output


def test_memory_list_with_tag_filter(runner: CliRunner, initialized_project: Path) -> None:
    """Test listing memories with tag filter."""
    # Add with tags
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Tagged Entry",
            "--content",
            "Content",
            "--category",
            "cat",
            "--tags",
            "api,rest",
        ],
        catch_exceptions=False,
    )

    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Untagged Entry",
            "--content",
            "Content",
            "--category",
            "cat",
        ],
        catch_exceptions=False,
    )

    result = runner.invoke(cli, ["memory", "list", "--tag", "api"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Tagged Entry" in result.output
    assert "Untagged Entry" not in result.output


# ============================================================================
# memory get Tests
# ============================================================================


def test_memory_get_existing(runner: CliRunner, initialized_project: Path) -> None:
    """Test getting an existing memory."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Test Memory",
            "--content",
            "Test content",
            "--category",
            "test",
            "--tags",
            "tag1,tag2",
        ],
        catch_exceptions=False,
    )

    # Extract memory ID
    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Get the memory
    result = runner.invoke(cli, ["memory", "get", memory_id], catch_exceptions=False)

    assert result.exit_code == 0
    assert memory_id in result.output
    assert "Test Memory" in result.output
    assert "Test content" in result.output
    assert "tag1, tag2" in result.output


def test_memory_get_nonexistent(runner: CliRunner, initialized_project: Path) -> None:
    """Test getting a non-existent memory."""
    result = runner.invoke(cli, ["memory", "get", "MEM-20260127-999"], catch_exceptions=False)

    assert result.exit_code != 0
    assert "Memory not found" in result.output


# ============================================================================
# memory update Tests
# ============================================================================


def test_memory_update_title(runner: CliRunner, initialized_project: Path) -> None:
    """Test updating memory title."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Original Title",
            "--content",
            "Content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Update title
    result = runner.invoke(
        cli,
        ["memory", "update", memory_id, "--title", "Updated Title"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "✓ Memory updated:" in result.output
    assert "Updated Title" in result.output


def test_memory_update_multiple_fields(runner: CliRunner, initialized_project: Path) -> None:
    """Test updating multiple fields."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Original",
            "--content",
            "Original content",
            "--category",
            "original",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Update multiple fields
    result = runner.invoke(
        cli,
        [
            "memory",
            "update",
            memory_id,
            "--title",
            "Updated",
            "--category",
            "updated",
            "--tags",
            "new,tags",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "✓ Memory updated:" in result.output


def test_memory_update_nonexistent(runner: CliRunner, initialized_project: Path) -> None:
    """Test updating non-existent memory."""
    result = runner.invoke(
        cli,
        ["memory", "update", "MEM-20260127-999", "--title", "New Title"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Memory not found" in result.output


def test_memory_update_no_fields(runner: CliRunner, initialized_project: Path) -> None:
    """Test update with no fields."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Test",
            "--content",
            "Content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Try to update with no fields
    result = runner.invoke(cli, ["memory", "update", memory_id], catch_exceptions=False)

    assert result.exit_code == 0
    assert "No fields to update" in result.output


# ============================================================================
# memory delete Tests
# ============================================================================


def test_memory_delete_with_yes_flag(runner: CliRunner, initialized_project: Path) -> None:
    """Test deleting memory with --yes flag."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "To Delete",
            "--content",
            "Content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Delete with --yes
    result = runner.invoke(
        cli, ["memory", "delete", memory_id, "--yes"], catch_exceptions=False
    )

    assert result.exit_code == 0
    assert "✓ Memory deleted:" in result.output


def test_memory_delete_with_confirmation(runner: CliRunner, initialized_project: Path) -> None:
    """Test deleting memory with confirmation prompt."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "To Delete",
            "--content",
            "Content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Delete with confirmation (answer 'y')
    result = runner.invoke(
        cli, ["memory", "delete", memory_id], input="y\n", catch_exceptions=False
    )

    assert result.exit_code == 0
    assert "✓ Memory deleted:" in result.output


def test_memory_delete_cancelled(runner: CliRunner, initialized_project: Path) -> None:
    """Test cancelling memory deletion."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Keep This",
            "--content",
            "Content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Try to delete but cancel (answer 'n')
    result = runner.invoke(
        cli, ["memory", "delete", memory_id], input="n\n", catch_exceptions=False
    )

    assert result.exit_code == 0
    assert "Cancelled" in result.output


def test_memory_delete_nonexistent(runner: CliRunner, initialized_project: Path) -> None:
    """Test deleting non-existent memory."""
    result = runner.invoke(
        cli, ["memory", "delete", "MEM-20260127-999", "--yes"], catch_exceptions=False
    )

    assert result.exit_code != 0
    assert "Memory not found" in result.output


# ============================================================================
# memory related Tests
# ============================================================================


def test_memory_related_basic(runner: CliRunner, initialized_project: Path) -> None:
    """Test finding related memories."""
    # Add memories with shared tags
    add_result1 = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Design",
            "--content",
            "REST API",
            "--category",
            "api",
            "--tags",
            "api,rest",
        ],
        catch_exceptions=False,
    )

    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Security",
            "--content",
            "JWT tokens",
            "--category",
            "api",
            "--tags",
            "api,security",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result1.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Find related
    result = runner.invoke(cli, ["memory", "related", memory_id], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Related to" in result.output
    assert "API Security" in result.output


def test_memory_related_no_results(runner: CliRunner, initialized_project: Path) -> None:
    """Test finding related when none exist."""
    # Add a memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Isolated",
            "--content",
            "Content",
            "--category",
            "unique",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Find related (should be none)
    result = runner.invoke(cli, ["memory", "related", memory_id], catch_exceptions=False)

    assert result.exit_code == 0
    assert "No related memories found" in result.output


def test_memory_related_nonexistent(runner: CliRunner, initialized_project: Path) -> None:
    """Test finding related for non-existent memory."""
    result = runner.invoke(
        cli, ["memory", "related", "MEM-20260127-999"], catch_exceptions=False
    )

    assert result.exit_code != 0
    assert "Memory not found" in result.output


def test_memory_related_with_limit(runner: CliRunner, initialized_project: Path) -> None:
    """Test finding related with limit."""
    # Add main memory
    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Main",
            "--content",
            "Content",
            "--category",
            "test",
            "--tags",
            "shared",
        ],
        catch_exceptions=False,
    )

    # Add multiple related memories
    for i in range(5):
        runner.invoke(
            cli,
            [
                "memory",
                "add",
                "--type",
                "knowledge",
                "--title",
                f"Related {i}",
                "--content",
                "Content",
                "--category",
                "test",
                "--tags",
                "shared",
            ],
            catch_exceptions=False,
        )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Find related with limit
    result = runner.invoke(
        cli, ["memory", "related", memory_id, "--limit", "3"], catch_exceptions=False
    )

    assert result.exit_code == 0
    # Should have at most 3 related entries
    assert result.output.count("MEM-") <= 4  # 1 for main + 3 related
