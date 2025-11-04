# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clauxton is a Claude Code plugin providing **persistent project context** through:
- **Knowledge Base**: Store architecture decisions, patterns, constraints, and conventions
- **Task Management**: Auto-inferred task dependencies with DAG validation
- **Conflict Detection**: Pre-merge conflict prediction
- **Repository Map**: Code intelligence with multi-language symbol extraction
- **Semantic Search**: AI-powered search using local embeddings
- **Proactive Intelligence**: Real-time monitoring and suggestions (v0.13.0)

**Current Status**: v0.13.0 (Week 3 Day 2) - Proactive Intelligence in development
**Latest Stable**: v0.12.0 - Semantic Intelligence (1,500+ tests, 87% coverage)

## Build/Test Commands

### Testing
```bash
# Run all tests with coverage
pytest

# Run with HTML coverage report
pytest --cov=clauxton --cov-report=html --cov-report=term

# Run specific test file
pytest tests/core/test_knowledge_base.py

# Run specific test function
pytest tests/core/test_knowledge_base.py::test_add_entry -v

# Run tests by keyword
pytest -k "search" -v
```

### Code Quality
```bash
# Type checking (strict mode enabled)
mypy clauxton

# Linting and formatting
ruff check clauxton tests
ruff check --fix clauxton tests  # Auto-fix issues

# Run all quality checks
mypy clauxton && ruff check clauxton tests && pytest
```

### Building
```bash
# Build package (creates wheel + sdist)
python -m build

# Validate package
twine check dist/*

# Install in editable mode for development
pip install -e .
```

### Running CLI
```bash
# Initialize Clauxton in a project
clauxton init

# Knowledge Base commands
clauxton kb add                    # Interactive add
clauxton kb search "query"         # TF-IDF relevance search
clauxton kb list                   # List all entries
clauxton kb get KB-20251019-001    # Get specific entry
clauxton kb update KB-20251019-001 --title "New title"
clauxton kb delete KB-20251019-001

# Task Management commands
clauxton task add --name "Task name" --priority high
clauxton task list                 # List all tasks
clauxton task get TASK-001         # Get specific task
clauxton task update TASK-001 --status in_progress
clauxton task next                 # Get AI-recommended next task
clauxton task delete TASK-001

# Conflict Detection commands
clauxton conflict detect TASK-001           # Check conflicts for a task
clauxton conflict order TASK-001 TASK-002   # Get safe execution order
clauxton conflict check src/api/users.py    # Check file availability

# Undo commands (v0.10.0+)
clauxton undo                               # Undo last operation (with confirmation)
clauxton undo --history                     # Show operation history

# Daily Workflow commands (v0.11.1+)
clauxton daily                              # Show daily activity summary
clauxton weekly                             # Weekly summary with velocity
clauxton morning                            # Interactive morning planning
clauxton trends                             # Productivity trends (30 days)
clauxton focus TASK-001                     # Set focus on a task
clauxton search "query"                     # Cross-search KB/Tasks/Files
clauxton pause "Meeting"                    # Pause work with reason
clauxton continue                           # Resume work after pause
clauxton resume                             # Show where you left off
```

## High-Level Architecture

### Package Structure
```
clauxton/
├── core/                          # Core business logic
│   ├── models.py                  # Pydantic data models
│   ├── knowledge_base.py          # KB CRUD operations
│   ├── task_manager.py            # Task lifecycle + DAG validation
│   ├── search.py                  # TF-IDF search implementation
│   └── conflict_detector.py       # Conflict detection
├── cli/                           # Click-based CLI interface
│   ├── main.py                    # Main CLI + KB commands
│   ├── tasks.py                   # Task management commands
│   ├── conflicts.py               # Conflict detection commands
│   └── repository.py              # Repository map commands
├── mcp/                           # MCP Server integration
│   └── server.py                  # 32 MCP tools for Claude Code
├── intelligence/                  # Code intelligence (v0.11.0+)
│   ├── symbol_extractor.py        # Multi-language symbol extraction
│   ├── parser.py                  # Tree-sitter parsers
│   └── repository_map.py          # Repository indexing
├── semantic/                      # Semantic intelligence (v0.12.0+)
│   ├── embeddings.py              # Local embedding generation
│   ├── vector_store.py            # FAISS vector store
│   ├── indexer.py                 # Index KB/Tasks/Files
│   └── search.py                  # Semantic search engine
├── analysis/                      # Pattern analysis (v0.12.0+)
│   ├── git_analyzer.py            # Commit analysis
│   ├── pattern_extractor.py       # Pattern recognition
│   └── task_suggester.py          # Task suggestions
├── proactive/                     # Proactive intelligence (v0.13.0+)
│   ├── file_monitor.py            # Real-time file monitoring
│   ├── event_processor.py         # Event processing
│   ├── context_manager.py         # Context awareness
│   └── suggestion_engine.py       # Proactive suggestions
└── utils/                         # Utility modules
    ├── yaml_utils.py              # Safe YAML I/O with atomic writes
    └── file_utils.py              # Secure file operations

Storage: .clauxton/
├── knowledge-base.yml             # All KB entries (YAML)
├── tasks.yml                      # All tasks (YAML)
└── backups/                       # Automatic backups
```

### Key Design Patterns

1. **Pydantic Models**: All data validated with strict typing
2. **YAML Storage**: Human-readable, Git-friendly, atomic writes
3. **DAG Validation**: Tasks form a Directed Acyclic Graph
4. **TF-IDF + Semantic Search**: Dual search modes for accuracy
5. **MCP Integration**: 32 tools exposed to Claude Code
6. **Proactive Monitoring**: Real-time file watching (v0.13.0+)

### API Usage Examples

#### Correct Way to Add KB Entry
```python
from datetime import datetime
from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry

kb = KnowledgeBase(project_root)
now = datetime.now()

# Create KnowledgeBaseEntry object
entry = KnowledgeBaseEntry(
    id=f"KB-{now.strftime('%Y%m%d')}-001",
    title="API Design Pattern",
    category="architecture",
    content="Use RESTful API design",
    tags=["api", "rest"],
    created_at=now,
    updated_at=now,
)

# Add to knowledge base
entry_id = kb.add(entry)
```

#### ⚠️ Common Mistake (Don't Do This)
```python
# ❌ WRONG: Passing keyword arguments directly
kb.add(
    title="API Design",  # TypeError!
    category="architecture",
    content="...",
)

# ✅ CORRECT: Create model objects first (shown above)
```

## Code Style Guidelines

### Python Type Hints (Required)
```python
# All functions must have type hints
def search_kb(query: str, limit: int = 10) -> List[KnowledgeBaseEntry]:
    """Search Knowledge Base by query."""
    pass
```

### Pydantic Models
```python
# Use Pydantic for data validation
from pydantic import BaseModel, Field

class Task(BaseModel):
    id: str = Field(..., pattern=r"^TASK-\d{3}$")
    name: str = Field(..., min_length=1)
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
```

### Error Handling
```python
# Use custom exceptions with clear messages
class ValidationError(Exception):
    """Validation failed."""
    pass

if not entry.title.strip():
    raise ValidationError(
        "Entry title cannot be empty. "
        "Please provide a descriptive title."
    )
```

### Docstrings (Google Style)
```python
def add_entry(entry: KnowledgeBaseEntry) -> str:
    """
    Add entry to Knowledge Base.

    Args:
        entry: KnowledgeBaseEntry to add

    Returns:
        Entry ID (e.g., "KB-20251019-001")

    Raises:
        ValidationError: If entry is invalid
        DuplicateError: If entry ID already exists
    """
    pass
```

## Testing Guidelines

### Test Structure
```
tests/
├── core/           # Unit tests for core modules (96% coverage target)
├── cli/            # CLI command tests (90% coverage target)
├── mcp/            # MCP server tests (95% coverage target)
├── semantic/       # Semantic search tests (90% coverage target)
├── analysis/       # Pattern analysis tests (90% coverage target)
├── proactive/      # Proactive features tests (90% coverage target)
├── utils/          # Utility tests (80% coverage target)
└── integration/    # End-to-end tests
```

### Writing Tests
- Use `tmp_path` fixture for file operations
- Test edge cases: Unicode, special characters, empty inputs
- Test error handling: Invalid inputs, missing files
- Test fallback behaviors: Search without scikit-learn

### Coverage Requirements
- Overall: 90% minimum (current: 87%)
- Core modules: 95%+ required
- New features: Must include comprehensive tests

## Important Patterns

### YAML Safety
```python
# ALWAYS use safe_load (never load)
import yaml
with open(path, "r") as f:
    data = yaml.safe_load(f)  # No code execution risk
```

### Atomic File Writes
```python
# Use temp file + rename for atomic writes
from clauxton.utils.yaml_utils import write_yaml

write_yaml(path, data)  # Automatic backup + atomic write
```

### ID Generation
```python
# KB entries: KB-YYYYMMDD-NNN (e.g., KB-20251019-001)
# Tasks: TASK-NNN (e.g., TASK-001)
```

## Clauxton Integration Philosophy

### Core Principle: "Transparent Yet Controllable"

Clauxton follows Claude Code's philosophy:
- **Do the Simple Thing First**: YAML + Markdown (human-readable, Git-friendly)
- **Composable**: MCP integration (seamless with Claude Code)
- **User Control**: CLI override always available
- **Safety-First**: Read-only by default, explicit writes with undo capability
- **Human-in-the-Loop**: Configurable confirmation levels

### When to Use Clauxton (Transparent Integration)

#### Phase 1: Requirements Gathering
**Trigger**: User mentions constraints, tech stack, or design decisions
**Action**: Automatically add to Knowledge Base via MCP

#### Phase 2: Task Planning
**Trigger**: User requests feature implementation or breaks down work
**Action**: Generate tasks and import via YAML

#### Phase 3: Conflict Detection
**Trigger**: Before starting a task
**Action**: Check conflicts via MCP

#### Phase 4: Implementation
**During Implementation**: Update task status

### Manual Override (User Control)

User can always override with CLI:
```bash
clauxton kb list
clauxton kb add --title "..." --category architecture
clauxton task list
clauxton task update TASK-001 --status completed
```

### Human-in-the-Loop (v0.10.0+)

**Configurable Confirmation Modes**:
- **"always" mode**: Every write operation requires confirmation
- **"auto" mode** (default): Threshold-based confirmation
- **"never" mode**: No confirmation prompts, undo available

```bash
clauxton config set confirmation_mode always   # Strict
clauxton config set confirmation_mode auto     # Balanced (default)
clauxton config set confirmation_mode never    # Fast
```

## MCP Tools Available (32 tools)

### Knowledge Base (6 tools)
- `kb_search()`, `kb_add()`, `kb_list()`, `kb_get()`, `kb_update()`, `kb_delete()`

### Task Management (7 tools)
- `task_add()`, `task_import_yaml()`, `task_list()`, `task_get()`, `task_update()`, `task_next()`, `task_delete()`

### Conflict Detection (3 tools)
- `detect_conflicts()`, `recommend_safe_order()`, `check_file_conflicts()`

### Repository Intelligence (2 tools)
- `index_repository()`, `search_symbols()`

### Semantic Search (3 tools - v0.12.0+)
- `search_knowledge_semantic()`, `search_tasks_semantic()`, `search_files_semantic()`

### Analysis & Suggestions (4 tools - v0.12.0+)
- `analyze_recent_commits()`, `suggest_next_tasks()`, `extract_decisions_from_commits()`, `find_related_entries()`

### Context Intelligence (4 tools - v0.12.0+)
- `get_project_context()`, `generate_project_summary()`, `get_knowledge_graph()`, `kb_export_docs()`

### Proactive Features (4 tools - v0.13.0+)
- `watch_project_changes()`, `get_recent_changes()`, `suggest_kb_updates()`, `detect_anomalies()`

### Utilities (2 tools)
- `undo_last_operation()`, `get_recent_operations()`

For detailed MCP documentation, see:
- **Index**: `docs/mcp-index.md` - Complete documentation index
- **Setup**: `docs/mcp-overview.md` - Installation and configuration
- **Core**: `docs/mcp-core-tools.md` - KB, Tasks, Conflicts (18 tools)
- **Intelligence**: `docs/mcp-repository-intelligence.md` - Code indexing (4 tools)
- **Monitoring**: `docs/mcp-proactive-monitoring.md` - File watching (2 tools)
- **Context**: `docs/mcp-context-intelligence.md` - Session analysis (3 tools)
- **Suggestions**: `docs/mcp-suggestions.md` - KB suggestions and anomalies (2 tools)

## Development Roadmap

**Current Focus**: v0.13.0 - Proactive Intelligence (Week 3 Day 2)

**Completed Phases**:
- ✅ v0.8.0 - Core Engine (TF-IDF, Task Management, MCP)
- ✅ v0.9.0 - Conflict Detection
- ✅ v0.10.0 - Advanced Workflows (Undo, YAML Import, HITL)
- ✅ v0.11.0 - Repository Intelligence
- ✅ v0.11.1 - Daily Workflow Commands
- ✅ v0.11.2 - Test Optimization
- ✅ v0.12.0 - Semantic Intelligence

**Upcoming Phases**:
- 🔥 v0.13.0 - Proactive Intelligence (Current, Target: 2025-12-06)
- 📋 v0.14.0 - Interactive TUI (Target: 2025-12-27)
- 📋 v0.15.0 - Web Dashboard (Target: 2026-01-24)
- 📋 v0.16.0 - Advanced AI Features (Target: 2026-03-01)

For detailed roadmap, see `docs/ROADMAP.md`.

## Common Development Tasks

### Add New CLI Command
1. Add Click command to `clauxton/cli/main.py` or submodule
2. Add corresponding test in `tests/cli/`
3. Update `README.md` usage section
4. Run: `pytest tests/cli/ && mypy clauxton/cli/`

### Add New MCP Tool
1. Add tool function to `clauxton/mcp/server.py` with `@server.call_tool()`
2. Add test in `tests/mcp/test_server.py`
3. Update appropriate MCP documentation (see `docs/mcp-index.md` for structure)
4. Run: `pytest tests/mcp/ && mypy clauxton/mcp/`

### Release Checklist
1. Update version in `clauxton/__version__.py` and `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Run full test suite: `pytest --cov=clauxton`
4. Run quality checks: `mypy clauxton && ruff check clauxton`
5. Build package: `python -m build`
6. Create git tag: `git tag -a v0.X.0 -m "Release v0.X.0"`
7. Push tag: `git push origin v0.X.0`
8. Upload to PyPI: `twine upload dist/*`

## Troubleshooting

### Import Errors
```bash
pip install -e .
```

### Test Failures
```bash
pytest -v
pytest tests/path/to/test.py::test_name -v
pytest --cov=clauxton --cov-report=term-missing
```

### mypy Errors
```bash
rm -rf .mypy_cache
mypy --install-types
mypy clauxton
```

## Links

- **PyPI**: https://pypi.org/project/clauxton/
- **GitHub**: https://github.com/nakishiyaman/clauxton
- **Issues**: https://github.com/nakishiyaman/clauxton/issues
- **Documentation**: See `docs/` directory
- **Roadmap**: See `docs/ROADMAP.md` for detailed development plans
