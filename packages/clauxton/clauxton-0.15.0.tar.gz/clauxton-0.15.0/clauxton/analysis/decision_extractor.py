"""
Decision extractor for Clauxton.

Extracts technical decisions from Git commit history for Knowledge Base.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from clauxton.analysis.git_analyzer import CommitInfo, GitAnalyzer
from clauxton.analysis.pattern_extractor import PatternExtractor
from clauxton.core.knowledge_base import KnowledgeBase


class DecisionCandidate:
    """Candidate for Knowledge Base entry."""

    def __init__(
        self,
        title: str,
        category: str,
        content: str,
        tags: List[str],
        commit_sha: str,
        confidence: float,
        reasoning: str,
    ):
        self.title = title
        self.category = category
        self.content = content
        self.tags = tags
        self.commit_sha = commit_sha
        self.confidence = confidence
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "tags": self.tags,
            "commit_sha": self.commit_sha,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class DecisionExtractor:
    """
    Decision extractor.

    Extracts technical decisions from commits for Knowledge Base.
    """

    # Keywords indicating decisions
    DECISION_KEYWORDS = [
        "adopt", "choose", "decide", "select", "switch to", "migrate to",
        "move to", "replace with", "use instead", "prefer", "standardize on",
    ]

    # Architecture/design keywords
    ARCHITECTURE_KEYWORDS = [
        "architecture", "design", "pattern", "approach", "structure",
        "framework", "library", "tool", "technology", "stack",
    ]

    # Constraint keywords
    CONSTRAINT_KEYWORDS = [
        "limit", "maximum", "minimum", "restrict", "require", "must",
        "cannot", "should not", "forbidden", "prohibited",
    ]

    # Convention keywords
    CONVENTION_KEYWORDS = [
        "convention", "style", "format", "naming", "standard",
        "guideline", "best practice", "code style",
    ]

    # Dependency files to monitor
    DEPENDENCY_FILES = [
        "package.json", "requirements.txt", "Pipfile", "Cargo.toml",
        "go.mod", "pom.xml", "build.gradle", "composer.json",
    ]

    # Config files to monitor
    CONFIG_FILES = [
        ".env", "config.yml", "config.yaml", "settings.py", "config.py",
        ".config", "tsconfig.json", "webpack.config.js",
    ]

    def __init__(self, project_root: Path):
        """
        Initialize DecisionExtractor.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.git_analyzer = GitAnalyzer(project_root)
        self.pattern_extractor = PatternExtractor()
        self.kb = KnowledgeBase(project_root)

    def extract_decisions(
        self,
        since_days: int = 30,
        max_candidates: int = 10,
    ) -> List[DecisionCandidate]:
        """
        Extract decision candidates from recent commits.

        Args:
            since_days: Number of days to analyze
            max_candidates: Maximum number of candidates

        Returns:
            List of DecisionCandidate objects
        """
        # Get recent commits
        commits = self.git_analyzer.get_recent_commits(since_days=since_days)

        candidates = []
        for commit in commits:
            candidate = self.analyze_commit_for_decision(commit)
            if candidate:
                candidates.append(candidate)

        # Filter duplicates
        candidates = self.filter_duplicates(candidates)

        # Sort by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        return candidates[:max_candidates]

    def analyze_commit_for_decision(
        self,
        commit_info: CommitInfo,
    ) -> Optional[DecisionCandidate]:
        """
        Analyze commit for decision-making content.

        Args:
            commit_info: CommitInfo object

        Returns:
            DecisionCandidate or None
        """
        message = commit_info.message
        files = commit_info.files

        # Check for decision keywords in message
        has_decision_keyword = any(
            keyword in message.lower() for keyword in self.DECISION_KEYWORDS
        )

        # Check for dependency changes
        has_dependency_change = any(
            dep_file in " ".join(files) for dep_file in self.DEPENDENCY_FILES
        )

        # Check for config changes
        has_config_change = any(
            config_file in " ".join(files) for config_file in self.CONFIG_FILES
        )

        # Check for ADR (Architecture Decision Records)
        has_adr = any(
            "adr" in file.lower() or "decision" in file.lower()
            for file in files
        )

        # Check impact
        patterns = self.pattern_extractor.detect_patterns(commit_info)
        is_high_impact = patterns["impact"] == "high"

        # Score confidence
        confidence = 0.0
        reasoning_parts = []

        if has_decision_keyword:
            confidence += 0.4
            reasoning_parts.append("Contains decision keywords")

        if has_dependency_change:
            confidence += 0.3
            reasoning_parts.append("Changes dependencies")

        if has_config_change:
            confidence += 0.2
            reasoning_parts.append("Modifies configuration")

        if has_adr:
            confidence += 0.5
            reasoning_parts.append("Architecture Decision Record")

        if is_high_impact:
            confidence += 0.1
            reasoning_parts.append("High-impact change")

        # Threshold: need at least 0.5 confidence
        if confidence < 0.5:
            return None

        # Categorize
        category = self.categorize_decision(commit_info, patterns)

        # Generate title
        title = self.generate_title(commit_info, category)

        # Generate content
        content = self.generate_content(commit_info, patterns)

        # Extract tags
        tags = self.extract_tags(commit_info, patterns)

        return DecisionCandidate(
            title=title,
            category=category,
            content=content,
            tags=tags,
            commit_sha=commit_info.sha,
            confidence=min(confidence, 1.0),
            reasoning="; ".join(reasoning_parts),
        )

    def categorize_decision(
        self,
        commit_info: CommitInfo,
        patterns: Dict[str, Any],
    ) -> str:
        """
        Categorize decision.

        Args:
            commit_info: CommitInfo object
            patterns: Detected patterns

        Returns:
            Category string
        """
        message = commit_info.message.lower()

        # Check for constraint keywords
        if any(keyword in message for keyword in self.CONSTRAINT_KEYWORDS):
            return "constraint"

        # Check for convention keywords
        if any(keyword in message for keyword in self.CONVENTION_KEYWORDS):
            return "convention"

        # Check for pattern keywords (before architecture to avoid being masked)
        if "pattern" in message or "approach" in message:
            return "pattern"

        # Check for architecture keywords
        if any(keyword in message for keyword in self.ARCHITECTURE_KEYWORDS):
            return "architecture"

        # Default to decision
        return "decision"

    def generate_title(
        self,
        commit_info: CommitInfo,
        category: str,
    ) -> str:
        """
        Generate title for KB entry.

        Args:
            commit_info: CommitInfo object
            category: Detected category

        Returns:
            Title string
        """
        # Use first line of commit message
        first_line = commit_info.message.split("\n")[0].strip()

        # Clean up conventional commits prefix
        first_line = re.sub(
            r"^(feat|fix|refactor|docs|test|chore|style|perf|ci|build|revert)"
            r"(?:\([^)]+\))?!?:\s*",
            "",
            first_line,
            flags=re.IGNORECASE,
        )

        # Capitalize
        if first_line:
            first_line = first_line[0].upper() + first_line[1:]

        return first_line[:100]  # Limit length

    def generate_content(
        self,
        commit_info: CommitInfo,
        patterns: Dict[str, Any],
    ) -> str:
        """
        Generate content for KB entry.

        Args:
            commit_info: CommitInfo object
            patterns: Detected patterns

        Returns:
            Content string
        """
        parts = []

        # Add commit message
        parts.append(f"**Commit Message:**\n{commit_info.message}\n")

        # Add metadata
        parts.append(
            f"**Commit:** {commit_info.sha[:7]} by {commit_info.author} "
            f"on {commit_info.date.strftime('%Y-%m-%d')}\n"
        )

        # Add affected files
        if commit_info.files:
            parts.append("**Affected Files:**")
            for file in commit_info.files[:10]:  # Limit to 10 files
                parts.append(f"- {file}")
            if len(commit_info.files) > 10:
                parts.append(f"- ... and {len(commit_info.files) - 10} more")
            parts.append("")

        # Add stats
        stats = commit_info.stats
        parts.append(
            f"**Changes:** +{stats['insertions']} -{stats['deletions']} "
            f"({stats['files_changed']} files)"
        )

        return "\n".join(parts)

    def extract_tags(
        self,
        commit_info: CommitInfo,
        patterns: Dict[str, Any],
    ) -> List[str]:
        """
        Extract tags from commit.

        Args:
            commit_info: CommitInfo object
            patterns: Detected patterns

        Returns:
            List of tags
        """
        tags = set()

        # Add category as tag
        tags.add(patterns["category"])

        # Add module as tag
        if patterns["module"] != "unknown":
            tags.add(patterns["module"])

        # Add top keywords
        keywords = patterns["keywords"][:3]
        tags.update(keywords)

        # Add file extensions
        file_types = patterns.get("file_patterns", {}).get("file_types", [])
        for ext in file_types[:2]:
            tags.add(ext)

        return list(tags)[:10]  # Limit to 10 tags

    def filter_duplicates(
        self,
        candidates: List[DecisionCandidate],
    ) -> List[DecisionCandidate]:
        """
        Filter out duplicate decisions.

        Args:
            candidates: List of DecisionCandidate objects

        Returns:
            Filtered list
        """
        # Get existing KB entries
        existing_entries = self.kb.list_all()
        existing_titles = {entry.title.lower() for entry in existing_entries}

        # Filter
        filtered = []
        for candidate in candidates:
            title_lower = candidate.title.lower()
            # Check if similar entry exists
            if not any(
                existing_title in title_lower or title_lower in existing_title
                for existing_title in existing_titles
            ):
                filtered.append(candidate)

        return filtered

    def auto_add_decisions(
        self,
        since_days: int = 30,
        min_confidence: float = 0.7,
    ) -> List[str]:
        """
        Automatically add high-confidence decisions to KB.

        Args:
            since_days: Number of days to analyze
            min_confidence: Minimum confidence threshold

        Returns:
            List of added entry IDs
        """
        candidates = self.extract_decisions(since_days=since_days)

        added_ids = []
        for candidate in candidates:
            if candidate.confidence >= min_confidence:
                # Create KB entry
                from datetime import datetime
                from typing import cast

                from clauxton.core.models import CategoryType, KnowledgeBaseEntry

                # Ensure category is valid
                category: CategoryType = cast(
                    CategoryType,
                    candidate.category if candidate.category in [
                        "architecture", "constraint", "decision", "pattern", "convention"
                    ] else "decision"
                )

                entry = KnowledgeBaseEntry(
                    id=self.kb._generate_id(),  # Private method
                    title=candidate.title,
                    category=category,
                    content=candidate.content,
                    tags=candidate.tags,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    author=None,  # Optional field
                )

                entry_id = self.kb.add(entry)
                added_ids.append(entry_id)

        return added_ids
