"""Tests for Repository CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from clauxton.cli.main import cli


def test_repo_index_without_init(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo index works even without initialization (creates empty index)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["repo", "index"])

        # Repo index can work without init (just indexes current directory)
        assert result.exit_code == 0


def test_repo_index_basic(runner: CliRunner, tmp_path: Path) -> None:
    """Test basic repository indexing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(cli, ["init"])

        # Create a simple Python file
        test_file = Path("example.py")
        test_file.write_text(
            "def hello():\n"
            "    return 'world'\n"
            "\n"
            "class Example:\n"
            "    pass\n"
        )

        # Index repository
        result = runner.invoke(cli, ["repo", "index"])

        assert result.exit_code == 0
        assert "indexed" in result.output.lower() or "success" in result.output.lower()


def test_repo_index_with_incremental(runner: CliRunner, tmp_path: Path) -> None:
    """Test repository indexing with incremental flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create test files
        Path("test.py").write_text("def test(): pass\n")
        Path("main.py").write_text("def main(): pass\n")

        # Index with incremental flag
        result = runner.invoke(cli, ["repo", "index", "--incremental"])

        assert result.exit_code == 0


def test_repo_index_incremental(runner: CliRunner, tmp_path: Path) -> None:
    """Test incremental repository indexing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Initial index
        Path("file1.py").write_text("def func1(): pass\n")
        runner.invoke(cli, ["repo", "index"])

        # Add new file and re-index
        Path("file2.py").write_text("def func2(): pass\n")
        result = runner.invoke(cli, ["repo", "index"])

        assert result.exit_code == 0


def test_repo_search_without_init(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo search warns about no index."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["repo", "search", "test"])

        # Either exits with error or shows warning about no index
        assert "index" in result.output.lower() or result.exit_code != 0


def test_repo_search_without_index(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo search without indexing first."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["repo", "search", "test"])

        # Should warn about no index
        assert "index" in result.output.lower() or result.exit_code != 0


def test_repo_search_basic(runner: CliRunner, tmp_path: Path) -> None:
    """Test basic symbol search."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create file with symbols
        Path("example.py").write_text(
            "def hello():\n"
            "    return 'world'\n"
            "\n"
            "class Example:\n"
            "    def method(self):\n"
            "        pass\n"
        )

        # Index and search
        runner.invoke(cli, ["repo", "index"])
        result = runner.invoke(cli, ["repo", "search", "hello"])

        assert result.exit_code == 0
        # Should show search results or "found" message
        output = result.output.lower()
        assert "hello" in output or "found" in output or "result" in output


def test_repo_search_with_type_filter(runner: CliRunner, tmp_path: Path) -> None:
    """Test symbol search with search algorithm type filter."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        Path("code.py").write_text(
            "def function(): pass\n"
            "class MyClass: pass\n"
        )

        runner.invoke(cli, ["repo", "index"])
        # Use valid search type: exact, fuzzy, or semantic
        result = runner.invoke(cli, ["repo", "search", "MyClass", "--type", "fuzzy"])

        assert result.exit_code == 0


def test_repo_search_with_limit(runner: CliRunner, tmp_path: Path) -> None:
    """Test symbol search with result limit."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create file with multiple functions
        Path("multi.py").write_text(
            "def test1(): pass\n"
            "def test2(): pass\n"
            "def test3(): pass\n"
        )

        runner.invoke(cli, ["repo", "index"])
        result = runner.invoke(cli, ["repo", "search", "test", "--limit", "2"])

        assert result.exit_code == 0


def test_repo_search_semantic_type(runner: CliRunner, tmp_path: Path) -> None:
    """Test symbol search with semantic (TF-IDF) type."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        Path("example.py").write_text("def example(): pass\n")

        runner.invoke(cli, ["repo", "index"])
        result = runner.invoke(cli, ["repo", "search", "example", "--type", "semantic"])

        assert result.exit_code == 0


def test_repo_status_without_init(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo status works without initialization."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["repo", "status"])

        # Status works even without init, just shows no index
        assert result.exit_code == 0 or "index" in result.output.lower()


def test_repo_status_no_index(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo status when not indexed."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["repo", "status"])

        assert result.exit_code == 0
        output = result.output.lower()
        assert "not indexed" in output or "no index" in output or "0" in result.output


def test_repo_status_with_index(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo status after indexing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create and index a file
        Path("test.py").write_text("def test(): pass\nclass Test: pass\n")
        runner.invoke(cli, ["repo", "index"])

        result = runner.invoke(cli, ["repo", "status"])

        assert result.exit_code == 0
        # Should show some statistics (files, symbols, etc.)
        output = result.output.lower()
        assert "file" in output or "symbol" in output or "indexed" in output


def test_repo_status_detailed(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo status shows detailed information."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        Path("example.py").write_text("def func(): pass\nclass Example: pass\n")
        runner.invoke(cli, ["repo", "index"])

        result = runner.invoke(cli, ["repo", "status"])

        assert result.exit_code == 0
        # Should show file/symbol counts
        assert result.output.strip() != ""


def test_repo_search_no_results(runner: CliRunner, tmp_path: Path) -> None:
    """Test symbol search with no matching results."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        Path("code.py").write_text("def hello(): pass\n")
        runner.invoke(cli, ["repo", "index"])

        result = runner.invoke(cli, ["repo", "search", "nonexistent_symbol"])

        assert result.exit_code == 0
        # Should indicate no results found
        output = result.output
        output_lower = output.lower()
        assert (
            "no" in output_lower
            or "not found" in output_lower
            or "0" in output
            or output.strip() == ""
            or "[]" in output
        )


def test_repo_index_empty_directory(runner: CliRunner, tmp_path: Path) -> None:
    """Test indexing an empty directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Index without any source files
        result = runner.invoke(cli, ["repo", "index"])

        # Should succeed but with no files indexed
        assert result.exit_code == 0 or "no files" in result.output.lower()


def test_repo_index_multiple_languages(runner: CliRunner, tmp_path: Path) -> None:
    """Test indexing multiple programming languages."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create files in different languages
        Path("code.py").write_text("def python_func(): pass\n")
        Path("code.js").write_text("function jsFunc() {}\n")
        Path("code.ts").write_text("function tsFunc(): void {}\n")

        result = runner.invoke(cli, ["repo", "index"])

        assert result.exit_code == 0


def test_repo_status_with_path_option(runner: CliRunner, tmp_path: Path) -> None:
    """Test repo status with --path option."""
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    # Initialize in project dir
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(project_dir)
        result_init = runner.invoke(cli, ["init"])
        assert result_init.exit_code == 0

        # Create and index a file
        Path("test.py").write_text("def test(): pass\n")
        runner.invoke(cli, ["repo", "index"])
    finally:
        os.chdir(original_dir)

    # Check status from parent dir with --path
    result = runner.invoke(cli, ["repo", "status", "--path", str(project_dir)])

    assert result.exit_code == 0
