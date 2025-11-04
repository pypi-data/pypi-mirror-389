"""CLI commands for Repository Map feature."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from clauxton.intelligence.repository_map import RepositoryMap, RepositoryMapError

console = Console()


@click.group(name="repo")
def repo_group() -> None:
    """Repository Map commands for codebase indexing and search."""
    pass


@repo_group.command(name="index")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    help="Path to project root (default: current directory)",
)
@click.option(
    "--incremental",
    is_flag=True,
    help="Perform incremental indexing (only changed files)",
)
def index_command(path: str, incremental: bool) -> None:
    """
    Index codebase for fast symbol search.

    This command scans all files in the project, extracts symbols
    (functions, classes, methods), and creates an index for fast searching.

    Example:
        clauxton repo index
        clauxton repo index --path /path/to/project
    """
    try:
        project_path = Path(path)
        console.print(f"[blue]Indexing codebase at:[/blue] {project_path}")

        repo_map = RepositoryMap(project_path)

        # Progress tracking
        import time
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Indexing files...", total=None)

            def progress_callback(current: int, total: Optional[int], status: str) -> None:
                description = f"Indexing: {status}"

                # Add estimated time if we have total and have processed some files
                if total and current > 0:
                    elapsed = time.time() - start_time
                    files_per_sec = current / elapsed if elapsed > 0 else 0

                    if files_per_sec > 0:
                        remaining_files = total - current
                        estimated_seconds = remaining_files / files_per_sec

                        # Format estimated time
                        if estimated_seconds < 60:
                            time_str = f"{int(estimated_seconds)}s"
                        else:
                            minutes = int(estimated_seconds / 60)
                            time_str = f"{minutes}m {int(estimated_seconds % 60)}s"

                        description += f" [dim](~{time_str} remaining)[/dim]"

                progress.update(task, description=description)

            result = repo_map.index(
                incremental=incremental,
                progress_callback=progress_callback
            )

        # Display results
        console.print("\n[green]✓ Indexing complete![/green]")
        console.print(f"  • Files indexed: {result.files_indexed}")
        console.print(f"  • Symbols found: {result.symbols_found}")
        console.print(f"  • Duration: {result.duration_seconds:.2f}s")

        # Display missing parser warnings
        if result.missing_parsers:
            console.print("\n[yellow]⚠ Missing Parsers:[/yellow]")
            console.print("[dim]Some files were skipped due to missing language parsers:[/dim]")

            # Language to package mapping
            parser_packages = {
                "python": "parsers-python",
                "javascript": "parsers-web",
                "typescript": "parsers-web",
                "go": "parsers-systems",
                "rust": "parsers-systems",
                "cpp": "parsers-systems",
                "java": "parsers-enterprise",
                "csharp": "parsers-enterprise",
                "kotlin": "parsers-enterprise",
                "php": "parsers-web",
                "ruby": "parsers-ruby",
                "swift": "parsers-swift",
            }

            for lang, count in sorted(result.missing_parsers.items()):
                package = parser_packages.get(lang, f"parsers-{lang}")
                install_cmd = f"pip install clauxton[{package}]"
                console.print(
                    f"  • {count} {lang} file(s) - install with: "
                    f"[cyan]{install_cmd}[/cyan]"
                )

            all_parsers_cmd = "pip install clauxton[parsers-all]"
            console.print(
                f"\n[dim]Or install all parsers: "
                f"[cyan]{all_parsers_cmd}[/cyan][/dim]"
            )

        if result.errors:
            console.print("\n[yellow]⚠ Warnings:[/yellow]")
            for error in result.errors[:5]:  # Show first 5 errors
                console.print(f"  • {error}")
            if len(result.errors) > 5:
                console.print(f"  ... and {len(result.errors) - 5} more")

        # Show index location
        console.print(f"\n[dim]Index stored in: {repo_map.map_dir}[/dim]")

    except RepositoryMapError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


@repo_group.command(name="search")
@click.argument("query")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    help="Path to project root (default: current directory)",
)
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["exact", "fuzzy", "semantic"], case_sensitive=False),
    default="exact",
    help="Search algorithm: exact (substring), fuzzy (typo-tolerant), semantic (TF-IDF)",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of results to return (default: 20)",
)
def search_command(query: str, path: str, search_type: str, limit: int) -> None:
    """
    Search codebase for symbols.

    Searches for functions, classes, and methods by name or docstring.
    Use --type to choose search algorithm:
    - exact: Fast substring matching (default)
    - fuzzy: Typo-tolerant matching
    - semantic: TF-IDF similarity search

    Example:
        clauxton repo search "authenticate"
        clauxton repo search "user" --type fuzzy
        clauxton repo search "login" --type semantic --limit 10
    """
    try:
        project_path = Path(path)
        repo_map = RepositoryMap(project_path)

        # Check if index exists
        if not (repo_map.map_dir / "index.json").exists():
            console.print("[yellow]⚠ No index found. Run 'clauxton repo index' first.[/yellow]")
            raise click.Abort()

        # Perform search
        console.print(f"[blue]Searching for:[/blue] '{query}' ({search_type} search)")
        # Cast search_type to Literal type for type checking
        from typing import Literal, cast
        search_type_literal = cast(Literal["semantic", "exact", "fuzzy"], search_type)
        results = repo_map.search(query, search_type=search_type_literal, limit=limit)

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        # Display results in table
        table = Table(title=f"Search Results ({len(results)} found)")
        table.add_column("Symbol", style="cyan", no_wrap=False)
        table.add_column("Type", style="magenta")
        table.add_column("Location", style="green")

        for symbol in results:
            # Format location
            location = f"{symbol.file_path}:{symbol.line_start}"

            # Add docstring preview if available
            symbol_display = symbol.name
            if symbol.docstring:
                # Truncate long docstrings
                doc_preview = symbol.docstring.split("\n")[0][:50]
                if len(symbol.docstring) > 50:
                    doc_preview += "..."
                symbol_display += f"\n[dim]{doc_preview}[/dim]"

            table.add_row(symbol_display, symbol.type, location)

        console.print(table)

    except RepositoryMapError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


@repo_group.command(name="status")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    help="Path to project root (default: current directory)",
)
def status_command(path: str) -> None:
    """
    Show repository index status.

    Displays information about the current index including number of files,
    symbols, and when it was last updated.

    Example:
        clauxton repo status
    """
    try:
        project_path = Path(path)
        repo_map = RepositoryMap(project_path)

        # Check if index exists
        index_file = repo_map.map_dir / "index.json"
        if not index_file.exists():
            console.print("[yellow]⚠ No index found. Run 'clauxton repo index' first.[/yellow]")
            return

        # Load index data
        index = repo_map.index_data
        symbols = repo_map.symbols_data

        # Display status
        console.print("[blue]Repository Index Status[/blue]\n")
        console.print(f"  Root: {project_path}")
        console.print(f"  Index: {repo_map.map_dir}")
        console.print(f"  Version: {index['version']}")
        console.print(f"  Last indexed: {index['indexed_at']}")

        # Statistics
        stats = index["statistics"]
        console.print("\n[cyan]Files:[/cyan]")
        console.print(f"  Total: {stats['total_files']}")

        if stats["by_type"]:
            console.print("\n[cyan]By Type:[/cyan]")
            for file_type, count in sorted(stats["by_type"].items()):
                console.print(f"  {file_type}: {count}")

        if stats["by_language"]:
            console.print("\n[cyan]By Language:[/cyan]")
            for language, count in sorted(stats["by_language"].items()):
                console.print(f"  {language}: {count}")

        # Symbol count
        total_symbols = sum(len(syms) for syms in symbols.values())
        console.print("\n[cyan]Symbols:[/cyan]")
        console.print(f"  Total: {total_symbols}")

    except RepositoryMapError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise
