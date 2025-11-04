"""
Tests for Java symbol extraction.

Tests JavaSymbolExtractor functionality including:
- Basic symbol extraction (classes, interfaces, methods, enums, annotations)
- Java specific features (constructors, generics, annotations)
- Edge cases (empty files, unicode names)
- Error handling
- Integration with SymbolExtractor
"""
# type: ignore  # tree-sitter has complex types

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import JavaSymbolExtractor, SymbolExtractor


class TestJavaSymbolExtractor:
    """Test Java symbol extraction."""

    def test_init(self):
        """Test JavaSymbolExtractor initialization."""
        extractor = JavaSymbolExtractor()
        assert extractor.parser is not None
        assert extractor.available is True

    def test_extract_class(self, tmp_path: Path):
        """Test extracting a simple class."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""/**
 * Test class
 */
public class Test {
    private String name;
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Test"
        assert symbols[0]["type"] == "class"
        assert symbols[0]["line_start"] == 4

    def test_extract_interface(self, tmp_path: Path):
        """Test extracting an interface."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public interface Repository {
    void save(Object obj);
    Object find(int id);
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract interface and methods
        assert len(symbols) >= 1
        interface_sym = next(s for s in symbols if s["type"] == "interface")
        assert interface_sym["name"] == "Repository"

    def test_extract_method(self, tmp_path: Path):
        """Test extracting methods."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Test {
    public int add(int a, int b) {
        return a + b;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract class and method
        assert len(symbols) >= 2
        method_sym = next(s for s in symbols if s["type"] == "method")
        assert method_sym["name"] == "add"

    def test_extract_constructor(self, tmp_path: Path):
        """Test extracting constructors."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class User {
    private String name;

    public User(String name) {
        this.name = name;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract class and constructor
        assert len(symbols) >= 2
        constructor_sym = next((s for s in symbols if s["type"] == "constructor"), None)
        assert constructor_sym is not None
        assert constructor_sym["name"] == "User"

    def test_extract_enum(self, tmp_path: Path):
        """Test extracting enums."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public enum Status {
    ACTIVE,
    INACTIVE,
    SUSPENDED
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Status"
        assert symbols[0]["type"] == "enum"

    def test_extract_annotation(self, tmp_path: Path):
        """Test extracting annotation types."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public @interface MyAnnotation {
    String value();
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) >= 1
        annotation_sym = next((s for s in symbols if s["type"] == "annotation"), None)
        assert annotation_sym is not None
        assert annotation_sym["name"] == "MyAnnotation"

    def test_extract_generic_class(self, tmp_path: Path):
        """Test extracting generic classes."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Container<T> {
    private T item;

    public T getItem() {
        return item;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract class and method
        assert len(symbols) >= 2
        class_sym = next(s for s in symbols if s["type"] == "class")
        assert class_sym["name"] == "Container"

    def test_extract_multiple_classes(self, tmp_path: Path):
        """Test extracting multiple classes."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class First {}
class Second {}
class Third {}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 3
        names = {s["name"] for s in symbols}
        assert names == {"First", "Second", "Third"}

    def test_extract_empty_file(self, tmp_path: Path):
        """Test extracting from empty file."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("")

        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 0

    def test_extract_comments_only(self, tmp_path: Path):
        """Test extracting from file with only comments."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""// This is a comment
/* Another comment */
""")

        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 0

    def test_extract_with_unicode(self, tmp_path: Path):
        """Test extracting symbols with unicode names."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class 使用者 {
    public void こんにちは() {
        // Hello
    }
}
""")

        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) >= 1
        # Unicode should be preserved
        class_sym = next(s for s in symbols if s["type"] == "class")
        assert "使用者" in class_sym["name"]

    def test_extract_file_not_found(self):
        """Test extract raises FileNotFoundError for non-existent file."""
        extractor = JavaSymbolExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/File.java"))

    def test_extract_when_parser_unavailable(self, tmp_path: Path):
        """Test extract returns empty list when parser unavailable."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("public class Test { }")

        extractor = JavaSymbolExtractor()
        extractor.available = False

        symbols = extractor.extract(java_file)
        assert len(symbols) == 0

    def test_integration_with_symbol_extractor(self, tmp_path: Path):
        """Test integration with main SymbolExtractor."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Test {
    public int add(int a, int b) {
        return a + b;
    }
}
""")

        dispatcher = SymbolExtractor()
        symbols = dispatcher.extract(java_file, "java")

        assert len(symbols) >= 1
        class_sym = next(s for s in symbols if s["type"] == "class")
        assert class_sym["name"] == "Test"

    def test_fixture_sample_java(self):
        """Test extraction from sample.java fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "java" / "sample.java"
        if not fixture_path.exists():
            pytest.skip("sample.java fixture not found")

        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract: User class, UserRepository interface, Status enum, Container class
        assert len(symbols) >= 4

        names = {s["name"] for s in symbols}
        assert "User" in names
        assert "UserRepository" in names
        assert "Status" in names
        assert "Container" in names

    def test_fixture_empty_java(self):
        """Test extraction from empty.java fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "java" / "empty.java"
        if not fixture_path.exists():
            pytest.skip("empty.java fixture not found")

        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        assert len(symbols) == 0

    def test_fixture_unicode_java(self):
        """Test extraction from unicode.java fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "java" / "unicode.java"
        if not fixture_path.exists():
            pytest.skip("unicode.java fixture not found")

        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract Unicode class
        assert len(symbols) >= 1

    def test_abstract_class(self, tmp_path: Path):
        """Test extracting abstract classes."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public abstract class Shape {
    abstract double area();
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) >= 1
        class_sym = next(s for s in symbols if s["type"] == "class")
        assert class_sym["name"] == "Shape"

    def test_static_method(self, tmp_path: Path):
        """Test extracting static methods."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Utils {
    public static int square(int x) {
        return x * x;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract class and static method
        assert len(symbols) >= 2
        method_sym = next((s for s in symbols if s["type"] == "method"), None)
        assert method_sym is not None

    def test_overloaded_methods(self, tmp_path: Path):
        """Test extracting overloaded methods."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public double add(double a, double b) {
        return a + b;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract class and both methods
        assert len(symbols) >= 3
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 2
        assert all(m["name"] == "add" for m in methods)

    def test_nested_class(self, tmp_path: Path):
        """Test extracting nested classes."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Outer {
    public class Inner {
        private int value;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract both outer and inner classes
        assert len(symbols) >= 2
        names = {s["name"] for s in symbols}
        assert "Outer" in names
        assert "Inner" in names

    def test_interface_with_default_method(self, tmp_path: Path):
        """Test extracting interface with default methods (Java 8+)."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public interface Service {
    void execute();

    default void log() {
        System.out.println("Logging");
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract interface and methods
        assert len(symbols) >= 1
        interface_sym = next(s for s in symbols if s["type"] == "interface")
        assert interface_sym["name"] == "Service"

    def test_method_with_signature(self, tmp_path: Path):
        """Test that method signature is extracted."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Test {
    public int compute(int x, int y) {
        return x + y;
    }
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        method_sym = next((s for s in symbols if s["type"] == "method"), None)
        assert method_sym is not None
        assert method_sym["signature"] is not None
        assert "compute" in method_sym["signature"]

    def test_line_numbers(self, tmp_path: Path):
        """Test that line numbers are correctly extracted."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""// Line 1
public class First {
    // Line 3
}
// Line 5
public class Second {
    // Line 7
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 2
        first_sym = next(s for s in symbols if s["name"] == "First")
        assert first_sym["line_start"] == 2
        second_sym = next(s for s in symbols if s["name"] == "Second")
        assert second_sym["line_start"] == 6

    def test_inheritance(self, tmp_path: Path):
        """Test extracting classes with inheritance."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public class Base {}
public class Derived extends Base {}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        assert len(symbols) == 2
        names = {s["name"] for s in symbols}
        assert "Base" in names
        assert "Derived" in names

    def test_interface_implementation(self, tmp_path: Path):
        """Test extracting classes implementing interfaces."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public interface Runnable {
    void run();
}

public class Task implements Runnable {
    public void run() {}
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract interface, class, and methods
        assert len(symbols) >= 2
        names = {s["name"] for s in symbols}
        assert "Runnable" in names
        assert "Task" in names

    def test_multiple_interfaces(self, tmp_path: Path):
        """Test extracting class implementing multiple interfaces."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""public interface Readable {
    void read();
}

public interface Writable {
    void write();
}

public class File implements Readable, Writable {
    public void read() {}
    public void write() {}
}
""")
        extractor = JavaSymbolExtractor()
        symbols = extractor.extract(java_file)

        # Should extract 2 interfaces, 1 class, and methods
        assert len(symbols) >= 3
        names = {s["name"] for s in symbols}
        assert "Readable" in names
        assert "Writable" in names
        assert "File" in names
