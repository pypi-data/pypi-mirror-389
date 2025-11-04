# MCP Server Guide

**⚠️ This document has been split into focused documentation**

For better readability and maintainability, the MCP Server documentation has been reorganized into topic-specific files.

## 📚 Documentation Index

Please visit the [**MCP Documentation Index**](mcp-index.md) for the complete documentation structure.

### Quick Links

- **[MCP Overview & Setup](mcp-overview.md)** - Installation, configuration, and getting started
- **[Core Tools](mcp-core-tools.md)** - Knowledge Base (6), Task Management (7), Conflict Detection (3)
- **[Repository Intelligence](mcp-repository-intelligence.md)** - Symbol search and code navigation (4 tools)
- **[Proactive Monitoring](mcp-proactive-monitoring.md)** - Real-time file change tracking (2 tools)
- **[Context Intelligence](mcp-context-intelligence.md)** - Work session analysis and predictions (3 tools) - v0.13.0 Week 3
- **[Proactive Suggestions](mcp-suggestions.md)** - KB updates and anomaly detection (2 tools) - v0.13.0 Week 2

## Tool Categories

### Core Tools (18 tools)
- **6 Knowledge Base tools** (kb_*) → [Core Tools](mcp-core-tools.md#knowledge-base-tools-6-tools)
- **7 Task Management tools** (task_*) → [Core Tools](mcp-core-tools.md#task-management-tools-7-tools)
- **3 Conflict Detection tools** → [Core Tools](mcp-core-tools.md#conflict-detection-tools-3-tools)
- **2 Operation tools** (undo, history) → [Core Tools](mcp-core-tools.md#operation-tools-2-tools)

### Intelligence Tools (18 tools)
- **4 Repository Map tools** → [Repository Intelligence](mcp-repository-intelligence.md)
- **3 Semantic Search tools** → [Core Tools](mcp-core-tools.md#semantic-search-tools-3-tools)
- **3 Git Analysis tools** → [Core Tools](mcp-core-tools.md#git-analysis-tools-3-tools)
- **4 Context Intelligence tools** → [Context Intelligence](mcp-context-intelligence.md)
- **2 Proactive Monitoring tools** → [Proactive Monitoring](mcp-proactive-monitoring.md)
- **2 Proactive Suggestion tools** → [Proactive Suggestions](mcp-suggestions.md)

## Getting Started

1. **Install**: `pip install -e .`
2. **Configure**: Add to `.claude-plugin/mcp-servers.json`
3. **Initialize**: `clauxton init`
4. **Use**: Claude Code automatically calls MCP tools

See [MCP Overview](mcp-overview.md) for detailed setup instructions.

---

## Why Split Documentation?

The original mcp-server.md was **1363 lines long**, making it difficult to:
- Find specific tools quickly
- Maintain and update individual sections
- Navigate between related topics

The new structure organizes tools by category:
- **mcp-overview.md** (Installation, configuration, troubleshooting)
- **mcp-core-tools.md** (KB, Tasks, Conflicts)
- **mcp-repository-intelligence.md** (Code indexing, symbol search)
- **mcp-proactive-monitoring.md** (File monitoring, pattern detection)
- **mcp-context-intelligence.md** (Session analysis, predictions)
- **mcp-suggestions.md** (KB suggestions, anomaly detection)

Each file includes cross-references and navigation links for easy browsing.

---

**Start here**: [MCP Documentation Index](mcp-index.md)
