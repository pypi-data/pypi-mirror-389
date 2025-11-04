"""
Autocomplete Provider System.

Provides autocomplete suggestions for query modal.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class AutocompleteProvider(ABC):
    """
    Base class for autocomplete providers.

    Subclasses should implement get_suggestions to provide
    context-specific autocomplete suggestions.
    """

    def __init__(self, project_root: Path) -> None:
        """
        Initialize autocomplete provider.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root

    @abstractmethod
    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get autocomplete suggestions for query.

        Args:
            query: Current query text
            limit: Maximum number of suggestions

        Returns:
            List of suggestions
        """
        pass

    def _fuzzy_match(self, query: str, candidates: List[str], limit: int) -> List[str]:
        """
        Perform fuzzy matching on candidates.

        Args:
            query: Query string
            candidates: Candidate strings
            limit: Maximum results

        Returns:
            Matched candidates
        """
        if not query:
            return candidates[:limit]

        query_lower = query.lower()
        matches = []

        for candidate in candidates:
            if query_lower in candidate.lower():
                matches.append(candidate)

        return matches[:limit]


class KBAutocompleteProvider(AutocompleteProvider):
    """Autocomplete provider for Knowledge Base entries."""

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get KB entry suggestions."""
        try:
            from clauxton.core.knowledge_base import KnowledgeBase

            kb = KnowledgeBase(self.project_root)
            entries = kb.list_all()

            # Extract titles and tags
            candidates = []
            for entry in entries:
                candidates.append(entry.title)
                candidates.extend(entry.tags)

            # Remove duplicates
            candidates = list(set(candidates))

            return self._fuzzy_match(query, candidates, limit)
        except Exception as e:
            logger.debug(f"KB autocomplete error: {e}")
            return []


class TaskAutocompleteProvider(AutocompleteProvider):
    """Autocomplete provider for tasks."""

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get task suggestions."""
        try:
            from clauxton.core.task_manager import TaskManager

            tm = TaskManager(self.project_root)
            tasks = tm.list_all()

            # Extract task names
            candidates = [task.name for task in tasks]

            return self._fuzzy_match(query, candidates, limit)
        except Exception as e:
            logger.debug(f"Task autocomplete error: {e}")
            return []


class FilePathAutocompleteProvider(AutocompleteProvider):
    """Autocomplete provider for file paths."""

    def __init__(self, project_root: Path) -> None:
        """Initialize file path autocomplete provider."""
        super().__init__(project_root)
        # Initialize file index cache for fast file lookups
        from clauxton.tui.services.file_index import FileIndexCache
        self._file_cache = FileIndexCache(project_root, ttl=300)

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get file path suggestions with caching."""
        try:
            # Use cached file index for fast lookups
            matching_files = self._file_cache.search(query, limit=limit * 2)

            # Convert to relative paths
            suggestions = [
                str(p.relative_to(self.project_root)) for p in matching_files
            ]

            return suggestions[:limit]
        except Exception as e:
            logger.debug(f"File autocomplete error: {e}")
            return []


class SymbolAutocompleteProvider(AutocompleteProvider):
    """Autocomplete provider for code symbols."""

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get symbol suggestions."""
        try:
            # from clauxton.intelligence.repository_map import RepositoryMap
            # repo_map = RepositoryMap(self.project_root)
            # TODO: Implement search_symbols method in RepositoryMap
            # symbols = repo_map.search_symbols(query, limit=limit)
            # candidates = [s["name"] for s in symbols]
            # For now, return empty list
            logger.debug("Symbol autocomplete not yet implemented in RepositoryMap")
            return []
        except (AttributeError, ImportError) as e:
            logger.debug(f"Symbol autocomplete not available: {e}")
            return []
        except Exception as e:
            logger.debug(f"Symbol autocomplete error: {e}")
            return []


class CompositeAutocompleteProvider(AutocompleteProvider):
    """
    Composite autocomplete provider.

    Combines suggestions from multiple providers.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize composite provider."""
        super().__init__(project_root)
        self.providers: List[AutocompleteProvider] = [
            KBAutocompleteProvider(project_root),
            TaskAutocompleteProvider(project_root),
            FilePathAutocompleteProvider(project_root),
        ]

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get suggestions from all providers."""
        all_suggestions = []

        for provider in self.providers:
            suggestions = provider.get_suggestions(query, limit // len(self.providers))
            all_suggestions.extend(suggestions)

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in all_suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)

        return unique_suggestions[:limit]
