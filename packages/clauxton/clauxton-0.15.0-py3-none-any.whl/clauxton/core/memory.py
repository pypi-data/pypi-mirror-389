"""
Memory management system for Clauxton v0.15.0.

This module provides the unified Memory System that consolidates:
- Knowledge Base entries (architecture, decisions, patterns)
- Task Management (tasks, dependencies)
- Code Intelligence (symbols, patterns)

Key Features:
- Unified MemoryEntry model with type discrimination
- CRUD operations with validation
- TF-IDF relevance search
- Relationship management between memories
- Atomic storage with backups

Example:
    >>> from pathlib import Path
    >>> from datetime import datetime
    >>> memory = Memory(Path("."))
    >>> entry = MemoryEntry(
    ...     id="MEM-20260127-001",
    ...     type="knowledge",
    ...     title="API Design Pattern",
    ...     content="Use RESTful API design",
    ...     category="architecture",
    ...     created_at=datetime.now(),
    ...     updated_at=datetime.now(),
    ...     source="manual"
    ... )
    >>> memory.add(entry)
    'MEM-20260127-001'
"""

from datetime import datetime
from pathlib import Path
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from clauxton.core.models import DuplicateError, ValidationError

# Optional TF-IDF search (falls back to simple search if scikit-learn not available)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None
    cosine_similarity = None


# ============================================================================
# Memory Entry Model
# ============================================================================


class MemoryEntry(BaseModel):
    """
    Unified memory entry for all project memory types.

    This model unifies Knowledge Base, Tasks, Code Intelligence, and Patterns
    into a single memory representation with type discrimination.

    Memory Types:
        - knowledge: Architecture decisions, patterns, conventions
        - decision: Specific architectural/technical decisions
        - code: Code structure, symbols, patterns
        - task: Work items, features to implement
        - pattern: Recurring patterns in code or workflow

    Attributes:
        id: Unique identifier (format: MEM-YYYYMMDD-NNN)
        type: Memory type (knowledge, decision, code, task, pattern)
        title: Short, descriptive title (max 200 chars)
        content: Detailed content (min 1 char)
        category: Category for grouping (e.g., architecture, api, database)
        tags: Optional tags for filtering and search
        created_at: Creation timestamp
        updated_at: Last update timestamp
        related_to: List of related memory IDs
        supersedes: Memory ID this entry replaces (for versioning)
        source: Origin of memory (manual, git-commit, code-analysis, import)
        confidence: Confidence score for auto-extracted memories (0.0-1.0)
        source_ref: Source reference (commit SHA, file path, etc.)
        legacy_id: Legacy ID for backward compatibility (KB-* or TASK-*)

    Example:
        >>> entry = MemoryEntry(
        ...     id="MEM-20260127-001",
        ...     type="knowledge",
        ...     title="API Design Pattern",
        ...     content="Use RESTful API design with versioning",
        ...     category="architecture",
        ...     tags=["api", "rest", "design"],
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now(),
        ...     source="manual",
        ...     confidence=1.0
        ... )
        >>> entry.type
        'knowledge'
    """

    # Core identity
    id: str = Field(
        ...,
        pattern=r"^MEM-\d{8}-\d{3}$",
        description="Memory ID (e.g., MEM-20260127-001)",
    )
    type: Literal["knowledge", "decision", "code", "task", "pattern"] = Field(
        ..., description="Memory type"
    )
    title: str = Field(
        ..., min_length=1, max_length=200, description="Memory title"
    )
    content: str = Field(..., min_length=1, description="Memory content")

    # Metadata
    category: str = Field(
        ..., min_length=1, description="Category (e.g., architecture, api, database)"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags for filtering"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Relationships (memory connections)
    related_to: List[str] = Field(
        default_factory=list, description="Related memory IDs"
    )
    supersedes: Optional[str] = Field(
        default=None, description="Replaced memory ID"
    )

    # Context (memory origin)
    source: Literal["manual", "git-commit", "code-analysis", "import"] = Field(
        ..., description="Memory source"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )

    # Source reference
    source_ref: Optional[str] = Field(
        default=None, description="Source reference (commit SHA, file path, etc.)"
    )

    # Legacy compatibility (deprecated)
    legacy_id: Optional[str] = Field(
        default=None, description="Legacy ID (KB-* or TASK-*)"
    )

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Remove leading/trailing whitespace from title."""
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Title cannot be empty or only whitespace")
        return sanitized

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Remove leading/trailing whitespace from content."""
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Content cannot be empty or only whitespace")
        return sanitized

    @field_validator("tags")
    @classmethod
    def sanitize_tags(cls, v: List[str]) -> List[str]:
        """Remove empty tags and duplicates."""
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        return list(dict.fromkeys(cleaned))  # Remove duplicates, preserve order

    @field_validator("category")
    @classmethod
    def sanitize_category(cls, v: str) -> str:
        """Remove leading/trailing whitespace and lowercase category."""
        sanitized = v.strip().lower()
        if not sanitized:
            raise ValueError("Category cannot be empty or only whitespace")
        return sanitized

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "MEM-20260127-001",
                "type": "knowledge",
                "title": "API Design Pattern",
                "content": "Use RESTful API design with versioning",
                "category": "architecture",
                "tags": ["api", "rest", "design"],
                "created_at": "2026-01-27T10:00:00",
                "updated_at": "2026-01-27T10:00:00",
                "related_to": [],
                "supersedes": None,
                "source": "manual",
                "confidence": 1.0,
                "source_ref": None,
                "legacy_id": None,
            }
        }
    }


# ============================================================================
# Memory Search Engine (Internal)
# ============================================================================


class MemorySearchEngine:
    """
    TF-IDF based search engine for Memory entries.

    Internal class used by Memory for relevance-based search.
    """

    def __init__(self, entries: List[MemoryEntry]) -> None:
        """
        Initialize search engine with entries.

        Args:
            entries: List of Memory entries to index

        Raises:
            ImportError: If scikit-learn is not installed
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required for TF-IDF search. "
                "Install with: pip install scikit-learn"
            )

        self.entries = entries
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=1000,
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=1,  # Minimum document frequency
            lowercase=True,
        )
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self) -> None:
        """Build TF-IDF index from entries."""
        if not self.entries:
            self.tfidf_matrix = None
            return

        # Create corpus: combine title, content, tags, category
        corpus = [
            f"{entry.title} {entry.content} {' '.join(entry.tags or [])} {entry.category}"
            for entry in self.entries
        ]

        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except ValueError:
            # Empty vocabulary (e.g., all stop words)
            self.tfidf_matrix = None

    def search(
        self,
        query: str,
        type_filter: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[tuple[MemoryEntry, float]]:
        """
        Search for entries matching query.

        Args:
            query: Search query string
            type_filter: Optional memory type filter (e.g., ["knowledge", "decision"])
            limit: Maximum number of results

        Returns:
            List of (entry, relevance_score) tuples, sorted by relevance
        """
        if not self.entries or self.tfidf_matrix is None:
            return []

        if not query.strip():
            return []

        # Filter by type first
        if type_filter:
            filtered_entries = [e for e in self.entries if e.type in type_filter]
            if not filtered_entries:
                return []

            # Rebuild index for filtered entries
            temp_engine = MemorySearchEngine.__new__(MemorySearchEngine)
            temp_engine.entries = filtered_entries
            temp_engine.vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1,
                lowercase=True,
            )
            temp_engine.tfidf_matrix = None
            temp_engine._build_index()

            if temp_engine.tfidf_matrix is None:
                return []

            # Transform query and calculate similarity
            try:
                query_vec = temp_engine.vectorizer.transform([query])
                scores = cosine_similarity(query_vec, temp_engine.tfidf_matrix)[0]
            except ValueError:
                return []

            # Sort by score descending
            indices = scores.argsort()[-limit:][::-1]
            return [
                (filtered_entries[i], float(scores[i]))
                for i in indices
                if scores[i] > 0
            ]
        else:
            # No type filter
            try:
                query_vec = self.vectorizer.transform([query])
                scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]
            except ValueError:
                return []

            # Sort by score descending
            indices = scores.argsort()[-limit:][::-1]
            return [
                (self.entries[i], float(scores[i]))
                for i in indices
                if scores[i] > 0
            ]


# ============================================================================
# Memory Management Class
# ============================================================================


class Memory:
    """
    Memory management system for unified project memory.

    Provides CRUD operations, search, and relationship management for
    all project memory types (knowledge, decisions, code, tasks, patterns).

    Storage:
        - File: .clauxton/memories.yml
        - Format: YAML with atomic writes
        - Backup: Automatic before modifications

    Attributes:
        project_root: Project root directory
        clauxton_dir: .clauxton directory path
        store: MemoryStore instance for persistence

    Example:
        >>> memory = Memory(Path("."))
        >>> entry = MemoryEntry(...)
        >>> memory.add(entry)
        'MEM-20260127-001'
        >>> results = memory.search("api design")
        >>> len(results)
        5
    """

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize Memory system.

        Args:
            project_root: Project root directory (Path or str)

        Example:
            >>> memory = Memory(Path("."))
            >>> memory = Memory(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.clauxton_dir = self.project_root / ".clauxton"

        # Import here to avoid circular dependency
        from clauxton.core.memory_store import MemoryStore
        self.store = MemoryStore(self.project_root)

        self._search_engine: Optional[MemorySearchEngine] = None
        self._rebuild_search_index()

    def add(self, entry: MemoryEntry) -> str:
        """
        Add memory entry.

        Args:
            entry: MemoryEntry to add

        Returns:
            Entry ID (e.g., "MEM-20260127-001")

        Raises:
            ValidationError: If entry validation fails
            DuplicateError: If entry ID already exists

        Example:
            >>> entry = MemoryEntry(
            ...     id="MEM-20260127-001",
            ...     type="knowledge",
            ...     title="API Design",
            ...     content="Use RESTful APIs",
            ...     category="architecture",
            ...     created_at=datetime.now(),
            ...     updated_at=datetime.now(),
            ...     source="manual"
            ... )
            >>> memory_id = memory.add(entry)
            >>> memory_id
            'MEM-20260127-001'
        """
        # Check for duplicate ID
        existing = self.store.load_all()
        if any(e.id == entry.id for e in existing):
            raise DuplicateError(
                f"Memory entry with ID '{entry.id}' already exists. "
                "Use update() to modify existing entries."
            )

        # Save entry
        self.store.save(entry)
        self._rebuild_search_index()

        return entry.id

    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Get memory by ID.

        Args:
            memory_id: Memory ID (e.g., "MEM-20260127-001")

        Returns:
            MemoryEntry if found, None otherwise

        Example:
            >>> entry = memory.get("MEM-20260127-001")
            >>> if entry:
            ...     print(entry.title)
            API Design Pattern
        """
        entries = self.store.load_all()
        for entry in entries:
            if entry.id == memory_id:
                return entry
        return None

    def search(
        self,
        query: str,
        type_filter: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """
        Search memories with TF-IDF relevance ranking.

        Uses TF-IDF algorithm for relevance-based search if scikit-learn is available.
        Falls back to simple keyword matching if not.

        Args:
            query: Search query (keywords)
            type_filter: Filter by types (e.g., ["knowledge", "decision"])
            limit: Maximum results to return

        Returns:
            List of matching MemoryEntry objects (sorted by relevance)

        Example:
            >>> results = memory.search("api design", type_filter=["knowledge"])
            >>> for entry in results:
            ...     print(entry.title)
            API Design Pattern
            REST API Guidelines
        """
        # Use TF-IDF search if available
        if SKLEARN_AVAILABLE and self._search_engine is not None:
            results = self._search_engine.search(query, type_filter=type_filter, limit=limit)
            return [entry for entry, _ in results]

        # Fallback to simple keyword search
        return self._simple_search(query, type_filter, limit)

    def _simple_search(
        self,
        query: str,
        type_filter: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """
        Simple keyword-based search (fallback when TF-IDF unavailable).

        Args:
            query: Search query
            type_filter: Optional type filter
            limit: Maximum results

        Returns:
            List of matching MemoryEntry objects
        """
        entries = self.store.load_all()
        query_lower = query.lower().strip()

        if not query_lower:
            return []

        matches: List[tuple[MemoryEntry, float]] = []

        for entry in entries:
            # Skip if type filter doesn't match
            if type_filter and entry.type not in type_filter:
                continue

            # Calculate relevance score
            score = 0.0

            # Title matches (weight: 2.0)
            if query_lower in entry.title.lower():
                score += 2.0

            # Content matches (weight: 1.0)
            if query_lower in entry.content.lower():
                score += 1.0

            # Tag matches (weight: 1.5)
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 1.5
                    break

            # Category matches (weight: 1.0)
            if query_lower in entry.category.lower():
                score += 1.0

            # Only include if there's a match
            if score > 0:
                matches.append((entry, score))

        # Sort by relevance (descending) and limit results
        matches.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in matches[:limit]]

    def update(self, memory_id: str, **kwargs: Any) -> bool:
        """
        Update memory entry.

        Args:
            memory_id: Memory ID to update
            **kwargs: Fields to update (e.g., title="New title", tags=["new", "tags"])

        Returns:
            True if successful, False if not found

        Raises:
            ValidationError: If update validation fails

        Example:
            >>> success = memory.update(
            ...     "MEM-20260127-001",
            ...     content="Updated content",
            ...     tags=["api", "rest", "updated"]
            ... )
            >>> success
            True
        """
        entry = self.get(memory_id)
        if entry is None:
            return False

        # Update fields
        entry_dict = entry.model_dump()
        for key, value in kwargs.items():
            if key in entry_dict and key not in ["id", "created_at"]:
                entry_dict[key] = value

        # Always update updated_at timestamp
        entry_dict["updated_at"] = datetime.now()

        # Create updated entry
        try:
            updated_entry = MemoryEntry(**entry_dict)
        except Exception as e:
            raise ValidationError(f"Failed to update memory: {e}") from e

        # Delete old entry and save updated one
        self.store.delete(memory_id)
        self.store.save(updated_entry)
        self._rebuild_search_index()

        return True

    def delete(self, memory_id: str) -> bool:
        """
        Delete memory entry.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if successful, False if not found

        Example:
            >>> success = memory.delete("MEM-20260127-001")
            >>> success
            True
        """
        result = self.store.delete(memory_id)
        if result:
            self._rebuild_search_index()
        return result

    def find_related(self, memory_id: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Find related memories.

        Finds memories related to the given memory ID by:
        1. Explicit relationships (related_to field)
        2. Shared tags (high relevance)
        3. Same category (medium relevance)
        4. Content similarity (semantic)

        Args:
            memory_id: Memory ID to find relations for
            limit: Maximum results to return

        Returns:
            List of related MemoryEntry objects (sorted by relevance)

        Example:
            >>> related = memory.find_related("MEM-20260127-001", limit=3)
            >>> for entry in related:
            ...     print(entry.title)
            REST API Guidelines
            API Versioning Strategy
        """
        entry = self.get(memory_id)
        if entry is None:
            return []

        all_entries = self.store.load_all()
        related: List[tuple[MemoryEntry, float]] = []

        for other in all_entries:
            if other.id == memory_id:
                continue

            score = 0.0

            # Explicit relationship (highest weight: 10.0)
            if memory_id in other.related_to or other.id in entry.related_to:
                score += 10.0

            # Shared tags (weight: 2.0 per tag)
            shared_tags = set(entry.tags) & set(other.tags)
            score += len(shared_tags) * 2.0

            # Same category (weight: 1.5)
            if entry.category == other.category:
                score += 1.5

            # Same type (weight: 1.0)
            if entry.type == other.type:
                score += 1.0

            if score > 0:
                related.append((other, score))

        # Sort by relevance (descending) and limit results
        related.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in related[:limit]]

    def list_all(
        self,
        type_filter: Optional[List[str]] = None,
        category_filter: Optional[str] = None,
        tag_filter: Optional[List[str]] = None,
    ) -> List[MemoryEntry]:
        """
        List all memories with optional filters.

        Args:
            type_filter: Filter by types (e.g., ["knowledge", "decision"])
            category_filter: Filter by category (e.g., "architecture")
            tag_filter: Filter by tags (any match, e.g., ["api", "rest"])

        Returns:
            List of MemoryEntry objects (sorted by created_at desc)

        Example:
            >>> all_memories = memory.list_all()
            >>> knowledge = memory.list_all(type_filter=["knowledge"])
            >>> api_memories = memory.list_all(tag_filter=["api"])
        """
        entries = self.store.load_all()

        # Apply filters
        if type_filter:
            entries = [e for e in entries if e.type in type_filter]

        if category_filter:
            entries = [e for e in entries if e.category == category_filter]

        if tag_filter:
            entries = [e for e in entries if any(tag in e.tags for tag in tag_filter)]

        # Sort by created_at descending (newest first)
        entries.sort(key=lambda e: e.created_at, reverse=True)

        return entries

    def _generate_memory_id(self) -> str:
        """
        Generate unique memory ID.

        Returns:
            Memory ID in format "MEM-YYYYMMDD-NNN"

        Example:
            >>> memory._generate_memory_id()
            'MEM-20260127-001'
        """
        entries = self.store.load_all()
        today = datetime.now().strftime("%Y%m%d")

        # Find all IDs for today
        today_ids = [
            int(e.id.split("-")[-1])
            for e in entries
            if e.id.startswith(f"MEM-{today}")
        ]

        # Get next sequence number
        next_num = max(today_ids, default=0) + 1

        return f"MEM-{today}-{next_num:03d}"

    def _rebuild_search_index(self) -> None:
        """Rebuild TF-IDF search index after data changes."""
        if not SKLEARN_AVAILABLE:
            return

        entries = self.store.load_all()
        if entries:
            try:
                self._search_engine = MemorySearchEngine(entries)
            except Exception:
                # If search engine fails to initialize, fall back to simple search
                self._search_engine = None
        else:
            self._search_engine = None
