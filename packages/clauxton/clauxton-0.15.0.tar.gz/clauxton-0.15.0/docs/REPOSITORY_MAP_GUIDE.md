# Repository Map Usage Guide

> **v0.11.0 Feature** - Automatic codebase indexing and symbol search

## Overview

Repository Map provides automatic codebase understanding through:
- **File structure indexing** (respects `.gitignore`)
- **Symbol extraction** (functions, classes, methods)
- **Fast symbol search** (exact, fuzzy, semantic)

## Quick Start

### 1. Index Your Codebase

```bash
# Index current directory
clauxton repo index

# Index specific project
clauxton repo index --path /path/to/project
```

**What it does:**
- Scans all files recursively
- Respects `.gitignore` patterns
- Extracts symbols from Python, JavaScript, TypeScript, Go, Rust, C++, Java, C#, PHP, Ruby, Swift, and Kotlin files (12 languages)
- Creates index in `.clauxton/map/`

### 2. Search for Symbols

```bash
# Exact search (default) - fast substring matching
clauxton repo search "authenticate"

# Fuzzy search - typo-tolerant
clauxton repo search "user" --type fuzzy

# Semantic search - TF-IDF similarity
clauxton repo search "authentication" --type semantic --limit 10
```

**Search types:**
- **exact**: Case-insensitive substring matching with priority scoring
  - Exact matches ranked highest
  - Starts-with matches next
  - Contains matches next
  - Docstring matches lowest
- **fuzzy**: Levenshtein distance-based similarity (uses Python's `difflib`)
  - Tolerates typos and slight variations
  - Minimum similarity threshold: 0.4
- **semantic**: TF-IDF cosine similarity (requires `scikit-learn`)
  - Searches by meaning, not just text
  - Falls back to exact search if sklearn unavailable

### 3. Check Index Status

```bash
clauxton repo status
```

Shows:
- Index version and last update time
- File counts by type (source/test/config/docs)
- File counts by language
- Total symbol count

## Use Cases

### Find All Authentication Functions

```bash
clauxton repo search "auth" --type exact
```

Output:
```
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Symbol               ┃ Type     ┃ Location              ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ authenticate_user    │ function │ src/api/auth.py:15    │
│ Authenticate user... │          │                       │
│ AuthManager          │ class    │ src/core/auth.py:5    │
│ Handle auth...       │          │                       │
└──────────────────────┴──────────┴───────────────────────┘
```

### Find Similar Functions (Typo-Tolerant)

```bash
# Works even with typos
clauxton repo search "authentcate" --type fuzzy
```

### Find Related Functionality

```bash
# Semantic search finds related concepts
clauxton repo search "user login" --type semantic
```

Finds: `authenticate_user`, `login_handler`, `verify_credentials`, etc.

## How It Works

### Indexing Process

1. **File Discovery**: Recursively scans project directory
2. **Filtering**: Applies `.gitignore` + default patterns (`.git`, `__pycache__`, `.venv`, etc.)
3. **Categorization**: Detects file types and languages
4. **Symbol Extraction**: Uses tree-sitter (or ast fallback) to extract:
   - Function definitions
   - Class definitions
   - Method definitions
   - Docstrings
   - Function signatures
5. **Storage**: Saves to `.clauxton/map/`:
   - `index.json`: File metadata and statistics
   - `symbols.json`: Extracted symbols by file

### Search Process

**Exact Search:**
```
Query: "user"
↓
1. Load all symbols from index
2. Check each symbol name (case-insensitive):
   - Exact match? Score: 100
   - Starts with query? Score: 90
   - Contains query? Score: 50
   - Docstring contains query? Score: 30
3. Sort by score (descending)
4. Return top N results
```

**Fuzzy Search:**
```
Query: "authentcate" (typo)
↓
1. Load all symbols
2. Calculate similarity ratio for each:
   - "authenticate_user" → 0.92 (high similarity)
   - "user_login" → 0.15 (low similarity)
3. Filter by threshold (>0.4)
4. Sort by similarity
5. Return top N results
```

**Semantic Search:**
```
Query: "user authentication"
↓
1. Load symbols + docstrings
2. Create TF-IDF vectors:
   - Document 1: "authenticate_user Authenticate user with password"
   - Document 2: "login_user Log in user by ID"
   - Query: "user authentication"
3. Calculate cosine similarity
4. Rank by relevance
5. Return top N results
```

## Performance

Benchmarks on typical projects:

| Project Size | Files | Symbols | Index Time | Search Time |
|--------------|-------|---------|------------|-------------|
| Small        | 50    | 200     | 0.1s       | <0.01s      |
| Medium       | 500   | 2,000   | 0.7s       | <0.05s      |
| Large        | 1,000 | 5,000   | 1.5s       | <0.1s       |

**Optimizations:**
- Lazy loading: Index loaded only when needed
- In-memory cache: Subsequent searches are instant
- Incremental indexing: Coming in v0.11.1

## Supported Languages

### v0.11.0 (Current)
- **Python** ✅ (functions, classes, methods, docstrings, type hints)
  - tree-sitter for accurate parsing
  - ast module fallback
- **JavaScript** ✅ (ES6+, classes, arrow functions, async/await)
  - tree-sitter-javascript
- **TypeScript** ✅ (interfaces, type aliases, generics, type annotations)
  - tree-sitter-typescript
- **Go** ✅ (functions, methods, structs, interfaces, type aliases, generics)
  - tree-sitter-go
- **Rust** ✅ (functions, methods, structs, enums, traits, type aliases, generics)
  - tree-sitter-rust
- **C++** ✅ (functions, classes, structs, namespaces, templates)
  - tree-sitter-cpp
  - Supports: constructors/destructors, const/static/virtual methods, operator overloading
  - Limitations: Method bodies not extracted separately (captured within class), Doxygen comments not parsed yet
- **Java** ✅ (classes, interfaces, methods, enums, annotations)
  - tree-sitter-java
  - Supports: constructors, generics, static methods, abstract classes, inheritance
  - Limitations: Javadoc comments not parsed yet, package declarations not extracted
- **C#** ✅ (classes, interfaces, methods, properties, enums, delegates, namespaces)
  - tree-sitter-c-sharp
  - Supports: constructors, async methods, static methods, generics, qualified namespaces
  - Limitations: XML documentation comments not parsed yet, using statements not extracted
- **PHP** ✅ (classes, functions, methods, interfaces, traits, namespaces)
  - tree-sitter-php
  - Supports: constructors, static methods, visibility modifiers, magic methods (__construct, etc.), type hints, nullable types, union types (PHP 8+), abstract classes/methods, inheritance, trait usage, promoted constructor properties (PHP 8+), attributes (PHP 8+)
  - PHP 7.4+ features fully supported, PHP 8+ features (enums, match expressions, named arguments) parsed correctly
  - Limitations: PHPDoc comments not parsed yet, anonymous classes may not be extracted
- **Ruby** ✅ (classes, modules, methods, attributes)
  - tree-sitter-ruby
  - Supports: instance methods, singleton methods (self.method_name, class << self), class methods, attr_reader/writer/accessor, inheritance, module mixins (include/extend/prepend), nested classes/modules, private/protected methods, initialize methods, method parameters (default/keyword arguments)
  - Ruby 2.7+ features fully supported
  - Limitations: RDoc/YARD comments not parsed yet, dynamic method definitions (define_method) not extracted
- **Swift** ✅ (classes, structs, enums, protocols, extensions, functions, methods, properties)
  - py-tree-sitter-swift (tree-sitter-swift binding)
  - Supports: initializers (init), static methods, computed properties, generic types, optional types (?), closures, protocol conformance, class inheritance, nested types (outer type extraction), access modifiers (public/private/internal/fileprivate/open), method parameters (external/internal names), inheritance
  - Swift 5.0+ features fully supported
  - Limitations: Documentation comments (///) not fully parsed yet, complex nested types extracted as outer type only

### v0.11.1 (Planned)
- Kotlin

## Integration with Claude Code

Repository Map is designed to work seamlessly with Claude Code:

```python
# MCP tool: index_repository
{
  "name": "index_repository",
  "arguments": {
    "path": "."
  }
}

# MCP tool: search_symbols
{
  "name": "search_symbols",
  "arguments": {
    "query": "authenticate",
    "search_type": "semantic",
    "limit": 10
  }
}
```

## Troubleshooting

### Issue: "No symbols found"

**Cause**: File detected as test file due to filename
**Solution**: Rename file to not start with `test_` or avoid `test.py` as filename

### Issue: Slow indexing on large projects

**Cause**: Too many files being scanned
**Solution**: Add patterns to `.gitignore` to exclude unnecessary directories

### Issue: Semantic search not working

**Cause**: `scikit-learn` not installed
**Solution**:
```bash
pip install scikit-learn
```
Or use `--type exact` or `--type fuzzy` instead

### Issue: Index out of date

**Solution**: Re-run indexing
```bash
clauxton repo index
```

## Best Practices

1. **Index After Major Changes**: Re-index after adding many files or refactoring
2. **Use Exact Search First**: It's fastest and works for most cases
3. **Try Fuzzy for Typos**: If you're unsure of exact spelling
4. **Use Semantic for Discovery**: When exploring unfamiliar codebases
5. **Keep .gitignore Updated**: Helps indexing performance
6. **Check Status Regularly**: Verify index is up to date

## Advanced Usage

### Custom Gitignore Patterns

Repository Map respects your `.gitignore` and adds these defaults:
```
.git
__pycache__
*.pyc
.venv
node_modules
.DS_Store
*.egg-info
.clauxton
htmlcov
.coverage
dist
build
```

### Programmatic Access

```python
from clauxton.intelligence import RepositoryMap
from pathlib import Path

# Initialize
repo_map = RepositoryMap(Path("."))

# Index
result = repo_map.index()
print(f"Indexed {result.files_indexed} files")
print(f"Found {result.symbols_found} symbols")

# Search
symbols = repo_map.search("authenticate", search_type="exact", limit=10)
for symbol in symbols:
    print(f"{symbol.name} ({symbol.type}) at {symbol.file_path}:{symbol.line_start}")
```

## FAQ

**Q: Does it support other languages besides Python?**
A: v0.11.0 supports Python, JavaScript, TypeScript, Go, Rust, and C++. Java/C# coming in v0.11.1.

**Q: Is the index stored in version control?**
A: No. `.clauxton/` is automatically added to `.gitignore`.

**Q: Can I search across multiple projects?**
A: Not yet. Each project has its own independent index.

**Q: How often should I re-index?**
A: After adding many new files or major refactoring. Incremental indexing coming in v0.11.1.

**Q: Does it work with monorepos?**
A: Yes. Index at the monorepo root or individual package roots.

## See Also

- [Repository Map API Documentation](./REPOSITORY_MAP_API.md) (planned)
- [MCP Integration Guide](./mcp-server.md)
- [Main Documentation](../README.md)
