"""
Backward compatibility layer for Knowledge Base operations.

This module provides a compatibility wrapper that maps the legacy Knowledge Base API
to the new unified Memory system. This allows existing code to continue working
while internally using the new Memory infrastructure.

DEPRECATED: This module is deprecated and will be removed in v0.17.0.
New code should use the Memory class directly.

Example:
    >>> from pathlib import Path
    >>> kb = KnowledgeBaseCompat(Path("."))
    >>> entry = KnowledgeBaseEntry(...)
    >>> kb.add(entry)
    'KB-20260127-001'
"""

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from clauxton.core.memory import Memory, MemoryEntry
from clauxton.core.models import (
    DuplicateError,
    KnowledgeBaseEntry,
    NotFoundError,
    ValidationError,
)


class KnowledgeBaseCompat:
    """
    Backward compatibility layer for Knowledge Base operations.

    Maps KB API to Memory system internally. All operations create
    Memory entries with type='knowledge' and preserve legacy KB IDs.

    DEPRECATED: This class is deprecated and will be removed in v0.17.0.
    Please use the Memory class directly:

        # Old way (deprecated):
        kb = KnowledgeBaseCompat(project_root)
        kb.add(entry)

        # New way (recommended):
        memory = Memory(project_root)
        memory_entry = MemoryEntry(type="knowledge", ...)
        memory.add(memory_entry)

    Attributes:
        memory: Unified Memory instance
        project_root: Project root directory

    Example:
        >>> kb = KnowledgeBaseCompat(Path("."))
        >>> entry = KnowledgeBaseEntry(
        ...     id="KB-20260127-001",
        ...     title="API Design",
        ...     category="architecture",
        ...     content="Use RESTful API design",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
        >>> kb.add(entry)
        'KB-20260127-001'
    """

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize KB compatibility layer.

        Args:
            project_root: Project root directory (Path or str)

        Warnings:
            DeprecationWarning: Always emitted on initialization

        Example:
            >>> kb = KnowledgeBaseCompat(Path("."))
            >>> kb = KnowledgeBaseCompat(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.memory = Memory(self.project_root)

        # Emit deprecation warning
        warnings.warn(
            "KnowledgeBase API is deprecated and will be removed in v0.17.0. "
            "Please migrate to the Memory class. "
            "See documentation: docs/v0.15.0_MIGRATION_GUIDE.md",
            DeprecationWarning,
            stacklevel=2
        )

    def add(self, entry: KnowledgeBaseEntry) -> str:
        """
        Add KB entry (maps to Memory entry with type=knowledge).

        Args:
            entry: KnowledgeBaseEntry to add

        Returns:
            Entry ID (original KB ID for compatibility)

        Raises:
            DuplicateError: If entry ID already exists
            ValidationError: If entry validation fails

        Example:
            >>> entry = KnowledgeBaseEntry(
            ...     id="KB-20260127-001",
            ...     title="API Design",
            ...     category="architecture",
            ...     content="Use RESTful APIs",
            ...     created_at=datetime.now(),
            ...     updated_at=datetime.now()
            ... )
            >>> kb.add(entry)
            'KB-20260127-001'
        """
        # Check if legacy_id already exists
        existing = self.memory.list_all(type_filter=["knowledge"])
        for mem in existing:
            if mem.legacy_id == entry.id:
                raise DuplicateError(
                    f"Entry with ID '{entry.id}' already exists. "
                    "Use update() to modify existing entries."
                )

        # Convert KB entry to Memory entry
        memory_entry = MemoryEntry(
            id=self.memory._generate_memory_id(),
            type="knowledge",
            title=entry.title,
            content=entry.content,
            category=entry.category,
            tags=entry.tags,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            related_to=[],
            source="manual",
            confidence=1.0,
            legacy_id=entry.id,  # Store original KB ID
        )

        self.memory.add(memory_entry)
        return entry.id  # Return original KB ID for compatibility

    def get(self, entry_id: str) -> KnowledgeBaseEntry:
        """
        Get KB entry by ID.

        Args:
            entry_id: KB entry ID (e.g., "KB-20260127-001")

        Returns:
            KnowledgeBaseEntry object

        Raises:
            NotFoundError: If entry not found

        Example:
            >>> entry = kb.get("KB-20260127-001")
            >>> print(entry.title)
            API Design
        """
        # Find by legacy_id
        memories = self.memory.list_all(type_filter=["knowledge"])
        for mem in memories:
            if mem.legacy_id == entry_id:
                return self._to_kb_entry(mem)

        raise NotFoundError(
            f"Entry with ID '{entry_id}' not found in Knowledge Base. "
            "Use list_all() to see available entries."
        )

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[KnowledgeBaseEntry]:
        """
        Search KB entries (maps to Memory search with type=knowledge).

        Args:
            query: Search query
            category: Optional category filter
            tags: Optional tag filter (matches any tag)
            limit: Maximum results

        Returns:
            List of KnowledgeBaseEntry objects

        Example:
            >>> results = kb.search("api", category="architecture")
            >>> for entry in results:
            ...     print(entry.title)
            API Design
            REST API Guidelines
        """
        # Search memories with type filter
        memories = self.memory.search(query, type_filter=["knowledge"], limit=limit)

        # Apply additional filters
        filtered = memories
        if category:
            filtered = [m for m in filtered if m.category == category]
        if tags:
            filtered = [m for m in filtered if any(tag in m.tags for tag in tags)]

        # Convert to KB entries
        return [self._to_kb_entry(m) for m in filtered[:limit]]

    def list_all(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[KnowledgeBaseEntry]:
        """
        List all KB entries.

        Args:
            category: Optional category filter
            tags: Optional tag filter (matches any tag)

        Returns:
            List of KnowledgeBaseEntry objects

        Example:
            >>> entries = kb.list_all(category="architecture")
            >>> len(entries)
            5
        """
        # Get all knowledge memories
        memories = self.memory.list_all(
            type_filter=["knowledge"],
            category_filter=category,
            tag_filter=tags
        )

        # Convert to KB entries
        return [self._to_kb_entry(m) for m in memories]

    def update(self, entry_id: str, **kwargs: Any) -> KnowledgeBaseEntry:
        """
        Update KB entry.

        Args:
            entry_id: KB entry ID to update
            **kwargs: Fields to update (e.g., title="New title", tags=["new"])

        Returns:
            Updated KnowledgeBaseEntry

        Raises:
            NotFoundError: If entry not found
            ValidationError: If update validation fails

        Example:
            >>> updated = kb.update(
            ...     "KB-20260127-001",
            ...     content="Updated content",
            ...     tags=["api", "rest", "updated"]
            ... )
            >>> updated.content
            'Updated content'
        """
        # Find memory by legacy_id
        memories = self.memory.list_all(type_filter=["knowledge"])
        memory_id = None
        for mem in memories:
            if mem.legacy_id == entry_id:
                memory_id = mem.id
                break

        if memory_id is None:
            raise NotFoundError(
                f"Entry with ID '{entry_id}' not found in Knowledge Base."
            )

        # Update memory
        success = self.memory.update(memory_id, **kwargs)
        if not success:
            raise ValidationError(f"Failed to update entry '{entry_id}'")

        # Return updated entry
        return self.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        """
        Delete KB entry.

        Args:
            entry_id: KB entry ID to delete

        Returns:
            True if successful, False if not found

        Example:
            >>> success = kb.delete("KB-20260127-001")
            >>> success
            True
        """
        # Find memory by legacy_id
        memories = self.memory.list_all(type_filter=["knowledge"])
        for mem in memories:
            if mem.legacy_id == entry_id:
                return self.memory.delete(mem.id)

        return False

    def _to_kb_entry(self, memory: MemoryEntry) -> KnowledgeBaseEntry:
        """
        Convert Memory entry to KB entry.

        Args:
            memory: MemoryEntry to convert

        Returns:
            KnowledgeBaseEntry

        Raises:
            ValidationError: If conversion fails
        """
        # Use legacy_id if available, otherwise use memory ID
        kb_id = memory.legacy_id or memory.id

        try:
            return KnowledgeBaseEntry(
                id=kb_id,
                title=memory.title,
                content=memory.content,
                category=memory.category,  # type: ignore  # Category is validated by KB model
                tags=memory.tags,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to convert Memory entry to KB entry: {e}"
            ) from e

    def _generate_kb_id(self) -> str:
        """
        Generate legacy KB ID.

        Returns:
            KB ID in format "KB-YYYYMMDD-NNN"

        Example:
            >>> kb._generate_kb_id()
            'KB-20260127-001'
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        # Find highest KB ID for today
        memories = self.memory.list_all(type_filter=["knowledge"])
        today_kb_ids = [
            m.legacy_id
            for m in memories
            if m.legacy_id and m.legacy_id.startswith(f"KB-{date_str}")
        ]

        if not today_kb_ids:
            seq = 1
        else:
            seqs = [int(kb_id.split("-")[-1]) for kb_id in today_kb_ids]
            seq = max(seqs) + 1

        return f"KB-{date_str}-{seq:03d}"
