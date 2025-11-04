"""
Symbol extraction from source files using tree-sitter.

This module extracts code symbols (functions, classes, methods) from source files
using tree-sitter for accurate AST parsing, with fallback to Python's built-in
ast module if tree-sitter is unavailable.

Example:
    >>> from clauxton.intelligence import PythonSymbolExtractor
    >>> extractor = PythonSymbolExtractor()
    >>> symbols = extractor.extract(Path("myfile.py"))
    >>> for symbol in symbols:
    ...     print(f"{symbol['name']} ({symbol['type']})")
"""
# type: ignore  # tree-sitter has complex types

import logging
from pathlib import Path
from typing import Dict, List, Optional

from clauxton.intelligence.parser import (
    CppParser,
    GoParser,
    JavaParser,
    PythonParser,
    RubyParser,
    RustParser,
    TypeScriptParser,
)

logger = logging.getLogger(__name__)


class SymbolExtractor:
    """
    Multi-language symbol extractor.

    Dispatches to language-specific extractors based on file extension.
    Supports Python, JavaScript, TypeScript, Go, Rust, C++, Java, C#, PHP, Ruby,
    Swift, and Kotlin (v0.11.0).
    """

    def __init__(self) -> None:
        """Initialize symbol extractor with language-specific extractors."""
        self.extractors: Dict[str, any] = {  # type: ignore
            "python": PythonSymbolExtractor(),
            "javascript": JavaScriptSymbolExtractor(),
            "typescript": TypeScriptSymbolExtractor(),
            "go": GoSymbolExtractor(),
            "rust": RustSymbolExtractor(),
            "cpp": CppSymbolExtractor(),
            "java": JavaSymbolExtractor(),
            "csharp": CSharpSymbolExtractor(),
            "php": PhpSymbolExtractor(),
            "ruby": RubySymbolExtractor(),
            "swift": SwiftSymbolExtractor(),
            "kotlin": KotlinSymbolExtractor(),
        }
        logger.debug(f"SymbolExtractor initialized with {len(self.extractors)} languages")

    def extract(self, file_path: Path, language: str) -> List[Dict]:
        """
        Extract symbols from a file.

        Args:
            file_path: Path to source file
            language: Programming language ("python", "javascript", etc.)

        Returns:
            List of symbol dictionaries with keys:
                - name: Symbol name
                - type: Symbol type ("function", "class", etc.)
                - file_path: Path to file
                - line_start: Starting line number
                - line_end: Ending line number
                - docstring: Optional docstring
                - signature: Optional function signature
        """
        extractor = self.extractors.get(language)
        if not extractor:
            logger.debug(f"No extractor available for language: {language}")
            return []

        try:
            return extractor.extract(file_path)
        except Exception as e:
            logger.warning(f"Failed to extract symbols from {file_path}: {e}")
            return []


class PythonSymbolExtractor:
    """
    Extract symbols from Python files.

    Uses PythonParser (tree-sitter) for accurate parsing when available,
    with automatic fallback to Python's built-in ast module.

    Refactored in v0.11.0 to use shared parser infrastructure.
    """

    def __init__(self) -> None:
        """
        Initialize Python symbol extractor.

        Uses PythonParser for tree-sitter parsing. If unavailable, uses ast module as fallback.
        """
        self.parser = PythonParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from Python file.

        Args:
            file_path: Path to Python source file

        Returns:
            List of extracted symbols

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.available:
            return self._extract_with_tree_sitter(file_path)
        else:
            return self._extract_with_ast(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via PythonParser.

        Args:
            file_path: Path to Python file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}, falling back to ast")
            return self._extract_with_ast(file_path)

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        if node.type == "function_definition":  # type: ignore
            # Extract function
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "function",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        elif node.type == "class_definition":  # type: ignore
            # Extract class
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract docstring from function or class node.

        Args:
            node: tree-sitter Node (function_definition or class_definition)

        Returns:
            Docstring content or None
        """
        # Look for expression_statement with string as first child of body
        for child in node.children:  # type: ignore
            if child.type == "block":
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for expr_child in stmt.children:
                            if expr_child.type == "string":
                                # Remove quotes
                                text = expr_child.text.decode()  # type: ignore
                                return text.strip('"""\'\'\'')  # type: ignore
                        break
                break
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function signature.

        Args:
            node: tree-sitter Node (function_definition)

        Returns:
            Function signature string or None
        """
        try:
            # Get everything before the colon
            text = node.text.decode()  # type: ignore
            signature = text.split(":")[0].strip()
            return signature  # type: ignore
        except Exception:
            return None

    def _extract_with_ast(self, file_path: Path) -> List[Dict]:
        """
        Fallback extraction using Python's built-in ast module.

        Args:
            file_path: Path to Python file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with ast module")

        import ast

        with open(file_path, encoding="utf-8") as f:
            try:
                source_code = f.read()
                tree = ast.parse(source_code, filename=str(file_path))
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
                return []

        symbols: List[Dict] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({
                    "name": node.name,
                    "type": "function",
                    "file_path": str(file_path),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node),
                    "signature": None,  # Not available from ast
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "file_path": str(file_path),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node),
                })

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols


class JavaScriptSymbolExtractor:
    """
    Extract symbols from JavaScript files.

    Supports ES6+ syntax including:
    - Classes (class declarations)
    - Functions (function declarations, arrow functions, async functions)
    - Method definitions
    - Export statements
    """

    def __init__(self) -> None:
        """
        Initialize JavaScript symbol extractor.

        Attempts to load tree-sitter-javascript. If unavailable, extraction will fail.
        """
        self.available = False
        self.parser = None  # type: ignore
        self.language = None  # type: ignore

        try:
            import tree_sitter_javascript as tsjs
            from tree_sitter import Language, Parser

            self.language = Language(tsjs.language())
            self.parser = Parser(self.language)
            self.available = True
            logger.info("tree-sitter-javascript initialized successfully")
        except ImportError as e:
            logger.warning(
                f"tree-sitter-javascript not available ({e}), "
                "JavaScript extraction will not work"
            )

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from JavaScript file.

        Args:
            file_path: Path to JavaScript source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-javascript not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter.

        Args:
            file_path: Path to JavaScript file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        with open(file_path, "rb") as f:
            source_code = f.read()

        tree = self.parser.parse(source_code)  # type: ignore
        symbols: List[Dict] = []

        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Class declaration
        if node.type == "class_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Function declaration (function foo() {})
        elif node.type == "function_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "function",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Method definition (inside class)
        elif node.type == "method_definition":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Arrow functions and function expressions (const foo = () => {} or function() {})
        elif node.type == "lexical_declaration":  # type: ignore
            # Look for variable_declarator with arrow_function or function_expression
            for child in node.children:  # type: ignore
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if name_node and value_node:
                        if value_node.type in ["arrow_function", "function_expression"]:
                            symbol = {
                                "name": name_node.text.decode(),
                                "type": "function",
                                "file_path": file_path,
                                "line_start": child.start_point[0] + 1,
                                "line_end": child.end_point[0] + 1,
                                "docstring": None,
                                "signature": None,
                            }
                            symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract JSDoc comment from function or class node.

        Args:
            node: tree-sitter Node (function_declaration, class_declaration, etc.)

        Returns:
            JSDoc content or None
        """
        # Look for comment node immediately before this node
        # In JavaScript, JSDoc is a comment node like: /** ... */
        # Note: This is a simplified implementation
        # Full JSDoc parsing would require more sophisticated logic
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function signature.

        Args:
            node: tree-sitter Node (function_declaration or method_definition)

        Returns:
            Function signature string or None
        """
        try:
            # Get the function/method declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except Exception:
            return None


class TypeScriptSymbolExtractor:
    """
    Extract symbols from TypeScript files.

    Uses TypeScriptParser (tree-sitter) for accurate parsing.
    Supports:
    - Interfaces
    - Type aliases
    - Classes with type annotations
    - Functions with type signatures
    - Arrow functions
    - Generics
    - Methods

    Based on JavaScriptSymbolExtractor with TypeScript-specific additions.
    """

    def __init__(self) -> None:
        """
        Initialize TypeScript symbol extractor.

        Uses TypeScriptParser for tree-sitter parsing.
        """
        self.parser = TypeScriptParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from TypeScript file.

        Args:
            file_path: Path to TypeScript source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-typescript not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via TypeScriptParser.

        Args:
            file_path: Path to TypeScript file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Interface declaration (TypeScript-specific)
        if node.type == "interface_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "interface",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Type alias declaration (TypeScript-specific)
        elif node.type == "type_alias_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "type_alias",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Class declaration
        elif node.type == "class_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Function declaration (function foo() {})
        elif node.type == "function_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "function",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Method definition (class methods)
        elif node.type == "method_definition":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Lexical declaration (const/let with arrow/function expression)
        elif node.type == "lexical_declaration":  # type: ignore
            # Look for arrow_function or function_expression
            for child in node.children:  # type: ignore
                if child.type == "variable_declarator":  # type: ignore
                    name_node = child.child_by_field_name("name")  # type: ignore
                    value_node = child.child_by_field_name("value")  # type: ignore
                    if name_node and value_node:
                        if value_node.type in ["arrow_function", "function_expression"]:  # type: ignore
                            symbol = {
                                "name": name_node.text.decode(),  # type: ignore
                                "type": "function",
                                "file_path": file_path,
                                "line_start": node.start_point[0] + 1,  # type: ignore
                                "line_end": node.end_point[0] + 1,  # type: ignore
                                "docstring": self._extract_docstring(node),
                                "signature": self._extract_signature(value_node),
                            }
                            symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract docstring/JSDoc from node.

        Args:
            node: tree-sitter Node

        Returns:
            Docstring content or None (currently returns None, JSDoc parsing not implemented)
        """
        # TODO: Implement JSDoc/TSDoc extraction
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function/method signature.

        Args:
            node: tree-sitter Node (function/method node)

        Returns:
            Function signature string or None
        """
        try:
            # Get the function/method declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except Exception:
            return None


class GoSymbolExtractor:
    """
    Extract symbols from Go files.

    Uses GoParser (tree-sitter) for accurate parsing.
    Supports:
    - Functions
    - Methods (with pointer/value receivers)
    - Structs
    - Interfaces
    - Type aliases
    - Generics (Go 1.18+)

    Go-specific features:
    - Pointer receivers (func (r *Type) Method())
    - Value receivers (func (r Type) Method())
    - Embedded structs
    - Interface declarations
    """

    def __init__(self) -> None:
        """
        Initialize Go symbol extractor.

        Uses GoParser for tree-sitter parsing.
        """
        self.parser = GoParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from Go file.

        Args:
            file_path: Path to Go source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-go not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via GoParser.

        Args:
            file_path: Path to Go file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Type declaration (struct, interface, type alias)
        if node.type == "type_declaration":  # type: ignore
            self._extract_type_declaration(node, symbols, file_path)

        # Function declaration
        elif node.type == "function_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "function",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Method declaration (with receiver)
        elif node.type == "method_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                receiver = self._extract_receiver(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                    "receiver": receiver,
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_type_declaration(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Extract type declaration (struct, interface, type alias).

        Args:
            node: type_declaration node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # type_declaration has type_spec child
        for child in node.children:  # type: ignore
            if child.type == "type_spec":  # type: ignore
                name_node = child.child_by_field_name("name")  # type: ignore
                type_node = child.child_by_field_name("type")  # type: ignore

                if name_node and type_node:
                    name = name_node.text.decode()  # type: ignore

                    # Determine type: struct, interface, or type_alias
                    if type_node.type == "struct_type":  # type: ignore
                        symbol_type = "struct"
                    elif type_node.type == "interface_type":  # type: ignore
                        symbol_type = "interface"
                    else:
                        symbol_type = "type_alias"

                    symbol = {
                        "name": name,
                        "type": symbol_type,
                        "file_path": file_path,
                        "line_start": node.start_point[0] + 1,  # type: ignore
                        "line_end": node.end_point[0] + 1,  # type: ignore
                        "docstring": self._extract_docstring(node),
                    }
                    symbols.append(symbol)

    def _extract_receiver(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract method receiver (e.g., "*User" or "User").

        Args:
            node: method_declaration node

        Returns:
            Receiver type string or None
        """
        try:
            receiver_node = node.child_by_field_name("receiver")  # type: ignore
            if receiver_node:
                # parameter_list -> parameter_declaration -> type
                for child in receiver_node.children:  # type: ignore
                    if child.type == "parameter_declaration":  # type: ignore
                        # Get type (could be pointer_type or type_identifier)
                        for subchild in child.children:  # type: ignore
                            if subchild.type in ["pointer_type", "type_identifier"]:  # type: ignore
                                return subchild.text.decode()  # type: ignore
            return None
        except Exception:
            return None

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract doc comment from node.

        Go doc comments are regular comments preceding a declaration.

        Args:
            node: tree-sitter Node

        Returns:
            Docstring content or None
        """
        # TODO: Implement Go doc comment extraction
        # Go doc comments appear as comment nodes before declarations
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function/method signature.

        Args:
            node: tree-sitter Node (function/method node)

        Returns:
            Function signature string or None
        """
        try:
            # Get the function/method declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except Exception:
            return None

class RustSymbolExtractor:
    """
    Extract symbols from Rust files.

    Uses RustParser (tree-sitter) for accurate parsing.
    Supports:
    - Functions (fn)
    - Methods (impl blocks)
    - Structs
    - Traits
    - Enums
    - Type aliases
    - Generics

    Rust-specific features:
    - Self receivers (&self, &mut self, self)
    - Associated functions (no self)
    - Trait implementations
    - Generic type parameters
    """

    def __init__(self) -> None:
        """
        Initialize Rust symbol extractor.

        Uses RustParser for tree-sitter parsing.
        """
        self.parser = RustParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from Rust file.

        Args:
            file_path: Path to Rust source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-rust not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via RustParser.

        Args:
            file_path: Path to Rust file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Function definition (fn foo() {})
        if node.type == "function_item":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "function",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Struct definition (struct User {})
        elif node.type == "struct_item":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "struct",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Enum definition (enum Status {})
        elif node.type == "enum_item":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "enum",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Trait definition (trait Display {})
        elif node.type == "trait_item":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "trait",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Type alias (type Result<T> = std::result::Result<T, Error>)
        elif node.type == "type_item":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "type_alias",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Impl block (impl User {} or impl Display for User {})
        elif node.type == "impl_item":  # type: ignore
            # Extract methods from impl block
            self._extract_impl_methods(node, symbols, file_path)
            # Don't recurse into impl_item children, we've already handled them
            return

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_impl_methods(  # type: ignore
        self, node: any, symbols: List[Dict], file_path: str  # type: ignore
    ) -> None:
        """
        Extract methods from impl block.

        Args:
            node: impl_item node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Get impl type (struct/trait being implemented)
        impl_type = self._extract_impl_type(node)

        # Walk children to find function_item nodes (methods)
        for child in node.children:  # type: ignore
            if child.type == "declaration_list":  # type: ignore
                for method_node in child.children:  # type: ignore
                    if method_node.type == "function_item":  # type: ignore
                        name_node = method_node.child_by_field_name("name")  # type: ignore
                        if name_node:
                            receiver = self._extract_receiver(method_node)
                            symbol = {
                                "name": name_node.text.decode(),  # type: ignore
                                "type": "method",
                                "file_path": file_path,
                                "line_start": method_node.start_point[0] + 1,  # type: ignore
                                "line_end": method_node.end_point[0] + 1,  # type: ignore
                                "docstring": self._extract_docstring(method_node),
                                "signature": self._extract_signature(method_node),
                                "receiver": receiver,
                                "impl_type": impl_type,
                            }
                            symbols.append(symbol)

    def _extract_impl_type(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract type from impl block (e.g., User from impl User {}).

        Args:
            node: impl_item node

        Returns:
            Type name or None
        """
        try:
            type_node = node.child_by_field_name("type")  # type: ignore
            if type_node:
                return type_node.text.decode()  # type: ignore
            return None
        except Exception:
            return None

    def _extract_receiver(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract method receiver (e.g., &self, &mut self, self).

        Args:
            node: function_item node (method)

        Returns:
            Receiver type string or None
        """
        try:
            # Look for parameters node
            params_node = node.child_by_field_name("parameters")  # type: ignore
            if params_node:
                # Check first parameter for self
                for child in params_node.children:  # type: ignore
                    if child.type in ["self_parameter", "parameter"]:  # type: ignore
                        param_text = child.text.decode()  # type: ignore
                        if "self" in param_text:
                            return param_text.strip()  # type: ignore
            return None
        except Exception:
            return None

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract doc comment from node.

        Rust doc comments are /// or //! comments preceding a declaration.

        Args:
            node: tree-sitter Node

        Returns:
            Docstring content or None
        """
        # TODO: Implement Rust doc comment extraction
        # Rust uses /// for outer doc comments and //! for inner doc comments
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function/method signature.

        Args:
            node: tree-sitter Node (function_item)

        Returns:
            Function signature string or None
        """
        try:
            # Get the function declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except Exception:
            return None


class CppSymbolExtractor:
    """
    Extract symbols from C++ files.

    Uses CppParser (tree-sitter) for accurate parsing.
    Supports:
    - Functions
    - Classes (with inheritance)
    - Methods (including constructors/destructors)
    - Structs
    - Namespaces
    - Templates
    - Operator overloading

    C++ specific features:
    - Constructor/destructor detection
    - Template parameter extraction
    - Namespace resolution
    - Method qualification (ClassName::method)
    """

    def __init__(self) -> None:
        """Initialize C++ symbol extractor."""
        self.parser = CppParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from C++ file.

        Args:
            file_path: Path to C++ source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-cpp not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via CppParser.

        Args:
            file_path: Path to C++ file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Function definition (int add(int a, int b) { ... })
        if node.type == "function_definition":  # type: ignore
            name_node = node.child_by_field_name("declarator")  # type: ignore
            if name_node:
                # Extract function name from declarator
                func_name = self._extract_function_name(name_node)
                if func_name:
                    symbol = {
                        "name": func_name,
                        "type": "function",
                        "file_path": file_path,
                        "line_start": node.start_point[0] + 1,  # type: ignore
                        "line_end": node.end_point[0] + 1,  # type: ignore
                        "docstring": None,  # TODO: Extract comments
                        "signature": self._extract_signature(node),
                    }
                    symbols.append(symbol)

        # Class definition (class MyClass { ... })
        elif node.type == "class_specifier":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Struct definition (struct Point { ... })
        elif node.type == "struct_specifier":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "struct",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Namespace definition (namespace utils { ... })
        elif node.type == "namespace_definition":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "namespace",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_function_name(self, declarator_node: any) -> Optional[str]:  # type: ignore
        """
        Extract function name from declarator node.

        Args:
            declarator_node: function_declarator node

        Returns:
            Function name or None
        """
        try:
            # Handle different declarator types
            if declarator_node.type == "function_declarator":  # type: ignore
                declarator = declarator_node.child_by_field_name("declarator")  # type: ignore
                if declarator:
                    return self._extract_function_name(declarator)
            elif declarator_node.type == "identifier":  # type: ignore
                return declarator_node.text.decode()  # type: ignore
            elif declarator_node.type == "qualified_identifier":  # type: ignore
                # For qualified names like ClassName::method
                name_node = declarator_node.child_by_field_name("name")  # type: ignore
                if name_node:
                    return name_node.text.decode()  # type: ignore
            elif declarator_node.type == "destructor_name":  # type: ignore
                return declarator_node.text.decode()  # type: ignore
            return None
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract function name: {e}")
            return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function signature.

        Args:
            node: tree-sitter Node (function_definition)

        Returns:
            Function signature string or None
        """
        try:
            # Get the function declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract signature: {e}")
            return None


class JavaSymbolExtractor:
    """
    Extract symbols from Java files.

    Uses JavaParser (tree-sitter) for accurate parsing.
    Supports:
    - Classes
    - Interfaces
    - Methods (including constructors)
    - Enums
    - Annotations
    - Generics

    Java specific features:
    - Constructor detection
    - Interface method signatures
    - Enum constants
    - Annotation extraction
    - Generic type parameters
    """

    def __init__(self) -> None:
        """Initialize Java symbol extractor."""
        self.parser = JavaParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from Java file.

        Args:
            file_path: Path to Java source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-java not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via JavaParser.

        Args:
            file_path: Path to Java file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Class declaration (class MyClass { ... })
        if node.type == "class_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Interface declaration (interface MyInterface { ... })
        elif node.type == "interface_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "interface",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Method declaration
        elif node.type == "method_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Constructor declaration
        elif node.type == "constructor_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "constructor",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

        # Enum declaration
        elif node.type == "enum_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "enum",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Annotation type declaration (@interface MyAnnotation)
        elif node.type == "annotation_type_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "annotation",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract Javadoc comment.

        Args:
            node: tree-sitter Node

        Returns:
            Javadoc content or None
        """
        # TODO: Implement Javadoc extraction
        # Java uses /** ... */ for documentation comments
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract method/constructor signature.

        Args:
            node: tree-sitter Node (method_declaration or constructor_declaration)

        Returns:
            Method signature string or None
        """
        try:
            # Get the method declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract signature: {e}")
            return None


class CSharpSymbolExtractor:
    """
    Extract symbols from C# files.

    Uses CSharpParser (tree-sitter) for accurate parsing.
    Supports:
    - Classes
    - Interfaces
    - Methods (including constructors)
    - Properties
    - Enums
    - Delegates
    - Namespaces

    C# specific features:
    - Property getters/setters
    - Async methods
    - Delegates
    - Namespace declarations
    - Generic type parameters
    """

    def __init__(self) -> None:
        """Initialize C# symbol extractor."""
        from clauxton.intelligence.parser import CSharpParser
        self.parser = CSharpParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from C# file.

        Args:
            file_path: Path to C# source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-c-sharp not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via CSharpParser.

        Args:
            file_path: Path to C# file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Class declaration (class MyClass { ... })
        if node.type == "class_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Interface declaration (interface IMyInterface { ... })
        elif node.type == "interface_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "interface",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Method declaration
        elif node.type == "method_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "signature": signature,
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Constructor declaration
        elif node.type == "constructor_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "constructor",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "signature": signature,
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Property declaration (public string Name { get; set; })
        elif node.type == "property_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "property",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "signature": signature,
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Enum declaration (enum Status { ... })
        elif node.type == "enum_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "enum",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Delegate declaration (public delegate void Handler(object sender, EventArgs e);)
        elif node.type == "delegate_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "delegate",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "signature": signature,
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Namespace declaration (namespace MyApp { ... })
        elif node.type == "namespace_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                # Handle both simple and qualified names (e.g., MyApp.Utils)
                name_text = name_node.text.decode()  # type: ignore
                symbol = {
                    "name": name_text,
                    "type": "namespace",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract XML documentation comment (/// or /** */) from C# node.

        Args:
            node: tree-sitter Node

        Returns:
            Docstring or None
        """
        # C# uses XML documentation comments (/// <summary>...</summary>)
        # or multi-line comments (/** ... */)
        # tree-sitter-c-sharp represents these as comment nodes
        # TODO: Implement XML doc comment extraction
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract method/property signature from node.

        Args:
            node: tree-sitter Node

        Returns:
            Method signature string or None
        """
        try:
            # Get the method/property declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract signature: {e}")
            return None


class PhpSymbolExtractor:
    """
    Extract symbols from PHP files.

    Uses PhpParser (tree-sitter) for accurate parsing.
    Supports:
    - Classes
    - Functions
    - Methods
    - Interfaces
    - Traits
    - Namespaces

    PHP specific features:
    - Namespace declarations
    - Trait usage
    - Magic methods (__construct, __destruct, etc.)
    - Visibility modifiers (public, private, protected)
    """

    def __init__(self) -> None:
        """Initialize PHP symbol extractor."""
        from clauxton.intelligence.parser import PhpParser
        self.parser = PhpParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from PHP file.

        Args:
            file_path: Path to PHP source file

        Returns:
            List of extracted symbols (empty if parser unavailable)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.available:
            logger.warning("tree-sitter-php not available, cannot extract symbols")
            return []

        return self._extract_with_tree_sitter(file_path)

    def _extract_with_tree_sitter(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols using tree-sitter via PhpParser.

        Args:
            file_path: Path to PHP file

        Returns:
            List of symbols
        """
        logger.debug(f"Extracting symbols from {file_path} with tree-sitter")

        tree = self.parser.parse(file_path)
        if not tree:
            logger.warning(f"Failed to parse {file_path}")
            return []

        symbols: List[Dict] = []
        self._walk_tree(tree.root_node, symbols, str(file_path))  # type: ignore

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path}")
        return symbols

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore
        """
        Recursively walk AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Path to file being parsed
        """
        # Class declaration (class MyClass { ... })
        if node.type == "class_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Function declaration (function myFunc() { ... })
        elif node.type == "function_definition":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "function",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "signature": signature,
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Method declaration
        elif node.type == "method_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "signature": signature,
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Interface declaration (interface MyInterface { ... })
        elif node.type == "interface_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "interface",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Trait declaration (trait MyTrait { ... })
        elif node.type == "trait_declaration":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "trait",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Namespace declaration (namespace MyNamespace;)
        elif node.type == "namespace_definition":  # type: ignore
            name_node = node.child_by_field_name("name")  # type: ignore
            if name_node:
                name_text = name_node.text.decode()  # type: ignore
                symbol = {
                    "name": name_text,
                    "type": "namespace",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract PHPDoc comment (/** ... */) from PHP node.

        Args:
            node: tree-sitter Node

        Returns:
            Docstring or None
        """
        # PHP uses PHPDoc comments (/** ... */)
        # tree-sitter-php represents these as comment nodes
        # TODO: Implement PHPDoc comment extraction
        return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore
        """
        Extract function/method signature from node.

        Args:
            node: tree-sitter Node

        Returns:
            Function signature string or None
        """
        try:
            # Get the function/method declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            # Remove trailing { if present
            if signature.endswith("{"):
                signature = signature[:-1].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract signature: {e}")
            return None


class RubySymbolExtractor:
    """
    Extract symbols from Ruby files.

    Uses RubyParser (tree-sitter) for accurate parsing.
    Supports:
    - Classes
    - Modules
    - Methods (instance methods)
    - Singleton methods (class methods using def self.method)
    - Constants
    - attr_accessor/attr_reader/attr_writer

    Ruby-specific features:
    - Modules as namespaces and mixins
    - Class inheritance (< ParentClass)
    - Module inclusion (include ModuleName)
    - attr_accessor/attr_reader/attr_writer declarations
    - Singleton methods (class methods)
    """

    def __init__(self) -> None:
        """
        Initialize Ruby symbol extractor.

        Uses RubyParser for tree-sitter parsing.
        """
        self.parser = RubyParser()
        self.available = self.parser.available

    def extract(self, file_path: Path) -> List[Dict]:
        """
        Extract symbols from Ruby file.

        Args:
            file_path: Path to Ruby source file

        Returns:
            List of extracted symbols (empty if parser unavailable)
        """
        if not self.available:
            logger.warning("RubyParser not available, cannot extract symbols")
            return []

        try:
            tree = self.parser.parse(file_path)
            if not tree:
                return []

            symbols: List[Dict] = []
            self._walk_tree(tree.root_node, symbols, str(file_path))
            return symbols

        except Exception as e:
            logger.error(f"Failed to extract symbols from {file_path}: {e}")
            return []

    def _walk_tree(self, node: any, symbols: List[Dict], file_path: str) -> None:  # type: ignore  # noqa: ANN401
        """
        Walk the AST and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append extracted symbols
            file_path: Path to source file
        """
        # Handle ERROR nodes that contain class/module definitions (for Unicode names)
        # Look for pattern: ERROR -> [ class/module keyword, ERROR with identifier ]
        if node.type == "ERROR":  # type: ignore
            # Check if first child is class or module keyword
            if len(node.children) >= 2:  # type: ignore
                first_child = node.children[0]  # type: ignore
                second_child = node.children[1]  # type: ignore

                symbol_type = None
                name_node = None

                # Pattern: class ERROR or module ERROR
                if first_child.type == "class" and second_child.type == "ERROR":  # type: ignore
                    symbol_type = "class"
                    # Look for identifier in the ERROR node
                    for subchild in second_child.children:  # type: ignore
                        if subchild.type == "identifier":
                            name_node = subchild
                            break
                elif first_child.type == "module" and second_child.type == "ERROR":  # type: ignore
                    symbol_type = "module"
                    # Look for identifier in the ERROR node
                    for subchild in second_child.children:  # type: ignore
                        if subchild.type == "identifier":
                            name_node = subchild
                            break

                # Create symbol if we found both type and name
                if symbol_type and name_node:
                    symbol = {
                        "name": name_node.text.decode(),  # type: ignore
                        "type": symbol_type,
                        "file_path": file_path,
                        "line_start": node.start_point[0] + 1,  # type: ignore
                        "line_end": node.end_point[0] + 1,  # type: ignore
                        "docstring": None,
                    }
                    symbols.append(symbol)

        # Class definition (standard case with constant names)
        elif node.type == "class":  # type: ignore
            class_node = None
            for child in node.children:  # type: ignore
                if child.type == "constant":  # type: ignore
                    class_node = child
                    break

            if class_node:
                symbol = {
                    "name": class_node.text.decode(),
                    "type": "class",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Module definition (standard case with constant names)
        elif node.type == "module":  # type: ignore
            module_node = None
            for child in node.children:  # type: ignore
                if child.type == "constant":  # type: ignore
                    module_node = child
                    break

            if module_node:
                symbol = {
                    "name": module_node.text.decode(),
                    "type": "module",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                }
                symbols.append(symbol)

        # Method definition (instance method)
        elif node.type == "method":  # type: ignore
            name_node = None
            for child in node.children:  # type: ignore
                if child.type == "identifier":  # type: ignore
                    name_node = child
                    break

            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                    "signature": signature,
                }
                symbols.append(symbol)

        # Singleton method (class method: def self.method)
        elif node.type == "singleton_method":  # type: ignore
            name_node = None
            for child in node.children:  # type: ignore
                if child.type == "identifier":  # type: ignore
                    name_node = child
                    break

            if name_node:
                signature = self._extract_signature(node)
                symbol = {
                    "name": f"self.{name_node.text.decode()}",  # type: ignore
                    "type": "singleton_method",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": None,
                    "signature": signature,
                }
                symbols.append(symbol)

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore  # noqa: ANN401
        """
        Extract method signature from method node.

        Args:
            node: tree-sitter Node (method or singleton_method)

        Returns:
            Method signature string or None
        """
        try:
            # Get the method declaration line
            text = node.text.decode()  # type: ignore
            # Get first line only (signature)
            signature = text.split("\n")[0].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract Ruby signature: {e}")
            return None


class SwiftSymbolExtractor:
    """
    Extract symbols from Swift source files using tree-sitter.

    Supports:
    - Classes
    - Structs
    - Enums
    - Protocols
    - Extensions
    - Functions
    - Methods
    - Properties (computed and stored)
    """

    def __init__(self) -> None:
        """Initialize Swift symbol extractor."""
        from clauxton.intelligence.parser import SwiftParser

        self.parser = SwiftParser()

    def extract(self, file_path: Path) -> list[dict[str, any]]:  # type: ignore  # noqa: ANN401
        """
        Extract symbols from Swift file.

        Args:
            file_path: Path to Swift file

        Returns:
            List of symbol dictionaries with keys:
                - name: Symbol name
                - type: Symbol type (class/struct/enum/protocol/extension/function/method/property)
                - file_path: Source file path
                - line_start: Starting line number
                - line_end: Ending line number
                - docstring: Documentation comment (if available)
                - signature: Full symbol signature (if applicable)
        """
        if not self.parser.available:
            logger.warning("SwiftParser not available, cannot extract symbols")
            return []

        try:
            tree = self.parser.parse(file_path)
            if tree is None:
                return []

            symbols: list[dict[str, any]] = []  # type: ignore  # noqa: ANN401
            self._walk_tree(tree.root_node, symbols, str(file_path))
            return symbols

        except Exception as e:
            logger.error(f"Failed to extract symbols from {file_path}: {e}")
            return []

    def _walk_tree(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """
        Walk AST tree and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Source file path
        """
        # Class, struct, enum, or extension declaration
        if node.type == "class_declaration":  # type: ignore
            self._extract_class_like(node, symbols, file_path)
            return  # Don't recurse into children - already handled

        # Protocol declaration
        elif node.type == "protocol_declaration":  # type: ignore
            self._extract_protocol(node, symbols, file_path)
            return  # Don't recurse into children

        # Function declaration (top-level only)
        elif node.type == "function_declaration":  # type: ignore
            # Only extract if it's a top-level function (parent is source_file)
            if node.parent and node.parent.type == "source_file":  # type: ignore
                self._extract_function(node, symbols, file_path)
                return

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_class_like(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """
        Extract class, struct, enum, or extension.

        Swift uses 'class_declaration' for all of: class, struct, enum, extension.
        We determine the type by looking at the first child keyword.
        """
        # Determine the actual type (class/struct/enum/extension)
        symbol_type = "class"  # default
        for child in node.children:  # type: ignore
            if child.type in ["class", "struct", "enum", "extension"]:  # type: ignore
                symbol_type = child.type  # type: ignore
                break

        # Get name
        name_node = node.child_by_field_name("name")  # type: ignore
        if not name_node:
            # For extension, name is in user_type
            for child in node.children:  # type: ignore
                if child.type == "user_type":  # type: ignore
                    type_id = child.child_by_field_name("name") or child.children[0]  # type: ignore
                    if type_id:
                        name_node = type_id
                        break

        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": symbol_type,
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

        # Extract methods and properties from body
        body_node = None
        for child in node.children:  # type: ignore
            if child.type in ["class_body", "enum_class_body"]:  # type: ignore
                body_node = child
                break

        if body_node:
            for child in body_node.children:  # type: ignore
                if child.type == "function_declaration":  # type: ignore
                    self._extract_method(child, symbols, file_path)
                elif child.type == "init_declaration":  # type: ignore
                    self._extract_method(child, symbols, file_path)
                elif child.type == "property_declaration":  # type: ignore
                    self._extract_property(child, symbols, file_path)

    def _extract_protocol(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract protocol declaration."""
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": "protocol",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

    def _extract_function(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract top-level function."""
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": "function",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

    def _extract_method(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract method from class/struct/enum."""
        name_node = node.child_by_field_name("name")  # type: ignore

        # For init_declaration, use "init" as the name
        if not name_node and node.type == "init_declaration":  # type: ignore
            symbol = {
                "name": "init",
                "type": "method",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)
        elif name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": "method",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

    def _extract_property(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract property declaration."""
        # Get property name from pattern_binding
        for child in node.children:  # type: ignore
            if child.type == "pattern":  # type: ignore
                name_node = child.children[0] if child.children else None  # type: ignore
                if name_node and name_node.type == "simple_identifier":
                    symbol = {
                        "name": name_node.text.decode(),  # type: ignore
                        "type": "property",
                        "file_path": file_path,
                        "line_start": node.start_point[0] + 1,  # type: ignore
                        "line_end": node.end_point[0] + 1,  # type: ignore
                        "docstring": self._extract_docstring(node),
                        "signature": self._extract_signature(node),
                    }
                    symbols.append(symbol)
                    break

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore  # noqa: ANN401
        """
        Extract documentation comment from node.

        Swift uses /// or /** */ for documentation comments.
        """
        try:
            # Look for comment before the node
            prev_sibling = node.prev_sibling  # type: ignore
            if prev_sibling and prev_sibling.type == "comment":
                comment_text = prev_sibling.text.decode()
                # Remove /// or /** */ markers
                cleaned = (
                    comment_text.replace("///", "").replace("/**", "").replace("*/", "").strip()
                )
                if cleaned:
                    return cleaned  # type: ignore
            return None
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract Swift docstring: {e}")
            return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore  # noqa: ANN401
        """
        Extract signature from node.

        Args:
            node: tree-sitter Node

        Returns:
            Signature string or None
        """
        try:
            # Get the first line of the declaration
            text = node.text.decode()  # type: ignore
            signature = text.split("\n")[0].strip()
            # Remove opening brace if present
            if "{" in signature:
                signature = signature.split("{")[0].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract Swift signature: {e}")
            return None

class KotlinSymbolExtractor:
    """
    Extract symbols from Kotlin source files using tree-sitter.

    Supports:
    - Classes (regular, data, sealed)
    - Interfaces
    - Objects (singleton, companion)
    - Functions (regular, extension, suspend)
    - Properties
    - Enums
    """

    def __init__(self) -> None:
        """Initialize Kotlin symbol extractor."""
        from clauxton.intelligence.parser import KotlinParser

        self.parser = KotlinParser()

    def extract(self, file_path: Path) -> list[dict[str, any]]:  # type: ignore  # noqa: ANN401
        """
        Extract symbols from Kotlin file.

        Args:
            file_path: Path to Kotlin file

        Returns:
            List of symbol dictionaries with keys:
                - name: Symbol name
                - type: Symbol type (class/interface/object/function/method/property/enum)
                - file_path: Source file path
                - line_start: Starting line number
                - line_end: Ending line number
                - docstring: Documentation comment (if available)
                - signature: Full symbol signature (if applicable)
        """
        if not self.parser.available:
            logger.warning("KotlinParser not available, cannot extract symbols")
            return []

        try:
            tree = self.parser.parse(file_path)
            if tree is None:
                return []

            symbols: list[dict[str, any]] = []  # type: ignore  # noqa: ANN401
            self._walk_tree(tree.root_node, symbols, str(file_path))
            return symbols

        except Exception as e:
            logger.error(f"Failed to extract symbols from {file_path}: {e}")
            return []

    def _walk_tree(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """
        Walk AST tree and extract symbols.

        Args:
            node: tree-sitter Node
            symbols: List to append symbols to
            file_path: Source file path
        """
        # Class/Interface/Enum declaration (Kotlin uses class_declaration for all)
        if node.type == "class_declaration":  # type: ignore
            # Check if it's an interface
            is_interface = any(child.type == "interface" for child in node.children)  # type: ignore
            if is_interface:
                self._extract_interface(node, symbols, file_path)
            else:
                self._extract_class(node, symbols, file_path)
            return  # Don't recurse - already handled

        # Object declaration (singleton or companion object)
        elif node.type == "object_declaration":  # type: ignore
            self._extract_object(node, symbols, file_path)
            return

        # Companion object
        elif node.type == "companion_object":  # type: ignore
            self._extract_companion_object(node, symbols, file_path)
            return

        # Function declaration (top-level only)
        elif node.type == "function_declaration":  # type: ignore
            # Only extract if it's top-level (parent is source_file)
            parent = node.parent  # type: ignore
            if parent and parent.type == "source_file":
                self._extract_function(node, symbols, file_path)
                return

        # Property declaration (top-level only)
        elif node.type == "property_declaration":  # type: ignore
            # Only extract if it's top-level
            parent = node.parent  # type: ignore
            if parent and parent.type == "source_file":
                self._extract_property(node, symbols, file_path)
                return

        # Recurse into children
        for child in node.children:  # type: ignore
            self._walk_tree(child, symbols, file_path)

    def _extract_class(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """
        Extract class (regular, data, sealed, or enum).

        Kotlin classes can have modifiers like 'data', 'sealed', 'abstract', etc.
        Enums are also class_declaration with 'enum' keyword.
        """
        # Check if it's an enum (modifiers contains 'enum' text)
        is_enum = False
        modifiers = []
        for child in node.children:  # type: ignore
            if child.type == "modifiers":  # type: ignore
                modifier_text = child.text.decode() if child.text else ""  # type: ignore
                if "enum" in modifier_text:
                    is_enum = True
                # Collect other modifiers
                for modifier_child in child.children:  # type: ignore
                    if modifier_child.type in ["data", "sealed", "class_modifier"]:  # type: ignore
                        mod_txt = modifier_child.text.decode() if modifier_child.text else ""  # type: ignore
                        if mod_txt in ["data", "sealed", "abstract", "open", "final"]:
                            modifiers.append(mod_txt)

        # Determine class type based on enum or modifiers
        class_type = "enum" if is_enum else "class"

        # Use first meaningful modifier as type prefix (unless it's an enum)
        if not is_enum:
            if "data" in modifiers:
                class_type = "data class"
            elif "sealed" in modifiers:
                class_type = "sealed class"

        # Get name
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": class_type,
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

        # Extract methods and properties from body
        body_node = None
        for child in node.children:  # type: ignore
            if child.type == "class_body":  # type: ignore
                body_node = child
                break

        if body_node:
            for child in body_node.children:  # type: ignore
                if child.type == "function_declaration":  # type: ignore
                    self._extract_method(child, symbols, file_path)
                elif child.type == "property_declaration":  # type: ignore
                    self._extract_property(child, symbols, file_path)
                elif child.type == "companion_object":  # type: ignore
                    self._extract_companion_object(child, symbols, file_path)

    def _extract_object(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract object declaration (singleton)."""
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": "object",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

        # Extract methods from body
        body_node = None
        for child in node.children:  # type: ignore
            if child.type == "class_body":  # type: ignore
                body_node = child
                break

        if body_node:
            for child in body_node.children:  # type: ignore
                if child.type == "function_declaration":  # type: ignore
                    self._extract_method(child, symbols, file_path)

    def _extract_companion_object(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract companion object."""
        # Companion objects may or may not have a name
        name_node = node.child_by_field_name("name")  # type: ignore
        name = name_node.text.decode() if name_node else "Companion"  # type: ignore

        symbol = {
            "name": name,
            "type": "companion object",
            "file_path": file_path,
            "line_start": node.start_point[0] + 1,  # type: ignore
            "line_end": node.end_point[0] + 1,  # type: ignore
            "docstring": self._extract_docstring(node),
            "signature": "companion object" + (f" {name}" if name_node else ""),
        }
        symbols.append(symbol)

        # Extract methods from companion object
        body_node = None
        for child in node.children:  # type: ignore
            if child.type == "class_body":  # type: ignore
                body_node = child
                break

        if body_node:
            for child in body_node.children:  # type: ignore
                if child.type == "function_declaration":  # type: ignore
                    self._extract_method(child, symbols, file_path)

    def _extract_interface(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract interface declaration."""
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": "interface",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

    def _extract_function(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract top-level function (including extension and suspend functions)."""
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            # Check for modifiers (suspend, inline, etc.)
            function_type = "function"
            for child in node.children:  # type: ignore
                if child.type == "modifiers":  # type: ignore
                    for modifier_child in child.children:  # type: ignore
                        if modifier_child.type == "function_modifier":  # type: ignore
                            modifier_text = (
                                modifier_child.text.decode() if modifier_child.text else ""  # type: ignore
                            )
                            if "suspend" in modifier_text:
                                function_type = "suspend function"
                                break

            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": function_type,
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

    def _extract_method(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract method from class/object/interface."""
        name_node = node.child_by_field_name("name")  # type: ignore
        if name_node:
            symbol = {
                "name": name_node.text.decode(),  # type: ignore
                "type": "method",
                "file_path": file_path,
                "line_start": node.start_point[0] + 1,  # type: ignore
                "line_end": node.end_point[0] + 1,  # type: ignore
                "docstring": self._extract_docstring(node),
                "signature": self._extract_signature(node),
            }
            symbols.append(symbol)

    def _extract_property(
        self, node: any, symbols: list[dict[str, any]], file_path: str  # type: ignore  # noqa: ANN401
    ) -> None:
        """Extract property declaration."""
        # Get variable declaration name
        var_decl = None
        for child in node.children:  # type: ignore
            if child.type == "variable_declaration":  # type: ignore
                var_decl = child
                break

        if var_decl:
            name_node = var_decl.child_by_field_name("name")
            if name_node:
                symbol = {
                    "name": name_node.text.decode(),  # type: ignore
                    "type": "property",
                    "file_path": file_path,
                    "line_start": node.start_point[0] + 1,  # type: ignore
                    "line_end": node.end_point[0] + 1,  # type: ignore
                    "docstring": self._extract_docstring(node),
                    "signature": self._extract_signature(node),
                }
                symbols.append(symbol)

    def _extract_docstring(self, node: any) -> Optional[str]:  # type: ignore  # noqa: ANN401
        """
        Extract documentation comment from node.

        Kotlin uses /** */ (KDoc) for documentation comments.
        """
        try:
            # Look for comment before the node
            prev_sibling = node.prev_sibling  # type: ignore
            comment_types = ["comment", "block_comment", "multiline_comment"]
            if prev_sibling and prev_sibling.type in comment_types:
                comment_text = prev_sibling.text.decode()
                # Remove /** */ markers and clean up
                cleaned = (
                    comment_text.replace("/**", "")
                    .replace("*/", "")
                    .replace("*", "")
                    .strip()
                )
                if cleaned:
                    return cleaned  # type: ignore
            return None
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract Kotlin docstring: {e}")
            return None

    def _extract_signature(self, node: any) -> Optional[str]:  # type: ignore  # noqa: ANN401
        """
        Extract signature from node.

        Args:
            node: tree-sitter Node

        Returns:
            Signature string or None
        """
        try:
            # Get the first line of the declaration
            text = node.text.decode()  # type: ignore
            signature = text.split("\n")[0].strip()
            # Remove opening brace if present
            if "{" in signature:
                signature = signature.split("{")[0].strip()
            return signature  # type: ignore
        except (AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to extract Kotlin signature: {e}")
            return None
