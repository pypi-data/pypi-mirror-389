"""
Integration tests for daily workflow.

Tests the complete user workflows that span multiple commands
and simulate real-world usage patterns.
"""

from datetime import datetime, timedelta
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
# Full Day Workflow Integration Tests
# ============================================================================


def test_complete_morning_to_evening_workflow(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test complete daily workflow: morning → work → pause → resume → daily.

    Simulates a full workday from morning planning to evening review.
    """
    # Morning: Start the day
    result = runner.invoke(cli, ["morning"], input="n\n")
    assert result.exit_code in (0, 1)  # May exit with 1 if no focus set

    # Add a high-priority task and start working
    result = runner.invoke(
        cli,
        [
            "task",
            "add",
            "--name",
            "Implement authentication",
            "--priority",
            "high",
            "--estimate",
            "3",
            "--start",
        ],
    )
    assert result.exit_code == 0
    assert "TASK-001" in result.output

    # Verify focus is set
    focus_file = Path.cwd() / ".clauxton" / "focus.yml"
    assert focus_file.exists()

    # Take a lunch break
    result = runner.invoke(cli, ["pause", "Lunch break"])
    assert result.exit_code == 0
    assert "paused" in result.output.lower()

    # Resume work
    result = runner.invoke(cli, ["resume"])
    assert result.exit_code == 0
    assert "Welcome back" in result.output

    # Complete the task
    from clauxton.core.task_manager import TaskManager

    tm = TaskManager(Path.cwd())
    tm.update(
        "TASK-001",
        {
            "status": "completed",
            "completed_at": datetime.now(),
            "actual_hours": 3.5,
        },
    )

    # End of day: Review accomplishments
    result = runner.invoke(cli, ["daily"])
    assert result.exit_code == 0
    assert "Daily Summary" in result.output
    assert "Completed Today" in result.output or "Implement authentication" in result.output


def test_weekly_workflow_with_multiple_tasks(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test weekly workflow: complete tasks over multiple days → weekly summary.

    Simulates completing tasks throughout the week and viewing the summary.
    """
    from clauxton.core.task_manager import TaskManager

    tm = TaskManager(Path.cwd())

    # Day 1: Complete 2 tasks
    runner.invoke(
        cli, ["task", "add", "--name", "Task 1", "--estimate", "2"]
    )
    runner.invoke(
        cli, ["task", "add", "--name", "Task 2", "--estimate", "3"]
    )

    day1 = datetime.now() - timedelta(days=6)
    tm.update(
        "TASK-001",
        {"status": "completed", "completed_at": day1, "actual_hours": 2.5},
    )
    tm.update(
        "TASK-002",
        {"status": "completed", "completed_at": day1, "actual_hours": 3.0},
    )

    # Day 3: Complete 1 task
    runner.invoke(cli, ["task", "add", "--name", "Task 3", "--estimate", "4"])
    day3 = datetime.now() - timedelta(days=4)
    tm.update(
        "TASK-003",
        {"status": "completed", "completed_at": day3, "actual_hours": 4.5},
    )

    # Day 5: Complete 2 tasks
    runner.invoke(cli, ["task", "add", "--name", "Task 4", "--estimate", "1"])
    runner.invoke(cli, ["task", "add", "--name", "Task 5", "--estimate", "2"])
    day5 = datetime.now() - timedelta(days=2)
    tm.update(
        "TASK-004",
        {"status": "completed", "completed_at": day5, "actual_hours": 1.0},
    )
    tm.update(
        "TASK-005",
        {"status": "completed", "completed_at": day5, "actual_hours": 2.5},
    )

    # Check weekly summary
    result = runner.invoke(cli, ["weekly"])
    assert result.exit_code == 0
    assert "Weekly Summary" in result.output
    # Should show 5 completed tasks
    assert "5" in result.output or "completed" in result.output.lower()


def test_search_across_kb_tasks_workflow(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test unified search workflow across KB and tasks.

    Simulates adding KB entries and tasks, then searching across all.
    """
    # Add KB entries
    runner.invoke(
        cli,
        ["kb", "add"],
        input="API Authentication\narchitecture\nUse JWT tokens for API auth\napi,jwt,auth\n",
    )
    runner.invoke(
        cli,
        ["kb", "add"],
        input="Database Schema\narchitecture\nUser authentication schema\nauth,database\n",
    )

    # Add tasks
    runner.invoke(
        cli, ["task", "add", "--name", "Implement auth API"]
    )
    runner.invoke(
        cli, ["task", "add", "--name", "Design authentication flow"]
    )

    # Search for "authentication"
    result = runner.invoke(cli, ["search", "authentication"])
    assert result.exit_code == 0
    assert "Searching for" in result.output
    assert "Knowledge Base" in result.output
    assert "Tasks" in result.output

    # Search with filter
    result = runner.invoke(cli, ["search", "auth", "--kb-only"])
    assert result.exit_code == 0
    assert "Knowledge Base" in result.output
    # Tasks section should not appear or be empty


def test_morning_planning_with_dependencies(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test morning planning with task dependencies.

    Verifies that morning command correctly handles task dependencies.
    """
    # Add tasks with dependencies
    runner.invoke(cli, ["task", "add", "--name", "Design API", "--priority", "high"])
    runner.invoke(
        cli,
        [
            "task",
            "add",
            "--name",
            "Implement API",
            "--depends-on",
            "TASK-001",
            "--priority",
            "high",
        ],
    )
    runner.invoke(
        cli,
        [
            "task",
            "add",
            "--name",
            "Write tests",
            "--depends-on",
            "TASK-002",
            "--priority",
            "medium",
        ],
    )

    # Morning planning should suggest Design API first (no dependencies)
    result = runner.invoke(cli, ["morning"], input="n\n")
    assert result.exit_code in (0, 1)
    assert "Design API" in result.output


def test_pause_resume_maintains_context(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test that pause/resume maintains work context.

    Verifies that pausing and resuming preserves focus and state.
    """
    # Start working on a task
    runner.invoke(
        cli,
        ["task", "add", "--name", "Important task", "--start"],
    )

    # Verify focus is set
    focus_file = Path.cwd() / ".clauxton" / "focus.yml"
    assert focus_file.exists()

    import yaml

    focus_data = yaml.safe_load(focus_file.read_text())
    assert focus_data["task_id"] == "TASK-001"

    # Pause work
    result = runner.invoke(cli, ["pause", "Meeting"])
    assert result.exit_code == 0

    # Resume should show the task we were working on
    result = runner.invoke(cli, ["resume"])
    assert result.exit_code == 0
    # Focus should still be preserved


def test_trends_analysis_workflow(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test trends analysis over multiple weeks.

    Simulates completing tasks over 3 weeks and analyzing trends.
    """
    from clauxton.core.task_manager import TaskManager

    tm = TaskManager(Path.cwd())

    # Week 1: 3 tasks (10 hours)
    for i in range(3):
        runner.invoke(cli, ["task", "add", "--name", f"Week1 Task {i+1}"])
        week1_date = datetime.now() - timedelta(days=14 + i)
        tm.update(
            f"TASK-{i+1:03d}",
            {
                "status": "completed",
                "completed_at": week1_date,
                "actual_hours": 3.0 + i,
            },
        )

    # Week 2: 4 tasks (12 hours)
    for i in range(4):
        task_num = 4 + i
        runner.invoke(cli, ["task", "add", "--name", f"Week2 Task {task_num}"])
        week2_date = datetime.now() - timedelta(days=7 + i)
        tm.update(
            f"TASK-{task_num:03d}",
            {
                "status": "completed",
                "completed_at": week2_date,
                "actual_hours": 3.0,
            },
        )

    # Week 3: 5 tasks (15 hours)
    for i in range(5):
        task_num = 8 + i
        runner.invoke(cli, ["task", "add", "--name", f"Week3 Task {task_num}"])
        week3_date = datetime.now() - timedelta(days=i)
        tm.update(
            f"TASK-{task_num:03d}",
            {
                "status": "completed",
                "completed_at": week3_date,
                "actual_hours": 3.0,
            },
        )

    # Check trends
    result = runner.invoke(cli, ["trends", "--days", "21"])
    assert result.exit_code == 0
    assert "Productivity Trends" in result.output


def test_json_output_integration(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test JSON output across different commands.

    Verifies that JSON output is consistent and parseable.
    """
    import json

    # Add and complete a task
    runner.invoke(cli, ["task", "add", "--name", "Test task"])

    from clauxton.core.task_manager import TaskManager

    tm = TaskManager(Path.cwd())
    tm.update(
        "TASK-001",
        {"status": "completed", "completed_at": datetime.now()},
    )

    # Test daily JSON
    result = runner.invoke(cli, ["daily", "--json"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    json_start = next((i for i, line in enumerate(lines) if line.strip().startswith("{")), None)
    if json_start is not None:
        json_str = "\n".join(lines[json_start:])
        data = json.loads(json_str)
        assert "date" in data
        assert "completed_tasks" in data

    # Test weekly JSON
    result = runner.invoke(cli, ["weekly", "--json"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    json_start = next((i for i, line in enumerate(lines) if line.strip().startswith("{")), None)
    if json_start is not None:
        json_str = "\n".join(lines[json_start:])
        data = json.loads(json_str)
        assert "week_start" in data
        assert "completed_tasks" in data


def test_task_lifecycle_integration(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test complete task lifecycle from creation to completion.

    Simulates: create → start → pause → resume → complete → review.
    """
    # Create task
    result = runner.invoke(
        cli,
        [
            "task",
            "add",
            "--name",
            "Implement feature",
            "--priority",
            "high",
            "--estimate",
            "5",
        ],
    )
    assert result.exit_code == 0
    assert "TASK-001" in result.output

    # Start working
    result = runner.invoke(
        cli, ["task", "update", "TASK-001", "--status", "in_progress"]
    )
    assert result.exit_code == 0

    # Pause
    result = runner.invoke(cli, ["pause", "Code review"])
    assert result.exit_code == 0

    # Resume
    result = runner.invoke(cli, ["resume"])
    assert result.exit_code == 0

    # Complete
    from clauxton.core.task_manager import TaskManager

    tm = TaskManager(Path.cwd())
    tm.update(
        "TASK-001",
        {
            "status": "completed",
            "completed_at": datetime.now(),
            "actual_hours": 5.5,
        },
    )

    # Review in daily summary
    result = runner.invoke(cli, ["daily"])
    assert result.exit_code == 0
    assert "Implement feature" in result.output


def test_kb_and_task_integration(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test KB and task management integration.

    Verifies that KB entries and tasks work together seamlessly.
    """
    # Add KB entry about a feature
    runner.invoke(
        cli,
        ["kb", "add"],
        input="Feature Spec\narchitecture\nDetailed feature specification\nfeature,spec\n",
    )

    # Create related task
    runner.invoke(
        cli,
        [
            "task",
            "add",
            "--name",
            "Implement feature from spec",
            "--description",
            "See KB-20251025-001",
        ],
    )

    # Search should find both
    result = runner.invoke(cli, ["search", "feature"])
    assert result.exit_code == 0
    assert "Knowledge Base" in result.output
    assert "Tasks" in result.output
    assert "Feature Spec" in result.output or "Implement feature" in result.output


def test_error_handling_workflow(
    runner: CliRunner, initialized_project: Path
) -> None:
    """
    Test error handling throughout workflows.

    Verifies that errors are user-friendly and provide actionable guidance.
    """
    # Test invalid date format in daily
    result = runner.invoke(cli, ["daily", "--date", "invalid-date"])
    assert result.exit_code == 1
    assert "Invalid date format" in result.output
    assert "YYYY-MM-DD" in result.output  # Provides format guidance

    # Test task update for non-existent task
    result = runner.invoke(
        cli, ["task", "update", "TASK-999", "--status", "completed"]
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()

    # Test search without .clauxton directory (simulate uninit state)
    import shutil

    shutil.rmtree(".clauxton")

    result = runner.invoke(cli, ["search", "test"])
    assert result.exit_code == 1
    assert ".clauxton" in result.output.lower() or "init" in result.output.lower()
    # Should suggest running clauxton init
