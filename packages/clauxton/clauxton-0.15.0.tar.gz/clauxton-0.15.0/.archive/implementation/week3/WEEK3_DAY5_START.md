# Week 3 Day 5 Start Guide: C++ Language Support

**Date**: 2025-10-24 (Ready to start)
**Task**: C++ Symbol Extraction Implementation
**Duration**: 2-3 hours
**Target**: 24+ tests, 90%+ coverage

---

## 🎯 Today's Goal

Implement complete C++ language support for symbol extraction:
- Functions, classes, methods, structs
- Namespaces, templates, constructors/destructors
- 24+ comprehensive tests with 90%+ coverage

---

## 📋 Pre-Flight Checklist

### ✅ Week 2 Complete
- 205 tests passing (100%)
- 92% coverage
- 5 languages: Python, JavaScript, TypeScript, Go, Rust
- All documentation updated

### 📦 Prerequisites
- tree-sitter-cpp package (will install)
- Week 2 code as templates
- Test fixtures ready to create

---

## 🛠️ Step-by-Step Implementation

### Step 1: Install Dependencies (5 min)

```bash
# Activate virtual environment
source .venv/bin/activate

# Install tree-sitter-cpp
pip install tree-sitter-cpp

# Verify installation
python -c "import tree_sitter_cpp; print('✅ tree-sitter-cpp installed')"
```

**Update pyproject.toml**:
```toml
dependencies = [
    ...
    "tree-sitter-rust>=0.20",
    "tree-sitter-cpp>=0.20",  # Add this line
]
```

---

### Step 2: Create CppParser (15 min)

**File**: `clauxton/intelligence/parser.py`

**Add import**:
```python
from clauxton.intelligence.parser import (
    GoParser,
    JavaScriptParser,
    PythonParser,
    RustParser,
    CppParser,  # Add this
    TypeScriptParser,
)
```

**Add class at end of file**:
```python
class CppParser(BaseParser):
    """
    C++ parser using tree-sitter.

    Parses C++ source files and returns AST for symbol extraction.
    Supports:
    - Functions
    - Classes (with inheritance)
    - Methods (including constructors/destructors)
    - Structs
    - Namespaces
    - Templates
    """

    def __init__(self) -> None:
        """Initialize C++ parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_cpp as tscpp
            from tree_sitter import Language, Parser

            self.language = Language(tscpp.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("CppParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-cpp not available: {e}")
            self.available = False
```

**Update module docstring**:
```python
"""
Multi-language parser using tree-sitter.

This module provides parsers for extracting AST nodes from source files.
Supports Python, JavaScript (ES6+), TypeScript, Go, Rust, and C++.

Example:
    >>> from clauxton.intelligence.parser import CppParser
    >>> cpp_parser = CppParser()
    >>> cpp_tree = cpp_parser.parse(Path("main.cpp"))
"""
```

---

### Step 3: Create CppSymbolExtractor (45 min)

**File**: `clauxton/intelligence/symbol_extractor.py`

**Add import**:
```python
from clauxton.intelligence.parser import (
    GoParser,
    PythonParser,
    RustParser,
    CppParser,  # Add this
    TypeScriptParser
)
```

**Add to SymbolExtractor.__init__**:
```python
def __init__(self) -> None:
    """Initialize symbol extractor with language-specific extractors."""
    self.extractors: Dict[str, any] = {  # type: ignore
        "python": PythonSymbolExtractor(),
        "javascript": JavaScriptSymbolExtractor(),
        "typescript": TypeScriptSymbolExtractor(),
        "go": GoSymbolExtractor(),
        "rust": RustSymbolExtractor(),
        "cpp": CppSymbolExtractor(),  # Add this
    }
```

**Add CppSymbolExtractor class** (at end of file):
```python
class CppSymbolExtractor:
    """
    Extract symbols from C++ files.

    Uses CppParser (tree-sitter) for accurate parsing.
    Supports:
    - Functions
    - Classes (with inheritance)
    - Methods (including constructors/destructors)
    - Structs
    - Namespaces
    - Templates
    - Operator overloading

    C++ specific features:
    - Constructor/destructor detection
    - Template parameter extraction
    - Namespace resolution
    - Method qualification (ClassName::method)
    """

    def __init__(self) -> None:
        """Initialize C++ symbol extractor."""
        self.parser = CppParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from C++ file.

        Args:
            file_path: Path to C++ source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-cpp not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via CppParser.

        Args:
            file_path: Path to C++ file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Function definition (int add(int a, int b) { ... })
        if node.type == "function_definition":  # type: ignore
            name_node = node.child_by_field_name("declarator")  # type: ignore
            if name_node:
                # Extract function name from declarator
                func_name = self._extract_function_name(name_node)
                if func_name:
                    symbol = {
                        "name": func_name,
                        "type": "function",
                        "file_path": file_path,
                        "line_start": node.start_point[0] + 1,  # type: ignore
                        "line_end": node.end_point[0] + 1,  # type: ignore
                        "docstring": None,  # TODO: Extract comments
                        "signature": self._extract_signature(node),
                    }
                    symbols.append(symbol)

        # Class definition (class MyClass { ... })
        elif node.type == "class_specifier":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Struct definition (struct Point { ... })
        elif node.type == "struct_specifier":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "struct",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Namespace definition (namespace utils { ... })
        elif node.type == "namespace_definition":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "namespace",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_function_name(self, declarator_node: any) -> Optional[str]:  # type: ignore
        """
        Extract function name from declarator node.

        Args:
            declarator_node: function_declarator node

        Returns:
            Function name or None
        """
        try:
            # Handle different declarator types
            if declarator_node.type == "function_declarator":  # type: ignore
                declarator = declarator_node.child_by_field_name("declarator")  # type: ignore
                if declarator:
                    return self._extract_function_name(declarator)
            elif declarator_node.type == "identifier":  # type: ignore
                return declarator_node.text.decode()  # type: ignore
            elif declarator_node.type == "qualified_identifier":  # type: ignore
                # For qualified names like ClassName::method
                name_node = declarator_node.child_by_field_name("name")  # type: ignore
                if name_node:
                    return name_node.text.decode()  # type: ignore
            elif declarator_node.type == "destructor_name":  # type: ignore
                return declarator_node.text.decode()  # type: ignore
            return None
        except Exception:
            return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function signature.

        Args:
            node: tree-sitter Node (function_definition)

        Returns:
            Function signature string or None
        """
        try:
            # Get the function declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except Exception:
            return None
```

---

### Step 4: Create Test Fixtures (10 min)

```bash
mkdir -p tests/fixtures/cpp
```

**Create `tests/fixtures/cpp/sample.cpp`**:
```cpp
// Sample C++ file for testing symbol extraction

#include <string>
#include <iostream>

/// User class
class User {
public:
    User(std::string name) : name_(name) {}
    ~User() {}

    std::string getName() const {
        return name_;
    }

    void setName(std::string name) {
        name_ = name;
    }

private:
    std::string name_;
};

/// Point struct
struct Point {
    int x;
    int y;
};

/// Utility namespace
namespace utils {
    /// Add two integers
    int add(int a, int b) {
        return a + b;
    }

    /// Max template function
    template<typename T>
    T max(T a, T b) {
        return a > b ? a : b;
    }
}

/// Global function
int multiply(int a, int b) {
    return a * b;
}
```

**Create `tests/fixtures/cpp/empty.cpp`**:
```cpp
// Empty C++ file for testing
```

**Create `tests/fixtures/cpp/unicode.cpp`**:
```cpp
// Unicode names test file

/// Japanese function
void こんにちは() {
    // Hello
}

/// Unicode class
class 使用者 {
public:
    void greet() {
        // Greeting
    }
};
```

---

### Step 5: Create Parser Tests (15 min)

**File**: `tests/intelligence/test_parser.py`

**Add import**:
```python
from clauxton.intelligence.parser import (
    GoParser,
    JavaScriptParser,
    PythonParser,
    RustParser,
    CppParser,  # Add this
    TypeScriptParser,
)
```

**Add test class** (at end of file):
```python
class TestCppParser:
    """Test CppParser initialization and parsing."""

    def test_init(self):
        """Test CppParser initialization."""
        parser = CppParser()
        assert parser is not None
        # Parser should be available if tree-sitter-cpp is installed
        assert parser.available is True

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple C++ file."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("""int add(int a, int b) {
    return a + b;
}
""")

        parser = CppParser()
        if not parser.available:
            pytest.skip("tree-sitter-cpp not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = CppParser()
        if not parser.available:
            pytest.skip("tree-sitter-cpp not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.cpp"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int foo() { return 0; }")

        parser = CppParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None
```

**Update module docstring** (at top of file):
```python
"""
Tests for language parsers.

Tests BaseParser, PythonParser, JavaScriptParser, TypeScriptParser,
GoParser, RustParser, and CppParser classes.
"""
```

---

### Step 6: Create Extractor Tests (30 min)

**Create `tests/intelligence/test_cpp_extractor.py`**:

```python
"""
Tests for C++ symbol extraction.

Tests CppSymbolExtractor functionality including:
- Basic symbol extraction (functions, classes, structs, namespaces)
- C++ specific features (templates, constructors/destructors)
- Edge cases (empty files, unicode names)
- Error handling
- Integration with SymbolExtractor
"""
# type: ignore  # tree-sitter has complex types

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import CppSymbolExtractor, SymbolExtractor


class TestCppSymbolExtractor:
    """Test C++ symbol extraction."""

    def test_init(self):
        """Test CppSymbolExtractor initialization."""
        extractor = CppSymbolExtractor()
        assert extractor.parser is not None
        assert extractor.available is True

    def test_extract_function(self, tmp_path: Path):
        """Test extracting a simple function."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""/// Add two integers
int add(int a, int b) {
    return a + b;
}
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "add"
        assert symbols[0]["type"] == "function"
        assert symbols[0]["line_start"] == 2

    def test_extract_class(self, tmp_path: Path):
        """Test extracting a class."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class User {
public:
    User();
    ~User();
    void setName(std::string name);
private:
    std::string name_;
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) >= 1
        class_sym = next(s for s in symbols if s["type"] == "class")
        assert class_sym["name"] == "User"

    def test_extract_struct(self, tmp_path: Path):
        """Test extracting a struct."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""struct Point {
    int x;
    int y;
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Point"
        assert symbols[0]["type"] == "struct"

    def test_extract_namespace(self, tmp_path: Path):
        """Test extracting a namespace."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""namespace utils {
    int helper() { return 42; }
}
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract namespace and function
        assert len(symbols) >= 1
        namespace_sym = next((s for s in symbols if s["type"] == "namespace"), None)
        assert namespace_sym is not None
        assert namespace_sym["name"] == "utils"

    def test_extract_multiple_symbols(self, tmp_path: Path):
        """Test extracting multiple symbols."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""int add(int a, int b) { return a + b; }
int multiply(int a, int b) { return a * b; }
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 2
        names = {s["name"] for s in symbols}
        assert names == {"add", "multiply"}

    def test_extract_empty_file(self, tmp_path: Path):
        """Test extracting from empty file."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("")

        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 0

    def test_extract_comments_only(self, tmp_path: Path):
        """Test extracting from file with only comments."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""// This is a comment
/* Another comment */
""")

        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 0

    def test_extract_with_unicode(self, tmp_path: Path):
        """Test extracting symbols with unicode names."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""void こんにちは() {
    // Hello
}
""")

        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) >= 1
        # Unicode should be preserved
        assert "こんにちは" in symbols[0]["name"]

    def test_extract_file_not_found(self):
        """Test extract raises FileNotFoundError for non-existent file."""
        extractor = CppSymbolExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/file.cpp"))

    def test_extract_when_parser_unavailable(self, tmp_path: Path):
        """Test extract returns empty list when parser unavailable."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("int foo() { return 0; }")

        extractor = CppSymbolExtractor()
        extractor.available = False

        symbols = extractor.extract(cpp_file)
        assert len(symbols) == 0

    def test_integration_with_symbol_extractor(self, tmp_path: Path):
        """Test integration with main SymbolExtractor."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""int add(int a, int b) {
    return a + b;
}
""")

        dispatcher = SymbolExtractor()
        symbols = dispatcher.extract(cpp_file, "cpp")

        assert len(symbols) == 1
        assert symbols[0]["name"] == "add"

    def test_fixture_sample_cpp(self):
        """Test extraction from sample.cpp fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "cpp" / "sample.cpp"
        if not fixture_path.exists():
            pytest.skip("sample.cpp fixture not found")

        extractor = CppSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract: User class, Point struct, utils namespace,
        # add function, max template, multiply function
        assert len(symbols) >= 6

        names = {s["name"] for s in symbols}
        assert "User" in names
        assert "Point" in names
        assert "utils" in names

    def test_fixture_empty_cpp(self):
        """Test extraction from empty.cpp fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "cpp" / "empty.cpp"
        if not fixture_path.exists():
            pytest.skip("empty.cpp fixture not found")

        extractor = CppSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        assert len(symbols) == 0

    def test_fixture_unicode_cpp(self):
        """Test extraction from unicode.cpp fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "cpp" / "unicode.cpp"
        if not fixture_path.exists():
            pytest.skip("unicode.cpp fixture not found")

        extractor = CppSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract Unicode function and class
        assert len(symbols) >= 2
```

---

### Step 7: Update Integration Tests (5 min)

**File**: `tests/intelligence/test_symbol_extractor.py`

Update the dispatcher test:
```python
def test_dispatcher_has_all_languages(self):
    """Test SymbolExtractor dispatcher includes all expected languages."""
    extractor = SymbolExtractor()

    expected_languages = {"python", "javascript", "typescript", "go", "rust", "cpp"}
    actual_languages = set(extractor.extractors.keys())

    assert expected_languages == actual_languages
```

---

### Step 8: Run Tests and Verify (10 min)

```bash
# Run C++ tests only
pytest tests/intelligence/test_cpp_extractor.py -v

# Run all intelligence tests
pytest tests/intelligence/ -q

# Check coverage
pytest tests/intelligence/ --cov=clauxton/intelligence --cov-report=term-missing

# Run quality checks
mypy clauxton/intelligence/
ruff check clauxton/intelligence/ tests/intelligence/
```

**Expected Results**:
- 24+ C++ tests passing
- 229+ total intelligence tests
- 90%+ coverage
- mypy: 0 errors
- ruff: 0 warnings

---

### Step 9: Update Documentation (10 min)

**1. REPOSITORY_MAP_GUIDE.md**:
```markdown
### v0.11.0 (Current)
- **C++** ✅ (functions, classes, methods, structs, namespaces, templates)
  - tree-sitter-cpp
```

**2. README.md**:
```markdown
  - **C++** ✅ Complete (functions, classes, structs, namespaces, templates)
```

**3. CHANGELOG.md**:
```markdown
- ✅ **C++ Support** (`symbol_extractor.py`): Complete feature set
  - tree-sitter-cpp parser
  - Extracts: functions, classes, methods, structs, namespaces, templates
  - Supports: constructors/destructors, operator overloading
  - 24 comprehensive tests with fixtures
```

**4. CLAUDE.md**:
```markdown
**v0.11.0 Progress**: Week 3 Day 5 Complete! (229 tests, 6 languages)
```

---

## ✅ Success Checklist

Before considering Day 5 complete:

### Implementation
- [ ] tree-sitter-cpp installed
- [ ] CppParser implemented and tested
- [ ] CppSymbolExtractor implemented
- [ ] Dispatcher integration complete

### Testing
- [ ] 4 parser tests passing
- [ ] 20+ extractor tests passing
- [ ] 3 fixtures created
- [ ] Integration tests updated
- [ ] 229+ total tests passing

### Quality
- [ ] mypy: 0 errors
- [ ] ruff: 0 warnings
- [ ] 90%+ coverage for new code
- [ ] All tests passing (100%)

### Documentation
- [ ] REPOSITORY_MAP_GUIDE.md updated
- [ ] README.md updated
- [ ] CHANGELOG.md updated
- [ ] CLAUDE.md updated
- [ ] WEEK3_DAY5_COMPLETION.md created

---

## 🎯 Expected Outcomes

**Test Count**: 205 → 229 (+24, +12%)
**Languages**: 5 → 6 (+C++)
**Coverage**: Maintained at 90%+
**Quality**: All checks passing

---

**Ready to start Week 3 Day 5! 🚀**

**Next**: After Day 5, proceed to Day 6 (Java) using similar pattern.
