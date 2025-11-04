# MCP Server Overview

**Model Context Protocol (MCP) Server for Clauxton**

[← Back to Index](mcp-index.md)

## Overview

The Clauxton MCP Server provides comprehensive tools for Claude Code through the Model Context Protocol. This allows Claude to:

**Knowledge Base**:
- Search your Knowledge Base for relevant context
- Add new entries during conversations
- List and retrieve existing entries
- Filter by category and tags

**Task Management**:
- Create and manage tasks with dependencies
- Track task status and priority
- Get AI-recommended next task to work on
- Auto-infer dependencies from file overlap
- Update and delete tasks

**Status**: ✅ Available (36 tools across 8 categories)

---

## Installation

### 1. Install Clauxton with MCP Support

```bash
# Install from source
cd clauxton
pip install -e .

# Verify MCP server is available
clauxton-mcp --help
```

### 2. Configure Claude Code

Add the Clauxton MCP Server to your Claude Code configuration:

**Location**: `.claude-plugin/mcp-servers.json` in your project

```json
{
  "mcpServers": {
    "clauxton": {
      "command": "python",
      "args": [
        "-m",
        "clauxton.mcp.server"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### 3. Initialize Your Project

```bash
# In your project directory
clauxton init
```

---

## Available Tools

The MCP Server exposes **36 tools** across 8 categories:
- **6 Knowledge Base tools** (kb_*) - See [Core Tools](mcp-core-tools.md)
- **7 Task Management tools** (task_*) - See [Core Tools](mcp-core-tools.md)
- **3 Conflict Detection tools** - See [Core Tools](mcp-core-tools.md)
- **4 Repository Map tools** - See [Repository Intelligence](mcp-repository-intelligence.md)
- **2 Proactive Monitoring tools** - See [Proactive Monitoring](mcp-proactive-monitoring.md)
- **2 Proactive Suggestion tools** - See [Proactive Suggestions](mcp-suggestions.md)
- **3 Semantic Search tools** - See [Core Tools](mcp-core-tools.md)
- **3 Git Analysis tools** - See [Core Tools](mcp-core-tools.md)
- **4 Context & Intelligence tools** - See [Context Intelligence](mcp-context-intelligence.md)
- **2 Operation tools** (undo_last_operation, get_recent_operations) - See [Core Tools](mcp-core-tools.md)

---

## Technical Details

### Server Implementation

The MCP Server is built using the official `mcp` Python SDK:

```python
from mcp.server.fastmcp import FastMCP
from clauxton.core.knowledge_base import KnowledgeBase

mcp = FastMCP("Clauxton Knowledge Base")

@mcp.tool()
def kb_search(query: str, category: Optional[str] = None, limit: int = 10):
    """Search the Knowledge Base."""
    kb = KnowledgeBase(Path.cwd())
    results = kb.search(query, category=category, limit=limit)
    return [entry.model_dump() for entry in results]
```

**Key Features**:
- **FastMCP**: Simplified MCP server creation with decorators
- **Type Safety**: Full Pydantic validation
- **Error Handling**: Proper error propagation to Claude Code
- **JSON Serialization**: Automatic datetime conversion

---

### Transport

The server uses **stdio transport** for communication with Claude Code:

- **Input**: JSON-RPC requests via stdin
- **Output**: JSON-RPC responses via stdout
- **Protocol**: Model Context Protocol v1.0

---

### Project Context

The MCP Server operates in the **current working directory**:

```python
kb = KnowledgeBase(Path.cwd())
```

This means:
- ✅ Works with `.clauxton/knowledge-base.yml` in your project
- ✅ No configuration needed (uses project's Knowledge Base)
- ✅ Multiple projects = isolated Knowledge Bases

---

## Troubleshooting

### "Server not found"

**Problem**: Claude Code can't find the MCP server.

**Solution**:
1. Check `.claude-plugin/mcp-servers.json` exists
2. Verify `python -m clauxton.mcp.server` works
3. Ensure Clauxton is installed (`pip list | grep clauxton`)

---

### "Knowledge Base not initialized"

**Problem**: MCP tools return errors about missing `.clauxton/`.

**Solution**:
```bash
clauxton init
```

---

### "Module not found: mcp"

**Problem**: MCP SDK not installed.

**Solution**:
```bash
pip install mcp
```

---

### "Permission denied"

**Problem**: Can't write to Knowledge Base.

**Solution**:
Check file permissions:
```bash
ls -la .clauxton/
# Should be: drwx------ (700) for directory
#            -rw------- (600) for knowledge-base.yml
```

---

### MCP Server not connecting

**Problem**: MCP Server not connecting to Claude Code

**Solution**:
- **Check**: `.claude-plugin/mcp-servers.json` configuration
- **Verify**: `clauxton-mcp --help` works
- **Solution**: Restart Claude Code after configuration changes

---

### "Clauxton not initialized" error

**Problem**: Tools return initialization errors

**Solution**:
- Run `clauxton init` in project root
- **Verify**: `.clauxton/` directory exists

---

### Permission errors

**Problem**: Can't read/write to `.clauxton/` directory

**Solution**:
```bash
chmod 700 .clauxton
chmod 600 .clauxton/*.yml
```

---

## Testing

### Unit Tests

Test the MCP server locally:

```bash
pytest tests/mcp/test_server.py -v
```

**Coverage**:
- Server instantiation
- Tool registration
- Tool execution (mocked)
- Error handling

---

### Manual Testing

Test the server manually:

```bash
# Start server (stdio mode)
python -m clauxton.mcp.server

# Server is now waiting for JSON-RPC requests on stdin
```

Send a test request (JSON-RPC format):
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "kb_search",
    "arguments": {
      "query": "API"
    }
  },
  "id": 1
}
```

---

## Next Steps

- **[Core Tools](mcp-core-tools.md)** - Learn about Knowledge Base and Task Management
- **[Repository Intelligence](mcp-repository-intelligence.md)** - Index and search your codebase
- **[Proactive Monitoring](mcp-proactive-monitoring.md)** - Track file changes in real-time
- **[Context Intelligence](mcp-context-intelligence.md)** - Analyze work sessions and predict next actions

---

## References

- [MCP Specification](https://modelcontextprotocol.io/specification)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Clauxton Architecture](architecture.md)
- [Knowledge Base Format](yaml-format.md)

---

[← Back to Index](mcp-index.md) | [Next: Core Tools →](mcp-core-tools.md)
