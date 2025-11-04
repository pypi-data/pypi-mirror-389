"""
Migration utilities for Clauxton v0.15.0 Unified Memory Model.

This module provides tools to migrate existing Knowledge Base and Task data
to the new unified Memory System format.

Features:
- Migrate KB entries to Memory (type=knowledge)
- Migrate Tasks to Memory (type=task)
- Automatic backup creation before migration
- Rollback capability if migration fails
- Dry-run mode for preview
- Legacy ID preservation for backward compatibility

Example:
    >>> from pathlib import Path
    >>> migrator = MemoryMigrator(Path("."))
    >>> result = migrator.migrate_all()
    >>> print(result)
    {'kb_count': 15, 'task_count': 8, 'total': 23}
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.memory import Memory, MemoryEntry
from clauxton.core.task_manager import TaskManager

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Migration failed."""

    pass


class MemoryMigrator:
    """
    Migrate existing KB/Tasks to Memory format.

    This migrator handles the conversion of existing Knowledge Base entries
    and Task Management data to the new unified Memory System format.

    Attributes:
        project_root: Project root directory
        dry_run: If True, preview only without writing changes
        memory: Memory instance for unified storage
        clauxton_dir: .clauxton directory path
        kb_file: Path to knowledge-base.yml
        tasks_file: Path to tasks.yml
        memories_file: Path to memories.yml

    Example:
        >>> migrator = MemoryMigrator(Path("."), dry_run=True)
        >>> result = migrator.migrate_all()
        >>> print(f"Would migrate {result['total']} entries")
    """

    def __init__(self, project_root: Path | str, dry_run: bool = False) -> None:
        """
        Initialize migrator.

        Args:
            project_root: Project root directory (Path or str)
            dry_run: If True, don't write changes (preview mode)

        Example:
            >>> migrator = MemoryMigrator(Path("."), dry_run=True)
            >>> migrator = MemoryMigrator(".", dry_run=False)
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.dry_run = dry_run
        self.memory = Memory(self.project_root)
        self.clauxton_dir = self.project_root / ".clauxton"

        self.kb_file = self.clauxton_dir / "knowledge-base.yml"
        self.tasks_file = self.clauxton_dir / "tasks.yml"
        self.memories_file = self.clauxton_dir / "memories.yml"

    def migrate_all(self) -> Dict[str, int]:
        """
        Migrate all data (KB + Tasks).

        Performs complete migration of Knowledge Base and Tasks to Memory format.
        Creates backup before migration unless in dry-run mode.

        Returns:
            Dictionary with migration statistics:
                - kb_count: Number of KB entries migrated
                - task_count: Number of tasks migrated
                - total: Total entries migrated

        Example:
            >>> result = migrator.migrate_all()
            >>> print(f"Migrated {result['total']} entries")
            Migrated 23 entries
        """
        backup_path = None

        if not self.dry_run:
            backup_path = self.create_rollback_backup()
            logger.info(f"Backup created: {backup_path}")

        try:
            kb_count = self.migrate_knowledge_base()
            task_count = self.migrate_tasks()

            return {"kb_count": kb_count, "task_count": task_count, "total": kb_count + task_count}

        except Exception as e:
            # If migration fails and we have a backup, inform user about rollback
            if backup_path and not self.dry_run:
                logger.error(
                    f"Migration failed: {e}. You can rollback using: "
                    f"clauxton migrate rollback {backup_path}"
                )
            raise MigrationError(f"Migration failed: {e}") from e

    def migrate_knowledge_base(self) -> int:
        """
        Convert KB entries to Memory entries (type=knowledge).

        Migrates all Knowledge Base entries to the Memory system, preserving:
        - Original title, content, category, tags
        - Creation and update timestamps
        - Legacy ID for backward compatibility

        Returns:
            Number of entries migrated

        Example:
            >>> count = migrator.migrate_knowledge_base()
            >>> print(f"Migrated {count} KB entries")
            Migrated 15 KB entries
        """
        if not self.kb_file.exists():
            logger.info("No knowledge-base.yml found, skipping KB migration")
            return 0

        kb = KnowledgeBase(self.project_root)
        entries = kb.list_all()

        if not entries:
            logger.info("Knowledge Base is empty, nothing to migrate")
            return 0

        migrated = 0
        for kb_entry in entries:
            # Create Memory entry from KB entry
            memory_entry = MemoryEntry(
                id=self._generate_memory_id(),
                type="knowledge",
                title=kb_entry.title,
                content=kb_entry.content,
                category=kb_entry.category,
                tags=kb_entry.tags,
                created_at=kb_entry.created_at,
                updated_at=kb_entry.updated_at,
                related_to=[],
                source="import",
                confidence=1.0,
                legacy_id=kb_entry.id,
            )

            if not self.dry_run:
                self.memory.add(memory_entry)

            migrated += 1
            logger.info(f"Migrated KB entry: {kb_entry.id} → {memory_entry.id}")

        return migrated

    def migrate_tasks(self) -> int:
        """
        Convert Tasks to Memory entries (type=task).

        Migrates all Task Management entries to the Memory system, preserving:
        - Task name (→ title), description (→ content)
        - Priority (→ category), tags
        - Dependencies (→ related_to)
        - Creation and update timestamps
        - Legacy ID for backward compatibility

        Returns:
            Number of tasks migrated

        Example:
            >>> count = migrator.migrate_tasks()
            >>> print(f"Migrated {count} tasks")
            Migrated 8 tasks
        """
        if not self.tasks_file.exists():
            logger.info("No tasks.yml found, skipping Task migration")
            return 0

        task_mgr = TaskManager(self.project_root)
        tasks = task_mgr.list_all()

        if not tasks:
            logger.info("Task list is empty, nothing to migrate")
            return 0

        migrated = 0
        for task in tasks:
            # Use description if available, otherwise use name
            content = task.description if task.description else task.name

            # Create Memory entry from Task
            memory_entry = MemoryEntry(
                id=self._generate_memory_id(),
                type="task",
                title=task.name,
                content=content,
                category=task.priority,  # Use priority as category
                tags=[],  # Tasks don't have tags, use empty list
                created_at=task.created_at,
                updated_at=task.created_at,  # Tasks don't have updated_at
                related_to=task.depends_on,  # Preserve dependencies
                source="import",
                confidence=1.0,
                legacy_id=task.id,
            )

            if not self.dry_run:
                self.memory.add(memory_entry)

            migrated += 1
            logger.info(f"Migrated Task: {task.id} → {memory_entry.id}")

        return migrated

    def create_rollback_backup(self) -> Path:
        """
        Create backup before migration.

        Creates timestamped backup of all relevant files:
        - knowledge-base.yml
        - tasks.yml
        - memories.yml (if exists)

        Returns:
            Path to backup directory

        Example:
            >>> backup_path = migrator.create_rollback_backup()
            >>> print(backup_path)
            /path/to/project/.clauxton/backups/pre_migration_20260127_143052
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.clauxton_dir / "backups" / f"pre_migration_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing files
        files_to_backup = [
            self.kb_file,
            self.tasks_file,
            self.memories_file,
        ]

        backed_up_files = []
        for file in files_to_backup:
            if file.exists():
                shutil.copy2(file, backup_dir / file.name)
                backed_up_files.append(file.name)
                logger.info(f"Backed up: {file.name}")

        if not backed_up_files:
            logger.warning("No files found to backup")

        return backup_dir

    def rollback(self, backup_path: Path | str) -> None:
        """
        Rollback migration from backup.

        Restores files from backup directory to .clauxton directory.
        Use this if migration fails or produces unexpected results.

        Args:
            backup_path: Path to backup directory (Path or str)

        Raises:
            MigrationError: If backup path doesn't exist or is invalid

        Example:
            >>> backup_path = Path(".clauxton/backups/pre_migration_20260127_143052")
            >>> migrator.rollback(backup_path)
            >>> # Files restored from backup
        """
        backup_path_obj: Path = (
            Path(backup_path) if isinstance(backup_path, str) else backup_path
        )

        if not backup_path_obj.exists():
            raise MigrationError(f"Backup not found: {backup_path_obj}")

        if not backup_path_obj.is_dir():
            raise MigrationError(f"Backup path is not a directory: {backup_path_obj}")

        # Restore files
        restored_files = []
        for backup_file in backup_path_obj.glob("*.yml"):
            target = self.clauxton_dir / backup_file.name
            shutil.copy2(backup_file, target)
            restored_files.append(backup_file.name)
            logger.info(f"Restored: {backup_file.name}")

        if not restored_files:
            raise MigrationError(f"No backup files found in: {backup_path_obj}")

        logger.info(f"Rollback complete: restored {len(restored_files)} files")

    def _generate_memory_id(self) -> str:
        """
        Generate unique Memory ID.

        Generates IDs in format "MEM-YYYYMMDD-NNN" where NNN is a
        sequential number starting from 001 each day.

        Returns:
            Memory ID string (e.g., "MEM-20260127-001")

        Example:
            >>> memory_id = migrator._generate_memory_id()
            >>> memory_id
            'MEM-20260127-001'
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        # Get existing memories
        memories = self.memory.list_all()
        today_memories = [m for m in memories if m.id.startswith(f"MEM-{date_str}")]

        if not today_memories:
            seq = 1
        else:
            # Extract sequence numbers and get max
            seqs = [int(m.id.split("-")[-1]) for m in today_memories]
            seq = max(seqs) + 1

        return f"MEM-{date_str}-{seq:03d}"
