"""
Tests for Kotlin symbol extraction.
"""

from pathlib import Path

import pytest

from clauxton.intelligence.symbol_extractor import KotlinSymbolExtractor


@pytest.fixture
def extractor():
    """Return KotlinSymbolExtractor instance."""
    return KotlinSymbolExtractor()


@pytest.fixture
def sample_file():
    """Return path to sample.kt fixture."""
    return Path(__file__).parent.parent / "fixtures" / "kotlin" / "sample.kt"


@pytest.fixture
def empty_file():
    """Return path to empty.kt fixture."""
    return Path(__file__).parent.parent / "fixtures" / "kotlin" / "empty.kt"


@pytest.fixture
def unicode_file():
    """Return path to unicode.kt fixture."""
    return Path(__file__).parent.parent / "fixtures" / "kotlin" / "unicode.kt"


# ============================================================================
# Basic Extraction Tests
# ============================================================================


def test_initialization(extractor):
    """Test extractor initialization."""
    assert extractor is not None
    assert extractor.parser is not None


def test_extract_data_class(extractor, sample_file):
    """Test extraction of data class."""
    symbols = extractor.extract(sample_file)
    data_classes = [s for s in symbols if s["type"] == "data class"]
    assert len(data_classes) >= 2

    user = next(s for s in data_classes if s["name"] == "User")
    assert user["type"] == "data class"
    assert "User" in user["signature"]
    assert user["line_start"] > 0
    assert user["line_end"] > user["line_start"]


def test_extract_class(extractor, sample_file):
    """Test extraction of regular class."""
    symbols = extractor.extract(sample_file)
    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) >= 2

    admin = next((s for s in classes if s["name"] == "Admin"), None)
    assert admin is not None
    assert admin["type"] == "class"


def test_extract_sealed_class(extractor, sample_file):
    """Test extraction of sealed class."""
    symbols = extractor.extract(sample_file)
    sealed_classes = [s for s in symbols if s["type"] == "sealed class"]
    assert len(sealed_classes) >= 1

    api_response = next(s for s in sealed_classes if s["name"] == "ApiResponse")
    assert api_response["type"] == "sealed class"
    assert "sealed" in api_response["signature"].lower()


def test_extract_enum(extractor, sample_file):
    """Test extraction of enum class."""
    symbols = extractor.extract(sample_file)
    enums = [s for s in symbols if s["type"] == "enum"]
    assert len(enums) >= 1

    direction = next(s for s in enums if s["name"] == "Direction")
    assert direction["type"] == "enum"
    assert "enum" in direction["signature"].lower()


def test_extract_interface(extractor, sample_file):
    """Test extraction of interface."""
    symbols = extractor.extract(sample_file)
    interfaces = [s for s in symbols if s["type"] == "interface"]
    assert len(interfaces) >= 1

    greetable = next(s for s in interfaces if s["name"] == "Greetable")
    assert greetable["type"] == "interface"


def test_extract_object(extractor, sample_file):
    """Test extraction of object (singleton)."""
    symbols = extractor.extract(sample_file)
    objects = [s for s in symbols if s["type"] == "object"]
    assert len(objects) >= 1

    logger = next(s for s in objects if s["name"] == "Logger")
    assert logger["type"] == "object"
    assert "object" in logger["signature"].lower()


def test_extract_companion_object(extractor, sample_file):
    """Test extraction of companion object."""
    symbols = extractor.extract(sample_file)
    companions = [s for s in symbols if s["type"] == "companion object"]
    assert len(companions) >= 1

    companion = companions[0]
    assert companion["type"] == "companion object"
    assert companion["name"] in ["Companion", "companion"]


def test_extract_function(extractor, sample_file):
    """Test extraction of top-level function."""
    symbols = extractor.extract(sample_file)
    functions = [s for s in symbols if s["type"] == "function"]
    assert len(functions) >= 4

    format_text = next((s for s in functions if s["name"] == "formatText"), None)
    assert format_text is not None
    assert format_text["type"] == "function"


def test_extract_suspend_function(extractor, sample_file):
    """Test extraction of suspend function."""
    symbols = extractor.extract(sample_file)
    suspend_functions = [s for s in symbols if s["type"] == "suspend function"]
    assert len(suspend_functions) >= 1

    fetch_data = next(s for s in suspend_functions if s["name"] == "fetchData")
    assert fetch_data["type"] == "suspend function"
    assert "suspend" in fetch_data["signature"]


def test_extract_method(extractor, sample_file):
    """Test extraction of methods."""
    symbols = extractor.extract(sample_file)
    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) >= 5

    # Check that User.greet() is extracted
    greet_methods = [m for m in methods if m["name"] == "greet"]
    assert len(greet_methods) >= 1


def test_extract_multiple_symbols(extractor, sample_file):
    """Test extraction of all symbols from comprehensive file."""
    symbols = extractor.extract(sample_file)
    assert len(symbols) >= 15

    # Verify we have different types
    types = set(s["type"] for s in symbols)
    assert "data class" in types
    assert "class" in types
    assert "enum" in types
    assert "interface" in types
    assert "object" in types
    assert "function" in types
    assert "method" in types


# ============================================================================
# Kotlin-Specific Features
# ============================================================================


def test_generic_class(extractor, sample_file):
    """Test extraction of generic class."""
    symbols = extractor.extract(sample_file)
    box = next((s for s in symbols if s["name"] == "Box"), None)
    assert box is not None
    assert box["type"] == "class"
    # Generic type parameter should be in signature
    assert "<" in box["signature"] or "T" in box["signature"]


def test_extension_function(extractor, sample_file):
    """Test extraction of extension function."""
    symbols = extractor.extract(sample_file)
    # Extension functions are extracted as regular functions
    is_email = next((s for s in symbols if s["name"] == "isEmail"), None)
    assert is_email is not None
    assert is_email["type"] == "function"


def test_infix_function(extractor, sample_file):
    """Test extraction of infix function."""
    symbols = extractor.extract(sample_file)
    times = next((s for s in symbols if s["name"] == "times"), None)
    assert times is not None
    assert times["type"] == "function"
    # Infix modifier should be in signature
    if times["signature"]:
        assert "infix" in times["signature"].lower() or "Int" in times["signature"]


def test_function_with_default_parameters(extractor, sample_file):
    """Test extraction of function with default parameters."""
    symbols = extractor.extract(sample_file)
    greet = next((s for s in symbols if s["name"] == "greet" and s["type"] == "function"), None)
    assert greet is not None
    # Should extract function regardless of default parameters
    assert greet["type"] == "function"


# ============================================================================
# Edge Cases & Integration
# ============================================================================


def test_empty_file(extractor, empty_file):
    """Test extraction from empty file."""
    symbols = extractor.extract(empty_file)
    assert isinstance(symbols, list)
    assert len(symbols) == 0


def test_unicode_symbols(extractor, unicode_file):
    """Test extraction of Unicode symbols (Japanese, emoji)."""
    symbols = extractor.extract(unicode_file)
    assert len(symbols) >= 1

    # Check Japanese class name
    user_jp = next((s for s in symbols if "ユーザー" in s["name"]), None)
    assert user_jp is not None


def test_file_not_found(extractor):
    """Test extraction from nonexistent file."""
    nonexistent = Path("/nonexistent/file.kt")
    symbols = extractor.extract(nonexistent)
    assert isinstance(symbols, list)
    assert len(symbols) == 0


def test_parser_unavailable():
    """Test graceful degradation when parser is unavailable."""
    extractor = KotlinSymbolExtractor()
    extractor.parser.available = False

    sample_file = Path(__file__).parent.parent / "fixtures" / "kotlin" / "sample.kt"
    symbols = extractor.extract(sample_file)
    assert isinstance(symbols, list)
    assert len(symbols) == 0


def test_line_numbers(extractor, sample_file):
    """Test that line numbers are correctly extracted."""
    symbols = extractor.extract(sample_file)

    user = next(s for s in symbols if s["name"] == "User" and s["type"] == "data class")
    assert user["line_start"] > 0
    assert user["line_end"] > user["line_start"]
    assert user["line_end"] - user["line_start"] < 100  # Reasonable range


def test_multiple_classes_one_file(extractor, sample_file):
    """Test extraction of multiple top-level declarations."""
    symbols = extractor.extract(sample_file)

    # Check for multiple different top-level symbols
    user = any(s["name"] == "User" for s in symbols)
    point = any(s["name"] == "Point" for s in symbols)
    logger = any(s["name"] == "Logger" for s in symbols)

    assert user
    assert point
    assert logger


def test_syntax_error_handling(extractor, tmp_path):
    """Test handling of Kotlin file with syntax errors."""
    invalid_file = tmp_path / "invalid.kt"
    invalid_file.write_text("class Incomplete {")

    symbols = extractor.extract(invalid_file)
    # Should return empty list or partial results, not crash
    assert isinstance(symbols, list)


def test_comments_ignored(extractor, sample_file):
    """Test that comments are not extracted as symbols."""
    symbols = extractor.extract(sample_file)

    # Comments should not be in symbol names
    for symbol in symbols:
        assert not symbol["name"].startswith("//")
        assert not symbol["name"].startswith("/*")


def test_integration_with_repository_map(extractor, sample_file):
    """Test integration with RepositoryMap via dispatcher."""
    from clauxton.intelligence.symbol_extractor import SymbolExtractor

    dispatcher = SymbolExtractor()
    symbols = dispatcher.extract(sample_file, "kotlin")

    assert len(symbols) >= 15
    assert any(s["name"] == "User" for s in symbols)
