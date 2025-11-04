"""
Memory summarization and prediction for Clauxton v0.15.0.

This module provides project summarization and task prediction capabilities
based on the unified Memory system.

Key Features:
- Generate comprehensive project summaries (architecture, tech stack, patterns)
- Predict next tasks based on project state and trends
- Detect knowledge gaps in documentation
- Extract insights from memory patterns

Example:
    >>> from pathlib import Path
    >>> from clauxton.semantic.memory_summarizer import MemorySummarizer
    >>> summarizer = MemorySummarizer(Path("."))
    >>> summary = summarizer.summarize_project()
    >>> predictions = summarizer.predict_next_tasks(limit=5)
    >>> gaps = summarizer.generate_knowledge_gaps()
"""

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from clauxton.core.memory import Memory, MemoryEntry


class MemorySummarizer:
    """
    Generate project summaries and predictions from memories.

    Analyzes the unified Memory system to provide:
    - Project summaries with key decisions and patterns
    - Next task predictions based on activity trends
    - Knowledge gap detection for missing documentation

    Attributes:
        project_root: Project root directory
        memory: Memory instance for accessing memories

    Example:
        >>> summarizer = MemorySummarizer(Path("."))
        >>> summary = summarizer.summarize_project()
        >>> summary.keys()
        dict_keys(['architecture_decisions', 'active_patterns', 'tech_stack',
                   'constraints', 'recent_changes', 'statistics'])
    """

    def __init__(self, project_root: Path) -> None:
        """
        Initialize summarizer.

        Args:
            project_root: Project root directory

        Example:
            >>> summarizer = MemorySummarizer(Path("."))
        """
        self.project_root = project_root
        self.memory = Memory(project_root)

    def summarize_project(self) -> Dict[str, Any]:
        """
        Generate comprehensive project summary.

        Analyzes all memories to extract:
        - Architecture decisions (type=decision)
        - Active patterns (type=pattern)
        - Tech stack (from content keywords)
        - Constraints (from content keywords)
        - Recent changes (last 7 days)
        - Statistics (counts by type/category)

        Returns:
            Dictionary with summary sections:
            {
                "architecture_decisions": [{"id": "...", "title": "...", ...}],
                "active_patterns": [{"id": "...", "title": "...", ...}],
                "tech_stack": ["Python", "PostgreSQL", ...],
                "constraints": ["...", "..."],
                "recent_changes": [{"id": "...", "title": "...", ...}],
                "statistics": {"total": 42, "by_type": {...}, ...}
            }

        Example:
            >>> summary = summarizer.summarize_project()
            >>> summary["statistics"]["total"]
            42
            >>> summary["tech_stack"]
            ['Python', 'PostgreSQL', 'Redis']
        """
        memories = self.memory.list_all()

        summary = {
            "architecture_decisions": self._extract_decisions(memories),
            "active_patterns": self._extract_patterns(memories),
            "tech_stack": self._extract_tech_stack(memories),
            "constraints": self._extract_constraints(memories),
            "recent_changes": self._extract_recent_changes(memories, days=7),
            "statistics": self._calculate_statistics(memories),
        }

        return summary

    def predict_next_tasks(
        self, context: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Predict likely next tasks based on project state.

        Analyzes memories to predict tasks based on:
        1. Incomplete patterns (e.g., auth without tests)
        2. Pending task memories
        3. Recent activity trends

        Args:
            context: Optional context filter (e.g., "frontend", "backend")
            limit: Maximum number of predictions to return

        Returns:
            List of task predictions with reasons and confidence scores:
            [
                {
                    "title": "Implement user login",
                    "reason": "Authentication mentioned in 3 recent decisions",
                    "priority": "high",
                    "confidence": 0.85
                },
                ...
            ]

        Example:
            >>> predictions = summarizer.predict_next_tasks(limit=3)
            >>> len(predictions)
            3
            >>> predictions[0]["title"]
            'Add authentication tests'
            >>> predictions[0]["confidence"]
            0.8
        """
        memories = self.memory.list_all()

        # Filter by context if provided
        if context:
            context_lower = context.lower()
            memories = [
                m
                for m in memories
                if context_lower in m.content.lower()
                or context_lower in m.title.lower()
                or context_lower in m.category.lower()
            ]

        # Analyze patterns and predict tasks
        predictions: List[Dict[str, Any]] = []

        # 1. Look for incomplete patterns
        predictions.extend(self._predict_from_patterns(memories))

        # 2. Look for pending tasks in memories
        predictions.extend(self._predict_from_tasks(memories))

        # 3. Look for recent activity trends
        predictions.extend(self._predict_from_trends(memories))

        # Remove duplicates based on title
        seen_titles = set()
        unique_predictions = []
        for pred in predictions:
            title_lower = pred["title"].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_predictions.append(pred)

        # Sort by confidence and limit
        unique_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return unique_predictions[:limit]

    def generate_knowledge_gaps(self) -> List[Dict[str, str]]:
        """
        Identify missing knowledge or decisions.

        Checks for:
        - Missing expected categories (auth, api, database, testing, deployment)
        - Missing error handling documentation
        - Missing security considerations
        - Missing performance documentation

        Returns:
            List of knowledge gaps with severity:
            [
                {
                    "category": "authentication",
                    "gap": "No documented authentication method",
                    "severity": "high"
                },
                ...
            ]

        Example:
            >>> gaps = summarizer.generate_knowledge_gaps()
            >>> len(gaps)
            3
            >>> gaps[0]["category"]
            'authentication'
            >>> gaps[0]["severity"]
            'high'
        """
        memories = self.memory.list_all()
        gaps: List[Dict[str, str]] = []

        # Check for common categories
        categories = Counter(m.category for m in memories)

        # Expected categories for a typical project
        expected_categories = [
            "authentication",
            "api",
            "database",
            "testing",
            "deployment",
        ]

        for category in expected_categories:
            if categories.get(category, 0) == 0:
                gaps.append(
                    {
                        "category": category,
                        "gap": f"No documented {category} decisions or patterns",
                        "severity": "medium",
                    }
                )

        # Check for specific important topics
        content_checks = [
            (
                "error handling",
                "error-handling",
                "No documented error handling strategy",
                "high",
            ),
            (
                "security",
                "security",
                "No documented security considerations",
                "high",
            ),
            (
                "performance",
                "performance",
                "No documented performance considerations",
                "medium",
            ),
            (
                "backup",
                "backup",
                "No documented backup or disaster recovery strategy",
                "medium",
            ),
        ]

        for keyword, category, message, severity in content_checks:
            if not any(keyword in m.content.lower() for m in memories):
                gaps.append({"category": category, "gap": message, "severity": severity})

        return gaps

    def _extract_decisions(
        self, memories: List[MemoryEntry]
    ) -> List[Dict[str, str]]:
        """
        Extract architecture decisions from memories.

        Args:
            memories: List of all memories

        Returns:
            List of decision summaries (top 10 most recent)

        Example:
            >>> decisions = summarizer._extract_decisions(memories)
            >>> decisions[0]["title"]
            'Switch to PostgreSQL'
        """
        decisions = [m for m in memories if m.type == "decision"]
        # Sort by created_at descending
        decisions.sort(key=lambda m: m.created_at, reverse=True)

        return [
            {
                "id": m.id,
                "title": m.title,
                "content": m.content[:200],  # Truncate to 200 chars
                "date": m.created_at.strftime("%Y-%m-%d"),
            }
            for m in decisions[:10]
        ]

    def _extract_patterns(self, memories: List[MemoryEntry]) -> List[Dict[str, str]]:
        """
        Extract active patterns from memories.

        Args:
            memories: List of all memories

        Returns:
            List of pattern summaries (top 10 most recent)

        Example:
            >>> patterns = summarizer._extract_patterns(memories)
            >>> patterns[0]["category"]
            'api'
        """
        patterns = [m for m in memories if m.type == "pattern"]
        # Sort by created_at descending
        patterns.sort(key=lambda m: m.created_at, reverse=True)

        return [
            {"id": m.id, "title": m.title, "category": m.category}
            for m in patterns[:10]
        ]

    def _extract_tech_stack(self, memories: List[MemoryEntry]) -> List[str]:
        """
        Extract tech stack from memory content.

        Args:
            memories: List of all memories

        Returns:
            Sorted list of detected technologies

        Example:
            >>> tech_stack = summarizer._extract_tech_stack(memories)
            >>> tech_stack
            ['Docker', 'Fastapi', 'PostgreSQL', 'Python', 'Redis']
        """
        tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "postgresql",
            "mysql",
            "redis",
            "mongodb",
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "fastapi",
            "django",
            "flask",
            "express",
            "nextjs",
            "node",
            "go",
            "rust",
            "java",
            "spring",
        ]

        found_tech = set()
        for mem in memories:
            text = f"{mem.title} {mem.content}".lower()
            for tech in tech_keywords:
                if tech in text:
                    # Capitalize properly
                    if tech == "postgresql":
                        found_tech.add("PostgreSQL")
                    elif tech == "mongodb":
                        found_tech.add("MongoDB")
                    elif tech == "mysql":
                        found_tech.add("MySQL")
                    elif tech == "fastapi":
                        found_tech.add("FastAPI")
                    elif tech == "nextjs":
                        found_tech.add("Next.js")
                    elif tech == "nodejs" or tech == "node":
                        found_tech.add("Node.js")
                    elif tech == "aws":
                        found_tech.add("AWS")
                    elif tech == "gcp":
                        found_tech.add("GCP")
                    elif tech == "azure":
                        found_tech.add("Azure")
                    else:
                        found_tech.add(tech.capitalize())

        return sorted(found_tech)

    def _extract_constraints(self, memories: List[MemoryEntry]) -> List[str]:
        """
        Extract project constraints from memories.

        Args:
            memories: List of all memories

        Returns:
            List of constraint descriptions (top 5)

        Example:
            >>> constraints = summarizer._extract_constraints(memories)
            >>> constraints[0]
            'API Design: Must use RESTful principles'
        """
        constraint_keywords = [
            "must",
            "should not",
            "cannot",
            "required",
            "constraint",
            "mandatory",
            "forbidden",
        ]

        constraints = []
        for mem in memories:
            text = f"{mem.title} {mem.content}".lower()
            if any(keyword in text for keyword in constraint_keywords):
                # Truncate content to 150 chars
                truncated_content = (
                    mem.content[:150] + "..." if len(mem.content) > 150 else mem.content
                )
                constraints.append(f"{mem.title}: {truncated_content}")

        return constraints[:5]

    def _extract_recent_changes(
        self, memories: List[MemoryEntry], days: int = 7
    ) -> List[Dict[str, str]]:
        """
        Extract recent changes from memories.

        Args:
            memories: List of all memories
            days: Number of days to look back

        Returns:
            List of recent memory summaries (top 10)

        Example:
            >>> recent = summarizer._extract_recent_changes(memories, days=7)
            >>> recent[0]["type"]
            'decision'
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent = [m for m in memories if m.created_at >= cutoff]

        # Sort by created_at descending
        recent.sort(key=lambda m: m.created_at, reverse=True)

        return [
            {
                "id": m.id,
                "title": m.title,
                "type": m.type,
                "date": m.created_at.strftime("%Y-%m-%d"),
            }
            for m in recent[:10]
        ]

    def _calculate_statistics(
        self, memories: List[MemoryEntry]
    ) -> Dict[str, Any]:
        """
        Calculate memory statistics.

        Args:
            memories: List of all memories

        Returns:
            Dictionary with counts by type, category, and relationships

        Example:
            >>> stats = summarizer._calculate_statistics(memories)
            >>> stats["total"]
            42
            >>> stats["by_type"]["decision"]
            15
        """
        return {
            "total": len(memories),
            "by_type": dict(Counter(m.type for m in memories)),
            "by_category": dict(Counter(m.category for m in memories)),
            "with_relationships": sum(1 for m in memories if m.related_to),
        }

    def _predict_from_patterns(
        self, memories: List[MemoryEntry]
    ) -> List[Dict[str, Any]]:
        """
        Predict tasks from pattern analysis.

        Args:
            memories: List of all memories

        Returns:
            List of task predictions

        Example:
            >>> predictions = summarizer._predict_from_patterns(memories)
            >>> predictions[0]["title"]
            'Add authentication tests'
        """
        predictions: List[Dict[str, Any]] = []

        # Example: If authentication pattern exists but no tests, suggest testing
        auth_patterns = [
            m for m in memories if "auth" in m.content.lower() or "auth" in m.title.lower()
        ]
        if auth_patterns:
            test_exists = any(
                m.type == "task" and "test" in m.title.lower() for m in memories
            )
            if not test_exists:
                predictions.append(
                    {
                        "title": "Add authentication tests",
                        "reason": (
                            f"Authentication patterns found ({len(auth_patterns)} "
                            "memories) but no test tasks"
                        ),
                        "priority": "high",
                        "confidence": 0.8,
                    }
                )

        # Check for API patterns without documentation
        api_patterns = [
            m for m in memories if "api" in m.content.lower() or "api" in m.title.lower()
        ]
        if api_patterns:
            doc_exists = any(
                "documentation" in m.content.lower() or "docs" in m.content.lower()
                for m in memories
            )
            if not doc_exists:
                predictions.append(
                    {
                        "title": "Document API endpoints",
                        "reason": (
                            f"API patterns found ({len(api_patterns)} memories) "
                            "but no documentation"
                        ),
                        "priority": "medium",
                        "confidence": 0.7,
                    }
                )

        # Check for database patterns without migration docs
        db_patterns = [
            m
            for m in memories
            if "database" in m.content.lower() or "db" in m.content.lower()
        ]
        if db_patterns:
            migration_exists = any("migration" in m.content.lower() for m in memories)
            if not migration_exists:
                predictions.append(
                    {
                        "title": "Document database migration strategy",
                        "reason": (
                            f"Database patterns found ({len(db_patterns)} memories) "
                            "but no migration docs"
                        ),
                        "priority": "medium",
                        "confidence": 0.6,
                    }
                )

        return predictions

    def _predict_from_tasks(
        self, memories: List[MemoryEntry]
    ) -> List[Dict[str, Any]]:
        """
        Predict tasks from existing task memories.

        Args:
            memories: List of all memories

        Returns:
            List of task predictions

        Example:
            >>> predictions = summarizer._predict_from_tasks(memories)
            >>> predictions[0]["priority"]
            'medium'
        """
        tasks = [m for m in memories if m.type == "task"]
        predictions: List[Dict[str, Any]] = []

        # Look for pending tasks
        pending = [
            t
            for t in tasks
            if "pending" in t.tags or "todo" in t.tags or "pending" in t.content.lower()
        ]
        for task in pending[:3]:
            predictions.append(
                {
                    "title": task.title,
                    "reason": "Pending task in memory",
                    "priority": "medium",
                    "confidence": 0.9,
                }
            )

        return predictions

    def _predict_from_trends(
        self, memories: List[MemoryEntry]
    ) -> List[Dict[str, Any]]:
        """
        Predict tasks from recent activity trends.

        Args:
            memories: List of all memories

        Returns:
            List of task predictions

        Example:
            >>> predictions = summarizer._predict_from_trends(memories)
            >>> predictions[0]["reason"]
            'Recent focus on api (5 memories)'
        """
        predictions: List[Dict[str, Any]] = []

        # Analyze recent activity (last 20 memories)
        recent = sorted(memories, key=lambda m: m.created_at, reverse=True)[:20]

        if not recent:
            return predictions

        categories = Counter(m.category for m in recent)

        # Most active category suggests related work
        if categories:
            top_category, count = categories.most_common(1)[0]
            predictions.append(
                {
                    "title": f"Continue {top_category} work",
                    "reason": f"Recent focus on {top_category} ({count} memories)",
                    "priority": "medium",
                    "confidence": 0.7,
                }
            )

        return predictions
