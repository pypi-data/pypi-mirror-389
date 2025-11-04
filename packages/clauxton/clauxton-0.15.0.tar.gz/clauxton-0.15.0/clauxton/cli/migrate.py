"""
CLI commands for Clauxton v0.15.0 migration.

Provides commands to migrate Knowledge Base and Task data to the
new unified Memory System format.

Commands:
    - clauxton migrate memory: Migrate KB and Tasks to Memory
    - clauxton migrate rollback: Rollback migration from backup

Example:
    $ clauxton migrate memory --dry-run
    $ clauxton migrate memory --confirm
    $ clauxton migrate rollback /path/to/backup
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from clauxton.utils.migrate_to_memory import MemoryMigrator, MigrationError

console = Console()


@click.group()
def migrate() -> None:
    """Migration commands for v0.15.0 Unified Memory Model."""
    pass


@migrate.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview migration without writing changes",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Execute migration (creates backup automatically)",
)
def memory(dry_run: bool, confirm: bool) -> None:
    """
    Migrate KB and Tasks to Memory format.

    This command migrates existing Knowledge Base entries and Tasks to
    the new unified Memory System format. A backup is created automatically
    before migration (unless in dry-run mode).

    Examples:
        # Preview migration
        $ clauxton migrate memory --dry-run

        # Execute migration
        $ clauxton migrate memory --confirm

    Notes:
        - Backup is created automatically in .clauxton/backups/
        - Legacy IDs are preserved for backward compatibility
        - Use rollback command if migration fails
    """
    if not dry_run and not confirm:
        console.print(
            Panel(
                "[yellow]Please use --dry-run to preview or --confirm to execute[/yellow]\n\n"
                "Examples:\n"
                "  [cyan]clauxton migrate memory --dry-run[/cyan]     # Preview migration\n"
                "  [cyan]clauxton migrate memory --confirm[/cyan]     # Execute migration",
                title="Migration Mode Required",
                border_style="yellow",
            )
        )
        return

    project_root = Path.cwd()
    migrator = MemoryMigrator(project_root, dry_run=dry_run)

    try:
        if dry_run:
            console.print(
                Panel(
                    "[bold cyan]Migration Preview (Dry Run)[/bold cyan]\n"
                    "No changes will be written to disk",
                    border_style="cyan",
                )
            )
        else:
            console.print(
                Panel(
                    "[bold green]Starting Migration...[/bold green]\n"
                    "A backup will be created automatically",
                    border_style="green",
                )
            )

        # Perform migration
        with console.status(
            "[bold blue]Migrating data..." if not dry_run else "[bold cyan]Analyzing data...",
            spinner="dots",
        ):
            result = migrator.migrate_all()

        # Display results
        table = Table(title="Migration Results", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Count", style="magenta", width=10, justify="right")

        table.add_row("Knowledge Base", str(result["kb_count"]))
        table.add_row("Tasks", str(result["task_count"]))
        table.add_row("", "")  # Separator
        table.add_row("[bold]Total[/bold]", f"[bold]{result['total']}[/bold]")

        console.print()
        console.print(table)
        console.print()

        if dry_run:
            console.print(
                Panel(
                    "[green]Dry run complete. Use --confirm to execute migration.[/green]",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "[bold green]Migration complete![/bold green]\n\n"
                    "Your Knowledge Base and Tasks have been migrated to the Memory System.\n\n"
                    "Next steps:\n"
                    "  1. Verify your data: [cyan]clauxton memory list[/cyan]\n"
                    "  2. If something went wrong, rollback:\n"
                    "     [cyan]clauxton migrate rollback <backup_path>[/cyan]\n"
                    "  3. Continue using Clauxton with the unified Memory System!",
                    title="Success",
                    border_style="green",
                )
            )

    except MigrationError as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Migration failed:[/bold red]\n\n{str(e)}\n\n"
                "Your original data is safe. Check the error message above.",
                title="Error",
                border_style="red",
            )
        )
        raise click.Abort()
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Unexpected error:[/bold red]\n\n{str(e)}\n\n"
                "Please report this issue on GitHub.",
                title="Error",
                border_style="red",
            )
        )
        raise click.Abort()


@migrate.command()
@click.argument("backup_path", type=click.Path(exists=True, path_type=Path))
def rollback(backup_path: Path) -> None:
    """
    Rollback migration from backup.

    Restores Knowledge Base and Task files from a backup created during migration.
    Use this if migration fails or produces unexpected results.

    Args:
        backup_path: Path to backup directory
            (e.g., .clauxton/backups/pre_migration_20260127_143052)

    Examples:
        # List available backups
        $ ls .clauxton/backups/

        # Rollback from backup
        $ clauxton migrate rollback .clauxton/backups/pre_migration_20260127_143052

    Notes:
        - This will overwrite current files with backup files
        - Make sure to specify the correct backup directory
    """
    project_root = Path.cwd()
    migrator = MemoryMigrator(project_root)

    try:
        console.print(
            Panel(
                f"[bold yellow]Rolling back from backup:[/bold yellow]\n\n{backup_path}\n\n"
                "This will restore your files from the backup.",
                title="Rollback Confirmation",
                border_style="yellow",
            )
        )

        # Ask for confirmation
        if not click.confirm("Do you want to proceed with rollback?"):
            console.print("[yellow]Rollback cancelled[/yellow]")
            return

        with console.status("[bold blue]Rolling back...", spinner="dots"):
            migrator.rollback(backup_path)

        console.print()
        console.print(
            Panel(
                "[bold green]Rollback complete![/bold green]\n\n"
                "Your files have been restored from the backup.",
                title="Success",
                border_style="green",
            )
        )

    except MigrationError as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Rollback failed:[/bold red]\n\n{str(e)}",
                title="Error",
                border_style="red",
            )
        )
        raise click.Abort()
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Unexpected error:[/bold red]\n\n{str(e)}",
                title="Error",
                border_style="red",
            )
        )
        raise click.Abort()
