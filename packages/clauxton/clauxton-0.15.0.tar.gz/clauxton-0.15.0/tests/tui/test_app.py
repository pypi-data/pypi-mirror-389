"""Tests for TUI application (app.py)."""

from pathlib import Path

from clauxton.tui.app import ClauxtonApp
from clauxton.tui.config import TUIConfig


class TestClauxtonApp:
    """Test suite for ClauxtonApp."""

    def test_app_initialization(self, tmp_path: Path) -> None:
        """Test app initializes correctly."""
        app = ClauxtonApp(project_root=tmp_path)

        assert app.project_root == tmp_path
        assert app.config is not None
        assert isinstance(app.config, TUIConfig)

    def test_app_with_custom_config_path(self, tmp_path: Path) -> None:
        """Test app with custom config path."""
        config_path = tmp_path / "custom_tui.yml"

        # Create custom config
        config = TUIConfig(theme="light")
        config.save(config_path)

        app = ClauxtonApp(project_root=tmp_path, config_path=config_path)

        assert app.config.theme == "light"
        assert app.config_path == config_path

    def test_app_loads_default_config_if_not_exists(self, tmp_path: Path) -> None:
        """Test app loads default config if file doesn't exist."""
        config_path = tmp_path / ".clauxton" / "tui.yml"
        # Don't create the file

        app = ClauxtonApp(project_root=tmp_path, config_path=config_path)

        # Should have default config
        assert app.config.theme == "dark"  # default
        assert app.config.vim_mode is True  # default

    def test_app_title_and_subtitle(self, tmp_path: Path) -> None:
        """Test app has correct title and subtitle."""
        app = ClauxtonApp(project_root=tmp_path)

        assert "Clauxton" in app.TITLE
        assert "0.14.0" in app.TITLE
        assert "AI" in app.SUB_TITLE

    def test_app_keybindings_registered(self, tmp_path: Path) -> None:
        """Test keyboard shortcuts are registered."""
        app = ClauxtonApp(project_root=tmp_path)

        # Extract binding keys
        binding_keys = [b.key for b in app.BINDINGS]

        # Check essential bindings
        assert "ctrl+c,q" in binding_keys  # Quit
        assert "ctrl+p" in binding_keys  # Command palette
        assert "ctrl+k" in binding_keys  # KB focus
        assert "ctrl+l" in binding_keys  # Content focus
        assert "ctrl+j" in binding_keys  # AI focus
        assert "?" in binding_keys  # Help

    def test_theme_toggle(self, tmp_path: Path) -> None:
        """Test theme toggle cycles through themes."""
        config_path = tmp_path / "tui.yml"
        app = ClauxtonApp(project_root=tmp_path, config_path=config_path)

        # Start with dark theme
        assert app._current_theme_name == "dark"

        # Toggle to light
        app.config.toggle_theme()
        assert app.config.theme == "light"

        # Toggle to high-contrast
        app.config.toggle_theme()
        assert app.config.theme == "high-contrast"

        # Toggle back to dark
        app.config.toggle_theme()
        assert app.config.theme == "dark"

    def test_config_persistence(self, tmp_path: Path) -> None:
        """Test config is saved and loaded correctly."""
        config_path = tmp_path / "tui.yml"

        # Create and save config
        app1 = ClauxtonApp(project_root=tmp_path, config_path=config_path)
        app1.config.theme = "light"
        app1.config.enable_ai_suggestions = False
        app1.config.save(config_path)

        # Load in new app instance
        app2 = ClauxtonApp(project_root=tmp_path, config_path=config_path)

        assert app2.config.theme == "light"
        assert app2.config.enable_ai_suggestions is False

    def test_app_with_different_themes(self, tmp_path: Path) -> None:
        """Test app works with different themes."""
        for theme in ["dark", "light", "high-contrast"]:
            config = TUIConfig(theme=theme)  # type: ignore
            config_path = tmp_path / f"{theme}_tui.yml"
            config.save(config_path)

            app = ClauxtonApp(project_root=tmp_path, config_path=config_path)

            assert app._current_theme_name == theme

    def test_app_css_loaded(self, tmp_path: Path) -> None:
        """Test app CSS is loaded."""
        app = ClauxtonApp(project_root=tmp_path)

        # Check CSS contains expected styles
        assert app.CSS is not None
        assert len(app.CSS) > 0
        # Should contain both TUI_STYLES and LAYOUT_STYLES
        assert "Screen" in app.CSS or "panel" in app.CSS


class TestAppActions:
    """Test app action handlers."""

    def test_action_quit_available(self, tmp_path: Path) -> None:
        """Test quit action is available."""
        app = ClauxtonApp(project_root=tmp_path)

        assert hasattr(app, "action_quit")
        assert callable(app.action_quit)

    def test_action_command_palette_available(self, tmp_path: Path) -> None:
        """Test command palette action is available."""
        app = ClauxtonApp(project_root=tmp_path)

        assert hasattr(app, "action_command_palette")
        assert callable(app.action_command_palette)

    def test_action_focus_kb_available(self, tmp_path: Path) -> None:
        """Test KB focus action is available."""
        app = ClauxtonApp(project_root=tmp_path)

        assert hasattr(app, "action_focus_kb")
        assert callable(app.action_focus_kb)

    def test_action_toggle_theme_available(self, tmp_path: Path) -> None:
        """Test theme toggle action is available."""
        app = ClauxtonApp(project_root=tmp_path)

        assert hasattr(app, "action_toggle_theme")
        assert callable(app.action_toggle_theme)

    def test_action_help_available(self, tmp_path: Path) -> None:
        """Test help action is available."""
        app = ClauxtonApp(project_root=tmp_path)

        assert hasattr(app, "action_help")
        assert callable(app.action_help)
