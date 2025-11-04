"""Tests for Keybinding System (keybindings.py)."""


from clauxton.tui.keybindings import Keybinding, KeybindingManager, KeyScope


class TestKeybinding:
    """Test suite for Keybinding dataclass."""

    def test_keybinding_creation(self) -> None:
        """Test creating a keybinding."""
        binding = Keybinding(
            key="ctrl+p",
            action="command_palette",
            description="Open command palette",
            scope=KeyScope.GLOBAL,
            category="Navigation",
        )

        assert binding.key == "ctrl+p"
        assert binding.action == "command_palette"
        assert binding.description == "Open command palette"
        assert binding.scope == KeyScope.GLOBAL
        assert binding.category == "Navigation"

    def test_keybinding_default_scope(self) -> None:
        """Test keybinding with default scope."""
        binding = Keybinding(
            key="a",
            action="test_action",
            description="Test",
        )

        assert binding.scope == KeyScope.GLOBAL
        assert binding.category == "General"


class TestKeybindingManager:
    """Test suite for KeybindingManager."""

    def test_manager_initialization(self) -> None:
        """Test manager initializes with default bindings."""
        manager = KeybindingManager()

        bindings = manager.get_all_bindings()
        assert len(bindings) > 0

    def test_register_keybinding(self) -> None:
        """Test registering a new keybinding."""
        manager = KeybindingManager()
        initial_count = len(manager.get_all_bindings())

        custom_binding = Keybinding(
            key="ctrl+x",
            action="custom_action",
            description="Custom action",
            scope=KeyScope.DASHBOARD,
        )
        manager.register(custom_binding)

        bindings = manager.get_all_bindings()
        assert len(bindings) == initial_count + 1
        assert custom_binding in bindings

    def test_get_bindings_by_scope_global(self) -> None:
        """Test getting global bindings."""
        manager = KeybindingManager()

        global_bindings = manager.get_bindings_by_scope(KeyScope.GLOBAL)
        assert len(global_bindings) > 0
        assert all(b.scope == KeyScope.GLOBAL for b in global_bindings)

    def test_get_bindings_by_scope_dashboard(self) -> None:
        """Test getting dashboard bindings."""
        manager = KeybindingManager()

        dashboard_bindings = manager.get_bindings_by_scope(KeyScope.DASHBOARD)
        assert len(dashboard_bindings) > 0
        assert all(b.scope == KeyScope.DASHBOARD for b in dashboard_bindings)

    def test_get_bindings_by_category(self) -> None:
        """Test getting bindings grouped by category."""
        manager = KeybindingManager()

        categories = manager.get_bindings_by_category()
        assert isinstance(categories, dict)
        assert len(categories) > 0

        # Check specific categories
        assert "Navigation" in categories
        assert "Quick Actions" in categories

    def test_find_binding_by_key_and_scope(self) -> None:
        """Test finding a binding by key and scope."""
        manager = KeybindingManager()

        # Find global binding
        binding = manager.find_binding("ctrl+q", KeyScope.GLOBAL)
        assert binding is not None
        assert binding.action == "quit"

        # Find dashboard binding
        binding = manager.find_binding("ctrl+k", KeyScope.DASHBOARD)
        assert binding is not None
        assert binding.action == "focus_kb"

    def test_find_binding_not_found(self) -> None:
        """Test finding non-existent binding returns None."""
        manager = KeybindingManager()

        binding = manager.find_binding("nonexistent", KeyScope.GLOBAL)
        assert binding is None

    def test_format_key_for_display_ctrl(self) -> None:
        """Test formatting ctrl key combinations."""
        manager = KeybindingManager()

        formatted = manager.format_key_for_display("ctrl+p")
        assert "Ctrl" in formatted
        assert "+" in formatted

    def test_format_key_for_display_special(self) -> None:
        """Test formatting special keys."""
        manager = KeybindingManager()

        assert manager.format_key_for_display("question_mark") == "?"
        assert manager.format_key_for_display("slash") == "/"
        assert "Esc" in manager.format_key_for_display("escape")
        assert "Tab" in manager.format_key_for_display("tab")

    def test_format_key_for_display_single_letter(self) -> None:
        """Test formatting single letter keys."""
        manager = KeybindingManager()

        formatted = manager.format_key_for_display("a")
        assert formatted == "A"

    def test_default_bindings_include_quit(self) -> None:
        """Test default bindings include quit commands."""
        manager = KeybindingManager()

        bindings = manager.get_all_bindings()
        quit_bindings = [b for b in bindings if b.action == "quit"]
        assert len(quit_bindings) >= 2  # ctrl+q and ctrl+c

    def test_default_bindings_include_vim_navigation(self) -> None:
        """Test default bindings include vim-style navigation."""
        manager = KeybindingManager()

        bindings = manager.get_all_bindings()
        vim_keys = ["h", "j", "k", "l"]
        vim_bindings = [b for b in bindings if b.key in vim_keys]
        assert len(vim_bindings) == len(vim_keys)

    def test_default_bindings_include_quick_actions(self) -> None:
        """Test default bindings include quick actions."""
        manager = KeybindingManager()

        quick_action_category = manager.get_bindings_by_category()["Quick Actions"]
        assert len(quick_action_category) >= 6  # a, s, r, n, e, t
