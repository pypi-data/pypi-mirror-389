"""
Tests for C# symbol extraction.

Tests CSharpSymbolExtractor functionality including:
- Basic symbol extraction (classes, interfaces, methods, properties, enums, delegates, namespaces)
- C# specific features (constructors, properties, async methods, generics)
- Edge cases (empty files, unicode names)
- Error handling
- Integration with SymbolExtractor
"""
# type: ignore  # tree-sitter has complex types

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import CSharpSymbolExtractor, SymbolExtractor


class TestCSharpSymbolExtractor:
    """Test C# symbol extraction."""

    def test_init(self):
        """Test CSharpSymbolExtractor initialization."""
        extractor = CSharpSymbolExtractor()
        assert extractor.parser is not None
        assert extractor.available is True

    def test_extract_class(self, tmp_path: Path):
        """Test extracting a simple class."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""/// <summary>
/// Test class
/// </summary>
public class Test
{
    private string name;
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Test"
        assert symbols[0]["type"] == "class"
        assert symbols[0]["line_start"] == 4

    def test_extract_interface(self, tmp_path: Path):
        """Test extracting an interface."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public interface IRepository
{
    void Save();
    Task<string> LoadAsync();
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Interface + 2 methods
        assert len(symbols) >= 1
        interface = next(s for s in symbols if s["type"] == "interface")
        assert interface["name"] == "IRepository"

    def test_extract_method(self, tmp_path: Path):
        """Test extracting methods."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class Calculator
{
    public int Add(int a, int b)
    {
        return a + b;
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and method
        assert len(symbols) == 2
        class_symbol = next(s for s in symbols if s["type"] == "class")
        method_symbol = next(s for s in symbols if s["type"] == "method")

        assert class_symbol["name"] == "Calculator"
        assert method_symbol["name"] == "Add"
        assert method_symbol["signature"] is not None

    def test_extract_constructor(self, tmp_path: Path):
        """Test extracting constructor."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class User
{
    private string name;

    public User(string name)
    {
        this.name = name;
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and constructor
        assert len(symbols) == 2
        constructor = next(s for s in symbols if s["type"] == "constructor")
        assert constructor["name"] == "User"

    def test_extract_property(self, tmp_path: Path):
        """Test extracting properties."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class Person
{
    public string Name { get; set; }
    public int Age { get; private set; }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and 2 properties
        assert len(symbols) == 3
        properties = [s for s in symbols if s["type"] == "property"]
        assert len(properties) == 2
        assert properties[0]["name"] == "Name"
        assert properties[1]["name"] == "Age"

    def test_extract_enum(self, tmp_path: Path):
        """Test extracting enum."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public enum Status
{
    Ok,
    Error,
    Pending
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Status"
        assert symbols[0]["type"] == "enum"

    def test_extract_delegate(self, tmp_path: Path):
        """Test extracting delegate."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public delegate void EventHandler(object sender, EventArgs e);

public class Publisher
{
    private EventHandler handler;
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract delegate and class
        assert len(symbols) == 2
        delegate = next(s for s in symbols if s["type"] == "delegate")
        assert delegate["name"] == "EventHandler"

    def test_extract_namespace(self, tmp_path: Path):
        """Test extracting namespace."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""namespace MyApp
{
    public class User
    {
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract namespace and class
        assert len(symbols) == 2
        namespace = next(s for s in symbols if s["type"] == "namespace")
        assert namespace["name"] == "MyApp"

    def test_extract_generic_class(self, tmp_path: Path):
        """Test extracting generic class."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class Container<T>
{
    private T item;

    public T GetItem()
    {
        return item;
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and method
        assert len(symbols) == 2
        class_symbol = next(s for s in symbols if s["type"] == "class")
        assert class_symbol["name"] == "Container"

    def test_extract_async_method(self, tmp_path: Path):
        """Test extracting async method."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class Service
{
    public async Task<string> FetchDataAsync()
    {
        return await Task.FromResult("data");
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and method
        assert len(symbols) == 2
        method = next(s for s in symbols if s["type"] == "method")
        assert method["name"] == "FetchDataAsync"
        assert "async" in method["signature"].lower()

    def test_extract_static_method(self, tmp_path: Path):
        """Test extracting static method."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public static class Helper
{
    public static int Add(int a, int b)
    {
        return a + b;
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and method
        assert len(symbols) == 2
        method = next(s for s in symbols if s["type"] == "method")
        assert method["name"] == "Add"
        assert "static" in method["signature"]

    def test_extract_multiple_symbols(self, tmp_path: Path):
        """Test extracting multiple symbols from one file."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""namespace MyApp
{
    public class User
    {
        public string Name { get; set; }

        public void UpdateName(string newName)
        {
            Name = newName;
        }
    }

    public interface IUser
    {
        string GetName();
    }

    public enum Role
    {
        Admin,
        User
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # namespace, class, property, method, interface (+interface methods), enum
        assert len(symbols) >= 6

        types = {s["type"] for s in symbols}
        assert "namespace" in types
        assert "class" in types
        assert "property" in types
        assert "method" in types
        assert "interface" in types
        assert "enum" in types

    def test_extract_empty_file(self, tmp_path: Path):
        """Test extracting from empty file."""
        cs_file = tmp_path / "empty.cs"
        cs_file.write_text("")

        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        assert len(symbols) == 0

    def test_extract_comments_only(self, tmp_path: Path):
        """Test extracting from file with only comments."""
        cs_file = tmp_path / "comments.cs"
        cs_file.write_text("""// Just comments
/* Block comment */
/// XML comment
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        assert len(symbols) == 0

    def test_extract_with_unicode(self, tmp_path: Path):
        """Test extracting symbols with unicode names."""
        cs_file = tmp_path / "unicode.cs"
        cs_file.write_text("""public class ユーザー
{
    public string 名前を取得()
    {
        return "名前";
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        assert len(symbols) == 2
        class_symbol = next(s for s in symbols if s["type"] == "class")
        assert class_symbol["name"] == "ユーザー"
        method_symbol = next(s for s in symbols if s["type"] == "method")
        assert method_symbol["name"] == "名前を取得"

    def test_extract_file_not_found(self):
        """Test extracting from non-existent file."""
        extractor = CSharpSymbolExtractor()
        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/file.cs"))

    def test_extract_when_parser_unavailable(self, tmp_path: Path, monkeypatch):
        """Test extraction when parser is unavailable."""
        cs_file = tmp_path / "test.cs"
        cs_file.write_text("""public class Test
{
}
""")

        extractor = CSharpSymbolExtractor()
        # Simulate parser unavailability
        extractor.available = False

        symbols = extractor.extract(cs_file)
        assert len(symbols) == 0

    def test_integration_with_symbol_extractor(self, tmp_path: Path):
        """Test CSharpSymbolExtractor integration with SymbolExtractor."""
        cs_file = tmp_path / "test.cs"
        cs_file.write_text("""public class Test
{
    public void Method()
    {
    }
}
""")

        symbol_extractor = SymbolExtractor()
        assert "csharp" in symbol_extractor.extractors

        symbols = symbol_extractor.extract(cs_file, "csharp")
        assert len(symbols) == 2  # class + method

    def test_fixture_sample_cs(self):
        """Test extraction from sample.cs fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "csharp" / "sample.cs"
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Verify we extract a good number of symbols from the sample file
        assert len(symbols) > 5

        # Check for expected symbol types
        types = {s["type"] for s in symbols}
        assert "class" in types
        assert "interface" in types
        assert "enum" in types
        assert "namespace" in types

    def test_fixture_empty_cs(self):
        """Test extraction from empty.cs fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "csharp" / "empty.cs"
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        assert len(symbols) == 0

    def test_fixture_unicode_cs(self):
        """Test extraction from unicode.cs fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "csharp" / "unicode.cs"
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract namespace and classes with unicode names
        assert len(symbols) > 0

        # Verify unicode names are preserved
        names = {s["name"] for s in symbols}
        assert "ユーザー" in names or "😀Emoji" in names

    def test_qualified_namespace(self, tmp_path: Path):
        """Test extracting qualified namespace (e.g., MyApp.Utils)."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""namespace MyApp.Utils
{
    public static class Helper
    {
        public static int Multiply(int a, int b)
        {
            return a * b;
        }
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract namespace, class, and method
        assert len(symbols) == 3
        namespace = next(s for s in symbols if s["type"] == "namespace")
        assert namespace["name"] == "MyApp.Utils"

    def test_line_numbers(self, tmp_path: Path):
        """Test that line numbers are correctly extracted."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""// Line 1
namespace MyApp  // Line 2
{  // Line 3
    public class User  // Line 4
    {  // Line 5
        public string Name { get; set; }  // Line 6
    }  // Line 7
}  // Line 8
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        namespace = next(s for s in symbols if s["type"] == "namespace")
        class_symbol = next(s for s in symbols if s["type"] == "class")
        property_symbol = next(s for s in symbols if s["type"] == "property")

        assert namespace["line_start"] == 2
        assert class_symbol["line_start"] == 4
        assert property_symbol["line_start"] == 6

    def test_nested_class(self, tmp_path: Path):
        """Test extracting nested class."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class Outer
{
    public class Inner
    {
        public void Method()
        {
        }
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract outer class, inner class, and method
        assert len(symbols) == 3
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 2
        assert "Outer" in [c["name"] for c in classes]
        assert "Inner" in [c["name"] for c in classes]

    def test_abstract_class(self, tmp_path: Path):
        """Test extracting abstract class."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public abstract class Shape
{
    public abstract double GetArea();

    public void Display()
    {
        Console.WriteLine("Shape");
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        # Should extract class and methods
        assert len(symbols) >= 1
        class_symbol = next(s for s in symbols if s["type"] == "class")
        assert class_symbol["name"] == "Shape"

    def test_multiple_classes(self, tmp_path: Path):
        """Test extracting multiple classes from one file."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class First
{
    public void Method1() { }
}

public class Second
{
    public void Method2() { }
}

public class Third
{
    public void Method3() { }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 3
        class_names = {c["name"] for c in classes}
        assert class_names == {"First", "Second", "Third"}

    def test_inheritance(self, tmp_path: Path):
        """Test extracting class with inheritance."""
        cs_file = tmp_path / "Test.cs"
        cs_file.write_text("""public class Animal
{
    public virtual void MakeSound() { }
}

public class Dog : Animal
{
    public override void MakeSound()
    {
        Console.WriteLine("Woof");
    }
}
""")
        extractor = CSharpSymbolExtractor()
        symbols = extractor.extract(cs_file)

        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 2
        class_names = {c["name"] for c in classes}
        assert "Animal" in class_names
        assert "Dog" in class_names
