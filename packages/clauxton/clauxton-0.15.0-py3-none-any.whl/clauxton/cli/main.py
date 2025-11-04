"""
Clauxton CLI - Command Line Interface for Knowledge Base and Task Management.

This module provides CLI commands for:
- Knowledge Base management (kb add, kb get, kb list, kb search, kb update, kb delete)
- Project initialization (init)
- Future: Task management (Phase 1)
- Future: Conflict detection (Phase 2)

Example:
    >>> clauxton init
    >>> clauxton kb add
    >>> clauxton kb search "architecture"
"""

from pathlib import Path
from typing import Any, Optional

import click

from clauxton.__version__ import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="clauxton")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Clauxton - Persistent context for Claude Code.

    Provides Knowledge Base, Task Management, Conflict Detection,
    and Repository Map to solve AI-assisted development pain points.

    ✅ Phase 0: Knowledge Base (Complete)
    ✅ Phase 1: Task Management (Complete)
    ✅ Phase 2: Conflict Detection (Complete)
    ✅ Phase 3: Enhanced UX (Complete - v0.10.0)
    ✅ Phase 4: Repository Map (Complete - v0.11.0)
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Show welcome message when invoked without subcommand
    if ctx.invoked_subcommand is None:
        from pathlib import Path

        clauxton_dir = Path.cwd() / ".clauxton"

        click.echo(click.style(f"\nClauxton v{__version__}", fg="cyan", bold=True))
        click.echo(click.style("Context that persists for Claude Code\n", fg="white"))

        if not clauxton_dir.exists():
            # First-time user
            click.echo(click.style("👋 Getting Started:\n", fg="green", bold=True))
            click.echo(click.style("  ⚡ Quick Start (Recommended):\n", fg="yellow", bold=True))
            click.echo("     All-in-one setup (init + index + MCP):")
            click.echo(click.style("     clauxton quickstart\n", fg="cyan"))
            click.echo(click.style("  📋 Manual Setup:\n", fg="white", bold=True))
            click.echo("     1. Initialize: " + click.style("clauxton init", fg="cyan"))
            click.echo("     2. Index codebase: " + click.style("clauxton repo index", fg="cyan"))
            click.echo("     3. Setup MCP: " + click.style("clauxton mcp setup", fg="cyan"))
            click.echo("     4. Add knowledge: " + click.style("clauxton kb add", fg="cyan"))
            click.echo("     5. Create tasks: " + click.style("clauxton task add\n", fg="cyan"))
        else:
            # Existing user
            click.echo(click.style("📋 Quick Commands:\n", fg="green", bold=True))
            click.echo("  Project Status:")
            click.echo(
                click.style("     clauxton status            ", fg="cyan")
                + "# Overall status\n"
            )
            click.echo("  Repository Map:")
            click.echo(
                click.style("     clauxton repo index        ", fg="cyan")
                + "# Index code"
            )
            click.echo(
                click.style("     clauxton repo search QUERY ", fg="cyan")
                + "# Search\n"
            )
            click.echo("  Knowledge Base:")
            click.echo(
                click.style("     clauxton kb search QUERY   ", fg="cyan") + "# Search"
            )
            click.echo(
                click.style("     clauxton kb list           ", fg="cyan") + "# List\n"
            )
            click.echo("  Task Management:")
            click.echo(
                click.style("     clauxton task next         ", fg="cyan") + "# Next"
            )
            click.echo(
                click.style("     clauxton task list         ", fg="cyan") + "# List\n"
            )
            click.echo("  MCP Integration:")
            click.echo(
                click.style("     clauxton mcp setup         ", fg="cyan") + "# Setup"
            )
            click.echo(
                click.style("     clauxton mcp status        ", fg="cyan") + "# Status\n"
            )

        click.echo(click.style("📚 Full documentation:", fg="white"))
        click.echo(click.style("   clauxton --help\n", fg="cyan"))


@cli.command()
def status() -> None:
    """
    Show overall project status.

    Displays summary of:
    - Repository Map (indexed files, symbols)
    - Tasks (pending, in progress, completed)
    - Knowledge Base (entry count, recent entries)
    - MCP Server (configuration status)

    Example:
        $ clauxton status
    """
    from pathlib import Path

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    click.echo(click.style("\nClauxton Project Status\n", fg="cyan", bold=True))
    click.echo(f"Location: {root_dir}\n")

    # Repository Map Status
    try:
        from clauxton.intelligence.repository_map import RepositoryMap
        repo_map = RepositoryMap(root_dir)

        index_file = repo_map.map_dir / "index.json"
        if index_file.exists():
            index = repo_map.index_data
            stats = index["statistics"]
            indexed_at = index.get("indexed_at", "unknown")

            # Calculate time ago
            from datetime import datetime
            if indexed_at != "unknown":
                try:
                    indexed_time = datetime.fromisoformat(indexed_at)
                    now = datetime.now()
                    delta = now - indexed_time

                    if delta.total_seconds() < 3600:
                        time_ago = f"{int(delta.total_seconds() / 60)} minutes ago"
                    elif delta.total_seconds() < 86400:
                        time_ago = f"{int(delta.total_seconds() / 3600)} hours ago"
                    else:
                        time_ago = f"{int(delta.total_seconds() / 86400)} days ago"
                except Exception:
                    time_ago = "recently"
            else:
                time_ago = "unknown"

            total_symbols = sum(len(syms) for syms in repo_map.symbols_data.values())

            click.echo(click.style("🗺️  Repository Map:", fg="green", bold=True))
            click.echo(f"  ✓ Indexed: {stats['total_files']} files, {total_symbols} symbols")
            click.echo(f"  Last updated: {time_ago}")
        else:
            click.echo(click.style("🗺️  Repository Map:", fg="yellow", bold=True))
            click.echo("  ⚠ Not indexed yet. Run: clauxton repo index")
    except Exception:
        click.echo(click.style("🗺️  Repository Map:", fg="yellow", bold=True))
        click.echo("  ⚠ Not indexed yet. Run: clauxton repo index")

    click.echo()

    # Task Status
    try:
        from clauxton.core.task_manager import TaskManager
        tm = TaskManager(root_dir)

        all_tasks = tm.list_all()
        pending = [t for t in all_tasks if t.status == "pending"]
        in_progress = [t for t in all_tasks if t.status == "in_progress"]
        completed = [t for t in all_tasks if t.status == "completed"]
        blocked = [t for t in all_tasks if t.status == "blocked"]

        click.echo(click.style("📋 Tasks:", fg="green", bold=True))
        if pending:
            click.echo(f"  📌 Pending: {len(pending)} tasks")
        if in_progress:
            click.echo(f"  🔄 In Progress: {len(in_progress)} tasks")
        if completed:
            click.echo(f"  ✅ Completed: {len(completed)} tasks")
        if blocked:
            click.echo(f"  ⛔ Blocked: {len(blocked)} tasks")

        if not all_tasks:
            click.echo("  No tasks yet. Create one: clauxton task add")
        else:
            # Get next task
            next_task = tm.get_next_task()
            if next_task:
                click.echo(f"  Next: {click.style(next_task.id, fg='cyan')} - {next_task.name}")
    except Exception:
        click.echo(click.style("📋 Tasks:", fg="yellow", bold=True))
        click.echo("  No tasks found")

    click.echo()

    # Knowledge Base Status
    try:
        from clauxton.core.knowledge_base import KnowledgeBase
        kb = KnowledgeBase(root_dir)

        all_entries = kb.list_all()

        click.echo(click.style("📚 Knowledge Base:", fg="green", bold=True))
        click.echo(f"  {len(all_entries)} entries")

        if all_entries:
            # Show most recent entry
            latest = max(all_entries, key=lambda e: e.created_at)

            from datetime import datetime
            delta = datetime.now() - latest.created_at
            if delta.total_seconds() < 3600:
                time_ago = f"{int(delta.total_seconds() / 60)} minutes ago"
            elif delta.total_seconds() < 86400:
                time_ago = f"{int(delta.total_seconds() / 3600)} hours ago"
            else:
                time_ago = f"{int(delta.total_seconds() / 86400)} days ago"

            click.echo(f"  Recent: {latest.title} ({time_ago})")
    except Exception:
        click.echo(click.style("📚 Knowledge Base:", fg="yellow", bold=True))
        click.echo("  No entries found")

    click.echo()

    # MCP Server Status
    try:
        import json
        mcp_file = root_dir / ".claude-plugin" / "mcp-servers.json"

        if mcp_file.exists():
            with open(mcp_file, "r") as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})

            if servers:
                click.echo(click.style("🔌 MCP Server:", fg="green", bold=True))
                for name in servers.keys():
                    click.echo(f"  ✓ Configured ({name})")
            else:
                click.echo(click.style("🔌 MCP Server:", fg="yellow", bold=True))
                click.echo("  ⚠ No servers configured. Run: clauxton mcp setup")
        else:
            click.echo(click.style("🔌 MCP Server:", fg="yellow", bold=True))
            click.echo("  ⚠ Not configured. Run: clauxton mcp setup")
    except Exception:
        click.echo(click.style("🔌 MCP Server:", fg="yellow", bold=True))
        click.echo("  ⚠ Not configured. Run: clauxton mcp setup")

    click.echo()


@cli.command()
@click.option(
    "--limit",
    default=3,
    type=int,
    help="Number of entries to show per category (default: 3)",
)
def overview(limit: int) -> None:
    """
    Show comprehensive project overview with detailed breakdowns.

    Displays:
    - Knowledge Base entries grouped by category
    - Task breakdown by status with next recommendations
    - Repository statistics
    - Recent activity

    Example:
        $ clauxton overview
        $ clauxton overview --limit 5  # Show 5 entries per category
    """
    from pathlib import Path

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    click.echo(
        click.style(f"\n📊 Project Overview: {root_dir.name}\n", fg="cyan", bold=True)
    )
    click.echo(f"Location: {root_dir}\n")

    # Knowledge Base by Category
    try:
        from typing import Dict, List

        from clauxton.core.knowledge_base import KnowledgeBase
        from clauxton.core.models import KnowledgeBaseEntry

        kb = KnowledgeBase(root_dir)
        entries = kb.list_all()

        if entries:
            click.echo(click.style("📚 Knowledge Base:\n", fg="green", bold=True))

            # Group by category
            by_category: Dict[str, List[KnowledgeBaseEntry]] = {}
            for entry in entries:
                cat = entry.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(entry)

            # Category icons
            icons = {
                "architecture": "🏗️ ",
                "constraint": "⚠️ ",
                "decision": "✅",
                "pattern": "🔧",
                "convention": "📋",
            }

            for category in [
                "architecture",
                "constraint",
                "decision",
                "pattern",
                "convention",
            ]:
                if category in by_category:
                    cat_entries = by_category[category]
                    count = len(cat_entries)
                    icon = icons.get(category, "•")

                    click.echo(
                        click.style(
                            f"{icon} {category.capitalize()} ({count} "
                            f"{'entry' if count == 1 else 'entries'})",
                            fg="yellow",
                            bold=True,
                        )
                    )

                    # Show first N entries
                    for entry in cat_entries[:limit]:
                        click.echo(f"  • {entry.title}")
                        if entry.content:
                            # Show first 60 chars of content
                            preview = (
                                entry.content[:60] + "..."
                                if len(entry.content) > 60
                                else entry.content
                            )
                            click.echo(
                                click.style(f"    {preview}", fg="white", dim=True)
                            )

                    if count > limit:
                        remaining = count - limit
                        click.echo(
                            click.style(
                                f"  ... and {remaining} more",
                                fg="cyan",
                                dim=True,
                            )
                        )
                    click.echo()
        else:
            click.echo(click.style("📚 Knowledge Base: ", fg="yellow", bold=True))
            click.echo("  No entries yet. Add one: clauxton kb add\n")
    except Exception:
        click.echo(click.style("📚 Knowledge Base: ", fg="yellow", bold=True))
        click.echo("  No entries yet.\n")

    # Task Breakdown
    try:
        from typing import Dict, List

        from clauxton.core.models import Task
        from clauxton.core.task_manager import TaskManager

        tm = TaskManager(root_dir)
        tasks = tm.list_all()

        if tasks:
            # Group by status
            by_status: Dict[str, List[Task]] = {
                "in_progress": [],
                "blocked": [],
                "pending": [],
                "completed": [],
            }
            for task in tasks:
                by_status[task.status].append(task)

            total = len(tasks)
            click.echo(
                click.style(
                    f"📋 Tasks: {total} total\n",
                    fg="green",
                    bold=True,
                )
            )

            # In Progress
            if by_status["in_progress"]:
                count = len(by_status["in_progress"])
                click.echo(
                    click.style(f"▶️  In Progress ({count}):", fg="blue", bold=True)
                )
                for task in by_status["in_progress"]:
                    priority_icon = (
                        "🔴" if task.priority == "critical"
                        else "🟠" if task.priority == "high"
                        else "🟡" if task.priority == "medium"
                        else "🟢"
                    )
                    click.echo(f"  {priority_icon} {task.id}: {task.name}")
                click.echo()

            # Blocked
            if by_status["blocked"]:
                count = len(by_status["blocked"])
                click.echo(click.style(f"⏸️  Blocked ({count}):", fg="red", bold=True))
                for task in by_status["blocked"]:
                    deps = ", ".join(task.depends_on) if task.depends_on else "unknown"
                    click.echo(f"  • {task.id}: {task.name}")
                    click.echo(
                        click.style(f"    Waiting for: {deps}", fg="white", dim=True)
                    )
                click.echo()

            # Pending
            if by_status["pending"]:
                count = len(by_status["pending"])
                click.echo(
                    click.style(f"📌 Pending ({count}):", fg="yellow", bold=True)
                )
                for task in by_status["pending"][:limit]:
                    priority_icon = (
                        "🔴" if task.priority == "critical"
                        else "🟠" if task.priority == "high"
                        else "🟡" if task.priority == "medium"
                        else "🟢"
                    )
                    click.echo(f"  {priority_icon} {task.id}: {task.name}")
                if count > limit:
                    remaining = count - limit
                    click.echo(
                        click.style(f"  ... and {remaining} more", fg="cyan", dim=True)
                    )
                click.echo()

            # Completed
            if by_status["completed"]:
                count = len(by_status["completed"])
                pct = int((count / total) * 100)
                click.echo(
                    click.style(
                        f"✅ Completed ({count}/{total} = {pct}%)", fg="green"
                    )
                )
                click.echo()

            # Next recommendation
            try:
                next_task = tm.get_next_task()
                if next_task:
                    click.echo(
                        click.style("💡 Recommended Next:", fg="blue", bold=True)
                    )
                    click.echo(f"  → {next_task.id}: {next_task.name}")
                    if next_task.description:
                        click.echo(
                            click.style(
                                f"    {next_task.description}", fg="white", dim=True
                            )
                        )
                    click.echo()
            except Exception:
                pass

        else:
            click.echo(click.style("📋 Tasks: ", fg="yellow", bold=True))
            click.echo("  No tasks yet. Create one: clauxton task add\n")
    except Exception:
        click.echo(click.style("📋 Tasks: ", fg="yellow", bold=True))
        click.echo("  No tasks yet.\n")

    click.echo(
        click.style("💡 Quick Actions:", fg="blue", bold=True)
    )
    click.echo("  • Full status: " + click.style("clauxton status", fg="cyan"))
    click.echo("  • Search KB: " + click.style("clauxton kb search QUERY", fg="cyan"))
    click.echo("  • Add entry: " + click.style("clauxton kb add", fg="cyan"))
    click.echo("  • Next task: " + click.style("clauxton task next", fg="cyan"))
    click.echo()


@cli.command()
@click.option("--yesterday", is_flag=True, help="Show yesterday's completed tasks")
def resume(yesterday: bool) -> None:
    """
    Resume work on project - shows where you left off.

    Perfect for coming back to a project after a break!
    Displays:
    - Time since last activity
    - Last task you were working on
    - Recent KB entries
    - Yesterday's achievements (with --yesterday)
    - Suggested next steps

    Examples:
        $ clauxton resume
        $ clauxton resume --yesterday
    """
    from datetime import datetime, timedelta, timezone
    from typing import Optional

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    click.echo(click.style("\n👋 Welcome back!\n", fg="cyan", bold=True))

    # Calculate time since last activity
    kb_file = clauxton_dir / "knowledge-base.yml"
    tasks_file = clauxton_dir / "tasks.yml"

    last_activity: Optional[datetime] = None
    activity_source = ""

    for file, name in [(kb_file, "KB"), (tasks_file, "Tasks")]:
        if file.exists():
            mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
            if last_activity is None or mtime > last_activity:
                last_activity = mtime
                activity_source = name

    if last_activity:
        now = datetime.now(timezone.utc)
        time_diff = now - last_activity
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60

        if days > 0:
            time_str = f"{days} day{'s' if days != 1 else ''} ago"
        elif hours > 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif minutes > 0:
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            time_str = "just now"

        click.echo(f"📅 Last activity: {time_str} ({activity_source})\n")
    else:
        click.echo("📅 No activity detected yet\n")

    # Get last task worked on
    tm = TaskManager(root_dir)
    all_tasks = tm.list_all()

    if all_tasks:
        # Find tasks in progress first
        in_progress = [t for t in all_tasks if t.status == "in_progress"]

        if in_progress:
            click.echo(click.style("📋 Where you left off:\n", fg="green", bold=True))
            for task in in_progress[:3]:  # Show up to 3 in-progress tasks
                priority_icon = (
                    "🔴"
                    if task.priority == "critical"
                    else "🟠"
                    if task.priority == "high"
                    else "🟡"
                    if task.priority == "medium"
                    else "🟢"
                )
                click.echo(f"  {priority_icon} {task.id}: {task.name}")
                if task.description:
                    preview = (
                        task.description[:60] + "..."
                        if len(task.description) > 60
                        else task.description
                    )
                    click.echo(click.style(f"     {preview}", fg="white", dim=True))
            click.echo()
        else:
            # Show most recently updated task
            sorted_tasks = sorted(
                all_tasks,
                key=lambda t: t.completed_at or t.started_at or t.created_at,
                reverse=True,
            )
            recent_task = sorted_tasks[0]

            status_emoji = (
                "✅"
                if recent_task.status == "completed"
                else "⏸️ "
                if recent_task.status == "blocked"
                else "📝"
            )
            click.echo(
                click.style("📋 Most recent task:\n", fg="green", bold=True)
            )
            click.echo(f"  {status_emoji} {recent_task.id}: {recent_task.name}")
            click.echo(
                click.style(f"     Status: {recent_task.status}", fg="white", dim=True)
            )
            click.echo()

    # Show yesterday's completed tasks if requested
    if yesterday:
        yesterday_date = (datetime.now() - timedelta(days=1)).date()

        def is_yesterday(dt: datetime) -> bool:
            """Check if datetime is yesterday."""
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt.date() == yesterday_date

        yesterday_tasks = [
            t for t in all_tasks
            if t.completed_at and is_yesterday(t.completed_at)
        ]

        if yesterday_tasks:
            total_hours = sum(t.actual_hours or 0 for t in yesterday_tasks)
            click.echo(click.style("🌅 Yesterday's achievements:\n", fg="green", bold=True))
            for task in yesterday_tasks:
                time_info = f" ({task.actual_hours}h)" if task.actual_hours else ""
                click.echo(f"  ✅ {task.id}: {task.name}{time_info}")
            if total_hours > 0:
                click.echo(click.style(f"\n  Total: {total_hours:.1f}h completed\n", fg="green"))
            else:
                click.echo()
        else:
            click.echo(click.style("🌅 No tasks completed yesterday\n", fg="yellow"))

    # Show recent KB entries
    kb = KnowledgeBase(root_dir)
    entries = kb.list_all()

    if entries:
        # Sort by created_at, most recent first
        sorted_entries = sorted(entries, key=lambda e: e.created_at, reverse=True)
        recent_entries = sorted_entries[:3]

        click.echo(click.style("📚 Recent knowledge:\n", fg="yellow", bold=True))

        icons = {
            "architecture": "🏗️ ",
            "constraint": "⚠️ ",
            "decision": "✅",
            "pattern": "🔧",
            "convention": "📋",
        }

        for entry in recent_entries:
            icon = icons.get(entry.category, "•")
            click.echo(f"  {icon} {entry.title}")

            # Calculate age
            # Use naive datetime for age calculation since KB entries are stored naive
            now_naive = datetime.now()
            entry_time = entry.created_at
            # Remove timezone if present
            if entry_time.tzinfo is not None:
                entry_time = entry_time.replace(tzinfo=None)
            age = now_naive - entry_time
            days = age.days

            if days == 0:
                age_str = "today"
            elif days == 1:
                age_str = "yesterday"
            else:
                age_str = f"{days} days ago"

            click.echo(
                click.style(
                    f"     {entry.category} • {age_str}", fg="white", dim=True
                )
            )

        click.echo()

    # Suggest next steps with actionable commands
    click.echo(click.style("💡 Suggested next actions:\n", fg="blue", bold=True))

    actions_shown = 0

    # 1. Continue in-progress tasks
    in_progress_tasks = [t for t in all_tasks if t.status == "in_progress"]
    if in_progress_tasks and actions_shown < 3:
        task = in_progress_tasks[0]
        actions_shown += 1
        click.echo(f"  {actions_shown}. Continue working on: {task.name}")
        click.echo(click.style(f"     → clauxton focus {task.id}", fg="cyan"))

    # 2. Start next high-priority pending task
    pending_tasks = [t for t in all_tasks if t.status == "pending"]
    if pending_tasks and actions_shown < 3:
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_pending = sorted(
            pending_tasks, key=lambda t: priority_order.get(t.priority, 4)
        )
        task = sorted_pending[0]
        priority_emoji = "🔴" if task.priority in ["critical", "high"] else "🟡"
        actions_shown += 1
        click.echo(f"  {actions_shown}. {priority_emoji} Start high-priority: {task.name}")
        click.echo(click.style(f"     → clauxton focus {task.id}", fg="cyan"))
        cmd = f"clauxton task update {task.id} --status in_progress"
        click.echo(click.style(f"     → {cmd}", fg="cyan"))

    # 3. Review completed tasks
    completed_tasks = [t for t in all_tasks if t.status == "completed"]
    if completed_tasks and actions_shown < 3:
        actions_shown += 1
        click.echo(f"  {actions_shown}. Review {len(completed_tasks)} completed task(s)")
        click.echo(click.style("     → clauxton task list --status completed", fg="cyan"))

    # 4. Add knowledge if no entries or very few
    if (not entries or len(entries) < 3) and actions_shown < 3:
        actions_shown += 1
        click.echo(f"  {actions_shown}. Document project knowledge")
        click.echo(click.style("     → clauxton kb add", fg="cyan"))
        click.echo(click.style("     → clauxton kb templates  (see examples)", fg="cyan", dim=True))

    # If no specific actions, show general getting started
    if actions_shown == 0:
        click.echo("  1. Get started with project setup:")
        click.echo(click.style("     → clauxton kb add", fg="cyan"))
        click.echo(click.style("     → clauxton task add", fg="cyan"))

    click.echo()

    # Show quick commands
    click.echo(click.style("⚡ Quick commands:\n", fg="magenta", bold=True))
    click.echo(f"  • Overview: {click.style('clauxton overview', fg='cyan')}")
    click.echo(f"  • Next task: {click.style('clauxton task next', fg='cyan')}")
    click.echo(f"  • Search: {click.style('clauxton kb search QUERY', fg='cyan')}")
    click.echo()


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def stats(json_output: bool) -> None:
    """
    Show project statistics and insights.

    Displays comprehensive metrics about your project:
    - Knowledge Base distribution by category
    - Task breakdown by status and priority
    - Repository statistics (if indexed)
    - Activity metrics and trends
    - Completion rates

    Perfect for understanding project health at a glance!

    Examples:
        $ clauxton stats         # Display statistics
        $ clauxton stats --json  # JSON output
    """
    from typing import Dict

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    click.echo(click.style(f"\n📊 Statistics: {root_dir.name}\n", fg="cyan", bold=True))

    # Knowledge Base Statistics
    kb = KnowledgeBase(root_dir)
    entries = kb.list_all()

    # Task Statistics
    tm = TaskManager(root_dir)
    tasks = tm.list_all()

    # Collect all data for JSON output
    by_category: Dict[str, int] = {}
    for entry in entries:
        by_category[entry.category] = by_category.get(entry.category, 0) + 1

    by_status: Dict[str, int] = {}
    for task_item in tasks:
        by_status[task_item.status] = by_status.get(task_item.status, 0) + 1

    by_priority: Dict[str, int] = {}
    for task_item in tasks:
        by_priority[task_item.priority] = by_priority.get(task_item.priority, 0) + 1

    completed = by_status.get("completed", 0)
    completion_rate = (completed / len(tasks) * 100) if tasks else 0

    total_estimated = sum(t.estimated_hours or 0 for t in tasks)
    total_actual = sum(t.actual_hours or 0 for t in tasks)

    # Repository stats
    repo_index_file = clauxton_dir / "repository_map.json"
    repo_stats = {}
    if repo_index_file.exists():
        import json as json_lib

        try:
            with open(repo_index_file) as f:
                repo_data = json_lib.load(f)
            total_files = len(repo_data.get("files", {}))
            total_symbols = sum(
                len(file_data.get("symbols", []))
                for file_data in repo_data.get("files", {}).values()
            )
            repo_stats = {
                "indexed_files": total_files,
                "total_symbols": total_symbols,
                "avg_symbols_per_file": total_symbols / total_files if total_files > 0 else 0,
            }
        except Exception:
            pass

    # JSON output
    if json_output:
        import json

        all_tags = []
        for entry in entries:
            all_tags.extend(entry.tags)

        data = {
            "project_name": root_dir.name,
            "knowledge_base": {
                "total_entries": len(entries),
                "total_categories": len(by_category),
                "by_category": by_category,
                "total_tags": len(all_tags),
                "unique_tags": len(set(all_tags)),
            },
            "tasks": {
                "total_tasks": len(tasks),
                "by_status": by_status,
                "by_priority": by_priority,
                "completion_rate": round(completion_rate, 1),
                "total_estimated_hours": total_estimated,
                "total_actual_hours": total_actual,
            },
            "repository": repo_stats if repo_stats else None,
        }
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(click.style(f"\n📊 Statistics: {root_dir.name}\n", fg="cyan", bold=True))

    click.echo(click.style("📚 Knowledge Base:\n", fg="green", bold=True))

    if entries:
        # Category icons
        icons = {
            "architecture": "🏗️ ",
            "constraint": "⚠️ ",
            "decision": "✅",
            "pattern": "🔧",
            "convention": "📋",
        }

        click.echo(f"  Total Entries: {len(entries)}")
        click.echo(f"  Categories: {len(by_category)}\n")

        # Show distribution
        click.echo("  Distribution:")
        for category in ["architecture", "constraint", "decision", "pattern", "convention"]:
            if category in by_category:
                count = by_category[category]
                percentage = (count / len(entries)) * 100
                icon = icons.get(category, "•")
                bar = "█" * int(percentage / 5)  # Scale to ~20 chars max
                click.echo(
                    f"    {icon} {category.capitalize():12} {count:3} "
                    f"({percentage:5.1f}%) {bar}"
                )
        click.echo()

        # Tag statistics
        all_tags = []
        for entry in entries:
            all_tags.extend(entry.tags)

        if all_tags:
            unique_tags = len(set(all_tags))
            click.echo(f"  Tags: {unique_tags} unique, {len(all_tags)} total")
            click.echo()
    else:
        click.echo("  No entries yet\n")

    click.echo(click.style("📋 Tasks:\n", fg="yellow", bold=True))

    if tasks:
        click.echo(f"  Total Tasks: {len(tasks)}\n")

        # Status breakdown
        click.echo("  By Status:")
        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "blocked": "🚫",
        }

        for status in ["pending", "in_progress", "completed", "blocked"]:
            if status in by_status:
                count = by_status[status]
                percentage = (count / len(tasks)) * 100
                icon = status_icons.get(status, "•")
                bar = "█" * int(percentage / 5)
                click.echo(
                    f"    {icon} {status.replace('_', ' ').capitalize():12} {count:3} "
                    f"({percentage:5.1f}%) {bar}"
                )
        click.echo()

        # Priority breakdown
        click.echo("  By Priority:")
        priority_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }

        for priority in ["critical", "high", "medium", "low"]:
            if priority in by_priority:
                count = by_priority[priority]
                percentage = (count / len(tasks)) * 100
                icon = priority_icons.get(priority, "•")
                bar = "█" * int(percentage / 5)
                click.echo(
                    f"    {icon} {priority.capitalize():12} {count:3} "
                    f"({percentage:5.1f}%) {bar}"
                )
        click.echo()

        # Completion rate
        completed = by_status.get("completed", 0)
        completion_rate = (completed / len(tasks)) * 100
        click.echo(f"  Completion Rate: {completion_rate:.1f}% ({completed}/{len(tasks)})")

        # Estimated hours
        total_estimated = sum(t.estimated_hours or 0 for t in tasks)
        total_actual = sum(t.actual_hours or 0 for t in tasks)

        if total_estimated > 0:
            click.echo(f"  Estimated Hours: {total_estimated:.1f}h")
            if total_actual > 0:
                click.echo(f"  Actual Hours: {total_actual:.1f}h")
                variance = ((total_actual - total_estimated) / total_estimated) * 100
                if variance > 0:
                    click.echo(
                        click.style(
                            f"  Variance: +{variance:.1f}% (over estimate)",
                            fg="yellow",
                        )
                    )
                elif variance < 0:
                    click.echo(
                        click.style(
                            f"  Variance: {variance:.1f}% (under estimate)",
                            fg="green",
                        )
                    )
        click.echo()
    else:
        click.echo("  No tasks yet\n")

    # Repository Statistics (if indexed)
    if repo_index_file.exists():
        import json

        click.echo(click.style("🗺️  Repository Map:\n", fg="blue", bold=True))

        try:
            with open(repo_index_file) as f:
                repo_data = json.load(f)

            total_files = len(repo_data.get("files", {}))
            total_symbols = sum(
                len(file_data.get("symbols", []))
                for file_data in repo_data.get("files", {}).values()
            )

            click.echo(f"  Indexed Files: {total_files}")
            click.echo(f"  Total Symbols: {total_symbols}")

            if total_files > 0:
                avg_symbols = total_symbols / total_files
                click.echo(f"  Avg Symbols/File: {avg_symbols:.1f}")

            click.echo()
        except Exception:
            click.echo("  Index file exists but couldn't be read\n")

    # Overall project health
    click.echo(click.style("💡 Project Health:\n", fg="magenta", bold=True))

    health_score: float = 0.0
    max_score: float = 0.0

    # KB coverage (0-30 points)
    max_score += 30
    if entries:
        kb_score = min(len(entries) * 3, 30)  # Up to 30 points for KB
        health_score += kb_score

    # Task management (0-40 points)
    max_score += 40
    if tasks:
        # Points for having tasks
        health_score += 10

        # Points for completion rate
        completion_points = min(completion_rate * 0.3, 30)
        health_score += completion_points

    # Repository indexing (0-30 points)
    max_score += 30
    if repo_index_file.exists():
        health_score += 30

    if max_score > 0:
        health_percentage = (health_score / max_score) * 100

        if health_percentage >= 80:
            health_status = click.style("Excellent", fg="green", bold=True)
            health_icon = "🌟"
        elif health_percentage >= 60:
            health_status = click.style("Good", fg="green")
            health_icon = "✨"
        elif health_percentage >= 40:
            health_status = click.style("Fair", fg="yellow")
            health_icon = "⚠️ "
        else:
            health_status = click.style("Needs Attention", fg="red")
            health_icon = "📉"

        health_bar = "█" * int(health_percentage / 5)
        click.echo(f"  {health_icon} Status: {health_status}")
        click.echo(f"  Score: {health_percentage:.0f}% {health_bar}")

        # Recommendations
        click.echo("\n  Recommendations:")
        if len(entries) < 5:
            click.echo("    • Add more knowledge base entries (architecture, decisions, etc.)")
        if len(tasks) == 0:
            click.echo("    • Create tasks to track your work")
        elif completion_rate < 50:
            click.echo("    • Focus on completing pending tasks")
        if not repo_index_file.exists():
            click.echo("    • Index your repository: clauxton repo index")
    else:
        click.echo("  No data yet. Run 'clauxton init' and add some content!")

    click.echo()


@cli.command()
def morning() -> None:
    """
    Interactive morning briefing and planning.

    Start your day right with a guided morning workflow that shows
    yesterday's accomplishments, suggests today's tasks, and helps you
    set focus for a productive day!

    Example:
        $ clauxton morning
    """
    from datetime import datetime, timedelta

    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    click.echo()
    click.echo(click.style("☀️  Good Morning! Let's plan your day.\n", fg="yellow", bold=True))

    # Show yesterday's summary
    tm = TaskManager(root_dir)
    tasks = tm.list_all()

    yesterday = (datetime.now() - timedelta(days=1)).date()
    completed_yesterday = [
        t
        for t in tasks
        if t.completed_at
        and t.completed_at.replace(tzinfo=None).date() == yesterday
    ]

    if completed_yesterday:
        click.echo(click.style("✅ Yesterday's Wins:\n", fg="green", bold=True))
        for task in completed_yesterday[:5]:
            click.echo(f"  • {task.name}")
        if len(completed_yesterday) > 5:
            click.echo(f"  ... and {len(completed_yesterday) - 5} more")
        click.echo()

    # Show current status
    in_progress = [t for t in tasks if t.status == "in_progress"]
    pending = [t for t in tasks if t.status == "pending"]

    if in_progress:
        click.echo(click.style("⏳ In Progress:\n", fg="cyan", bold=True))
        for task in in_progress:
            click.echo(f"  • {task.id}: {task.name}")
        click.echo()

    # Suggest today's tasks
    click.echo(click.style("📋 Suggested Tasks for Today:\n", fg="magenta", bold=True))

    # Get high priority pending tasks
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_pending = sorted(pending, key=lambda t: priority_order.get(t.priority, 4))

    if not sorted_pending:
        click.echo("  No pending tasks. Great job! 🎉")
        click.echo()
        return

    # Show top 5 suggested tasks
    suggestions = sorted_pending[:5]
    for idx, task in enumerate(suggestions, 1):
        priority_icon = (
            "🔴"
            if task.priority == "critical"
            else "🟠"
            if task.priority == "high"
            else "🟡"
            if task.priority == "medium"
            else "🟢"
        )
        click.echo(f"  {idx}. {priority_icon} {task.id}: {task.name} ({task.priority})")

    click.echo()

    # Interactive selection
    choice = click.prompt(
        click.style("Select a task to focus on (1-5, or 0 to skip)", fg="cyan"),
        type=int,
        default=0
    )

    if choice > 0 and choice <= len(suggestions):
        selected_task = suggestions[choice - 1]

        # Set focus
        import yaml

        focus_file = clauxton_dir / "focus.yml"
        focus_data = {
            "task_id": selected_task.id,
            "task_name": selected_task.name,
            "started_at": datetime.now().isoformat(),
        }
        focus_file.write_text(yaml.dump(focus_data), encoding="utf-8")

        # Update task status
        tm.update(
            selected_task.id,
            {"status": "in_progress", "started_at": datetime.now()},
        )

        click.echo()
        click.echo(click.style("🎯 Focus set!", fg="green", bold=True))
        click.echo(f"   Working on: {selected_task.id} - {selected_task.name}")
        click.echo()
        click.echo("   Commands:")
        click.echo(f"     Check focus: {click.style('clauxton focus', fg='cyan')}")
        click.echo(f"     Clear focus: {click.style('clauxton focus --clear', fg='cyan')}")
        complete_cmd = f"clauxton task update {selected_task.id} --status completed"
        click.echo(f"     Mark complete: {click.style(complete_cmd, fg='cyan')}")
        click.echo()
        click.echo(click.style("   Have a productive day! 🚀", fg="yellow"))
    else:
        click.echo()
        no_focus_msg = "   No focus set. You can set it anytime with:"
        click.echo(click.style(no_focus_msg, fg="white", dim=True))
        click.echo(f"     {click.style('clauxton focus TASK-ID', fg='cyan')}")

    click.echo()


@cli.command()
@click.option(
    "--date",
    "-d",
    default=None,
    help="Date to show (YYYY-MM-DD format). Default: today",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def daily(date: Optional[str], json_output: bool) -> None:
    """
    Show daily summary of activities.

    Perfect for end-of-day review or standup preparation!
    Shows what you accomplished today and what's next.

    Examples:
        $ clauxton daily                    # Today's summary
        $ clauxton daily --date 2025-10-24  # Specific date
        $ clauxton daily --json             # JSON output
    """
    import datetime as dt_module
    from datetime import datetime, timedelta

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    # Parse target date
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(
                click.style(
                    f"Invalid date format: {date}. Use YYYY-MM-DD", fg="red"
                )
            )
            raise click.Abort()
    else:
        target_date = datetime.now().date()

    # Display header
    if target_date == datetime.now().date():
        date_str = "Today"
    elif target_date == (datetime.now().date() - timedelta(days=1)):
        date_str = "Yesterday"
    else:
        date_str = target_date.strftime("%Y-%m-%d")

    click.echo(
        click.style(f"\n📅 Daily Summary - {date_str}\n", fg="cyan", bold=True)
    )

    # Get all KB entries and tasks
    kb = KnowledgeBase(root_dir)
    tm = TaskManager(root_dir)

    entries = kb.list_all()
    tasks = tm.list_all()

    # Filter by today
    def is_same_date(dt: datetime, target: dt_module.date) -> bool:
        """Check if datetime is on target date."""
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt.date() == target

    # Today's completed tasks
    completed_today = [
        t
        for t in tasks
        if t.completed_at and is_same_date(t.completed_at, target_date)
    ]

    if completed_today:
        click.echo(
            click.style(
                f"✅ Completed Today ({len(completed_today)}):\n",
                fg="green",
                bold=True,
            )
        )
        total_actual = 0.0
        total_estimated = 0.0
        for task in completed_today:
            estimated = task.estimated_hours or 0
            actual = task.actual_hours or 0
            total_actual += actual
            total_estimated += estimated

            time_info = ""
            if estimated > 0 or actual > 0:
                time_info = f" ({estimated}h est"
                if actual > 0:
                    time_info += f", {actual}h actual"
                time_info += ")"

            click.echo(f"  • {task.id}: {task.name}{time_info}")

        # Enhanced time summary
        click.echo()
        click.echo(click.style("  ⏱  Time Summary:", fg="cyan", bold=True))
        if total_actual > 0:
            click.echo(f"     Actual work: {total_actual:.1f}h")
        if total_estimated > 0:
            click.echo(f"     Estimated: {total_estimated:.1f}h")
        if total_actual > 0 and total_estimated > 0:
            diff = total_actual - total_estimated
            diff_pct = (diff / total_estimated * 100) if total_estimated > 0 else 0
            if diff > 0:
                variance_msg = f"     Variance: +{diff:.1f}h ({diff_pct:+.0f}%) over estimate"
                click.echo(click.style(variance_msg, fg="yellow"))
            elif diff < 0:
                variance_msg = f"     Variance: {diff:.1f}h ({diff_pct:+.0f}%) under estimate"
                click.echo(click.style(variance_msg, fg="green"))
            else:
                click.echo(click.style("     Variance: On target! 🎯", fg="green"))
        click.echo()

    # Today's KB entries
    kb_today = [e for e in entries if is_same_date(e.created_at, target_date)]

    if kb_today:
        click.echo(
            click.style(
                f"📝 Knowledge Added Today ({len(kb_today)}):\n",
                fg="yellow",
                bold=True,
            )
        )

        icons = {
            "architecture": "🏗️ ",
            "constraint": "⚠️ ",
            "decision": "✅",
            "pattern": "🔧",
            "convention": "📋",
        }

        for entry in kb_today:
            icon = icons.get(entry.category, "•")
            click.echo(f"  {icon} {entry.id}: {entry.title} ({entry.category})")
        click.echo()

    # Today's new tasks
    tasks_today = [t for t in tasks if is_same_date(t.created_at, target_date)]

    if tasks_today:
        click.echo(
            click.style(
                f"📋 Tasks Created Today ({len(tasks_today)}):\n",
                fg="blue",
                bold=True,
            )
        )

        for task in tasks_today:
            priority_icon = (
                "🔴"
                if task.priority == "critical"
                else "🟠"
                if task.priority == "high"
                else "🟡"
                if task.priority == "medium"
                else "🟢"
            )
            status_str = f" [{task.status}]"
            click.echo(f"  {priority_icon} {task.id}: {task.name}{status_str}")
        click.echo()

    # In progress tasks
    in_progress = [t for t in tasks if t.status == "in_progress"]

    # JSON output
    if json_output:
        import json

        total_actual = sum(t.actual_hours or 0 for t in completed_today)
        total_estimated = sum(t.estimated_hours or 0 for t in completed_today)

        data = {
            "date": target_date.isoformat(),
            "completed_tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                    "estimated_hours": t.estimated_hours,
                    "actual_hours": t.actual_hours,
                }
                for t in completed_today
            ],
            "kb_entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "category": e.category,
                }
                for e in kb_today
            ],
            "tasks_created": [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                    "status": t.status,
                }
                for t in tasks_today
            ],
            "in_progress_tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                }
                for t in in_progress
            ],
            "summary": {
                "total_completed": len(completed_today),
                "total_kb_entries": len(kb_today),
                "total_tasks_created": len(tasks_today),
                "total_in_progress": len(in_progress),
                "total_actual_hours": total_actual,
                "total_estimated_hours": total_estimated,
            },
        }
        click.echo(json.dumps(data, indent=2))
        return

    if in_progress:
        click.echo(click.style("⏳ In Progress:\n", fg="magenta", bold=True))
        for task in in_progress[:3]:
            priority_icon = (
                "🔴"
                if task.priority == "critical"
                else "🟠"
                if task.priority == "high"
                else "🟡"
                if task.priority == "medium"
                else "🟢"
            )

            # Calculate time since started
            time_info = ""
            if task.started_at:
                started = task.started_at
                if started.tzinfo is not None:
                    started = started.replace(tzinfo=None)
                duration = datetime.now() - started
                hours = duration.total_seconds() / 3600
                if hours < 1:
                    time_info = f" (started {int(duration.total_seconds() / 60)}m ago)"
                elif hours < 24:
                    time_info = f" (started {int(hours)}h ago)"
                else:
                    days = int(hours / 24)
                    time_info = f" (started {days}d ago)"

            click.echo(f"  {priority_icon} {task.id}: {task.name}{time_info}")
        click.echo()

    # If nothing happened today
    if not completed_today and not kb_today and not tasks_today:
        click.echo(
            click.style(
                "No activity recorded for this date.\n", fg="white", dim=True
            )
        )

    # Tomorrow's focus (only show for today)
    if target_date == datetime.now().date():
        click.echo(click.style("💡 Tomorrow's Focus:\n", fg="green", bold=True))

        # Suggest next high priority pending tasks
        pending = [t for t in tasks if t.status == "pending"]
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_pending = sorted(
            pending, key=lambda t: priority_order.get(t.priority, 4)
        )

        if sorted_pending:
            for task in sorted_pending[:3]:
                click.echo(f"  • {task.id}: {task.name} ({task.priority} priority)")
        elif in_progress:
            click.echo("  • Continue working on in-progress tasks")
        else:
            click.echo("  • No pending tasks. Great job! 🎉")

    click.echo()


@cli.command()
@click.option("--week", type=int, default=0, help="Week offset (0=current, -1=last week)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def weekly(week: int, json_output: bool) -> None:
    """
    Weekly summary with completion rate and velocity.

    Shows a comprehensive overview of your productivity for a specific week,
    including task completion rate, work hours, and knowledge base growth.

    Examples:
        $ clauxton weekly              # Current week
        $ clauxton weekly --week -1    # Last week
        $ clauxton weekly --week -2    # Two weeks ago
        $ clauxton weekly --json       # JSON output
    """
    from datetime import datetime, timedelta

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    kb = KnowledgeBase(root_dir)
    tm = TaskManager(root_dir)

    # Calculate week start (Monday) and end (Sunday)
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday) + timedelta(weeks=week)
    week_end = week_start + timedelta(days=6)

    # Get all tasks and entries
    tasks = tm.list_all()
    entries = kb.list_all()

    # Filter tasks completed this week
    def is_in_week(dt: datetime, start: Any, end: Any) -> bool:
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        task_date = dt.date()
        return bool(start <= task_date <= end)

    completed_this_week = [
        t for t in tasks if t.completed_at and is_in_week(t.completed_at, week_start, week_end)
    ]
    created_this_week = [
        t for t in tasks if is_in_week(t.created_at, week_start, week_end)
    ]
    kb_this_week = [
        e for e in entries if is_in_week(e.created_at, week_start, week_end)
    ]

    # Calculate metrics
    total_estimated = sum(t.estimated_hours or 0 for t in completed_this_week)
    total_actual = sum(t.actual_hours or 0 for t in completed_this_week)
    completion_rate = (
        (len(completed_this_week) / len(created_this_week) * 100)
        if created_this_week
        else 0
    )

    # Category breakdown
    kb_categories: dict[str, int] = {}
    for entry in kb_this_week:
        kb_categories[entry.category] = kb_categories.get(entry.category, 0) + 1

    # Priority breakdown
    task_priorities: dict[str, int] = {}
    for task_item in completed_this_week:
        task_priorities[task_item.priority] = task_priorities.get(task_item.priority, 0) + 1

    # JSON output
    if json_output:
        import json

        data = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "week_offset": week,
            "completed_tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                    "estimated_hours": t.estimated_hours,
                    "actual_hours": t.actual_hours,
                }
                for t in completed_this_week
            ],
            "created_tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                }
                for t in created_this_week
            ],
            "kb_entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "category": e.category,
                }
                for e in kb_this_week
            ],
            "summary": {
                "total_completed": len(completed_this_week),
                "total_created": len(created_this_week),
                "completion_rate": round(completion_rate, 1),
                "velocity": len(completed_this_week),
                "total_estimated_hours": total_estimated,
                "total_actual_hours": total_actual,
                "total_kb_entries": len(kb_this_week),
                "kb_by_category": kb_categories,
                "tasks_by_priority": task_priorities,
            },
        }
        click.echo(json.dumps(data, indent=2))
        return

    # Display header
    week_label = "This Week" if week == 0 else f"{abs(week)} Week{'s' if abs(week) > 1 else ''} Ago"
    click.echo()
    click.echo(click.style(f"📊 Weekly Summary - {week_label}", fg="cyan", bold=True))
    click.echo(
        click.style(
            f"   {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}\n",
            fg="white",
            dim=True
        )
    )

    # Task completion metrics
    click.echo(click.style("✅ Task Completion:", fg="green", bold=True))
    click.echo(f"   Completed: {len(completed_this_week)} tasks")
    click.echo(f"   Created: {len(created_this_week)} tasks")

    # Calculate completion rate
    if created_this_week:
        completion_rate = (len(completed_this_week) / len(created_this_week)) * 100
        click.echo(f"   Completion rate: {completion_rate:.0f}%")

    # Velocity (tasks per week)
    click.echo(f"   Velocity: {len(completed_this_week)} tasks/week")
    click.echo()

    # Work hours summary
    total_estimated = sum(t.estimated_hours or 0 for t in completed_this_week)
    total_actual = sum(t.actual_hours or 0 for t in completed_this_week)

    click.echo(click.style("⏱  Work Hours:", fg="cyan", bold=True))
    if total_estimated > 0:
        click.echo(f"   Estimated: {total_estimated:.1f}h")
    if total_actual > 0:
        click.echo(f"   Actual: {total_actual:.1f}h")
    if total_estimated > 0 and total_actual > 0:
        diff = total_actual - total_estimated
        diff_pct = (diff / total_estimated * 100) if total_estimated > 0 else 0
        if diff > 0:
            click.echo(click.style(f"   Variance: +{diff:.1f}h ({diff_pct:+.0f}%)", fg="yellow"))
        elif diff < 0:
            click.echo(click.style(f"   Variance: {diff:.1f}h ({diff_pct:+.0f}%)", fg="green"))
        else:
            click.echo(click.style("   On target! 🎯", fg="green"))
    if total_estimated == 0 and total_actual == 0:
        click.echo(click.style("   No time tracking data", fg="white", dim=True))
    click.echo()

    # Knowledge Base growth
    click.echo(click.style("📝 Knowledge Base Growth:", fg="yellow", bold=True))
    click.echo(f"   New entries: {len(kb_this_week)}")

    if kb_this_week:
        click.echo("   By category:")
        icons = {
            "architecture": "🏗️ ",
            "constraint": "⚠️ ",
            "decision": "✅",
            "pattern": "🔧",
            "convention": "📋",
        }
        for cat, count in sorted(kb_categories.items(), key=lambda x: x[1], reverse=True):
            icon = icons.get(cat, "•")
            click.echo(f"     {icon} {cat}: {count}")
    click.echo()

    # Priority breakdown of completed tasks
    if completed_this_week:
        click.echo(click.style("🎯 Completed Tasks by Priority:", fg="magenta", bold=True))
        priority_icons: dict[str, str] = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        for priority in ["critical", "high", "medium", "low"]:
            if priority in task_priorities:
                icon = priority_icons.get(priority, "•")
                click.echo(f"   {icon} {priority}: {task_priorities[priority]}")
        click.echo()

    # Show top completed tasks (max 5)
    if completed_this_week:
        click.echo(click.style("🏆 Top Completed Tasks:", fg="green", bold=True))
        for task in completed_this_week[:5]:
            priority_icon = (
                "🔴"
                if task.priority == "critical"
                else "🟠"
                if task.priority == "high"
                else "🟡"
                if task.priority == "medium"
                else "🟢"
            )
            click.echo(f"   {priority_icon} {task.id}: {task.name}")
        if len(completed_this_week) > 5:
            click.echo(f"   ... and {len(completed_this_week) - 5} more")
        click.echo()

    # Summary message
    if not completed_this_week and not kb_this_week:
        click.echo(
            click.style(
                "No activity recorded for this week.\n",
                fg="white",
                dim=True
            )
        )


@cli.command()
@click.option("--days", default=30, help="Number of days to analyze (default: 30)")
def trends(days: int) -> None:
    """
    Productivity trends and analysis.

    Analyzes your productivity patterns over time, showing task completion
    trends, work hours evolution, and category focus shifts.

    Examples:
        $ clauxton trends           # Last 30 days
        $ clauxton trends --days 7  # Last week
        $ clauxton trends --days 90 # Last quarter
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    click.echo()
    click.echo(click.style(f"📈 Productivity Trends (Last {days} Days)\n", fg="cyan", bold=True))

    # Get data
    tm = TaskManager(root_dir)
    kb = KnowledgeBase(root_dir)

    tasks = tm.list_all()
    entries = kb.list_all()

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    # Group tasks by completion date
    daily_completions: dict[str, int] = defaultdict(int)
    daily_hours: dict[str, float] = defaultdict(float)

    for task_item in tasks:
        if task_item.completed_at:
            comp_date = task_item.completed_at.replace(tzinfo=None).date()
            if start_date <= comp_date <= end_date:
                date_key = comp_date.isoformat()
                daily_completions[date_key] += 1
                if task_item.actual_hours:
                    daily_hours[date_key] += task_item.actual_hours

    # Calculate weekly averages
    total_completed = sum(daily_completions.values())
    total_hours = sum(daily_hours.values())
    weeks = days / 7
    avg_per_week = total_completed / weeks if weeks > 0 else 0
    avg_hours_per_week = total_hours / weeks if weeks > 0 else 0

    # Display summary
    click.echo(click.style("📊 Overview:", fg="green", bold=True))
    click.echo(f"  Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    click.echo(f"  Tasks completed: {total_completed}")
    click.echo(f"  Average per week: {avg_per_week:.1f} tasks")
    if total_hours > 0:
        click.echo(f"  Total hours tracked: {total_hours:.1f}h")
        click.echo(f"  Average per week: {avg_hours_per_week:.1f}h")
    click.echo()

    # Task completion trend (simple ASCII chart)
    if daily_completions:
        click.echo(click.style("📅 Completion Trend (Daily):", fg="magenta", bold=True))

        # Group by week for better visualization
        weekly_data: dict[str, int] = {}
        current_week_start = start_date
        while current_week_start <= end_date:
            week_end = min(current_week_start + timedelta(days=6), end_date)
            week_key = f"{current_week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')}"

            week_total = 0
            num_days = (week_end - current_week_start).days + 1
            date_range = [current_week_start + timedelta(days=x) for x in range(num_days)]
            for single_date in date_range:
                date_key = single_date.isoformat()
                week_total += daily_completions.get(date_key, 0)

            weekly_data[week_key] = week_total
            current_week_start = week_end + timedelta(days=1)

        # Display ASCII chart
        if weekly_data:
            max_count = max(weekly_data.values()) if weekly_data.values() else 1
            for week_label, count in weekly_data.items():
                bar_length = int((count / max_count) * 40) if max_count > 0 else 0
                bar = "█" * bar_length
                click.echo(f"  {week_label:13} {count:3} {bar}")
        click.echo()

    # Category focus over time
    kb_by_category: dict[str, int] = defaultdict(int)
    for entry in entries:
        entry_date = entry.created_at.replace(tzinfo=None).date()
        if start_date <= entry_date <= end_date:
            kb_by_category[entry.category] += 1

    if kb_by_category:
        click.echo(click.style("📝 Knowledge Base Focus:", fg="yellow", bold=True))
        icons = {
            "architecture": "🏗️ ",
            "constraint": "⚠️ ",
            "decision": "✅",
            "pattern": "🔧",
            "convention": "📋",
        }
        sorted_cats = sorted(kb_by_category.items(), key=lambda x: x[1], reverse=True)
        total_kb = sum(kb_by_category.values())
        for category, count in sorted_cats:
            icon = icons.get(category, "•")
            percentage = (count / total_kb) * 100 if total_kb > 0 else 0
            click.echo(f"  {icon} {category.capitalize():12} {count:3} ({percentage:5.1f}%)")
        click.echo()

    # Priority distribution trend
    priority_dist: dict[str, int] = defaultdict(int)
    for task_item in tasks:
        if task_item.completed_at:
            comp_date = task_item.completed_at.replace(tzinfo=None).date()
            if start_date <= comp_date <= end_date:
                priority_dist[task_item.priority] += 1

    if priority_dist:
        click.echo(click.style("🎯 Completed Tasks by Priority:", fg="blue", bold=True))
        priority_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        for priority in ["critical", "high", "medium", "low"]:
            if priority in priority_dist:
                count = priority_dist[priority]
                percentage = (count / total_completed) * 100 if total_completed > 0 else 0
                icon = priority_icons.get(priority, "•")
                click.echo(f"  {icon} {priority.capitalize():8} {count:3} ({percentage:5.1f}%)")
        click.echo()

    # Insights
    click.echo(click.style("💡 Insights:", fg="green", bold=True))
    if avg_per_week > 5:
        click.echo("  ✨ Great velocity! You're completing 5+ tasks per week on average")
    elif avg_per_week > 0:
        click.echo(f"  📈 You're averaging {avg_per_week:.1f} tasks per week")
    else:
        click.echo("  💤 No tasks completed in this period")

    if priority_dist.get("critical", 0) > priority_dist.get("low", 0):
        click.echo("  🔥 Focusing on high-priority items - excellent prioritization!")

    if len(kb_by_category) >= 3:
        click.echo("  📚 Well-rounded knowledge base across multiple categories")

    click.echo()


@cli.command()
@click.argument("task_id", required=False)
@click.option("--clear", is_flag=True, help="Clear current focus")
def focus(task_id: Optional[str], clear: bool) -> None:
    """
    Set or view focus task for concentration.

    Focus mode helps you concentrate on a single task by highlighting it
    in overview and resume commands. Perfect for deep work sessions!

    Examples:
        $ clauxton focus TASK-001     # Set focus
        $ clauxton focus               # View current focus
        $ clauxton focus --clear       # Clear focus
    """
    from datetime import datetime

    from clauxton.core.task_manager import TaskManager
    from clauxton.utils.yaml_utils import read_yaml, write_yaml

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    focus_file = clauxton_dir / "focus.yml"

    # Clear focus
    if clear:
        if focus_file.exists():
            focus_file.unlink()
            click.echo(click.style("✓ Focus cleared", fg="green"))
        else:
            click.echo(click.style("No active focus to clear", fg="yellow"))
        return

    # Set focus
    if task_id:
        # Validate task exists
        tm = TaskManager(root_dir)
        try:
            task = tm.get(task_id)
        except Exception:
            click.echo(click.style(f"Error: Task {task_id} not found", fg="red"))
            raise click.Abort()

        # Save focus
        focus_data = {
            "task_id": task_id,
            "task_name": task.name,
            "set_at": datetime.now().isoformat(),
        }
        write_yaml(focus_file, focus_data)

        click.echo(click.style("🎯 Focus set!", fg="green", bold=True))
        click.echo(f"  Task: {task_id} - {task.name}")
        click.echo(f"  Priority: {task.priority}")
        click.echo(f"  Status: {task.status}")
        click.echo()
        click.echo(
            click.style(
                "💡 This task will be highlighted in overview/resume commands",
                fg="blue",
            )
        )
        return

    # Show current focus
    if not focus_file.exists():
        click.echo(click.style("No focus task set", fg="yellow"))
        click.echo()
        click.echo("Set a focus task with:")
        click.echo(click.style("  clauxton focus TASK-ID", fg="cyan"))
        return

    # Load and display focus
    focus_data = read_yaml(focus_file)
    focused_task_id = focus_data.get("task_id")
    set_at_str = focus_data.get("set_at", "")

    if not focused_task_id:
        click.echo(click.style("⚠ Invalid focus file", fg="yellow"))
        click.echo("Clear focus with: clauxton focus --clear")
        return

    # Get task details
    tm = TaskManager(root_dir)
    try:
        task = tm.get(focused_task_id)
    except Exception:
        click.echo(
            click.style(
                f"⚠ Focus task {focused_task_id} not found (may have been deleted)",
                fg="yellow",
            )
        )
        click.echo("Clear focus with: clauxton focus --clear")
        return

    # Calculate focus duration
    if set_at_str:
        set_at = datetime.fromisoformat(set_at_str)
        duration = datetime.now() - set_at
        hours = duration.total_seconds() / 3600

        if hours < 1:
            duration_str = f"{int(duration.total_seconds() / 60)} minutes"
        elif hours < 24:
            duration_str = f"{int(hours)} hours"
        else:
            days = int(hours / 24)
            duration_str = f"{days} days"
    else:
        duration_str = "unknown"

    click.echo(click.style("\n🎯 Current Focus\n", fg="green", bold=True))
    click.echo(f"  Task: {task.id} - {task.name}")
    click.echo(f"  Priority: {task.priority}")
    click.echo(f"  Status: {task.status}")
    click.echo(f"  Focused for: {duration_str}")

    if task.description:
        click.echo()
        click.echo(click.style("  Description:", fg="white", dim=True))
        click.echo(f"  {task.description}")

    click.echo()
    click.echo("Commands:")
    click.echo(click.style("  clauxton focus --clear", fg="cyan") + "  Clear focus")
    click.echo(
        click.style("  clauxton task update {} --status in_progress".format(task.id), fg="cyan")
        + "  Start work"
    )
    click.echo()


@cli.command(name="search")
@click.argument("query")
@click.option("--limit", "-l", default=5, help="Results per category (default: 5)")
@click.option("--kb-only", is_flag=True, help="Search Knowledge Base only")
@click.option("--tasks-only", is_flag=True, help="Search Tasks only")
@click.option("--files-only", is_flag=True, help="Search Files (Repository Map) only")
def cross_search(
    query: str, limit: int, kb_only: bool, tasks_only: bool, files_only: bool
) -> None:
    """
    Search across Knowledge Base, Tasks, and Files.

    Cross-searches all project knowledge for quick information retrieval.
    Perfect for finding related information across different sources!

    Examples:
        $ clauxton search "authentication"
        $ clauxton search "API" --limit 10
        $ clauxton search "auth" --kb-only
        $ clauxton search "bug" --tasks-only
    """
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    # Determine what to search
    search_kb = not tasks_only and not files_only
    search_tasks = not kb_only and not files_only
    search_files = not kb_only and not tasks_only

    click.echo(click.style(f"\n🔍 Searching for: {query}\n", fg="cyan", bold=True))

    total_results = 0

    # Search Knowledge Base
    if search_kb:
        kb = KnowledgeBase(root_dir)
        kb_results = kb.search(query, limit=limit)
    else:
        kb_results = []

    if kb_results and search_kb:
        result_count = len(kb_results)
        result_text = f"result{'s' if result_count != 1 else ''}"
        click.echo(
            click.style(
                f"📚 Knowledge Base ({result_count} {result_text}):\n",
                fg="green",
                bold=True,
            )
        )
        icons = {
            "architecture": "🏗️ ",
            "constraint": "⚠️ ",
            "decision": "✅",
            "pattern": "🔧",
            "convention": "📋",
        }
        for entry in kb_results[:limit]:
            icon = icons.get(entry.category, "•")
            click.echo(f"  {icon} {entry.id}: {entry.title} ({entry.category})")
            if entry.content:
                preview = entry.content[:80] + "..." if len(entry.content) > 80 else entry.content
                click.echo(click.style(f"     {preview}", fg="white", dim=True))
        click.echo()
        total_results += len(kb_results)

    # Search Tasks
    if search_tasks:
        tm = TaskManager(root_dir)
        all_tasks = tm.list_all()
        query_lower = query.lower()
        task_results = [
            t
            for t in all_tasks
            if query_lower in t.name.lower()
            or (t.description and query_lower in t.description.lower())
        ]
    else:
        task_results = []

    if task_results and search_tasks:
        click.echo(
            click.style(
                f"📋 Tasks ({len(task_results)} result{'s' if len(task_results) != 1 else ''}):\n",
                fg="yellow",
                bold=True,
            )
        )
        for task in task_results[:limit]:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "blocked": "🚫",
            }.get(task.status, "•")
            click.echo(f"  {status_icon} {task.id}: {task.name} [{task.status}]")
            if task.description:
                desc = task.description
                preview = desc[:80] + "..." if len(desc) > 80 else desc
                click.echo(click.style(f"     {preview}", fg="white", dim=True))
        click.echo()
        total_results += len(task_results)

    # Search Repository Map (if available)
    if search_files:
        repo_map_file = clauxton_dir / "repository_map.json"
        if repo_map_file.exists():
            try:
                from clauxton.intelligence.repository_map import RepositoryMap

                repo_map = RepositoryMap(root_dir)
                symbol_results = repo_map.search(query, search_type="exact", limit=limit)
            except Exception:
                symbol_results = []
        else:
            symbol_results = []
    else:
        symbol_results = []

    if symbol_results and search_files:
        result_count = len(symbol_results)
        result_text = f"result{'s' if result_count != 1 else ''}"
        click.echo(
            click.style(
                f"📁 Files ({result_count} {result_text}):\n",
                fg="blue",
                bold=True,
            )
        )
        for symbol in symbol_results[:limit]:
            symbol_type = f" ({symbol.type})" if symbol.type != "function" else "()"
            location = f"{symbol.file_path}:{symbol.line_start}"
            click.echo(f"  • {location} - {symbol.name}{symbol_type}")
            if symbol.docstring:
                doc = symbol.docstring
                preview = doc[:80] + "..." if len(doc) > 80 else doc
                click.echo(click.style(f"     {preview}", fg="white", dim=True))
        click.echo()
        total_results += len(symbol_results)

    if total_results == 0:
        click.echo(click.style("No results found", fg="yellow"))
        click.echo()
        click.echo("Try:")
        click.echo("  • Using different keywords")
        click.echo("  • Searching individual sources:")
        click.echo(click.style(f"    clauxton kb search '{query}'", fg="cyan"))
        click.echo(click.style(f"    clauxton repo search '{query}'", fg="cyan"))
    else:
        click.echo(click.style(f"Total: {total_results} results\n", fg="cyan", bold=True))


@cli.command()
@click.argument("reason", required=False)
@click.option("--note", "-n", help="Additional notes about current work")
@click.option("--history", is_flag=True, help="Show interruption history and statistics")
def pause(reason: Optional[str], note: Optional[str], history: bool) -> None:
    """
    Pause current work and save context.

    Useful for handling interruptions - saves your current state so you can
    easily resume later. Tracks pause duration and provides context on resume.

    Examples:
        $ clauxton pause "Meeting"
        $ clauxton pause "Urgent issue" --note "Working on user auth bug"
        $ clauxton pause
        $ clauxton pause --history        # Show pause history
    """
    from datetime import datetime

    from clauxton.utils.yaml_utils import read_yaml, write_yaml

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    pause_file = clauxton_dir / "pause.yml"
    focus_file = clauxton_dir / "focus.yml"
    history_file = clauxton_dir / "pause_history.yml"

    # Show history if --history flag is set
    if history:
        if not history_file.exists():
            click.echo(click.style("No pause history yet", fg="yellow"))
            return

        history_data = read_yaml(history_file)
        pauses = history_data.get("pauses", [])

        if not pauses:
            click.echo(click.style("No pause history yet", fg="yellow"))
            return

        click.echo()
        click.echo(click.style("⏸  Pause History & Statistics\n", fg="cyan", bold=True))

        # Calculate statistics
        total_pauses = len(pauses)
        reasons: dict[str, int] = {}
        total_duration_seconds: float = 0.0
        pause_count = 0

        for pause_entry in pauses:
            pause_reason = pause_entry.get("reason", "Unspecified")
            reasons[pause_reason] = reasons.get(pause_reason, 0) + 1

            # Calculate duration if resumed
            if pause_entry.get("resumed_at"):
                paused_at_str = pause_entry.get("paused_at", "")
                resumed_at_str = pause_entry.get("resumed_at", "")
                try:
                    paused_at = datetime.fromisoformat(paused_at_str)
                    resumed_at = datetime.fromisoformat(resumed_at_str)
                    duration = (resumed_at - paused_at).total_seconds()
                    total_duration_seconds += duration
                    pause_count += 1
                except Exception:
                    pass

        # Display statistics
        click.echo(click.style("📊 Summary:", fg="green", bold=True))
        click.echo(f"  Total pauses: {total_pauses}")

        if pause_count > 0:
            avg_duration_minutes = (total_duration_seconds / pause_count) / 60
            total_hours = total_duration_seconds / 3600
            click.echo(f"  Average pause duration: {avg_duration_minutes:.1f} minutes")
            click.echo(f"  Total pause time: {total_hours:.1f} hours")

        click.echo()

        # Most common reasons
        click.echo(click.style("📋 Most Common Reasons:", fg="yellow", bold=True))
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        for pause_reason, count in sorted_reasons[:5]:
            percentage = (count / total_pauses) * 100
            click.echo(f"  • {pause_reason}: {count} ({percentage:.1f}%)")

        click.echo()

        # Recent pauses
        click.echo(click.style("🕐 Recent Pauses (last 5):", fg="magenta", bold=True))
        for pause_entry in reversed(pauses[-5:]):
            paused_at_str = pause_entry.get("paused_at", "")
            pause_reason = pause_entry.get("reason", "Unspecified")
            resumed = pause_entry.get("resumed_at")

            try:
                paused_at = datetime.fromisoformat(paused_at_str)
                date_str = paused_at.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = paused_at_str

            status = "✅" if resumed else "⏸"
            click.echo(f"  {status} {date_str} - {pause_reason}")

        click.echo()
        return

    # Get current focus if any
    focused_task = None
    if focus_file.exists():
        focus_data = read_yaml(focus_file)
        focused_task = focus_data.get("task_id")

    # Save pause state
    pause_data = {
        "paused_at": datetime.now().isoformat(),
        "reason": reason or "Unspecified",
        "note": note,
        "focused_task": focused_task,
    }
    write_yaml(pause_file, pause_data)

    # Save to history
    if history_file.exists():
        history_data = read_yaml(history_file)
    else:
        history_data = {"pauses": []}

    history_data["pauses"].append(pause_data.copy())
    write_yaml(history_file, history_data)

    click.echo(click.style("⏸  Work paused!", fg="yellow", bold=True))
    if reason:
        click.echo(f"  Reason: {reason}")
    if note:
        click.echo(f"  Note: {note}")
    if focused_task:
        click.echo(f"  Focus task: {focused_task}")
    click.echo()
    click.echo(click.style("💡 Run 'clauxton continue' to resume", fg="blue"))
    click.echo()


@cli.command(name="continue")
def continue_work() -> None:
    """
    Continue work after a pause.

    Restores your context and shows how long you were away.
    Perfect for resuming after meetings or interruptions!

    Examples:
        $ clauxton continue
    """
    from datetime import datetime

    from clauxton.core.task_manager import TaskManager
    from clauxton.utils.yaml_utils import read_yaml

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    pause_file = clauxton_dir / "pause.yml"

    if not pause_file.exists():
        click.echo(click.style("⚠ No paused work found", fg="yellow"))
        click.echo()
        click.echo("To pause work, run: clauxton pause \"reason\"")
        return

    # Load pause data
    pause_data = read_yaml(pause_file)
    paused_at_str = pause_data.get("paused_at", "")
    reason = pause_data.get("reason", "Unspecified")
    note = pause_data.get("note")
    focused_task_id = pause_data.get("focused_task")

    # Calculate pause duration
    if paused_at_str:
        paused_at = datetime.fromisoformat(paused_at_str)
        now = datetime.now()
        duration = now - paused_at
        hours = duration.total_seconds() / 3600

        if hours < 1:
            duration_str = f"{int(duration.total_seconds() / 60)} minutes"
        elif hours < 24:
            duration_str = f"{int(hours)} hours"
        else:
            days = int(hours / 24)
            duration_str = f"{days} days"
    else:
        duration_str = "unknown"

    click.echo(click.style("\n▶  Resuming work!\n", fg="green", bold=True))
    click.echo(f"  Paused for: {duration_str}")
    click.echo(f"  Reason: {reason}")
    if note:
        click.echo(f"  Note: {note}")
    click.echo()

    # Show focused task if any
    if focused_task_id:
        try:
            tm = TaskManager(root_dir)
            task = tm.get(focused_task_id)
            click.echo(click.style("📌 You were working on:", fg="cyan", bold=True))
            click.echo(f"  {task.id}: {task.name}")
            click.echo(f"  Priority: {task.priority}")
            click.echo(f"  Status: {task.status}")
            if task.description:
                click.echo(f"  Description: {task.description}")
            click.echo()
        except Exception:
            pass

    # Show current in-progress tasks
    try:
        tm = TaskManager(root_dir)
        in_progress = [t for t in tm.list_all() if t.status == "in_progress"]
        if in_progress:
            click.echo(click.style("🔄 In-progress tasks:", fg="yellow"))
            for task in in_progress[:3]:
                click.echo(f"  • {task.id}: {task.name}")
            click.echo()
    except Exception:
        pass

    # Update history with resume time
    from clauxton.utils.yaml_utils import write_yaml

    history_file = clauxton_dir / "pause_history.yml"
    if history_file.exists():
        history_data = read_yaml(history_file)
        pauses = history_data.get("pauses", [])

        # Find the most recent pause matching this one and update it
        for pause_entry in reversed(pauses):
            if (
                pause_entry.get("paused_at") == paused_at_str
                and not pause_entry.get("resumed_at")
            ):
                pause_entry["resumed_at"] = datetime.now().isoformat()
                write_yaml(history_file, history_data)
                break

    # Clear pause file
    pause_file.unlink()

    click.echo(click.style("💡 Ready to continue!", fg="green"))
    click.echo()


@cli.command()
@click.option(
    "--skip-mcp",
    is_flag=True,
    help="Skip MCP server setup (can run 'clauxton mcp setup' later)",
)
@click.option(
    "--skip-index",
    is_flag=True,
    help="Skip repository indexing (can run 'clauxton repo index' later)",
)
@click.pass_context
def quickstart(ctx: click.Context, skip_mcp: bool, skip_index: bool) -> None:
    """
    Quick setup for new projects (all-in-one initialization).

    This command runs the essential setup steps automatically:
    1. Initialize Clauxton (.clauxton/ directory)
    2. Index your codebase (Repository Map)
    3. Setup MCP server for Claude Code integration

    Perfect for getting started quickly!

    Example:
        $ clauxton quickstart
        $ clauxton quickstart --skip-mcp     # Skip MCP setup
        $ clauxton quickstart --skip-index   # Skip repository indexing
    """
    import sys
    from pathlib import Path

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    click.echo(click.style("\n🚀 Clauxton Quick Start\n", fg="cyan", bold=True))
    click.echo(f"Project: {root_dir.name}")
    click.echo(f"Location: {root_dir}\n")

    # Check if already initialized
    if clauxton_dir.exists():
        click.echo(
            click.style(
                "⚠ Clauxton already initialized in this directory", fg="yellow"
            )
        )
        click.echo("Use individual commands to configure:")
        click.echo(click.style("  clauxton repo index", fg="cyan"))
        click.echo(click.style("  clauxton mcp setup", fg="cyan"))
        click.echo(click.style("  clauxton status", fg="cyan"))
        ctx.exit(0)

    # Step 1: Initialize
    click.echo(click.style("Step 1/3: ", fg="blue", bold=True) + "Initializing Clauxton...")
    try:
        ctx.invoke(init, force=False)
    except Exception as e:
        click.echo(click.style(f"✗ Initialization failed: {e}", fg="red"))
        ctx.exit(1)

    # Step 2: Index repository (optional)
    if not skip_index:
        click.echo(
            click.style("\nStep 2/3: ", fg="blue", bold=True) + "Indexing codebase..."
        )
        try:
            # Import here to avoid circular dependency
            from clauxton.cli.repository import index_command

            # Call index command with current directory
            ctx.invoke(index_command, path=str(root_dir), incremental=False)
        except Exception as e:
            msg = (
                f"⚠ Indexing failed (non-fatal): {e}\n"
                "  You can run 'clauxton repo index' later"
            )
            click.echo(click.style(msg, fg="yellow"))
    else:
        click.echo(click.style("\nStep 2/3: ", fg="blue", bold=True) + "Skipped indexing")
        click.echo("  Run later: clauxton repo index")

    # Step 3: Setup MCP (optional)
    if not skip_mcp:
        click.echo(
            click.style("\nStep 3/3: ", fg="blue", bold=True)
            + "Setting up MCP server for Claude Code..."
        )
        try:
            # Import here to avoid circular dependency
            from clauxton.cli.mcp import setup_command

            # Call mcp setup with defaults
            ctx.invoke(
                setup_command, path=str(root_dir), server_name="clauxton", python=sys.executable
            )
        except Exception as e:
            msg = (
                f"⚠ MCP setup failed (non-fatal): {e}\n"
                "  You can run 'clauxton mcp setup' later"
            )
            click.echo(click.style(msg, fg="yellow"))
    else:
        click.echo(click.style("\nStep 3/3: ", fg="blue", bold=True) + "Skipped MCP setup")
        click.echo("  Run later: clauxton mcp setup")

    # Show final status
    click.echo(click.style("\n✓ Quick Start Complete!\n", fg="green", bold=True))
    click.echo(click.style("📊 Project Status:\n", fg="cyan", bold=True))

    # Invoke status command to show current state
    try:
        ctx.invoke(status)
    except Exception:
        pass  # Status is just informational

    click.echo(click.style("\n💡 Next Steps:", fg="blue", bold=True))
    click.echo("  1. Add knowledge: " + click.style("clauxton kb add", fg="cyan"))
    click.echo("  2. Create tasks: " + click.style("clauxton task add", fg="cyan"))
    click.echo("  3. Check status: " + click.style("clauxton status", fg="cyan"))
    if skip_mcp:
        click.echo(
            "  4. Setup MCP (skipped): " + click.style("clauxton mcp setup", fg="cyan")
        )
    click.echo()


@cli.command()
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing .clauxton directory if it exists",
)
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    """
    Initialize Clauxton in the current directory.

    Creates .clauxton/ directory with:
    - knowledge-base.yml (empty Knowledge Base)
    - tasks.yml (for Phase 1)
    - .gitignore (excludes sensitive files)

    Example:
        $ clauxton init
        $ clauxton init --force  # Overwrite existing
    """
    from clauxton.utils.file_utils import ensure_clauxton_dir, set_secure_directory_permissions
    from clauxton.utils.yaml_utils import write_yaml

    root_dir = Path.cwd()

    # Check if .clauxton already exists
    clauxton_dir = root_dir / ".clauxton"
    if clauxton_dir.exists() and not force:
        click.echo(
            click.style(
                f"Error: .clauxton/ already exists at {root_dir}", fg="red"
            )
        )
        click.echo("Use --force to overwrite")
        ctx.exit(1)

    # Create .clauxton directory
    clauxton_dir = ensure_clauxton_dir(root_dir)
    set_secure_directory_permissions(clauxton_dir)

    # Create knowledge-base.yml
    from typing import Any, Dict

    kb_file = clauxton_dir / "knowledge-base.yml"
    kb_data: Dict[str, Any] = {
        "version": "1.0",
        "project_name": root_dir.name,
        "project_description": None,
        "entries": [],
    }
    write_yaml(kb_file, kb_data, backup=False)

    # Create .gitignore
    gitignore_file = clauxton_dir / ".gitignore"
    gitignore_content = """# Clauxton internal files
*.bak
*.tmp
.DS_Store
"""
    gitignore_file.write_text(gitignore_content)

    click.echo(click.style("✓ Initialized Clauxton", fg="green"))
    click.echo(f"  Location: {clauxton_dir}")
    click.echo(f"  Knowledge Base: {kb_file}")
    click.echo()
    click.echo(click.style("💡 Next Step: Index your codebase for fast symbol search", fg="blue"))
    click.echo(click.style("   clauxton repo index", fg="cyan"))


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=False, path_type=Path),
    help="Path to TUI config file",
)
def tui(config: Optional[Path]) -> None:
    """
    Launch Interactive Terminal UI (v0.14.0+).

    Provides a modern, keyboard-driven interface with AI integration:
    - AI-enhanced dashboard with real-time suggestions
    - Knowledge Base browser with semantic search
    - Code review workflow
    - KB generation from commits
    - Interactive chat with AI

    Keyboard Shortcuts:
    - Ctrl+P: Command palette
    - Ctrl+K: Focus KB browser
    - Ctrl+L: Focus content panel
    - Ctrl+J: Focus AI suggestions
    - Ctrl+T: Toggle theme
    - Q: Quit
    - ?: Help

    Example:
        $ clauxton tui
        $ clauxton tui --config ~/.clauxton/custom-tui.yml

    Note: Requires 'textual' package. Install with:
        $ pip install clauxton[tui]
    """
    try:
        from clauxton.tui.app import run_tui
    except ImportError:
        click.echo(
            click.style(
                "❌ TUI requires 'textual' package. Install with:",
                fg="red",
            )
        )
        click.echo(click.style("   pip install clauxton[tui]", fg="cyan"))
        click.echo()
        raise click.Abort()

    root_dir = Path.cwd()
    clauxton_dir = root_dir / ".clauxton"

    if not clauxton_dir.exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    # Launch TUI
    click.echo(click.style("🚀 Launching Clauxton TUI...", fg="cyan"))
    click.echo()

    try:
        run_tui(project_root=root_dir, config_path=config)
    except KeyboardInterrupt:
        click.echo("\n" + click.style("👋 Bye!", fg="cyan"))
    except Exception as e:
        click.echo(click.style(f"\n❌ TUI crashed: {e}", fg="red"))
        click.echo()
        click.echo(click.style("Check log file:", fg="yellow"))
        click.echo(click.style(f"   {clauxton_dir / 'tui.log'}", fg="cyan"))
        raise


@cli.group()
def kb() -> None:
    """
    Knowledge Base commands.

    Manage project context with:
    - add: Add new entry
    - get: Get entry by ID
    - list: List all entries
    - search: Search entries
    - update: Update entry (Phase 1)
    - delete: Delete entry (Phase 1)
    """
    pass


@kb.command()
@click.option("--title", prompt="Title", help="Entry title (max 50 chars)")
@click.option(
    "--category",
    prompt="Category",
    type=click.Choice(
        ["architecture", "constraint", "decision", "pattern", "convention"]
    ),
    help="Entry category",
)
@click.option("--content", prompt="Content", help="Entry content (max 10000 chars)")
@click.option(
    "--tags",
    help="Comma-separated tags (e.g., 'api,backend,fastapi')",
    default="",
)
def add(title: str, category: str, content: str, tags: str) -> None:
    """
    Add new entry to Knowledge Base.

    Example:
        $ clauxton kb add
        Title: Use FastAPI framework
        Category: architecture
        Content: All backend APIs use FastAPI...
        Tags (optional): backend,api,fastapi
    """
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    # Create Knowledge Base instance
    kb_instance = KnowledgeBase(root_dir)

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Generate ID
    entry_id = kb_instance._generate_id()

    # Create entry
    from typing import Literal, cast

    now = datetime.now()
    entry = KnowledgeBaseEntry(
        id=entry_id,
        title=title,
        category=cast(
            Literal["architecture", "constraint", "decision", "pattern", "convention"],
            category,
        ),
        content=content,
        tags=tag_list,
        created_at=now,
        updated_at=now,
        author=None,
    )

    # Add to Knowledge Base
    try:
        kb_instance.add(entry)

        # Record operation to history for undo support
        from clauxton.core.operation_history import Operation, OperationHistory, OperationType

        history = OperationHistory(root_dir)
        operation = Operation(
            operation_type=OperationType.KB_ADD,
            operation_data={"entry_id": entry_id},
            description=f"Added KB entry: {title}"
        )
        history.record(operation)

        click.echo(click.style(f"✓ Added entry: {entry_id}", fg="green"))
        click.echo(f"  Title: {title}")
        click.echo(f"  Category: {category}")
        click.echo(f"  Tags: {', '.join(tag_list) if tag_list else '(none)'}")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@kb.command()
@click.argument("entry_id")
def get(entry_id: str) -> None:
    """
    Get entry by ID.

    Example:
        $ clauxton kb get KB-20251019-001
    """
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import NotFoundError

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    kb_instance = KnowledgeBase(root_dir)

    try:
        entry = kb_instance.get(entry_id)

        # Display entry
        click.echo(click.style(f"\n{entry.id}", fg="cyan", bold=True))
        click.echo(click.style(f"Title: {entry.title}", bold=True))
        click.echo(f"Category: {entry.category}")
        click.echo(f"Tags: {', '.join(entry.tags) if entry.tags else '(none)'}")
        click.echo(f"Version: {entry.version}")
        click.echo(f"Created: {entry.created_at}")
        click.echo(f"Updated: {entry.updated_at}")
        click.echo(f"\n{entry.content}\n")
    except NotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@kb.command("list")
@click.option(
    "--category",
    type=click.Choice(
        ["architecture", "constraint", "decision", "pattern", "convention"]
    ),
    help="Filter by category",
)
def list_entries(category: Optional[str]) -> None:
    """
    List all Knowledge Base entries.

    Example:
        $ clauxton kb list
        $ clauxton kb list --category architecture
    """
    from clauxton.core.knowledge_base import KnowledgeBase

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    kb_instance = KnowledgeBase(root_dir)
    entries = kb_instance.list_all()

    # Filter by category if specified
    if category:
        entries = [e for e in entries if e.category == category]

    if not entries:
        if category:
            click.echo(f"No entries found with category '{category}'")
        else:
            click.echo("No entries found")
        click.echo("Use 'clauxton kb add' to add an entry")
        return

    # Display entries
    click.echo(click.style(f"\nKnowledge Base Entries ({len(entries)}):\n", bold=True))

    for entry in entries:
        click.echo(click.style(f"  {entry.id}", fg="cyan"))
        click.echo(f"    Title: {entry.title}")
        click.echo(f"    Category: {entry.category}")
        if entry.tags:
            click.echo(f"    Tags: {', '.join(entry.tags)}")
        click.echo()


@kb.command()
@click.argument("query")
@click.option(
    "--category",
    type=click.Choice(
        ["architecture", "constraint", "decision", "pattern", "convention"]
    ),
    help="Filter by category",
)
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--limit", default=10, help="Maximum number of results (default: 10)")
def search(query: str, category: Optional[str], tags: Optional[str], limit: int) -> None:
    """
    Search Knowledge Base entries.

    Searches in title, content, and tags.

    Example:
        $ clauxton kb search "API"
        $ clauxton kb search "FastAPI" --category architecture
        $ clauxton kb search "database" --tags backend,postgresql
    """
    from clauxton.core.knowledge_base import KnowledgeBase

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    kb_instance = KnowledgeBase(root_dir)

    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Search
    results = kb_instance.search(query, category=category, tags=tag_list, limit=limit)

    if not results:
        click.echo(f"No results found for '{query}'")
        return

    # Display results
    click.echo(
        click.style(f"\nSearch Results for '{query}' ({len(results)}):\n", bold=True)
    )

    for entry in results:
        click.echo(click.style(f"  {entry.id}", fg="cyan"))
        click.echo(f"    Title: {entry.title}")
        click.echo(f"    Category: {entry.category}")
        if entry.tags:
            click.echo(f"    Tags: {', '.join(entry.tags)}")
        # Show first 100 chars of content
        content_preview = (
            entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
        )
        click.echo(f"    Preview: {content_preview}")
        click.echo()


@kb.command()
@click.argument("entry_id")
@click.option("--title", help="New title")
@click.option("--content", help="New content")
@click.option(
    "--category",
    type=click.Choice(["architecture", "constraint", "decision", "pattern", "convention"]),
    help="New category",
)
@click.option("--tags", help="New tags (comma-separated)")
def update(
    entry_id: str,
    title: Optional[str],
    content: Optional[str],
    category: Optional[str],
    tags: Optional[str],
) -> None:
    """
    Update an existing Knowledge Base entry.

    Example:
        $ clauxton kb update KB-20251019-001 --title "New title"
        $ clauxton kb update KB-20251019-001 --content "New content"
        $ clauxton kb update KB-20251019-001 --tags "api,backend,updated"
    """
    from clauxton.core.knowledge_base import KnowledgeBase

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    kb_instance = KnowledgeBase(root_dir)

    # Prepare updates
    updates: dict[str, Any] = {}
    if title:
        updates["title"] = title
    if content:
        updates["content"] = content
    if category:
        updates["category"] = category
    if tags:
        updates["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

    if not updates:
        click.echo(click.style("Error: No fields to update", fg="yellow"))
        click.echo("Use --title, --content, --category, or --tags")
        return

    try:
        updated_entry = kb_instance.update(entry_id, updates)
        click.echo(click.style(f"✓ Updated entry: {entry_id}", fg="green"))
        click.echo(f"  Title: {updated_entry.title}")
        click.echo(f"  Version: {updated_entry.version}")
        click.echo(f"  Updated: {updated_entry.updated_at.strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@kb.command()
@click.argument("entry_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete(entry_id: str, yes: bool) -> None:
    """
    Delete a Knowledge Base entry.

    Example:
        $ clauxton kb delete KB-20251019-001
        $ clauxton kb delete KB-20251019-001 --yes
    """
    from clauxton.core.knowledge_base import KnowledgeBase

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    kb_instance = KnowledgeBase(root_dir)

    try:
        entry = kb_instance.get(entry_id)

        if not yes:
            click.echo(f"Delete entry: {entry.title} ({entry_id})?")
            if not click.confirm("Are you sure?"):
                click.echo("Cancelled")
                return

        kb_instance.delete(entry_id)
        click.echo(click.style(f"✓ Deleted entry: {entry_id}", fg="green"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@kb.command()
@click.argument("output_dir", type=click.Path())
@click.option(
    "--category",
    "-c",
    type=click.Choice(["architecture", "constraint", "decision", "pattern", "convention"]),
    help="Export only entries from this category",
)
@click.option(
    "--summary",
    "-s",
    is_flag=True,
    help="Export as compact summary (one file, perfect for team onboarding)",
)
def export(output_dir: str, category: Optional[str], summary: bool) -> None:
    """
    Export Knowledge Base entries to Markdown documentation files.

    Creates one Markdown file per category (or a single file if category specified).
    Decision entries use ADR (Architecture Decision Record) format.
    Other categories use standard documentation format.

    Use --summary for a compact overview perfect for team onboarding.

    Examples:
        $ clauxton kb export ./docs/kb                    # Export all categories
        $ clauxton kb export ./docs/adr --category decision  # Export only decisions
        $ clauxton kb export ~/project-docs/kb -c architecture
        $ clauxton kb export ./docs/kb --summary          # Export compact summary
    """
    from typing import Dict, List

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry, NotFoundError, ValidationError

    root_dir = Path.cwd()

    # Check if .clauxton exists
    if not (root_dir / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    kb_instance = KnowledgeBase(root_dir)
    output_path = Path(output_dir)

    try:
        # Handle summary export
        if summary:
            # Get all entries
            entries = kb_instance.list_all()

            if category:
                entries = [e for e in entries if e.category == category]

            if not entries:
                click.echo(click.style("⚠ No entries to export", fg="yellow"))
                raise click.Abort()

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Group by category
            by_category: Dict[str, List[KnowledgeBaseEntry]] = {}
            for entry in entries:
                cat = entry.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(entry)

            # Build summary content
            lines = []
            lines.append(f"# {root_dir.name} - Knowledge Base Summary\n")
            lines.append(f"**Total Entries**: {len(entries)}\n")
            lines.append(
                f"**Categories**: {', '.join(sorted(by_category.keys()))}\n"
            )
            lines.append(
                f"**Generated**: {Path.cwd().name} project\n\n"
            )

            lines.append("---\n\n")

            # Category icons
            icons = {
                "architecture": "🏗️ ",
                "constraint": "⚠️ ",
                "decision": "✅",
                "pattern": "🔧",
                "convention": "📋",
            }

            # Add each category
            for cat_name in [
                "architecture",
                "constraint",
                "decision",
                "pattern",
                "convention",
            ]:
                if cat_name not in by_category:
                    continue

                cat_entries = by_category[cat_name]
                icon = icons.get(cat_name, "•")

                lines.append(f"## {icon} {cat_name.capitalize()} ({len(cat_entries)})\n\n")

                for entry in cat_entries:
                    lines.append(f"### {entry.title}\n\n")

                    # Show ID and tags
                    lines.append(f"**ID**: `{entry.id}`")
                    if entry.tags:
                        lines.append(f" | **Tags**: {', '.join(f'`{t}`' for t in entry.tags)}")
                    lines.append("\n\n")

                    # Show content preview (first 200 chars)
                    if entry.content:
                        preview = (
                            entry.content[:200] + "..."
                            if len(entry.content) > 200
                            else entry.content
                        )
                        lines.append(f"{preview}\n\n")

                    lines.append("---\n\n")

            # Write summary file
            summary_file = output_path / "SUMMARY.md"
            summary_file.write_text("".join(lines), encoding="utf-8")

            # Display success
            click.echo(click.style("✓ Summary export successful!", fg="green"))
            click.echo(f"Output file: {summary_file.absolute()}")
            click.echo(f"Total entries: {len(entries)}")
            click.echo(f"Categories: {', '.join(sorted(by_category.keys()))}")
            click.echo(
                click.style(
                    "\n💡 Perfect for team onboarding and quick reference!",
                    fg="blue",
                )
            )

        else:
            # Regular export to markdown
            stats = kb_instance.export_to_markdown(output_path, category=category)

            # Display success message
            click.echo(click.style("✓ Export successful!", fg="green"))
            click.echo(f"Output directory: {output_path.absolute()}")
            click.echo(f"Total entries: {stats['total_entries']}")
            click.echo(f"Files created: {stats['files_created']}")
            click.echo(f"Categories: {', '.join(stats['categories'])}")

            # List created files
            click.echo("\nCreated files:")
            for cat in stats["categories"]:
                file_path = output_path / f"{cat}.md"
                click.echo(f"  - {file_path}")

            # Show tip for decisions
            if "decision" in stats["categories"]:
                click.echo(
                    click.style(
                        "\nℹ Decision entries exported in ADR format",
                        fg="blue",
                    )
                )

    except NotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()
    except ValidationError as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@kb.command()
def templates() -> None:
    """
    Show KB entry templates and examples.

    Displays helpful templates for common KB entry types to guide content creation.
    Use these as reference when creating new entries with 'clauxton kb add'.

    Examples:
        $ clauxton kb templates              # List all templates
    """
    from typing import Any, Dict, List

    click.echo(click.style("\n📋 Knowledge Base Templates\n", fg="cyan", bold=True))

    templates_list: List[Dict[str, Any]] = [
        {
            "name": "API Endpoint",
            "category": "architecture",
            "tags": ["api", "backend"],
            "example":  (
                "Endpoint: POST /api/users\n"
                "Purpose: Create new user account\n"
                "Request: {email, password, name}\n"
                "Response: {id, email, name, created_at}\n"
                "Authentication: Bearer token required"
            )
        },
        {
            "name": "Database Schema",
            "category": "architecture",
            "tags": ["database", "schema"],
            "example": (
                "Table: users\n"
                "Columns:\n"
                "  - id: UUID, primary key\n"
                "  - email: VARCHAR(255), unique\n"
                "  - created_at: TIMESTAMP\n"
                "Indexes: email\n"
                "Relations: has_many tasks"
            )
        },
        {
            "name": "Code Pattern",
            "category": "pattern",
            "tags": ["code", "pattern"],
            "example": (
                "Pattern: Repository Pattern\n"
                "Purpose: Separate data access logic\n"
                "Implementation:\n"
                "  class UserRepository:\n"
                "    def find_by_id(user_id): ...\n"
                "    def save(user): ...\n"
                "Benefits: Testability, decoupling"
            )
        },
        {
            "name": "External Dependency",
            "category": "decision",
            "tags": ["dependency", "library"],
            "example": (
                "Library: FastAPI\n"
                "Version: ^0.104.0\n"
                "Purpose: Web framework for async APIs\n"
                "Chosen because: Type hints, async support, auto docs\n"
                "Alternatives considered: Flask, Django"
            )
        },
        {
            "name": "Project Constraint",
            "category": "constraint",
            "tags": ["limit", "requirement"],
            "example": (
                "Constraint: Maximum response time\n"
                "Limit: 200ms for API endpoints\n"
                "Reason: User experience requirement\n"
                "Impact: Requires caching, optimized queries\n"
                "Monitoring: Track via APM tools"
            )
        },
        {
            "name": "Coding Convention",
            "category": "convention",
            "tags": ["style", "code"],
            "example": (
                "Convention: Naming style\n"
                "Functions: snake_case\n"
                "Classes: PascalCase\n"
                "Constants: UPPER_SNAKE_CASE\n"
                "Reason: PEP 8 compliance\n"
                "Enforcement: Configured in ruff/mypy"
            )
        },
    ]

    for i, template in enumerate(templates_list, 1):
        icon = {
            "architecture": "🏗️ ",
            "decision": "✅",
            "pattern": "🔧",
            "constraint": "⚠️ ",
            "convention": "📋",
        }.get(template["category"], "•")

        click.echo(
            click.style(f"{i}. {icon} {template['name']}", fg="green", bold=True)
        )
        click.echo(f"   Category: {template['category']}")
        click.echo(f"   Suggested tags: {', '.join(template['tags'])}")
        click.echo()
        click.echo(click.style("   Example content:", fg="white", dim=True))
        for line in template["example"].split("\n"):
            click.echo(click.style(f"   {line}", fg="white", dim=True))
        click.echo()

    click.echo(click.style("💡 Usage Tips:\n", fg="blue", bold=True))
    click.echo("  • Copy/adapt these templates when creating entries")
    click.echo("  • Use 'clauxton kb add' to create new entries")
    click.echo("  • Templates are guidelines - customize as needed!")
    click.echo()


# Quick Add Shortcuts - makes daily usage faster
def _create_kb_shortcut(category: str, icon: str) -> Any:
    """Helper to create KB category shortcut commands."""

    @cli.command(name=f"add-{category}")
    @click.argument("title")
    @click.argument("content")
    @click.option("--tags", help="Comma-separated tags")
    def shortcut_cmd(title: str, content: str, tags: Optional[str]) -> None:
        f"""
        Quick add {category} entry.

        Faster than 'clauxton kb add' - no interactive prompts needed!

        Example:
            $ clauxton add-{category} "My Title" "Description here"
            $ clauxton add-{category} "My Title" "Description" --tags tag1,tag2
        """
        from datetime import datetime

        from clauxton.core.knowledge_base import KnowledgeBase
        from clauxton.core.models import KnowledgeBaseEntry

        root_dir = Path.cwd()

        if not (root_dir / ".clauxton").exists():
            click.echo(
                click.style(
                    "⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"
                )
            )
            raise click.Abort()

        kb = KnowledgeBase(root_dir)

        # Create entry with generated ID
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=kb._generate_id(),  # Generate ID before creating entry
            title=title,
            category=category,  # type: ignore[arg-type]
            content=content,
            tags=[t.strip() for t in tags.split(",")] if tags else [],
            created_at=now,
            updated_at=now,
            author=None,
        )

        try:
            entry_id = kb.add(entry)
            click.echo(click.style(f"{icon} Added {category}:", fg="green"))
            click.echo(f"  ID: {entry_id}")
            click.echo(f"  Title: {title}")
            if tags:
                click.echo(f"  Tags: {tags}")
        except Exception as e:
            click.echo(click.style(f"Error: {e}", fg="red"))
            raise click.Abort()

    return shortcut_cmd


# Create KB shortcuts for each category
_arch_cmd = _create_kb_shortcut("architecture", "🏗️ ")
_decision_cmd = _create_kb_shortcut("decision", "✅")
_constraint_cmd = _create_kb_shortcut("constraint", "⚠️ ")
_pattern_cmd = _create_kb_shortcut("pattern", "🔧")
_convention_cmd = _create_kb_shortcut("convention", "📋")


# Quick task creation
@cli.command(name="quick-task")
@click.argument("name")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["critical", "high", "medium", "low"]),
    default="medium",
    help="Task priority (default: medium)",
)
@click.option("--high", is_flag=True, help="Shortcut for --priority high")
@click.option("--critical", is_flag=True, help="Shortcut for --priority critical")
def quick_task(
    name: str, priority: str, high: bool, critical: bool
) -> None:
    """
    Quick add task.

    Faster than 'clauxton task add' - no interactive prompts!

    Examples:
        $ clauxton quick-task "Setup backend"
        $ clauxton quick-task "Fix bug" --high
        $ clauxton quick-task "Security patch" --critical
    """
    from datetime import datetime

    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager

    root_dir = Path.cwd()

    if not (root_dir / ".clauxton").exists():
        click.echo(
            click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red")
        )
        raise click.Abort()

    # Handle priority shortcuts
    if critical:
        priority = "critical"
    elif high:
        priority = "high"

    tm = TaskManager(root_dir)

    # Create task with generated ID
    task = Task(
        id=tm.generate_task_id(),  # Generate ID before creating task
        name=name,
        priority=priority,  # type: ignore[arg-type]
        created_at=datetime.now(),
        description=None,
        estimated_hours=None,
        actual_hours=None,
        started_at=None,
        completed_at=None,
    )

    try:
        task_id = tm.add(task)
        icon = (
            "🔴" if priority == "critical"
            else "🟠" if priority == "high"
            else "🟡" if priority == "medium"
            else "🟢"
        )
        click.echo(click.style(f"{icon} Added task:", fg="green"))
        click.echo(f"  ID: {task_id}")
        click.echo(f"  Name: {name}")
        click.echo(f"  Priority: {priority}")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


# ============================================================================
# Task Management Commands (Phase 1)
# ============================================================================

from clauxton.cli.tasks import task  # noqa: E402

cli.add_command(task)


# ============================================================================
# Conflict Detection Commands (Phase 2)
# ============================================================================

from clauxton.cli.conflicts import conflict  # noqa: E402

cli.add_command(conflict)


# ============================================================================
# Configuration Commands (v0.10.0)
# ============================================================================

from clauxton.cli.config import config  # noqa: E402

cli.add_command(config)


# ============================================================================
# Repository Map Commands (v0.11.0)
# ============================================================================

from clauxton.cli.repository import repo_group  # noqa: E402

cli.add_command(repo_group)


# ============================================================================
# MCP Server Configuration Commands (v0.11.0)
# ============================================================================

from clauxton.cli.mcp import mcp_group  # noqa: E402

cli.add_command(mcp_group)


# ============================================================================
# Memory Management Commands (v0.15.0)
# ============================================================================

from clauxton.cli.memory import memory  # noqa: E402

cli.add_command(memory)


# ============================================================================
# Migration Commands (v0.15.0)
# ============================================================================

from clauxton.cli.migrate import migrate  # noqa: E402

cli.add_command(migrate)


# ============================================================================
# Undo Commands
# ============================================================================


@cli.command()
@click.option(
    "--history",
    "-h",
    is_flag=True,
    help="Show operation history instead of undoing",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Number of operations to show in history (default: 10)",
)
def undo(history: bool, limit: int) -> None:
    """
    Undo the last operation or show operation history.

    Examples:
        $ clauxton undo                # Undo last operation
        $ clauxton undo --history      # Show operation history
        $ clauxton undo -h -l 20       # Show last 20 operations
    """
    from clauxton.core.operation_history import OperationHistory

    root_dir = Path.cwd()
    op_history = OperationHistory(root_dir)

    try:
        if history:
            # Show operation history
            operations = op_history.list_operations(limit=limit)

            if not operations:
                click.echo("No operations in history")
                return

            click.echo(
                click.style(f"\n📜 Operation History (last {len(operations)}):\n", bold=True)
            )

            for i, op in enumerate(operations, start=1):
                click.echo(
                    f"{i}. [{op.operation_type}] {op.description}\n"
                    f"   Timestamp: {op.timestamp}"
                )
                if i < len(operations):
                    click.echo()

            click.echo(
                click.style(
                    "\nTo undo the last operation, run: clauxton undo",
                    fg="cyan",
                )
            )

        else:
            # Undo last operation
            last_op = op_history.get_last_operation()

            if not last_op:
                click.echo(click.style("No operations to undo", fg="yellow"))
                return

            # Show what will be undone
            click.echo(
                click.style("\n🔄 Undoing last operation:\n", bold=True)
            )
            click.echo(f"Operation: {last_op.operation_type}")
            click.echo(f"Description: {last_op.description}")
            click.echo(f"Timestamp: {last_op.timestamp}\n")

            # Confirm
            if not click.confirm("Are you sure you want to undo this operation?"):
                click.echo("Cancelled")
                return

            # Perform undo
            result = op_history.undo_last_operation()

            if result["status"] == "success":
                click.echo(
                    click.style(f"\n✓ {result['message']}", fg="green")
                )
            else:
                click.echo(
                    click.style(f"\n✗ Undo failed: {result['message']}", fg="red")
                )
                if result.get("error"):
                    click.echo(click.style(f"Error: {result['error']}", fg="red"))
                raise click.Abort()

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@cli.command()
@click.option(
    "--limit",
    "-l",
    default=100,
    help="Maximum number of log entries to display (default: 100)",
)
@click.option(
    "--operation",
    "-o",
    help="Filter by operation type (e.g., task_add, kb_search)",
)
@click.option(
    "--level",
    help="Filter by log level (debug, info, warning, error)",
)
@click.option(
    "--days",
    "-d",
    default=7,
    help="Number of days to look back (default: 7)",
)
@click.option(
    "--date",
    help="Show logs for specific date (YYYY-MM-DD format)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output logs in JSON format",
)
@click.pass_context
def logs(
    ctx: click.Context,
    limit: int,
    operation: Optional[str],
    level: Optional[str],
    days: int,
    date: Optional[str],
    output_json: bool,
) -> None:
    """
    View Clauxton operation logs.

    Shows recent operations performed by Clauxton, including task
    management, KB operations, and other activities.

    Examples:
        $ clauxton logs                              # Last 100 entries, 7 days
        $ clauxton logs --limit 20                   # Last 20 entries
        $ clauxton logs --operation task_add         # Only task_add operations
        $ clauxton logs --level error                # Only errors
        $ clauxton logs --days 30                    # Last 30 days
        $ clauxton logs --date 2025-10-21            # Specific date
        $ clauxton logs --json                       # JSON format output
    """
    import json

    from clauxton.utils.logger import ClauxtonLogger

    try:
        logger = ClauxtonLogger(Path.cwd())

        # Get logs
        if date:
            # Specific date
            log_entries = logger.get_logs_by_date(date)
            # Apply filters
            if operation:
                log_entries = [
                    e for e in log_entries if e.get("operation") == operation
                ]
            if level:
                log_entries = [
                    e for e in log_entries if e.get("level") == level.lower()
                ]
            # Apply limit
            log_entries = log_entries[-limit:]
        else:
            # Recent logs
            log_entries = logger.get_recent_logs(
                limit=limit,
                operation=operation,
                level=level,
                days=days,
            )

        # Output
        if output_json:
            # JSON format
            click.echo(json.dumps(log_entries, indent=2, ensure_ascii=False))
        else:
            # Human-readable format
            if not log_entries:
                click.echo(click.style("No logs found.", fg="yellow"))
                return

            click.echo(
                click.style(
                    f"\n📋 Showing {len(log_entries)} log entries:\n",
                    bold=True,
                )
            )

            for entry in log_entries:
                # Color by level
                level_color = {
                    "debug": "cyan",
                    "info": "green",
                    "warning": "yellow",
                    "error": "red",
                }.get(entry.get("level", "info"), "white")

                # Format timestamp
                timestamp = entry.get("timestamp", "")
                if "T" in timestamp:
                    timestamp = timestamp.replace("T", " ")[:19]

                # Format operation
                op = entry.get("operation", "unknown")
                level_str = entry.get("level", "info").upper()
                message = entry.get("message", "")

                # Output line
                click.echo(
                    click.style(f"[{timestamp}] ", fg="white", dim=True)
                    + click.style(f"{level_str:<8}", fg=level_color, bold=True)
                    + click.style(f"{op:<20}", fg="blue")
                    + click.style(message, fg="white")
                )

                # Show metadata if present
                metadata = entry.get("metadata", {})
                if metadata:
                    for key, value in metadata.items():
                        click.echo(
                            click.style(f"  └─ {key}: ", fg="white", dim=True)
                            + click.style(str(value), fg="cyan")
                        )

            click.echo("")  # Blank line

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


if __name__ == "__main__":
    cli()
