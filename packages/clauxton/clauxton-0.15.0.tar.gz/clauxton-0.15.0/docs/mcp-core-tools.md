# MCP Core Tools

**Knowledge Base, Task Management, and Conflict Detection**

[← Back to Index](mcp-index.md) | [Overview](mcp-overview.md)

This document covers the 18 core MCP tools for managing knowledge and tasks.

## Knowledge Base Tools (6 tools)

### 1. kb_search

Search the Knowledge Base for entries matching a query using **TF-IDF relevance ranking**.

**Search Algorithm**: TF-IDF (Term Frequency-Inverse Document Frequency)
- Results are automatically ranked by **relevance score** (0.0-1.0)
- More relevant entries appear first
- Considers keyword frequency and rarity across all entries
- Filters common words ("the", "a", "is") automatically

**Parameters**:
- `query` (string, required): Search query
- `category` (string, optional): Filter by category (architecture, constraint, decision, pattern, convention)
- `limit` (integer, optional): Max results (default: 10)

**Returns**: List of matching entries **ranked by relevance**

**Example**:
```python
kb_search(query="FastAPI", category="architecture", limit=5)
```

**Use Cases**:
- "Find all architecture decisions about APIs"
- "Search for database-related constraints"
- "Show recent decisions about testing"

**Fallback Behavior**: If `scikit-learn` is not installed, automatically falls back to simple keyword matching.

---

### 2. kb_add

Add a new entry to the Knowledge Base.

**Parameters**:
- `title` (string, required): Entry title (max 50 chars)
- `category` (string, required): architecture | constraint | decision | pattern | convention
- `content` (string, required): Detailed description
- `tags` (list[string], optional): Tags for categorization

**Returns**: Entry ID and success message

**Example**:
```python
kb_add(
    title="Use FastAPI framework",
    category="architecture",
    content="All backend APIs use FastAPI for async support and automatic docs.",
    tags=["backend", "api", "fastapi"]
)
```

---

### 3. kb_list

List all Knowledge Base entries.

**Parameters**:
- `category` (string, optional): Filter by category

**Returns**: List of all entries (or filtered by category)

**Example**:
```python
kb_list(category="architecture")
```

---

### 4. kb_get

Get a specific Knowledge Base entry by ID.

**Parameters**:
- `entry_id` (string, required): Entry ID (format: KB-YYYYMMDD-NNN)

**Returns**: Complete entry details including version

**Example**:
```python
kb_get(entry_id="KB-20251019-001")
```

---

### 5. kb_update

Update an existing Knowledge Base entry.

**Parameters**:
- `entry_id` (string, required): Entry ID to update
- `title` (string, optional): New title
- `content` (string, optional): New content
- `category` (string, optional): New category
- `tags` (list[string], optional): New tags

**Returns**: Updated entry with incremented version number

**Example**:
```python
kb_update(
    entry_id="KB-20251019-001",
    title="Updated Title",
    content="Updated content"
)
```

---

### 6. kb_delete

Delete a Knowledge Base entry.

**Parameters**:
- `entry_id` (string, required): Entry ID to delete

**Returns**: Success message

**Example**:
```python
kb_delete(entry_id="KB-20251019-001")
```

**Note**: This is a hard delete (entry is permanently removed).

---

## Usage Examples

### Example 1: Search for Context

**User**: "What's our API architecture?"

**Claude Code**:
1. Uses `kb_search(query="API architecture", category="architecture")`
2. Retrieves entries about API design
3. Provides answer based on Knowledge Base

**Response**: "According to your Knowledge Base (KB-20251019-001), all backend APIs use FastAPI framework..."

---

### Example 2: Add Decision

**User**: "Remember that we decided to use PostgreSQL 15+ for production."

**Claude Code**:
1. Uses `kb_add(title="PostgreSQL for production", category="decision", ...)`
2. Returns entry ID

**Response**: "I've added this decision to your Knowledge Base as entry KB-20251019-002."

---

### Example 3: List Constraints

**User**: "What constraints do we have?"

**Claude Code**:
1. Uses `kb_list(category="constraint")`
2. Formats as a list

**Response**: "You have 3 constraints: KB-20251019-003 (Support IE11), KB-20251019-007 (Max 200ms response), KB-20251019-012 (GDPR compliance)"

---

## Task Management Tools (7 tools)

### task_add

Create a new task with dependencies, files, and KB references.

**Parameters**:
- `name` (string, required): Task name
- `description` (string, optional): Detailed description
- `priority` (string, optional): low | medium | high | critical (default: medium)
- `depends_on` (array, optional): List of task IDs this depends on
- `files` (array, optional): List of files this task will modify
- `kb_refs` (array, optional): Related KB entry IDs
- `estimate` (float, optional): Estimated hours

**Returns**: Task ID and success message

**Example**:
```json
{
  "name": "task_add",
  "arguments": {
    "name": "Add user authentication",
    "description": "Implement JWT-based authentication",
    "priority": "high",
    "depends_on": ["TASK-001"],
    "files": ["src/auth.py", "tests/test_auth.py"],
    "estimate": 4.5
  }
}
```

---

### task_list

List all tasks with optional filters.

**Parameters**:
- `status` (string, optional): pending | in_progress | completed | blocked
- `priority` (string, optional): low | medium | high | critical

**Returns**: List of tasks with details

---

### task_get

Get detailed information about a specific task.

**Parameters**:
- `task_id` (string, required): Task ID (e.g., TASK-001)

**Returns**: Complete task details

---

### task_import_yaml

Import multiple tasks from YAML format.

**Parameters**:
- `yaml_content` (string, required): YAML content with tasks
- `dry_run` (boolean, optional): Validate without creating (default: False)

**Returns**: Import results with task IDs and errors

**Example YAML**:
```yaml
tasks:
  - name: "Implement authentication"
    priority: high
    files:
      - src/auth.py
  - name: "Add tests"
    depends_on:
      - TASK-001
```

---

### task_update

Update task fields (status, priority, name, description).

**Parameters**:
- `task_id` (string, required): Task ID to update
- `status` (string, optional): New status
- `priority` (string, optional): New priority
- `name` (string, optional): New task name

**Note**: Timestamps (`started_at`, `completed_at`) are set automatically when status changes.

---

### task_next

Get AI-recommended next task to work on.

Returns the highest priority task whose dependencies are completed.

**Parameters**: None

**Returns**: Next task details or null if no tasks available

---

### task_delete

Delete a task.

**Parameters**:
- `task_id` (string, required): Task ID to delete

**Returns**: Success message

**Note**: Cannot delete tasks that have dependents. Delete dependent tasks first.

---

## Auto-Dependency Inference

Clauxton automatically infers task dependencies based on file overlap:

1. When multiple tasks edit the same files
2. Earlier tasks (by `created_at`) become dependencies
3. Inferred dependencies merge with manual dependencies
4. No duplicates in the final dependency list

**Example**:
```
TASK-001: Edit src/main.py, src/utils.py
TASK-002: Edit src/main.py
→ TASK-002 automatically depends on TASK-001 (file overlap)
```

This ensures tasks that modify the same files are executed in the correct order, preventing conflicts.

---

## Conflict Detection Tools (3 tools)

### detect_conflicts

Detect potential conflicts for a task.

**Parameters**:
- `task_id` (string, required): Task ID to check

**Returns**: Dictionary with conflict count and details

**Example**:
```python
detect_conflicts("TASK-002")
# Returns conflicts with in_progress tasks
```

---

### recommend_safe_order

Get safe execution order for multiple tasks.

**Parameters**:
- `task_ids` (array, required): List of task IDs

**Returns**: Recommended execution order to avoid conflicts

---

### check_file_conflicts

Check if specific files are being edited by other tasks.

**Parameters**:
- `file_paths` (array, required): List of file paths

**Returns**: List of tasks currently editing these files

---

## Semantic Search Tools (3 tools)

Available in v0.12.0+. See [Semantic Intelligence documentation](../docs/semantic-intelligence.md) for details.

- `search_knowledge_semantic()` - AI-powered KB search
- `search_tasks_semantic()` - AI-powered task search
- `search_files_semantic()` - AI-powered file search

---

## Git Analysis Tools (3 tools)

Available in v0.12.0+. See [Pattern Analysis documentation](../docs/pattern-analysis.md) for details.

- `analyze_recent_commits()` - Analyze commit patterns
- `suggest_next_tasks()` - Suggest tasks based on patterns
- `extract_decisions_from_commits()` - Extract decisions from commits

---

## Operation Tools (2 tools)

### undo_last_operation

Undo the last write operation.

**Parameters**: None

**Returns**: Success message with restored state

**Note**: Only works for write operations (add, update, delete). Read operations cannot be undone.

---

### get_recent_operations

Get list of recent operations.

**Parameters**:
- `limit` (integer, optional): Number of operations (default: 10)

**Returns**: List of recent operations with timestamps

---

## Next Steps

- **[Repository Intelligence](mcp-repository-intelligence.md)** - Index and search your codebase
- **[Proactive Monitoring](mcp-proactive-monitoring.md)** - Track file changes in real-time
- **[Context Intelligence](mcp-context-intelligence.md)** - Analyze work sessions and predict next actions

---

[← Back to Index](mcp-index.md) | [Next: Repository Intelligence →](mcp-repository-intelligence.md)
