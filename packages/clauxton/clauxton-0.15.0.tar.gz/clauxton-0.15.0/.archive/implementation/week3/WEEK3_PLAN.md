# Week 3 Implementation Plan: C++, Java, C# Support

**Version**: 1.0
**Created**: 2025-10-24
**Status**: 📋 Planning
**Branch**: `feature/v0.11.0-repository-map`
**Duration**: 3-4 days (6-8 hours)

---

## 📊 Current Status (Week 2 Complete)

### ✅ Completed Features
- **5 Languages Supported**: Python, JavaScript, TypeScript, Go, Rust
- **205 Intelligence Tests**: 100% passing
- **92% Coverage**: All modules above 90%
- **Quality**: mypy ✓, ruff ✓, pytest ✓

### 📈 Progress
```
Week 1: Python symbol extraction (81 tests)
Week 2: JS/TS/Go/Rust support (+124 tests → 205 total)
Week 3: C++/Java/C# support (target: +60 tests → 265 total)
```

---

## 🎯 Week 3 Goals

### Primary Objectives
1. ✅ Add C++ language support (Day 5)
2. ✅ Add Java language support (Day 6)
3. ✅ Add C# language support (Day 7)
4. ✅ Maintain 90%+ coverage
5. ✅ Update all documentation

### Success Criteria
- **Tests**: 265+ total (205 + 60 new)
- **Coverage**: 90%+ for new code
- **Quality**: mypy ✓, ruff ✓, all tests passing
- **Documentation**: Complete and accurate

---

## 📅 Day-by-Day Plan

### Day 5: C++ Language Support

**Duration**: 2-3 hours
**Target**: 20+ tests, 90%+ coverage

#### Implementation Tasks
1. **Install dependency**:
   ```bash
   pip install tree-sitter-cpp
   ```
   - Add to `pyproject.toml`: `tree-sitter-cpp>=0.20`

2. **Create CppParser** (`parser.py`):
   ```python
   class CppParser(BaseParser):
       """C++ parser using tree-sitter."""
       def __init__(self) -> None:
           import tree_sitter_cpp as tscpp
           super().__init__(tscpp)
   ```

3. **Create CppSymbolExtractor** (`symbol_extractor.py`):
   - **Functions**: `int add(int a, int b)`
   - **Methods**: `void MyClass::method()`
   - **Classes**: `class MyClass { ... }`
   - **Structs**: `struct Point { ... }`
   - **Namespaces**: `namespace utils { ... }`
   - **Templates**: `template<typename T> T max(T a, T b)`
   - **Constructors/Destructors**: `MyClass()`, `~MyClass()`

4. **Test Implementation** (`test_cpp_extractor.py`):
   - Initialization (1 test)
   - Basic extraction (8 tests): function, method, class, struct, namespace, template, constructor, destructor
   - Multiple symbols (1 test)
   - C++ features (3 tests): operator overload, virtual methods, static members
   - Edge cases (4 tests): empty file, comments, Unicode, headers
   - Error handling (2 tests): file not found, parser unavailable
   - Integration (1 test)
   - Fixtures (3 tests): sample.cpp, empty.cpp, unicode.cpp

5. **Test Fixtures**:
   - `tests/fixtures/cpp/sample.cpp`: Comprehensive example (10+ symbols)
   - `tests/fixtures/cpp/empty.cpp`: Empty file
   - `tests/fixtures/cpp/unicode.cpp`: Unicode names

6. **Update Integration**:
   - Add `"cpp": CppSymbolExtractor()` to `SymbolExtractor`
   - Update `test_dispatcher_has_all_languages` test
   - Update parser tests (4 CppParser tests)

#### C++ Symbol Types to Extract

```cpp
// 1. Functions
int add(int a, int b) { return a + b; }
→ {"name": "add", "type": "function", "signature": "int add(int a, int b)"}

// 2. Classes
class User {
public:
    User(std::string name);
    ~User();
    void setName(std::string name);
private:
    std::string name_;
};
→ {"name": "User", "type": "class"}

// 3. Methods
void User::setName(std::string name) { name_ = name; }
→ {"name": "setName", "type": "method", "class": "User"}

// 4. Structs
struct Point {
    int x, y;
};
→ {"name": "Point", "type": "struct"}

// 5. Namespaces
namespace utils {
    int helper() { return 42; }
}
→ {"name": "utils", "type": "namespace"}

// 6. Templates
template<typename T>
T max(T a, T b) { return a > b ? a : b; }
→ {"name": "max", "type": "function", "signature": "template<typename T> T max(T a, T b)"}

// 7. Constructors/Destructors
User::User(std::string name) : name_(name) {}
User::~User() {}
→ {"name": "User", "type": "constructor"}
→ {"name": "~User", "type": "destructor"}
```

#### Expected Test Count
- **CppParser tests**: 4
- **CppSymbolExtractor tests**: 20+
- **Total new tests**: 24+
- **Running total**: 229+ (205 + 24)

---

### Day 6: Java Language Support

**Duration**: 2-3 hours
**Target**: 20+ tests, 90%+ coverage

#### Implementation Tasks
1. **Install dependency**:
   ```bash
   pip install tree-sitter-java
   ```
   - Add to `pyproject.toml`: `tree-sitter-java>=0.20`

2. **Create JavaParser** (`parser.py`):
   ```python
   class JavaParser(BaseParser):
       """Java parser using tree-sitter."""
       def __init__(self) -> None:
           import tree_sitter_java as tsjava
           super().__init__(tsjava)
   ```

3. **Create JavaSymbolExtractor** (`symbol_extractor.py`):
   - **Classes**: `public class User { ... }`
   - **Methods**: `public void doSomething()`
   - **Interfaces**: `public interface Runnable { ... }`
   - **Enums**: `public enum Status { OK, ERROR }`
   - **Annotations**: `@Override`, `@Deprecated`
   - **Constructors**: `public User() { ... }`
   - **Static members**: `public static void main(String[] args)`

4. **Test Implementation** (`test_java_extractor.py`):
   - Initialization (1 test)
   - Basic extraction (8 tests): class, method, interface, enum, constructor, static method, annotation, package
   - Multiple symbols (1 test)
   - Java features (3 tests): generics, inheritance, inner classes
   - Edge cases (4 tests): empty file, comments, Unicode, imports
   - Error handling (2 tests): file not found, parser unavailable
   - Integration (1 test)
   - Fixtures (3 tests): sample.java, empty.java, unicode.java

5. **Test Fixtures**:
   - `tests/fixtures/java/sample.java`: Comprehensive example (10+ symbols)
   - `tests/fixtures/java/empty.java`: Empty file
   - `tests/fixtures/java/unicode.java`: Unicode names

6. **Update Integration**:
   - Add `"java": JavaSymbolExtractor()` to `SymbolExtractor`
   - Update dispatcher tests
   - Update parser tests (4 JavaParser tests)

#### Java Symbol Types to Extract

```java
// 1. Classes
public class User {
    private String name;

    public User(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }
}
→ {"name": "User", "type": "class"}

// 2. Methods
public String getName() { return name; }
→ {"name": "getName", "type": "method", "modifiers": ["public"]}

// 3. Interfaces
public interface Runnable {
    void run();
}
→ {"name": "Runnable", "type": "interface"}

// 4. Enums
public enum Status {
    OK,
    ERROR,
    PENDING
}
→ {"name": "Status", "type": "enum"}

// 5. Constructors
public User(String name) { this.name = name; }
→ {"name": "User", "type": "constructor"}

// 6. Static Methods
public static void main(String[] args) { }
→ {"name": "main", "type": "method", "modifiers": ["public", "static"]}

// 7. Generics
public class List<T> { ... }
→ {"name": "List", "type": "class", "generics": "<T>"}
```

#### Expected Test Count
- **JavaParser tests**: 4
- **JavaSymbolExtractor tests**: 20+
- **Total new tests**: 24+
- **Running total**: 253+ (229 + 24)

---

### Day 7: C# Language Support

**Duration**: 2-3 hours
**Target**: 20+ tests, 90%+ coverage

#### Implementation Tasks
1. **Install dependency**:
   ```bash
   pip install tree-sitter-c-sharp
   ```
   - Add to `pyproject.toml`: `tree-sitter-c-sharp>=0.20`

2. **Create CSharpParser** (`parser.py`):
   ```python
   class CSharpParser(BaseParser):
       """C# parser using tree-sitter."""
       def __init__(self) -> None:
           import tree_sitter_c_sharp as tscsharp
           super().__init__(tscsharp)
   ```

3. **Create CSharpSymbolExtractor** (`symbol_extractor.py`):
   - **Classes**: `public class User { ... }`
   - **Methods**: `public void DoSomething()`
   - **Properties**: `public string Name { get; set; }`
   - **Interfaces**: `public interface IRunnable { ... }`
   - **Enums**: `public enum Status { Ok, Error }`
   - **Delegates**: `public delegate void Handler()`
   - **Namespaces**: `namespace MyApp { ... }`

4. **Test Implementation** (`test_csharp_extractor.py`):
   - Initialization (1 test)
   - Basic extraction (8 tests): class, method, property, interface, enum, delegate, namespace, constructor
   - Multiple symbols (1 test)
   - C# features (3 tests): async/await, LINQ, attributes
   - Edge cases (4 tests): empty file, comments, Unicode, using statements
   - Error handling (2 tests): file not found, parser unavailable
   - Integration (1 test)
   - Fixtures (3 tests): sample.cs, empty.cs, unicode.cs

5. **Test Fixtures**:
   - `tests/fixtures/csharp/sample.cs`: Comprehensive example (10+ symbols)
   - `tests/fixtures/csharp/empty.cs`: Empty file
   - `tests/fixtures/csharp/unicode.cs`: Unicode names

6. **Update Integration**:
   - Add `"csharp": CSharpSymbolExtractor()` to `SymbolExtractor`
   - Update dispatcher tests
   - Update parser tests (4 CSharpParser tests)

#### C# Symbol Types to Extract

```csharp
// 1. Classes
public class User
{
    private string name;

    public User(string name)
    {
        this.name = name;
    }

    public string GetName()
    {
        return name;
    }
}
→ {"name": "User", "type": "class"}

// 2. Methods
public string GetName() { return name; }
→ {"name": "GetName", "type": "method", "modifiers": ["public"]}

// 3. Properties
public string Name { get; set; }
→ {"name": "Name", "type": "property"}

// 4. Interfaces
public interface IRunnable
{
    void Run();
}
→ {"name": "IRunnable", "type": "interface"}

// 5. Enums
public enum Status
{
    Ok,
    Error,
    Pending
}
→ {"name": "Status", "type": "enum"}

// 6. Delegates
public delegate void Handler(object sender, EventArgs e);
→ {"name": "Handler", "type": "delegate"}

// 7. Async Methods
public async Task<string> FetchDataAsync()
{
    return await Task.FromResult("data");
}
→ {"name": "FetchDataAsync", "type": "method", "async": true}
```

#### Expected Test Count
- **CSharpParser tests**: 4
- **CSharpSymbolExtractor tests**: 20+
- **Total new tests**: 24+
- **Running total**: 277+ (253 + 24)

---

## 📊 Week 3 Expected Outcomes

### Test Statistics
```
Starting:     205 tests (Week 2 complete)
Day 5 (C++):  +24 tests → 229 tests
Day 6 (Java): +24 tests → 253 tests
Day 7 (C#):   +24 tests → 277 tests

Target:       265+ tests
Expected:     277 tests (105% of target)
```

### Language Support Matrix
| Language | Parser | Extractor | Tests | Status |
|----------|--------|-----------|-------|--------|
| Python | ✅ | ✅ | 13 | Complete (Week 1) |
| JavaScript | ✅ | ✅ | 23 | Complete (Week 2 Day 1) |
| TypeScript | ✅ | ✅ | 24 | Complete (Week 2 Day 2) |
| Go | ✅ | ✅ | 22 | Complete (Week 2 Day 3) |
| Rust | ✅ | ✅ | 29 | Complete (Week 2 Day 4) |
| **C++** | 📋 | 📋 | 24 | **Week 3 Day 5** |
| **Java** | 📋 | 📋 | 24 | **Week 3 Day 6** |
| **C#** | 📋 | 📋 | 24 | **Week 3 Day 7** |

### Coverage Goals
- **Intelligence Module**: Maintain 90%+ coverage
- **parser.py**: Target 85%+
- **symbol_extractor.py**: Target 90%+
- **All new code**: 90%+ coverage

---

## 🔧 Implementation Guidelines

### Code Style
1. **Follow existing patterns**: Use Week 2 implementations as templates
2. **Consistent naming**: `CppParser`, `JavaParser`, `CSharpParser`
3. **Type hints**: Full type annotations for all functions
4. **Docstrings**: Google style for all classes and methods
5. **Error handling**: Graceful fallback when parser unavailable

### Testing Strategy
1. **Start with fixtures**: Create test files first
2. **Test-driven**: Write tests before implementation
3. **Coverage first**: Aim for 90%+ from the start
4. **Edge cases**: Empty files, syntax errors, Unicode
5. **Integration**: Verify dispatcher hookup

### Documentation Updates
After each day, update:
1. **REPOSITORY_MAP_GUIDE.md**: Add language to supported list
2. **README.md**: Mark language as complete
3. **CHANGELOG.md**: Add to Week 3 section
4. **CLAUDE.md**: Update progress
5. **WEEKX_DAYX_COMPLETION.md**: Create daily report

---

## 📋 Daily Checklist Template

### Pre-Implementation
- [ ] Install tree-sitter dependency
- [ ] Add to pyproject.toml
- [ ] Create test fixtures directory
- [ ] Review tree-sitter documentation

### Implementation
- [ ] Create Parser class
- [ ] Create SymbolExtractor class
- [ ] Implement symbol extraction logic
- [ ] Add to SymbolExtractor dispatcher
- [ ] Update imports in test files

### Testing
- [ ] Write parser tests (4 tests)
- [ ] Write extractor tests (20+ tests)
- [ ] Create 3 test fixtures
- [ ] Update integration tests
- [ ] Run full test suite
- [ ] Verify 90%+ coverage

### Quality Checks
- [ ] Run mypy (no errors)
- [ ] Run ruff (no warnings)
- [ ] All tests passing
- [ ] Coverage report reviewed

### Documentation
- [ ] Update REPOSITORY_MAP_GUIDE.md
- [ ] Update README.md
- [ ] Update CHANGELOG.md
- [ ] Update CLAUDE.md
- [ ] Create completion report

---

## 🎯 Success Metrics

### Minimum Requirements (Must Have)
- ✅ 265+ total tests (205 + 60 new)
- ✅ 90%+ coverage for new code
- ✅ mypy: 0 errors
- ✅ ruff: 0 warnings
- ✅ All tests passing
- ✅ 8 languages supported (Python, JS, TS, Go, Rust, C++, Java, C#)

### Stretch Goals (Nice to Have)
- ✅ 277+ tests (105% of target)
- ✅ 92%+ coverage (match Week 2)
- ✅ Advanced features: operator overloading (C++), annotations (Java), async/await (C#)
- ✅ Performance: <3 seconds for all tests

---

## ⚠️ Known Challenges

### C++ Specific
- **Complex templates**: Nested templates may be difficult to parse
- **Preprocessor directives**: #include, #define may need special handling
- **Multiple translation units**: Header files vs implementation

**Mitigation**: Start with basic cases, add complexity incrementally

### Java Specific
- **Inner classes**: Nested class definitions
- **Anonymous classes**: May need special handling
- **Annotations**: Complex annotation syntax

**Mitigation**: Focus on common patterns first, add edge cases later

### C# Specific
- **Properties**: Different from methods, need special extraction
- **Events**: May need separate handling
- **LINQ syntax**: Query expressions may be complex

**Mitigation**: Start with classes/methods/properties, add advanced features incrementally

---

## 📚 References

### Tree-Sitter Documentation
- [tree-sitter-cpp](https://github.com/tree-sitter/tree-sitter-cpp)
- [tree-sitter-java](https://github.com/tree-sitter/tree-sitter-java)
- [tree-sitter-c-sharp](https://github.com/tree-sitter/tree-sitter-c-sharp)

### Week 2 Templates
- Use `test_rust_extractor.py` as template (29 tests, most comprehensive)
- Use `RustSymbolExtractor` as code template
- Follow `WEEK2_DAY4_COMPLETION.md` report structure

---

## 🚀 Post-Week 3 Plan

After completing Week 3, the roadmap continues:

### Week 4-5: Additional Enhancements
- CLI/MCP integration improvements
- Performance optimization
- Incremental indexing

### Week 6: Final Polish
- Documentation review
- Performance benchmarks
- Release preparation

### v0.11.0 Release Target
- **8 languages**: Python, JavaScript, TypeScript, Go, Rust, C++, Java, C#
- **270+ tests**: Comprehensive coverage
- **90%+ coverage**: High quality code
- **Complete docs**: User-ready documentation

---

## 📝 Notes

### From Week 2 Review
- Rust implementation took 2 hours (efficient due to learnings)
- 29 tests achieved (145% of target) - set high bar for Week 3
- Documentation updates crucial - don't forget!
- 6 advanced tests added in review - plan for this in Week 3

### Best Practices Learned
1. **Start with tree-sitter exploration**: Understand AST structure first
2. **Create fixtures early**: Helps guide implementation
3. **Test incrementally**: Don't wait until end
4. **Document as you go**: Easier than batch updates
5. **Review coverage frequently**: Catch gaps early

---

**Plan Version**: 1.0
**Created**: 2025-10-24
**Author**: Claude Code Assistant
**Status**: Ready for Week 3 Day 5 (C++) 🚀
