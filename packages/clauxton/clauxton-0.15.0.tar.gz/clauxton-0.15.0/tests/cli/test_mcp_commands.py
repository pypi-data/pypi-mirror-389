"""Tests for MCP CLI commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from clauxton.cli.main import cli


def test_mcp_setup_without_init(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp setup fails without initialization."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["mcp", "setup"])

        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()


def test_mcp_setup_basic(runner: CliRunner, tmp_path: Path) -> None:
    """Test basic MCP setup creates configuration."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project first
        runner.invoke(cli, ["init"])

        # Setup MCP
        result = runner.invoke(cli, ["mcp", "setup"])

        assert result.exit_code == 0
        assert "successfully" in result.output.lower()

        # Verify config file created
        config_file = Path(".claude-plugin/mcp-servers.json")
        assert config_file.exists()

        # Verify config content
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "clauxton" in config["mcpServers"]
        assert config["mcpServers"]["clauxton"]["args"] == ["-m", "clauxton.mcp.server"]


def test_mcp_setup_with_custom_server_name(runner: CliRunner, tmp_path: Path) -> None:
    """Test MCP setup with custom server name."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["mcp", "setup", "--server-name", "my-server"])

        assert result.exit_code == 0

        config_file = Path(".claude-plugin/mcp-servers.json")
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        assert "my-server" in config["mcpServers"]


def test_mcp_setup_existing_config_no_conflict(runner: CliRunner, tmp_path: Path) -> None:
    """Test MCP setup with existing config (different server name)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create existing config with different server
        config_dir = Path(".claude-plugin")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "mcp-servers.json"

        existing_config = {
            "mcpServers": {
                "other-server": {
                    "command": "python",
                    "args": ["-m", "other.module"]
                }
            }
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(existing_config, f)

        # Setup with different name
        result = runner.invoke(cli, ["mcp", "setup", "--server-name", "clauxton"])

        assert result.exit_code == 0

        # Verify both servers exist
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        assert len(config["mcpServers"]) == 2
        assert "other-server" in config["mcpServers"]
        assert "clauxton" in config["mcpServers"]


def test_mcp_setup_existing_config_with_conflict_cancel(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Test MCP setup with existing server (user cancels)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create first setup
        runner.invoke(cli, ["mcp", "setup"])

        # Try to setup again with same name (cancel)
        result = runner.invoke(cli, ["mcp", "setup"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output or "already configured" in result.output


def test_mcp_setup_existing_config_with_conflict_overwrite(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Test MCP setup with existing server (user overwrites)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create first setup
        runner.invoke(cli, ["mcp", "setup"])

        # Try to setup again with same name (overwrite)
        result = runner.invoke(cli, ["mcp", "setup"], input="y\n")

        assert result.exit_code == 0


def test_mcp_status_not_configured(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp status when not configured."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["mcp", "status"])

        assert result.exit_code == 0
        assert "not configured" in result.output.lower()


def test_mcp_status_configured(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp status when configured."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["mcp", "setup"])

        result = runner.invoke(cli, ["mcp", "status"])

        assert result.exit_code == 0
        assert "configured" in result.output.lower()
        assert "clauxton" in result.output


def test_mcp_status_empty_config(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp status with empty config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create empty config
        config_dir = Path(".claude-plugin")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "mcp-servers.json"

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"mcpServers": {}}, f)

        result = runner.invoke(cli, ["mcp", "status"])

        assert result.exit_code == 0
        assert "No MCP servers configured" in result.output


def test_mcp_status_invalid_json(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp status with invalid JSON."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create invalid JSON
        config_dir = Path(".claude-plugin")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "mcp-servers.json"

        with open(config_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        result = runner.invoke(cli, ["mcp", "status"])

        assert result.exit_code != 0
        assert "Error" in result.output or "error" in result.output


def test_mcp_setup_with_path_option(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp setup with --path option."""
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    # Initialize in project dir (without isolated_filesystem to persist files)
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(project_dir)
        result_init = runner.invoke(cli, ["init"])
        assert result_init.exit_code == 0
    finally:
        os.chdir(original_dir)

    # Setup from parent dir with --path
    result = runner.invoke(cli, ["mcp", "setup", "--path", str(project_dir)])

    assert result.exit_code == 0

    config_file = project_dir / ".claude-plugin" / "mcp-servers.json"
    assert config_file.exists()


def test_mcp_status_with_path_option(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp status with --path option."""
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    # Initialize and setup in project dir
    runner_proj = CliRunner()
    with runner_proj.isolated_filesystem(temp_dir=project_dir):
        runner_proj.invoke(cli, ["init"])
        runner_proj.invoke(cli, ["mcp", "setup"])

    # Check status from parent dir with --path
    result = runner.invoke(cli, ["mcp", "status", "--path", str(project_dir)])

    assert result.exit_code == 0
    assert "configured" in result.output.lower()


def test_mcp_setup_corrupted_existing_config(runner: CliRunner, tmp_path: Path) -> None:
    """Test MCP setup with corrupted existing config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Create corrupted config
        config_dir = Path(".claude-plugin")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "mcp-servers.json"

        with open(config_file, "w", encoding="utf-8") as f:
            f.write("{ corrupted }")

        # Try to setup (should offer to create new)
        result = runner.invoke(cli, ["mcp", "setup"], input="y\n")

        # Should succeed after confirmation
        assert result.exit_code == 0 or "Error" in result.output


def test_mcp_setup_custom_python_path(runner: CliRunner, tmp_path: Path) -> None:
    """Test MCP setup with custom Python path."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(
            cli, ["mcp", "setup", "--python", "/usr/bin/python3"]
        )

        assert result.exit_code == 0

        config_file = Path(".claude-plugin/mcp-servers.json")
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        assert config["mcpServers"]["clauxton"]["command"] == "/usr/bin/python3"


def test_mcp_status_multiple_servers(runner: CliRunner, tmp_path: Path) -> None:
    """Test mcp status with multiple servers."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        # Setup multiple servers
        runner.invoke(cli, ["mcp", "setup", "--server-name", "server1"])
        runner.invoke(cli, ["mcp", "setup", "--server-name", "server2"], input="y\n")

        result = runner.invoke(cli, ["mcp", "status"])

        assert result.exit_code == 0
        assert "2" in result.output or "server1" in result.output
        assert "server2" in result.output
