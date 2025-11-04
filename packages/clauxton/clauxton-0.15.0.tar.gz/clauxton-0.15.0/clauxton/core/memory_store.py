"""
Storage backend for Memory entries.

Provides persistent storage for Memory entries with:
- YAML format (human-readable, Git-friendly)
- Atomic writes (temp file + rename)
- Automatic backups before modifications
- In-memory caching for performance
- Fast lookup index

Storage format:
    .clauxton/
        memories.yml          # All memory entries (YAML list)
        memories.index        # Fast lookup index (JSON)
        backups/
            memories_YYYYMMDD_HHMMSS.yml

Example:
    >>> store = MemoryStore(Path("."))
    >>> entries = store.load_all()
    >>> store.save(entry)
    >>> store.rebuild_index()
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from clauxton.core.memory import MemoryEntry
from clauxton.utils.file_utils import ensure_clauxton_dir, set_secure_permissions
from clauxton.utils.yaml_utils import read_yaml, write_yaml


class MemoryStore:
    """
    Storage backend for Memory entries.

    Provides CRUD operations with YAML persistence, atomic writes,
    automatic backups, and in-memory caching.

    Storage Structure:
        - memories.yml: Main storage file (YAML)
        - memories.index: Fast lookup index (JSON)
        - backups/: Timestamped backups

    Attributes:
        project_root: Project root directory
        clauxton_dir: .clauxton directory path
        memories_file: Path to memories.yml
        index_file: Path to memories.index
        backup_dir: Path to backups directory
        _cache: In-memory cache of entries
        _index: In-memory index for fast lookup

    Example:
        >>> store = MemoryStore(Path("."))
        >>> entries = store.load_all()
        >>> entry = MemoryEntry(...)
        >>> store.save(entry)
        >>> success = store.delete("MEM-20260127-001")
    """

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize MemoryStore.

        Args:
            project_root: Project root directory (Path or str)

        Example:
            >>> store = MemoryStore(Path("."))
            >>> store = MemoryStore(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.clauxton_dir = ensure_clauxton_dir(project_root)
        self.memories_file = self.clauxton_dir / "memories.yml"
        self.index_file = self.clauxton_dir / "memories.index"
        self.backup_dir = self.clauxton_dir / "backups"

        # In-memory cache
        self._cache: Optional[List[MemoryEntry]] = None
        self._index: Optional[Dict[str, int]] = None  # memory_id -> index in list

        # Ensure files exist
        self._ensure_files_exist()

    def load_all(self) -> List[MemoryEntry]:
        """
        Load all memories with caching.

        Uses in-memory cache if available, otherwise reads from disk.

        Returns:
            List of all MemoryEntry objects

        Example:
            >>> entries = store.load_all()
            >>> len(entries)
            42
        """
        if self._cache is not None:
            return self._cache

        # Read from disk
        data = read_yaml(self.memories_file)

        if not data or "memories" not in data:
            self._cache = []
            return []

        # Parse entries
        entries = []
        for entry_data in data["memories"]:
            # Parse datetime fields
            if "created_at" in entry_data and isinstance(
                entry_data["created_at"], str
            ):
                entry_data["created_at"] = datetime.fromisoformat(
                    entry_data["created_at"]
                )
            if "updated_at" in entry_data and isinstance(
                entry_data["updated_at"], str
            ):
                entry_data["updated_at"] = datetime.fromisoformat(
                    entry_data["updated_at"]
                )

            entries.append(MemoryEntry(**entry_data))

        # Update cache
        self._cache = entries
        self._rebuild_index_cache()

        return entries

    def save(self, entry: MemoryEntry) -> None:
        """
        Save memory with atomic write.

        If memory ID already exists, replaces it. Otherwise, appends.

        Args:
            entry: MemoryEntry to save

        Example:
            >>> entry = MemoryEntry(...)
            >>> store.save(entry)
        """
        entries = self.load_all()

        # Check if entry exists (update) or is new (append)
        existing_index = None
        for i, e in enumerate(entries):
            if e.id == entry.id:
                existing_index = i
                break

        if existing_index is not None:
            # Update existing
            entries[existing_index] = entry
        else:
            # Append new
            entries.append(entry)

        # Save to disk
        self._save_entries(entries)
        self._invalidate_cache()

    def delete(self, memory_id: str) -> bool:
        """
        Delete memory by ID.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if deleted, False if not found

        Example:
            >>> success = store.delete("MEM-20260127-001")
            >>> success
            True
        """
        entries = self.load_all()

        # Find and remove entry
        initial_count = len(entries)
        entries = [e for e in entries if e.id != memory_id]

        if len(entries) == initial_count:
            # Entry not found
            return False

        # Save updated list
        self._save_entries(entries)
        self._invalidate_cache()

        return True

    def rebuild_index(self) -> None:
        """
        Rebuild search index from memories.yml.

        Creates fast lookup index (JSON) for memory IDs.

        Example:
            >>> store.rebuild_index()
        """
        entries = self.load_all()
        index = {entry.id: i for i, entry in enumerate(entries)}

        # Write index to JSON
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2)
            set_secure_permissions(self.index_file)
        except Exception:
            # Index is optional, continue without it
            pass

        # Update in-memory index
        self._index = index

    def create_backup(self) -> Path:
        """
        Create backup of memories.yml.

        Returns:
            Path to backup file

        Example:
            >>> backup_path = store.create_backup()
            >>> backup_path.name
            'memories_20260127_143052.yml'
        """
        if not self.memories_file.exists():
            raise FileNotFoundError(f"Memory file does not exist: {self.memories_file}")

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"memories_{timestamp}.yml"

        # Copy file
        import shutil
        shutil.copy2(self.memories_file, backup_path)
        set_secure_permissions(backup_path)

        return backup_path

    def _save_entries(self, entries: List[MemoryEntry]) -> None:
        """
        Save entries to YAML with atomic write.

        Args:
            entries: List of MemoryEntry objects to save
        """
        # Convert entries to dict format
        entries_data = []
        for entry in entries:
            entry_dict = entry.model_dump()
            # Convert datetime to ISO format string
            entry_dict["created_at"] = entry.created_at.isoformat()
            entry_dict["updated_at"] = entry.updated_at.isoformat()
            entries_data.append(entry_dict)

        # Create data structure
        data = {
            "version": "1.0",
            "project_name": self.project_root.name,
            "memories": entries_data,
        }

        # Write with backup
        write_yaml(self.memories_file, data, backup=True)
        set_secure_permissions(self.memories_file)

        # Rebuild index
        self.rebuild_index()

    def _ensure_files_exist(self) -> None:
        """
        Create memory files if they don't exist.

        Creates minimal YAML structure.
        """
        if not self.memories_file.exists():
            initial_data: Dict[str, Any] = {
                "version": "1.0",
                "project_name": self.project_root.name,
                "memories": [],
            }
            write_yaml(self.memories_file, initial_data, backup=False)
            set_secure_permissions(self.memories_file)

    def _invalidate_cache(self) -> None:
        """Invalidate in-memory cache."""
        self._cache = None
        self._index = None

    def _rebuild_index_cache(self) -> None:
        """Rebuild in-memory index from cache."""
        if self._cache is not None:
            self._index = {entry.id: i for i, entry in enumerate(self._cache)}
