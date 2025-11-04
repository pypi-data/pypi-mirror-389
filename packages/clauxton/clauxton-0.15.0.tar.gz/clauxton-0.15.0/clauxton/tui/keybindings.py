"""
Keybinding Management System.

Centralized keybinding management with support for:
- Global and context-specific bindings
- Vim-style navigation
- Customizable shortcuts
- Help text generation
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class KeyScope(str, Enum):
    """Scope of a keybinding."""

    GLOBAL = "global"  # Available everywhere
    DASHBOARD = "dashboard"  # Dashboard screen only
    MODAL = "modal"  # Modal screens
    KB_BROWSER = "kb_browser"  # KB browser widget
    CONTENT = "content"  # Content widget
    AI_PANEL = "ai_panel"  # AI suggestions panel


@dataclass
class Keybinding:
    """
    Keybinding definition.

    Attributes:
        key: Key combination (e.g., "ctrl+p", "a", "escape")
        action: Action name (e.g., "command_palette", "quit")
        description: Human-readable description
        scope: Where this binding applies
        category: Category for help display
    """

    key: str
    action: str
    description: str
    scope: KeyScope = KeyScope.GLOBAL
    category: str = "General"


class KeybindingManager:
    """
    Keybinding manager.

    Manages all keybindings for the TUI application.
    """

    def __init__(self) -> None:
        """Initialize keybinding manager."""
        self._bindings: List[Keybinding] = []
        self._scope_bindings: Dict[KeyScope, List[Keybinding]] = {
            scope: [] for scope in KeyScope
        }
        self._register_default_bindings()

    def _register_default_bindings(self) -> None:
        """Register default keybindings."""
        # Global navigation
        self.register(
            Keybinding(
                key="ctrl+q",
                action="quit",
                description="Quit application",
                scope=KeyScope.GLOBAL,
                category="Navigation",
            )
        )
        self.register(
            Keybinding(
                key="ctrl+c",
                action="quit",
                description="Quit application",
                scope=KeyScope.GLOBAL,
                category="Navigation",
            )
        )
        self.register(
            Keybinding(
                key="ctrl+p",
                action="command_palette",
                description="Open query modal",
                scope=KeyScope.GLOBAL,
                category="Navigation",
            )
        )
        self.register(
            Keybinding(
                key="question_mark",
                action="help",
                description="Show help",
                scope=KeyScope.GLOBAL,
                category="Navigation",
            )
        )
        self.register(
            Keybinding(
                key="escape",
                action="cancel",
                description="Close modal/cancel",
                scope=KeyScope.MODAL,
                category="Navigation",
            )
        )

        # Dashboard focus
        self.register(
            Keybinding(
                key="ctrl+k",
                action="focus_kb",
                description="Focus KB browser",
                scope=KeyScope.DASHBOARD,
                category="Focus",
            )
        )
        self.register(
            Keybinding(
                key="ctrl+l",
                action="focus_content",
                description="Focus main content",
                scope=KeyScope.DASHBOARD,
                category="Focus",
            )
        )
        self.register(
            Keybinding(
                key="ctrl+j",
                action="focus_ai",
                description="Focus AI panel",
                scope=KeyScope.DASHBOARD,
                category="Focus",
            )
        )

        # Vim-style navigation
        self.register(
            Keybinding(
                key="h",
                action="focus_left",
                description="Focus left panel (vim)",
                scope=KeyScope.DASHBOARD,
                category="Vim Navigation",
            )
        )
        self.register(
            Keybinding(
                key="l",
                action="focus_right",
                description="Focus right panel (vim)",
                scope=KeyScope.DASHBOARD,
                category="Vim Navigation",
            )
        )
        self.register(
            Keybinding(
                key="j",
                action="scroll_down",
                description="Scroll down (vim)",
                scope=KeyScope.GLOBAL,
                category="Vim Navigation",
            )
        )
        self.register(
            Keybinding(
                key="k",
                action="scroll_up",
                description="Scroll up (vim)",
                scope=KeyScope.GLOBAL,
                category="Vim Navigation",
            )
        )

        # Quick actions
        self.register(
            Keybinding(
                key="a",
                action="ask_ai",
                description="Ask AI (query modal in AI mode)",
                scope=KeyScope.DASHBOARD,
                category="Quick Actions",
            )
        )
        self.register(
            Keybinding(
                key="s",
                action="show_suggestions",
                description="Show AI suggestions",
                scope=KeyScope.DASHBOARD,
                category="Quick Actions",
            )
        )
        self.register(
            Keybinding(
                key="r",
                action="refresh",
                description="Refresh current view",
                scope=KeyScope.DASHBOARD,
                category="Quick Actions",
            )
        )
        self.register(
            Keybinding(
                key="n",
                action="new_task",
                description="Create new task",
                scope=KeyScope.DASHBOARD,
                category="Quick Actions",
            )
        )
        self.register(
            Keybinding(
                key="e",
                action="new_kb_entry",
                description="Create new KB entry",
                scope=KeyScope.DASHBOARD,
                category="Quick Actions",
            )
        )
        self.register(
            Keybinding(
                key="t",
                action="open_task_list",
                description="Open task list",
                scope=KeyScope.DASHBOARD,
                category="Quick Actions",
            )
        )

        # Search
        self.register(
            Keybinding(
                key="slash",
                action="search_current",
                description="Search in current panel",
                scope=KeyScope.DASHBOARD,
                category="Search",
            )
        )

        # Tab navigation
        self.register(
            Keybinding(
                key="tab",
                action="focus_next",
                description="Focus next widget",
                scope=KeyScope.GLOBAL,
                category="Focus",
            )
        )
        self.register(
            Keybinding(
                key="shift+tab",
                action="focus_previous",
                description="Focus previous widget",
                scope=KeyScope.GLOBAL,
                category="Focus",
            )
        )

    def register(self, binding: Keybinding) -> None:
        """
        Register a keybinding.

        Args:
            binding: Keybinding to register
        """
        self._bindings.append(binding)
        self._scope_bindings[binding.scope].append(binding)

    def get_bindings_by_scope(self, scope: KeyScope) -> List[Keybinding]:
        """
        Get all bindings for a scope.

        Args:
            scope: Scope to filter by

        Returns:
            List of bindings
        """
        return self._scope_bindings[scope].copy()

    def get_all_bindings(self) -> List[Keybinding]:
        """
        Get all registered bindings.

        Returns:
            List of all bindings
        """
        return self._bindings.copy()

    def get_bindings_by_category(self) -> Dict[str, List[Keybinding]]:
        """
        Get bindings grouped by category.

        Returns:
            Dictionary mapping category to bindings
        """
        categories: Dict[str, List[Keybinding]] = {}
        for binding in self._bindings:
            if binding.category not in categories:
                categories[binding.category] = []
            categories[binding.category].append(binding)
        return categories

    def find_binding(self, key: str, scope: KeyScope) -> Optional[Keybinding]:
        """
        Find a binding by key and scope.

        Args:
            key: Key to search for
            scope: Scope to search in

        Returns:
            Binding if found, None otherwise
        """
        # Check scope-specific bindings first
        for binding in self._scope_bindings[scope]:
            if binding.key == key:
                return binding

        # Check global bindings
        for binding in self._scope_bindings[KeyScope.GLOBAL]:
            if binding.key == key:
                return binding

        return None

    def format_key_for_display(self, key: str) -> str:
        """
        Format key for display in help.

        Args:
            key: Key to format

        Returns:
            Formatted key string
        """
        # Convert internal key names to display format
        replacements = {
            "ctrl": "Ctrl",
            "shift": "Shift",
            "alt": "Alt",
            "question_mark": "?",
            "slash": "/",
            "escape": "Esc",
            "tab": "Tab",
        }

        result = key
        for old, new in replacements.items():
            result = result.replace(old, new)

        # Capitalize single letters
        if len(result) == 1:
            result = result.upper()

        return result
