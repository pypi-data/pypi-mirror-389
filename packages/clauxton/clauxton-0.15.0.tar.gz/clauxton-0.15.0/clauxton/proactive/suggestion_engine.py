"""
Proactive Suggestion Engine for Clauxton.

Analyzes file change patterns and generates intelligent suggestions for:
- Knowledge Base entries
- Tasks
- Refactoring opportunities
- Documentation updates
- Anomaly detection
"""

from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

# Day 5: Behavior tracking and context awareness (lazy imports to avoid circular dependencies)
# These will be imported when needed
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from clauxton.core.models import Priority
from clauxton.proactive.models import DetectedPattern, FileChange

if TYPE_CHECKING:
    from clauxton.proactive.behavior_tracker import BehaviorTracker
    from clauxton.proactive.context_manager import ContextManager


class SuggestionType(str, Enum):
    """Types of suggestions that can be generated."""

    KB_ENTRY = "kb_entry"
    TASK = "task"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    CONFLICT = "conflict"
    ANOMALY = "anomaly"


class Suggestion(BaseModel):
    """A proactive suggestion generated from pattern analysis."""

    type: SuggestionType
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    affected_files: List[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    suggestion_id: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class SuggestionEngine:
    """
    Analyzes patterns and generates proactive suggestions.

    The engine uses various heuristics to detect:
    - Need for documentation (multiple related files changed)
    - Task opportunities (TODOs, incomplete features)
    - Refactoring needs (large changes, complexity)
    - Anomalies (unusual patterns)
    """

    # Code quality thresholds
    MAX_FUNCTION_LINES = 50  # Functions longer than this may need refactoring
    MAX_FILE_LINES = 500  # Files longer than this may need splitting
    MAX_NESTING_DEPTH = 4  # Nesting deeper than this indicates complexity
    DOCUMENTATION_GAP_THRESHOLD = 3  # Files without docs trigger suggestion

    def __init__(
        self,
        project_root: Path,
        min_confidence: float = 0.7,
        behavior_tracker: Optional["BehaviorTracker"] = None,
        context_manager: Optional["ContextManager"] = None,
    ):
        """
        Initialize suggestion engine.

        Args:
            project_root: Root directory of the project
            min_confidence: Minimum confidence score for suggestions (default: 0.7)
            behavior_tracker: Optional BehaviorTracker for personalization (Day 5)
            context_manager: Optional ContextManager for context awareness (Day 5)
        """
        self.project_root = project_root
        self.min_confidence = min_confidence
        self._suggestion_counter = 0

        # Day 5: Behavior tracking and context awareness
        self.behavior_tracker = behavior_tracker
        self.context_manager = context_manager

    def analyze_pattern(self, pattern: DetectedPattern) -> List[Suggestion]:
        """
        Generate suggestions from a detected pattern.

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            List of Suggestion objects
        """
        suggestions: List[Suggestion] = []

        # Try different suggestion strategies
        kb_suggestion = self._suggest_kb_entry(pattern)
        if kb_suggestion and kb_suggestion.confidence >= self.min_confidence:
            suggestions.append(kb_suggestion)

        task_suggestion = self._suggest_task(pattern)
        if task_suggestion and task_suggestion.confidence >= self.min_confidence:
            suggestions.append(task_suggestion)

        refactor_suggestion = self._suggest_refactor(pattern)
        if refactor_suggestion and refactor_suggestion.confidence >= self.min_confidence:
            suggestions.append(refactor_suggestion)

        anomaly_suggestion = self._detect_anomaly(pattern)
        if anomaly_suggestion and anomaly_suggestion.confidence >= self.min_confidence:
            suggestions.append(anomaly_suggestion)

        # Day 2: Advanced suggestions
        doc_suggestion = self._suggest_documentation(pattern)
        if doc_suggestion and doc_suggestion.confidence >= self.min_confidence:
            suggestions.append(doc_suggestion)

        code_smell_suggestions = self._detect_code_smells(pattern)
        suggestions.extend(
            [s for s in code_smell_suggestions if s.confidence >= self.min_confidence]
        )

        # Rank and deduplicate
        return self.rank_suggestions(suggestions)

    def analyze_changes(self, changes: List[FileChange]) -> List[Suggestion]:
        """
        Generate suggestions from file changes.

        Args:
            changes: List of FileChange objects

        Returns:
            List of Suggestion objects
        """
        if not changes:
            return []

        suggestions: List[Suggestion] = []

        # Group changes by file
        files_changed = {str(change.path) for change in changes}

        # Check for module-wide changes (KB entry suggestion)
        if len(files_changed) >= 3:
            kb_suggestion = self._suggest_kb_from_files(list(files_changed))
            if kb_suggestion and kb_suggestion.confidence >= self.min_confidence:
                suggestions.append(kb_suggestion)

        # Check for rapid changes (anomaly)
        time_window = timedelta(minutes=10)
        recent_changes = [
            c
            for c in changes
            if c.timestamp > datetime.now() - time_window
        ]
        if len(recent_changes) > 10:
            anomaly = self._create_rapid_change_anomaly(recent_changes)
            if anomaly.confidence >= self.min_confidence:
                suggestions.append(anomaly)

        # Day 2: Advanced analysis
        # Check for file deletion pattern
        deletion_suggestion = self.detect_file_deletion_pattern(changes)
        if deletion_suggestion and deletion_suggestion.confidence >= self.min_confidence:
            suggestions.append(deletion_suggestion)

        # Check for weekend activity
        weekend_suggestion = self.detect_weekend_activity(changes)
        if weekend_suggestion and weekend_suggestion.confidence >= self.min_confidence:
            suggestions.append(weekend_suggestion)

        # Check for late-night activity (separate from weekend)
        late_night_suggestion = self.detect_late_night_activity(changes)
        if late_night_suggestion and late_night_suggestion.confidence >= self.min_confidence:
            suggestions.append(late_night_suggestion)

        return self.rank_suggestions(suggestions)

    def _suggest_kb_entry(self, pattern: DetectedPattern) -> Optional[Suggestion]:
        """
        Suggest KB entry based on pattern.

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            Suggestion or None
        """
        # Convert Path objects to strings
        files = [str(f) for f in pattern.files]
        if not files:
            return None

        common_prefix = self._get_common_path_prefix(files)
        if not common_prefix:
            return None

        # Use pattern confidence as base
        confidence = min(0.9, pattern.confidence + len(files) * 0.05)

        return Suggestion(
            type=SuggestionType.KB_ENTRY,
            title=f"Document changes in {common_prefix}",
            description=f"Multiple files in {common_prefix} have been modified. "
            f"Consider documenting the changes.",
            confidence=confidence,
            reasoning=f"Pattern '{pattern.pattern_type.value}' detected with {len(files)} files",
            affected_files=files,
            priority=Priority.MEDIUM,
            metadata={"pattern": pattern.pattern_type.value, "file_count": len(files)},
            suggestion_id=self._generate_id(),
        )

    def _suggest_kb_from_files(self, files: List[str]) -> Optional[Suggestion]:
        """
        Suggest KB entry based on file list.

        Args:
            files: List of file paths

        Returns:
            Suggestion or None
        """
        common_prefix = self._get_common_path_prefix(files)
        if not common_prefix:
            return None

        confidence = min(0.9, 0.6 + len(files) * 0.05)

        return Suggestion(
            type=SuggestionType.KB_ENTRY,
            title=f"Document module: {common_prefix}",
            description=f"Significant changes across {len(files)} files in {common_prefix}. "
            f"Consider adding architecture documentation.",
            confidence=confidence,
            reasoning=f"{len(files)} files modified in same module",
            affected_files=files,
            priority=Priority.HIGH if len(files) >= 5 else Priority.MEDIUM,
            metadata={"module": common_prefix, "file_count": len(files)},
            suggestion_id=self._generate_id(),
        )

    def _suggest_task(self, pattern: DetectedPattern) -> Optional[Suggestion]:
        """
        Suggest task based on pattern.

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            Suggestion or None
        """
        # Look for incomplete features (code modified but no tests)
        files = [str(f) for f in pattern.files]
        if not files:
            return None

        has_code = any(
            f.endswith((".py", ".js", ".ts"))
            and not f.startswith("test_")
            and "/tests/" not in f
            for f in files
        )
        has_tests = any(f.startswith("test_") or "/tests/" in f for f in files)

        if has_code and not has_tests:
            confidence = 0.75
            return Suggestion(
                type=SuggestionType.TASK,
                title="Add tests for recent changes",
                description="Code files modified without corresponding tests. "
                "Consider adding test coverage.",
                confidence=confidence,
                reasoning="Code changes without test coverage detected",
                affected_files=files,
                priority=Priority.HIGH,
                metadata={"pattern": pattern.pattern_type.value, "missing_tests": True},
                suggestion_id=self._generate_id(),
            )

        return None

    def _suggest_refactor(self, pattern: DetectedPattern) -> Optional[Suggestion]:
        """
        Suggest refactoring based on pattern.

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            Suggestion or None
        """
        files = [str(f) for f in pattern.files]
        large_files = [f for f in files if "large" in f.lower()]

        if large_files:
            confidence = 0.70
            return Suggestion(
                type=SuggestionType.REFACTOR,
                title="Consider splitting large files",
                description="Large file changes detected. Consider refactoring "
                "into smaller, more manageable modules.",
                confidence=confidence,
                reasoning="Large file modifications detected",
                affected_files=large_files,
                priority=Priority.LOW,
                metadata={"pattern": pattern.pattern_type.value},
                suggestion_id=self._generate_id(),
            )

        return None

    def _detect_anomaly(self, pattern: DetectedPattern) -> Optional[Suggestion]:
        """
        Detect anomalies in pattern.

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            Suggestion or None
        """
        # For now, we don't detect anomalies from patterns directly
        # Anomalies are detected from rapid changes
        return None

    def _create_rapid_change_anomaly(self, changes: List[FileChange]) -> Suggestion:
        """
        Create anomaly suggestion for rapid changes.

        Args:
            changes: List of recent FileChange objects

        Returns:
            Suggestion
        """
        files = list({str(c.path) for c in changes})
        confidence = min(0.9, 0.7 + len(changes) / 50)

        return Suggestion(
            type=SuggestionType.ANOMALY,
            title=f"Rapid changes: {len(changes)} changes in 10 minutes",
            description=f"{len(changes)} file changes detected in last 10 minutes. "
            f"Unusual activity pattern detected.",
            confidence=confidence,
            reasoning=f"{len(changes)} changes in short time window",
            affected_files=files,
            priority=Priority.HIGH if len(changes) > 20 else Priority.MEDIUM,
            metadata={"change_count": len(changes), "file_count": len(files)},
            suggestion_id=self._generate_id(),
        )

    def rank_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """
        Rank suggestions by confidence and priority.

        Day 5: Now uses behavior tracking to adjust confidence based on user preferences.

        Args:
            suggestions: List of Suggestion objects

        Returns:
            Sorted list of Suggestion objects
        """
        if not suggestions:
            return []

        # Remove duplicates based on title
        seen_titles = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.title not in seen_titles:
                seen_titles.add(suggestion.title)
                unique_suggestions.append(suggestion)

        # Day 5: Adjust confidence based on user preferences
        if self.behavior_tracker:
            for suggestion in unique_suggestions:
                adjusted_confidence = self.behavior_tracker.adjust_confidence(
                    suggestion.confidence, suggestion.type
                )
                suggestion.confidence = adjusted_confidence

        # Sort by confidence (desc) then priority (critical > high > medium > low)
        priority_order = {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1,
        }

        return sorted(
            unique_suggestions,
            key=lambda s: (s.confidence, priority_order[s.priority]),
            reverse=True,
        )

    def calculate_confidence(self, evidence: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on evidence.

        Args:
            evidence: Dictionary with:
                - pattern_frequency: float (0-1)
                - file_relevance: float (0-1)
                - historical_accuracy: float (0-1)
                - user_context: float (0-1)

        Returns:
            Confidence score (0.0-1.0)
        """
        weights = {
            "pattern_frequency": 0.3,
            "file_relevance": 0.25,
            "historical_accuracy": 0.25,
            "user_context": 0.2,
        }

        score = 0.0
        for key, weight in weights.items():
            value = evidence.get(key, 0.0)
            score += min(1.0, max(0.0, value)) * weight

        return min(1.0, max(0.0, score))

    def _get_common_path_prefix(self, files: List[str]) -> str:
        """
        Get common path prefix for multiple files.

        Args:
            files: List of file paths

        Returns:
            Common prefix (directory name or empty string)
        """
        if not files:
            return ""

        if len(files) == 1:
            path = Path(files[0])
            return path.parent.name if path.parent != Path(".") else path.name

        paths = [Path(f).parts for f in files]
        common_parts = []

        for parts in zip(*paths):
            if len(set(parts)) == 1:
                common_parts.append(parts[0])
            else:
                break

        if not common_parts:
            return ""

        return "/".join(common_parts)

    def _generate_id(self) -> str:
        """
        Generate unique suggestion ID.

        Returns:
            Suggestion ID (e.g., "SUGG-001")
        """
        self._suggestion_counter += 1
        return f"SUGG-{self._suggestion_counter:03d}"

    # ========================================================================
    # Day 2: Advanced Suggestion Methods
    # ========================================================================

    def _suggest_documentation(self, pattern: DetectedPattern) -> Optional[Suggestion]:
        """
        Suggest documentation updates based on pattern.

        Detects:
        - New modules without README
        - New Python files without docstrings
        - New packages without __init__.py documentation

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            Suggestion or None
        """
        files = [str(f) for f in pattern.files]
        if not files:
            return None

        # Check for new Python files (potential documentation gap)
        new_py_files = [
            f for f in files
            if f.endswith(".py") and "__init__" not in f
        ]

        # Check for new directories (potential README gap)
        directories = set()
        for f in files:
            parent = str(Path(f).parent)
            if parent != ".":
                directories.add(parent)

        # Multiple new Python files suggest need for documentation
        if len(new_py_files) >= self.DOCUMENTATION_GAP_THRESHOLD:
            confidence = min(0.85, 0.6 + len(new_py_files) * 0.05)
            return Suggestion(
                type=SuggestionType.DOCUMENTATION,
                title=f"Add documentation for {len(new_py_files)} new files",
                description=f"{len(new_py_files)} new Python files created. "
                f"Consider adding docstrings and module documentation.",
                confidence=confidence,
                reasoning=f"{len(new_py_files)} new files without documentation",
                affected_files=new_py_files,
                priority=Priority.MEDIUM,
                metadata={
                    "file_count": len(new_py_files),
                    "documentation_gap": True,
                },
                suggestion_id=self._generate_id(),
            )

        # New directory suggests need for README
        if len(directories) >= 2 and pattern.pattern_type.value == "new_feature":
            confidence = 0.75
            return Suggestion(
                type=SuggestionType.DOCUMENTATION,
                title="Add README for new module",
                description="New module structure detected. "
                "Consider adding README to explain the architecture.",
                confidence=confidence,
                reasoning=f"New module with {len(directories)} directories",
                affected_files=list(directories),
                priority=Priority.MEDIUM,
                metadata={
                    "directory_count": len(directories),
                    "needs_readme": True,
                },
                suggestion_id=self._generate_id(),
            )

        return None

    def _detect_code_smells(self, pattern: DetectedPattern) -> List[Suggestion]:
        """
        Detect code smells in pattern.

        Detects:
        - Large files (>500 lines)
        - Potential complexity issues
        - Files with many changes (instability)

        Args:
            pattern: DetectedPattern to analyze

        Returns:
            List of Suggestion objects
        """
        suggestions: List[Suggestion] = []
        files = [str(f) for f in pattern.files]

        if not files:
            return suggestions

        # Detect potentially large files by name patterns
        large_file_indicators = ["large", "big", "main", "utils", "helpers"]
        potentially_large_files = [
            f for f in files
            if any(indicator in f.lower() for indicator in large_file_indicators)
        ]

        if potentially_large_files:
            confidence = 0.70
            suggestions.append(
                Suggestion(
                    type=SuggestionType.REFACTOR,
                    title="Review file size and complexity",
                    description=f"Files with names suggesting large size detected: "
                    f"{', '.join([Path(f).name for f in potentially_large_files])}. "
                    f"Consider checking if they need to be split.",
                    confidence=confidence,
                    reasoning="File names suggest potential size/complexity issues",
                    affected_files=potentially_large_files,
                    priority=Priority.LOW,
                    metadata={
                        "code_smell": "large_file",
                        "file_count": len(potentially_large_files),
                    },
                    suggestion_id=self._generate_id(),
                )
            )

        # Detect files modified many times (instability indicator)
        if len(files) >= 5 and pattern.confidence > 0.8:
            # Check if these are test files
            test_files = [f for f in files if "test" in f.lower()]
            is_mostly_tests = len(test_files) > len(files) * 0.5

            if is_mostly_tests:
                # Skip - will be handled by test organization check below
                pass
            else:
                confidence = 0.72
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.REFACTOR,
                        title="High change frequency detected",
                        description=f"{len(files)} files changed frequently. "
                        f"This may indicate design instability or unclear requirements.",
                        confidence=confidence,
                        reasoning=f"Frequent changes to {len(files)} files",
                        affected_files=files,
                        priority=Priority.MEDIUM,
                        metadata={
                            "code_smell": "change_frequency",
                            "file_count": len(files),
                            "pattern_confidence": pattern.confidence,
                        },
                        suggestion_id=self._generate_id(),
                    )
                )

        # Detect test files that might need refactoring
        test_files = [f for f in files if "test" in f.lower()]
        if len(test_files) >= 5:
            confidence = 0.70  # Increased from 0.68 to meet threshold
            suggestions.append(
                Suggestion(
                    type=SuggestionType.REFACTOR,
                    title="Consider test organization",
                    description=f"{len(test_files)} test files modified. "
                    f"Consider grouping related tests or using fixtures.",
                    confidence=confidence,
                    reasoning=f"Many test files ({len(test_files)}) modified",
                    affected_files=test_files,
                    priority=Priority.LOW,
                    metadata={
                        "code_smell": "test_organization",
                        "test_file_count": len(test_files),
                    },
                    suggestion_id=self._generate_id(),
                )
            )

        return suggestions

    def analyze_file_content(self, file_path: Path) -> List[Suggestion]:
        """
        Analyze actual file content for code quality issues.

        This is a more advanced analysis that reads file content.

        Args:
            file_path: Path to file to analyze

        Returns:
            List of Suggestion objects
        """
        suggestions: List[Suggestion] = []

        try:
            if not file_path.exists():
                return suggestions

            # Only analyze text files
            if file_path.suffix not in [".py", ".js", ".ts", ".java", ".go"]:
                return suggestions

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            line_count = len(lines)
            file_str = str(file_path)

            # Check file size
            if line_count > self.MAX_FILE_LINES:
                confidence = min(0.85, 0.6 + (line_count - self.MAX_FILE_LINES) / 1000)
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.REFACTOR,
                        title=f"Large file: {file_path.name} ({line_count} lines)",
                        description=f"File has {line_count} lines, exceeding "
                        f"recommended maximum of {self.MAX_FILE_LINES}. "
                        f"Consider splitting into smaller modules.",
                        confidence=confidence,
                        reasoning=f"File size {line_count} lines exceeds {self.MAX_FILE_LINES}",
                        affected_files=[file_str],
                        priority=Priority.MEDIUM,
                        metadata={
                            "code_smell": "large_file",
                            "line_count": line_count,
                            "threshold": self.MAX_FILE_LINES,
                        },
                        suggestion_id=self._generate_id(),
                    )
                )

            # Check for missing docstrings (Python)
            if file_path.suffix == ".py":
                has_module_docstring = False
                for i, line in enumerate(lines[:10]):  # Check first 10 lines
                    if '"""' in line or "'''" in line:
                        has_module_docstring = True
                        break

                if not has_module_docstring and line_count > 20:
                    confidence = 0.75
                    suggestions.append(
                        Suggestion(
                            type=SuggestionType.DOCUMENTATION,
                            title=f"Add docstring to {file_path.name}",
                            description=f"Python module has {line_count} lines but no "
                            f"module-level docstring. Consider adding documentation.",
                            confidence=confidence,
                            reasoning="Missing module docstring in Python file",
                            affected_files=[file_str],
                            priority=Priority.LOW,
                            metadata={
                                "documentation_gap": True,
                                "file_type": "python",
                                "line_count": line_count,
                            },
                            suggestion_id=self._generate_id(),
                        )
                    )

            # Check for deep nesting (simple heuristic: count leading spaces)
            max_indent = 0
            for line in lines:
                if line.strip():  # Non-empty line
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent // 4)  # Assume 4-space indent

            if max_indent > self.MAX_NESTING_DEPTH:
                confidence = 0.78
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.REFACTOR,
                        title=f"Deep nesting in {file_path.name}",
                        description=f"File has nesting depth of ~{max_indent} levels. "
                        f"Consider extracting functions to reduce complexity.",
                        confidence=confidence,
                        reasoning=f"Nesting depth {max_indent} exceeds {self.MAX_NESTING_DEPTH}",
                        affected_files=[file_str],
                        priority=Priority.MEDIUM,
                        metadata={
                            "code_smell": "deep_nesting",
                            "nesting_depth": max_indent,
                            "threshold": self.MAX_NESTING_DEPTH,
                        },
                        suggestion_id=self._generate_id(),
                    )
                )

        except Exception:
            # If we can't read the file, just return empty suggestions
            pass

        return [s for s in suggestions if s.confidence >= self.min_confidence]

    def detect_file_deletion_pattern(self, changes: List[FileChange]) -> Optional[Suggestion]:
        """
        Detect if many files are being deleted (cleanup or removal pattern).

        Args:
            changes: List of FileChange objects

        Returns:
            Suggestion or None
        """
        from clauxton.proactive.models import ChangeType

        deleted_files = [
            str(c.path) for c in changes
            if c.change_type == ChangeType.DELETED
        ]

        if len(deleted_files) >= 5:
            confidence = min(0.85, 0.65 + len(deleted_files) * 0.03)
            return Suggestion(
                type=SuggestionType.ANOMALY,
                title=f"Mass deletion: {len(deleted_files)} files deleted",
                description=f"{len(deleted_files)} files have been deleted. "
                f"Ensure this is intentional and update documentation if needed.",
                confidence=confidence,
                reasoning=f"{len(deleted_files)} files deleted in short period",
                affected_files=deleted_files,
                priority=Priority.HIGH,
                metadata={
                    "deletion_count": len(deleted_files),
                    "requires_verification": True,
                },
                suggestion_id=self._generate_id(),
            )

        return None

    def detect_weekend_activity(self, changes: List[FileChange]) -> Optional[Suggestion]:
        """
        Detect unusual weekend activity.

        Note: This method only checks weekend patterns.
        For late-night detection, use detect_late_night_activity().

        Args:
            changes: List of FileChange objects

        Returns:
            Suggestion or None
        """
        if not changes:
            return None

        weekend_changes = []

        for change in changes:
            # Weekend: Saturday (5) or Sunday (6)
            if change.timestamp.weekday() >= 5:
                weekend_changes.append(change)

        total = len(changes)
        weekend_ratio = len(weekend_changes) / total if total > 0 else 0

        # If more than 50% of changes are on weekend
        if weekend_ratio > 0.5 and total >= 5:
            confidence = 0.70
            return Suggestion(
                type=SuggestionType.ANOMALY,
                title="High weekend activity detected",
                description=f"{len(weekend_changes)} out of {total} changes occurred "
                f"on weekends. This may indicate deadline pressure or unusual work patterns.",
                confidence=confidence,
                reasoning=f"Weekend activity ratio: {weekend_ratio:.1%}",
                affected_files=[str(c.path) for c in weekend_changes[:5]],
                priority=Priority.LOW,
                metadata={
                    "anomaly_type": "weekend_activity",
                    "weekend_count": len(weekend_changes),
                    "total_count": total,
                    "ratio": weekend_ratio,
                },
                suggestion_id=self._generate_id(),
            )

        return None

    def detect_late_night_activity(self, changes: List[FileChange]) -> Optional[Suggestion]:
        """
        Detect unusual late-night activity.

        Args:
            changes: List of FileChange objects

        Returns:
            Suggestion or None
        """
        if not changes:
            return None

        late_night_changes = []

        for change in changes:
            # Late night: 10 PM - 6 AM
            hour = change.timestamp.hour
            if hour >= 22 or hour <= 6:
                late_night_changes.append(change)

        total = len(changes)
        late_night_ratio = len(late_night_changes) / total if total > 0 else 0

        # If more than 40% of changes are late night
        if late_night_ratio > 0.4 and total >= 5:
            confidence = 0.70  # Increased from 0.68 to meet min_confidence threshold
            return Suggestion(
                type=SuggestionType.ANOMALY,
                title="Late-night activity detected",
                description=f"{len(late_night_changes)} out of {total} changes occurred "
                f"late at night (10 PM - 6 AM). Consider work-life balance.",
                confidence=confidence,
                reasoning=f"Late-night activity ratio: {late_night_ratio:.1%}",
                affected_files=[str(c.path) for c in late_night_changes[:5]],
                priority=Priority.LOW,
                metadata={
                    "anomaly_type": "late_night_activity",
                    "late_night_count": len(late_night_changes),
                    "total_count": total,
                    "ratio": late_night_ratio,
                },
                suggestion_id=self._generate_id(),
            )

        return None

    # ========================================================================
    # Day 5: Context-Aware Suggestion Methods
    # ========================================================================

    def get_context_aware_suggestions(self) -> List[Suggestion]:
        """
        Generate context-aware suggestions based on current project state.

        Uses ContextManager to understand:
        - Current git branch (feature/fix/etc)
        - Time of day (morning/afternoon/evening)
        - Active files
        - Current task

        Returns:
            List of context-aware Suggestion objects
        """
        if not self.context_manager:
            return []

        suggestions: List[Suggestion] = []
        context = self.context_manager.get_current_context()

        # Morning suggestions: Planning and review
        if context.time_context == "morning":
            suggestions.append(
                Suggestion(
                    type=SuggestionType.TASK,
                    title="Plan today's work",
                    description="Good morning! Review your task list and prioritize today's work.",
                    confidence=0.75,
                    reasoning="Morning is ideal for planning",
                    affected_files=[],
                    priority=Priority.MEDIUM,
                    metadata={"context": "morning", "time_based": True},
                    suggestion_id=self._generate_id(),
                )
            )

        # Feature branch suggestions: Document feature
        if context.is_feature_branch and context.current_branch:
            branch_name = context.current_branch.replace("feature/", "").replace(
                "feat/", ""
            )
            suggestions.append(
                Suggestion(
                    type=SuggestionType.KB_ENTRY,
                    title=f"Document feature: {branch_name}",
                    description=f"You're working on feature branch '{context.current_branch}'. "
                    f"Consider documenting this feature in the Knowledge Base.",
                    confidence=0.80,
                    reasoning="Feature branch detected, KB documentation recommended",
                    affected_files=[],
                    priority=Priority.MEDIUM,
                    metadata={
                        "context": "feature_branch",
                        "branch": context.current_branch,
                    },
                    suggestion_id=self._generate_id(),
                )
            )

        # Active files suggestions: Related work
        if context.active_files and len(context.active_files) >= 3:
            # Group by directory
            directories = set()
            for file in context.active_files:
                parent = str(Path(file).parent)
                if parent != ".":
                    directories.add(parent)

            if len(directories) >= 2:
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.KB_ENTRY,
                        title=f"Document changes across {len(directories)} modules",
                        description=f"You've been working in {len(directories)} different modules. "
                        f"Consider documenting cross-module changes.",
                        confidence=0.78,
                        reasoning=f"Active changes in {len(directories)} modules",
                        affected_files=context.active_files[:5],
                        priority=Priority.MEDIUM,
                        metadata={
                            "context": "active_files",
                            "directory_count": len(directories),
                        },
                        suggestion_id=self._generate_id(),
                    )
                )

        # Current task suggestions
        if context.current_task:
            suggestions.append(
                Suggestion(
                    type=SuggestionType.TASK,
                    title=f"Review progress on {context.current_task}",
                    description=f"You're working on {context.current_task}. "
                    f"Consider updating its status.",
                    confidence=0.72,
                    reasoning="Current task detected from branch/commits",
                    affected_files=[],
                    priority=Priority.LOW,
                    metadata={
                        "context": "current_task",
                        "task_id": context.current_task,
                    },
                    suggestion_id=self._generate_id(),
                )
            )

        # Evening suggestions: Wrap up and document
        if context.time_context == "evening":
            if context.active_files:
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.KB_ENTRY,
                        title="Document today's changes before wrapping up",
                        description=f"You've modified {len(context.active_files)} files today. "
                        f"Consider documenting key changes before ending the day.",
                        confidence=0.77,
                        reasoning="Evening time, good to document before finishing",
                        affected_files=context.active_files[:5],
                        priority=Priority.MEDIUM,
                        metadata={
                            "context": "evening",
                            "time_based": True,
                            "file_count": len(context.active_files),
                        },
                        suggestion_id=self._generate_id(),
                    )
                )

        # Night suggestions: Work-life balance
        if context.time_context == "night":
            suggestions.append(
                Suggestion(
                    type=SuggestionType.ANOMALY,
                    title="Late-night work detected",
                    description="You're working late. Consider taking a break and "
                    "resuming tomorrow if possible.",
                    confidence=0.70,
                    reasoning="Night-time activity detected",
                    affected_files=[],
                    priority=Priority.LOW,
                    metadata={"context": "night", "work_life_balance": True},
                    suggestion_id=self._generate_id(),
                )
            )

        # Long session suggestions
        if context.work_session_start:
            session_duration = datetime.now() - context.work_session_start
            if session_duration > timedelta(hours=3):
                hours = int(session_duration.total_seconds() / 3600)
                suggestions.append(
                    Suggestion(
                        type=SuggestionType.TASK,
                        title="Long work session - consider a break",
                        description=f"You've been working for {hours} hours. "
                        f"Consider taking a break to maintain productivity.",
                        confidence=0.73,
                        reasoning=f"Work session duration: {hours} hours",
                        affected_files=[],
                        priority=Priority.LOW,
                        metadata={
                            "context": "long_session",
                            "duration_hours": hours,
                        },
                        suggestion_id=self._generate_id(),
                    )
                )

        # Filter by confidence and return
        return [s for s in suggestions if s.confidence >= self.min_confidence]
