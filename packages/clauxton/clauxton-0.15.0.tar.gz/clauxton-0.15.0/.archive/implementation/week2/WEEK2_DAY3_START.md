# Week 2 Day 3: Start Guide - Go Parser Setup

**Date**: 2025-10-23+
**Task**: Go Parser Implementation
**Estimated Time**: 2-3 hours
**Branch**: `feature/v0.11.0-repository-map`
**Previous Session**: Week 2 Day 2 Complete (TypeScript Parser + Enhanced Testing)

---

## 📊 Current State (Week 2 Day 2 完了時点)

### ✅ Completed Languages
1. **Python** ✅ (Week 1 + Week 2 Day 2 refactored)
   - PythonParser, PythonSymbolExtractor
   - 13 tests, 93% coverage
   - Supports: functions, classes, methods, docstrings, type hints, decorators

2. **JavaScript** ✅ (Week 2 Day 1)
   - JavaScriptParser, JavaScriptSymbolExtractor
   - 23 tests, 93% coverage
   - Supports: ES6+ classes, arrow functions, async/await, methods

3. **TypeScript** ✅ (Week 2 Day 2)
   - TypeScriptParser, TypeScriptSymbolExtractor
   - 24 tests (21 + 3 enhanced), 93% coverage
   - Supports: interfaces, type aliases, generics, type annotations

### 📈 Current Test Statistics
```
Total Tests: 146 (100% pass)
├── Parser Tests: 14 (direct unit tests)
├── Python Tests: 13
├── JavaScript Tests: 23
├── TypeScript Tests: 24 (21 + 3 enum/namespace/overload)
├── Integration Tests: 4
├── Repository Map Tests: 81
└── Execution Time: ~2.1s

Coverage (Intelligence Module):
├── parser.py: 86% (59 lines, 8 missed)
├── symbol_extractor.py: 93% (226 lines, 15 missed)
└── repository_map.py: 92% (287 lines, 22 missed)
```

### 📁 File Structure
```
clauxton/intelligence/
├── __init__.py
├── parser.py                     # BaseParser, PythonParser, JavaScriptParser, TypeScriptParser
├── symbol_extractor.py           # SymbolExtractor, Python/JS/TS extractors (674 lines)
└── repository_map.py             # RepositoryMap (indexing, search)

tests/intelligence/
├── test_parser.py                # 14 tests (NEW in Day 2)
├── test_symbol_extractor.py      # 17 tests (13 Python + 4 integration)
├── test_javascript_extractor.py  # 23 tests
├── test_typescript_extractor.py  # 24 tests (21 + 3 enhanced)
└── test_repository_map.py        # 81 tests

tests/fixtures/
├── python/                       # sample.py, empty.py, unicode.py
├── javascript/                   # sample.js, empty.js, unicode.js
└── typescript/                   # sample.ts, empty.ts, unicode.ts
```

### 🔧 Dependencies (pyproject.toml)
```toml
dependencies = [
    "pydantic>=2.0",
    "click>=8.1",
    "pyyaml>=6.0",
    "gitpython>=3.1",
    "mcp>=1.0",
    "scikit-learn>=1.3",
    "numpy>=1.24",
    "tree-sitter>=0.20",
    "tree-sitter-python>=0.20",
    "tree-sitter-javascript>=0.20",
    "tree-sitter-typescript>=0.20",
]
```

---

## 🎯 Week 2 Day 3 Goals

### Task 5: Go Parser Implementation (2-3 hours)

**Objective**: Add Go language symbol extraction support

**Target Symbols**:
1. Functions: `func add(a, b int) int`
2. Methods: `func (r *Receiver) Method()`
3. Structs: `type User struct { Name string }`
4. Interfaces: `type Reader interface { Read() }`
5. Type definitions: `type Status string`

**Deliverables**:
- GoParser class in parser.py
- GoSymbolExtractor class in symbol_extractor.py
- 20+ comprehensive tests
- 3 test fixtures (sample.go, empty.go, unicode.go)
- Documentation updates

---

## 📋 Implementation Plan

### Step 1: Install Dependencies (5 min)
```bash
# Activate virtual environment
source .venv/bin/activate

# Install tree-sitter-go
pip install tree-sitter-go

# Verify installation
python -c "import tree_sitter_go; print('✅ Go parser installed')"

# Update pyproject.toml
# Add: "tree-sitter-go>=0.20" to dependencies
```

### Step 2: Investigate Go AST Structure (15 min)
Create investigation script to understand Go AST nodes:
```python
# /tmp/test_go_ast.py
import tree_sitter_go as tsgo
from tree_sitter import Language, Parser

go_code = """
package main

type User struct {
    Name string
    Age  int
}

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Status string

func add(a, b int) int {
    return a + b
}

func (u *User) GetName() string {
    return u.Name
}
"""

language = Language(tsgo.language())
parser = Parser(language)
tree = parser.parse(go_code.encode())

def print_tree(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{node.type}")
    if node.type in ["identifier", "type_identifier", "field_identifier"]:
        print(f"{prefix}  → {node.text.decode()}")
    for child in node.children:
        print_tree(child, indent + 1)

print("=== Go AST Structure ===")
print_tree(tree.root_node)
```

**Key node types to identify**:
- `type_declaration` + `struct_type` → struct
- `type_declaration` + `interface_type` → interface
- `type_declaration` → type alias
- `function_declaration` → function
- `method_declaration` → method

### Step 3: Create Test Fixtures (10 min)
```bash
mkdir -p tests/fixtures/go
```

**tests/fixtures/go/sample.go**:
```go
// Sample Go file for testing symbol extraction.
package main

import "fmt"

// User represents a user in the system
type User struct {
    Name string
    Age  int
}

// Reader defines the Read interface
type Reader interface {
    Read(p []byte) (n int, err error)
    Close() error
}

// Status represents operation status
type Status string

// Add adds two integers
func Add(a, b int) int {
    return a + b
}

// Multiply multiplies two integers
func Multiply(a, b int) int {
    return a * b
}

// GetName returns the user's name
func (u *User) GetName() string {
    return u.Name
}

// SetName sets the user's name
func (u *User) SetName(name string) {
    u.Name = name
}

// Generic function (Go 1.18+)
func Identity[T any](x T) T {
    return x
}
```

**tests/fixtures/go/empty.go**:
```go
// Empty file for testing edge cases
package main
```

**tests/fixtures/go/unicode.go**:
```go
// Unicode test file (日本語)
package main

// こんにちは greets with Japanese
func こんにちは(名前 string) string {
    return "こんにちは、" + 名前 + "さん！"
}

// 😀Emoji represents an emoji interface
type 😀Emoji interface {
    Greet() string
}

// 🎉Celebration implements Emoji
type 🎉Celebration struct {
    Message string
}

func (c *🎉Celebration) Greet() string {
    return c.Message + " 🎉"
}
```

### Step 4: Implement GoParser (20 min)
**File**: `clauxton/intelligence/parser.py`

Add GoParser class:
```python
class GoParser(BaseParser):
    """
    Go parser using tree-sitter.

    Parses Go source files and returns AST for symbol extraction.
    Supports:
    - Functions
    - Methods
    - Structs
    - Interfaces
    - Type definitions
    - Generics (Go 1.18+)
    """

    def __init__(self) -> None:
        """Initialize Go parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_go as tsgo
            from tree_sitter import Language, Parser

            self.language = Language(tsgo.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("GoParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-go not available: {e}")
            self.available = False
```

Update module docstring to include Go.

### Step 5: Implement GoSymbolExtractor (40 min)
**File**: `clauxton/intelligence/symbol_extractor.py`

Add GoSymbolExtractor class (reference TypeScriptSymbolExtractor structure):

**Key implementation points**:
1. Import GoParser
2. Initialize in __init__
3. Implement _walk_tree with Go-specific nodes:
   - `type_declaration` → Check child for struct/interface/type alias
   - `function_declaration` → Extract function
   - `method_declaration` → Extract method
4. Extract signatures and comments
5. Handle Unicode names

**Symbol types**:
- "struct"
- "interface"
- "type_alias"
- "function"
- "method"

### Step 6: Update SymbolExtractor Dispatcher (5 min)
```python
class SymbolExtractor:
    def __init__(self) -> None:
        self.extractors: Dict[str, any] = {  # type: ignore
            "python": PythonSymbolExtractor(),
            "javascript": JavaScriptSymbolExtractor(),
            "typescript": TypeScriptSymbolExtractor(),
            "go": GoSymbolExtractor(),  # ADD THIS
        }
```

### Step 7: Create Comprehensive Tests (30 min)
**File**: `tests/intelligence/test_go_extractor.py`

**Test structure** (target: 20+ tests):
```python
class TestGoSymbolExtractor:
    # Initialization
    def test_init(self)

    # Basic extraction (8 tests)
    def test_extract_function(self)
    def test_extract_method(self)
    def test_extract_struct(self)
    def test_extract_interface(self)
    def test_extract_type_alias(self)
    def test_extract_multiple_functions(self)
    def test_extract_struct_with_methods(self)
    def test_extract_mixed_symbols(self)

    # Go-specific (3 tests)
    def test_extract_pointer_receiver(self)
    def test_extract_value_receiver(self)
    def test_extract_generic_function(self)  # Go 1.18+

    # Edge cases (4 tests)
    def test_extract_empty_file(self)
    def test_extract_comments_only(self)
    def test_extract_with_unicode(self)
    def test_extract_with_package_only(self)

    # Error handling (2 tests)
    def test_extract_file_not_found(self)
    def test_extract_when_parser_unavailable(self)

    # Integration (1 test)
    def test_integration_with_symbol_extractor(self)

    # Fixtures (3 tests)
    def test_fixture_sample_go(self)
    def test_fixture_empty_go(self)
    def test_fixture_unicode_go(self)
```

### Step 8: Add Parser Tests (10 min)
**File**: `tests/intelligence/test_parser.py`

Add TestGoParser class (4 tests):
```python
class TestGoParser:
    def test_init(self)
    def test_parse_simple_file(self, tmp_path)
    def test_parse_nonexistent_file(self)
    def test_parse_when_unavailable(self, tmp_path, monkeypatch)
```

### Step 9: Run Tests & Quality Checks (10 min)
```bash
# Run Go tests
pytest tests/intelligence/test_go_extractor.py -v
# Expected: 20+ tests passing

# Run all intelligence tests
pytest tests/intelligence/ -v
# Expected: 146 + 24 = 170 tests passing

# Check coverage
pytest tests/intelligence/ --cov=clauxton/intelligence --cov-report=term-missing

# Type checking
mypy clauxton/intelligence/

# Linting
ruff check clauxton/intelligence/ tests/intelligence/
ruff check --fix clauxton/intelligence/ tests/intelligence/
```

### Step 10: Update Documentation (10 min)
**Files to update**:
1. `CLAUDE.md` - Update progress, package structure
2. `STATUS.md` - Mark Week 2 Day 3 complete
3. `README.md` - Add Go to language support list
4. `pyproject.toml` - Add tree-sitter-go dependency
5. Create `docs/WEEK2_DAY3_COMPLETION.md`

---

## ✅ Success Criteria

### Must Have
- [ ] tree-sitter-go installed and verified
- [ ] GoParser implemented and tested (4 tests)
- [ ] GoSymbolExtractor implemented (200+ lines)
- [ ] 20+ Go extractor tests passing (100%)
- [ ] Coverage > 90% for new code
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] All existing tests still passing (146 tests)

### Go Symbol Support
- [ ] Functions (`func Foo()`)
- [ ] Methods (`func (r *Receiver) Method()`)
- [ ] Structs (`type User struct {}`)
- [ ] Interfaces (`type Reader interface {}`)
- [ ] Type aliases (`type Status string`)
- [ ] Unicode names (日本語, 😀)

### Expected Metrics
```
Total Tests: 170 (146 + 24 Go)
├── Parser Tests: 18 (14 + 4 Go)
├── Go Tests: 20+
├── Other Tests: 146 (unchanged)
└── Pass Rate: 100%

Coverage:
├── parser.py: 86% → 88%+
├── symbol_extractor.py: 93% (maintain)
└── repository_map.py: 92% (maintain)
```

---

## 🔧 Environment Setup Commands

```bash
# Verify current branch
git status
git branch  # Should be on feature/v0.11.0-repository-map

# Check current state
pytest tests/intelligence/ -q  # Should show 146 passed

# Activate environment
source .venv/bin/activate

# Verify dependencies
python -c "import tree_sitter_python; print('Python ✅')"
python -c "import tree_sitter_javascript; print('JavaScript ✅')"
python -c "import tree_sitter_typescript; print('TypeScript ✅')"
```

---

## 📚 Reference Materials

### Similar Implementations
- **TypeScriptSymbolExtractor**: Lines 465-674 in symbol_extractor.py
- **JavaScriptSymbolExtractor**: Lines 278-462 in symbol_extractor.py
- **TypeScriptParser**: Lines 116-148 in parser.py

### Go-specific Resources
- Tree-sitter Go: https://github.com/tree-sitter/tree-sitter-go
- Go AST Explorer: https://astexplorer.net/ (select tree-sitter-go)
- Go Language Spec: https://go.dev/ref/spec

### Key Differences from TypeScript
1. **Structs** instead of classes
2. **Interfaces** with implicit implementation
3. **Methods** with explicit receiver syntax
4. **Type aliases** are simpler (no union types)
5. **Package declarations** at file start
6. **Capitalization** determines visibility (PascalCase = exported)

---

## 🐛 Known Issues to Consider

### From Week 2 Day 2
1. **Enum/Namespace**: TypeScript enum/namespace not extracted (documented behavior)
2. **Nested functions**: Deep nesting may not be fully extracted
3. **JSDoc/TSDoc**: Comment extraction not implemented (returns None)

### Go-specific Considerations
1. **Embedded structs**: May need special handling
2. **Anonymous functions**: Closures and function literals
3. **Build tags**: `// +build` directives (likely ignore)
4. **CGO**: C code integration (likely ignore)

---

## 📝 Git Commit Template

```
feat(intelligence): add Go symbol extraction support

Week 2 Day 3 Complete - Go Parser Setup

- Add GoParser with tree-sitter-go integration
- Add GoSymbolExtractor with full Go support
- Add 20+ comprehensive tests (100% pass, 93% coverage)
- Create Go test fixtures (sample.go, empty.go, unicode.go)
- Add tree-sitter-go dependency

Supported Go features:
- Functions (func Foo())
- Methods (func (r *Receiver) Method())
- Structs (type User struct {})
- Interfaces (type Reader interface {})
- Type aliases (type Status string)
- Pointer/value receivers
- Unicode/emoji names
- Generics (Go 1.18+)

Test coverage:
- 170 intelligence tests (24 Go + 146 existing)
- 93% symbol_extractor.py coverage
- 88% parser.py coverage

Quality checks:
✅ mypy: no issues
✅ ruff: compliant
✅ pytest: 170/170 passed (100%)

Language support: Python ✅ | JavaScript ✅ | TypeScript ✅ | Go ✅
```

---

## 📊 Expected Final State

### Test Count
```
Before: 146 tests
After:  170 tests (+24, +16.4%)

New Tests:
├── test_parser.py: +4 (GoParser tests)
└── test_go_extractor.py: +20 (NEW file)
```

### Coverage
```
Intelligence Module:
├── parser.py: 86% → 88%+ (Go parser tests)
├── symbol_extractor.py: 93% (maintain, add ~200 lines)
└── repository_map.py: 92% (unchanged)
```

### Language Support Matrix
| Language   | Parser | Extractor | Tests | Status |
|------------|--------|-----------|-------|--------|
| Python     | ✅     | ✅        | 13    | Complete |
| JavaScript | ✅     | ✅        | 23    | Complete |
| TypeScript | ✅     | ✅        | 24    | Complete |
| **Go**     | ✅     | ✅        | 20+   | **Complete (Day 3)** |
| Rust       | ❌     | ❌        | -     | Day 4 (Next) |

---

## 🚀 Next Steps After Completion

**Week 2 Day 4**: Rust Parser Setup (2-3 hours)
- Similar structure to Go
- Focus on: functions, methods, structs, traits, impl blocks
- Target: 20+ tests, 93% coverage

**Week 2 Day 5-7**: Testing, Polish, Documentation
- Integration testing across all languages
- Performance optimization
- Comprehensive documentation
- CLI/MCP integration

---

## 📞 Quick Reference

### File Paths
```
Implementation:
- clauxton/intelligence/parser.py (add GoParser)
- clauxton/intelligence/symbol_extractor.py (add GoSymbolExtractor)

Tests:
- tests/intelligence/test_parser.py (add TestGoParser)
- tests/intelligence/test_go_extractor.py (NEW, 20+ tests)
- tests/fixtures/go/ (NEW, 3 fixtures)

Documentation:
- CLAUDE.md (update progress)
- STATUS.md (mark Day 3 complete)
- README.md (add Go support)
- pyproject.toml (add dependency)
- docs/WEEK2_DAY3_COMPLETION.md (NEW)
```

### Key Commands
```bash
# Development
source .venv/bin/activate
pytest tests/intelligence/test_go_extractor.py -v
mypy clauxton/intelligence/
ruff check --fix clauxton/intelligence/ tests/intelligence/

# Verification
pytest tests/intelligence/ -q  # Should show 170 passed
pytest tests/intelligence/ --cov=clauxton/intelligence --cov-report=term-missing
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: Claude Code Assistant
**Status**: Ready for Week 2 Day 3 Implementation
**Estimated Time**: 2-3 hours

---

**Good luck with Week 2 Day 3! 🚀**
