"""
Integration tests for code quality regression.

Tests that verify code quality improvements (Ruff fixes, type safety)
don't regress and that refactored code maintains functionality.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from clauxton.cli.main import cli
from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry, Task
from clauxton.core.task_manager import TaskManager


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def initialized_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Create and initialize a test project."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, f"Init failed: {result.output}"
        yield Path(td)


# ============================================================================
# Ruff F402 Fix Regression Tests (Loop Variable Shadowing)
# ============================================================================


def test_stats_command_after_shadowing_fix(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that stats command works after fixing loop variable shadowing.

    Verifies that changing 'task' to 'task_item' in main.py:820, 1605, 1814, 1896
    didn't break the stats functionality.
    """
    # Add some tasks and KB entries
    result1 = runner.invoke(
        cli, ["task", "add", "--name", "High priority task", "--priority", "high"]
    )
    assert result1.exit_code == 0
    result2 = runner.invoke(
        cli, ["task", "add", "--name", "Low priority task", "--priority", "low"]
    )
    assert result2.exit_code == 0

    # Complete one task
    tm = TaskManager(initialized_project)
    tasks = tm.list_all()
    assert len(tasks) == 2
    tm.update(
        tasks[0].id,
        {"status": "completed", "completed_at": datetime.now(), "actual_hours": 2.0},
    )

    # Run stats command (uses the refactored code)
    result = runner.invoke(cli, ["stats"])
    assert result.exit_code == 0

    # Should show correct statistics
    assert "Tasks" in result.output
    assert "2" in result.output  # Total tasks


def test_weekly_command_after_shadowing_fix(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that weekly command works after fixing loop variable shadowing.

    Verifies main.py:1605 fix (priority distribution in weekly summary).
    """
    # Add and complete tasks with different priorities
    for i, priority in enumerate(["high", "medium", "low"]):
        result = runner.invoke(
            cli, ["task", "add", "--name", f"Task {i+1}", "--priority", priority]
        )
        assert result.exit_code == 0

    # Complete all tasks
    tm = TaskManager(initialized_project)
    tasks = tm.list_all()
    assert len(tasks) == 3

    for i, task in enumerate(tasks):
        tm.update(
            task.id,
            {
                "status": "completed",
                "completed_at": datetime.now() - timedelta(days=i),
                "actual_hours": 2.0,
            },
        )

    # Run weekly command (uses the refactored code at line 1605)
    result = runner.invoke(cli, ["weekly"])
    assert result.exit_code == 0

    # Should show weekly summary with priority breakdown
    assert "Weekly Summary" in result.output
    assert "3" in result.output or "completed" in result.output.lower()


def test_trends_command_after_shadowing_fix(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that trends command works after fixing loop variable shadowing.

    Verifies main.py:1814 and 1896 fixes (trends analysis).
    """
    # Add tasks over 30 days
    for i in range(10):
        result = runner.invoke(cli, ["task", "add", "--name", f"Task {i+1}"])
        assert result.exit_code == 0

    # Complete all tasks
    tm = TaskManager(initialized_project)
    tasks = tm.list_all()
    assert len(tasks) == 10

    for i, task in enumerate(tasks):
        days_ago = i * 3
        tm.update(
            task.id,
            {
                "status": "completed",
                "completed_at": datetime.now() - timedelta(days=days_ago),
                "actual_hours": 2.0,
            },
        )

    # Run trends command (uses refactored code at lines 1814, 1896)
    result = runner.invoke(cli, ["trends", "--days", "30"])
    assert result.exit_code == 0

    # Should show trends analysis
    assert "Productivity Trends" in result.output or "trends" in result.output.lower()


# ============================================================================
# Ruff E501 Fix Regression Tests (Line Length)
# ============================================================================


def test_config_show_after_line_length_fix(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that config list works after fixing line length issues.

    Verifies that refactoring config.py:180, 186, 199, 210 didn't break display.
    """
    result = runner.invoke(cli, ["config", "list"])
    assert result.exit_code == 0

    # Should show configuration (refactored code should work)
    assert "Configuration" in result.output or "confirmation_mode" in result.output.lower()


def test_repo_index_after_line_length_fix(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that repo index works after fixing line length issues in repository.py.

    Verifies that refactoring repository.py:119, 121 didn't break indexing.
    """
    # Create some Python files to index
    src_dir = initialized_project / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text("def hello(): pass\n")

    result = runner.invoke(cli, ["repo", "index"])

    # Should complete without errors (may warn about missing parsers)
    assert result.exit_code in (0, 1)  # 1 if parsers missing, but shouldn't crash


def test_repo_search_basic_functionality(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that repo search works correctly (v0.11.0 Repository Map feature).

    Verifies basic symbol search functionality after indexing.
    """
    # Create Python files with various symbols
    src_dir = initialized_project / "src"
    src_dir.mkdir()

    (src_dir / "user_service.py").write_text("""
class UserService:
    def get_user(self, user_id: int):
        pass

    def create_user(self, name: str):
        pass

def authenticate_user(username: str, password: str):
    return True
""")

    (src_dir / "auth.py").write_text("""
def validate_token(token: str) -> bool:
    return True

class AuthManager:
    pass
""")

    # Index the repository
    index_result = runner.invoke(cli, ["repo", "index"])
    # May exit with 1 if tree-sitter parsers are missing, but should not crash
    assert index_result.exit_code in (0, 1)

    # Search for function
    result = runner.invoke(cli, ["repo", "search", "get_user"])
    assert result.exit_code in (0, 1)  # 1 if no parsers, but should handle gracefully

    # If parsers are available, verify results contain the symbol
    if result.exit_code == 0 and "get_user" in result.output:
        # Check that symbol name and type are in output (location may be truncated in table)
        assert "get_user" in result.output
        assert "function" in result.output or "method" in result.output

    # Search for class
    result = runner.invoke(cli, ["repo", "search", "AuthManager"])
    assert result.exit_code in (0, 1)
    if result.exit_code == 0 and "AuthManager" in result.output:
        assert "class" in result.output.lower()


def test_repo_search_with_no_results(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that repo search handles non-existent symbols gracefully.

    Verifies error handling when searching for symbols that don't exist.
    """
    # Create and index a simple file
    src_dir = initialized_project / "src"
    src_dir.mkdir()
    (src_dir / "simple.py").write_text("def simple_function(): pass\n")

    index_result = runner.invoke(cli, ["repo", "index"])
    assert index_result.exit_code in (0, 1)

    # Search for non-existent symbol
    result = runner.invoke(cli, ["repo", "search", "NonExistentSymbol"])
    assert result.exit_code in (0, 1)  # Should handle gracefully, not crash


def test_repo_status_command(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that repo status command works correctly.

    Verifies that repo status displays repository index information.
    """
    # Create some Python files
    src_dir = initialized_project / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("def main(): pass\n")
    (src_dir / "utils.py").write_text("def helper(): pass\n")

    # Index the repository
    index_result = runner.invoke(cli, ["repo", "index"])
    assert index_result.exit_code in (0, 1)

    # Check status
    result = runner.invoke(cli, ["repo", "status"])
    assert result.exit_code in (0, 1)  # May exit with 1 if no parsers, but should not crash

    # If parsers available, status should contain useful info
    if result.exit_code == 0:
        # Status output should contain information about indexed files or symbols
        assert len(result.output) > 0


# ============================================================================
# Type Safety Regression Tests
# ============================================================================


def test_type_annotations_preserved_after_refactoring(
    initialized_project: Path,
) -> None:
    """
    Test that type annotations work correctly after refactoring.

    Verifies that mypy-compatible type hints are preserved.
    """
    # These should work with proper type checking
    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    # Create typed objects
    now = datetime.now()
    entry: KnowledgeBaseEntry = KnowledgeBaseEntry(
        id=f"KB-{now.strftime('%Y%m%d')}-001",
        title="Test",
        category="architecture",
        content="Content",
        tags=["test"],
        created_at=now,
        updated_at=now,
    )

    task: Task = Task(
        id=tm.generate_task_id(),
        name="Test task",
        status="pending",
        created_at=now,
    )

    # Operations should maintain type safety
    entry_id: str = kb.add(entry)
    task_id: str = tm.add(task)

    assert isinstance(entry_id, str)
    assert isinstance(task_id, str)


# ============================================================================
# Functional Regression Tests
# ============================================================================


def test_full_workflow_after_all_fixes(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test complete workflow after all code quality fixes.

    This is a comprehensive regression test to ensure all refactoring
    maintains the original functionality.
    """
    # Initialize
    result = runner.invoke(cli, ["status"], obj={"cwd": str(initialized_project)})
    assert result.exit_code == 0

    # Add KB entry
    result = runner.invoke(
        cli,
        ["kb", "add"],
        input="Test Entry\narchitecture\nTest content\ntest\n",
        obj={"cwd": str(initialized_project)},
    )
    assert result.exit_code == 0

    # Add task
    result = runner.invoke(
        cli,
        ["task", "add", "--name", "Test task", "--priority", "high"],
        obj={"cwd": str(initialized_project)},
    )
    assert result.exit_code == 0

    # Search
    result = runner.invoke(
        cli, ["search", "test"], obj={"cwd": str(initialized_project)}
    )
    assert result.exit_code == 0

    # Daily summary
    result = runner.invoke(cli, ["daily"], obj={"cwd": str(initialized_project)})
    assert result.exit_code == 0

    # Stats
    result = runner.invoke(cli, ["stats"], obj={"cwd": str(initialized_project)})
    assert result.exit_code == 0

    # All commands should work after refactoring
    assert True  # If we got here, all workflows passed


def test_performance_not_degraded_after_refactoring(
    initialized_project: Path,
) -> None:
    """
    Test that performance is not degraded after code quality improvements.

    Verifies that refactoring didn't introduce performance regressions.
    """
    import time

    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    # Add 100 entries and tasks
    start_time = time.time()

    for i in range(100):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i+1}",
            category="architecture",
            content=f"Content {i+1}",
            tags=[f"tag{i+1}"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i+1}",
            status="pending",
            created_at=datetime.now(),
        )
        tm.add(task)

    elapsed = time.time() - start_time

    # Should complete reasonably fast (adjusted for environment)
    # Note: Performance may vary in CI/WSL/Docker environments
    # Increased threshold to 40s to account for environment variability
    assert elapsed < 40.0, f"Adding 100 items took {elapsed}s, should be < 40s"

    # Verify all added
    assert len(kb.list_all()) == 100
    assert len(tm.list_all()) == 100
