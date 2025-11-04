"""
Task suggester for Clauxton.

Suggests next tasks based on Git commit history and patterns.
"""

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from clauxton.analysis.git_analyzer import CommitInfo, GitAnalyzer
from clauxton.analysis.pattern_extractor import PatternExtractor
from clauxton.core.task_manager import TaskManager


class TaskSuggestion:
    """Task suggestion with reasoning."""

    def __init__(
        self,
        name: str,
        description: str,
        priority: str,
        reasoning: str,
        related_commits: List[str],
        confidence: float,
    ):
        self.name = name
        self.description = description
        self.priority = priority
        self.reasoning = reasoning
        self.related_commits = related_commits
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "related_commits": self.related_commits,
            "confidence": self.confidence,
        }


class TaskSuggester:
    """
    Task suggester.

    Suggests next tasks based on Git commit patterns.
    """

    def __init__(self, project_root: Path):
        """
        Initialize TaskSuggester.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.git_analyzer = GitAnalyzer(project_root)
        self.pattern_extractor = PatternExtractor()
        self.task_manager = TaskManager(project_root)

    def suggest_tasks(
        self,
        since_days: int = 7,
        max_suggestions: int = 5,
    ) -> List[TaskSuggestion]:
        """
        Suggest tasks based on recent commits.

        Args:
            since_days: Number of days to analyze
            max_suggestions: Maximum number of suggestions

        Returns:
            List of TaskSuggestion objects
        """
        # Get recent commits
        commits = self.git_analyzer.get_recent_commits(since_days=since_days)

        if not commits:
            return []

        # Analyze patterns
        analysis = self.analyze_patterns(commits)

        # Generate suggestions
        suggestions = self.generate_suggestions(analysis, commits)

        # Filter out duplicates
        suggestions = self.filter_duplicates(suggestions)

        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:max_suggestions]

    def analyze_patterns(
        self,
        commits: List[CommitInfo],
    ) -> Dict[str, Any]:
        """
        Analyze patterns from commits.

        Args:
            commits: List of CommitInfo objects

        Returns:
            Analysis results
        """
        categories = []
        modules = []
        keywords = []
        impacts = []

        for commit in commits:
            patterns = self.pattern_extractor.detect_patterns(commit)
            categories.append(patterns["category"])
            modules.append(patterns["module"])
            keywords.extend(patterns["keywords"])
            impacts.append(patterns["impact"])

        # Count occurrences
        category_counts = Counter(categories)
        module_counts = Counter(modules)
        keyword_counts = Counter(keywords)
        impact_counts = Counter(impacts)

        return {
            "category_counts": dict(category_counts),
            "module_counts": dict(module_counts),
            "keyword_counts": dict(keyword_counts),
            "impact_counts": dict(impact_counts),
            "total_commits": len(commits),
        }

    def generate_suggestions(
        self,
        analysis: Dict[str, Any],
        commits: List[CommitInfo],
    ) -> List[TaskSuggestion]:
        """
        Generate task suggestions from analysis.

        Args:
            analysis: Pattern analysis results
            commits: List of CommitInfo objects

        Returns:
            List of TaskSuggestion objects
        """
        suggestions = []

        # Rule 1: Multiple bugfixes → Add tests
        bugfix_count = analysis["category_counts"].get("bugfix", 0)
        if bugfix_count >= 3:
            suggestions.append(
                TaskSuggestion(
                    name="Add comprehensive tests to prevent regressions",
                    description=(
                        f"Recent {bugfix_count} bugfixes suggest missing test coverage. "
                        "Add tests for affected modules."
                    ),
                    priority="high",
                    reasoning=(
                        f"{bugfix_count} bugfixes in the last week indicates potential "
                        "gaps in test coverage."
                    ),
                    related_commits=[
                        c.sha[:7] for c in commits
                        if self.pattern_extractor.categorize_commit(c) == "bugfix"
                    ][:3],
                    confidence=0.8 + min(bugfix_count * 0.05, 0.15),
                )
            )

        # Rule 2: New features → Update documentation
        feature_count = analysis["category_counts"].get("feature", 0)
        if feature_count >= 2:
            modules = [
                module for module, count in analysis["module_counts"].items()
                if count >= 2
            ]
            module_str = ", ".join(modules) if modules else "affected modules"

            suggestions.append(
                TaskSuggestion(
                    name="Update documentation for new features",
                    description=(
                        f"Document new features added in {module_str}. "
                        "Update README, API docs, and examples."
                    ),
                    priority="medium",
                    reasoning=(
                        f"{feature_count} new features added recently. "
                        "Documentation should be updated to reflect changes."
                    ),
                    related_commits=[
                        c.sha[:7] for c in commits
                        if self.pattern_extractor.categorize_commit(c) == "feature"
                    ][:3],
                    confidence=0.75 + min(feature_count * 0.05, 0.15),
                )
            )

        # Rule 3: High-impact changes → Review and test
        high_impact_count = analysis["impact_counts"].get("high", 0)
        if high_impact_count >= 2:
            suggestions.append(
                TaskSuggestion(
                    name="Review and test high-impact changes",
                    description=(
                        f"{high_impact_count} high-impact commits made recently. "
                        "Conduct thorough testing and code review."
                    ),
                    priority="high",
                    reasoning=(
                        "Large changes increase risk of regressions. "
                        "Extra validation recommended."
                    ),
                    related_commits=[
                        c.sha[:7] for c in commits
                        if self.pattern_extractor.estimate_impact(c) == "high"
                    ][:3],
                    confidence=0.85,
                )
            )

        # Rule 4: Refactoring → Verify tests pass
        refactor_count = analysis["category_counts"].get("refactor", 0)
        if refactor_count >= 2:
            suggestions.append(
                TaskSuggestion(
                    name="Verify all tests pass after refactoring",
                    description=(
                        f"{refactor_count} refactoring commits made. "
                        "Run full test suite and check for regressions."
                    ),
                    priority="high",
                    reasoning=(
                        "Refactoring can introduce subtle bugs. "
                        "Comprehensive testing is essential."
                    ),
                    related_commits=[
                        c.sha[:7] for c in commits
                        if self.pattern_extractor.categorize_commit(c) == "refactor"
                    ][:3],
                    confidence=0.80,
                )
            )

        # Rule 5: Test additions → Check coverage
        test_count = analysis["category_counts"].get("test", 0)
        if test_count >= 2:
            suggestions.append(
                TaskSuggestion(
                    name="Review test coverage metrics",
                    description=(
                        f"{test_count} test-related commits made. "
                        "Check coverage reports and identify gaps."
                    ),
                    priority="low",
                    reasoning=(
                        "New tests added. Good time to review overall coverage."
                    ),
                    related_commits=[
                        c.sha[:7] for c in commits
                        if self.pattern_extractor.categorize_commit(c) == "test"
                    ][:3],
                    confidence=0.70,
                )
            )

        # Rule 6: Frequent commits to same module → Review consistency
        most_active_module = max(
            analysis["module_counts"].items(),
            key=lambda x: x[1],
            default=(None, 0),
        )
        if most_active_module[1] >= 5:
            module_name = most_active_module[0]
            suggestions.append(
                TaskSuggestion(
                    name=f"Review {module_name} module for consistency",
                    description=(
                        f"Module '{module_name}' has {most_active_module[1]} commits. "
                        "Review for code quality and consistency."
                    ),
                    priority="medium",
                    reasoning=(
                        "Frequent changes to one module may indicate "
                        "need for refactoring or better design."
                    ),
                    related_commits=[
                        c.sha[:7] for c in commits
                        if self.pattern_extractor.detect_module(c.files) == module_name
                    ][:3],
                    confidence=0.65,
                )
            )

        return suggestions

    def filter_duplicates(
        self,
        suggestions: List[TaskSuggestion],
    ) -> List[TaskSuggestion]:
        """
        Filter out duplicate or similar suggestions.

        Args:
            suggestions: List of TaskSuggestion objects

        Returns:
            Filtered list
        """
        # Get existing tasks
        existing_tasks = self.task_manager.list_all()
        existing_names = {
            task.name.lower() for task in existing_tasks
            if task.status != "completed"
        }

        # Filter out duplicates
        filtered = []
        for suggestion in suggestions:
            # Check if similar task exists
            name_lower = suggestion.name.lower()
            if not any(existing_name in name_lower or name_lower in existing_name
                      for existing_name in existing_names):
                filtered.append(suggestion)

        return filtered

    def get_task_statistics(self, since_days: int = 30) -> Dict[str, Any]:
        """
        Get task-related statistics from commits.

        Args:
            since_days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        commits = self.git_analyzer.get_recent_commits(since_days=since_days)
        analysis = self.analyze_patterns(commits)

        return {
            "total_commits": analysis["total_commits"],
            "commits_per_day": analysis["total_commits"] / max(since_days, 1),
            "category_distribution": analysis["category_counts"],
            "module_distribution": analysis["module_counts"],
            "impact_distribution": analysis["impact_counts"],
            "top_keywords": dict(
                Counter(analysis["keyword_counts"]).most_common(10)
            ),
        }
