"""
Repository Map for automatic codebase indexing.

This module provides automatic understanding of codebase structure through:
- File structure indexing (respects .gitignore)
- Symbol extraction (functions, classes, methods)
- Dependency graph building
- Semantic search over code

Example:
    >>> from clauxton.intelligence import RepositoryMap
    >>> repo_map = RepositoryMap(".")
    >>> result = repo_map.index()
    >>> print(f"Indexed {result.files_indexed} files")
    >>> symbols = repo_map.search("authentication")
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional

from clauxton.core.models import ClauxtonError

logger = logging.getLogger(__name__)


class RepositoryMapError(ClauxtonError):
    """Base error for repository map operations."""
    pass


class IndexResult:
    """Result of indexing operation."""

    def __init__(
        self,
        files_indexed: int,
        symbols_found: int,
        duration_seconds: float,
        by_type: Optional[Dict[str, int]] = None,
        by_language: Optional[Dict[str, int]] = None,
        indexed_at: Optional[datetime] = None,
        errors: Optional[List[str]] = None,
        missing_parsers: Optional[Dict[str, int]] = None
    ):
        """
        Initialize index result.

        Args:
            files_indexed: Number of files successfully indexed
            symbols_found: Number of symbols extracted
            duration_seconds: Time taken for indexing
            by_type: Breakdown of files by type (source/test/config/docs/other)
            by_language: Breakdown of files by language
            indexed_at: Timestamp of indexing
            errors: List of error messages (if any)
            missing_parsers: Languages with missing parsers (language: file_count)
        """
        self.files_indexed = files_indexed
        self.symbols_found = symbols_found
        self.duration_seconds = duration_seconds
        self.by_type = by_type or {}
        self.by_language = by_language or {}
        self.indexed_at = indexed_at or datetime.now()
        self.errors = errors or []
        self.missing_parsers = missing_parsers or {}

    def __repr__(self) -> str:
        return (
            f"IndexResult(files={self.files_indexed}, "
            f"symbols={self.symbols_found}, "
            f"duration={self.duration_seconds:.2f}s)"
        )


class FileNode:
    """Represents a file in the repository."""

    def __init__(
        self,
        path: Path,
        relative_path: str,
        file_type: str,
        language: Optional[str],
        size_bytes: int,
        line_count: int,
        last_modified: datetime,
    ):
        """Initialize file node."""
        self.path = path
        self.relative_path = relative_path
        self.file_type = file_type
        self.language = language
        self.size_bytes = size_bytes
        self.line_count = line_count
        self.last_modified = last_modified

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "relative_path": self.relative_path,
            "file_type": self.file_type,
            "language": self.language,
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "last_modified": self.last_modified.isoformat(),
        }


class Symbol:
    """Represents a code symbol (function, class, etc.)."""

    def __init__(
        self,
        name: str,
        type: str,
        file_path: str,
        line_start: int,
        line_end: int,
        docstring: Optional[str] = None,
        signature: Optional[str] = None,
    ):
        """Initialize symbol."""
        self.name = name
        self.type = type
        self.file_path = file_path
        self.line_start = line_start
        self.line_end = line_end
        self.docstring = docstring
        self.signature = signature

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
            "signature": self.signature,
        }

    def __repr__(self) -> str:
        return f"Symbol({self.name}, {self.type}, {self.file_path}:{self.line_start})"


class RepositoryMap:
    """
    Indexes and queries codebase structure.

    This class provides automatic codebase understanding through file indexing
    and symbol extraction. It creates a searchable map of your code.

    Usage:
        >>> repo_map = RepositoryMap(Path("."))
        >>> result = repo_map.index()
        >>> print(f"Found {result.symbols_found} symbols")
        >>>
        >>> # Search for symbols
        >>> results = repo_map.search("create_user")
        >>> for symbol in results:
        ...     print(f"{symbol.name} at {symbol.file_path}:{symbol.line_start}")

    Attributes:
        root_dir: Project root directory
        map_dir: Directory where index data is stored (.clauxton/map/)
    """

    def __init__(self, root_dir: Path | str):
        """
        Initialize repository map at root_dir.

        Args:
            root_dir: Project root directory (Path or str)

        Raises:
            RepositoryMapError: If root_dir doesn't exist
        """
        self.root_dir = Path(root_dir) if isinstance(root_dir, str) else root_dir

        if not self.root_dir.exists():
            raise RepositoryMapError(f"Root directory does not exist: {self.root_dir}")

        # Ensure .clauxton directory exists
        clauxton_dir = self.root_dir / ".clauxton"
        clauxton_dir.mkdir(parents=True, exist_ok=True)

        # Map data directory
        self.map_dir = clauxton_dir / "map"
        self.map_dir.mkdir(parents=True, exist_ok=True)

        # Lazy-loaded data
        self._index: Optional[Dict] = None
        self._symbols: Optional[Dict] = None

        logger.debug(f"RepositoryMap initialized at {self.root_dir}")

    def index(
        self,
        incremental: bool = False,
        progress_callback: Optional[Callable[[int, Optional[int], str], None]] = None
    ) -> IndexResult:
        """
        Index the codebase.

        Scans all files in the repository, extracts symbols from source files,
        and builds an index for fast searching.

        Args:
            incremental: If True, only index changed files (not implemented yet)
            progress_callback: Optional callback (current, total, status) -> None

        Returns:
            IndexResult with statistics
        """
        import time

        logger.info(f"Starting indexing of {self.root_dir}")
        start_time = time.time()

        if incremental:
            logger.warning("Incremental indexing not yet implemented, doing full index")

        # Load gitignore patterns
        gitignore_patterns = self._load_gitignore()
        logger.debug(f"Loaded {len(gitignore_patterns)} gitignore patterns")

        # Scan all files
        files_indexed = 0
        symbols_found = 0
        errors = []
        all_files = []
        by_type: Dict[str, int] = {}
        by_language: Dict[str, int] = {}
        missing_parsers: Dict[str, int] = {}  # Track missing parsers

        from clauxton.intelligence.symbol_extractor import SymbolExtractor
        symbol_extractor = SymbolExtractor()

        # Collect all files
        for file_path in self.root_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Check if should ignore
            if self._should_ignore(file_path, gitignore_patterns):
                continue

            # Categorize file
            try:
                file_info = self._categorize_file(file_path)
                all_files.append(file_info)
                files_indexed += 1

                # Track statistics
                file_type = file_info["file_type"]
                language = file_info["language"]
                by_type[file_type] = by_type.get(file_type, 0) + 1
                if language:
                    by_language[language] = by_language.get(language, 0) + 1

                # Extract symbols from source files
                if file_info["file_type"] == "source" and file_info["language"]:
                    try:
                        symbols = symbol_extractor.extract(
                            file_path,
                            file_info["language"]
                        )

                        # Check if parser is available
                        if symbols is None:
                            # Parser not available for this language
                            lang = file_info["language"]
                            missing_parsers[lang] = missing_parsers.get(lang, 0) + 1
                        else:
                            symbols_found += len(symbols)
                            # Store symbols
                            if symbols:
                                self._store_symbols(file_path, symbols)

                    except Exception as e:
                        error_msg = f"Error extracting symbols from {file_path}: {e}"
                        logger.warning(error_msg)
                        errors.append(error_msg)

                # Progress callback
                if progress_callback:
                    progress_callback(files_indexed, None, f"Indexing {file_path.name}")

            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

        # Save index to disk
        self._save_index(all_files)

        duration = time.time() - start_time
        indexed_at = datetime.now()
        logger.info(
            f"Indexing complete: {files_indexed} files, "
            f"{symbols_found} symbols in {duration:.2f}s"
        )

        return IndexResult(
            files_indexed=files_indexed,
            symbols_found=symbols_found,
            duration_seconds=duration,
            by_type=by_type,
            by_language=by_language,
            indexed_at=indexed_at,
            errors=errors,
            missing_parsers=missing_parsers
        )

    def search(
        self,
        query: str,
        search_type: Literal["semantic", "exact", "fuzzy"] = "exact",
        limit: int = 20
    ) -> List[Symbol]:
        """
        Search codebase for symbols.

        Args:
            query: Search query (symbol name or pattern)
            search_type: Search algorithm to use
                - "exact": Exact substring match (default)
                - "fuzzy": Fuzzy matching (typo-tolerant)
                - "semantic": TF-IDF semantic search
            limit: Maximum number of results to return

        Returns:
            List of matching symbols, ranked by relevance
        """
        logger.info(f"Searching for '{query}' with {search_type} search")

        # Load symbols data
        symbols_data = self.symbols_data
        if not symbols_data:
            logger.debug("No symbols available for search")
            return []

        # Collect all symbols
        all_symbols: List[Symbol] = []
        for file_path, file_symbols in symbols_data.items():
            for symbol_dict in file_symbols:
                symbol = Symbol(
                    name=symbol_dict["name"],
                    type=symbol_dict["type"],
                    file_path=symbol_dict["file_path"],
                    line_start=symbol_dict["line_start"],
                    line_end=symbol_dict["line_end"],
                    docstring=symbol_dict.get("docstring"),
                    signature=symbol_dict.get("signature"),
                )
                all_symbols.append(symbol)

        logger.debug(f"Searching through {len(all_symbols)} symbols")

        # Perform search based on type
        if search_type == "exact":
            results = self._exact_search(query, all_symbols)
        elif search_type == "fuzzy":
            results = self._fuzzy_search(query, all_symbols)
        elif search_type == "semantic":
            results = self._semantic_search(query, all_symbols)
        else:
            logger.warning(f"Unknown search type: {search_type}, using exact")
            results = self._exact_search(query, all_symbols)

        # Apply limit
        limited_results = results[:limit]
        logger.info(f"Found {len(results)} results, returning {len(limited_results)}")

        return limited_results

    def _exact_search(self, query: str, symbols: List[Symbol]) -> List[Symbol]:
        """
        Exact substring search (case-insensitive).

        Args:
            query: Search query
            symbols: List of symbols to search

        Returns:
            Matching symbols, sorted by relevance
        """
        query_lower = query.lower()
        results = []

        for symbol in symbols:
            name_lower = symbol.name.lower()

            # Exact match (highest priority)
            if name_lower == query_lower:
                results.append((symbol, 100))
            # Starts with query (high priority)
            elif name_lower.startswith(query_lower):
                results.append((symbol, 90))
            # Contains query (medium priority)
            elif query_lower in name_lower:
                results.append((symbol, 50))
            # Search in docstring if available
            elif symbol.docstring and query_lower in symbol.docstring.lower():
                results.append((symbol, 30))

        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return [symbol for symbol, score in results]

    def _fuzzy_search(self, query: str, symbols: List[Symbol]) -> List[Symbol]:
        """
        Fuzzy search using Levenshtein distance.

        Args:
            query: Search query
            symbols: List of symbols to search

        Returns:
            Matching symbols, sorted by similarity
        """
        import difflib

        query_lower = query.lower()
        results = []

        for symbol in symbols:
            name_lower = symbol.name.lower()

            # Calculate similarity ratio (0-1)
            ratio = difflib.SequenceMatcher(None, query_lower, name_lower).ratio()

            # Only include if similarity > 0.4
            if ratio > 0.4:
                results.append((symbol, ratio))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return [symbol for symbol, score in results]

    def _semantic_search(self, query: str, symbols: List[Symbol]) -> List[Symbol]:
        """
        Semantic search using TF-IDF.

        Args:
            query: Search query
            symbols: List of symbols to search

        Returns:
            Matching symbols, sorted by relevance
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # Prepare documents (symbol names + docstrings)
            documents = []
            for symbol in symbols:
                doc = symbol.name
                if symbol.docstring:
                    doc += " " + symbol.docstring
                documents.append(doc)

            if not documents:
                return []

            # Create TF-IDF matrix
            vectorizer = TfidfVectorizer(lowercase=True, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(documents + [query])

            # Calculate cosine similarity
            query_vector = tfidf_matrix[-1]
            doc_vectors = tfidf_matrix[:-1]
            similarities = cosine_similarity(query_vector, doc_vectors)[0]

            # Create results with scores
            results = []
            for symbol, score in zip(symbols, similarities):
                if score > 0.01:  # Threshold for relevance
                    results.append((symbol, score))

            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)

            return [symbol for symbol, score in results]

        except ImportError:
            logger.warning("scikit-learn not available, falling back to exact search")
            return self._exact_search(query, symbols)

    @property
    def index_data(self) -> Dict:
        """
        Lazy load index data from disk.

        Returns:
            Index data dictionary with file information
        """
        if self._index is None:
            index_file = self.map_dir / "index.json"
            if index_file.exists():
                logger.debug(f"Loading index from {index_file}")
                with open(index_file) as f:
                    self._index = json.load(f)
            else:
                logger.debug("No index file found, returning empty index")
                self._index = {
                    "version": "0.11.0",
                    "indexed_at": None,
                    "root_path": str(self.root_dir),
                    "files": [],
                    "statistics": {
                        "total_files": 0,
                        "by_type": {},
                        "by_language": {},
                    }
                }
        return self._index

    @property
    def symbols_data(self) -> Dict:
        """
        Lazy load symbols data from disk.

        Returns:
            Symbols data dictionary mapping file paths to symbol lists
        """
        if self._symbols is None:
            symbols_file = self.map_dir / "symbols.json"
            if symbols_file.exists():
                logger.debug(f"Loading symbols from {symbols_file}")
                with open(symbols_file) as f:
                    self._symbols = json.load(f)
            else:
                logger.debug("No symbols file found, returning empty dict")
                self._symbols = {}
        return self._symbols

    def clear_cache(self) -> None:
        """Clear in-memory cache, forcing reload from disk."""
        self._index = None
        self._symbols = None
        logger.debug("Cache cleared")

    # Helper methods for indexing

    def _load_gitignore(self) -> List[str]:
        """
        Load .gitignore patterns.

        Returns:
            List of patterns to ignore
        """

        # Default patterns
        patterns = [
            ".git", ".git/*",
            "__pycache__", "__pycache__/*", "*.pyc", "*.pyo",
            ".venv", ".venv/*", "venv", "venv/*",
            "node_modules", "node_modules/*",
            ".DS_Store",
            "*.egg-info", "*.egg-info/*",
            ".clauxton", ".clauxton/*",
            "htmlcov", "htmlcov/*",
            ".coverage",
            "dist", "dist/*",
            "build", "build/*",
        ]

        # Load from .gitignore
        gitignore_file = self.root_dir / ".gitignore"
        if gitignore_file.exists():
            try:
                with open(gitignore_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
                            # Also add pattern with /*
                            if not line.endswith("*") and not line.endswith("/"):
                                patterns.append(f"{line}/*")
            except Exception as e:
                logger.warning(f"Error reading .gitignore: {e}")

        return patterns

    def _should_ignore(self, file_path: Path, patterns: List[str]) -> bool:
        """
        Check if file should be ignored based on patterns.

        Args:
            file_path: Path to check
            patterns: List of gitignore patterns

        Returns:
            True if file should be ignored
        """
        import fnmatch

        try:
            relative = file_path.relative_to(self.root_dir)
            path_str = str(relative)
        except ValueError:
            # File is not relative to root
            return True

        # Check against patterns
        for pattern in patterns:
            # Try direct match
            if fnmatch.fnmatch(path_str, pattern):
                return True

            # Try matching any part of the path
            parts = path_str.split("/")
            for part in parts:
                if fnmatch.fnmatch(part, pattern.rstrip("/*")):
                    return True

        return False

    def _categorize_file(self, file_path: Path) -> Dict:
        """
        Categorize file by type and detect language.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        suffix = file_path.suffix.lower()

        # Language detection
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cs": "csharp",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        language = language_map.get(suffix)

        # File type detection
        # Only consider it a test file if filename contains "test", not just the path
        filename = file_path.name.lower()
        if filename.startswith("test_") or filename.endswith("_test.py") or filename == "test.py":
            file_type = "test"
        elif suffix in [".md", ".rst", ".txt", ".adoc"]:
            file_type = "docs"
        elif suffix in [".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf"]:
            file_type = "config"
        elif language:
            file_type = "source"
        else:
            file_type = "other"

        # Get file stats
        stat = file_path.stat()
        line_count = 0

        if file_type in ["source", "test"]:
            try:
                with open(file_path, encoding="utf-8") as f:
                    line_count = len(f.readlines())
            except Exception:
                # Binary file or encoding error
                line_count = 0

        return {
            "path": str(file_path),
            "relative_path": str(file_path.relative_to(self.root_dir)),
            "file_type": file_type,
            "language": language,
            "size_bytes": stat.st_size,
            "line_count": line_count,
            "last_modified": stat.st_mtime,
        }

    def _store_symbols(self, file_path: Path, symbols: List[Dict]) -> None:
        """
        Store symbols for a file.

        Args:
            file_path: Path to file
            symbols: List of extracted symbols
        """
        # Get or create symbols dict
        if self._symbols is None:
            self._symbols = {}

        relative_path = str(file_path.relative_to(self.root_dir))
        self._symbols[relative_path] = symbols

    def _save_index(self, files: List[Dict]) -> None:
        """
        Save index to disk.

        Args:
            files: List of file information dictionaries
        """
        # Calculate statistics
        by_type: Dict[str, int] = {}
        by_language: Dict[str, int] = {}

        for file_info in files:
            file_type = file_info["file_type"]
            language = file_info["language"]

            by_type[file_type] = by_type.get(file_type, 0) + 1
            if language:
                by_language[language] = by_language.get(language, 0) + 1

        stats = {
            "total_files": len(files),
            "by_type": by_type,
            "by_language": by_language,
        }

        # Create index data
        index_data = {
            "version": "0.11.0",
            "indexed_at": datetime.now().isoformat(),
            "root_path": str(self.root_dir),
            "files": files,
            "statistics": stats,
        }

        # Write to disk
        index_file = self.map_dir / "index.json"
        with open(index_file, "w") as f:
            json.dump(index_data, f, indent=2)

        self._index = index_data
        logger.debug(f"Index saved to {index_file}")

        # Save symbols if any
        if self._symbols:
            symbols_file = self.map_dir / "symbols.json"
            with open(symbols_file, "w") as f:
                json.dump(self._symbols, f, indent=2)
            logger.debug(f"Symbols saved to {symbols_file}")
