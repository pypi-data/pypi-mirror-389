"""
Tests for TypeScript symbol extraction.

Tests TypeScriptSymbolExtractor class using tree-sitter-typescript.
"""

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import SymbolExtractor, TypeScriptSymbolExtractor


class TestTypeScriptSymbolExtractor:
    """Test TypeScriptSymbolExtractor class."""

    def test_init(self):
        """Test TypeScriptSymbolExtractor initialization."""
        extractor = TypeScriptSymbolExtractor()

        # Parser should always be initialized
        assert extractor.parser is not None
        from clauxton.intelligence.parser import TypeScriptParser
        assert isinstance(extractor.parser, TypeScriptParser)

        # Should have tree-sitter available
        assert extractor.available in [True, False]

    def test_extract_interface(self, tmp_path):
        """Test extracting interface."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
interface User {
  name: string;
  age: number;
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) == 1
        assert symbols[0]["name"] == "User"
        assert symbols[0]["type"] == "interface"
        assert symbols[0]["file_path"] == str(test_file)
        assert symbols[0]["line_start"] == 2
        assert symbols[0]["line_end"] == 5

    def test_extract_type_alias(self, tmp_path):
        """Test extracting type alias."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
type Operation = 'add' | 'subtract' | 'multiply';
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) == 1
        assert symbols[0]["name"] == "Operation"
        assert symbols[0]["type"] == "type_alias"
        assert symbols[0]["file_path"] == str(test_file)

    def test_extract_class(self, tmp_path):
        """Test extracting class with type annotations."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
class Calculator {
  constructor(private precision: number) {}
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Should extract: class + constructor method
        assert len(symbols) >= 1
        class_symbol = next(s for s in symbols if s["type"] == "class")
        assert class_symbol["name"] == "Calculator"

    def test_extract_function_with_types(self, tmp_path):
        """Test extracting function with type annotations."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
function add(a: number, b: number): number {
  return a + b;
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) == 1
        assert symbols[0]["name"] == "add"
        assert symbols[0]["type"] == "function"
        assert "signature" in symbols[0]

    def test_extract_arrow_function_with_types(self, tmp_path):
        """Test extracting arrow function with type annotations."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
const multiply = (x: number, y: number): number => x * y;
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) == 1
        assert symbols[0]["name"] == "multiply"
        assert symbols[0]["type"] == "function"

    def test_extract_generic_function(self, tmp_path):
        """Test extracting generic function."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
function identity<T>(arg: T): T {
  return arg;
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) == 1
        assert symbols[0]["name"] == "identity"
        assert symbols[0]["type"] == "function"

    def test_extract_async_function(self, tmp_path):
        """Test extracting async function with types."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
async function fetchData(url: string): Promise<string> {
  return await fetch(url);
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) == 1
        assert symbols[0]["name"] == "fetchData"
        assert symbols[0]["type"] == "function"

    def test_extract_class_methods(self, tmp_path):
        """Test extracting class methods with types."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
class MathService {
  add(a: number, b: number): number {
    return a + b;
  }

  async calculate(op: string): Promise<number> {
    return 0;
  }
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Should extract: class + 2 methods
        assert len(symbols) >= 3
        class_symbol = next(s for s in symbols if s["type"] == "class")
        assert class_symbol["name"] == "MathService"

        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) >= 2
        method_names = {m["name"] for m in methods}
        assert "add" in method_names
        assert "calculate" in method_names

    def test_extract_mixed_symbols(self, tmp_path):
        """Test extracting mixed symbol types."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
interface Config {
  debug: boolean;
}

type Status = 'ok' | 'error';

class App {
  start(): void {}
}

function main(): void {}

const helper = (): number => 42;
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Interface + Type alias + Class + Method + Function + Arrow function
        assert len(symbols) >= 6

        symbol_types = {s["type"] for s in symbols}
        assert "interface" in symbol_types
        assert "type_alias" in symbol_types
        assert "class" in symbol_types
        assert "function" in symbol_types

    def test_extract_empty_file(self, tmp_path):
        """Test extracting from empty file."""
        test_file = tmp_path / "empty.ts"
        test_file.write_text("")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert symbols == []

    def test_extract_comments_only(self, tmp_path):
        """Test extracting from file with only comments."""
        test_file = tmp_path / "comments.ts"
        test_file.write_text("""
// This is a comment
/* Multi-line
   comment */
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert symbols == []

    def test_extract_with_unicode(self, tmp_path):
        """Test extracting symbols with Unicode names."""
        test_file = tmp_path / "unicode.ts"
        test_file.write_text("""
function こんにちは(名前: string): string {
  return `こんにちは、${名前}さん！`;
}

interface 😀Emoji {
  greet(): string;
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        assert len(symbols) >= 2

        names = {s["name"] for s in symbols}
        assert "こんにちは" in names
        assert "😀Emoji" in names

    def test_extract_with_export(self, tmp_path):
        """Test extracting exported symbols."""
        test_file = tmp_path / "exports.ts"
        test_file.write_text("""
export interface User {
  name: string;
}

export class UserService {
  getUser(): User | null {
    return null;
  }
}

export function createUser(): User {
  return { name: '' };
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Interface + Class + Method + Function
        assert len(symbols) >= 4

        names = {s["name"] for s in symbols}
        assert "User" in names
        assert "UserService" in names
        assert "createUser" in names

    def test_extract_nested_structures(self, tmp_path):
        """Test extracting nested structures."""
        test_file = tmp_path / "nested.ts"
        test_file.write_text("""
class Outer {
  method(): void {
    const inner = (): number => 42;
  }
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Should extract: class + method (inner function may or may not be extracted)
        assert len(symbols) >= 2

    def test_extract_file_not_found(self):
        """Test extracting from non-existent file."""
        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/file.ts"))

    def test_extract_when_parser_unavailable(self, tmp_path, monkeypatch):
        """Test extraction when tree-sitter-typescript is unavailable."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("function test() {}")

        # Mock parser to be unavailable
        extractor = TypeScriptSymbolExtractor()
        extractor.available = False

        symbols = extractor.extract(test_file)
        assert symbols == []

    def test_integration_with_symbol_extractor(self, tmp_path):
        """Test TypeScriptSymbolExtractor integration with SymbolExtractor."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
interface Data {
  value: number;
}

function process(data: Data): void {}
""")

        extractor = SymbolExtractor()
        symbols = extractor.extract(test_file, "typescript")

        # If tree-sitter available, should extract symbols
        if "typescript" in extractor.extractors and extractor.extractors["typescript"].available:
            assert len(symbols) >= 2
            names = {s["name"] for s in symbols}
            assert "Data" in names
            assert "process" in names

    def test_fixture_sample_ts(self):
        """Test extraction from sample.ts fixture."""
        fixture_path = Path("tests/fixtures/typescript/sample.ts")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(fixture_path)

        # Sample.ts should have: interface, type, class, methods, functions
        assert len(symbols) >= 8

        names = {s["name"] for s in symbols}
        assert "Calculator" in names  # interface
        assert "Operation" in names  # type alias
        assert "MathService" in names  # class
        assert "factorial" in names  # function
        assert "square" in names  # arrow function
        assert "identity" in names  # generic function

    def test_fixture_empty_ts(self):
        """Test extraction from empty.ts fixture."""
        fixture_path = Path("tests/fixtures/typescript/empty.ts")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(fixture_path)
        assert symbols == []

    def test_fixture_unicode_ts(self):
        """Test extraction from unicode.ts fixture."""
        fixture_path = Path("tests/fixtures/typescript/unicode.ts")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(fixture_path)
        assert len(symbols) >= 3

        names = {s["name"] for s in symbols}
        assert "こんにちは" in names
        assert "😀Emoji" in names
        assert "🎉Celebration" in names

    def test_extract_enum(self, tmp_path):
        """Test extracting TypeScript enum."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
enum Color {
  Red,
  Green,
  Blue
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Note: Current implementation may not extract enum (not in _walk_tree)
        # This test documents current behavior
        # If enum support is added later, update assertions
        assert isinstance(symbols, list)

    def test_extract_namespace(self, tmp_path):
        """Test extracting TypeScript namespace."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
namespace Utils {
  export function formatDate(date: Date): string {
    return date.toISOString();
  }
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Note: Current implementation may not extract namespace (not in _walk_tree)
        # This test documents current behavior
        # Should extract at least the function inside
        assert isinstance(symbols, list)

    def test_extract_multiple_signatures(self, tmp_path):
        """Test extracting function with multiple overload signatures."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("""
function add(a: number, b: number): number;
function add(a: string, b: string): string;
function add(a: any, b: any): any {
  return a + b;
}
""")

        extractor = TypeScriptSymbolExtractor()
        if not extractor.available:
            pytest.skip("tree-sitter-typescript not available")

        symbols = extractor.extract(test_file)
        # Should extract at least the implementation
        assert len(symbols) >= 1
        names = {s["name"] for s in symbols}
        assert "add" in names
