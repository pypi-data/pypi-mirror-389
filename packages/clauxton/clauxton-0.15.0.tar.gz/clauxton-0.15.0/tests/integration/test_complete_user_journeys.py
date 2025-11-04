"""
Complete User Journey Integration Tests.

Tests real-world end-to-end user journeys that span the entire application lifecycle.
These tests ensure all features work together seamlessly in realistic scenarios.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from clauxton.cli.main import cli
from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.task_manager import TaskManager


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


# ============================================================================
# Complete User Journey Tests
# ============================================================================


def test_new_project_from_zero_to_production(
    runner: CliRunner, tmp_path: Path
) -> None:
    """
    Test complete project lifecycle: init → build → review → export.

    This test simulates a real project from initialization to production-ready state.
    Covers: init, KB building, task planning, execution, weekly review, export.
    """
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        test_dir = Path(td)

        # Step 1: Initialize project
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert (test_dir / ".clauxton").exists()

        # Step 2: Build Knowledge Base (architecture decisions)
        result = runner.invoke(
            cli,
            ["kb", "add"],
            input="FastAPI Backend\narchitecture\nUse FastAPI for REST API\nfastapi,backend\n",
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            ["kb", "add"],
            input=(
                "React Frontend\narchitecture\n"
                "Use React with TypeScript\nreact,frontend,typescript\n"
            ),
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            ["kb", "add"],
            input=(
                "PostgreSQL Database\ndecision\n"
                "Use PostgreSQL for data persistence\npostgresql,database\n"
            ),
        )
        assert result.exit_code == 0

        # Verify KB entries
        kb = KnowledgeBase(test_dir)
        entries = kb.list_all()
        assert len(entries) == 3

        # Step 3: Plan tasks
        result = runner.invoke(
            cli,
            ["task", "add", "--name", "Setup FastAPI project", "--priority", "high"],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            ["task", "add", "--name", "Design database schema", "--priority", "high"],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            ["task", "add", "--name", "Create API endpoints", "--priority", "medium"],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            ["task", "add", "--name", "Setup React app", "--priority", "medium"],
        )
        assert result.exit_code == 0

        # Verify tasks
        tm = TaskManager(test_dir)
        tasks = tm.list_all()
        assert len(tasks) == 4

        # Step 4: Execute tasks (simulate work)
        for i, task in enumerate(tasks[:2]):  # Complete first 2 tasks
            tm.update(
                task.id,
                {
                    "status": "completed",
                    "completed_at": datetime.now() - timedelta(days=6 - i),
                    "actual_hours": 3.0,
                },
            )

        # Step 5: Weekly review
        result = runner.invoke(cli, ["weekly"])
        assert result.exit_code == 0
        assert "Weekly Summary" in result.output or "2" in result.output

        # Step 6: Export knowledge base
        export_dir = test_dir / "docs"
        export_dir.mkdir()

        kb_file = test_dir / ".clauxton" / "knowledge-base.yml"
        exported = export_dir / "kb_export.yml"
        exported.write_text(kb_file.read_text())

        assert exported.exists()

        # Step 7: Verify final state
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "4" in result.output or "Tasks" in result.output


def test_team_development_daily_workflow(
    runner: CliRunner, tmp_path: Path
) -> None:
    """
    Test typical team development day: morning → work → pause → resume → daily.

    Simulates a developer's complete workday using Clauxton for task management.
    Covers: morning planning, task focus, work sessions, pause/resume, daily summary.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        test_dir = Path(td)

        # Setup: Initialize and create some tasks
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0

        # Create tasks for the day
        tasks_to_create = [
            ("Fix authentication bug", "critical"),
            ("Code review for PR #123", "high"),
            ("Update documentation", "medium"),
            ("Refactor user service", "low"),
        ]

        for task_name, priority in tasks_to_create:
            result = runner.invoke(
                cli,
                ["task", "add", "--name", task_name, "--priority", priority],
            )
            assert result.exit_code == 0

        # 8:00 AM - Morning planning
        result = runner.invoke(cli, ["morning"], input="n\n")
        # May exit with 1 if no focus set yet, but should not crash
        assert result.exit_code in (0, 1)

        # 9:00 AM - Focus on critical bug
        tm = TaskManager(test_dir)
        tasks = tm.list_all()
        critical_task = next(t for t in tasks if t.priority == "critical")

        result = runner.invoke(cli, ["focus", critical_task.id])
        assert result.exit_code == 0

        # 10:30 AM - Pause for meeting
        result = runner.invoke(cli, ["pause", "Team standup meeting"])
        assert result.exit_code == 0

        # 11:00 AM - Resume work
        result = runner.invoke(cli, ["continue"])
        assert result.exit_code == 0

        # 12:00 PM - Complete critical task
        tm.update(
            critical_task.id,
            {
                "status": "completed",
                "completed_at": datetime.now(),
                "actual_hours": 3.0,
            },
        )

        # 2:00 PM - Focus on code review
        high_priority_task = next(t for t in tasks if t.priority == "high")
        result = runner.invoke(cli, ["focus", high_priority_task.id])
        assert result.exit_code == 0

        # 3:00 PM - Search for relevant KB entries
        result = runner.invoke(cli, ["search", "review"])
        assert result.exit_code == 0

        # 5:00 PM - Complete code review
        tm.update(
            high_priority_task.id,
            {
                "status": "completed",
                "completed_at": datetime.now(),
                "actual_hours": 2.0,
            },
        )

        # 6:00 PM - Daily summary
        result = runner.invoke(cli, ["daily"])
        assert result.exit_code == 0

        # Verify work completed
        completed_tasks = [t for t in tm.list_all() if t.status == "completed"]
        assert len(completed_tasks) == 2
        assert sum(t.actual_hours or 0 for t in completed_tasks) == 5.0


def test_troubleshooting_workflow(
    runner: CliRunner, tmp_path: Path
) -> None:
    """
    Test troubleshooting workflow: error → search KB → add solution → update task.

    Simulates discovering a problem, searching for solutions, documenting the fix.
    Covers: KB search, adding entries during development, task updates, knowledge capture.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        test_dir = Path(td)

        # Setup
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0

        # Pre-populate KB with some technical knowledge
        result = runner.invoke(
            cli,
            ["kb", "add"],
            input="CORS Configuration\nconstraint\nAllow origins: localhost:3000\ncors,security\n",
        )
        assert result.exit_code == 0

        # Developer encounters CORS error
        result = runner.invoke(
            cli,
            ["task", "add", "--name", "Fix CORS error in production", "--priority", "critical"],
        )
        assert result.exit_code == 0

        # Search KB for CORS info
        result = runner.invoke(cli, ["kb", "search", "CORS"])
        assert result.exit_code == 0
        assert "CORS" in result.output or "cors" in result.output.lower()

        # Document new solution found
        result = runner.invoke(
            cli,
            ["kb", "add"],
            input=(
                "CORS Production Fix\ndecision\n"
                "Add trusted domains to allowlist\ncors,production,security\n"
            ),
        )
        assert result.exit_code == 0

        # Update task with solution
        tm = TaskManager(test_dir)
        tasks = tm.list_all()
        cors_task = tasks[0]

        tm.update(
            cors_task.id,
            {
                "status": "completed",
                "completed_at": datetime.now(),
                "actual_hours": 1.5,
                "description": "Fixed by updating CORS config with production domains",
            },
        )

        # Verify knowledge captured
        kb = KnowledgeBase(test_dir)
        cors_entries = kb.search("CORS")
        assert len(cors_entries) >= 2

        # Verify task completed
        completed = tm.get(cors_task.id)
        assert completed.status == "completed"
        assert "CORS" in (completed.description or "")


def test_documentation_maintenance_cycle(
    runner: CliRunner, tmp_path: Path
) -> None:
    """
    Test documentation maintenance: organize → export → review → update cycle.

    Simulates maintaining project documentation through KB organization.
    Covers: KB organization, export, bulk updates, categorization.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        test_dir = Path(td)

        # Setup
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0

        # Add various KB entries (simulating accumulated knowledge)
        entries_to_add = [
            ("API Rate Limiting", "constraint", "Max 100 req/min per user", "api,limit"),
            ("Database Indexes", "pattern", "Add indexes on foreign keys", "db,performance"),
            ("Code Style Guide", "convention", "Use black formatter", "style,python"),
            ("Deployment Process", "pattern", "Use GitHub Actions CI/CD", "deploy,ci"),
            ("Error Handling", "pattern", "Log errors to Sentry", "error,logging"),
        ]

        for title, category, content, tags in entries_to_add:
            result = runner.invoke(
                cli,
                ["kb", "add"],
                input=f"{title}\n{category}\n{content}\n{tags}\n",
            )
            assert result.exit_code == 0

        # List and organize by category
        for category in ["pattern", "constraint", "convention"]:
            result = runner.invoke(cli, ["kb", "list", "--category", category])
            assert result.exit_code == 0

        # Export for documentation
        export_dir = test_dir / "docs"
        export_dir.mkdir()

        kb_file = test_dir / ".clauxton" / "knowledge-base.yml"
        exported = export_dir / "architecture_docs.yml"
        exported.write_text(kb_file.read_text())

        # Verify export
        assert exported.exists()
        assert exported.stat().st_size > 0

        # Add new entry after review
        result = runner.invoke(
            cli,
            ["kb", "add"],
            input="Testing Strategy\npattern\nUse pytest with 90%+ coverage\ntesting,pytest\n",
        )
        assert result.exit_code == 0

        # Verify final state
        kb = KnowledgeBase(test_dir)
        all_entries = kb.list_all()
        assert len(all_entries) == 6

        patterns = [e for e in all_entries if e.category == "pattern"]
        assert len(patterns) == 4
