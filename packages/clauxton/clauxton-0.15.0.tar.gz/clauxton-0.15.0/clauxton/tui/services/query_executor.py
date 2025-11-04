"""
Query Executor Service.

Executes queries across different search backends.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class QueryMode(str, Enum):
    """Query execution mode."""

    NORMAL = "normal"  # KB + Tasks search
    AI = "ai"  # AI question/answer
    FILE = "file"  # File search
    SYMBOL = "symbol"  # Code symbol search


class QueryResult:
    """Query result item."""

    def __init__(
        self,
        title: str,
        content: str,
        result_type: str,
        score: float = 1.0,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize query result.

        Args:
            title: Result title
            content: Result content/preview
            result_type: Type of result (kb, task, file, symbol)
            score: Relevance score (0.0-1.0)
            metadata: Additional metadata
        """
        self.title = title
        self.content = content
        self.result_type = result_type
        self.score = score
        self.metadata = metadata or {}


class QueryExecutor:
    """
    Query executor service.

    Executes queries across multiple search backends.
    """

    def __init__(self, project_root: Path) -> None:
        """
        Initialize query executor.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root

        # Initialize file index cache for fast file searches
        from clauxton.tui.services.file_index import FileIndexCache
        self._file_cache = FileIndexCache(project_root, ttl=300)

    def execute(
        self,
        query: str,
        mode: QueryMode = QueryMode.NORMAL,
        limit: int = 20,
    ) -> List[QueryResult]:
        """
        Execute query.

        Args:
            query: Query string
            mode: Query mode
            limit: Maximum results

        Returns:
            List of query results
        """
        if mode == QueryMode.NORMAL:
            return self._execute_normal(query, limit)
        elif mode == QueryMode.AI:
            return self._execute_ai(query, limit)
        elif mode == QueryMode.FILE:
            return self._execute_file(query, limit)
        elif mode == QueryMode.SYMBOL:
            return self._execute_symbol(query, limit)
        else:
            return []

    def _execute_normal(self, query: str, limit: int) -> List[QueryResult]:
        """Execute normal search (KB + Tasks)."""
        results = []

        # Search KB
        try:
            from clauxton.core.knowledge_base import KnowledgeBase

            kb = KnowledgeBase(self.project_root)
            kb_entries = kb.search(query, limit=limit // 2)

            for entry in kb_entries:
                results.append(
                    QueryResult(
                        title=entry.title,
                        content=entry.content[:200] + "..."
                        if len(entry.content) > 200
                        else entry.content,
                        result_type="kb",
                        score=0.9,  # Placeholder
                        metadata={"id": entry.id, "category": entry.category},
                    )
                )
        except Exception as e:
            logger.debug(f"KB search error: {e}")

        # Search Tasks
        try:
            from clauxton.core.task_manager import TaskManager

            tm = TaskManager(self.project_root)
            all_tasks = tm.list_all()

            # Simple search
            query_lower = query.lower()
            matching_tasks = [
                t
                for t in all_tasks
                if query_lower in t.name.lower()
                or (t.description and query_lower in t.description.lower())
            ]

            for task in matching_tasks[: limit // 2]:
                results.append(
                    QueryResult(
                        title=task.name,
                        content=task.description or "No description",
                        result_type="task",
                        score=0.8,
                        metadata={
                            "id": task.id,
                            "status": task.status,
                            "priority": task.priority,
                        },
                    )
                )
        except Exception as e:
            logger.debug(f"Task search error: {e}")

        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _execute_ai(self, query: str, limit: int) -> List[QueryResult]:
        """Execute AI query (context-aware Q&A)."""
        # Placeholder for AI integration
        return [
            QueryResult(
                title="AI Response",
                content=f"AI would answer: '{query}' (Coming soon...)",
                result_type="ai",
                score=1.0,
                metadata={"query": query},
            )
        ]

    def _execute_file(self, query: str, limit: int) -> List[QueryResult]:
        """Execute file search with caching."""
        results = []

        try:
            # Use cached file index for fast search
            matching_files = self._file_cache.search(query, limit=limit)

            for file_path in matching_files:
                rel_path = file_path.relative_to(self.project_root)
                results.append(
                    QueryResult(
                        title=str(rel_path),
                        content=f"File: {file_path.name}",
                        result_type="file",
                        score=0.85,
                        metadata={
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                        },
                    )
                )
        except Exception as e:
            logger.debug(f"File search error: {e}")

        return results

    def _execute_symbol(self, query: str, limit: int) -> List[QueryResult]:
        """Execute symbol search."""
        results: List[QueryResult] = []

        try:
            # from clauxton.intelligence.repository_map import RepositoryMap
            # repo_map = RepositoryMap(self.project_root)
            # TODO: Implement search_symbols method in RepositoryMap
            # symbols = repo_map.search_symbols(query, limit=limit)
            # For now, return empty results
            logger.debug("Symbol search not yet implemented in RepositoryMap")
        except (AttributeError, ImportError) as e:
            logger.debug(f"Symbol search not available: {e}")
        except Exception as e:
            logger.debug(f"Symbol search error: {e}")

        return results
