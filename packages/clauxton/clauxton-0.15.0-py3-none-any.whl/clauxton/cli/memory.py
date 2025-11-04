"""CLI commands for unified Memory management (v0.15.0)."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click

from clauxton.core.memory import Memory

if TYPE_CHECKING:
    from clauxton.core.memory import MemoryEntry


@click.group()
def memory() -> None:
    """Memory management commands."""
    pass


@memory.command("add")
@click.option(
    "--type",
    "entry_type",
    type=click.Choice(["knowledge", "decision", "code", "task", "pattern"]),
    help="Memory type",
)
@click.option("--title", help="Memory title")
@click.option("--content", help="Memory content")
@click.option("--category", help="Category")
@click.option("--tags", help="Comma-separated tags")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
def add(
    entry_type: Optional[str],
    title: Optional[str],
    content: Optional[str],
    category: Optional[str],
    tags: Optional[str],
    interactive: bool,
) -> None:
    """
    Add memory entry.

    Examples:
        clauxton memory add -i                    # Interactive
        clauxton memory add --type knowledge --title "API Design" \\
            --content "Use RESTful API" --category architecture
    """
    from clauxton.core.memory import MemoryEntry

    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    if interactive:
        # Interactive mode with guided prompts
        click.echo(click.style("\nAdd Memory Entry (Interactive Mode)\n", fg="cyan", bold=True))

        entry_type = click.prompt(
            "Memory type",
            type=click.Choice(["knowledge", "decision", "code", "task", "pattern"]),
        )
        title = click.prompt("Title")

        click.echo("\nContent (multi-line, press Ctrl+D when done):")
        content_lines = []
        try:
            while True:
                line = input()
                content_lines.append(line)
        except EOFError:
            pass
        content = "\n".join(content_lines).strip()

        if not content:
            click.echo(click.style("Error: Content cannot be empty", fg="red"))
            raise click.Abort()

        category = click.prompt("Category")
        tags_str = click.prompt("Tags (comma-separated)", default="")
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
    else:
        if not all([entry_type, title, content, category]):
            click.echo(
                click.style(
                    "Missing required fields. Use --interactive or provide all options.",
                    fg="red",
                )
            )
            click.echo("\nRequired: --type, --title, --content, --category")
            click.echo("Optional: --tags")
            raise click.Abort()
        tags_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    # Generate memory ID
    memory_id = mem._generate_memory_id()

    now = datetime.now()
    entry = MemoryEntry(
        id=memory_id,
        type=entry_type,  # type: ignore[arg-type]
        title=title,  # type: ignore[arg-type]
        content=content,  # type: ignore[arg-type]
        category=category,  # type: ignore[arg-type]
        tags=tags_list,
        created_at=now,
        updated_at=now,
        source="manual",
        confidence=1.0,
    )

    try:
        result_id = mem.add(entry)
        click.echo(click.style(f"\n✓ Memory added: {result_id}", fg="green"))
        click.echo(f"  Type: {entry_type}")
        click.echo(f"  Title: {title}")
        click.echo(f"  Category: {category}")
        if tags_list:
            click.echo(f"  Tags: {', '.join(tags_list)}")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@memory.command("search")
@click.argument("query")
@click.option(
    "--type",
    "type_filter",
    multiple=True,
    type=click.Choice(["knowledge", "decision", "code", "task", "pattern"]),
    help="Filter by type (can be used multiple times)",
)
@click.option("--limit", default=10, help="Maximum results")
def search(query: str, type_filter: tuple[str, ...], limit: int) -> None:
    """
    Search memories.

    Examples:
        clauxton memory search "authentication"
        clauxton memory search "API" --type knowledge --type decision
    """
    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    results = mem.search(query, type_filter=list(type_filter) or None, limit=limit)

    if not results:
        click.echo(click.style("\nNo memories found", fg="yellow"))
        return

    click.echo(click.style(f"\nSearch Results: '{query}'", fg="cyan", bold=True))
    click.echo(click.style(f"Found {len(results)} matches\n", fg="white"))

    for entry in results:
        click.echo(click.style(f"  {entry.id}", fg="cyan"))
        click.echo(f"    Type: {entry.type}")
        click.echo(f"    Title: {entry.title}")
        click.echo(f"    Category: {entry.category}")
        if entry.tags:
            click.echo(f"    Tags: {', '.join(entry.tags)}")
        click.echo()


@memory.command("list")
@click.option(
    "--type",
    "type_filter",
    multiple=True,
    type=click.Choice(["knowledge", "decision", "code", "task", "pattern"]),
    help="Filter by type",
)
@click.option("--category", help="Filter by category")
@click.option("--tag", "tag_filter", multiple=True, help="Filter by tags")
def list_memories(
    type_filter: tuple[str, ...], category: Optional[str], tag_filter: tuple[str, ...]
) -> None:
    """
    List all memories.

    Examples:
        clauxton memory list
        clauxton memory list --type knowledge
        clauxton memory list --category architecture
        clauxton memory list --tag api --tag rest
    """
    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    memories = mem.list_all(
        type_filter=list(type_filter) or None,
        category_filter=category,
        tag_filter=list(tag_filter) or None,
    )

    if not memories:
        click.echo(click.style("\nNo memories found", fg="yellow"))
        return

    click.echo(click.style(f"\nMemories ({len(memories)}):\n", bold=True))

    for entry in memories:
        click.echo(click.style(f"  {entry.id}", fg="cyan"))
        click.echo(f"    Type: {entry.type}")
        title_display = entry.title[:50] + "..." if len(entry.title) > 50 else entry.title
        click.echo(f"    Title: {title_display}")
        click.echo(f"    Category: {entry.category}")
        if entry.tags:
            tags_display = ", ".join(entry.tags[:3])
            if len(entry.tags) > 3:
                tags_display += f" (+{len(entry.tags) - 3} more)"
            click.echo(f"    Tags: {tags_display}")
        click.echo()


@memory.command("get")
@click.argument("memory_id")
def get(memory_id: str) -> None:
    """
    Get memory details.

    Example:
        clauxton memory get MEM-20260127-001
    """
    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    entry = mem.get(memory_id)

    if not entry:
        click.echo(click.style(f"\nMemory not found: {memory_id}", fg="red"))
        raise click.Abort()

    click.echo(click.style(f"\n{entry.id}", fg="cyan", bold=True))
    click.echo(f"Type: {entry.type}")
    click.echo(f"Title: {entry.title}")
    click.echo(f"Category: {entry.category}")

    if entry.tags:
        click.echo(f"Tags: {', '.join(entry.tags)}")

    click.echo(f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Source: {entry.source}")

    if entry.confidence < 1.0:
        click.echo(f"Confidence: {entry.confidence:.2f}")

    click.echo(click.style("\nContent:", bold=True))
    click.echo(entry.content)

    if entry.related_to:
        click.echo(click.style("\nRelated:", bold=True))
        click.echo(", ".join(entry.related_to))

    if entry.supersedes:
        click.echo(click.style(f"\nSupersedes: {entry.supersedes}", fg="yellow"))

    if entry.source_ref:
        click.echo(f"Source ref: {entry.source_ref}")

    if entry.legacy_id:
        click.echo(f"Legacy ID: {entry.legacy_id}")

    click.echo()


@memory.command("update")
@click.argument("memory_id")
@click.option("--title", help="New title")
@click.option("--content", help="New content")
@click.option("--category", help="New category")
@click.option("--tags", help="New tags (comma-separated)")
def update(
    memory_id: str,
    title: Optional[str],
    content: Optional[str],
    category: Optional[str],
    tags: Optional[str],
) -> None:
    """
    Update memory.

    Example:
        clauxton memory update MEM-20260127-001 --title "New Title"
        clauxton memory update MEM-20260127-001 --tags "api,rest,v2"
    """
    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    # Build kwargs
    kwargs: dict[str, str | list[str]] = {}
    if title:
        kwargs["title"] = title
    if content:
        kwargs["content"] = content
    if category:
        kwargs["category"] = category
    if tags:
        kwargs["tags"] = [t.strip() for t in tags.split(",")]

    if not kwargs:
        click.echo(click.style("No fields to update", fg="yellow"))
        return

    try:
        success = mem.update(memory_id, **kwargs)

        if success:
            click.echo(click.style(f"\n✓ Memory updated: {memory_id}", fg="green"))
            for key, value in kwargs.items():
                if key == "tags" and isinstance(value, list):
                    click.echo(f"  {key}: {', '.join(value)}")
                else:
                    display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    click.echo(f"  {key}: {display_value}")
        else:
            click.echo(click.style(f"\nMemory not found: {memory_id}", fg="red"))
            raise click.Abort()

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort()


@memory.command("delete")
@click.argument("memory_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(memory_id: str, yes: bool) -> None:
    """
    Delete memory.

    Example:
        clauxton memory delete MEM-20260127-001
        clauxton memory delete MEM-20260127-001 --yes
    """
    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    # Get entry to show details before deletion
    entry = mem.get(memory_id)
    if not entry:
        click.echo(click.style(f"\nMemory not found: {memory_id}", fg="red"))
        raise click.Abort()

    if not yes:
        click.echo(f"\nDelete memory: {entry.title} ({memory_id})?")
        click.echo(f"Type: {entry.type}")
        click.echo(f"Category: {entry.category}")
        if not click.confirm("\nAre you sure?"):
            click.echo("Cancelled")
            return

    success = mem.delete(memory_id)

    if success:
        click.echo(click.style(f"\n✓ Memory deleted: {memory_id}", fg="green"))
    else:
        click.echo(click.style(f"\nMemory not found: {memory_id}", fg="red"))
        raise click.Abort()


@memory.command("related")
@click.argument("memory_id")
@click.option("--limit", default=5, help="Maximum results")
def related(memory_id: str, limit: int) -> None:
    """
    Find related memories.

    Example:
        clauxton memory related MEM-20260127-001
        clauxton memory related MEM-20260127-001 --limit 10
    """
    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    mem = Memory(project_root)

    # Check if memory exists
    entry = mem.get(memory_id)
    if not entry:
        click.echo(click.style(f"\nMemory not found: {memory_id}", fg="red"))
        raise click.Abort()

    related_entries = mem.find_related(memory_id, limit=limit)

    if not related_entries:
        click.echo(click.style(f"\nNo related memories found for {memory_id}", fg="yellow"))
        return

    click.echo(click.style(f"\nRelated to {memory_id}:", fg="cyan", bold=True))
    click.echo(f"'{entry.title}'")
    click.echo(click.style(f"\nFound {len(related_entries)} related memories:\n", fg="white"))

    for related_entry in related_entries:
        click.echo(click.style(f"  {related_entry.id}", fg="cyan"))
        click.echo(f"    Type: {related_entry.type}")
        title_display = (
            related_entry.title[:50] + "..."
            if len(related_entry.title) > 50
            else related_entry.title
        )
        click.echo(f"    Title: {title_display}")
        click.echo(f"    Category: {related_entry.category}")

        # Show reason for relation
        reasons = []
        if memory_id in related_entry.related_to or related_entry.id in entry.related_to:
            reasons.append("explicit link")
        shared_tags = set(entry.tags) & set(related_entry.tags)
        if shared_tags:
            reasons.append(f"shared tags: {', '.join(list(shared_tags)[:2])}")
        if entry.category == related_entry.category:
            reasons.append("same category")

        if reasons:
            click.echo(click.style(f"    Relation: {', '.join(reasons)}", fg="yellow"))

        click.echo()


# ============================================================================
# Helper Functions
# ============================================================================


def _parse_time_delta(time_str: str) -> int:
    """
    Parse time string to days.

    Args:
        time_str: Time string (e.g., "7d", "2w", "1m")

    Returns:
        Number of days

    Raises:
        ValueError: If format is invalid

    Example:
        >>> _parse_time_delta("7d")
        7
        >>> _parse_time_delta("2w")
        14
        >>> _parse_time_delta("1m")
        30
    """
    try:
        if time_str.endswith("d"):
            return int(time_str[:-1])
        elif time_str.endswith("w"):
            return int(time_str[:-1]) * 7
        elif time_str.endswith("m"):
            return int(time_str[:-1]) * 30
        else:
            raise ValueError(f"Invalid time format: {time_str}. Use format: 7d, 2w, or 1m")
    except ValueError as e:
        # Re-raise with better error message if int() conversion fails
        if "invalid literal" in str(e):
            raise ValueError(
                f"Invalid time format: {time_str}. Use format: 7d, 2w, or 1m"
            ) from e
        raise


def _display_memory_preview(
    memories: list["MemoryEntry"], title: str = "Extracted Memories"
) -> None:
    """
    Display memory preview in formatted table.

    Args:
        memories: List of MemoryEntry objects
        title: Preview title
    """
    if not memories:
        click.echo(click.style("\nNo memories to display", fg="yellow"))
        return

    click.echo(click.style(f"\n{title}", fg="cyan", bold=True))
    click.echo(click.style(f"Total: {len(memories)}\n", fg="white"))

    for i, memory in enumerate(memories, 1):
        click.echo(click.style(f"{i}. {memory.title}", fg="cyan", bold=True))
        click.echo(f"   ID: {memory.id}")
        click.echo(f"   Type: {memory.type}")
        click.echo(f"   Category: {memory.category}")
        click.echo(f"   Confidence: {memory.confidence:.2f}")
        if memory.tags:
            click.echo(f"   Tags: {', '.join(memory.tags)}")
        # Truncate content for preview
        content_preview = (
            memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
        )
        click.echo(f"   Content: {content_preview}")
        if memory.source_ref:
            click.echo(f"   Source: {memory.source_ref[:7]}")
        click.echo()


# ============================================================================
# Extract Commands
# ============================================================================


@memory.command("extract")
@click.option("--since", default="7d", help="Extract from commits since (e.g., 7d, 30d, 2w)")
@click.option("--commit", help="Extract from specific commit SHA")
@click.option("--auto-add", is_flag=True, help="Automatically add extracted memories")
@click.option("--preview/--no-preview", default=True, help="Preview before adding")
def extract_memories(since: str, commit: Optional[str], auto_add: bool, preview: bool) -> None:
    """
    Extract memories from Git commits.

    Examples:
        clauxton memory extract --since 7d
        clauxton memory extract --commit abc123
        clauxton memory extract --since 30d --auto-add
    """
    from clauxton.semantic.memory_extractor import MemoryExtractor, MemoryExtractorError

    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    try:
        extractor = MemoryExtractor(project_root)
    except Exception as e:
        click.echo(click.style(f"Error initializing extractor: {e}", fg="red"), err=True)
        raise click.Abort()

    # Extract memories
    try:
        if commit:
            # Extract from specific commit
            click.echo(f"Extracting from commit: {commit}")
            memories = extractor.extract_from_commit(commit, auto_add=False)
        else:
            # Extract from recent commits
            try:
                since_days = _parse_time_delta(since)
            except ValueError as e:
                click.echo(click.style(f"Error: {e}", fg="red"), err=True)
                raise click.Abort()

            click.echo(f"Extracting from last {since_days} days...")
            memories = extractor.extract_from_recent_commits(since_days=since_days, auto_add=False)

    except MemoryExtractorError as e:
        click.echo(click.style(f"Extraction error: {e}", fg="red"), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()

    # Display results
    if not memories:
        click.echo(click.style("\nNo memories extracted", fg="yellow"))
        return

    # Count by type
    decisions = sum(1 for m in memories if m.type == "decision")
    patterns = sum(1 for m in memories if m.type == "pattern")

    click.echo(click.style(f"\n✓ Extracted {len(memories)} memories:", fg="green"))
    click.echo(f"  Decisions: {decisions}")
    click.echo(f"  Patterns: {patterns}")

    # Preview memories
    if preview:
        _display_memory_preview(memories)

    # Add to storage
    if auto_add:
        # Auto-add without confirmation
        mem = Memory(project_root)
        added = 0
        skipped = 0

        for memory in memories:
            try:
                mem.add(memory)
                added += 1
            except Exception:
                # Skip if already exists or validation fails
                skipped += 1

        click.echo(click.style(f"\n✓ Added {added} memories to storage", fg="green"))
        if skipped > 0:
            click.echo(click.style(f"  Skipped {skipped} (duplicates or errors)", fg="yellow"))

    elif preview and memories:
        # Ask for confirmation
        if click.confirm(f"\nAdd {len(memories)} memories to storage?"):
            mem = Memory(project_root)
            added = 0
            skipped = 0

            for memory in memories:
                try:
                    mem.add(memory)
                    added += 1
                except Exception:
                    skipped += 1

            click.echo(click.style(f"\n✓ Added {added} memories to storage", fg="green"))
            if skipped > 0:
                click.echo(click.style(f"  Skipped {skipped} (duplicates or errors)", fg="yellow"))
        else:
            click.echo("Cancelled.")


@memory.command("link")
@click.option("--id", "memory_id", help="Link specific memory by ID")
@click.option("--auto", is_flag=True, help="Auto-link all memories")
@click.option("--threshold", default=0.3, type=float, help="Similarity threshold (0.0-1.0)")
def link_memories(memory_id: Optional[str], auto: bool, threshold: float) -> None:
    """
    Find and link related memories.

    Examples:
        clauxton memory link --id MEM-20251103-001
        clauxton memory link --auto
        clauxton memory link --auto --threshold 0.5
    """
    from clauxton.semantic.memory_linker import MemoryLinker

    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    # Validate threshold
    if not 0.0 <= threshold <= 1.0:
        click.echo(click.style("Error: Threshold must be between 0.0 and 1.0", fg="red"), err=True)
        raise click.Abort()

    # Require either --id or --auto
    if not memory_id and not auto:
        click.echo(
            click.style("Error: Must specify either --id or --auto", fg="red"),
            err=True,
        )
        raise click.Abort()

    try:
        linker = MemoryLinker(project_root)
        mem = Memory(project_root)

        if auto:
            # Auto-link all memories
            click.echo(f"Auto-linking all memories (threshold: {threshold})...")
            links_created = linker.auto_link_all(threshold=threshold)

            click.echo(click.style(f"\n✓ Created {links_created} new relationships", fg="green"))

        else:
            # Link specific memory
            entry = mem.get(memory_id)  # type: ignore[arg-type]
            if not entry:
                click.echo(click.style(f"\nMemory not found: {memory_id}", fg="red"))
                raise click.Abort()

            click.echo(f"Finding relationships for: {entry.title}")
            related_ids = linker.find_relationships(entry, threshold=threshold)

            if not related_ids:
                click.echo(click.style("\nNo relationships found", fg="yellow"))
                return

            click.echo(click.style(f"\n✓ Found {len(related_ids)} relationships:", fg="green"))
            for rid in related_ids:
                related = mem.get(rid)
                if related:
                    click.echo(f"  - {rid}: {related.title[:50]}")

            # Update memory with relationships
            existing_related = set(entry.related_to or [])
            new_related = [rid for rid in related_ids if rid not in existing_related]

            if new_related:
                updated_related = list(existing_related) + new_related
                mem.update(memory_id, related_to=updated_related)  # type: ignore[arg-type]
                msg = f"\n✓ Updated {memory_id} with {len(new_related)} new relationships"
                click.echo(click.style(msg, fg="green"))
            else:
                click.echo(click.style("\nAll relationships already exist", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@memory.command("suggest-merge")
@click.option("--threshold", default=0.8, type=float, help="Similarity threshold (0.8-1.0)")
@click.option("--limit", default=10, type=int, help="Max suggestions to show")
def suggest_merge(threshold: float, limit: int) -> None:
    """
    Find duplicate or highly similar memories that should be merged.

    Examples:
        clauxton memory suggest-merge
        clauxton memory suggest-merge --threshold 0.9
    """
    from clauxton.semantic.memory_linker import MemoryLinker

    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    # Validate threshold
    if not 0.0 <= threshold <= 1.0:
        click.echo(click.style("Error: Threshold must be between 0.0 and 1.0", fg="red"), err=True)
        raise click.Abort()

    try:
        linker = MemoryLinker(project_root)
        mem = Memory(project_root)

        click.echo(f"Searching for merge candidates (threshold: {threshold})...")
        candidates = linker.suggest_merge_candidates(threshold=threshold)

        if not candidates:
            click.echo(click.style("\nNo merge candidates found", fg="yellow"))
            return

        # Limit results
        candidates = candidates[:limit]

        click.echo(click.style(f"\n✓ Found {len(candidates)} merge candidates:\n", fg="green"))

        for i, (id1, id2, score) in enumerate(candidates, 1):
            mem1 = mem.get(id1)
            mem2 = mem.get(id2)

            if mem1 and mem2:
                click.echo(click.style(f"{i}. Similarity: {score:.2f}", fg="cyan", bold=True))
                click.echo(f"   Memory 1: {id1}")
                click.echo(f"     Title: {mem1.title[:60]}")
                click.echo(f"     Type: {mem1.type} | Category: {mem1.category}")
                click.echo()
                click.echo(f"   Memory 2: {id2}")
                click.echo(f"     Title: {mem2.title[:60]}")
                click.echo(f"     Type: {mem2.type} | Category: {mem2.category}")
                click.echo()

        click.echo(click.style("\nNote: Manual review recommended before merging", fg="yellow"))
        click.echo("Use 'clauxton memory get <ID>' to view full details")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@memory.command("graph")
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["dot", "mermaid", "json"]),
    default="mermaid",
    help="Output format",
)
@click.option("--type", "memory_type", help="Filter by memory type")
@click.option("--max-nodes", type=int, default=100, help="Maximum number of nodes")
def generate_graph(
    output: Optional[str], format: str, memory_type: Optional[str], max_nodes: int
) -> None:
    """
    Generate memory relationship graph.

    Creates a visual representation of memory relationships in various formats:
    - DOT: Graphviz format for high-quality rendering
    - Mermaid: Markdown-compatible diagrams
    - JSON: Data format for web visualizations

    Examples:
        clauxton memory graph
        clauxton memory graph --format mermaid --output graph.md
        clauxton memory graph --output graph.dot --format dot
        clauxton memory graph --type knowledge --format json
    """
    from clauxton.visualization.memory_graph import MemoryGraph

    project_root = Path.cwd()

    # Check if .clauxton exists
    if not (project_root / ".clauxton").exists():
        click.echo(click.style("⚠ .clauxton/ not found. Run 'clauxton init' first", fg="red"))
        raise click.Abort()

    try:
        graph = MemoryGraph(project_root)

        # Generate output filename if not provided
        if not output:
            ext = "md" if format == "mermaid" else format
            output = f"memory_graph.{ext}"

        output_path = Path(output)

        click.echo(f"Generating {format} graph...")

        # Export based on format
        if format == "dot":
            graph.export_to_dot(output_path, memory_type, max_nodes)
        elif format == "mermaid":
            graph.export_to_mermaid(output_path, memory_type, max_nodes)
        elif format == "json":
            graph.export_to_json(output_path, memory_type, max_nodes)

        click.echo(click.style(f"\n✓ Graph exported to {output_path}", fg="green"))

        # Show statistics
        graph_data = graph.generate_graph_data(memory_type, max_nodes)
        click.echo(f"  Nodes: {graph_data['metadata']['total_nodes']}")
        click.echo(f"  Edges: {graph_data['metadata']['total_edges']}")

        if memory_type:
            click.echo(f"  Type: {memory_type}")

        # Show usage hints based on format
        if format == "dot":
            click.echo(
                click.style(
                    f"\nRender with: dot -Tpng {output_path} -o {output_path.stem}.png",
                    fg="yellow",
                )
            )
        elif format == "mermaid":
            click.echo(
                click.style(
                    "\nInclude in Markdown or view on GitHub/GitLab",
                    fg="yellow",
                )
            )

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()
