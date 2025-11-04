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

    def test_class_with_methods(self, tmp_path: Path):
        """Test extracting class with constructor and destructor."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class MyClass {
public:
    MyClass() {}
    ~MyClass() {}
    void method() {}
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract class and possibly methods
        assert len(symbols) >= 1
        class_sym = next((s for s in symbols if s["type"] == "class"), None)
        assert class_sym is not None
        assert class_sym["name"] == "MyClass"

    def test_namespace_with_function(self, tmp_path: Path):
        """Test extracting namespace containing function."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""namespace math {
    int square(int x) {
        return x * x;
    }
}
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract namespace and function
        assert len(symbols) >= 2
        namespace_sym = next((s for s in symbols if s["type"] == "namespace"), None)
        function_sym = next((s for s in symbols if s["type"] == "function"), None)
        assert namespace_sym is not None
        assert function_sym is not None
        assert namespace_sym["name"] == "math"
        assert function_sym["name"] == "square"

    def test_multiple_classes(self, tmp_path: Path):
        """Test extracting multiple classes."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class First {};
class Second {};
class Third {};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 3
        names = {s["name"] for s in symbols}
        assert names == {"First", "Second", "Third"}

    def test_mixed_symbols(self, tmp_path: Path):
        """Test extracting mixed types of symbols."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class MyClass {};
struct MyStruct {};
namespace MyNamespace {}
int myFunction() { return 0; }
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 4
        types = {s["type"] for s in symbols}
        assert types == {"class", "struct", "namespace", "function"}

    def test_function_with_signature(self, tmp_path: Path):
        """Test that function signature is extracted."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""int compute(int x, int y) {
    return x + y;
}
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 1
        assert symbols[0]["signature"] is not None
        assert "compute" in symbols[0]["signature"]

    def test_line_numbers(self, tmp_path: Path):
        """Test that line numbers are correctly extracted."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""// Line 1
int first() { return 1; }
// Line 3
int second() { return 2; }
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        assert len(symbols) == 2
        # First function should start at line 2
        first_sym = next(s for s in symbols if s["name"] == "first")
        assert first_sym["line_start"] == 2
        # Second function should start at line 4
        second_sym = next(s for s in symbols if s["name"] == "second")
        assert second_sym["line_start"] == 4

    def test_complex_class(self, tmp_path: Path):
        """Test extracting complex class with inheritance."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class Base {};
class Derived : public Base {
public:
    Derived() {}
    virtual ~Derived() {}
    virtual void method() = 0;
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract Base and Derived classes
        assert len(symbols) >= 2
        names = {s["name"] for s in symbols}
        assert "Base" in names
        assert "Derived" in names

    def test_const_method(self, tmp_path: Path):
        """Test extracting const methods."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class Calculator {
public:
    int getValue() const {
        return value_;
    }
private:
    int value_;
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract Calculator class
        assert len(symbols) >= 1
        class_sym = next((s for s in symbols if s["type"] == "class"), None)
        assert class_sym is not None
        assert class_sym["name"] == "Calculator"

    def test_static_method(self, tmp_path: Path):
        """Test extracting static methods."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class Factory {
public:
    static Factory* create() {
        return new Factory();
    }
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract Factory class
        assert len(symbols) >= 1
        class_sym = next((s for s in symbols if s["type"] == "class"), None)
        assert class_sym is not None

    def test_virtual_method(self, tmp_path: Path):
        """Test extracting virtual methods."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class Shape {
public:
    virtual double area() = 0;
    virtual ~Shape() {}
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract Shape class
        assert len(symbols) >= 1
        class_sym = next((s for s in symbols if s["type"] == "class"), None)
        assert class_sym is not None
        assert class_sym["name"] == "Shape"

    def test_nested_namespace(self, tmp_path: Path):
        """Test extracting nested namespaces."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""namespace outer {
    namespace inner {
        void func() {}
    }
}
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract both namespaces
        assert len(symbols) >= 2
        namespace_symbols = [s for s in symbols if s["type"] == "namespace"]
        assert len(namespace_symbols) >= 2

    def test_template_class(self, tmp_path: Path):
        """Test extracting template classes."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""template<typename T>
class Container {
public:
    void add(T item) {}
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract Container class
        assert len(symbols) >= 1
        class_sym = next((s for s in symbols if s["type"] == "class"), None)
        assert class_sym is not None
        assert class_sym["name"] == "Container"

    def test_operator_overload(self, tmp_path: Path):
        """Test extracting operator overloading."""
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text("""class Vector {
public:
    Vector operator+(const Vector& other) {
        return Vector();
    }
};
""")
        extractor = CppSymbolExtractor()
        symbols = extractor.extract(cpp_file)

        # Should extract Vector class
        assert len(symbols) >= 1
        class_sym = next((s for s in symbols if s["type"] == "class"), None)
        assert class_sym is not None
        assert class_sym["name"] == "Vector"
