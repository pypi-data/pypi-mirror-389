# Week 2 Implementation Plan: JavaScript/TypeScript Support

**Version**: v0.11.0
**Week**: 2 of 6
**Duration**: 5-7 days
**Estimated Effort**: 30 hours
**Status**: 📋 Ready to Start

---

## 🎯 Week 2 Goals

### Primary Objective
Add JavaScript and TypeScript symbol extraction to Repository Map.

### Success Criteria
- ✅ JavaScript symbol extraction working (tree-sitter)
- ✅ TypeScript symbol extraction working (tree-sitter)
- ✅ Multi-language dispatcher with fallback chain
- ✅ 40+ tests passing (90% coverage)
- ✅ Performance: 1000+ JS/TS files in <2 seconds
- ✅ CLI & MCP integration complete

---

## 📋 Task List (6 Tasks, 30 Hours)

### Task 1: JavaScript Parser Setup (2 hours)
**Priority**: HIGH
**Blocking**: Task 2, 3

**Subtasks**:
1. Install tree-sitter-javascript parser
   ```bash
   pip install tree-sitter-javascript
   ```

2. Research JavaScript AST structure
   - Function declarations: `function foo() {}`
   - Arrow functions: `const foo = () => {}`
   - Class declarations: `class Foo {}`
   - Method definitions: `foo() {}`
   - Async functions: `async function foo() {}`
   - Generator functions: `function* foo() {}`

3. Create test fixtures
   ```javascript
   // tests/fixtures/javascript/sample.js
   function authenticateUser(username, password) {
     // Authenticate user
     return true;
   }

   const getAuthToken = (userId) => {
     // Get auth token
     return 'token';
   };

   class AuthService {
     /**
      * Verify user credentials
      */
     verifyCredentials(username, password) {
       return true;
     }
   }
   ```

**Deliverable**: tree-sitter-javascript installed, AST research complete

---

### Task 2: JSSymbolExtractor Implementation (6 hours)
**Priority**: HIGH
**Depends on**: Task 1

**File**: `clauxton/intelligence/symbol_extractor.py`

**Implementation**:
```python
class JSSymbolExtractor:
    """Extract symbols from JavaScript files using tree-sitter."""

    def __init__(self):
        """Initialize JavaScript parser."""
        try:
            from tree_sitter_javascript import language as js_lang
            self.parser = Parser()
            self.parser.set_language(js_lang())
            self.available = True
        except ImportError:
            self.available = False

    def extract(self, file_path: Path) -> List[Symbol]:
        """
        Extract symbols from JavaScript file.

        Handles:
        - Function declarations
        - Arrow functions
        - Class declarations
        - Method definitions
        - Async/generator functions
        - JSDoc comments

        Returns:
            List of Symbol objects
        """
        if not self.available:
            return self._fallback_extract(file_path)

        # tree-sitter implementation
        # ...

    def _fallback_extract(self, file_path: Path) -> List[Symbol]:
        """Fallback using regex patterns."""
        # Simple regex-based extraction
        # ...
```

**Test Coverage**:
- Function declarations (5 types)
- Class declarations
- Method definitions
- Async/generator functions
- JSDoc extraction
- Edge cases: nested, destructuring, etc.

**Deliverable**: JSSymbolExtractor with 90%+ coverage

---

### Task 3: TypeScript Support (4 hours)
**Priority**: HIGH
**Depends on**: Task 2

**Subtasks**:
1. Install tree-sitter-typescript
   ```bash
   pip install tree-sitter-typescript
   ```

2. Implement TSSymbolExtractor
   - Extends JSSymbolExtractor
   - Additional TypeScript features:
     - Type annotations: `function foo(x: number): string`
     - Interfaces: `interface User {}`
     - Type aliases: `type ID = string | number`
     - Enums: `enum Status {}`
     - Decorators: `@Component`

3. Handle TypeScript-specific patterns
   ```typescript
   interface AuthService {
     authenticate(user: string, pass: string): Promise<boolean>;
   }

   class UserAuth implements AuthService {
     async authenticate(user: string, pass: string): Promise<boolean> {
       // Implementation
       return true;
     }
   }

   type Credentials = { username: string; password: string };
   ```

**Test Coverage**:
- All JavaScript features
- Type annotations
- Interfaces
- Type aliases
- Enums
- Decorators

**Deliverable**: TSSymbolExtractor with 90%+ coverage

---

### Task 4: Multi-Language Integration (3 hours)
**Priority**: HIGH
**Depends on**: Task 2, 3

**File**: `clauxton/intelligence/symbol_extractor.py`

**Implementation**:
```python
class SymbolExtractor:
    """
    Multi-language symbol extractor with automatic language detection.

    Supports:
    - Python (tree-sitter + ast fallback)
    - JavaScript (tree-sitter + regex fallback)
    - TypeScript (tree-sitter + regex fallback)
    - Future: Go, Rust, Java, C/C++
    """

    def __init__(self):
        """Initialize extractors for all supported languages."""
        self.extractors = {
            "python": PythonSymbolExtractor(),
            "javascript": JSSymbolExtractor(),
            "typescript": TSSymbolExtractor(),
        }

    def extract(self, file_path: Path, language: str) -> List[Symbol]:
        """
        Extract symbols using appropriate extractor.

        Args:
            file_path: Path to source file
            language: Detected language (from repository_map)

        Returns:
            List of Symbol objects

        Raises:
            ValueError: If language not supported
        """
        extractor = self.extractors.get(language)
        if not extractor:
            logger.warning(f"No extractor for {language}, skipping")
            return []

        return extractor.extract(file_path)

    def supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return list(self.extractors.keys())
```

**Integration with RepositoryMap**:
- Update `_categorize_file()` to detect JS/TS
- Call appropriate extractor based on language
- Handle multiple languages in single project

**Deliverable**: Multi-language dispatcher working

---

### Task 5: Comprehensive Tests (6 hours)
**Priority**: HIGH
**Depends on**: Task 2, 3, 4

**Test Files**:
1. `tests/intelligence/test_js_symbol_extractor.py` (20+ tests)
   - Function extraction (5 types)
   - Class extraction
   - Method extraction
   - JSDoc parsing
   - Edge cases

2. `tests/intelligence/test_ts_symbol_extractor.py` (20+ tests)
   - All JS tests
   - Type annotations
   - Interfaces
   - Type aliases
   - Enums
   - Decorators

3. `tests/intelligence/test_multi_language.py` (10+ tests)
   - Language detection
   - Extractor selection
   - Mixed projects (Python + JS + TS)
   - Fallback behavior

**Test Fixtures**:
```
tests/fixtures/
├── javascript/
│   ├── functions.js
│   ├── classes.js
│   ├── arrow.js
│   └── async.js
└── typescript/
    ├── interfaces.ts
    ├── types.ts
    ├── decorators.ts
    └── complex.ts
```

**Coverage Target**: 90%+ on all new modules

**Deliverable**: 50+ tests, 90% coverage

---

### Task 6: Documentation Updates (2 hours)
**Priority**: MEDIUM
**Depends on**: Task 5

**Updates Required**:
1. **REPOSITORY_MAP_GUIDE.md**
   - Add JS/TS examples
   - Update supported languages section
   - Add language-specific notes

2. **README.md**
   - Update "Multi-Language Support" section
   - Change "Python (complete)" to "Python, JavaScript, TypeScript (complete)"

3. **CHANGELOG.md**
   - Add Week 2 section

4. **SESSION_16_SUMMARY.md** (new)
   - Week 2 complete record

**Deliverable**: Documentation complete

---

## 📊 Progress Tracking

### Daily Goals

**Day 1** (2-3 hours):
- [ ] Task 1: JS parser setup (2h)
- Target: tree-sitter-javascript installed, AST research done

**Day 2** (6-7 hours):
- [ ] Task 2: JSSymbolExtractor (6h)
- Target: 20+ tests passing for JS extraction

**Day 3** (4-5 hours):
- [ ] Task 3: TypeScript support (4h)
- Target: 20+ tests passing for TS extraction

**Day 4** (3-4 hours):
- [ ] Task 4: Multi-language integration (3h)
- Target: Dispatcher working, 10+ tests

**Day 5** (6-7 hours):
- [ ] Task 5: Additional tests (6h)
- Target: 50+ total tests, 90% coverage

**Day 6-7** (2-3 hours):
- [ ] Task 6: Documentation (2h)
- Target: All docs updated

---

## 🎯 Success Metrics

### Quantitative Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| JS extraction accuracy | >95% | Test with real-world JS files |
| TS extraction accuracy | >95% | Test with real-world TS files |
| Tests written | 50+ | pytest count |
| Code coverage | 90%+ | pytest-cov |
| Performance | <2s for 1000 files | Benchmark |

### Qualitative Targets

- [ ] Handles all common JS patterns (functions, classes, arrows)
- [ ] Handles all common TS patterns (types, interfaces, enums)
- [ ] Graceful fallback when tree-sitter unavailable
- [ ] Clear error messages for unsupported patterns
- [ ] Documentation with examples for each language

---

## 🔧 Technical Decisions

### 1. Parser Choice: tree-sitter
**Rationale**: Consistent with Python implementation, accurate, fast

### 2. Fallback Strategy: Regex
**Rationale**: Works without dependencies, covers 80% of cases

### 3. Language Detection
**Approach**: File extension (.js, .jsx, .ts, .tsx)
**Rationale**: Simple, reliable, standard

### 4. JSDoc Support
**Priority**: HIGH (common in JavaScript)
**Extraction**: JSDoc comments → Symbol.docstring

### 5. TypeScript Complexity
**Scope Week 2**: Basic types, interfaces, classes
**Future**: Advanced types, generics, mapped types

---

## 🚨 Risks & Mitigations

### Risk 1: tree-sitter-javascript/typescript Installation Issues
**Severity**: MEDIUM
**Mitigation**: Document installation, provide troubleshooting, regex fallback

### Risk 2: JSX/TSX Complexity
**Severity**: MEDIUM
**Mitigation**: Start with .js/.ts, add .jsx/.tsx in Week 3 if time allows

### Risk 3: Performance Degradation
**Severity**: LOW
**Mitigation**: Benchmark early, optimize if needed

---

## 📚 Resources

### tree-sitter Documentation
- JavaScript: https://github.com/tree-sitter/tree-sitter-javascript
- TypeScript: https://github.com/tree-sitter/tree-sitter-typescript

### AST References
- JavaScript AST: https://astexplorer.net/ (select @babel/parser)
- TypeScript AST: https://ts-ast-viewer.com/

### Test Examples
- Week 1 Python tests: `tests/intelligence/test_symbol_extractor.py`
- Pattern: Similar structure for JS/TS

---

## 🎉 Expected Deliverables

**Code**:
- `clauxton/intelligence/symbol_extractor.py` (updated, +200 lines)
- `tests/intelligence/test_js_symbol_extractor.py` (new, 20+ tests)
- `tests/intelligence/test_ts_symbol_extractor.py` (new, 20+ tests)
- `tests/intelligence/test_multi_language.py` (new, 10+ tests)

**Documentation**:
- REPOSITORY_MAP_GUIDE.md (updated)
- README.md (updated)
- CHANGELOG.md (Week 2 section)
- SESSION_16_SUMMARY.md (new)

**Quality**:
- 50+ tests total (Week 2 only)
- 90%+ coverage on new modules
- mypy ✓, ruff ✓, pytest ✓
- Performance: <2s for 1000 JS/TS files

---

**Next Session**: Start with Task 1 (JS parser setup, 2 hours)
