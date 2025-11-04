# MCP Server Documentation

**Model Context Protocol (MCP) Server for Clauxton**

This is the main index for Clauxton's MCP Server documentation. The MCP Server provides 36 tools across 8 categories to integrate with Claude Code.

## Quick Links

- **[Overview & Setup](mcp-overview.md)** - Installation, configuration, and getting started
- **[Core Tools](mcp-core-tools.md)** - Knowledge Base, Task Management, and Conflict Detection
- **[Repository Intelligence](mcp-repository-intelligence.md)** - Symbol search and code navigation
- **[Proactive Monitoring](mcp-proactive-monitoring.md)** - Real-time file change tracking
- **[Context Intelligence](mcp-context-intelligence.md)** - Work session analysis and predictions (v0.13.0 Week 3)
- **[Proactive Suggestions](mcp-suggestions.md)** - KB updates and anomaly detection (v0.13.0 Week 2)

## Tool Categories

### Core Tools (18 tools)
- **6 Knowledge Base tools** (kb_*) - Store and retrieve project knowledge
- **7 Task Management tools** (task_*) - Create and track tasks with dependencies
- **3 Conflict Detection tools** - Detect and prevent file conflicts
- **2 Operation tools** - Undo operations and view history

### Intelligence Tools (18 tools)
- **4 Repository Map tools** - Index and search code symbols (v0.11.0+)
- **3 Semantic Search tools** - AI-powered search (v0.12.0+)
- **3 Git Analysis tools** - Analyze commits and suggest tasks (v0.12.0+)
- **4 Context Intelligence tools** - Session analysis and predictions (v0.13.0 Week 3)
- **2 Proactive Monitoring tools** - Real-time change tracking (v0.13.0 Week 1)
- **2 Proactive Suggestion tools** - KB suggestions and anomaly detection (v0.13.0 Week 2)

## Version History

- **v0.13.0 Week 3 Day 2** - Context Intelligence tools (analyze_work_session, predict_next_action, get_current_context)
- **v0.13.0 Week 2** - Proactive Suggestion tools (suggest_kb_updates, detect_anomalies)
- **v0.13.0 Week 1** - Proactive Monitoring tools (watch_project_changes, get_recent_changes)
- **v0.12.0** - Semantic Search tools (search_knowledge_semantic, search_tasks_semantic, search_files_semantic)
- **v0.11.0** - Repository Map tools (index_repository, search_symbols)
- **v0.10.0** - Operation tools (undo_last_operation, get_recent_operations)
- **v0.9.0** - Conflict Detection tools
- **v0.8.0** - Core KB and Task Management tools

## Getting Started

1. **Install Clauxton**: `pip install -e .`
2. **Configure MCP Server**: Add to `.claude-plugin/mcp-servers.json`
3. **Initialize Project**: `clauxton init`
4. **Start Using**: Claude Code automatically calls MCP tools transparently

See [Overview & Setup](mcp-overview.md) for detailed instructions.

## Documentation Structure

Each documentation file covers a specific area:

- **mcp-overview.md**: Installation, configuration, technical details, troubleshooting, testing
- **mcp-core-tools.md**: Knowledge Base (6 tools), Task Management (7 tools), Conflict Detection (3 tools)
- **mcp-repository-intelligence.md**: Repository indexing and symbol search (4 tools)
- **mcp-proactive-monitoring.md**: File monitoring and pattern detection (2 tools)
- **mcp-context-intelligence.md**: Session analysis and next action prediction (3 tools)
- **mcp-suggestions.md**: KB update suggestions and anomaly detection (2 tools)

## Support

- **GitHub Issues**: https://github.com/nakishiyaman/clauxton/issues
- **Documentation**: https://github.com/nakishiyaman/clauxton/tree/main/docs
- **PyPI**: https://pypi.org/project/clauxton/

---

**Status**: ✅ v0.13.0 Week 3 Day 2 - 36 MCP tools available
