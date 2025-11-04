"""CLI commands for MCP server configuration."""

import json
import platform
import sys
from pathlib import Path

import click


@click.group(name="mcp")
def mcp_group() -> None:
    """MCP server configuration commands."""
    pass


@mcp_group.command(name="setup")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    help="Path to project root (default: current directory)",
)
@click.option(
    "--server-name",
    default="clauxton",
    help="Name for the MCP server (default: clauxton)",
)
@click.option(
    "--python",
    default=sys.executable,
    help="Path to Python executable (default: current Python)",
)
def setup_command(path: str, server_name: str, python: str) -> None:
    """
    Auto-configure MCP server for Claude Code.

    This command automatically:
    - Detects your platform and Python environment
    - Generates the correct MCP configuration
    - Creates .claude-plugin/mcp-servers.json

    Example:
        clauxton mcp setup
        clauxton mcp setup --server-name my-project
        clauxton mcp setup --python /path/to/python
    """
    project_path = Path(path)

    # Check if Clauxton is initialized
    if not (project_path / ".clauxton").exists():
        click.echo(
            click.style(
                "⚠ Clauxton not initialized. Run 'clauxton init' first",
                fg="red",
            )
        )
        raise click.Abort()

    click.echo(click.style(f"\nConfiguring MCP Server for: {project_path}\n", bold=True))

    # Detect platform
    system = platform.system()
    click.echo(f"Platform: {system}")
    click.echo(f"Python: {python}")
    click.echo(f"Server name: {server_name}\n")

    # Generate MCP configuration
    config_dir = project_path / ".claude-plugin"
    config_file = config_dir / "mcp-servers.json"

    # Create configuration
    mcp_config = {
        "mcpServers": {
            server_name: {
                "command": python,
                "args": ["-m", "clauxton.mcp.server"],
                "cwd": "${workspaceFolder}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            }
        }
    }

    # Check if config already exists
    if config_file.exists():
        click.echo(click.style("⚠ MCP configuration already exists", fg="yellow"))

        # Load existing config
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                existing_config = json.load(f)

            # Check if server name conflicts
            if server_name in existing_config.get("mcpServers", {}):
                click.echo(f"\nServer '{server_name}' already configured:")
                click.echo(json.dumps(existing_config["mcpServers"][server_name], indent=2))

                if not click.confirm("\nOverwrite existing configuration?", default=False):
                    click.echo("Cancelled")
                    return

            # Merge with existing config
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            existing_config["mcpServers"][server_name] = mcp_config["mcpServers"][server_name]
            mcp_config = existing_config

        except Exception as e:
            click.echo(click.style(f"⚠ Error reading existing config: {e}", fg="yellow"))
            if not click.confirm("Create new configuration?", default=True):
                click.echo("Cancelled")
                return

    # Create directory
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write configuration
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2)
            f.write("\n")  # Add trailing newline

        click.echo(click.style("\n✓ MCP configuration created successfully!", fg="green"))
        click.echo(f"  Location: {config_file}")
        click.echo("\nConfiguration:\n")
        click.echo(json.dumps(mcp_config, indent=2))

        # Next steps
        click.echo(click.style("\n📋 Next Steps:", bold=True))
        click.echo("1. Restart Claude Code to load the MCP server")
        click.echo("2. Verify connection: Claude Code should show MCP tools available")
        click.echo("3. Test with: Ask Claude to search your knowledge base")

    except Exception as e:
        click.echo(click.style(f"\n⚠ Error writing configuration: {e}", fg="red"))
        raise click.Abort()


@mcp_group.command(name="status")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    help="Path to project root (default: current directory)",
)
def status_command(path: str) -> None:
    """
    Show MCP server configuration status.

    Example:
        clauxton mcp status
    """
    project_path = Path(path)
    config_file = project_path / ".claude-plugin" / "mcp-servers.json"

    click.echo(click.style("\nMCP Server Status\n", bold=True))

    if not config_file.exists():
        click.echo(click.style("✗ MCP server not configured", fg="red"))
        click.echo("\nTo configure:")
        click.echo(click.style("  clauxton mcp setup", fg="cyan"))
        return

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})

        if not servers:
            click.echo(click.style("✗ No MCP servers configured", fg="yellow"))
            return

        click.echo(click.style(f"✓ {len(servers)} MCP server(s) configured:", fg="green"))
        click.echo()

        for name, server_config in servers.items():
            click.echo(click.style(f"  {name}:", fg="cyan", bold=True))
            click.echo(f"    Command: {server_config.get('command', 'N/A')}")

            args = server_config.get('args', [])
            if args:
                click.echo(f"    Args: {' '.join(args)}")

            cwd = server_config.get('cwd', 'N/A')
            click.echo(f"    Working directory: {cwd}")

            env = server_config.get('env', {})
            if env:
                click.echo("    Environment:")
                for key, value in env.items():
                    click.echo(f"      {key}={value}")
            click.echo()

        click.echo(f"Configuration file: {config_file}")

    except Exception as e:
        click.echo(click.style(f"⚠ Error reading configuration: {e}", fg="red"))
        raise click.Abort()
