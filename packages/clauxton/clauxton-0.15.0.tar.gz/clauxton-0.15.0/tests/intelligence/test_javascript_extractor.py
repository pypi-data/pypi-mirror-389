"""Tests for JavaScript symbol extraction."""

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import (
    JavaScriptSymbolExtractor,
    SymbolExtractor,
)


class TestJavaScriptSymbolExtractor:
    """Test JavaScriptSymbolExtractor class."""

    def test_init(self):
        """Test JavaScriptSymbolExtractor initialization."""
        extractor = JavaScriptSymbolExtractor()

        # Should have either tree-sitter or be unavailable
        assert extractor.available in [True, False]

        if extractor.available:
            assert extractor.parser is not None
            assert extractor.language is not None

    def test_extract_simple_function(self, tmp_path):
        """Test extracting a simple function."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
function hello() {
  console.log("Hello, World!");
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert len(symbols) == 1
        symbol = symbols[0]
        assert symbol["name"] == "hello"
        assert symbol["type"] == "function"
        assert symbol["line_start"] > 0
        assert symbol["line_end"] > symbol["line_start"]

    def test_extract_arrow_function(self, tmp_path):
        """Test extracting arrow functions."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
const square = (x) => x * x;
const double = (x) => x * 2;
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert len(symbols) == 2
        names = [s["name"] for s in symbols]
        assert "square" in names
        assert "double" in names
        for symbol in symbols:
            assert symbol["type"] == "function"

    def test_extract_async_function(self, tmp_path):
        """Test extracting async functions."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
async function fetchData(url) {
  const response = await fetch(url);
  return response.json();
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert len(symbols) == 1
        symbol = symbols[0]
        assert symbol["name"] == "fetchData"
        assert symbol["type"] == "function"

    def test_extract_class(self, tmp_path):
        """Test extracting a class."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
class Calculator {
  constructor(name) {
    this.name = name;
  }

  add(a, b) {
    return a + b;
  }
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        # Should extract class and methods
        assert len(symbols) >= 1
        class_symbols = [s for s in symbols if s["type"] == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0]["name"] == "Calculator"

        method_symbols = [s for s in symbols if s["type"] == "method"]
        method_names = [s["name"] for s in method_symbols]
        assert "constructor" in method_names
        assert "add" in method_names

    def test_extract_mixed_symbols(self, tmp_path):
        """Test extracting mix of functions, classes, and arrow functions."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
// Regular function
function factorial(n) {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// Arrow function
const square = (x) => x * x;

// Class
class MyClass {
  method1() {
    return 42;
  }
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        names = [s["name"] for s in symbols]
        assert "factorial" in names
        assert "square" in names
        assert "MyClass" in names
        assert "method1" in names

    def test_extract_function_expression(self, tmp_path):
        """Test extracting function expressions."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
const greet = function(name) {
  return `Hello, ${name}!`;
};
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert len(symbols) == 1
        symbol = symbols[0]
        assert symbol["name"] == "greet"
        assert symbol["type"] == "function"

    def test_extract_empty_file(self, tmp_path):
        """Test extracting from empty file."""
        test_file = tmp_path / "test.js"
        test_file.write_text("")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert symbols == []

    def test_extract_file_with_only_comments(self, tmp_path):
        """Test extracting from file with only comments."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
// Just a comment
/* Block comment */
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert symbols == []

    def test_extract_nonexistent_file_raises_error(self, tmp_path):
        """Test that extracting from non-existent file raises error."""
        nonexistent = tmp_path / "does_not_exist.js"

        extractor = JavaScriptSymbolExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract(nonexistent)

    def test_extract_with_unicode(self, tmp_path):
        """Test extracting from file with Unicode characters."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
// Function with Japanese name
function こんにちは(名前) {
  return `こんにちは、${名前}さん！`;
}

// Class with emoji
class 😀Emoji {
  greet() {
    return "Hello! 🎉";
  }
}
""", encoding="utf-8")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        names = [s["name"] for s in symbols]
        assert "こんにちは" in names
        assert "😀Emoji" in names

    def test_extract_with_export_statements(self, tmp_path):
        """Test extracting from file with export statements."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
function publicFunc() {
  return "public";
}

class PublicClass {
  method() {
    return true;
  }
}

export { publicFunc, PublicClass };
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        # Should extract functions and classes regardless of export
        names = [s["name"] for s in symbols]
        assert "publicFunc" in names
        assert "PublicClass" in names

    def test_extract_with_let_arrow_function(self, tmp_path):
        """Test extracting arrow functions declared with let."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
let double = (x) => x * 2;
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        assert len(symbols) == 1
        symbol = symbols[0]
        assert symbol["name"] == "double"
        assert symbol["type"] == "function"

    def test_extract_fixture_sample_js(self):
        """Test extracting from sample.js fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "javascript" / "sample.js"

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(fixture_path)

        # Verify expected symbols from sample.js
        names = [s["name"] for s in symbols]
        assert "Calculator" in names
        assert "factorial" in names
        assert "square" in names
        assert "double" in names
        assert "fetchData" in names
        assert "greet" in names

        # Verify types
        class_symbols = [s for s in symbols if s["type"] == "class"]
        assert len(class_symbols) >= 1

        function_symbols = [s for s in symbols if s["type"] == "function"]
        assert len(function_symbols) >= 4

    def test_extract_fixture_empty_js(self):
        """Test extracting from empty.js fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "javascript" / "empty.js"

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(fixture_path)

        assert symbols == []

    def test_extract_fixture_unicode_js(self):
        """Test extracting from unicode.js fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "javascript" / "unicode.js"

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(fixture_path)

        names = [s["name"] for s in symbols]
        assert "こんにちは" in names
        assert "😀Emoji" in names


class TestSymbolExtractorWithJavaScript:
    """Test SymbolExtractor class with JavaScript."""

    def test_symbol_extractor_has_javascript(self):
        """Test that SymbolExtractor includes JavaScript extractor."""
        extractor = SymbolExtractor()
        assert "javascript" in extractor.extractors
        assert isinstance(extractor.extractors["javascript"], JavaScriptSymbolExtractor)

    def test_symbol_extractor_extract_javascript(self, tmp_path):
        """Test extracting JavaScript file through SymbolExtractor."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
function testFunc() {
  return 42;
}
""")

        extractor = SymbolExtractor()
        js_extractor = extractor.extractors["javascript"]

        if not js_extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file, "javascript")

        assert len(symbols) >= 1
        assert symbols[0]["name"] == "testFunc"


class TestJavaScriptSymbolExtractorUnavailable:
    """Test behavior when tree-sitter-javascript is unavailable."""

    def test_extract_returns_empty_when_unavailable(self, tmp_path, monkeypatch):
        """Test that extraction returns empty list when tree-sitter-javascript unavailable."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
function test() {
  return true;
}
""")

        # Force tree-sitter-javascript to be unavailable
        import sys
        monkeypatch.setitem(sys.modules, "tree_sitter_javascript", None)

        # Create new extractor (will be unavailable)
        extractor = JavaScriptSymbolExtractor()
        assert not extractor.available

        symbols = extractor.extract(test_file)

        # Should return empty list when unavailable
        assert symbols == []

    def test_extract_logs_warning_when_unavailable(self, tmp_path, monkeypatch, caplog):
        """Test that warning is logged when tree-sitter-javascript unavailable."""
        import logging

        test_file = tmp_path / "test.js"
        test_file.write_text("function test() {}")

        # Force tree-sitter-javascript to be unavailable
        import sys
        monkeypatch.setitem(sys.modules, "tree_sitter_javascript", None)

        # Create new extractor (will be unavailable)
        with caplog.at_level(logging.WARNING):
            extractor = JavaScriptSymbolExtractor()
            extractor.extract(test_file)

        # Should have logged warnings
        assert "tree-sitter-javascript not available" in caplog.text


class TestJavaScriptSymbolExtractorEdgeCases:
    """Test edge cases for JavaScript symbol extraction."""

    def test_extract_signature_with_exception(self, tmp_path):
        """Test signature extraction handles exceptions gracefully."""
        test_file = tmp_path / "test.js"
        # Create a function with unusual formatting that might cause issues
        test_file.write_text("""
function veryLongFunctionNameWithManyParameters(
  param1, param2, param3, param4, param5,
  param6, param7, param8, param9, param10
) {
  return true;
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        # Should still extract function
        assert len(symbols) >= 1
        assert symbols[0]["name"] == "veryLongFunctionNameWithManyParameters"

    def test_extract_nested_classes_and_functions(self, tmp_path):
        """Test extracting nested structures."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
class Outer {
  innerMethod() {
    const innerFunc = () => {
      return "nested";
    };
    return innerFunc;
  }
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        symbols = extractor.extract(test_file)

        # Should extract class and method (innerFunc is deeply nested)
        names = [s["name"] for s in symbols]
        assert "Outer" in names
        assert "innerMethod" in names

    def test_extract_with_jsx_like_syntax(self, tmp_path):
        """Test extraction with JSX-like syntax (should handle or skip gracefully)."""
        test_file = tmp_path / "test.js"
        test_file.write_text("""
function Component() {
  return <div>Hello</div>;
}
""")

        extractor = JavaScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-javascript not available")

        # Should not crash, may or may not extract depending on parser
        symbols = extractor.extract(test_file)
        assert isinstance(symbols, list)
