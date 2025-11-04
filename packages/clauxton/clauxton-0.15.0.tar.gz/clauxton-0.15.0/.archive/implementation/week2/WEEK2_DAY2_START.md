# Week 2 Day 2: Quick Start Guide

**Date**: 2025-10-23+
**Task**: TypeScript Parser Setup + Python Parser Integration
**Estimated Time**: 3 hours (1h Python + 2h TypeScript)
**Branch**: `feature/v0.11.0-repository-map`

---

## 🎯 Goals for Today

1. **Task 2**: Python Parser Integration (1 hour)
   - Refactor PythonSymbolExtractor to use PythonParser
   - Ensure backward compatibility

2. **Task 3**: TypeScript Parser Setup (2 hours)
   - Install tree-sitter-typescript
   - Implement TypeScriptParser and TypeScriptSymbolExtractor
   - Add 20+ comprehensive tests

---

## 🚀 Quick Start Commands

### Environment Setup
```bash
# Navigate to project
cd /home/kishiyama-n/workspace/projects/clauxton

# Activate virtual environment
source .venv/bin/activate

# Verify current state
git status
git branch  # Should be on feature/v0.11.0-repository-map

# Verify JavaScript implementation works
python -c "from clauxton.intelligence.symbol_extractor import JavaScriptSymbolExtractor; print('✅ JS ready')"

# Run existing tests to confirm baseline
pytest tests/intelligence/test_javascript_extractor.py -v
# Expected: 23 passed
```

---

## 📋 Task 2: Python Parser Integration (1 hour)

### Current State
- PythonSymbolExtractor currently has its own tree-sitter initialization
- PythonParser exists in parser.py but is not used
- All Python tests passing (18 tests)

### Implementation Steps

#### Step 1: Review Current Code (5 min)
```bash
# View current PythonSymbolExtractor
cat clauxton/intelligence/symbol_extractor.py | grep -A 30 "class PythonSymbolExtractor"

# View PythonParser
cat clauxton/intelligence/parser.py | grep -A 20 "class PythonParser"
```

#### Step 2: Refactor PythonSymbolExtractor (30 min)
**File**: `clauxton/intelligence/symbol_extractor.py`

**Changes needed**:
1. Remove tree-sitter initialization from `__init__`
2. Import and use PythonParser
3. Update `extract()` method to use parser

**Example**:
```python
from clauxton.intelligence.parser import PythonParser

class PythonSymbolExtractor:
    def __init__(self) -> None:
        self.parser = PythonParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        if not self.available:
            # Fallback to ast module
            return self._extract_with_ast(file_path)

        tree = self.parser.parse(file_path)
        if not tree:
            return self._extract_with_ast(file_path)

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))
        return symbols
```

#### Step 3: Run Tests (15 min)
```bash
# Run Python extractor tests
pytest tests/intelligence/test_symbol_extractor.py::TestPythonSymbolExtractor -v

# Expected: All 18 tests passing
# If failures: Debug and fix

# Run type checking
mypy clauxton/intelligence/symbol_extractor.py

# Run linting
ruff check clauxton/intelligence/symbol_extractor.py
```

#### Step 4: Update Documentation (10 min)
Add comment explaining the refactoring:
```python
class PythonSymbolExtractor:
    """
    Extract symbols from Python files.

    Uses PythonParser (tree-sitter) for accurate parsing when available,
    with automatic fallback to Python's built-in ast module.

    Refactored in v0.11.0 to use shared parser infrastructure.
    """
```

---

## 📋 Task 3: TypeScript Parser Setup (2 hours)

### Step 1: Install Dependencies (5 min)
```bash
# Install tree-sitter-typescript
pip install tree-sitter-typescript

# Verify installation
python -c "import tree_sitter_typescript; print('✅ TypeScript parser installed')"

# Update pyproject.toml
# Add: "tree-sitter-typescript>=0.20" to dependencies
```

### Step 2: Investigate TypeScript AST (15 min)
Create investigation script:
```bash
# Create test script
cat > /tmp/test_ts_ast.py << 'EOF'
#!/usr/bin/env python3
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser

ts_code = """
// TypeScript sample
interface User {
  name: string;
  age: number;
}

class UserService {
  constructor(private db: Database) {}

  async getUser(id: string): Promise<User> {
    return await this.db.findOne(id);
  }
}

function processUser(user: User): void {
  console.log(user.name);
}

const formatName = (name: string): string => name.toUpperCase();

export { UserService, processUser };
"""

language = Language(tsts.language_typescript())
parser = Parser(language)
tree = parser.parse(ts_code.encode())

def print_tree(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{node.type}")
    if node.type in ["identifier", "property_identifier", "type_identifier"]:
        print(f"{prefix}  → {node.text.decode()}")
    for child in node.children:
        print_tree(child, indent + 1)

print("=== TypeScript AST Structure ===\n")
print_tree(tree.root_node)
EOF

python /tmp/test_ts_ast.py
```

**Key node types to identify**:
- `class_declaration`
- `function_declaration`
- `method_definition`
- `arrow_function`
- `interface_declaration` (TypeScript-specific)
- `type_alias_declaration` (TypeScript-specific)
- `lexical_declaration`

### Step 3: Create Test Fixtures (10 min)
```bash
# Create fixtures directory
mkdir -p tests/fixtures/typescript

# Create sample.ts
cat > tests/fixtures/typescript/sample.ts << 'EOF'
/**
 * Sample TypeScript file for testing symbol extraction.
 */

// Interface
interface Calculator {
  add(a: number, b: number): number;
  multiply(a: number, b: number): number;
}

// Type alias
type Operation = 'add' | 'subtract' | 'multiply' | 'divide';

// Class with types
class MathService implements Calculator {
  constructor(private precision: number = 2) {}

  add(a: number, b: number): number {
    return a + b;
  }

  multiply(a: number, b: number): number {
    return a * b;
  }

  async calculate(op: Operation, a: number, b: number): Promise<number> {
    switch (op) {
      case 'add': return this.add(a, b);
      case 'multiply': return this.multiply(a, b);
      default: throw new Error('Unsupported');
    }
  }
}

// Regular function with types
function factorial(n: number): number {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// Arrow function with types
const square = (x: number): number => x * x;

// Generic function
function identity<T>(arg: T): T {
  return arg;
}

// Export
export { MathService, factorial, Calculator };
EOF

# Create empty.ts
echo "// Empty file for testing edge cases" > tests/fixtures/typescript/empty.ts

# Create unicode.ts
cat > tests/fixtures/typescript/unicode.ts << 'EOF'
/**
 * Unicode test file (日本語)
 */

// Function with Japanese name
function こんにちは(名前: string): string {
  return `こんにちは、${名前}さん！`;
}

// Interface with emoji
interface 😀Emoji {
  message: string;
  greet(): string;
}

// Class with emoji
class 🎉Celebration implements 😀Emoji {
  constructor(public message: string) {}

  greet(): string {
    return `${this.message} 🎉`;
  }
}

export { こんにちは, 😀Emoji, 🎉Celebration };
EOF
```

### Step 4: Implement TypeScriptParser (20 min)
**File**: `clauxton/intelligence/parser.py`

Add TypeScriptParser class:
```python
class TypeScriptParser(BaseParser):
    """
    TypeScript parser using tree-sitter.

    Parses TypeScript source files and returns AST for symbol extraction.
    Supports:
    - Interfaces
    - Type aliases
    - Classes with type annotations
    - Functions with type signatures
    - Generics
    - Arrow functions
    - Import/export statements
    """

    def __init__(self) -> None:
        """Initialize TypeScript parser."""
        try:
            import tree_sitter_typescript as tsts
            # Use TypeScript language (not TSX)
            super().__init__(tsts.language_typescript)
        except ImportError:
            logger.warning("tree-sitter-typescript not available")
            self.available = False
```

### Step 5: Implement TypeScriptSymbolExtractor (40 min)
**File**: `clauxton/intelligence/symbol_extractor.py`

Add TypeScriptSymbolExtractor class (similar to JavaScriptSymbolExtractor but with TypeScript-specific nodes):

Key additions:
- `interface_declaration` → type="interface"
- `type_alias_declaration` → type="type_alias"
- Handle generic type parameters
- Extract type annotations from signatures

**Important**: TypeScript shares most syntax with JavaScript, so copy JavaScriptSymbolExtractor and extend it.

### Step 6: Update SymbolExtractor Dispatcher (5 min)
```python
class SymbolExtractor:
    def __init__(self) -> None:
        self.extractors: Dict[str, any] = {
            "python": PythonSymbolExtractor(),
            "javascript": JavaScriptSymbolExtractor(),
            "typescript": TypeScriptSymbolExtractor(),  # ADD THIS
        }
```

### Step 7: Create Comprehensive Tests (30 min)
**File**: `tests/intelligence/test_typescript_extractor.py`

Copy structure from `test_javascript_extractor.py` and adapt:

**Test categories** (target: 20+ tests):
1. Basic extraction (8 tests):
   - Interfaces
   - Type aliases
   - Classes
   - Regular functions
   - Arrow functions
   - Generic functions
   - Async functions
   - Methods

2. TypeScript-specific (5 tests):
   - Interface extraction
   - Type alias extraction
   - Generic types
   - Type annotations in signatures
   - Enum declarations (if supported)

3. Edge cases (4 tests):
   - Empty files
   - Comments only
   - Unicode/emoji
   - Nested structures

4. Error handling (2 tests):
   - File not found
   - tree-sitter unavailable

5. Integration (1 test):
   - SymbolExtractor dispatch

### Step 8: Run Tests & Quality Checks (10 min)
```bash
# Run TypeScript tests
pytest tests/intelligence/test_typescript_extractor.py -v
# Expected: 20+ tests passing

# Run all intelligence tests
pytest tests/intelligence/ -v
# Expected: 104 + 20 = 124 tests passing

# Check coverage
pytest tests/intelligence/test_typescript_extractor.py --cov=clauxton/intelligence/symbol_extractor --cov-report=term-missing

# Type checking
mypy clauxton/intelligence/

# Linting
ruff check clauxton/intelligence/ tests/intelligence/
ruff check --fix clauxton/intelligence/ tests/intelligence/
```

### Step 9: Update Documentation (10 min)
Update CLAUDE.md:
```diff
- **v0.11.0 Progress**: Week 2 Day 1 Complete! (551 tests, JS/Python symbol extraction)
+ **v0.11.0 Progress**: Week 2 Day 2 Complete! (574 tests, Python/JS/TS symbol extraction)
```

Update pyproject.toml:
```diff
+ "tree-sitter-typescript>=0.20",
```

---

## ✅ Success Criteria

### Task 2: Python Parser Integration
- [ ] PythonSymbolExtractor uses PythonParser
- [ ] All 18 Python tests passing
- [ ] No regression in functionality
- [ ] Type checking passes
- [ ] Linting passes

### Task 3: TypeScript Parser Setup
- [ ] tree-sitter-typescript installed
- [ ] TypeScript AST structure documented
- [ ] 3 test fixtures created
- [ ] TypeScriptParser implemented
- [ ] TypeScriptSymbolExtractor implemented
- [ ] 20+ tests passing (100%)
- [ ] Coverage > 90%
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated

---

## 📊 Expected Final Metrics

```
Total Tests: 574 (551 + 23 refactor validation)
├── JavaScript: 23 tests
├── TypeScript: 20+ tests (NEW)
├── Python: 18 tests (refactored)
└── Pass Rate: 100%

Coverage:
├── symbol_extractor.py: 93%+
├── parser.py: 40%+ (direct testing)
└── repository_map.py: 92%
```

---

## 🐛 Troubleshooting

### Issue: tree-sitter-typescript import fails
```bash
# Solution: Ensure correct import
import tree_sitter_typescript as tsts
language = Language(tsts.language_typescript())  # NOT language_tsx()
```

### Issue: Tests fail after Python refactoring
```bash
# Debug: Check parser availability
python -c "from clauxton.intelligence.parser import PythonParser; p = PythonParser(); print(p.available)"

# If False: tree-sitter-python not installed
pip install tree-sitter-python
```

### Issue: TypeScript tests have lower coverage
```bash
# Check missing lines
pytest tests/intelligence/test_typescript_extractor.py --cov=clauxton/intelligence/symbol_extractor --cov-report=term-missing

# Add tests for uncovered branches
```

---

## 📞 Support Resources

### AST References
- TypeScript AST: https://astexplorer.net/ (select tree-sitter-typescript)
- Node types: https://github.com/tree-sitter/tree-sitter-typescript/blob/master/src/node-types.json

### Code References
- JavaScriptSymbolExtractor: `clauxton/intelligence/symbol_extractor.py:280-473`
- JavaScript tests: `tests/intelligence/test_javascript_extractor.py`

---

## 📝 After Completion

### Create Completion Report
```bash
# Document today's work
cp docs/WEEK2_DAY1_COMPLETION.md docs/WEEK2_DAY2_COMPLETION.md
# Edit with Day 2 details

# Update STATUS.md
# Mark Day 2 as complete
```

### Commit Changes
```bash
git add clauxton/intelligence/ tests/intelligence/ docs/ pyproject.toml CLAUDE.md STATUS.md
git commit -m "feat(intelligence): add TypeScript support + refactor Python parser

Week 2 Day 2 Complete - TypeScript Parser Setup

- Refactor PythonSymbolExtractor to use PythonParser
- Add TypeScriptSymbolExtractor with full type support
- Support interfaces, type aliases, generics
- Add 20+ TypeScript tests (100% pass, 93% coverage)
- Create TypeScript test fixtures
- Add tree-sitter-typescript dependency

Test coverage:
- 574 total tests (23 JS + 20 TS + 18 Python refactored)
- 93% symbol_extractor.py coverage

Quality checks:
✅ mypy: no issues
✅ ruff: compliant
✅ pytest: 574/574 passed"
```

---

**Good luck with Week 2 Day 2! 🚀**

**Estimated Time**: 3 hours
**Start**: When you're ready
**Expected Completion**: Same day
