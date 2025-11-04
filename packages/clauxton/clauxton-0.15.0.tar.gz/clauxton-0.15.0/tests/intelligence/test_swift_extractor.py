"""Tests for Swift symbol extraction."""

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import SwiftSymbolExtractor


@pytest.fixture
def swift_extractor():
    """Create SwiftSymbolExtractor instance."""
    return SwiftSymbolExtractor()


@pytest.fixture
def sample_file(tmp_path):
    """Path to sample Swift file."""
    return Path(__file__).parent.parent / "fixtures" / "swift" / "sample.swift"


@pytest.fixture
def empty_file(tmp_path):
    """Path to empty Swift file."""
    return Path(__file__).parent.parent / "fixtures" / "swift" / "empty.swift"


@pytest.fixture
def unicode_file(tmp_path):
    """Path to Unicode Swift file."""
    return Path(__file__).parent.parent / "fixtures" / "swift" / "unicode.swift"


# ===========================
# 1. Initialization Tests
# ===========================


def test_initialization(swift_extractor):
    """Test SwiftSymbolExtractor initialization."""
    assert swift_extractor is not None
    assert hasattr(swift_extractor, "parser")


# ===========================
# 2. Basic Extraction Tests
# ===========================


def test_extract_class(tmp_path):
    """Test extracting a class."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var name: String
    init(name: String) {
        self.name = name
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 1
    assert classes[0]["name"] == "User"
    assert classes[0]["line_start"] == 2


def test_extract_struct(tmp_path):
    """Test extracting a struct."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
struct Point {
    var x: Int
    var y: Int
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    structs = [s for s in symbols if s["type"] == "struct"]
    assert len(structs) == 1
    assert structs[0]["name"] == "Point"
    assert structs[0]["line_start"] == 2


def test_extract_enum(tmp_path):
    """Test extracting an enum."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
enum Direction {
    case north, south, east, west
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    enums = [s for s in symbols if s["type"] == "enum"]
    assert len(enums) == 1
    assert enums[0]["name"] == "Direction"
    assert enums[0]["line_start"] == 2


def test_extract_protocol(tmp_path):
    """Test extracting a protocol."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
protocol Greetable {
    func greet() -> String
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    protocols = [s for s in symbols if s["type"] == "protocol"]
    assert len(protocols) == 1
    assert protocols[0]["name"] == "Greetable"
    assert protocols[0]["line_start"] == 2


def test_extract_extension(tmp_path):
    """Test extracting an extension."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
extension String {
    func reverse() -> String {
        return String(self.reversed())
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    extensions = [s for s in symbols if s["type"] == "extension"]
    assert len(extensions) == 1
    assert extensions[0]["name"] == "String"
    assert extensions[0]["line_start"] == 2


def test_extract_function(tmp_path):
    """Test extracting a top-level function."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
func calculate(value: Int) -> Int {
    return value * 2
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    functions = [s for s in symbols if s["type"] == "function"]
    assert len(functions) == 1
    assert functions[0]["name"] == "calculate"
    assert functions[0]["line_start"] == 2


def test_extract_method(tmp_path):
    """Test extracting a method from a class."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Calculator {
    func add(a: Int, b: Int) -> Int {
        return a + b
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "add"
    assert methods[0]["line_start"] == 3


def test_extract_property(tmp_path):
    """Test extracting a property."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var name: String
    var email: String
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    properties = [s for s in symbols if s["type"] == "property"]
    assert len(properties) == 2
    assert properties[0]["name"] == "name"
    assert properties[1]["name"] == "email"


def test_extract_multiple_symbols(sample_file):
    """Test extracting multiple symbols from sample file."""
    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(sample_file)

    assert len(symbols) > 0

    # Check for expected symbol types
    classes = [s for s in symbols if s["type"] == "class"]
    structs = [s for s in symbols if s["type"] == "struct"]
    enums = [s for s in symbols if s["type"] == "enum"]
    protocols = [s for s in symbols if s["type"] == "protocol"]
    functions = [s for s in symbols if s["type"] == "function"]

    assert len(classes) >= 1
    assert len(structs) >= 1
    assert len(enums) >= 1
    assert len(protocols) >= 1
    assert len(functions) >= 2


# ===========================
# 3. Swift-Specific Features
# ===========================


def test_static_method(tmp_path):
    """Test extracting a static method."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Factory {
    static func create() -> Factory {
        return Factory()
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "create"
    assert "static" in methods[0]["signature"]


def test_computed_property(tmp_path):
    """Test extracting a computed property."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var firstName: String
    var lastName: String
    var fullName: String {
        return "\\(firstName) \\(lastName)"
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    properties = [s for s in symbols if s["type"] == "property"]
    assert len(properties) == 3
    property_names = [p["name"] for p in properties]
    assert "firstName" in property_names
    assert "lastName" in property_names
    assert "fullName" in property_names


def test_init_method(tmp_path):
    """Test extracting an initializer."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var name: String
    init(name: String) {
        self.name = name
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "init"


def test_generic_class(tmp_path):
    """Test extracting a generic class."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Box<T> {
    var value: T
    init(value: T) {
        self.value = value
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 1
    assert classes[0]["name"] == "Box"


def test_protocol_with_requirements(tmp_path):
    """Test extracting a protocol with method requirements."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
protocol Drawable {
    func draw()
    var size: Int { get }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    protocols = [s for s in symbols if s["type"] == "protocol"]
    assert len(protocols) == 1
    assert protocols[0]["name"] == "Drawable"


def test_extension_with_protocol_conformance(tmp_path):
    """Test extracting an extension with protocol conformance."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {}

extension User: Equatable {
    static func == (lhs: User, rhs: User) -> Bool {
        return true
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    extensions = [s for s in symbols if s["type"] == "extension"]
    assert len(extensions) == 1
    assert extensions[0]["name"] == "User"


def test_nested_types(tmp_path):
    """Test extracting nested types (currently extracts outer only)."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Outer {
    struct Inner {
        var value: Int
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]

    # Currently, nested types are not recursively extracted
    # This is consistent with avoiding duplicate extraction
    assert len(classes) == 1
    assert classes[0]["name"] == "Outer"


def test_optional_types(tmp_path):
    """Test extracting properties with optional types."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var name: String?
    var age: Int?
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    properties = [s for s in symbols if s["type"] == "property"]
    assert len(properties) == 2
    assert properties[0]["name"] == "name"
    assert properties[1]["name"] == "age"


def test_closure_in_function(tmp_path):
    """Test extracting function with closure parameter."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
func process(completion: (String) -> Void) {
    completion("Done")
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    functions = [s for s in symbols if s["type"] == "function"]
    assert len(functions) == 1
    assert functions[0]["name"] == "process"


def test_inheritance(tmp_path):
    """Test extracting class with inheritance."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var name: String
}

class Admin: User {
    var role: String
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 2
    assert classes[0]["name"] == "User"
    assert classes[1]["name"] == "Admin"


def test_access_modifiers(tmp_path):
    """Test extracting methods with access modifiers."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Account {
    public func publicMethod() {}
    private func privateMethod() {}
    internal func internalMethod() {}
    fileprivate func fileprivateMethod() {}
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 4
    method_names = [m["name"] for m in methods]
    assert "publicMethod" in method_names
    assert "privateMethod" in method_names
    assert "internalMethod" in method_names
    assert "fileprivateMethod" in method_names


def test_method_with_parameters(tmp_path):
    """Test extracting method with external and internal parameter names."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Greeter {
    func greet(to name: String, with greeting: String = "Hello") -> String {
        return "\\(greeting), \\(name)!"
    }
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "greet"
    # Signature should contain parameter info
    assert "to" in methods[0]["signature"] or "name" in methods[0]["signature"]


def test_empty_class(tmp_path):
    """Test extracting empty class and struct."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class EmptyClass {}

struct EmptyStruct {}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    structs = [s for s in symbols if s["type"] == "struct"]
    assert len(classes) == 1
    assert classes[0]["name"] == "EmptyClass"
    assert len(structs) == 1
    assert structs[0]["name"] == "EmptyStruct"


# ===========================
# 4. Edge Cases
# ===========================


def test_empty_file(empty_file):
    """Test extracting from an empty file."""
    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(empty_file)

    assert symbols == []


def test_unicode_symbols(unicode_file):
    """Test extracting symbols with Unicode characters."""
    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(unicode_file)

    assert len(symbols) > 0

    classes = [s for s in symbols if s["type"] == "class"]
    functions = [s for s in symbols if s["type"] == "function"]

    assert len(classes) >= 1
    assert len(functions) >= 1


def test_file_not_found():
    """Test handling of non-existent file."""
    extractor = SwiftSymbolExtractor()
    nonexistent_file = Path("/nonexistent/file.swift")

    symbols = extractor.extract(nonexistent_file)
    assert symbols == []


def test_parser_unavailable(tmp_path):
    """Test behavior when parser is unavailable."""
    test_file = tmp_path / "test.swift"
    test_file.write_text("class User {}")

    extractor = SwiftSymbolExtractor()
    # Manually set parser as unavailable
    extractor.parser.available = False

    symbols = extractor.extract(test_file)

    assert symbols == []


def test_line_numbers(tmp_path):
    """Test that line numbers are correctly reported."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class First {
    var value: Int
}

struct Second {
    var name: String
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    structs = [s for s in symbols if s["type"] == "struct"]

    assert classes[0]["line_start"] == 2
    assert structs[0]["line_start"] == 6


def test_multiple_classes_one_file(tmp_path):
    """Test extracting multiple classes from one file."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class User {
    var name: String
}

class Admin {
    var role: String
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 2
    assert classes[0]["name"] == "User"
    assert classes[1]["name"] == "Admin"


def test_syntax_error_handling(tmp_path):
    """Test handling of files with syntax errors."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
class Broken {
    var name String  // Missing colon
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    # Should still extract what it can
    assert isinstance(symbols, list)


def test_comments_ignored(tmp_path):
    """Test that comments are ignored."""
    file = tmp_path / "test.swift"
    file.write_text(
        """
// This is a comment
class User {
    // Another comment
    var name: String
}
"""
    )

    extractor = SwiftSymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 1
    assert classes[0]["name"] == "User"


# ===========================
# 5. Integration Test
# ===========================


def test_integration_with_repository_map(sample_file):
    """Test integration with SymbolExtractor dispatcher."""
    from clauxton.intelligence.symbol_extractor import SymbolExtractor

    dispatcher = SymbolExtractor()
    symbols = dispatcher.extract(sample_file, "swift")

    assert len(symbols) > 0
    assert all(isinstance(s, dict) for s in symbols)
    assert all("name" in s for s in symbols)
    assert all("type" in s for s in symbols)
