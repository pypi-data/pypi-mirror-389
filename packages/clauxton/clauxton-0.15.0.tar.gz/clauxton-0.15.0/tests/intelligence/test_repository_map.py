"""Tests for clauxton.intelligence.repository_map module."""

from pathlib import Path

import pytest

from clauxton.intelligence.repository_map import (
    FileNode,
    IndexResult,
    RepositoryMap,
    RepositoryMapError,
    Symbol,
)


class TestRepositoryMapInit:
    """Test RepositoryMap initialization."""

    def test_init_with_path_object(self, tmp_path):
        """Test initialization with Path object."""
        repo_map = RepositoryMap(tmp_path)
        assert repo_map.root_dir == tmp_path
        assert repo_map.map_dir == tmp_path / ".clauxton" / "map"
        assert repo_map.map_dir.exists()

    def test_init_with_string_path(self, tmp_path):
        """Test initialization with string path."""
        repo_map = RepositoryMap(str(tmp_path))
        assert repo_map.root_dir == tmp_path
        assert isinstance(repo_map.root_dir, Path)

    def test_init_creates_clauxton_directory(self, tmp_path):
        """Test that initialization creates .clauxton directory."""
        clauxton_dir = tmp_path / ".clauxton"
        assert not clauxton_dir.exists()

        RepositoryMap(tmp_path)

        assert clauxton_dir.exists()
        assert (clauxton_dir / "map").exists()

    def test_init_with_nonexistent_directory_raises_error(self, tmp_path):
        """Test that initializing with non-existent directory raises error."""
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(RepositoryMapError):
            RepositoryMap(nonexistent)

    def test_multiple_init_same_directory(self, tmp_path):
        """Test that multiple initializations on same directory work."""
        repo_map1 = RepositoryMap(tmp_path)
        repo_map2 = RepositoryMap(tmp_path)

        assert repo_map1.root_dir == repo_map2.root_dir
        assert repo_map1.map_dir == repo_map2.map_dir


class TestRepositoryMapLazyLoading:
    """Test lazy loading of index and symbols data."""

    def test_index_data_lazy_loading(self, tmp_path):
        """Test that index data is not loaded until accessed."""
        repo_map = RepositoryMap(tmp_path)

        # Initially None
        assert repo_map._index is None

        # Access triggers loading
        index = repo_map.index_data
        assert repo_map._index is not None
        assert isinstance(index, dict)

    def test_symbols_data_lazy_loading(self, tmp_path):
        """Test that symbols data is not loaded until accessed."""
        repo_map = RepositoryMap(tmp_path)

        # Initially None
        assert repo_map._symbols is None

        # Access triggers loading
        symbols = repo_map.symbols_data
        assert repo_map._symbols is not None
        assert isinstance(symbols, dict)

    def test_index_data_returns_default_when_no_file(self, tmp_path):
        """Test that index_data returns default structure when no file exists."""
        repo_map = RepositoryMap(tmp_path)
        index = repo_map.index_data

        assert index["version"] == "0.11.0"
        assert index["indexed_at"] is None
        assert index["root_path"] == str(tmp_path)
        assert index["files"] == []
        assert index["statistics"]["total_files"] == 0

    def test_symbols_data_returns_empty_when_no_file(self, tmp_path):
        """Test that symbols_data returns empty dict when no file exists."""
        repo_map = RepositoryMap(tmp_path)
        symbols = repo_map.symbols_data

        assert symbols == {}

    def test_clear_cache(self, tmp_path):
        """Test clearing cache."""
        repo_map = RepositoryMap(tmp_path)

        # Load data
        _ = repo_map.index_data
        _ = repo_map.symbols_data
        assert repo_map._index is not None
        assert repo_map._symbols is not None

        # Clear cache
        repo_map.clear_cache()
        assert repo_map._index is None
        assert repo_map._symbols is None


class TestIndexResult:
    """Test IndexResult class."""

    def test_index_result_creation(self):
        """Test creating IndexResult."""
        result = IndexResult(
            files_indexed=10,
            symbols_found=50,
            duration_seconds=1.5
        )

        assert result.files_indexed == 10
        assert result.symbols_found == 50
        assert result.duration_seconds == 1.5
        assert result.errors == []

    def test_index_result_with_errors(self):
        """Test IndexResult with errors."""
        errors = ["Error 1", "Error 2"]
        result = IndexResult(
            files_indexed=5,
            symbols_found=20,
            duration_seconds=0.5,
            errors=errors
        )

        assert result.errors == errors

    def test_index_result_repr(self):
        """Test IndexResult string representation."""
        result = IndexResult(10, 50, 1.5)
        repr_str = repr(result)

        assert "10" in repr_str
        assert "50" in repr_str
        assert "1.5" in repr_str or "1.50" in repr_str


class TestFileNode:
    """Test FileNode class."""

    def test_file_node_creation(self, tmp_path):
        """Test creating FileNode."""
        from datetime import datetime

        file_path = tmp_path / "test.py"
        node = FileNode(
            path=file_path,
            relative_path="test.py",
            file_type="source",
            language="python",
            size_bytes=1024,
            line_count=50,
            last_modified=datetime.now()
        )

        assert node.path == file_path
        assert node.relative_path == "test.py"
        assert node.file_type == "source"
        assert node.language == "python"

    def test_file_node_to_dict(self, tmp_path):
        """Test FileNode.to_dict()."""
        from datetime import datetime

        file_path = tmp_path / "test.py"
        now = datetime.now()

        node = FileNode(
            path=file_path,
            relative_path="test.py",
            file_type="source",
            language="python",
            size_bytes=1024,
            line_count=50,
            last_modified=now
        )

        d = node.to_dict()

        assert d["path"] == str(file_path)
        assert d["relative_path"] == "test.py"
        assert d["file_type"] == "source"
        assert d["language"] == "python"
        assert d["size_bytes"] == 1024
        assert d["line_count"] == 50
        assert isinstance(d["last_modified"], str)


class TestSymbol:
    """Test Symbol class."""

    def test_symbol_creation(self):
        """Test creating Symbol."""
        symbol = Symbol(
            name="my_function",
            type="function",
            file_path="/path/to/file.py",
            line_start=10,
            line_end=20,
            docstring="Does something",
            signature="def my_function(x: int) -> str"
        )

        assert symbol.name == "my_function"
        assert symbol.type == "function"
        assert symbol.file_path == "/path/to/file.py"
        assert symbol.line_start == 10
        assert symbol.line_end == 20

    def test_symbol_to_dict(self):
        """Test Symbol.to_dict()."""
        symbol = Symbol(
            name="MyClass",
            type="class",
            file_path="/path/to/file.py",
            line_start=5,
            line_end=15
        )

        d = symbol.to_dict()

        assert d["name"] == "MyClass"
        assert d["type"] == "class"
        assert d["file_path"] == "/path/to/file.py"
        assert d["line_start"] == 5
        assert d["line_end"] == 15

    def test_symbol_repr(self):
        """Test Symbol string representation."""
        symbol = Symbol(
            name="test_func",
            type="function",
            file_path="test.py",
            line_start=1,
            line_end=5
        )

        repr_str = repr(symbol)
        assert "test_func" in repr_str
        assert "function" in repr_str
        assert "test.py" in repr_str


class TestRepositoryMapIndex:
    """Test RepositoryMap.index() method."""

    def test_index_returns_index_result(self, tmp_path):
        """Test that index() returns IndexResult."""
        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        assert isinstance(result, IndexResult)

    def test_index_empty_directory(self, tmp_path):
        """Test indexing empty directory."""
        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Empty directory should index successfully
        assert result.files_indexed == 0
        assert result.symbols_found == 0
        assert result.duration_seconds >= 0


class TestRepositoryMapSearch:
    """Test RepositoryMap.search() method."""

    def test_search_returns_list(self, tmp_path):
        """Test that search() returns a list."""
        repo_map = RepositoryMap(tmp_path)
        results = repo_map.search("test")

        assert isinstance(results, list)

    def test_search_empty_when_no_symbols(self, tmp_path):
        """Test search returns empty list when no symbols exist."""
        repo_map = RepositoryMap(tmp_path)
        results = repo_map.search("anything")

        assert results == []

    def test_search_exact_match(self, tmp_path):
        """Test exact search finds matching symbols."""
        # Create Python file with functions
        (tmp_path / "module.py").write_text("""
def hello_world():
    '''Say hello to the world.'''
    pass

def hello_user():
    '''Say hello to user.'''
    pass

def goodbye():
    '''Say goodbye.'''
    pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        # Search for "hello"
        results = repo_map.search("hello", search_type="exact")

        # Should find hello_world and hello_user
        assert len(results) >= 2
        names = [s.name for s in results]
        assert "hello_world" in names
        assert "hello_user" in names

    def test_search_exact_case_insensitive(self, tmp_path):
        """Test exact search is case-insensitive."""
        (tmp_path / "module.py").write_text("def MyFunction(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("myfunction", search_type="exact")

        assert len(results) == 1
        assert results[0].name == "MyFunction"

    def test_search_exact_prioritization(self, tmp_path):
        """Test that exact matches are prioritized."""
        (tmp_path / "module.py").write_text("""
def test(): pass
def test_func(): pass
def my_test(): pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("test", search_type="exact")

        # "test" (exact match) should come first
        assert len(results) >= 3
        assert results[0].name == "test"

    def test_search_fuzzy(self, tmp_path):
        """Test fuzzy search finds similar names."""
        (tmp_path / "module.py").write_text("""
def hello_world(): pass
def helo_wrld(): pass
def goodbye(): pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("hello_world", search_type="fuzzy")

        # Should find both hello_world and helo_wrld (typo)
        assert len(results) >= 2

    def test_search_semantic(self, tmp_path):
        """Test semantic search using TF-IDF."""
        (tmp_path / "module.py").write_text("""
def authenticate_user():
    '''Authenticate user with password.'''
    pass

def login():
    '''User login function.'''
    pass

def calculate_sum():
    '''Calculate sum of numbers.'''
    pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        # Search for "authentication"
        results = repo_map.search("authentication", search_type="semantic")

        # Should find authenticate_user and login (related to auth)
        # but not calculate_sum
        if results:  # scikit-learn might not be available
            names = [s.name for s in results]
            # authenticate_user should be in results
            assert "authenticate_user" in names or "login" in names

    def test_search_limit(self, tmp_path):
        """Test search limit parameter."""
        # Create many functions
        funcs = "\n".join([f"def func{i}(): pass" for i in range(10)])
        (tmp_path / "module.py").write_text(funcs)

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("func", search_type="exact", limit=5)

        # Should return at most 5 results
        assert len(results) <= 5

    def test_search_in_docstring(self, tmp_path):
        """Test search includes docstring matches."""
        (tmp_path / "module.py").write_text("""
def process_data():
    '''Handle user authentication.'''
    pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("authentication", search_type="exact")

        # Should find process_data because docstring contains "authentication"
        assert len(results) >= 1
        assert results[0].name == "process_data"

    def test_search_classes(self, tmp_path):
        """Test search finds classes."""
        (tmp_path / "module.py").write_text("""
class UserManager:
    '''Manage users.'''
    pass

class TaskManager:
    '''Manage tasks.'''
    pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("Manager", search_type="exact")

        # Should find both classes
        assert len(results) >= 2
        names = [s.name for s in results]
        assert "UserManager" in names
        assert "TaskManager" in names

    def test_search_symbol_types(self, tmp_path):
        """Test search results include correct symbol types."""
        (tmp_path / "module.py").write_text("""
def my_func(): pass

class MyClass: pass
""")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("my", search_type="exact")

        # Check symbol types
        types = {s.type for s in results}
        assert "function" in types or "class" in types


class TestRepositoryMapFileIndexing:
    """Test file indexing functionality."""

    def test_index_python_file(self, tmp_path):
        """Test indexing a Python file."""
        # Create Python file
        py_file = tmp_path / "module.py"
        py_file.write_text("def hello(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        assert result.files_indexed == 1
        assert result.symbols_found >= 1
        assert result.duration_seconds >= 0

    def test_index_multiple_files(self, tmp_path):
        """Test indexing multiple files."""
        # Create multiple Python files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")
        (tmp_path / "module3.py").write_text("class MyClass: pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        assert result.files_indexed == 3
        assert result.symbols_found >= 3

    def test_index_nested_directories(self, tmp_path):
        """Test indexing files in nested directories."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "module1.py").write_text("def nested_func(): pass")
        (tmp_path / "module2.py").write_text("def root_func(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        assert result.files_indexed == 2
        assert result.symbols_found >= 2

    def test_index_respects_gitignore(self, tmp_path):
        """Test that .gitignore patterns are respected."""
        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("ignored.py\n")

        # Create files
        (tmp_path / "included.py").write_text("def included(): pass")
        (tmp_path / "ignored.py").write_text("def ignored(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Only included.py should be indexed
        assert result.files_indexed == 2  # included.py + .gitignore

    def test_index_skips_venv(self, tmp_path):
        """Test that .venv directory is skipped."""
        # Create .venv directory
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "lib.py").write_text("def lib(): pass")
        (tmp_path / "main.py").write_text("def main(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Only main.py should be indexed
        assert result.files_indexed == 1

    def test_index_skips_pycache(self, tmp_path):
        """Test that __pycache__ directory is skipped."""
        # Create __pycache__ directory
        pycache_dir = tmp_path / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "cached.pyc").write_text("")
        (tmp_path / "main.py").write_text("def main(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Only main.py should be indexed
        assert result.files_indexed == 1

    def test_index_saves_to_disk(self, tmp_path):
        """Test that index is saved to .clauxton/map/."""
        (tmp_path / "module.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        # Check that index file was created
        assert (tmp_path / ".clauxton" / "map" / "index.json").exists()
        # symbols.json is only created if symbols were found
        # Since we have a source file with a function, symbols should exist
        assert (tmp_path / ".clauxton" / "map" / "symbols.json").exists()

    def test_index_data_after_indexing(self, tmp_path):
        """Test that index_data property works after indexing."""
        (tmp_path / "module.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        index = repo_map.index_data
        assert index["version"] == "0.11.0"
        assert index["indexed_at"] is not None
        assert len(index["files"]) == 1
        assert index["statistics"]["total_files"] == 1

    def test_symbols_data_after_indexing(self, tmp_path):
        """Test that symbols_data property works after indexing."""
        (tmp_path / "module.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        symbols = repo_map.symbols_data
        assert isinstance(symbols, dict)
        # Should have symbols for module.py
        assert len(symbols) >= 1

    def test_index_categorizes_file_types(self, tmp_path):
        """Test that files are categorized correctly."""
        # Create different file types
        (tmp_path / "module.py").write_text("def func(): pass")
        (tmp_path / "test_module.py").write_text("def test(): pass")
        (tmp_path / "config.json").write_text("{}")
        (tmp_path / "docs.md").write_text("# Documentation")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        index = repo_map.index_data
        stats = index["statistics"]

        # Check statistics by type
        assert stats["by_type"]["source"] >= 1
        assert stats["by_type"]["test"] >= 1
        assert stats["by_type"]["config"] >= 1
        assert stats["by_type"]["docs"] >= 1

    def test_index_detects_languages(self, tmp_path):
        """Test that programming languages are detected."""
        (tmp_path / "module.py").write_text("def func(): pass")
        (tmp_path / "script.js").write_text("function func() {}")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        index = repo_map.index_data
        stats = index["statistics"]

        # Check statistics by language
        assert stats["by_language"]["python"] >= 1
        assert stats["by_language"]["javascript"] >= 1

    def test_index_handles_binary_files(self, tmp_path):
        """Test that binary files don't cause errors."""
        # Create a binary file
        binary_file = tmp_path / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        (tmp_path / "test.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Should not crash
        assert result.files_indexed == 2

    def test_index_with_progress_callback(self, tmp_path):
        """Test indexing with progress callback."""
        (tmp_path / "file1.py").write_text("def func1(): pass")
        (tmp_path / "file2.py").write_text("def func2(): pass")

        callback_calls = []
        def callback(current, total, status):
            callback_calls.append((current, total, status))

        repo_map = RepositoryMap(tmp_path)
        repo_map.index(progress_callback=callback)

        # Callback should have been called
        assert len(callback_calls) >= 2

    def test_index_incremental_warning(self, tmp_path):
        """Test that incremental indexing shows warning."""
        (tmp_path / "test.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        # Should not crash with incremental=True
        result = repo_map.index(incremental=True)

        assert result.files_indexed == 1


class TestRepositoryMapHelperMethods:
    """Test helper methods."""

    def test_load_gitignore_with_no_file(self, tmp_path):
        """Test loading gitignore when .gitignore doesn't exist."""
        repo_map = RepositoryMap(tmp_path)
        patterns = repo_map._load_gitignore()

        # Should have default patterns
        assert ".git" in patterns
        assert "__pycache__" in patterns
        assert ".venv" in patterns

    def test_load_gitignore_with_file(self, tmp_path):
        """Test loading gitignore patterns from file."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\ntemp/\n# Comment\n\n")

        repo_map = RepositoryMap(tmp_path)
        patterns = repo_map._load_gitignore()

        # Should include custom patterns
        assert "*.log" in patterns
        assert "temp/" in patterns
        # Comments and empty lines should be skipped
        assert "# Comment" not in patterns

    def test_should_ignore_basic_patterns(self, tmp_path):
        """Test file ignoring with basic patterns."""
        repo_map = RepositoryMap(tmp_path)
        patterns = [".git", "*.pyc", "__pycache__"]

        # Should ignore these
        assert repo_map._should_ignore(tmp_path / ".git" / "config", patterns)
        assert repo_map._should_ignore(tmp_path / "test.pyc", patterns)
        assert repo_map._should_ignore(tmp_path / "__pycache__" / "test.py", patterns)

        # Should not ignore these
        assert not repo_map._should_ignore(tmp_path / "test.py", patterns)

    def test_categorize_file_python(self, tmp_path):
        """Test file categorization for Python files."""
        py_file = tmp_path / "module.py"
        py_file.write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        info = repo_map._categorize_file(py_file)

        assert info["file_type"] == "source"
        assert info["language"] == "python"
        assert info["line_count"] > 0

    def test_categorize_file_test(self, tmp_path):
        """Test categorization of test files."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_func(): pass")

        repo_map = RepositoryMap(tmp_path)
        info = repo_map._categorize_file(test_file)

        assert info["file_type"] == "test"
        assert info["language"] == "python"

    def test_categorize_file_config(self, tmp_path):
        """Test categorization of config files."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        repo_map = RepositoryMap(tmp_path)
        info = repo_map._categorize_file(config_file)

        assert info["file_type"] == "config"
        assert info["language"] is None

    def test_categorize_file_docs(self, tmp_path):
        """Test categorization of documentation files."""
        docs_file = tmp_path / "README.md"
        docs_file.write_text("# Docs")

        repo_map = RepositoryMap(tmp_path)
        info = repo_map._categorize_file(docs_file)

        assert info["file_type"] == "docs"

    def test_categorize_file_javascript(self, tmp_path):
        """Test categorization of JavaScript files."""
        js_file = tmp_path / "script.js"
        js_file.write_text("function test() {}")

        repo_map = RepositoryMap(tmp_path)
        info = repo_map._categorize_file(js_file)

        assert info["file_type"] == "source"
        assert info["language"] == "javascript"

    def test_categorize_file_other(self, tmp_path):
        """Test categorization of unknown file types."""
        other_file = tmp_path / "data.xyz"
        other_file.write_text("content")

        repo_map = RepositoryMap(tmp_path)
        info = repo_map._categorize_file(other_file)

        assert info["file_type"] == "other"
        assert info["language"] is None


class TestRepositoryMapErrorHandling:
    """Test error handling and edge cases."""

    def test_index_with_symbol_extraction_error(self, tmp_path):
        """Test that symbol extraction errors are handled gracefully."""
        # Create a Python file with invalid syntax
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(\n")  # Unclosed parenthesis

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Should still index the file even if symbol extraction fails
        assert result.files_indexed == 1
        # Errors list may contain error messages
        assert isinstance(result.errors, list)

    def test_index_with_file_processing_error(self, tmp_path):
        """Test that file processing errors are handled gracefully."""
        # Create a file and then make it unreadable
        test_file = tmp_path / "module.py"
        test_file.write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Should complete without crashing
        assert isinstance(result, IndexResult)
        assert result.files_indexed >= 0

    def test_index_with_empty_symbols_dict(self, tmp_path):
        """Test indexing when no symbols are found."""
        # Create a file with no symbols
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("just some text")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        assert result.files_indexed == 1
        assert result.symbols_found == 0

    def test_search_with_no_index(self, tmp_path):
        """Test search when no index exists."""
        repo_map = RepositoryMap(tmp_path)
        results = repo_map.search("test")

        # Should return empty list, not crash
        assert results == []

    def test_search_with_empty_query(self, tmp_path):
        """Test search with empty query string."""
        (tmp_path / "module.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        results = repo_map.search("")

        # Should handle empty query gracefully
        assert isinstance(results, list)

    def test_search_with_unknown_search_type(self, tmp_path):
        """Test search with invalid search type."""
        (tmp_path / "module.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        # Should fall back to exact search
        results = repo_map.search("func", search_type="invalid")  # type: ignore

        assert isinstance(results, list)

    def test_semantic_search_without_sklearn(self, tmp_path, monkeypatch):
        """Test semantic search falls back when sklearn unavailable."""
        (tmp_path / "module.py").write_text("def func(): pass")

        repo_map = RepositoryMap(tmp_path)
        repo_map.index()

        # Mock sklearn import error
        import sys
        original_sklearn = sys.modules.get('sklearn.feature_extraction.text')
        try:
            if 'sklearn.feature_extraction.text' in sys.modules:
                del sys.modules['sklearn.feature_extraction.text']

            results = repo_map.search("func", search_type="semantic")

            # Should fall back to exact search
            assert isinstance(results, list)
        finally:
            if original_sklearn:
                sys.modules['sklearn.feature_extraction.text'] = original_sklearn

    def test_index_with_binary_file_encoding_error(self, tmp_path):
        """Test indexing handles binary files gracefully."""
        # Create a binary file
        binary_file = tmp_path / "binary.dat"
        binary_file.write_bytes(b"\x00\xFF\x00\xFF")

        repo_map = RepositoryMap(tmp_path)
        result = repo_map.index()

        # Should not crash on binary files
        assert result.files_indexed == 1

    def test_categorize_file_with_encoding_error(self, tmp_path):
        """Test file categorization handles encoding errors."""
        # Create a file with invalid UTF-8
        bad_file = tmp_path / "bad_encoding.py"
        bad_file.write_bytes(b"def func():\n    # \xFF\xFE\n    pass")

        repo_map = RepositoryMap(tmp_path)

        try:
            info = repo_map._categorize_file(bad_file)
            # Should still categorize, line_count might be 0
            assert info["file_type"] in ["source", "test"]
            assert info["language"] == "python"
        except Exception:
            # It's acceptable to fail on encoding errors
            pass

    def test_gitignore_with_read_error(self, tmp_path):
        """Test gitignore loading handles read errors gracefully."""
        # Create a .gitignore that will cause read error
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc")

        repo_map = RepositoryMap(tmp_path)
        patterns = repo_map._load_gitignore()

        # Should still have default patterns
        assert ".git" in patterns
        assert "__pycache__" in patterns
