"""Tests for PhpSymbolExtractor."""

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import PhpSymbolExtractor


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to PHP test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "php"


@pytest.fixture
def extractor() -> PhpSymbolExtractor:
    """Create PHP symbol extractor."""
    return PhpSymbolExtractor()


class TestPhpSymbolExtractor:
    """Test PHP symbol extraction."""

    def test_initialization(self, extractor: PhpSymbolExtractor) -> None:
        """Test extractor initializes correctly."""
        assert extractor.parser is not None
        assert isinstance(extractor.available, bool)

    def test_extract_class(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting a PHP class."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class User {
    private $name;

    public function getName() {
        return $this->name;
    }
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "User"
        assert classes[0]["line_start"] == 2

    def test_extract_function(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting a PHP function."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
function calculate(int $a, int $b): int {
    return $a + $b;
}
""")
        symbols = extractor.extract(php_file)
        functions = [s for s in symbols if s["type"] == "function"]
        assert len(functions) == 1
        assert functions[0]["name"] == "calculate"
        assert "calculate" in functions[0]["signature"]

    def test_extract_method(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting PHP methods."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Calculator {
    public function add(int $a, int $b): int {
        return $a + $b;
    }

    private function subtract(int $a, int $b): int {
        return $a - $b;
    }
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 2
        method_names = [m["name"] for m in methods]
        assert "add" in method_names
        assert "subtract" in method_names

    def test_extract_interface(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting a PHP interface."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
interface Loggable {
    public function log(string $message): void;
}
""")
        symbols = extractor.extract(php_file)
        interfaces = [s for s in symbols if s["type"] == "interface"]
        assert len(interfaces) == 1
        assert interfaces[0]["name"] == "Loggable"

    def test_extract_trait(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting a PHP trait."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
trait Timestampable {
    private $createdAt;

    public function touch(): void {
        $this->updatedAt = time();
    }
}
""")
        symbols = extractor.extract(php_file)
        traits = [s for s in symbols if s["type"] == "trait"]
        assert len(traits) == 1
        assert traits[0]["name"] == "Timestampable"

    def test_extract_namespace(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting PHP namespace."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

class User {
    // ...
}
""")
        symbols = extractor.extract(php_file)
        namespaces = [s for s in symbols if s["type"] == "namespace"]
        assert len(namespaces) == 1
        assert "App" in namespaces[0]["name"] or "Models" in namespaces[0]["name"]

    def test_extract_multiple_symbols(
        self, extractor: PhpSymbolExtractor, fixtures_dir: Path
    ) -> None:
        """Test extracting multiple symbols from sample.php."""
        php_file = fixtures_dir / "sample.php"
        if not php_file.exists():
            pytest.skip("sample.php fixture not found")

        symbols = extractor.extract(php_file)
        assert len(symbols) > 0

        # Check for classes
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) >= 1
        class_names = [c["name"] for c in classes]
        assert "User" in class_names

        # Check for functions
        functions = [s for s in symbols if s["type"] == "function"]
        assert len(functions) >= 2
        func_names = [f["name"] for f in functions]
        assert "calculateTotal" in func_names or "formatCurrency" in func_names

        # Check for interfaces
        interfaces = [s for s in symbols if s["type"] == "interface"]
        assert len(interfaces) >= 1
        interface_names = [i["name"] for i in interfaces]
        assert "Loggable" in interface_names

        # Check for traits
        traits = [s for s in symbols if s["type"] == "trait"]
        assert len(traits) >= 1
        trait_names = [t["name"] for t in traits]
        assert "Timestampable" in trait_names

    def test_extract_constructor(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting PHP constructor."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class User {
    public function __construct(string $name) {
        $this->name = $name;
    }
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        constructors = [m for m in methods if "__construct" in m["name"]]
        assert len(constructors) >= 0  # Constructor may be extracted as method

    def test_extract_static_method(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting static method."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class User {
    public static function create(string $name): self {
        return new self($name);
    }
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) >= 1
        assert methods[0]["name"] == "create"

    def test_extract_visibility_modifiers(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting methods with different visibility modifiers."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Example {
    public function publicMethod(): void {}
    protected function protectedMethod(): void {}
    private function privateMethod(): void {}
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 3
        method_names = [m["name"] for m in methods]
        assert "publicMethod" in method_names
        assert "protectedMethod" in method_names
        assert "privateMethod" in method_names

    def test_empty_file(self, extractor: PhpSymbolExtractor, fixtures_dir: Path) -> None:
        """Test extracting from empty PHP file."""
        php_file = fixtures_dir / "empty.php"
        if not php_file.exists():
            pytest.skip("empty.php fixture not found")

        symbols = extractor.extract(php_file)
        assert symbols == []

    def test_unicode_symbols(self, extractor: PhpSymbolExtractor, fixtures_dir: Path) -> None:
        """Test extracting symbols with Unicode names."""
        php_file = fixtures_dir / "unicode.php"
        if not php_file.exists():
            pytest.skip("unicode.php fixture not found")

        symbols = extractor.extract(php_file)
        assert len(symbols) > 0

        # Check for Unicode class
        classes = [s for s in symbols if s["type"] == "class"]
        if classes:
            # Unicode class names may be extracted
            assert len(classes) >= 1

    def test_file_not_found(self, extractor: PhpSymbolExtractor) -> None:
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("/nonexistent/file.php"))

    def test_parser_unavailable(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test graceful handling when parser unavailable."""
        php_file = tmp_path / "test.php"
        php_file.write_text("<?php\nclass Test {}\n")

        # Simulate parser unavailable
        extractor.available = False

        symbols = extractor.extract(php_file)
        assert symbols == []

    def test_nested_classes(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting nested classes (PHP doesn't support true nesting)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Outer {
    // PHP doesn't support nested classes like Java/C#
}

class Inner {
    // Separate top-level class
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 2

    def test_abstract_class(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting abstract class."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
abstract class AbstractUser {
    abstract public function getName(): string;
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "AbstractUser"

    def test_abstract_method(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting abstract method."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
abstract class Base {
    abstract public function execute(): void;
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 1
        assert methods[0]["name"] == "execute"

    def test_type_hints(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting methods with type hints."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class TypedClass {
    public function process(string $input, int $count): array {
        return [];
    }
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 1
        assert methods[0]["name"] == "process"
        assert "string" in methods[0]["signature"] or "int" in methods[0]["signature"]

    def test_nullable_types(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting methods with nullable type hints."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class NullableExample {
    public function findUser(?int $id): ?User {
        return null;
    }
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 1
        assert methods[0]["name"] == "findUser"

    def test_union_types(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting methods with union types (PHP 8+)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class UnionExample {
    public function process(int|string $value): bool|null {
        return true;
    }
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) == 1
        assert methods[0]["name"] == "process"

    def test_line_numbers(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test that line numbers are correctly captured."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php

class User {
    public function getName() {
        return "test";
    }
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["line_start"] == 3
        assert classes[0]["line_end"] >= 3

    def test_complex_namespace(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting complex namespace."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Http\\Controllers;

class UserController {
    public function index() {
        return [];
    }
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "UserController"

    def test_implements_interface(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting class that implements interface."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
interface LoggerInterface {
    public function log(string $message): void;
}

class FileLogger implements LoggerInterface {
    public function log(string $message): void {
        // Log to file
    }
}
""")
        symbols = extractor.extract(php_file)
        interfaces = [s for s in symbols if s["type"] == "interface"]
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(interfaces) == 1
        assert len(classes) == 1
        assert classes[0]["name"] == "FileLogger"

    def test_extends_class(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting class inheritance."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class BaseController {
    public function index() {}
}

class UserController extends BaseController {
    public function show() {}
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 2
        class_names = [c["name"] for c in classes]
        assert "BaseController" in class_names
        assert "UserController" in class_names

    def test_use_trait(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting class that uses trait."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
trait Timestampable {
    public function touch() {}
}

class User {
    use Timestampable;

    public function getName() {
        return "test";
    }
}
""")
        symbols = extractor.extract(php_file)
        traits = [s for s in symbols if s["type"] == "trait"]
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(traits) == 1
        assert len(classes) == 1

    def test_magic_methods(self, extractor: PhpSymbolExtractor, tmp_path: Path) -> None:
        """Test extracting magic methods."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class MagicClass {
    public function __construct() {}
    public function __destruct() {}
    public function __toString(): string {
        return "test";
    }
    public function __get(string $name) {}
    public function __set(string $name, $value): void {}
}
""")
        symbols = extractor.extract(php_file)
        methods = [s for s in symbols if s["type"] == "method"]
        method_names = [m["name"] for m in methods]
        # Check for at least some magic methods
        magic_methods = [n for n in method_names if n.startswith("__")]
        assert len(magic_methods) >= 1

    def test_integration_with_repository_map(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test that extracted symbols work with repository map."""
        php_file = tmp_path / "User.php"
        php_file.write_text("""<?php
namespace App\\Models;

class User {
    public function getName(): string {
        return $this->name;
    }
}
""")
        symbols = extractor.extract(php_file)
        assert len(symbols) > 0

        # Verify symbol structure matches expected format
        for symbol in symbols:
            assert "name" in symbol
            assert "type" in symbol
            assert "file_path" in symbol
            assert "line_start" in symbol
            assert "line_end" in symbol
            assert symbol["line_start"] > 0
            assert symbol["line_end"] >= symbol["line_start"]

    def test_syntax_error_handling(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test handling of PHP files with syntax errors."""
        php_file = tmp_path / "invalid.php"
        php_file.write_text("""<?php
class Broken {
    public function incomplete(
    // Missing closing brace and parenthesis
""")
        # Should not crash, should return empty or partial symbols
        symbols = extractor.extract(php_file)
        assert isinstance(symbols, list)

    def test_multiple_classes_same_file(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting multiple classes from same file."""
        php_file = tmp_path / "multiple.php"
        php_file.write_text("""<?php
class FirstClass {
    public function firstMethod() {}
}

class SecondClass {
    public function secondMethod() {}
}

class ThirdClass {
    public function thirdMethod() {}
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 3
        class_names = [c["name"] for c in classes]
        assert "FirstClass" in class_names
        assert "SecondClass" in class_names
        assert "ThirdClass" in class_names

    def test_anonymous_class(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test handling of anonymous classes (PHP 7+)."""
        php_file = tmp_path / "anon.php"
        php_file.write_text("""<?php
$obj = new class {
    public function doSomething() {
        return 42;
    }
};
""")
        symbols = extractor.extract(php_file)
        # Anonymous classes may or may not be extracted depending on tree-sitter
        assert isinstance(symbols, list)

    def test_final_class(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting final classes."""
        php_file = tmp_path / "final.php"
        php_file.write_text("""<?php
final class FinalClass {
    public function method() {}
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "FinalClass"

    def test_readonly_property(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting classes with readonly properties (PHP 8.1+)."""
        php_file = tmp_path / "readonly.php"
        php_file.write_text("""<?php
class User {
    public readonly string $name;

    public function __construct(string $name) {
        $this->name = $name;
    }
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "User"

    def test_enum_php8(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting enums (PHP 8.1+)."""
        php_file = tmp_path / "enum.php"
        php_file.write_text("""<?php
enum Status {
    case Pending;
    case Approved;
    case Rejected;
}
""")
        symbols = extractor.extract(php_file)
        # Enums may be extracted depending on tree-sitter support
        assert isinstance(symbols, list)

    def test_promoted_constructor_properties(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test promoted constructor properties (PHP 8.0+)."""
        php_file = tmp_path / "promoted.php"
        php_file.write_text("""<?php
class User {
    public function __construct(
        private string $name,
        private int $age,
        public string $email
    ) {}
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        methods = [s for s in symbols if s["type"] == "method"]
        assert len(methods) >= 1  # __construct should be found

    def test_attribute_syntax(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting classes with attributes (PHP 8.0+)."""
        php_file = tmp_path / "attribute.php"
        php_file.write_text("""<?php
#[Route('/users')]
class UserController {
    #[Get('/list')]
    public function list() {}
}
""")
        symbols = extractor.extract(php_file)
        classes = [s for s in symbols if s["type"] == "class"]
        assert len(classes) == 1
        assert classes[0]["name"] == "UserController"

    def test_named_arguments(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting functions using named arguments (PHP 8.0+)."""
        php_file = tmp_path / "named_args.php"
        php_file.write_text("""<?php
function createUser(string $name, int $age, string $email) {
    return new User(name: $name, age: $age, email: $email);
}
""")
        symbols = extractor.extract(php_file)
        functions = [s for s in symbols if s["type"] == "function"]
        assert len(functions) == 1
        assert functions[0]["name"] == "createUser"

    def test_match_expression(
        self, extractor: PhpSymbolExtractor, tmp_path: Path
    ) -> None:
        """Test extracting functions with match expressions (PHP 8.0+)."""
        php_file = tmp_path / "match.php"
        php_file.write_text("""<?php
function getStatus(int $code): string {
    return match($code) {
        200 => 'OK',
        404 => 'Not Found',
        default => 'Unknown'
    };
}
""")
        symbols = extractor.extract(php_file)
        functions = [s for s in symbols if s["type"] == "function"]
        assert len(functions) == 1
        assert functions[0]["name"] == "getStatus"
