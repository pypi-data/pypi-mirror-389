# MCP Repository Intelligence

**Code Indexing and Symbol Search**

[← Back to Index](mcp-index.md) | [Core Tools](mcp-core-tools.md)

## Repository Map Tools (v0.11.0+)

### 1. index_repository

Index a repository to build a symbol map for fast code navigation and search.

**Parameters**:
- `root_path` (string, optional): Root directory to index (defaults to current working directory)

**Returns**: Dictionary with:
- `status` - "success" or "error"
- `files_indexed` - Number of files processed
- `symbols_found` - Number of symbols extracted
- `duration` - Indexing duration in seconds
- `by_type` - Files breakdown by type (source/test/config/docs/other)
- `by_language` - Files breakdown by language (python/javascript/etc)
- `indexed_at` - Timestamp of indexing

**Example**:
```python
# Index current project
result = index_repository()
# → {"status": "success", "files_indexed": 50, "symbols_found": 200, ...}

# Index specific directory
result = index_repository(root_path="/path/to/project")
```

**Features**:
- Respects `.gitignore` patterns
- Supports Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, and more
- Extracts functions, classes, methods with signatures and docstrings
- Stores index in `.clauxton/map/` directory
- Typical performance: 1000+ files in <2 seconds

**Use Cases**:
1. **Initial Setup**: Index repository when starting work on a project
2. **Refresh Index**: Re-index after major changes
3. **Symbol Discovery**: Find all functions/classes in codebase
4. **Codebase Understanding**: Get overview of project structure

---

### 2. search_symbols

Search for symbols (functions, classes, methods) in the indexed repository.

**Parameters**:
- `query` (string, required): Search query (symbol name or description)
- `mode` (string, optional): Search algorithm - "exact", "fuzzy", or "semantic" (default: "exact")
- `limit` (integer, optional): Maximum results to return (default: 10)
- `root_path` (string, optional): Root directory of indexed repository (defaults to cwd)

**Returns**: Dictionary with:
- `status` - "success" or "error"
- `count` - Number of results found
- `symbols` - List of matching symbols with metadata:
  - `name` - Symbol name
  - `type` - "function", "class", or "method"
  - `file_path` - Full path to source file
  - `line_start` - Starting line number
  - `line_end` - Ending line number
  - `docstring` - Symbol documentation (if available)
  - `signature` - Function/method signature

**Search Modes**:

**exact** (default): Fast substring matching with priority scoring
- Exact match: highest priority
- Starts with: high priority
- Contains: medium priority
- Docstring: low priority
- Example: "auth" finds "authenticate_user", "get_auth_token"

**fuzzy**: Typo-tolerant using Levenshtein distance
- Handles typos and misspellings
- Similarity threshold: 0.4
- Example: "authentcate" finds "authenticate_user"

**semantic**: Meaning-based search using TF-IDF
- Searches by concept, not just text
- Requires scikit-learn (falls back to exact if unavailable)
- Example: "user login" finds "authenticate_user", "verify_credentials"

**Examples**:
```python
# Exact search (default)
result = search_symbols(query="authenticate")
# → {"status": "success", "count": 2, "symbols": [...]}

# Fuzzy search (typo-tolerant)
result = search_symbols(query="authentcate", mode="fuzzy")
# → Finds "authenticate_user" despite typo

# Semantic search (by meaning)
result = search_symbols(query="user login", mode="semantic")
# → Finds "authenticate_user", "verify_credentials", etc.
```

**Use Cases**:
1. **Find Function**: Locate specific function by name
2. **Explore API**: Discover related functions (semantic search)
3. **Code Navigation**: Jump to symbol definition
4. **Refactoring**: Find all usages of a symbol
5. **Documentation**: Find functions by description

**Note**: Repository must be indexed first using `index_repository`.

---

## Integration Workflow

Here's a typical workflow for using Repository Map with Claude Code:

### 1. Initial Setup
```python
# Claude Code automatically calls this when starting work
result = index_repository()
# → Indexes entire project in ~1-2 seconds
```

### 2. Exploration Phase
```python
# Find authentication-related code
symbols = search_symbols(query="authenticate", mode="exact")
# → Returns all functions/classes with "authenticate" in name

# Discover related functionality
symbols = search_symbols(query="user login", mode="semantic")
# → Returns authenticate_user, verify_credentials, check_session, etc.
```

### 3. Implementation Phase
```python
# Find specific function to modify
symbols = search_symbols(query="validate_password", mode="exact", limit=1)
# → Jump to line 45 in auth/validators.py

# After making changes, re-index if needed
result = index_repository()
# → Updates symbol map with new/modified functions
```

### Performance Notes
- **Indexing**: 1000+ files in <2 seconds
- **Search**: <0.01s for exact, <0.1s for semantic
- **Memory**: ~1MB per 1000 symbols
- **Storage**: JSON files in `.clauxton/map/` (~10-50KB per project)

### Transparent Usage in Claude Code
Claude Code automatically:
1. **Indexes on project open** (if not indexed recently)
2. **Searches when needed** (user mentions "find", "search", "where is")
3. **Re-indexes after major changes** (new files, bulk edits)

You don't need to manually call these tools - Claude Code handles it transparently.

---


---

[← Back to Index](mcp-index.md) | [Next: Proactive Monitoring →](mcp-proactive-monitoring.md)
