"""
Semantic search engine for KB, tasks, and code files.

This module provides semantic search capabilities using embeddings and vector similarity:
- Search Knowledge Base entries by semantic meaning
- Search tasks by description similarity
- Search code files by content relevance
- Unified search across all sources
- Filtering by metadata (category, status, priority, etc.)
- Ranking by relevance score

Example:
    >>> from pathlib import Path
    >>> from clauxton.semantic.search import SemanticSearchEngine
    >>>
    >>> engine = SemanticSearchEngine(Path("."))
    >>>
    >>> # Search KB
    >>> results = engine.search_kb("database architecture", limit=5)
    >>> for result in results:
    ...     print(f"{result['title']} (score: {result['score']:.3f})")
    >>>
    >>> # Search tasks
    >>> results = engine.search_tasks("authentication bug", limit=3, status="pending")
    >>>
    >>> # Search files
    >>> results = engine.search_files("API endpoint", limit=10)
    >>>
    >>> # Unified search
    >>> results = engine.search_all("user authentication", limit=10)
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict

from clauxton.semantic.embeddings import EmbeddingEngine
from clauxton.semantic.vector_store import VectorStore


class SearchResult(TypedDict):
    """
    Search result with score and metadata.

    Attributes:
        score: Similarity score (0.0 to 1.0, higher is better)
        source_type: Source type ("kb", "task", "file")
        source_id: Source ID (e.g., "KB-20251026-001", "TASK-001")
        title: Result title
        content: Result content (truncated if too long)
        metadata: Additional metadata (category, tags, etc.)
    """

    score: float
    source_type: str
    source_id: str
    title: str
    content: str
    metadata: Dict[str, Any]


class SemanticSearchEngine:
    """
    Semantic search engine for KB, tasks, and code files.

    Uses embeddings and vector similarity to find relevant items based on
    semantic meaning rather than keyword matching.

    Features:
    - Multi-source search (KB, tasks, files)
    - Metadata filtering (category, status, priority)
    - Relevance ranking
    - Configurable result limits
    - Content truncation for large results

    Attributes:
        project_root: Project root directory
        embedding_engine: Embedding engine for query encoding
        vector_store: Vector store for similarity search
        semantic_dir: Directory for semantic indices
    """

    def __init__(
        self,
        project_root: Path,
        embedding_engine: Optional[EmbeddingEngine] = None,
        vector_store: Optional[VectorStore] = None,
    ) -> None:
        """
        Initialize semantic search engine.

        Args:
            project_root: Project root directory
            embedding_engine: Optional EmbeddingEngine instance (creates new if None)
            vector_store: Optional VectorStore instance (creates new if None)

        Example:
            >>> engine = SemanticSearchEngine(Path("."))
            >>> # Or with custom components
            >>> engine = SemanticSearchEngine(
            ...     Path("."),
            ...     embedding_engine=custom_engine,
            ...     vector_store=custom_store,
            ... )
        """
        self.project_root = project_root
        self.semantic_dir = project_root / ".clauxton" / "semantic"
        self.embedding_engine = (
            embedding_engine if embedding_engine is not None
            else EmbeddingEngine()
        )
        self.vector_store = (
            vector_store if vector_store is not None
            else VectorStore(dimension=384)
        )

    def search_kb(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search Knowledge Base entries by semantic similarity.

        Args:
            query: Search query
            limit: Maximum number of results (default: 5)
            category: Optional category filter ("architecture", "decision", etc.)

        Returns:
            List of SearchResult dictionaries, sorted by relevance

        Example:
            >>> results = engine.search_kb("database design", limit=5)
            >>> for r in results:
            ...     print(f"{r['title']} - {r['score']:.3f}")
            >>>
            >>> # Filter by category
            >>> results = engine.search_kb("API", category="architecture")
        """
        index_path = self.semantic_dir / "kb_index.index"

        def filter_func(metadata: Dict[str, Any]) -> bool:
            """Filter by category if specified."""
            if category is None:
                return True
            return metadata.get("category") == category

        return self._search_index(query, index_path, limit, filter_func)

    def search_tasks(
        self,
        query: str,
        limit: int = 5,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search tasks by semantic similarity.

        Args:
            query: Search query
            limit: Maximum number of results (default: 5)
            status: Optional status filter ("pending", "in_progress", "completed")
            priority: Optional priority filter ("critical", "high", "medium", "low")

        Returns:
            List of SearchResult dictionaries, sorted by relevance

        Example:
            >>> results = engine.search_tasks("authentication", limit=3)
            >>>
            >>> # Filter by status and priority
            >>> results = engine.search_tasks(
            ...     "bug fix",
            ...     status="pending",
            ...     priority="high",
            ... )
        """
        index_path = self.semantic_dir / "task_index.index"

        def filter_func(metadata: Dict[str, Any]) -> bool:
            """Filter by status and priority if specified."""
            if status is not None and metadata.get("status") != status:
                return False
            if priority is not None and metadata.get("priority") != priority:
                return False
            return True

        return self._search_index(query, index_path, limit, filter_func)

    def search_files(
        self,
        query: str,
        limit: int = 10,
        pattern: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search code files by semantic similarity.

        Args:
            query: Search query
            limit: Maximum number of results (default: 10)
            pattern: Optional file pattern filter (e.g., "*.py", "src/**/*.ts")

        Returns:
            List of SearchResult dictionaries, sorted by relevance

        Example:
            >>> results = engine.search_files("authentication logic", limit=10)
            >>>
            >>> # Filter by file pattern
            >>> results = engine.search_files("API handler", pattern="**/*.py")
        """
        index_path = self.semantic_dir / "file_index.index"

        def filter_func(metadata: Dict[str, Any]) -> bool:
            """Filter by file pattern if specified."""
            if pattern is None:
                return True

            # Get file path from metadata
            file_path = metadata.get("file_path", "")
            if not file_path:
                return False

            # Simple pattern matching (supports * wildcard)
            from fnmatch import fnmatch
            return fnmatch(file_path, pattern)

        return self._search_index(query, index_path, limit, filter_func)

    def search_all(
        self,
        query: str,
        limit: int = 10,
        sources: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Unified search across all sources (KB, tasks, files).

        Args:
            query: Search query
            limit: Maximum number of results across all sources (default: 10)
            sources: Optional list of sources to search (default: ["kb", "task", "file"])

        Returns:
            List of SearchResult dictionaries from all sources, sorted by relevance

        Example:
            >>> # Search all sources
            >>> results = engine.search_all("authentication", limit=10)
            >>>
            >>> # Search specific sources only
            >>> results = engine.search_all(
            ...     "API design",
            ...     sources=["kb", "file"],
            ... )
        """
        if sources is None:
            sources = ["kb", "task", "file"]

        all_results: List[SearchResult] = []

        # Search each source
        if "kb" in sources:
            kb_results = self.search_kb(query, limit=limit)
            all_results.extend(kb_results)

        if "task" in sources:
            task_results = self.search_tasks(query, limit=limit)
            all_results.extend(task_results)

        if "file" in sources:
            file_results = self.search_files(query, limit=limit)
            all_results.extend(file_results)

        # Rank and limit results
        ranked = self._rank_results(all_results)
        return ranked[:limit]

    def _search_index(
        self,
        query: str,
        index_path: Path,
        limit: int,
        filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> List[SearchResult]:
        """
        Search a specific index with optional filtering.

        Args:
            query: Search query
            index_path: Path to FAISS index file (without .index extension)
            limit: Maximum number of results
            filter_func: Optional filter function for metadata

        Returns:
            List of SearchResult dictionaries

        Raises:
            FileNotFoundError: If index file doesn't exist
        """
        # Check if index exists
        if not index_path.exists():
            return []

        # Load index (VectorStore.load() is a classmethod)
        # Remove .index extension from path if present
        base_path = Path(str(index_path).replace(".index", ""))
        # Use dimension from vector_store (default: 384)
        store = VectorStore.load(base_path, dimension=self.vector_store.dimension)

        # Check if index is empty
        if store.index.ntotal == 0:
            return []

        # Encode query
        query_embedding = self.embedding_engine.encode([query])[0]

        # Search with higher limit to account for filtering
        search_limit = limit * 3 if filter_func else limit

        # VectorStore.search() returns List[Dict] with "distance", "metadata", "index"
        raw_results = store.search(
            query_embedding,
            k=min(search_limit, store.index.ntotal),
            filter_fn=filter_func,
        )

        # Build SearchResult objects
        results: List[SearchResult] = []
        for raw_result in raw_results:
            metadata = raw_result["metadata"]
            distance = raw_result["distance"]

            # Convert distance to similarity score (0.0 to 1.0)
            # For IndexFlatIP with normalized vectors, distance is cosine similarity (0-1)
            # Already in correct range, just ensure it's in [0, 1]
            score = max(0.0, min(1.0, float(distance)))

            # Build result
            # Try "title" (KB), then "name" (Task), then "file_path" (File)
            title = metadata.get("title") or metadata.get("name") or metadata.get("file_path", "")

            result: SearchResult = {
                "score": score,
                "source_type": metadata.get("source_type", "unknown"),
                "source_id": metadata.get("source_id", ""),
                "title": title,
                "content": self._truncate_content(metadata.get("content", "")),
                "metadata": metadata,
            }
            results.append(result)

            # Stop if we have enough filtered results
            if len(results) >= limit:
                break

        return results

    def _rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank results by score (descending).

        Args:
            results: List of SearchResult dictionaries

        Returns:
            Sorted list of SearchResult dictionaries
        """
        return sorted(results, key=lambda r: r["score"], reverse=True)

    def _truncate_content(self, content: str, max_length: int = 200) -> str:
        """
        Truncate content to max_length with ellipsis.

        Args:
            content: Content string
            max_length: Maximum length (default: 200)

        Returns:
            Truncated content
        """
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."
