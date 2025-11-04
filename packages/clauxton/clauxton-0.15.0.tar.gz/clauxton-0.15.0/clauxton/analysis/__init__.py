"""
Analysis module for Clauxton.

This module provides Git commit analysis, pattern extraction, and task suggestions.
"""

from clauxton.analysis.decision_extractor import DecisionExtractor
from clauxton.analysis.git_analyzer import GitAnalyzer
from clauxton.analysis.pattern_extractor import PatternExtractor
from clauxton.analysis.task_suggester import TaskSuggester

__all__ = [
    "GitAnalyzer",
    "PatternExtractor",
    "TaskSuggester",
    "DecisionExtractor",
]
