"""
Tests for Rust symbol extraction.

Tests RustSymbolExtractor functionality including:
- Basic symbol extraction (functions, methods, structs, enums, traits, type aliases)
- Rust-specific features (self receivers, impl blocks)
- Edge cases (empty files, unicode names)
- Error handling
- Integration with SymbolExtractor
"""
# type: ignore  # tree-sitter has complex types

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import RustSymbolExtractor, SymbolExtractor


class TestRustSymbolExtractor:
    """Test Rust symbol extraction."""

    def test_init(self):
        """Test RustSymbolExtractor initialization."""
        extractor = RustSymbolExtractor()
        assert extractor.parser is not None
        # Parser should be available if tree-sitter-rust is installed
        assert extractor.available is True

    def test_extract_function(self, tmp_path: Path):
        """Test extracting a simple function."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""/// Add two integers
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "add"
        assert symbols[0]["type"] == "function"
        assert symbols[0]["line_start"] == 2
        assert "signature" in symbols[0]
        assert "fn add" in symbols[0]["signature"]

    def test_extract_method(self, tmp_path: Path):
        """Test extracting a method with self receiver."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    pub name: String,
}

impl User {
    pub fn get_name(&self) -> &str {
        &self.name
    }
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        # Should extract struct and method
        assert len(symbols) == 2
        struct_sym = next(s for s in symbols if s["type"] == "struct")
        method_sym = next(s for s in symbols if s["type"] == "method")

        assert struct_sym["name"] == "User"
        assert method_sym["name"] == "get_name"
        assert method_sym["receiver"] == "&self"

    def test_extract_struct(self, tmp_path: Path):
        """Test extracting a struct declaration."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    pub name: String,
    pub age: u32,
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "User"
        assert symbols[0]["type"] == "struct"
        assert symbols[0]["line_start"] == 1

    def test_extract_enum(self, tmp_path: Path):
        """Test extracting an enum declaration."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub enum Status {
    Ok,
    Error(String),
    Pending,
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Status"
        assert symbols[0]["type"] == "enum"
        assert symbols[0]["line_start"] == 1

    def test_extract_trait(self, tmp_path: Path):
        """Test extracting a trait declaration."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub trait Display {
    fn fmt(&self) -> String;
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Display"
        assert symbols[0]["type"] == "trait"
        assert symbols[0]["line_start"] == 1

    def test_extract_type_alias(self, tmp_path: Path):
        """Test extracting a type alias."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text(
            """pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
"""
        )
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "Result"
        assert symbols[0]["type"] == "type_alias"
        assert symbols[0]["line_start"] == 1

    def test_extract_multiple_functions(self, tmp_path: Path):
        """Test extracting multiple functions."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn subtract(a: i32, b: i32) -> i32 {
    a - b
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 2
        assert symbols[0]["name"] == "add"
        assert symbols[1]["name"] == "subtract"

    def test_extract_struct_with_methods(self, tmp_path: Path):
        """Test extracting struct with multiple methods."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct Counter {
    count: u32,
}

impl Counter {
    pub fn new() -> Self {
        Counter { count: 0 }
    }

    pub fn increment(&mut self) {
        self.count += 1;
    }

    pub fn get(&self) -> u32 {
        self.count
    }
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 4  # 1 struct + 3 methods
        assert symbols[0]["type"] == "struct"
        assert sum(1 for s in symbols if s["type"] == "method") == 3

    def test_extract_mixed_symbols(self, tmp_path: Path):
        """Test extracting mixed symbol types."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    name: String,
}

pub enum Status {
    Active,
    Inactive,
}

pub trait Greet {
    fn greet(&self) -> String;
}

pub fn hello() -> String {
    "Hello".to_string()
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 4
        types = {s["type"] for s in symbols}
        assert types == {"struct", "enum", "trait", "function"}

    def test_extract_immutable_self_receiver(self, tmp_path: Path):
        """Test extracting method with immutable self reference."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    name: String,
}

impl User {
    pub fn get_name(&self) -> &str {
        &self.name
    }
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        method_sym = next(s for s in symbols if s["type"] == "method")
        assert method_sym["receiver"] == "&self"

    def test_extract_mutable_self_receiver(self, tmp_path: Path):
        """Test extracting method with mutable self reference."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct Counter {
    count: u32,
}

impl Counter {
    pub fn increment(&mut self) {
        self.count += 1;
    }
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        method_sym = next(s for s in symbols if s["type"] == "method")
        assert method_sym["receiver"] == "&mut self"

    def test_extract_owned_self_receiver(self, tmp_path: Path):
        """Test extracting method that consumes self."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    name: String,
}

impl User {
    pub fn into_name(self) -> String {
        self.name
    }
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        method_sym = next(s for s in symbols if s["type"] == "method")
        assert method_sym["receiver"] == "self"

    def test_extract_generic_function(self, tmp_path: Path):
        """Test extracting generic function."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub fn identity<T>(x: T) -> T {
    x
}
""")
        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "identity"
        assert "<T>" in symbols[0]["signature"]

    def test_extract_empty_file(self, tmp_path: Path):
        """Test extracting from empty file."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 0

    def test_extract_comments_only(self, tmp_path: Path):
        """Test extracting from file with only comments."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""// This is a comment
// Another comment
""")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 0

    def test_extract_with_unicode(self, tmp_path: Path):
        """Test extracting symbols with unicode names."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub fn こんにちは() -> String {
    "Hello".to_string()
}

pub struct 使用者 {
    name: String,
}
""")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 2
        # Unicode should be preserved
        assert "こんにちは" in symbols[0]["name"]
        assert "使用者" in symbols[1]["name"]

    def test_extract_file_not_found(self):
        """Test extract raises FileNotFoundError for non-existent file."""
        extractor = RustSymbolExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/file.rs"))

    def test_extract_when_parser_unavailable(self, tmp_path: Path):
        """Test extract returns empty list when parser unavailable."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("pub fn foo() {}")

        extractor = RustSymbolExtractor()
        extractor.available = False

        symbols = extractor.extract(rust_file)
        assert len(symbols) == 0

    def test_integration_with_symbol_extractor(self, tmp_path: Path):
        """Test integration with main SymbolExtractor."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
""")

        dispatcher = SymbolExtractor()
        symbols = dispatcher.extract(rust_file, "rust")

        assert len(symbols) == 1
        assert symbols[0]["name"] == "add"

    def test_fixture_sample_rs(self):
        """Test extraction from sample.rs fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "rust" / "sample.rs"
        if not fixture_path.exists():
            pytest.skip("sample.rs fixture not found")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract: User struct, Status enum, Display trait, Result type alias,
        # add, multiply functions, and User methods (new, get_name, set_name, into_name)
        # + Display impl methods
        assert len(symbols) >= 10

        # Check specific symbols
        names = {s["name"] for s in symbols}
        assert "User" in names
        assert "Status" in names
        assert "Display" in names
        assert "Result" in names
        assert "add" in names
        assert "multiply" in names

    def test_fixture_empty_rs(self):
        """Test extraction from empty.rs fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "rust" / "empty.rs"
        if not fixture_path.exists():
            pytest.skip("empty.rs fixture not found")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        assert len(symbols) == 0

    def test_fixture_unicode_rs(self):
        """Test extraction from unicode.rs fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "rust" / "unicode.rs"
        if not fixture_path.exists():
            pytest.skip("unicode.rs fixture not found")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(fixture_path)

        # Should extract: こんにちは func, 😀Celebration struct, 🎉Party trait, greet method
        assert len(symbols) >= 3

        # Check for unicode symbols (emoji may be handled differently by parser)
        names = [s["name"] for s in symbols]
        assert any("こんにちは" in name for name in names)

    def test_extract_multiple_impl_blocks(self, tmp_path: Path):
        """Test extracting multiple impl blocks for the same type."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    name: String,
}

impl User {
    pub fn new(name: String) -> Self {
        User { name }
    }
}

impl User {
    pub fn get_name(&self) -> &str {
        &self.name
    }
}
""")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        # Should extract: 1 struct + 2 methods from 2 impl blocks
        assert len(symbols) == 3
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 2
        method_names = {m["name"] for m in methods}
        assert method_names == {"new", "get_name"}

    def test_extract_trait_impl(self, tmp_path: Path):
        """Test extracting trait implementation (impl Trait for Type)."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub trait Display {
    fn fmt(&self) -> String;
}

pub struct User {
    name: String,
}

impl Display for User {
    fn fmt(&self) -> String {
        format!("User: {}", self.name)
    }
}
""")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        # Should extract: 1 trait + 1 struct + 1 method (from trait impl)
        assert len(symbols) >= 3
        trait_sym = next((s for s in symbols if s["type"] == "trait"), None)
        struct_sym = next((s for s in symbols if s["type"] == "struct"), None)
        method_sym = next((s for s in symbols if s["type"] == "method"), None)

        assert trait_sym is not None
        assert struct_sym is not None
        assert method_sym is not None
        assert method_sym["name"] == "fmt"

    def test_extract_associated_function(self, tmp_path: Path):
        """Test extracting associated function (no self parameter)."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub struct User {
    name: String,
}

impl User {
    pub fn new(name: String) -> Self {
        User { name }
    }

    pub fn default_name() -> String {
        "Anonymous".to_string()
    }
}
""")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        # Should extract: 1 struct + 2 methods (both are methods in impl block)
        assert len(symbols) == 3
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 2

        # Check that associated functions are extracted (may have None receiver)
        new_method = next(m for m in methods if m["name"] == "new")
        default_method = next(m for m in methods if m["name"] == "default_name")
        assert new_method is not None
        assert default_method is not None

    def test_extract_nested_generics(self, tmp_path: Path):
        """Test extracting function with nested generics."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text(
            """pub fn complex<T, U>(data: Vec<Vec<T>>, map: HashMap<String, U>) -> Option<T> {
    None
}
"""
        )

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        assert len(symbols) == 1
        assert symbols[0]["name"] == "complex"
        assert symbols[0]["type"] == "function"
        # Should capture generics in signature
        assert "<T, U>" in symbols[0]["signature"] or "<T," in symbols[0]["signature"]

    def test_extract_syntax_error_file(self, tmp_path: Path):
        """Test extracting from file with syntax errors."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub fn incomplete(
    // Missing closing parenthesis and body
""")

        extractor = RustSymbolExtractor()
        # Should not crash, may return empty or partial results
        symbols = extractor.extract(rust_file)
        # Parser may or may not extract symbols from malformed code
        assert isinstance(symbols, list)

    def test_extract_pub_visibility(self, tmp_path: Path):
        """Test that pub and non-pub items are both extracted."""
        rust_file = tmp_path / "test.rs"
        rust_file.write_text("""pub fn public_func() {}

fn private_func() {}

pub struct PublicStruct {}

struct PrivateStruct {}
""")

        extractor = RustSymbolExtractor()
        symbols = extractor.extract(rust_file)

        # Should extract all items regardless of visibility
        assert len(symbols) == 4
        names = {s["name"] for s in symbols}
        assert names == {"public_func", "private_func", "PublicStruct", "PrivateStruct"}
