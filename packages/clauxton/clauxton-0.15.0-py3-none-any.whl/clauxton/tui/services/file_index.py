"""
File Index Cache Service.

Provides fast file lookups with caching to avoid repeated filesystem scans.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class FileIndexCache:
    """
    File index cache for fast file searches.

    Caches file lists to avoid repeated filesystem scans.
    """

    def __init__(
        self,
        project_root: Path,
        ttl: int = 300,  # 5 minutes
        extensions: List[str] | None = None,
    ) -> None:
        """
        Initialize file index cache.

        Args:
            project_root: Project root directory
            ttl: Cache TTL in seconds
            extensions: File extensions to index (default: common code files)
        """
        self.project_root = project_root
        self.ttl = ttl
        self.extensions = extensions or [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".md",
            ".yml",
            ".yaml",
            ".json",
            ".toml",
        ]

        # Cache storage
        self._file_list: List[Path] = []
        self._file_map: Dict[str, Path] = {}  # filename -> path
        self._last_indexed: float = 0.0

        # Excluded directories
        self._exclude_dirs: Set[str] = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            "dist",
            "build",
            ".egg-info",
        }

    def _should_refresh(self) -> bool:
        """Check if cache should be refreshed."""
        if not self._file_list:
            return True
        elapsed = time.time() - self._last_indexed
        return elapsed > self.ttl

    def _is_excluded(self, path: Path) -> bool:
        """
        Check if path should be excluded.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded
        """
        parts = path.parts
        return any(excluded in parts for excluded in self._exclude_dirs)

    def _index_files(self) -> None:
        """Index files in project."""
        logger.debug(f"Indexing files in {self.project_root}")
        start_time = time.time()

        self._file_list = []
        self._file_map = {}

        for ext in self.extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if not self._is_excluded(file_path):
                    self._file_list.append(file_path)
                    self._file_map[file_path.name] = file_path

        self._last_indexed = time.time()

        elapsed = time.time() - start_time
        logger.debug(
            f"Indexed {len(self._file_list)} files in {elapsed:.2f}s "
            f"(TTL: {self.ttl}s)"
        )

    def get_all_files(self) -> List[Path]:
        """
        Get all indexed files.

        Returns:
            List of file paths
        """
        if self._should_refresh():
            self._index_files()
        return self._file_list.copy()

    def search(self, query: str, limit: int = 100) -> List[Path]:
        """
        Search for files matching query.

        Args:
            query: Search query (case-insensitive)
            limit: Maximum results

        Returns:
            List of matching file paths
        """
        if self._should_refresh():
            self._index_files()

        query_lower = query.lower()
        results = []

        for file_path in self._file_list:
            # Search in relative path
            rel_path = str(file_path.relative_to(self.project_root)).lower()
            if query_lower in rel_path:
                results.append(file_path)
                if len(results) >= limit:
                    break

        return results

    def find_by_name(self, filename: str) -> Path | None:
        """
        Find file by exact name.

        Args:
            filename: File name to find

        Returns:
            File path if found, None otherwise
        """
        if self._should_refresh():
            self._index_files()

        return self._file_map.get(filename)

    def invalidate(self) -> None:
        """Invalidate cache (force refresh on next access)."""
        self._last_indexed = 0.0
        logger.debug("File index cache invalidated")

    def get_stats(self) -> Dict[str, int | float]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        age = time.time() - self._last_indexed if self._last_indexed > 0 else 0
        return {
            "file_count": len(self._file_list),
            "cache_age_seconds": age,
            "is_fresh": not self._should_refresh(),
            "ttl_seconds": self.ttl,
        }
