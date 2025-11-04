"""
Pattern extractor for Git commits.

Extracts patterns, keywords, and categories from commit messages and diffs.
"""

import re
from typing import Any, Dict, List, Set

from clauxton.analysis.git_analyzer import CommitInfo


class PatternExtractor:
    """
    Pattern extractor for commits.

    Extracts patterns, keywords, and categories from commits.
    """

    # Conventional Commits prefixes
    COMMIT_TYPES = {
        "feat": "feature",
        "fix": "bugfix",
        "refactor": "refactor",
        "docs": "docs",
        "test": "test",
        "chore": "chore",
        "style": "style",
        "perf": "performance",
        "ci": "ci",
        "build": "build",
        "revert": "revert",
    }

    # Keywords for pattern detection
    FEATURE_KEYWORDS = [
        "add", "implement", "create", "introduce", "support",
        "enable", "allow", "provide",
    ]

    BUGFIX_KEYWORDS = [
        "fix", "bug", "issue", "error", "crash", "problem",
        "resolve", "correct", "patch",
    ]

    REFACTOR_KEYWORDS = [
        "refactor", "cleanup", "reorganize", "restructure",
        "improve", "optimize", "simplify",
    ]

    TEST_KEYWORDS = [
        "test", "spec", "unittest", "integration", "e2e",
        "coverage", "mock", "fixture",
    ]

    DOCS_KEYWORDS = [
        "docs", "documentation", "readme", "guide", "tutorial",
        "example", "comment", "docstring",
    ]

    def __init__(self) -> None:
        """Initialize PatternExtractor."""
        pass

    def detect_patterns(self, commit_info: CommitInfo) -> Dict[str, Any]:
        """
        Detect all patterns in a commit.

        Args:
            commit_info: CommitInfo object

        Returns:
            Dictionary with detected patterns
        """
        message_patterns = self.extract_from_message(commit_info.message)
        file_patterns = self.extract_from_files(commit_info.files)
        diff_patterns = self.extract_from_diff(commit_info.diff)

        # Determine primary category
        category = self.categorize_commit(commit_info)

        # Extract keywords
        keywords = self.extract_keywords(commit_info.message)

        # Detect module/component
        module = self.detect_module(commit_info.files)

        # Estimate impact
        impact = self.estimate_impact(commit_info)

        return {
            "category": category,
            "keywords": keywords,
            "module": module,
            "impact": impact,
            "message_patterns": message_patterns,
            "file_patterns": file_patterns,
            "diff_patterns": diff_patterns,
        }

    def extract_from_message(self, message: str) -> Dict[str, Any]:
        """
        Extract patterns from commit message.

        Args:
            message: Commit message

        Returns:
            Dictionary with patterns
        """
        patterns: Dict[str, Any] = {
            "conventional_commits": False,
            "type": None,
            "scope": None,
            "breaking": False,
            "has_issue_ref": False,
            "issue_numbers": [],
        }

        # Check Conventional Commits format
        # Format: type(scope)!: subject
        match = re.match(
            r"^(feat|fix|refactor|docs|test|chore|style|perf|ci|build|revert)"
            r"(?:\(([^)]+)\))?(!)?:\s+(.+)",
            message,
            re.IGNORECASE,
        )

        if match:
            patterns["conventional_commits"] = True
            patterns["type"] = self.COMMIT_TYPES.get(
                match.group(1).lower(), match.group(1).lower()
            )
            patterns["scope"] = match.group(2)
            patterns["breaking"] = match.group(3) == "!"

        # Extract issue references (#123, GH-123, etc.)
        issue_refs = re.findall(r"#(\d+)|GH-(\d+)|ISSUE-(\d+)", message, re.IGNORECASE)
        if issue_refs:
            patterns["has_issue_ref"] = True
            # Flatten and filter None values
            patterns["issue_numbers"] = [
                ref for group in issue_refs for ref in group if ref
            ]

        return patterns

    def extract_from_files(self, files: List[str]) -> Dict[str, Any]:
        """
        Extract patterns from modified files.

        Args:
            files: List of file paths

        Returns:
            Dictionary with file patterns
        """
        patterns: Dict[str, Any] = {
            "file_types": set(),  # Will be converted to list
            "directories": set(),  # Will be converted to list
            "test_files": False,
            "doc_files": False,
            "config_files": False,
        }
        # Type hints for sets
        file_types_set: set[str] = patterns["file_types"]  # type: ignore
        directories_set: set[str] = patterns["directories"]  # type: ignore

        for file in files:
            # Extract file extension
            if "." in file:
                ext = file.split(".")[-1]
                file_types_set.add(ext)

            # Extract directory
            if "/" in file:
                directory = file.split("/")[0]
                directories_set.add(directory)

            # Detect special file types
            file_lower = file.lower()
            if any(keyword in file_lower for keyword in ["test", "spec"]):
                patterns["test_files"] = True
            if any(keyword in file_lower for keyword in ["readme", "doc", "md"]):
                patterns["doc_files"] = True
            if any(keyword in file_lower for keyword in ["config", "settings", ".env"]):
                patterns["config_files"] = True

        # Convert sets to lists for JSON serialization
        patterns["file_types"] = list(file_types_set)
        patterns["directories"] = list(directories_set)

        return patterns

    def extract_from_diff(self, diff: str) -> Dict[str, Any]:
        """
        Extract patterns from diff.

        Args:
            diff: Commit diff

        Returns:
            Dictionary with diff patterns
        """
        patterns: Dict[str, Any] = {
            "has_imports": False,
            "has_class_def": False,
            "has_function_def": False,
            "has_comments": False,
            "language_hints": set(),  # Will be converted to list
        }
        # Type hint for set
        language_hints_set: set[str] = patterns["language_hints"]  # type: ignore

        if not diff:
            # Convert to list before returning
            patterns["language_hints"] = []
            return patterns

        # Detect language patterns
        if "import " in diff or "from " in diff:
            patterns["has_imports"] = True
            language_hints_set.add("python")

        if re.search(r"\bclass\s+\w+", diff):
            patterns["has_class_def"] = True

        if re.search(r"\bdef\s+\w+\(", diff):
            patterns["has_function_def"] = True
            language_hints_set.add("python")

        if re.search(r"\bfunction\s+\w+\(", diff):
            patterns["has_function_def"] = True
            language_hints_set.add("javascript")

        if re.search(r"#.*$|//.*$|/\*.*\*/", diff, re.MULTILINE):
            patterns["has_comments"] = True

        # Convert sets to lists
        patterns["language_hints"] = list(language_hints_set)

        return patterns

    def categorize_commit(self, commit_info: CommitInfo) -> str:
        """
        Categorize commit based on message and files.

        Args:
            commit_info: CommitInfo object

        Returns:
            Category string (feature/bugfix/refactor/docs/test/chore)
        """
        message = commit_info.message.lower()

        # Check Conventional Commits
        for prefix, category in self.COMMIT_TYPES.items():
            if message.startswith(f"{prefix}:") or message.startswith(f"{prefix}("):
                return category

        # Keyword-based detection
        if any(keyword in message for keyword in self.BUGFIX_KEYWORDS):
            return "bugfix"

        if any(keyword in message for keyword in self.FEATURE_KEYWORDS):
            return "feature"

        if any(keyword in message for keyword in self.REFACTOR_KEYWORDS):
            return "refactor"

        if any(keyword in message for keyword in self.TEST_KEYWORDS):
            return "test"

        if any(keyword in message for keyword in self.DOCS_KEYWORDS):
            return "docs"

        # File-based detection
        files_str = " ".join(commit_info.files).lower()
        if "test" in files_str or "spec" in files_str:
            return "test"

        if "readme" in files_str or "docs" in files_str or ".md" in files_str:
            return "docs"

        # Default
        return "chore"

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Remove special characters and lowercase
        text = re.sub(r"[^\w\s]", " ", text.lower())

        # Split into words
        words = text.split()

        # Filter stop words and short words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can",
        }

        keywords = [
            word for word in words
            if len(word) > 3 and word not in stop_words
        ]

        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords[:10]  # Limit to top 10

    def detect_module(self, files: List[str]) -> str:
        """
        Detect module/component from file paths.

        Args:
            files: List of file paths

        Returns:
            Module name or "unknown"
        """
        if not files:
            return "unknown"

        # Extract first directory from each file
        directories = []
        for file in files:
            if "/" in file:
                directory = file.split("/")[0]
                directories.append(directory)

        if not directories:
            return "unknown"

        # Return most common directory
        from collections import Counter
        counter = Counter(directories)
        most_common = counter.most_common(1)[0][0]

        return most_common

    def estimate_impact(self, commit_info: CommitInfo) -> str:
        """
        Estimate impact of commit (low/medium/high).

        Args:
            commit_info: CommitInfo object

        Returns:
            Impact level (low/medium/high)
        """
        stats = commit_info.stats

        # Calculate total changes
        total_changes = stats["insertions"] + stats["deletions"]
        files_changed = stats["files_changed"]

        # Impact scoring
        if total_changes > 500 or files_changed > 10:
            return "high"
        elif total_changes > 100 or files_changed > 5:
            return "medium"
        else:
            return "low"
