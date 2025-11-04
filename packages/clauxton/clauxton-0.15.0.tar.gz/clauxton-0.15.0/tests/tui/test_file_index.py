"""Tests for File Index Cache (services/file_index.py)."""

import time
from pathlib import Path

from clauxton.tui.services.file_index import FileIndexCache


class TestFileIndexCache:
    """Test suite for FileIndexCache."""

    def test_cache_initialization(self, tmp_path: Path) -> None:
        """Test cache initializes correctly."""
        cache = FileIndexCache(tmp_path, ttl=60)

        assert cache.project_root == tmp_path
        assert cache.ttl == 60
        assert len(cache.extensions) > 0

    def test_cache_indexes_files_on_first_access(self, tmp_path: Path) -> None:
        """Test cache indexes files on first access."""
        # Create test files
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / "test.md").write_text("# Test")

        cache = FileIndexCache(tmp_path, ttl=60)
        files = cache.get_all_files()

        assert len(files) >= 2
        assert any(f.name == "test.py" for f in files)
        assert any(f.name == "test.md" for f in files)

    def test_cache_excludes_directories(self, tmp_path: Path) -> None:
        """Test cache excludes specified directories."""
        # Create files in excluded directory
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "test.py").write_text("excluded")

        # Create file in included directory
        (tmp_path / "included.py").write_text("included")

        cache = FileIndexCache(tmp_path, ttl=60)
        files = cache.get_all_files()

        # Should only include files not in excluded dirs
        file_names = [f.name for f in files]
        assert "included.py" in file_names
        assert "test.py" not in file_names  # Excluded

    def test_cache_search_returns_matching_files(self, tmp_path: Path) -> None:
        """Test search returns files matching query."""
        # Create test files
        (tmp_path / "foo_test.py").write_text("test")
        (tmp_path / "bar_test.py").write_text("test")
        (tmp_path / "unrelated.py").write_text("code")

        cache = FileIndexCache(tmp_path, ttl=60)
        results = cache.search("test")

        assert len(results) == 2
        file_names = [f.name for f in results]
        assert "foo_test.py" in file_names
        assert "bar_test.py" in file_names

    def test_cache_search_case_insensitive(self, tmp_path: Path) -> None:
        """Test search is case-insensitive."""
        (tmp_path / "MyFile.py").write_text("code")

        cache = FileIndexCache(tmp_path, ttl=60)
        results = cache.search("myfile")

        assert len(results) == 1
        assert results[0].name == "MyFile.py"

    def test_cache_search_respects_limit(self, tmp_path: Path) -> None:
        """Test search respects result limit."""
        # Create many files
        for i in range(10):
            (tmp_path / f"test_{i}.py").write_text("code")

        cache = FileIndexCache(tmp_path, ttl=60)
        results = cache.search("test", limit=5)

        assert len(results) == 5

    def test_cache_find_by_name(self, tmp_path: Path) -> None:
        """Test finding file by exact name."""
        test_file = tmp_path / "unique_file.py"
        test_file.write_text("code")

        cache = FileIndexCache(tmp_path, ttl=60)
        found = cache.find_by_name("unique_file.py")

        assert found is not None
        assert found.name == "unique_file.py"

    def test_cache_find_by_name_returns_none_if_not_found(
        self, tmp_path: Path
    ) -> None:
        """Test find_by_name returns None if file not found."""
        cache = FileIndexCache(tmp_path, ttl=60)
        found = cache.find_by_name("nonexistent.py")

        assert found is None

    def test_cache_ttl_expiration(self, tmp_path: Path) -> None:
        """Test cache expires after TTL."""
        (tmp_path / "test.py").write_text("code")

        # Create cache with very short TTL
        cache = FileIndexCache(tmp_path, ttl=1)

        # First access - should index
        files1 = cache.get_all_files()
        assert len(files1) >= 1

        # Wait for TTL to expire
        time.sleep(1.1)

        # Add new file
        (tmp_path / "new.py").write_text("new code")

        # Second access - should re-index
        files2 = cache.get_all_files()
        assert len(files2) > len(files1)

    def test_cache_invalidation(self, tmp_path: Path) -> None:
        """Test manual cache invalidation."""
        (tmp_path / "test.py").write_text("code")

        cache = FileIndexCache(tmp_path, ttl=3600)  # Long TTL

        # First access
        files1 = cache.get_all_files()
        assert len(files1) >= 1

        # Invalidate cache
        cache.invalidate()

        # Add new file
        (tmp_path / "new.py").write_text("new code")

        # Second access - should re-index despite long TTL
        files2 = cache.get_all_files()
        assert len(files2) > len(files1)

    def test_cache_stats(self, tmp_path: Path) -> None:
        """Test cache statistics."""
        (tmp_path / "test.py").write_text("code")

        cache = FileIndexCache(tmp_path, ttl=60)
        cache.get_all_files()  # Trigger indexing

        stats = cache.get_stats()

        assert "file_count" in stats
        assert "cache_age_seconds" in stats
        assert "is_fresh" in stats
        assert "ttl_seconds" in stats
        assert stats["file_count"] >= 1
        assert stats["is_fresh"] is True

    def test_cache_custom_extensions(self, tmp_path: Path) -> None:
        """Test cache with custom file extensions."""
        (tmp_path / "test.py").write_text("code")
        (tmp_path / "test.txt").write_text("text")

        # Cache only .txt files
        cache = FileIndexCache(tmp_path, ttl=60, extensions=[".txt"])
        files = cache.get_all_files()

        file_names = [f.name for f in files]
        assert "test.txt" in file_names
        assert "test.py" not in file_names

    def test_cache_nested_directories(self, tmp_path: Path) -> None:
        """Test cache indexes nested directories."""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "src" / "utils").mkdir()
        (tmp_path / "src" / "utils" / "helper.py").write_text("helper")

        cache = FileIndexCache(tmp_path, ttl=60)
        files = cache.get_all_files()

        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "helper.py" in file_names

    def test_cache_empty_project(self, tmp_path: Path) -> None:
        """Test cache handles empty project."""
        cache = FileIndexCache(tmp_path, ttl=60)
        files = cache.get_all_files()

        assert isinstance(files, list)
        assert len(files) == 0

    def test_cache_search_empty_query(self, tmp_path: Path) -> None:
        """Test search with empty query returns all files."""
        (tmp_path / "test.py").write_text("code")

        cache = FileIndexCache(tmp_path, ttl=60)
        results = cache.search("", limit=100)

        # Empty query should still return results
        # (since empty string is in all paths)
        assert len(results) >= 1
