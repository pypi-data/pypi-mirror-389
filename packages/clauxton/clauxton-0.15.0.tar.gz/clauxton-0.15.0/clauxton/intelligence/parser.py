"""
Multi-language parser using tree-sitter.

This module provides parsers for extracting AST nodes from source files.
Supports Python, JavaScript (ES6+), TypeScript, Go, Rust, C++, Java, C#, PHP,
Ruby, Swift, and Kotlin.

Example:
    >>> from clauxton.intelligence.parser import (
    ...     PythonParser, JavaScriptParser, TypeScriptParser, GoParser,
    ...     RustParser, CppParser, JavaParser, CSharpParser, PhpParser, RubyParser,
    ...     SwiftParser, KotlinParser
    ... )
    >>> py_parser = PythonParser()
    >>> js_parser = JavaScriptParser()
    >>> ts_parser = TypeScriptParser()
    >>> go_parser = GoParser()
    >>> rust_parser = RustParser()
    >>> cpp_parser = CppParser()
    >>> java_parser = JavaParser()
    >>> cs_parser = CSharpParser()
    >>> php_parser = PhpParser()
    >>> rb_parser = RubyParser()
    >>> swift_parser = SwiftParser()
    >>> kt_parser = KotlinParser()
    >>> py_tree = py_parser.parse(Path("script.py"))
    >>> js_tree = js_parser.parse(Path("script.js"))
    >>> ts_tree = ts_parser.parse(Path("script.ts"))
    >>> go_tree = go_parser.parse(Path("main.go"))
    >>> rust_tree = rust_parser.parse(Path("main.rs"))
    >>> cpp_tree = cpp_parser.parse(Path("main.cpp"))
    >>> java_tree = java_parser.parse(Path("Main.java"))
    >>> cs_tree = cs_parser.parse(Path("Program.cs"))
    >>> php_tree = php_parser.parse(Path("script.php"))
    >>> rb_tree = rb_parser.parse(Path("script.rb"))
    >>> swift_tree = swift_parser.parse(Path("Main.swift"))
    >>> kt_tree = kt_parser.parse(Path("Main.kt"))
"""
# type: ignore  # tree-sitter has complex types

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BaseParser:
    """Base class for language parsers."""

    def __init__(self, language_module: Any) -> None:
        """
        Initialize parser with tree-sitter language.

        Args:
            language_module: tree-sitter language module (e.g., tree_sitter_python)
        """
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            from tree_sitter import Language, Parser

            self.language = Language(language_module.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
        except ImportError as e:
            logger.warning(f"{self.__class__.__name__} not available: {e}")

    def parse(self, file_path: Path) -> Optional[Any]:
        """
        Parse source file and return AST.

        Args:
            file_path: Path to source file

        Returns:
            tree-sitter Tree object or None if parser unavailable

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning(f"{self.__class__.__name__} not available")
            return None

        with open(file_path, "rb") as f:
            source_code = f.read()

        tree = self.parser.parse(source_code)  # type: ignore
        logger.debug(f"Parsed {file_path} with {self.__class__.__name__}")
        return tree


class PythonParser(BaseParser):
    """
    Python parser using tree-sitter.

    Parses Python source files and returns AST for symbol extraction.
    """

    def __init__(self) -> None:
        """Initialize Python parser."""
        try:
            import tree_sitter_python as tspython
            super().__init__(tspython)
        except ImportError:
            logger.warning("tree-sitter-python not available")
            self.available = False


class JavaScriptParser(BaseParser):
    """
    JavaScript/ES6+ parser using tree-sitter.

    Parses JavaScript source files and returns AST for symbol extraction.
    Supports:
    - ES6 Classes
    - Arrow functions
    - Async/await
    - Import/export statements
    """

    def __init__(self) -> None:
        """Initialize JavaScript parser."""
        try:
            import tree_sitter_javascript as tsjs
            super().__init__(tsjs)
        except ImportError:
            logger.warning("tree-sitter-javascript not available")
            self.available = False


class TypeScriptParser(BaseParser):
    """
    TypeScript parser using tree-sitter.

    Parses TypeScript source files and returns AST for symbol extraction.
    Supports:
    - Interfaces
    - Type aliases
    - Classes with type annotations
    - Functions with type signatures
    - Generics
    - Arrow functions
    - Import/export statements
    """

    def __init__(self) -> None:
        """Initialize TypeScript parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_typescript as tsts
            from tree_sitter import Language, Parser

            # Use TypeScript language (not TSX)
            self.language = Language(tsts.language_typescript())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("TypeScriptParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-typescript not available: {e}")
            self.available = False


class GoParser(BaseParser):
    """
    Go parser using tree-sitter.

    Parses Go source files and returns AST for symbol extraction.
    Supports:
    - Functions
    - Methods (with pointer/value receivers)
    - Structs
    - Interfaces
    - Type aliases
    - Generics (Go 1.18+)
    """

    def __init__(self) -> None:
        """Initialize Go parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_go as tsgo
            from tree_sitter import Language, Parser

            self.language = Language(tsgo.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("GoParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-go not available: {e}")
            self.available = False


class RustParser(BaseParser):
    """
    Rust parser using tree-sitter.

    Parses Rust source files and returns AST for symbol extraction.
    Supports:
    - Functions (fn)
    - Methods (impl blocks)
    - Structs
    - Traits
    - Enums
    - Type aliases
    - Generics
    """

    def __init__(self) -> None:
        """Initialize Rust parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_rust as tsrust
            from tree_sitter import Language, Parser

            self.language = Language(tsrust.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("RustParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-rust not available: {e}")
            self.available = False


class CppParser(BaseParser):
    """
    C++ parser using tree-sitter.

    Parses C++ source files and returns AST for symbol extraction.
    Supports:
    - Functions
    - Classes (with inheritance)
    - Methods (including constructors/destructors)
    - Structs
    - Namespaces
    - Templates
    """

    def __init__(self) -> None:
        """Initialize C++ parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_cpp as tscpp
            from tree_sitter import Language, Parser

            self.language = Language(tscpp.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("CppParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-cpp not available: {e}")
            self.available = False


class JavaParser(BaseParser):
    """
    Java parser using tree-sitter.

    Parses Java source files and returns AST for symbol extraction.
    Supports:
    - Classes
    - Interfaces
    - Methods (including constructors)
    - Enums
    - Annotations
    - Generics
    """

    def __init__(self) -> None:
        """Initialize Java parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_java as tsjava
            from tree_sitter import Language, Parser

            self.language = Language(tsjava.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("JavaParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-java not available: {e}")
            self.available = False


class CSharpParser(BaseParser):
    """
    C# parser using tree-sitter.

    Parses C# source files and returns AST for symbol extraction.
    Supports:
    - Classes
    - Interfaces
    - Methods (including constructors)
    - Properties
    - Enums
    - Delegates
    - Namespaces
    """

    def __init__(self) -> None:
        """Initialize C# parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_c_sharp as tscsharp
            from tree_sitter import Language, Parser

            self.language = Language(tscsharp.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("CSharpParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-c-sharp not available: {e}")
            self.available = False


class PhpParser(BaseParser):
    """
    PHP parser using tree-sitter.

    Parses PHP source files and returns AST for symbol extraction.
    Supports:
    - Classes
    - Functions
    - Methods
    - Interfaces
    - Traits
    - Namespaces
    """

    def __init__(self) -> None:
        """Initialize PHP parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_php as tsphp
            from tree_sitter import Language, Parser

            self.language = Language(tsphp.language_php())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("PhpParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-php not available: {e}")
            self.available = False


class RubyParser(BaseParser):
    """
    Ruby parser using tree-sitter.

    Parses Ruby source files and returns AST for symbol extraction.
    Supports:
    - Classes
    - Modules
    - Methods (instance methods)
    - Singleton methods (class methods)
    - Constants
    - attr_accessor/attr_reader/attr_writer
    """

    def __init__(self) -> None:
        """Initialize Ruby parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_ruby as tsruby
            from tree_sitter import Language, Parser

            self.language = Language(tsruby.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("RubyParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-ruby not available: {e}")
            self.available = False


class SwiftParser(BaseParser):
    """
    Swift parser using tree-sitter.

    Parses Swift source files and returns AST for symbol extraction.
    Supports:
    - Classes
    - Structs
    - Enums
    - Protocols
    - Extensions
    - Functions
    """

    def __init__(self) -> None:
        """Initialize Swift parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_swift as tsswift
            from tree_sitter import Language, Parser

            self.language = Language(tsswift.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("SwiftParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-swift not available: {e}")
            self.available = False


class KotlinParser(BaseParser):
    """
    Kotlin parser using tree-sitter.

    Parses Kotlin source files and returns AST for symbol extraction.
    Supports:
    - Classes (regular, data, sealed)
    - Interfaces
    - Objects (singleton, companion)
    - Functions (regular, extension, suspend)
    - Properties
    - Enums
    """

    def __init__(self) -> None:
        """Initialize Kotlin parser."""
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_kotlin as tskotlin
            from tree_sitter import Language, Parser

            self.language = Language(tskotlin.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("KotlinParser initialized successfully")
        except ImportError as e:
            logger.warning(f"tree-sitter-kotlin not available: {e}")
            self.available = False
