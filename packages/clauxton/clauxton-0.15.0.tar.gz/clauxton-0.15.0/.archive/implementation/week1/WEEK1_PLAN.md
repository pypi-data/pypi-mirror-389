# Week 1 Implementation Plan: Repository Map Core

**Version**: v0.11.0
**Week**: 1 of 6
**Duration**: 5-7 days
**Estimated Effort**: 27 hours
**Status**: 📋 Ready to Start

---

## 🎯 Week 1 Goals

### Primary Objective
Implement core Repository Map functionality with Python symbol extraction.

### Success Criteria
- ✅ File structure indexing works (respects .gitignore)
- ✅ Python symbol extraction functional (tree-sitter)
- ✅ Basic search by symbol name
- ✅ JSON storage working (index.json, symbols.json)
- ✅ 40+ tests passing (90% coverage)
- ✅ Graceful fallback to ast module
- ✅ Basic CLI commands (`clauxton map index`, `clauxton map search`)

---

## 📋 Task List (8 Tasks, 27 Hours)

### Task 1: Project Setup (30 minutes)
**Priority**: HIGH
**Blocking**: All other tasks

**Subtasks**:
1. Create feature branch
   ```bash
   git checkout -b feature/v0.11.0-repository-map
   git push -u origin feature/v0.11.0-repository-map
   ```

2. Create directory structure
   ```bash
   mkdir -p clauxton/intelligence
   touch clauxton/intelligence/__init__.py
   touch clauxton/intelligence/repository_map.py
   touch clauxton/intelligence/symbol_extractor.py
   touch clauxton/intelligence/dependency_graph.py

   mkdir -p tests/intelligence
   touch tests/intelligence/__init__.py
   touch tests/intelligence/test_repository_map.py
   touch tests/intelligence/test_symbol_extractor.py
   ```

3. Update dependencies in pyproject.toml
   ```toml
   dependencies = [
       # ... existing ...
       "tree-sitter>=0.25.0",
       "tree-sitter-python>=0.25.0",
   ]
   ```

**Deliverable**: Clean directory structure, dependencies updated

---

### Task 2: Implement RepositoryMap Skeleton (3 hours)
**Priority**: HIGH
**Depends on**: Task 1

**File**: `clauxton/intelligence/repository_map.py`

**Implementation**:
```python
"""
Repository Map for automatic codebase indexing.

This module provides:
- File structure indexing
- Symbol extraction (functions, classes)
- Dependency graph building
- Semantic search
"""

from pathlib import Path
from typing import List, Dict, Optional, Literal
from datetime import datetime
import json
from clauxton.core.models import ClauxtonError

class RepositoryMapError(ClauxtonError):
    """Base error for repository map operations."""
    pass

class IndexResult:
    """Result of indexing operation."""
    def __init__(
        self,
        files_indexed: int,
        symbols_found: int,
        duration_seconds: float,
        errors: List[str] = None
    ):
        self.files_indexed = files_indexed
        self.symbols_found = symbols_found
        self.duration_seconds = duration_seconds
        self.errors = errors or []

class FileNode:
    """Represents a file in the repository."""
    def __init__(
        self,
        path: Path,
        relative_path: str,
        file_type: str,
        language: Optional[str],
        size_bytes: int,
        line_count: int,
        last_modified: datetime,
    ):
        self.path = path
        self.relative_path = relative_path
        self.file_type = file_type
        self.language = language
        self.size_bytes = size_bytes
        self.line_count = line_count
        self.last_modified = last_modified

class Symbol:
    """Represents a code symbol (function, class, etc.)."""
    def __init__(
        self,
        name: str,
        type: str,
        file_path: str,
        line_start: int,
        line_end: int,
        docstring: Optional[str] = None,
        signature: Optional[str] = None,
    ):
        self.name = name
        self.type = type
        self.file_path = file_path
        self.line_start = line_start
        self.line_end = line_end
        self.docstring = docstring
        self.signature = signature

class RepositoryMap:
    """
    Indexes and queries codebase structure.

    Usage:
        repo_map = RepositoryMap(Path("."))
        repo_map.index()
        results = repo_map.search("authentication")
    """

    def __init__(self, root_dir: Path | str):
        """Initialize repository map at root_dir."""
        self.root_dir = Path(root_dir) if isinstance(root_dir, str) else root_dir
        self.map_dir = self.root_dir / ".clauxton" / "map"
        self.map_dir.mkdir(parents=True, exist_ok=True)

        # Lazy-loaded data
        self._index: Optional[Dict] = None
        self._symbols: Optional[Dict] = None

    def index(
        self,
        incremental: bool = False,
        progress_callback: Optional[callable] = None
    ) -> IndexResult:
        """
        Index the codebase.

        Args:
            incremental: Only index changed files
            progress_callback: (current, total, status) -> None

        Returns:
            IndexResult with statistics
        """
        # Implementation in Task 3
        raise NotImplementedError("To be implemented in Task 3")

    def search(
        self,
        query: str,
        search_type: Literal["semantic", "exact", "fuzzy"] = "semantic",
        limit: int = 20
    ) -> List[Symbol]:
        """
        Search codebase for symbols.

        Args:
            query: Search query
            search_type: Search algorithm
            limit: Max results

        Returns:
            List of matching symbols
        """
        # Implementation in Task 5
        raise NotImplementedError("To be implemented in Task 5")

    @property
    def index_data(self) -> Dict:
        """Lazy load index data."""
        if self._index is None:
            index_file = self.map_dir / "index.json"
            if index_file.exists():
                with open(index_file) as f:
                    self._index = json.load(f)
            else:
                self._index = {"files": [], "statistics": {}}
        return self._index

    @property
    def symbols_data(self) -> Dict:
        """Lazy load symbols data."""
        if self._symbols is None:
            symbols_file = self.map_dir / "symbols.json"
            if symbols_file.exists():
                with open(symbols_file) as f:
                    self._symbols = json.load(f)
            else:
                self._symbols = {}
        return self._symbols
```

**Tests** (`tests/intelligence/test_repository_map.py`):
```python
import pytest
from pathlib import Path
from clauxton.intelligence.repository_map import RepositoryMap

def test_repository_map_init(tmp_path):
    """Test RepositoryMap initialization."""
    repo_map = RepositoryMap(tmp_path)
    assert repo_map.root_dir == tmp_path
    assert repo_map.map_dir == tmp_path / ".clauxton" / "map"
    assert repo_map.map_dir.exists()

def test_repository_map_accepts_string_path(tmp_path):
    """Test that RepositoryMap accepts string paths."""
    repo_map = RepositoryMap(str(tmp_path))
    assert repo_map.root_dir == tmp_path

def test_repository_map_lazy_loading(tmp_path):
    """Test lazy loading of index and symbols."""
    repo_map = RepositoryMap(tmp_path)
    assert repo_map._index is None
    assert repo_map._symbols is None

    # Access triggers loading
    index = repo_map.index_data
    assert index == {"files": [], "statistics": {}}
    assert repo_map._index is not None
```

**Deliverable**: RepositoryMap class with skeleton, 5+ tests passing

---

### Task 3: Implement File Indexing (4 hours)
**Priority**: HIGH
**Depends on**: Task 2

**Implementation**: Add to `RepositoryMap.index()`

**Features**:
- Recursive directory traversal
- Respect .gitignore patterns
- Detect file types (source, test, config, docs)
- Detect programming language
- Count lines and file size
- Track last modified time
- Generate index.json

**Pseudocode**:
```python
def index(self, incremental: bool = False, progress_callback = None) -> IndexResult:
    import time
    from pathlib import Path

    start = time.time()
    files_indexed = 0
    symbols_found = 0
    errors = []

    # Load .gitignore patterns
    gitignore_patterns = self._load_gitignore()

    # Scan files
    all_files = []
    for file_path in self.root_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # Check gitignore
        if self._should_ignore(file_path, gitignore_patterns):
            continue

        # Categorize file
        file_info = self._categorize_file(file_path)
        all_files.append(file_info)
        files_indexed += 1

        # Extract symbols for source files
        if file_info["file_type"] == "source" and file_info["language"] == "python":
            try:
                symbols = self._extract_symbols(file_path)
                symbols_found += len(symbols)
                # Store symbols
                self._store_symbols(file_path, symbols)
            except Exception as e:
                errors.append(f"Error extracting {file_path}: {e}")

        # Progress callback
        if progress_callback:
            progress_callback(files_indexed, None, f"Indexing {file_path.name}")

    # Save index
    self._save_index(all_files)

    duration = time.time() - start
    return IndexResult(files_indexed, symbols_found, duration, errors)
```

**Helper Methods**:
```python
def _load_gitignore(self) -> List[str]:
    """Load .gitignore patterns."""
    patterns = [
        ".git", "__pycache__", "*.pyc", ".venv", "venv",
        "node_modules", ".DS_Store", "*.egg-info"
    ]

    gitignore_file = self.root_dir / ".gitignore"
    if gitignore_file.exists():
        with open(gitignore_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)

    return patterns

def _should_ignore(self, file_path: Path, patterns: List[str]) -> bool:
    """Check if file should be ignored."""
    import fnmatch
    relative = file_path.relative_to(self.root_dir)
    path_str = str(relative)

    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern):
            return True
        if pattern in path_str:  # Simple substring match
            return True

    return False

def _categorize_file(self, file_path: Path) -> Dict:
    """Categorize file by type and language."""
    suffix = file_path.suffix.lower()

    # Detect language
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
    }
    language = language_map.get(suffix)

    # Detect file type
    path_str = str(file_path)
    if "test" in path_str or path_str.endswith("_test.py"):
        file_type = "test"
    elif suffix in [".md", ".rst", ".txt"]:
        file_type = "docs"
    elif suffix in [".json", ".yml", ".yaml", ".toml", ".ini"]:
        file_type = "config"
    elif language:
        file_type = "source"
    else:
        file_type = "other"

    # Get file stats
    stat = file_path.stat()
    line_count = 0
    if file_type in ["source", "test"]:
        try:
            with open(file_path) as f:
                line_count = len(f.readlines())
        except:
            pass

    return {
        "path": str(file_path),
        "relative_path": str(file_path.relative_to(self.root_dir)),
        "file_type": file_type,
        "language": language,
        "size_bytes": stat.st_size,
        "line_count": line_count,
        "last_modified": stat.st_mtime,
    }

def _save_index(self, files: List[Dict]):
    """Save index to JSON."""
    index_data = {
        "version": "0.11.0",
        "indexed_at": datetime.now().isoformat(),
        "root_path": str(self.root_dir),
        "files": files,
        "statistics": {
            "total_files": len(files),
            "by_type": self._count_by_key(files, "file_type"),
            "by_language": self._count_by_key(files, "language"),
        }
    }

    index_file = self.map_dir / "index.json"
    with open(index_file, "w") as f:
        json.dump(index_data, f, indent=2)

    self._index = index_data
```

**Tests** (10+ tests):
- Test file scanning
- Test .gitignore respect
- Test file categorization
- Test language detection
- Test index.json creation
- Test incremental indexing
- Test error handling

**Deliverable**: Working file indexing, 15+ tests passing

---

### Task 4: Implement PythonSymbolExtractor (6 hours)
**Priority**: HIGH
**Depends on**: Task 2

**File**: `clauxton/intelligence/symbol_extractor.py`

**Implementation**:
```python
"""
Symbol extraction from source files using tree-sitter.
"""

from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class SymbolExtractor:
    """Extract symbols from source files."""

    def __init__(self):
        self.extractors = {
            "python": PythonSymbolExtractor(),
        }

    def extract(self, file_path: Path, language: str) -> List:
        """Extract symbols from file."""
        extractor = self.extractors.get(language)
        if not extractor:
            logger.debug(f"No extractor for {language}")
            return []

        try:
            return extractor.extract(file_path)
        except Exception as e:
            logger.warning(f"Failed to extract from {file_path}: {e}")
            return []

class PythonSymbolExtractor:
    """Extract symbols from Python files."""

    def __init__(self):
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_python as tspython

            self.language = Language(tspython.language())
            self.parser = Parser(self.language)
            self.available = True
        except ImportError:
            logger.warning("tree-sitter not available, using ast fallback")
            self.available = False

    def extract(self, file_path: Path) -> List:
        """Extract symbols from Python file."""
        if self.available:
            return self._extract_with_tree_sitter(file_path)
        else:
            return self._extract_with_ast(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List:
        """Extract using tree-sitter."""
        with open(file_path, "rb") as f:
            tree = self.parser.parse(f.read())

        symbols = []
        self._walk_tree(tree.root_node, symbols, str(file_path))
        return symbols

    def _walk_tree(self, node, symbols: List, file_path: str):
        """Walk AST and extract symbols."""
        if node.type == "function_definition":
            # Extract function
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")

            # Get docstring
            docstring = None
            for child in node.children:
                if child.type == "expression_statement":
                    string_node = child.child_by_field_name("string")
                    if string_node:
                        docstring = string_node.text.decode().strip('"""\'\'\'')
                        break

            symbols.append({
                "name": name_node.text.decode() if name_node else "unknown",
                "type": "function",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,
                "line_end": node.end_point[0] + 1,
                "docstring": docstring,
                "signature": self._get_signature(node),
            })

        elif node.type == "class_definition":
            # Extract class
            name_node = node.child_by_field_name("name")

            # Get docstring
            docstring = None
            for child in node.children:
                if child.type == "block":
                    for stmt in child.children:
                        if stmt.type == "expression_statement":
                            string_node = stmt.children[0]
                            if string_node.type == "string":
                                docstring = string_node.text.decode().strip('"""\'\'\'')
                                break
                    break

            symbols.append({
                "name": name_node.text.decode() if name_node else "unknown",
                "type": "class",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,
                "line_end": node.end_point[0] + 1,
                "docstring": docstring,
            })

        # Recurse
        for child in node.children:
            self._walk_tree(child, symbols, file_path)

    def _get_signature(self, node) -> Optional[str]:
        """Extract function signature."""
        # Simplified - just get the name and parameters
        try:
            return node.text.decode().split(":")[0].strip()
        except:
            return None

    def _extract_with_ast(self, file_path: Path) -> List:
        """Fallback using built-in ast module."""
        import ast

        with open(file_path) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return []

        symbols = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({
                    "name": node.name,
                    "type": "function",
                    "file_path": str(file_path),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node),
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "file_path": str(file_path),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node),
                })

        return symbols
```

**Tests** (15+ tests):
- Test tree-sitter extraction
- Test function extraction
- Test class extraction
- Test docstring extraction
- Test signature extraction
- Test ast fallback
- Test syntax error handling
- Test empty file
- Test large file

**Deliverable**: Working symbol extraction, 30+ total tests

---

### Task 5: Implement Symbol Search (4 hours)
**Priority**: HIGH
**Depends on**: Task 3, Task 4

**Implementation**: Complete `RepositoryMap.search()`

**Features**:
- Search by symbol name (exact match)
- Search by symbol type (function, class)
- Search by file path
- Ranking by relevance

**Pseudocode**:
```python
def search(
    self,
    query: str,
    search_type: Literal["semantic", "exact", "fuzzy"] = "exact",
    limit: int = 20
) -> List[Symbol]:
    """Search for symbols."""
    symbols_data = self.symbols_data
    results = []

    query_lower = query.lower()

    for file_path, symbols in symbols_data.items():
        for symbol in symbols:
            # Exact match
            if search_type == "exact":
                if query_lower in symbol["name"].lower():
                    results.append(Symbol(**symbol))

            # Fuzzy match
            elif search_type == "fuzzy":
                if self._fuzzy_match(query_lower, symbol["name"].lower()):
                    results.append(Symbol(**symbol))

    # Limit results
    return results[:limit]

def _fuzzy_match(self, query: str, text: str) -> bool:
    """Simple fuzzy matching."""
    query_chars = list(query)
    text_chars = list(text)

    qi = 0
    for char in text_chars:
        if qi < len(query_chars) and char == query_chars[qi]:
            qi += 1

    return qi == len(query_chars)
```

**Tests** (10+ tests):
- Test exact search
- Test fuzzy search
- Test case insensitivity
- Test limit parameter
- Test empty results
- Test search by type

**Deliverable**: Working search, 40+ total tests

---

### Task 6: Add ast Module Fallback (2 hours)
**Priority**: MEDIUM
**Depends on**: Task 4

**Implementation**: Already included in Task 4

**Additional Tests**:
- Test fallback when tree-sitter unavailable
- Test parity between tree-sitter and ast
- Test error messages

**Deliverable**: Graceful degradation, 42+ total tests

---

### Task 7: Write Comprehensive Tests (5 hours)
**Priority**: HIGH
**Depends on**: Task 5

**Test Coverage Target**: 90%

**Test Categories**:
1. Unit tests (repository_map.py): 20 tests
2. Unit tests (symbol_extractor.py): 15 tests
3. Integration tests (end-to-end): 10 tests
4. Edge cases and errors: 5 tests

**Total**: 50+ tests

**Key Test Scenarios**:
- Empty project
- Project with no Python files
- Large project (1000+ files)
- Syntax errors in source files
- Unicode filenames
- Nested directories
- Symlinks (skip)
- Binary files (skip)

**Deliverable**: 50+ tests, 90% coverage

---

### Task 8: Add Basic CLI Commands (2 hours)
**Priority**: MEDIUM
**Depends on**: Task 5

**File**: `clauxton/cli/map.py` (new)

**Commands**:
```bash
clauxton map index           # Index codebase
clauxton map stats           # Show statistics
clauxton map search QUERY    # Search symbols
clauxton map clear           # Delete index
```

**Implementation**:
```python
import click
from pathlib import Path
from clauxton.intelligence.repository_map import RepositoryMap

@click.group()
def map():
    """Repository map commands."""
    pass

@map.command()
def index():
    """Index the codebase."""
    root = Path.cwd()
    repo_map = RepositoryMap(root)

    click.echo("🔍 Indexing repository...")
    result = repo_map.index()

    click.echo(f"✅ Indexed {result.files_indexed} files")
    click.echo(f"✅ Found {result.symbols_found} symbols")
    click.echo(f"⏱️  Duration: {result.duration_seconds:.2f}s")

@map.command()
def stats():
    """Show repository statistics."""
    root = Path.cwd()
    repo_map = RepositoryMap(root)

    index = repo_map.index_data
    stats = index.get("statistics", {})

    click.echo("📊 Repository Statistics")
    click.echo(f"Total files: {stats.get('total_files', 0)}")
    # ... more stats

@map.command()
@click.argument("query")
def search(query: str):
    """Search for symbols."""
    root = Path.cwd()
    repo_map = RepositoryMap(root)

    results = repo_map.search(query, limit=10)

    click.echo(f"🔍 Search results for '{query}':")
    for symbol in results:
        click.echo(f"  {symbol.name} ({symbol.type}) at {symbol.file_path}:{symbol.line_start}")
```

**Integration**: Add to `clauxton/cli/main.py`:
```python
from clauxton.cli.map import map

cli.add_command(map)
```

**Deliverable**: Working CLI commands, 55+ total tests

---

## 📊 Progress Tracking

### Daily Goals

**Day 1** (3-4 hours):
- ✅ Task 1: Project setup (30min)
- ✅ Task 2: RepositoryMap skeleton (3h)
- Target: 5+ tests passing

**Day 2** (4-5 hours):
- ✅ Task 3: File indexing (4h)
- Target: 15+ tests passing

**Day 3** (6-7 hours):
- ✅ Task 4: Symbol extraction (6h)
- Target: 30+ tests passing

**Day 4** (4-5 hours):
- ✅ Task 5: Symbol search (4h)
- Target: 40+ tests passing

**Day 5** (3-4 hours):
- ✅ Task 6: ast fallback (2h)
- ✅ Task 7: Additional tests (2h)
- Target: 50+ tests passing

**Day 6-7** (2-3 hours):
- ✅ Task 7: Complete tests (3h)
- ✅ Task 8: CLI commands (2h)
- Target: 55+ tests, 90% coverage

---

## 🎯 Success Metrics

### Quantitative Targets

| Metric | Target | Status |
|--------|--------|--------|
| Tests | 50+ | TBD |
| Coverage | 90% | TBD |
| Performance (1K files) | <2s | TBD |
| Performance (10K files) | <10s | TBD |
| Symbol accuracy | 95%+ | TBD |

### Qualitative Targets

- ✅ Code passes mypy strict mode
- ✅ Code passes ruff checks
- ✅ Documentation complete
- ✅ API intuitive and clean
- ✅ Error messages helpful

---

## 🚧 Known Challenges

### Challenge 1: .gitignore Parsing
**Complexity**: MEDIUM
**Solution**: Use simple pattern matching, improve later

### Challenge 2: Large Files
**Complexity**: LOW
**Solution**: Skip files >1MB by default

### Challenge 3: Binary Files
**Complexity**: LOW
**Solution**: Detect and skip automatically

---

## 📚 Resources

### Documentation
- tree-sitter Python docs: https://github.com/tree-sitter/tree-sitter-python
- Python ast docs: https://docs.python.org/3/library/ast.html
- fnmatch docs: https://docs.python.org/3/library/fnmatch.html

### Code References
- Benchmark script: `benchmarks/benchmark_indexing.py`
- Technical decisions: `docs/V0.11.0_TECHNICAL_DECISIONS.md`

---

## 🎉 Week 1 Deliverables

At end of Week 1, we should have:

1. ✅ Working Repository Map with Python support
2. ✅ File indexing (respects .gitignore)
3. ✅ Symbol extraction (tree-sitter + ast fallback)
4. ✅ Basic search functionality
5. ✅ JSON storage (index.json, symbols.json)
6. ✅ 50+ tests passing
7. ✅ 90% code coverage
8. ✅ Basic CLI commands
9. ✅ Performance validated (<2s for 1K files)

**Ready to proceed to Week 2**: Dependency graph + semantic search

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Status**: 📋 Ready to Start
