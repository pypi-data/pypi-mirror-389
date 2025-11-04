# Clauxton MCP Integration Guide - Claude Code

**Version**: v0.11.0
**Updated**: 2025-10-24

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Locate MCP Configuration File](#step-1-locate-mcp-configuration-file)
3. [Step 2: Add MCP Configuration](#step-2-add-mcp-configuration)
4. [Step 3: Restart Claude Code](#step-3-restart-claude-code)
5. [Step 4: Verify Integration](#step-4-verify-integration)
6. [Troubleshooting](#troubleshooting)
7. [Available Tools Reference](#available-tools-reference)

---

## Prerequisites

### Required Environment

- ✅ Claude Code installed
- ✅ Python 3.11+ installed
- ✅ Clauxton v0.11.0 installed

### Verify Clauxton Installation

```bash
# Install from PyPI
pip install clauxton

# Verify version
clauxton --version
# Output: clauxton, version 0.11.0

# Or, if using development version
cd /home/kishiyama-n/workspace/projects/clauxton
source .venv/bin/activate
clauxton --version
```

---

## Step 1: Locate MCP Configuration File

Claude Code's MCP configuration file location varies by platform:

### Linux/WSL

```bash
# Configuration file location
~/.config/claude-code/mcp-servers.json

# Create directory if it doesn't exist
mkdir -p ~/.config/claude-code
```

### macOS

```bash
# Configuration file location
~/Library/Application Support/Claude/mcp-servers.json

# Create directory if it doesn't exist
mkdir -p ~/Library/Application\ Support/Claude
```

### Windows

```powershell
# Configuration file location
%APPDATA%\Claude\mcp-servers.json

# Actual path (example)
C:\Users\YourName\AppData\Roaming\Claude\mcp-servers.json
```

---

## Step 2: Add MCP Configuration

### Method A: Using Development Version (Current Environment)

**Important**: If using the current clauxton development directory

Add the following to `~/.config/claude-code/mcp-servers.json`:

```json
{
  "mcpServers": {
    "clauxton": {
      "command": "/home/kishiyama-n/workspace/projects/clauxton/.venv/bin/python",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "/home/kishiyama-n/workspace/projects/clauxton"
      }
    }
  }
}
```

**Key Points**:
- `command`: Directly specify the virtual environment's Python
- `PYTHONPATH`: Specify the location of the clauxton package
- `cwd`: `${workspaceFolder}` is the root directory of the project Claude Code has open

### Method B: Using System Installation (Future)

If installed from PyPI:

```json
{
  "mcpServers": {
    "clauxton": {
      "command": "python3",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### If You Have Existing MCP Servers

If you're already using other MCP servers, add `clauxton`:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "clauxton": {
      "command": "/home/kishiyama-n/workspace/projects/clauxton/.venv/bin/python",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "/home/kishiyama-n/workspace/projects/clauxton"
      }
    }
  }
}
```

---

## Step 3: Restart Claude Code

### VSCode Claude Code

1. Completely exit VSCode
2. Restart VSCode
3. Claude Code extension will automatically start MCP servers

### CLI Claude Code

```bash
# Completely terminate the process
pkill -9 claude-code

# Restart
claude-code
```

---

## Step 4: Verify Integration

### 4.1 Initialize Clauxton in Your Project

```bash
# Initialize in your test project
cd /path/to/test-project
clauxton init
```

### 4.2 Verify in Claude Code

Open Claude Code and try asking questions like:

#### Verification 1: Knowledge Base Search

```
User: "Search for FastAPI information in clauxton"
```

**Expected Behavior**:
- Claude Code calls the `kb_search` tool
- Results are displayed (empty if no entries yet)

#### Verification 2: Task List

```
User: "List current tasks"
```

**Expected Behavior**:
- Claude Code calls the `task_list` tool
- Task list is displayed

#### Verification 3: Check Available Tools

```
User: "What clauxton tools are available?"
```

**Expected Response**:
```
The following Clauxton tools are available:

Knowledge Base (6 tools):
- kb_search: Search information
- kb_add: Add information
- kb_list: List entries
...

Task Management (6 tools):
- task_add: Add task
- task_list: List tasks
...

Conflict Detection (3 tools):
- detect_conflicts: Detect conflicts
- recommend_safe_order: Optimal order
- check_file_conflicts: Check file conflicts
```

---

## Troubleshooting

### Issue 1: MCP Server Won't Start

**Symptom**: Tools not appearing in Claude Code

**How to Verify**:
```bash
# Manually start MCP server to check for errors
cd /path/to/test-project
source /home/kishiyama-n/workspace/projects/clauxton/.venv/bin/activate
python -m clauxton.mcp.server
```

**Common Causes**:
1. **Incorrect Python path**
   - Verify the `command` path
   - Match it with `which python` output

2. **PYTHONPATH not set**
   - When using development version, `env.PYTHONPATH` is required

3. **Incorrect cwd**
   - Verify that `${workspaceFolder}` is being expanded

**Solution**:
```json
{
  "mcpServers": {
    "clauxton": {
      "command": "/home/kishiyama-n/workspace/projects/clauxton/.venv/bin/python",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "/home/kishiyama-n/workspace/projects/clauxton"
      }
    }
  }
}
```

### Issue 2: Tools Appear But Can't Execute

**Symptom**: Error when calling tools

**How to Verify**:
```bash
# Check if project is initialized
cd /path/to/your-project
ls -la .clauxton/

# If not initialized
clauxton init
```

**Common Causes**:
1. **Clauxton not initialized**
   - Run `clauxton init` in the project

2. **Permission errors**
   - Check `.clauxton/` permissions
   - `chmod 700 .clauxton`

### Issue 3: "Task not found" Error

**Symptom**: Error during task operations

**How to Verify**:
```bash
# Check if task exists
clauxton task list

# Verify task ID format
# Correct: TASK-001, TASK-002, ...
# Incorrect: task-1, Task1, ...
```

### Issue 4: Want to Check MCP Server Logs

**Log Location** (varies by platform):

Linux/WSL:
```bash
~/.local/state/claude-code/logs/
```

macOS:
```bash
~/Library/Logs/Claude/
```

**Check Logs**:
```bash
# View latest logs
tail -f ~/.local/state/claude-code/logs/mcp-server-clauxton.log
```

---

## Available Tools Reference

**Total: 22 MCP Tools** across 7 categories:
- Knowledge Base: 6 tools
- Task Management: 6 tools
- Conflict Detection: 3 tools (v0.9.0-beta)
- Bulk Operations: 2 tools (v0.10.0)
- Undo/History: 2 tools (v0.10.0)
- Logging: 1 tool (v0.10.0)
- Repository Map: 2 tools (v0.11.0)

---

### Knowledge Base Tools (6)

#### `kb_search`
```json
{
  "query": "FastAPI",
  "category": "architecture",  // optional
  "limit": 10                   // optional
}
```
**Description**: Search information using TF-IDF relevance search

#### `kb_add`
```json
{
  "title": "Using FastAPI",
  "category": "architecture",
  "content": "Backend built with FastAPI...",
  "tags": ["backend", "api"]
}
```
**Description**: Add a new entry to Knowledge Base

#### `kb_list`
```json
{
  "category": "architecture"  // optional
}
```
**Description**: List all entries

#### `kb_get`
```json
{
  "entry_id": "KB-20251020-001"
}
```
**Description**: Get a specific entry

#### `kb_update`
```json
{
  "entry_id": "KB-20251020-001",
  "title": "New title",          // optional
  "content": "New content",        // optional
  "category": "decision",          // optional
  "tags": ["updated"]              // optional
}
```
**Description**: Update an entry

#### `kb_delete`
```json
{
  "entry_id": "KB-20251020-001"
}
```
**Description**: Delete an entry

---

### Task Management Tools (6)

#### `task_add`
```json
{
  "name": "Add authentication feature",
  "description": "Implement JWT authentication",  // optional
  "priority": "high",                             // optional: critical, high, medium, low
  "depends_on": ["TASK-001"],                     // optional
  "files": ["src/api/auth.py"],                   // optional
  "kb_refs": ["KB-20251020-001"],                 // optional
  "estimate": 4.0                                  // optional: hours
}
```
**Description**: Add a new task (with automatic dependency inference)

#### `task_list`
```json
{
  "status": "pending",     // optional: pending, in_progress, completed, blocked
  "priority": "high"       // optional: critical, high, medium, low
}
```
**Description**: Get task list (filterable)

#### `task_get`
```json
{
  "task_id": "TASK-001"
}
```
**Description**: Get specific task details

#### `task_update`
```json
{
  "task_id": "TASK-001",
  "status": "in_progress",   // optional
  "priority": "critical",    // optional
  "name": "New name"          // optional
}
```
**Description**: Update a task

#### `task_next`
```json
{}
```
**Description**: Get AI-recommended next task

#### `task_delete`
```json
{
  "task_id": "TASK-001"
}
```
**Description**: Delete a task

---

### Conflict Detection Tools (3) - v0.9.0-beta

#### `detect_conflicts`
```json
{
  "task_id": "TASK-002"
}
```
**Description**: Detect conflicts for a task (with risk level)

**Output Example**:
```json
{
  "task_id": "TASK-002",
  "task_name": "Add authentication feature",
  "files": ["src/api/auth.py", "src/models/user.py"],
  "conflicts": [
    {
      "with_task_id": "TASK-003",
      "with_task_name": "Database connection",
      "risk_level": "HIGH",
      "overlap_percentage": 75.0,
      "conflicting_files": ["src/models/user.py"]
    }
  ]
}
```

#### `recommend_safe_order`
```json
{
  "task_ids": ["TASK-001", "TASK-002", "TASK-003"]
}
```
**Description**: Recommend optimal execution order to minimize conflicts

**Output Example**:
```json
{
  "recommended_order": [
    {
      "position": 1,
      "task_id": "TASK-001",
      "task_name": "FastAPI setup",
      "reason": "No dependencies, no conflicts"
    },
    {
      "position": 2,
      "task_id": "TASK-003",
      "task_name": "Database connection",
      "reason": "Complete before TASK-002 to avoid file conflicts"
    },
    {
      "position": 3,
      "task_id": "TASK-002",
      "task_name": "Authentication",
      "reason": "Depends on TASK-003 completion"
    }
  ]
}
```

#### `check_file_conflicts`
```json
{
  "files": ["src/models/user.py", "src/api/auth.py"]
}
```
**Description**: Check which tasks are editing specific files

**Output Example**:
```json
{
  "files_in_use": [
    {
      "file_path": "src/models/user.py",
      "in_use": true,
      "tasks": [
        {
          "task_id": "TASK-002",
          "task_name": "Add authentication feature",
          "status": "in_progress"
        }
      ]
    },
    {
      "file_path": "src/api/auth.py",
      "in_use": false,
      "tasks": []
    }
  ]
}
```

---

### Bulk Operations Tools (2) - v0.10.0

#### `task_import_yaml`
```json
{
  "yaml_content": "tasks:\n  - name: Setup FastAPI\n    priority: high\n    files_to_edit: [backend/main.py]\n  - name: Add authentication\n    priority: high\n    files_to_edit: [backend/auth.py]",
  "skip_confirmation": false,
  "on_error": "rollback"
}
```
**Description**: Bulk import tasks from YAML (30x faster than individual adds)

**Parameters**:
- `yaml_content`: YAML string with task definitions
- `skip_confirmation`: Skip confirmation prompt (default: false)
- `on_error`: Error handling strategy ("rollback", "skip", "abort")

**Output Example**:
```json
{
  "status": "success",
  "imported_count": 2,
  "failed_count": 0,
  "task_ids": ["TASK-001", "TASK-002"],
  "duration_seconds": 0.15
}
```

#### `kb_export_docs`
```json
{
  "output_dir": "docs/knowledge",
  "category": "architecture"
}
```
**Description**: Export Knowledge Base to Markdown documentation

**Parameters**:
- `output_dir`: Output directory for Markdown files
- `category`: Filter by category (optional, exports all if omitted)

**Output Example**:
```json
{
  "exported_count": 5,
  "output_dir": "docs/knowledge",
  "files": [
    "docs/knowledge/architecture/KB-20251024-001.md",
    "docs/knowledge/architecture/KB-20251024-002.md"
  ]
}
```

---

### Undo/History Tools (2) - v0.10.0

#### `undo_last_operation`
```json
{}
```
**Description**: Reverse the last operation (KB/Task add/update/delete)

**Output Example**:
```json
{
  "undone": true,
  "operation_type": "kb_add",
  "operation_timestamp": "2025-10-24T10:30:00Z",
  "details": "Reversed KB entry addition: KB-20251024-001"
}
```

#### `get_recent_operations`
```json
{
  "limit": 10
}
```
**Description**: Get recent operation history for undo/audit

**Output Example**:
```json
{
  "operations": [
    {
      "timestamp": "2025-10-24T10:30:00Z",
      "operation_type": "kb_add",
      "entry_id": "KB-20251024-001",
      "details": "Added KB entry: FastAPI Setup"
    },
    {
      "timestamp": "2025-10-24T10:25:00Z",
      "operation_type": "task_update",
      "task_id": "TASK-001",
      "details": "Updated task status: pending -> in_progress"
    }
  ]
}
```

---

### Logging Tools (1) - v0.10.0

#### `get_recent_logs`
```json
{
  "limit": 20,
  "level": "ERROR"
}
```
**Description**: Get recent operation logs for debugging

**Parameters**:
- `limit`: Number of logs to retrieve (default: 50)
- `level`: Filter by log level (DEBUG/INFO/WARNING/ERROR)

**Output Example**:
```json
{
  "logs": [
    {
      "timestamp": "2025-10-24T10:30:00Z",
      "level": "ERROR",
      "operation": "task_add",
      "message": "Task validation failed: missing required field 'name'"
    }
  ]
}
```

---

### Repository Map Tools (2) - 🆕 v0.11.0

#### `index_repository`
```json
{
  "root_path": "/path/to/project"
}
```
**Description**: Index codebase with symbol extraction (12 languages)

**Supported Languages**: Python, JavaScript, TypeScript, Go, Rust, C++, Java, C#, PHP, Ruby, Swift, Kotlin

**Output Example**:
```json
{
  "files_indexed": 50,
  "symbols_found": 200,
  "by_language": {
    "python": {"files": 15, "symbols": 50},
    "typescript": {"files": 20, "symbols": 80},
    "javascript": {"files": 15, "symbols": 70}
  },
  "duration_seconds": 0.15,
  "indexed_at": "2025-10-24T10:30:00Z"
}
```

#### `search_symbols`
```json
{
  "query": "authenticate",
  "mode": "exact",
  "limit": 10,
  "root_path": "/path/to/project"
}
```
**Description**: Search symbols with exact/fuzzy/semantic modes

**Parameters**:
- `query`: Search query string
- `mode`: Search mode ("exact", "fuzzy", "semantic")
- `limit`: Max results (default: 10)
- `root_path`: Project root (optional, uses current dir)

**Search Modes**:
- **exact**: Fast substring matching with priority scoring (<0.01s)
- **fuzzy**: Typo-tolerant using Levenshtein distance
- **semantic**: TF-IDF meaning-based search (requires scikit-learn)

**Output Example**:
```json
{
  "count": 3,
  "symbols": [
    {
      "name": "authenticate_user",
      "type": "function",
      "file": "auth.py",
      "line_start": 10,
      "line_end": 20,
      "signature": "def authenticate_user(username: str, password: str) -> bool",
      "docstring": "Authenticate user with username and password"
    },
    {
      "name": "AuthService",
      "type": "class",
      "file": "auth_service.ts",
      "line_start": 15,
      "line_end": 50,
      "signature": "class AuthService"
    }
  ]
}
```

---

## Practical Examples: Using with Claude Code

### Scenario 1: Starting a Project

```
User: "Record the reason for using FastAPI in this project"

Claude Code: Uses kb_add tool
{
  "title": "Adopting FastAPI",
  "category": "architecture",
  "content": "Async processing, automatic OpenAPI generation, high performance",
  "tags": ["backend", "fastapi"]
}

User: "Add 3 tasks: authentication, database, API"

Claude Code: Calls task_add 3 times
TASK-001: Authentication feature
TASK-002: Database connection
TASK-003: API implementation

User: "Are there any conflicts?"

Claude Code: Calls recommend_safe_order
Recommended order: TASK-002 → TASK-001 → TASK-003
```

### Scenario 2: Pre-Task Check

```
User: "What should I do next?"

Claude Code: Calls task_next
Recommendation: TASK-002 (Database connection)

User: "Is TASK-002 safe?"

Claude Code: Calls detect_conflicts("TASK-002")
Result: No conflicts, safe to start

User: "Start it"

Claude Code: task_update("TASK-002", status="in_progress")
Updated successfully
```

### Scenario 3: Pre-File-Edit Check

```
User: "I want to edit user.py"

Claude Code: check_file_conflicts(["src/models/user.py"])
Result: TASK-001 is editing it

User: "Who's using it?"

Claude Code: task_get("TASK-001")
Details displayed: Authentication feature task, in_progress

User: "I'll work on another file"

Claude Code: Understood, recommending other tasks
```

---

## Configuration File Templates

### Full Version (Development Environment)

```json
{
  "mcpServers": {
    "clauxton": {
      "command": "/home/kishiyama-n/workspace/projects/clauxton/.venv/bin/python",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "/home/kishiyama-n/workspace/projects/clauxton",
        "CLAUXTON_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Simple Version (PyPI Version - Future)

```json
{
  "mcpServers": {
    "clauxton": {
      "command": "python3",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

---

## Next Steps

1. ✅ MCP integration complete
2. Run `clauxton init` in your project
3. Add and search information in Claude Code
4. Start task management
5. Utilize Conflict Detection

---

## Support

- **Documentation**: `docs/` directory (420KB+)
- **GitHub Issues**: https://github.com/nakishiyaman/clauxton/issues
- **Quick Start**: `docs/quick-start.md`
- **Troubleshooting**: `docs/troubleshooting.md`

---

**Clauxton v0.9.0-beta MCP Integration** ✅

*Last Updated: 2025-10-20*
*Status: Production Ready*
