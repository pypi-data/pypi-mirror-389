"""
Tests for language parsers.

Tests BaseParser, PythonParser, JavaScript Parser, TypeScriptParser,
GoParser, RustParser, CppParser, JavaParser, CSharpParser, PhpParser, RubyParser, and SwiftParser.
"""

from pathlib import Path

import pytest

from clauxton.intelligence.parser import (
    CppParser,
    CSharpParser,
    GoParser,
    JavaParser,
    JavaScriptParser,
    PhpParser,
    PythonParser,
    RubyParser,
    RustParser,
    SwiftParser,
    TypeScriptParser,
)


class TestPythonParser:
    """Test PythonParser class."""

    def test_init(self):
        """Test PythonParser initialization."""
        parser = PythonParser()
        assert parser.available in [True, False]
        assert parser.parser is not None or not parser.available

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Python file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def hello():
    print("Hello, World!")
""")

        parser = PythonParser()
        if not parser.available:
            pytest.skip("tree-sitter-python not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = PythonParser()
        if not parser.available:
            pytest.skip("tree-sitter-python not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.py"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        parser = PythonParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


class TestJavaScriptParser:
    """Test JavaScriptParser class."""

    def test_init(self):
        """Test JavaScriptParser initialization."""
        parser = JavaScriptParser()
        assert parser.available in [True, False]
        assert parser.parser is not None or not parser.available

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple JavaScript file."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
function hello() {
  console.log("Hello, World!");
}
""")

        parser = JavaScriptParser()
        if not parser.available:
            pytest.skip("tree-sitter-javascript not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = JavaScriptParser()
        if not parser.available:
            pytest.skip("tree-sitter-javascript not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.js"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.js"
        test_file.write_text("function foo() {}")

        parser = JavaScriptParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


class TestTypeScriptParser:
    """Test TypeScriptParser class."""

    def test_init(self):
        """Test TypeScriptParser initialization."""
        parser = TypeScriptParser()
        assert parser.available in [True, False]
        assert parser.parser is not None or not parser.available

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple TypeScript file."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
function hello(): void {
  console.log("Hello, World!");
}
""")

        parser = TypeScriptParser()
        if not parser.available:
            pytest.skip("tree-sitter-typescript not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = TypeScriptParser()
        if not parser.available:
            pytest.skip("tree-sitter-typescript not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.ts"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("function foo(): void {}")

        parser = TypeScriptParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None

    def test_parse_interface(self, tmp_path):
        """Test parsing TypeScript interface."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
interface User {
  name: string;
  age: number;
}
""")

        parser = TypeScriptParser()
        if not parser.available:
            pytest.skip("tree-sitter-typescript not available")

        tree = parser.parse(test_file)
        assert tree is not None
        root = tree.root_node

        # Find interface_declaration node
        found_interface = False
        for child in root.children:
            if child.type == "interface_declaration":
                found_interface = True
                break

        assert found_interface, "Should find interface_declaration node"

    def test_parse_type_alias(self, tmp_path):
        """Test parsing TypeScript type alias."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
type Status = 'ok' | 'error';
""")

        parser = TypeScriptParser()
        if not parser.available:
            pytest.skip("tree-sitter-typescript not available")

        tree = parser.parse(test_file)
        assert tree is not None
        root = tree.root_node

        # Find type_alias_declaration node
        found_type_alias = False
        for child in root.children:
            if child.type == "type_alias_declaration":
                found_type_alias = True
                break

        assert found_type_alias, "Should find type_alias_declaration node"

class TestGoParser:
    """Test GoParser initialization and parsing."""

    def test_init(self):
        """Test GoParser initialization."""
        parser = GoParser()
        assert parser is not None
        # Parser should be available if tree-sitter-go is installed
        assert parser.available is True

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Go file."""
        test_file = tmp_path / "test.go"
        test_file.write_text("""package main

func Add(a, b int) int {
    return a + b
}
""")

        parser = GoParser()
        if not parser.available:
            pytest.skip("tree-sitter-go not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = GoParser()
        if not parser.available:
            pytest.skip("tree-sitter-go not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.go"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.go"
        test_file.write_text("package main\n\nfunc foo() {}")

        parser = GoParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None



class TestRustParser:
    """Test RustParser initialization and parsing."""

    def test_init(self):
        """Test RustParser initialization."""
        parser = RustParser()
        assert parser is not None
        # Parser should be available if tree-sitter-rust is installed
        assert parser.available is True

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Rust file."""
        test_file = tmp_path / "test.rs"
        test_file.write_text("""pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
""")

        parser = RustParser()
        if not parser.available:
            pytest.skip("tree-sitter-rust not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = RustParser()
        if not parser.available:
            pytest.skip("tree-sitter-rust not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.rs"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.rs"
        test_file.write_text("pub fn foo() {}")

        parser = RustParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


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


class TestJavaParser:
    """Test JavaParser initialization and parsing."""

    def test_init(self):
        """Test JavaParser initialization."""
        parser = JavaParser()
        assert parser is not None
        # Parser should be available if tree-sitter-java is installed
        assert parser.available is True

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Java file."""
        test_file = tmp_path / "Test.java"
        test_file.write_text("""public class Test {
    public int add(int a, int b) {
        return a + b;
    }
}
""")

        parser = JavaParser()
        if not parser.available:
            pytest.skip("tree-sitter-java not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = JavaParser()
        if not parser.available:
            pytest.skip("tree-sitter-java not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/File.java"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "Test.java"
        test_file.write_text("public class Test { }")

        parser = JavaParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


class TestCSharpParser:
    """Test CSharpParser initialization and parsing."""

    def test_init(self):
        """Test CSharpParser initialization."""
        parser = CSharpParser()
        assert parser is not None
        # Parser should be available if tree-sitter-c-sharp is installed
        assert parser.available is True

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple C# file."""
        test_file = tmp_path / "Test.cs"
        test_file.write_text("""public class Test
{
    public int Add(int a, int b)
    {
        return a + b;
    }
}
""")

        parser = CSharpParser()
        if not parser.available:
            pytest.skip("tree-sitter-c-sharp not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = CSharpParser()
        if not parser.available:
            pytest.skip("tree-sitter-c-sharp not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/File.cs"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "Test.cs"
        test_file.write_text("public class Test { }")

        parser = CSharpParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


class TestPhpParser:
    """Test PhpParser class."""

    def test_init(self):
        """Test PhpParser initialization."""
        parser = PhpParser()
        assert parser.available in [True, False]
        assert parser.parser is not None or not parser.available

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple PHP file."""
        test_file = tmp_path / "test.php"
        test_file.write_text("""<?php
class User {
    public function getName() {
        return "test";
    }
}
""")

        parser = PhpParser()
        if not parser.available:
            pytest.skip("tree-sitter-php not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = PhpParser()
        if not parser.available:
            pytest.skip("tree-sitter-php not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.php"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.php"
        test_file.write_text("<?php class Test { }")

        parser = PhpParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


class TestRubyParser:
    """Test RubyParser class."""

    def test_init(self):
        """Test RubyParser initialization."""
        parser = RubyParser()
        assert parser.available in [True, False]
        assert parser.parser is not None or not parser.available

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Ruby file."""
        test_file = tmp_path / "test.rb"
        test_file.write_text("""class User
  def initialize(name)
    @name = name
  end

  def greet
    "Hello, #{@name}"
  end
end
""")

        parser = RubyParser()
        if not parser.available:
            pytest.skip("tree-sitter-ruby not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = RubyParser()
        if not parser.available:
            pytest.skip("tree-sitter-ruby not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.rb"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.rb"
        test_file.write_text("class User\nend")

        parser = RubyParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


class TestSwiftParser:
    """Test SwiftParser class."""

    def test_init(self):
        """Test SwiftParser initialization."""
        parser = SwiftParser()
        assert parser.available in [True, False]
        assert parser.parser is not None or not parser.available

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Swift file."""
        test_file = tmp_path / "test.swift"
        test_file.write_text("""class User {
    var name: String
    init(name: String) {
        self.name = name
    }

    func greet() -> String {
        return "Hello, \\(name)"
    }
}
""")

        parser = SwiftParser()
        if not parser.available:
            pytest.skip("tree-sitter-swift not available")

        tree = parser.parse(test_file)
        assert tree is not None
        assert hasattr(tree, "root_node")

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = SwiftParser()
        if not parser.available:
            pytest.skip("tree-sitter-swift not available")

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.swift"))

    def test_parse_when_unavailable(self, tmp_path, monkeypatch):
        """Test parse returns None when parser unavailable."""
        test_file = tmp_path / "test.swift"
        test_file.write_text("class User { }")

        parser = SwiftParser()
        parser.available = False

        result = parser.parse(test_file)
        assert result is None


# ============================================================================
# Kotlin Parser Tests
# ============================================================================


def test_kotlin_parser_init():
    """Test KotlinParser initialization."""
    from clauxton.intelligence.parser import KotlinParser

    parser = KotlinParser()
    assert parser is not None


def test_kotlin_parser_parse_simple_file():
    """Test KotlinParser can parse a simple Kotlin file."""
    from clauxton.intelligence.parser import KotlinParser

    parser = KotlinParser()
    if not parser.available:
        pytest.skip("tree-sitter-kotlin not available")

    sample_file = Path(__file__).parent.parent / "fixtures" / "kotlin" / "sample.kt"
    tree = parser.parse(sample_file)

    assert tree is not None
    assert tree.root_node is not None
    assert tree.root_node.type == "source_file"


def test_kotlin_parser_parse_nonexistent_file():
    """Test KotlinParser raises FileNotFoundError for nonexistent file."""
    from clauxton.intelligence.parser import KotlinParser

    parser = KotlinParser()
    if not parser.available:
        pytest.skip("tree-sitter-kotlin not available")

    with pytest.raises(FileNotFoundError):
        parser.parse(Path("/nonexistent/file.kt"))


def test_kotlin_parser_when_unavailable():
    """Test KotlinParser when tree-sitter-kotlin is unavailable."""
    from clauxton.intelligence.parser import KotlinParser

    parser = KotlinParser()
    parser.available = False

    sample_file = Path(__file__).parent.parent / "fixtures" / "kotlin" / "sample.kt"
    tree = parser.parse(sample_file)
    assert tree is None
