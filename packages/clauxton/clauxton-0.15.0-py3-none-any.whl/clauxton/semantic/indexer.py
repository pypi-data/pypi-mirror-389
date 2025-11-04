"""
Indexer for embedding KB entries, tasks, and code files.

This module provides indexing functionality for semantic search:
- Index Knowledge Base entries (title + content + tags)
- Index tasks (name + description)
- Index code files (file content)
- Incremental updates (only reindex changed items)
- Batch processing with progress tracking

Example:
    >>> from pathlib import Path
    >>> from clauxton.semantic.embeddings import EmbeddingEngine
    >>> from clauxton.semantic.vector_store import VectorStore
    >>>
    >>> engine = EmbeddingEngine()
    >>> store = VectorStore(dimension=384)
    >>> indexer = Indexer(Path("."), engine, store)
    >>>
    >>> # Index all sources
    >>> counts = indexer.index_all()
    >>> print(counts)  # {"kb": 10, "tasks": 5, "files": 50}
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.task_manager import TaskManager
from clauxton.semantic.embeddings import EmbeddingEngine
from clauxton.semantic.vector_store import VectorStore


class Indexer:
    """
    Indexer for semantic search.

    Converts KB entries, tasks, and code files into embeddings and stores them
    in a VectorStore for fast similarity search.

    Features:
    - Incremental updates (only reindex changed items)
    - Batch processing for efficiency
    - Content hashing for change detection
    - Metadata tracking for each indexed item

    Attributes:
        project_root: Project root directory
        embedding_engine: Engine for generating embeddings
        vector_store: Store for embeddings and metadata
        kb: KnowledgeBase instance
        task_manager: TaskManager instance

    Example:
        >>> indexer = Indexer(Path("."), engine, store)
        >>> count = indexer.index_knowledge_base()
        >>> print(f"Indexed {count} KB entries")
    """

    def __init__(
        self,
        project_root: Path,
        embedding_engine: EmbeddingEngine,
        vector_store: VectorStore,
    ) -> None:
        """
        Initialize Indexer.

        Args:
            project_root: Project root directory
            embedding_engine: Engine for generating embeddings
            vector_store: Store for embeddings and metadata

        Example:
            >>> from pathlib import Path
            >>> indexer = Indexer(Path("."), engine, store)
        """
        self.project_root = Path(project_root)
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.kb = KnowledgeBase(self.project_root)
        self.task_manager = TaskManager(self.project_root)

    def index_knowledge_base(self, force: bool = False) -> int:
        """
        Index all Knowledge Base entries.

        Args:
            force: If True, reindex all entries regardless of change status

        Returns:
            Number of entries indexed (new or updated)

        Example:
            >>> count = indexer.index_knowledge_base()
            >>> print(f"Indexed {count} entries")
            Indexed 10 entries
        """
        # Invalidate cache to ensure we get latest entries from disk
        self.kb._invalidate_cache()
        entries = self.kb.list_all()
        indexed_count = 0

        # Build existing metadata map for quick lookup
        existing = self._get_existing_metadata("kb")

        for entry in entries:
            # Check if needs reindexing
            if not force:
                existing_meta = existing.get(entry.id)
                if existing_meta and not self._needs_reindex(
                    existing_meta, entry.updated_at
                ):
                    continue

            # Extract text for embedding
            text = self._extract_kb_text(entry)

            # Generate content hash
            content_hash = self._hash_content(text)

            # Skip if content unchanged (even with force=False and timestamp changed)
            if not force:
                existing_meta = existing.get(entry.id)
                if existing_meta and existing_meta.get("content_hash") == content_hash:
                    continue

            # Generate embedding
            embedding = self.embedding_engine.encode([text])[0]

            # Create metadata
            metadata = {
                "source_type": "kb",
                "source_id": entry.id,
                "title": entry.title,
                "category": entry.category,
                "tags": entry.tags,
                "updated_at": entry.updated_at.isoformat(),
                "indexed_at": datetime.now().isoformat(),
                "content_hash": content_hash,
            }

            # Add to vector store (metadata as list)
            self.vector_store.add(embedding, [metadata])
            indexed_count += 1

        # Save vector store if any updates
        if indexed_count > 0:
            path = self.project_root / ".clauxton" / "semantic" / "kb_index"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save(path)

        return indexed_count

    def index_tasks(self, force: bool = False) -> int:
        """
        Index all tasks.

        Args:
            force: If True, reindex all tasks regardless of change status

        Returns:
            Number of tasks indexed (new or updated)

        Example:
            >>> count = indexer.index_tasks()
            >>> print(f"Indexed {count} tasks")
            Indexed 5 tasks
        """
        # Invalidate cache to ensure we get latest tasks from disk
        self.task_manager._invalidate_cache()
        tasks = self.task_manager.list_all()
        indexed_count = 0

        # Build existing metadata map
        existing = self._get_existing_metadata("task")

        for task in tasks:
            # Check if needs reindexing
            if not force:
                # For tasks, we use created_at as the timestamp (tasks don't have updated_at)
                # So we check if the task already exists in the index
                existing_meta = existing.get(task.id)
                if existing_meta:
                    # Check content hash instead of timestamp
                    text = self._extract_task_text(task)
                    content_hash = self._hash_content(text)
                    if existing_meta.get("content_hash") == content_hash:
                        continue

            # Extract text for embedding
            text = self._extract_task_text(task)

            # Generate content hash
            content_hash = self._hash_content(text)

            # Generate embedding
            embedding = self.embedding_engine.encode([text])[0]

            # Create metadata
            metadata = {
                "source_type": "task",
                "source_id": task.id,
                "name": task.name,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "indexed_at": datetime.now().isoformat(),
                "content_hash": content_hash,
            }

            # Add to vector store (metadata as list)
            self.vector_store.add(embedding, [metadata])
            indexed_count += 1

        # Save vector store if any updates
        if indexed_count > 0:
            path = self.project_root / ".clauxton" / "semantic" / "task_index"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save(path)

        return indexed_count

    def index_files(
        self, file_patterns: List[str], force: bool = False
    ) -> int:
        """
        Index code files matching patterns.

        Args:
            file_patterns: List of glob patterns (e.g., ["**/*.py", "**/*.ts"])
            force: If True, reindex all files regardless of change status

        Returns:
            Number of files indexed (new or updated)

        Example:
            >>> count = indexer.index_files(["**/*.py"])
            >>> print(f"Indexed {count} Python files")
            Indexed 50 Python files
        """
        indexed_count = 0

        # Build existing metadata map
        existing = self._get_existing_metadata("file")

        for pattern in file_patterns:
            # Find matching files
            files = list(self.project_root.glob(pattern))

            for file_path in files:
                # Skip non-files
                if not file_path.is_file():
                    continue

                # Skip .clauxton directory
                if ".clauxton" in file_path.parts:
                    continue

                # Get relative path for consistent IDs
                try:
                    rel_path = file_path.relative_to(self.project_root)
                except ValueError:
                    # File outside project root, skip
                    continue

                source_id = str(rel_path)

                # Check if needs reindexing
                if not force:
                    existing_meta = existing.get(source_id)
                    if existing_meta:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if not self._needs_reindex(existing_meta, mtime):
                            # Also check content hash for extra safety
                            try:
                                text = file_path.read_text(encoding="utf-8")
                                content_hash = self._hash_content(text)
                                if existing_meta.get("content_hash") == content_hash:
                                    continue
                            except (UnicodeDecodeError, OSError):
                                # Skip files that can't be read
                                continue

                # Read file content
                try:
                    text = file_path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    # Skip files that can't be read as text
                    continue

                # Skip empty files
                if not text.strip():
                    continue

                # Generate content hash
                content_hash = self._hash_content(text)

                # Generate embedding
                embedding = self.embedding_engine.encode([text])[0]

                # Create metadata
                metadata = {
                    "source_type": "file",
                    "source_id": source_id,
                    "file_path": str(rel_path),
                    "extension": file_path.suffix,
                    "updated_at": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat(),
                    "indexed_at": datetime.now().isoformat(),
                    "content_hash": content_hash,
                }

                # Add to vector store (metadata as list)
                self.vector_store.add(embedding, [metadata])
                indexed_count += 1

        # Save vector store if any updates
        if indexed_count > 0:
            path = self.project_root / ".clauxton" / "semantic" / "file_index"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save(path)

        return indexed_count

    def index_all(
        self,
        file_patterns: Optional[List[str]] = None,
        force: bool = False,
    ) -> Dict[str, int]:
        """
        Index all sources (KB, tasks, files).

        Args:
            file_patterns: Patterns for files to index (default: ["**/*.py"])
            force: If True, reindex all items regardless of change status

        Returns:
            Dictionary with counts by source type

        Example:
            >>> counts = indexer.index_all()
            >>> print(counts)
            {'kb': 10, 'tasks': 5, 'files': 50}
        """
        if file_patterns is None:
            file_patterns = ["**/*.py"]

        kb_count = self.index_knowledge_base(force=force)
        task_count = self.index_tasks(force=force)
        file_count = self.index_files(file_patterns, force=force)

        return {
            "kb": kb_count,
            "tasks": task_count,
            "files": file_count,
        }

    def clear_index(self, source_type: Optional[str] = None) -> int:
        """
        Clear index for a specific source type or all sources.

        Args:
            source_type: Type to clear ("kb", "task", "file"), or None for all

        Returns:
            Number of items removed

        Example:
            >>> count = indexer.clear_index("kb")
            >>> print(f"Removed {count} KB entries from index")
        """
        if source_type is None:
            # Clear all
            initial_size = self.vector_store.size()
            self.vector_store.clear()
            path = self.project_root / ".clauxton" / "semantic" / "index"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save(path)
            return initial_size

        # Clear specific source type
        removed = 0
        all_metadata = self.vector_store.metadata

        for i, meta in enumerate(all_metadata):
            if meta.get("source_type") == source_type:
                # Mark for removal (we'll rebuild the store)
                removed += 1

        if removed > 0:
            # Rebuild store without the removed items
            new_store = VectorStore(dimension=self.vector_store.dimension)

            for i, meta in enumerate(all_metadata):
                if meta.get("source_type") != source_type:
                    # Keep this item
                    vectors = self.vector_store.index.reconstruct_n(i, 1)
                    new_store.add(vectors[0], [meta])

            # Replace store
            self.vector_store = new_store
            path = self.project_root / ".clauxton" / "semantic" / "index"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save(path)

        return removed

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_existing_metadata(self, source_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get existing metadata for a source type.

        Args:
            source_type: Type of source ("kb", "task", "file")

        Returns:
            Dictionary mapping source_id to metadata
        """
        result: Dict[str, Dict[str, Any]] = {}

        all_metadata = self.vector_store.metadata
        for meta in all_metadata:
            if meta.get("source_type") == source_type:
                source_id = meta.get("source_id")
                if source_id:
                    result[source_id] = meta

        return result

    def _needs_reindex(
        self, existing_meta: Dict[str, Any], updated_at: datetime
    ) -> bool:
        """
        Check if item needs reindexing based on timestamp.

        Args:
            existing_meta: Existing metadata from vector store
            updated_at: Updated timestamp of the item

        Returns:
            True if item needs reindexing
        """
        existing_updated_at = existing_meta.get("updated_at")
        if not existing_updated_at:
            return True

        # Parse existing timestamp
        try:
            existing_dt = datetime.fromisoformat(existing_updated_at)
        except (ValueError, TypeError):
            return True

        # Compare timestamps
        return updated_at > existing_dt

    def _hash_content(self, text: str) -> str:
        """
        Generate hash of content for change detection.

        Args:
            text: Text content to hash

        Returns:
            SHA256 hash (hex string)
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _extract_kb_text(self, entry: Any) -> str:
        """
        Extract text from KB entry for embedding.

        Args:
            entry: KnowledgeBaseEntry

        Returns:
            Combined text (title + content + tags)
        """
        tags_text = " ".join(entry.tags) if entry.tags else ""
        return f"{entry.title}\n{entry.content}\n{tags_text}".strip()

    def _extract_task_text(self, task: Any) -> str:
        """
        Extract text from task for embedding.

        Args:
            task: Task

        Returns:
            Combined text (name + description)
        """
        description = task.description or ""
        return f"{task.name}\n{description}".strip()
