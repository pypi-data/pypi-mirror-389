"""
Clauxton TUI Module.

Interactive Terminal User Interface for Clauxton with AI integration.
Provides a modern, keyboard-driven interface for knowledge base management,
task tracking, and AI-powered suggestions.

Usage:
    clauxton tui

Features:
    - AI-enhanced dashboard with real-time suggestions
    - Semantic search interface
    - Code review workflow
    - KB generation from commits
    - Interactive chat with AI
"""

from clauxton.tui.app import ClauxtonApp
from clauxton.tui.config import TUIConfig

__all__ = [
    "ClauxtonApp",
    "TUIConfig",
]
