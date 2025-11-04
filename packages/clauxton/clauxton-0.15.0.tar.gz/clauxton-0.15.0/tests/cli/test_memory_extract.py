"""
CLI tests for memory extraction and linking commands (v0.15.0).

Tests the following commands:
- clauxton memory extract
- clauxton memory link
- clauxton memory suggest-merge
"""

import subprocess
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
    """Create and initialize a test project with git repo."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Initialize clauxton
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = project_dir / "test.py"
    test_file.write_text("# Test file\n")
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    return project_dir


# ============================================================================
# memory extract Tests
# ============================================================================


def test_extract_from_recent_commits(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract command with --since option."""
    # Create a commit with decision pattern
    api_file = initialized_project / "api.py"
    api_file.write_text("# API endpoint\n")
    subprocess.run(["git", "add", "."], cwd=initialized_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: Add user authentication"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
    )

    # Extract from last 7 days
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d", "--auto-add"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Extracting from last 7 days" in result.output
    assert "Extracted" in result.output


def test_extract_from_specific_commit(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract command with --commit option."""
    # Create a commit
    api_file = initialized_project / "api.py"
    api_file.write_text("# API endpoint\n")
    subprocess.run(["git", "add", "."], cwd=initialized_project, check=True, capture_output=True)
    result = subprocess.run(
        ["git", "commit", "-m", "refactor: Migrate to FastAPI"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
    )

    # Get commit SHA
    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
        text=True,
    )
    commit_sha = sha_result.stdout.strip()

    # Extract from specific commit
    result = runner.invoke(
        cli,
        ["memory", "extract", "--commit", commit_sha, "--auto-add"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert f"Extracting from commit: {commit_sha}" in result.output


def test_extract_with_auto_add(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract with --auto-add flag."""
    # Create commit
    api_file = initialized_project / "api.py"
    api_file.write_text("# API endpoint\n")
    subprocess.run(["git", "add", "."], cwd=initialized_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: Add REST API"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
    )

    # Extract with auto-add
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d", "--auto-add"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Added" in result.output
    assert "memories to storage" in result.output


def test_extract_preview_and_confirm(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract with preview (default behavior)."""
    # Create commit
    api_file = initialized_project / "api.py"
    api_file.write_text("# API endpoint\n")
    subprocess.run(["git", "add", "."], cwd=initialized_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: Add authentication"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
    )

    # Extract with preview and confirm
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d"],
        input="y\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Extracted Memories" in result.output
    assert "Add" in result.output and "memories to storage" in result.output


def test_extract_preview_and_cancel(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract with preview and cancel."""
    # Create commit
    api_file = initialized_project / "api.py"
    api_file.write_text("# API endpoint\n")
    subprocess.run(["git", "add", "."], cwd=initialized_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: Add API"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
    )

    # Extract and cancel
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d"],
        input="n\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Cancelled" in result.output


def test_extract_no_preview(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract with --no-preview flag."""
    # Create commit
    api_file = initialized_project / "api.py"
    api_file.write_text("# API endpoint\n")
    subprocess.run(["git", "add", "."], cwd=initialized_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: Add API"],
        cwd=initialized_project,
        check=True,
        capture_output=True,
    )

    # Extract without preview
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d", "--no-preview", "--auto-add"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    # Should not show preview
    assert "Extracted Memories" not in result.output


def test_extract_not_git_repo(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test extract command when not in git repo."""
    # Create project without git
    project_dir = tmp_path / "no-git"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Initialize clauxton
    runner.invoke(cli, ["init"])

    # Try to extract
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Error" in result.output


def test_extract_invalid_commit(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract with non-existent commit."""
    result = runner.invoke(
        cli,
        ["memory", "extract", "--commit", "invalid123"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Error" in result.output


def test_extract_invalid_time_format(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract with invalid time format."""
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "invalid"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Invalid time format" in result.output


def test_extract_no_memories(runner: CliRunner, initialized_project: Path) -> None:
    """Test extract when no memories are found."""
    # Only initial commit exists (no decision/pattern)
    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "No memories extracted" in result.output


def test_extract_without_init(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test extract fails without initialization."""
    project_dir = tmp_path / "uninit"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(
        cli,
        ["memory", "extract", "--since", "7d"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert ".clauxton/ not found" in result.output


# ============================================================================
# memory link Tests
# ============================================================================


def test_link_specific_memory(runner: CliRunner, initialized_project: Path) -> None:
    """Test link command with --id option."""
    # Add memories
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
            "REST API",
            "--category",
            "api",
            "--tags",
            "api,rest",
        ],
        catch_exceptions=False,
    )

    add_result = runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API Security",
            "--content",
            "JWT auth",
            "--category",
            "api",
            "--tags",
            "api,security",
        ],
        catch_exceptions=False,
    )

    memory_id = add_result.output.split("Memory added: ")[1].split("\n")[0].strip()

    # Link the memory
    result = runner.invoke(
        cli,
        ["memory", "link", "--id", memory_id],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Finding relationships for:" in result.output


def test_link_all_memories(runner: CliRunner, initialized_project: Path) -> None:
    """Test link command with --auto flag."""
    # Add multiple memories
    for i in range(3):
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
                "--tags",
                "api,rest",
            ],
            catch_exceptions=False,
        )

    # Auto-link all
    result = runner.invoke(
        cli,
        ["memory", "link", "--auto"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Auto-linking all memories" in result.output
    assert "Created" in result.output


def test_link_with_threshold(runner: CliRunner, initialized_project: Path) -> None:
    """Test link with custom threshold."""
    # Add memories
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "API",
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
            "API 2",
            "--content",
            "Content",
            "--category",
            "api",
        ],
        catch_exceptions=False,
    )

    # Link with high threshold
    result = runner.invoke(
        cli,
        ["memory", "link", "--auto", "--threshold", "0.8"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "threshold: 0.8" in result.output


def test_link_invalid_memory_id(runner: CliRunner, initialized_project: Path) -> None:
    """Test link with non-existent memory ID."""
    result = runner.invoke(
        cli,
        ["memory", "link", "--id", "MEM-20251103-999"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Memory not found" in result.output


def test_link_invalid_threshold(runner: CliRunner, initialized_project: Path) -> None:
    """Test link with invalid threshold."""
    result = runner.invoke(
        cli,
        ["memory", "link", "--auto", "--threshold", "1.5"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Threshold must be between 0.0 and 1.0" in result.output


def test_link_missing_required_option(runner: CliRunner, initialized_project: Path) -> None:
    """Test link without --id or --auto."""
    result = runner.invoke(
        cli,
        ["memory", "link"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Must specify either --id or --auto" in result.output


def test_link_without_init(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test link fails without initialization."""
    project_dir = tmp_path / "uninit"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(
        cli,
        ["memory", "link", "--auto"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert ".clauxton/ not found" in result.output


# ============================================================================
# memory suggest-merge Tests
# ============================================================================


def test_suggest_merge_candidates(runner: CliRunner, initialized_project: Path) -> None:
    """Test suggest-merge command."""
    # Add similar memories
    runner.invoke(
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
            "API Design Pattern",
            "--content",
            "Use RESTful API design",
            "--category",
            "api",
        ],
        catch_exceptions=False,
    )

    # Suggest merge
    result = runner.invoke(
        cli,
        ["memory", "suggest-merge"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    # Should find candidates or show "No merge candidates"
    assert "merge candidates" in result.output.lower()


def test_suggest_merge_with_threshold(runner: CliRunner, initialized_project: Path) -> None:
    """Test suggest-merge with custom threshold."""
    # Add memories
    runner.invoke(
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

    result = runner.invoke(
        cli,
        ["memory", "suggest-merge", "--threshold", "0.9"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "threshold: 0.9" in result.output


def test_suggest_merge_with_limit(runner: CliRunner, initialized_project: Path) -> None:
    """Test suggest-merge with limit option."""
    # Add multiple similar memories
    for i in range(5):
        runner.invoke(
            cli,
            [
                "memory",
                "add",
                "--type",
                "knowledge",
                "--title",
                "Similar Memory",
                "--content",
                "Same content",
                "--category",
                "test",
            ],
            catch_exceptions=False,
        )

    result = runner.invoke(
        cli,
        ["memory", "suggest-merge", "--limit", "3", "--threshold", "0.7"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0


def test_suggest_merge_no_candidates(runner: CliRunner, initialized_project: Path) -> None:
    """Test suggest-merge when no candidates found."""
    # Add single memory
    runner.invoke(
        cli,
        [
            "memory",
            "add",
            "--type",
            "knowledge",
            "--title",
            "Unique",
            "--content",
            "Content",
            "--category",
            "test",
        ],
        catch_exceptions=False,
    )

    result = runner.invoke(
        cli,
        ["memory", "suggest-merge"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "No merge candidates found" in result.output


def test_suggest_merge_invalid_threshold(runner: CliRunner, initialized_project: Path) -> None:
    """Test suggest-merge with invalid threshold."""
    result = runner.invoke(
        cli,
        ["memory", "suggest-merge", "--threshold", "2.0"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "Threshold must be between 0.0 and 1.0" in result.output


def test_suggest_merge_without_init(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test suggest-merge fails without initialization."""
    project_dir = tmp_path / "uninit"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(
        cli,
        ["memory", "suggest-merge"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert ".clauxton/ not found" in result.output


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_parse_time_delta_days() -> None:
    """Test _parse_time_delta with days."""
    from clauxton.cli.memory import _parse_time_delta

    assert _parse_time_delta("7d") == 7
    assert _parse_time_delta("1d") == 1
    assert _parse_time_delta("30d") == 30


def test_parse_time_delta_weeks() -> None:
    """Test _parse_time_delta with weeks."""
    from clauxton.cli.memory import _parse_time_delta

    assert _parse_time_delta("1w") == 7
    assert _parse_time_delta("2w") == 14
    assert _parse_time_delta("4w") == 28


def test_parse_time_delta_months() -> None:
    """Test _parse_time_delta with months."""
    from clauxton.cli.memory import _parse_time_delta

    assert _parse_time_delta("1m") == 30
    assert _parse_time_delta("2m") == 60


def test_parse_time_delta_invalid() -> None:
    """Test _parse_time_delta with invalid format."""
    from clauxton.cli.memory import _parse_time_delta

    with pytest.raises(ValueError, match="Invalid time format"):
        _parse_time_delta("invalid")

    with pytest.raises(ValueError):
        _parse_time_delta("7x")
