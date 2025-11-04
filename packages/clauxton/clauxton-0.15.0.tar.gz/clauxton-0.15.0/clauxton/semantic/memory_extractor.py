"""
Memory extraction from Git commits for Clauxton v0.15.0.

This module automatically extracts architectural decisions and code patterns
from Git commit history to populate the unified Memory system.

Key Features:
- Extract decisions from commit messages (feat:, refactor:, migration)
- Detect patterns from code diffs (API, UI, database changes)
- Confidence scoring for auto-extracted memories
- Auto-add to Memory system
- Handle edge cases (merge commits, initial commits, empty diffs)

Example:
    >>> from pathlib import Path
    >>> from clauxton.semantic.memory_extractor import MemoryExtractor
    >>> extractor = MemoryExtractor(Path("."))
    >>> memories = extractor.extract_from_recent_commits(since_days=7)
    >>> len(memories)
    5
    >>> extractor.extract_from_recent_commits(since_days=7, auto_add=True)
"""

import re
from pathlib import Path
from typing import Any, List, Optional, Set

from clauxton.analysis.git_analyzer import CommitInfo, GitAnalyzer
from clauxton.core.memory import Memory, MemoryEntry

# Conventional commit patterns
DECISION_PATTERNS = {
    # Migration/refactoring (high confidence: 0.9)
    "migration": [
        r"(?i)migrate(?:d)?\s+(?:to|from)\s+(\w+)",
        r"(?i)switch(?:ed)?\s+(?:to|from)\s+(\w+)",
        r"(?i)replace(?:d)?\s+(\w+)\s+with\s+(\w+)",
        r"(?i)move(?:d)?\s+(?:to|from)\s+(\w+)",
    ],
    # Feature additions (medium-high confidence: 0.8)
    "feature": [
        r"^feat(?:\([^)]+\))?:\s*(.+)",
        r"^add(?:\([^)]+\))?:\s*(.+)",
        r"(?i)implement(?:ed)?\s+(.+)",
        r"(?i)introduce(?:d)?\s+(.+)",
    ],
    # Refactoring (medium confidence: 0.7)
    "refactor": [
        r"^refactor(?:\([^)]+\))?:\s*(.+)",
        r"(?i)refactor(?:ed)?\s+(.+)",
        r"(?i)restructure(?:d)?\s+(.+)",
    ],
    # Performance improvements (medium confidence: 0.7)
    "performance": [
        r"^perf(?:\([^)]+\))?:\s*(.+)",
        r"(?i)optimize(?:d)?\s+(.+)",
        r"(?i)improve(?:d)?\s+performance\s+(?:of|for)\s+(.+)",
    ],
    # Architecture changes (medium-high confidence: 0.85)
    "architecture": [
        r"(?i)architect(?:ure)?\s+(.+)",
        r"(?i)design(?:ed)?\s+(.+)",
        r"(?i)pattern\s+(.+)",
    ],
}

# Pattern detection thresholds for code changes
PATTERN_THRESHOLDS: dict[str, Any] = {
    "api": {"files": 2, "extensions": {".py", ".js", ".ts", ".go", ".java", ".rs"}},
    "ui": {"files": 3, "extensions": {".jsx", ".tsx", ".vue", ".html", ".css", ".scss"}},
    "database": {
        "files": 1,
        "patterns": [
            r"migration",
            r"schema",
            r"models?\.py",
            r"database",
            r"\.sql$",
        ],
    },
    "test": {
        "files": 2,
        "patterns": [r"test_", r"_test\.", r"\.test\.", r"\.spec\."],
    },
}


class MemoryExtractorError(Exception):
    """Base exception for MemoryExtractor errors."""

    pass


class MemoryExtractor:
    """
    Extract memories from Git commits and code changes.

    Analyzes Git commit history to automatically extract:
    - Architectural decisions from commit messages
    - Code patterns from diffs
    - Related tags and categories

    Attributes:
        project_root: Project root directory
        git_analyzer: GitAnalyzer instance for commit analysis
        memory: Memory instance for storage

    Example:
        >>> extractor = MemoryExtractor(Path("."))
        >>> memories = extractor.extract_from_commit("abc123")
        >>> len(memories)
        2
        >>> memories[0].type
        'decision'
    """

    def __init__(self, project_root: Path) -> None:
        """
        Initialize MemoryExtractor.

        Args:
            project_root: Project root directory

        Raises:
            NotAGitRepositoryError: If project is not a Git repository
            ImportError: If GitPython is not installed
        """
        self.project_root = project_root
        self.git_analyzer = GitAnalyzer(project_root)
        self.memory = Memory(project_root)

    def extract_from_commit(
        self, commit_sha: str, auto_add: bool = False
    ) -> List[MemoryEntry]:
        """
        Extract memories from a single commit.

        Analyzes commit message for decisions and diff for patterns.

        Args:
            commit_sha: Commit SHA hash
            auto_add: If True, automatically add to Memory system

        Returns:
            List of extracted MemoryEntry objects

        Example:
            >>> memories = extractor.extract_from_commit("abc123")
            >>> len(memories)
            2
            >>> memories[0].type
            'decision'
        """
        # Get commit info
        commit_info = self.git_analyzer.analyze_commit(commit_sha)

        memories: List[MemoryEntry] = []

        # Extract decision from commit message
        decision = self._extract_decision(commit_info.message, commit_info)
        if decision:
            memories.append(decision)

        # Detect patterns from diff
        patterns = self._detect_patterns(commit_info.diff, commit_info)
        memories.extend(patterns)

        # Auto-add if requested
        if auto_add:
            for memory in memories:
                try:
                    self.memory.add(memory)
                except Exception:
                    # Skip if already exists or validation fails
                    pass

        return memories

    def extract_from_recent_commits(
        self, since_days: int = 7, auto_add: bool = False
    ) -> List[MemoryEntry]:
        """
        Extract memories from recent commits.

        Args:
            since_days: Number of days to look back (default: 7)
            auto_add: If True, automatically add to Memory system

        Returns:
            List of extracted MemoryEntry objects

        Example:
            >>> memories = extractor.extract_from_recent_commits(since_days=7)
            >>> len(memories)
            10
        """
        commits = self.git_analyzer.get_recent_commits(since_days=since_days)

        all_memories: List[MemoryEntry] = []

        for commit_info in commits:
            memories = self.extract_from_commit(commit_info.sha, auto_add=auto_add)
            all_memories.extend(memories)

        return all_memories

    def _extract_decision(
        self, commit_message: str, commit: CommitInfo
    ) -> Optional[MemoryEntry]:
        """
        Extract architectural decision from commit message.

        Patterns:
        - "feat:", "fix:", "refactor:", "perf:"
        - "Switch to X", "Migrate to Y", "Replace X with Y"
        - "Add authentication", "Implement caching"

        Args:
            commit_message: Commit message text
            commit: CommitInfo object for context

        Returns:
            MemoryEntry if decision detected, None otherwise

        Example:
            >>> decision = extractor._extract_decision("feat: Add user authentication", commit)
            >>> decision.type
            'decision'
            >>> decision.confidence
            0.8
        """
        # Get first line (subject)
        lines = commit_message.strip().split("\n")
        subject = lines[0].strip()

        # Get body (if exists)
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        decision_type: Optional[str] = None
        confidence = 0.5
        extracted_content: Optional[str] = None

        # Try to match decision patterns
        for pattern_type, patterns in DECISION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, subject)
                if match:
                    decision_type = pattern_type
                    extracted_content = match.group(1) if match.groups() else subject
                    # Set confidence based on pattern type
                    if pattern_type == "migration":
                        confidence = 0.9
                    elif pattern_type in ["feature", "architecture"]:
                        confidence = 0.8
                    else:
                        confidence = 0.7
                    break
            if decision_type:
                break

        # No decision pattern matched
        if not decision_type or not extracted_content:
            return None

        # Generate memory ID
        memory_id = self._generate_memory_id()

        # Extract tags from commit message
        tags = self._extract_tags(commit_message)

        # Determine category
        category = self._determine_category(commit_message, commit.files)

        # Build content
        content_parts = [extracted_content]
        if body:
            content_parts.append(f"\nDetails: {body}")
        content_parts.append(f"\nCommit: {commit.sha[:7]} by {commit.author}")

        content = "\n".join(content_parts)

        # Create MemoryEntry
        return MemoryEntry(
            id=memory_id,
            type="decision",
            title=extracted_content[:200],  # Limit to 200 chars
            content=content,
            category=category,
            tags=tags,
            created_at=commit.date,
            updated_at=commit.date,
            source="git-commit",
            confidence=confidence,
            source_ref=commit.sha,
        )

    def _detect_patterns(
        self, diff: str, commit: CommitInfo
    ) -> List[MemoryEntry]:
        """
        Detect code patterns from diff.

        Examples:
        - API changes (2+ API files modified)
        - UI changes (3+ UI files modified)
        - Database changes (1+ migration/schema files)
        - Test patterns

        Args:
            diff: Commit diff text
            commit: CommitInfo object for context

        Returns:
            List of MemoryEntry objects for detected patterns

        Example:
            >>> patterns = extractor._detect_patterns(diff, commit)
            >>> len(patterns)
            1
            >>> patterns[0].type
            'pattern'
        """
        patterns: List[MemoryEntry] = []

        # Get file paths
        file_paths = [f.lower() for f in commit.files]

        # Check API pattern
        api_threshold = PATTERN_THRESHOLDS["api"]
        api_extensions: set[str] = api_threshold["extensions"]
        api_files_threshold: int = api_threshold["files"]
        api_files = [
            f
            for f in commit.files
            if Path(f).suffix in api_extensions
            and any(
                keyword in f.lower()
                for keyword in ["api", "endpoint", "route", "handler", "controller"]
            )
        ]
        if len(api_files) >= api_files_threshold:
            pattern = self._create_pattern_memory(
                pattern_type="api",
                title=f"API changes in {len(api_files)} files",
                files=api_files,
                commit=commit,
                confidence=0.8,
            )
            patterns.append(pattern)

        # Check UI pattern
        ui_threshold = PATTERN_THRESHOLDS["ui"]
        ui_extensions: set[str] = ui_threshold["extensions"]
        ui_files_threshold: int = ui_threshold["files"]
        ui_files = [
            f
            for f in commit.files
            if Path(f).suffix in ui_extensions
        ]
        if len(ui_files) >= ui_files_threshold:
            pattern = self._create_pattern_memory(
                pattern_type="ui",
                title=f"UI changes in {len(ui_files)} files",
                files=ui_files,
                commit=commit,
                confidence=0.7,
            )
            patterns.append(pattern)

        # Check database pattern
        db_threshold = PATTERN_THRESHOLDS["database"]
        db_patterns: list[str] = db_threshold["patterns"]
        db_files_threshold: int = db_threshold["files"]
        db_files = [
            f
            for f in file_paths
            if any(re.search(p, f) for p in db_patterns)
        ]
        if len(db_files) >= db_files_threshold:
            pattern = self._create_pattern_memory(
                pattern_type="database",
                title=f"Database changes in {len(db_files)} files",
                files=db_files,
                commit=commit,
                confidence=0.9,
            )
            patterns.append(pattern)

        # Check test pattern
        test_threshold = PATTERN_THRESHOLDS["test"]
        test_patterns: list[str] = test_threshold["patterns"]
        test_files_threshold: int = test_threshold["files"]
        test_files = [
            f
            for f in file_paths
            if any(re.search(p, f) for p in test_patterns)
        ]
        if len(test_files) >= test_files_threshold:
            pattern = self._create_pattern_memory(
                pattern_type="test",
                title=f"Test changes in {len(test_files)} files",
                files=test_files,
                commit=commit,
                confidence=0.6,
            )
            patterns.append(pattern)

        return patterns

    def _create_pattern_memory(
        self,
        pattern_type: str,
        title: str,
        files: List[str],
        commit: CommitInfo,
        confidence: float,
    ) -> MemoryEntry:
        """
        Create a pattern MemoryEntry.

        Args:
            pattern_type: Pattern type (api, ui, database, test)
            title: Memory title
            files: List of affected files
            commit: CommitInfo object
            confidence: Confidence score (0.0-1.0)

        Returns:
            MemoryEntry object
        """
        memory_id = self._generate_memory_id()

        # Build content
        content_parts = [
            f"Pattern detected: {pattern_type}",
            f"Files affected: {len(files)}",
            "- " + "\n- ".join(files[:10]),  # Limit to 10 files
        ]
        if len(files) > 10:
            content_parts.append(f"... and {len(files) - 10} more files")
        commit_msg_first = commit.message.split(chr(10))[0][:50]
        content_parts.append(f"\nCommit: {commit.sha[:7]} - {commit_msg_first}")
        content_parts.append(f"Author: {commit.author}")

        content = "\n".join(content_parts)

        # Extract tags
        tags = [pattern_type, "auto-detected"]

        return MemoryEntry(
            id=memory_id,
            type="pattern",
            title=title,
            content=content,
            category=pattern_type,
            tags=tags,
            created_at=commit.date,
            updated_at=commit.date,
            source="git-commit",
            confidence=confidence,
            source_ref=commit.sha,
        )

    def _extract_tags(self, text: str) -> List[str]:
        """
        Extract relevant tags from text.

        Args:
            text: Text to extract tags from

        Returns:
            List of tags (lowercase, no duplicates)

        Example:
            >>> tags = extractor._extract_tags("feat: Add authentication with JWT")
            >>> tags
            ['authentication', 'jwt']
        """
        # Common keywords to extract as tags
        keywords = [
            "api",
            "authentication",
            "auth",
            "jwt",
            "oauth",
            "database",
            "db",
            "cache",
            "redis",
            "postgres",
            "postgresql",
            "mysql",
            "mongodb",
            "ui",
            "frontend",
            "backend",
            "rest",
            "graphql",
            "websocket",
            "docker",
            "kubernetes",
            "k8s",
            "ci",
            "cd",
            "test",
            "testing",
            "security",
            "performance",
            "optimization",
            "migration",
            "refactor",
            "bug",
            "fix",
        ]

        text_lower = text.lower()
        tags: Set[str] = set()

        for keyword in keywords:
            if keyword in text_lower:
                tags.add(keyword)

        return sorted(list(tags))

    def _determine_category(self, commit_message: str, files: List[str]) -> str:
        """
        Determine category from commit message and files.

        Args:
            commit_message: Commit message text
            files: List of modified files

        Returns:
            Category string (e.g., "architecture", "api", "database")

        Example:
            >>> category = extractor._determine_category("feat: Add API endpoint", ["api/users.py"])
            >>> category
            'api'
        """
        message_lower = commit_message.lower()

        # Check for explicit categories in message
        if any(word in message_lower for word in ["architect", "design", "pattern"]):
            return "architecture"
        if any(word in message_lower for word in ["api", "endpoint", "route"]):
            return "api"
        if any(word in message_lower for word in ["database", "migration", "schema"]):
            return "database"
        if any(word in message_lower for word in ["ui", "frontend", "component"]):
            return "ui"
        if any(word in message_lower for word in ["test", "testing"]):
            return "test"
        if any(word in message_lower for word in ["security", "auth"]):
            return "security"
        if any(word in message_lower for word in ["performance", "optimize"]):
            return "performance"

        # Check files for category hints
        file_paths = [f.lower() for f in files]
        if any("api" in f for f in file_paths):
            return "api"
        if any("test" in f for f in file_paths):
            return "test"
        if any("ui" in f or "frontend" in f for f in file_paths):
            return "ui"
        if any("migration" in f or "schema" in f for f in file_paths):
            return "database"

        # Default category
        return "general"

    def _generate_memory_id(self) -> str:
        """
        Generate unique memory ID.

        Returns:
            Memory ID in format "MEM-YYYYMMDD-NNN"

        Example:
            >>> memory_id = extractor._generate_memory_id()
            >>> memory_id
            'MEM-20251103-001'
        """
        return self.memory._generate_memory_id()
