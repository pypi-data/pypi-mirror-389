"""
Tests for Go symbol extraction.

Tests GoSymbolExtractor functionality including:
- Basic symbol extraction (functions, methods, structs, interfaces, type aliases)
- Go-specific features (pointer/value receivers, generics)
- Edge cases (empty files, unicode names)
- Error handling
- Integration with SymbolExtractor
"""
# type: ignore  # tree-sitter has complex types

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import GoSymbolExtractor, SymbolExtractor


class TestGoSymbolExtractor:
    """Test Go symbol extraction."""

    def test_init(self):
        """Test GoSymbolExtractor initialization."""
        extractor = GoSymbolExtractor()
        assert extractor.parser is not None
        # Parser should be available if tree-sitter-go is installed
        assert extractor.available is True

    def test_extract_function(self, tmp_path: Path):
        """Test extracting a simple function."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

// Add adds two integers
func Add(a, b int) int {
    return a + b
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Add"
        assert symbols[0]["type"] == "function"
        assert symbols[0]["line_start"] == 4
        assert "signature" in symbols[0]
        assert "func Add(a, b int) int" in symbols[0]["signature"]

    def test_extract_method(self, tmp_path: Path):
        """Test extracting a method with receiver."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type User struct {
    Name string
}

func (u *User) GetName() string {
    return u.Name
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        # Should extract struct and method
        assert len(symbols) == 2
        struct_sym = next(s for s in symbols if s["type"] == "struct")
        method_sym = next(s for s in symbols if s["type"] == "method")

        assert struct_sym["name"] == "User"
        assert method_sym["name"] == "GetName"
        assert method_sym["receiver"] == "*User"

    def test_extract_struct(self, tmp_path: Path):
        """Test extracting a struct declaration."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type User struct {
    Name string
    Age  int
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "User"
        assert symbols[0]["type"] == "struct"
        assert symbols[0]["line_start"] == 3

    def test_extract_interface(self, tmp_path: Path):
        """Test extracting an interface declaration."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type Reader interface {
    Read(p []byte) (n int, err error)
    Close() error
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Reader"
        assert symbols[0]["type"] == "interface"
        assert symbols[0]["line_start"] == 3

    def test_extract_type_alias(self, tmp_path: Path):
        """Test extracting a type alias."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type Status string
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Status"
        assert symbols[0]["type"] == "type_alias"

    def test_extract_multiple_functions(self, tmp_path: Path):
        """Test extracting multiple functions."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

func Add(a, b int) int {
    return a + b
}

func Multiply(a, b int) int {
    return a * b
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 2
        assert symbols[0]["name"] == "Add"
        assert symbols[1]["name"] == "Multiply"

    def test_extract_struct_with_methods(self, tmp_path: Path):
        """Test extracting struct and its methods."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type User struct {
    Name string
}

func (u *User) GetName() string {
    return u.Name
}

func (u *User) SetName(name string) {
    u.Name = name
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 3
        struct_syms = [s for s in symbols if s["type"] == "struct"]
        method_syms = [s for s in symbols if s["type"] == "method"]

        assert len(struct_syms) == 1
        assert len(method_syms) == 2
        assert struct_syms[0]["name"] == "User"
        assert method_syms[0]["name"] == "GetName"
        assert method_syms[1]["name"] == "SetName"

    def test_extract_mixed_symbols(self, tmp_path: Path):
        """Test extracting mixed symbol types."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type User struct {
    Name string
}

type Status string

func Add(a, b int) int {
    return a + b
}

func (u *User) GetName() string {
    return u.Name
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 4
        types_count = {"struct": 0, "type_alias": 0, "function": 0, "method": 0}
        for s in symbols:
            types_count[s["type"]] += 1

        assert types_count["struct"] == 1
        assert types_count["type_alias"] == 1
        assert types_count["function"] == 1
        assert types_count["method"] == 1

    def test_extract_pointer_receiver(self, tmp_path: Path):
        """Test extracting method with pointer receiver."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type User struct {
    Name string
}

func (u *User) SetName(name string) {
    u.Name = name
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        method_sym = next(s for s in symbols if s["type"] == "method")
        assert method_sym["receiver"] == "*User"

    def test_extract_value_receiver(self, tmp_path: Path):
        """Test extracting method with value receiver."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

type User struct {
    Name string
}

func (u User) GetName() string {
    return u.Name
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        method_sym = next(s for s in symbols if s["type"] == "method")
        assert method_sym["receiver"] == "User"

    def test_extract_generic_function(self, tmp_path: Path):
        """Test extracting generic function (Go 1.18+)."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

func Identity[T any](x T) T {
    return x
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Identity"
        assert symbols[0]["type"] == "function"
        assert "Identity[T any]" in symbols[0]["signature"]

    def test_extract_empty_file(self, tmp_path: Path):
        """Test extracting from empty file."""
        go_file = tmp_path / "empty.go"
        go_file.write_text("package main\n")

        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 0

    def test_extract_comments_only(self, tmp_path: Path):
        """Test extracting from file with only comments."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""// This is a comment
package main

// Another comment
// Yet another comment
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 0

    def test_extract_with_unicode(self, tmp_path: Path):
        """Test extracting symbols with unicode names."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

// こんにちは greets with Japanese
func こんにちは(名前 string) string {
    return "こんにちは、" + 名前 + "さん！"
}

type 😀Emoji interface {
    Greet() string
}
""")
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 2
        func_sym = next(s for s in symbols if s["type"] == "function")
        iface_sym = next(s for s in symbols if s["type"] == "interface")

        assert func_sym["name"] == "こんにちは"
        # Note: Emoji in type names may be handled differently by tree-sitter-go
        # The emoji might be part of the name or excluded depending on parser behavior
        assert "Emoji" in iface_sym["name"]

    def test_extract_with_package_only(self, tmp_path: Path):
        """Test extracting from file with only package declaration."""
        go_file = tmp_path / "test.go"
        go_file.write_text("package main")

        extractor = GoSymbolExtractor()
        symbols = extractor.extract(go_file)

        assert len(symbols) == 0

    def test_extract_file_not_found(self):
        """Test extracting from non-existent file."""
        extractor = GoSymbolExtractor()
        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/file.go"))

    def test_extract_when_parser_unavailable(self, tmp_path: Path, monkeypatch):
        """Test extraction when parser is unavailable."""
        go_file = tmp_path / "test.go"
        go_file.write_text("package main\n\nfunc Add(a, b int) int { return a + b }")

        extractor = GoSymbolExtractor()
        # Simulate parser unavailable
        monkeypatch.setattr(extractor, "available", False)

        symbols = extractor.extract(go_file)
        assert len(symbols) == 0

    def test_integration_with_symbol_extractor(self, tmp_path: Path):
        """Test integration with SymbolExtractor dispatcher."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""package main

func Add(a, b int) int {
    return a + b
}
""")
        extractor = SymbolExtractor()
        symbols = extractor.extract(go_file, "go")

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Add"
        assert symbols[0]["type"] == "function"

    def test_fixture_sample_go(self):
        """Test extraction from sample.go fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "go" / "sample.go"
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract: User (struct), Reader (interface), Status (type alias),
        # Add (func), Multiply (func), GetName (method), SetName (method), Identity (func)
        assert len(symbols) >= 8

        names = [s["name"] for s in symbols]
        assert "User" in names
        assert "Reader" in names
        assert "Status" in names
        assert "Add" in names
        assert "Multiply" in names
        assert "GetName" in names
        assert "SetName" in names
        assert "Identity" in names

    def test_fixture_empty_go(self):
        """Test extraction from empty.go fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "go" / "empty.go"
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        assert len(symbols) == 0

    def test_fixture_unicode_go(self):
        """Test extraction from unicode.go fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "go" / "unicode.go"
        extractor = GoSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract: こんにちは (func), Emoji (interface), Celebration (struct), Greet (method)
        # Note: Emoji symbols in type names may be handled differently by tree-sitter-go
        assert len(symbols) >= 4

        names = [s["name"] for s in symbols]
        assert "こんにちは" in names
        # Emoji in type names may be excluded by tree-sitter-go parser
        assert any("Emoji" in name for name in names)
        assert any("Celebration" in name for name in names)
