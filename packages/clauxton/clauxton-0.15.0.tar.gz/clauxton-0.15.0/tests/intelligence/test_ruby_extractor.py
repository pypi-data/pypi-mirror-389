"""Tests for Ruby symbol extraction."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clauxton.intelligence.symbol_extractor import RubySymbolExtractor


@pytest.fixture
def ruby_extractor():
    """Create RubySymbolExtractor instance."""
    return RubySymbolExtractor()


@pytest.fixture
def sample_file(tmp_path):
    """Path to sample Ruby file."""
    return Path(__file__).parent.parent / "fixtures" / "ruby" / "sample.rb"


@pytest.fixture
def empty_file(tmp_path):
    """Path to empty Ruby file."""
    return Path(__file__).parent.parent / "fixtures" / "ruby" / "empty.rb"


@pytest.fixture
def unicode_file(tmp_path):
    """Path to Unicode Ruby file."""
    return Path(__file__).parent.parent / "fixtures" / "ruby" / "unicode.rb"


# ===========================
# 1. Initialization Tests
# ===========================


def test_initialization(ruby_extractor):
    """Test RubySymbolExtractor initialization."""
    assert ruby_extractor is not None
    assert hasattr(ruby_extractor, "parser")
    assert hasattr(ruby_extractor, "available")


# ===========================
# 2. Basic Extraction Tests
# ===========================


def test_extract_class(tmp_path):
    """Test extracting a class."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def initialize(name)
    @name = name
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 1
    assert classes[0]["name"] == "User"
    assert classes[0]["line_start"] == 2


def test_extract_module(tmp_path):
    """Test extracting a module."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
module Authentication
  def self.login
    puts "logging in"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    modules = [s for s in symbols if s["type"] == "module"]
    assert len(modules) == 1
    assert modules[0]["name"] == "Authentication"
    assert modules[0]["line_start"] == 2


def test_extract_method(tmp_path):
    """Test extracting an instance method."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def greet
    "Hello"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "greet"
    assert methods[0]["signature"] is not None
    assert "def greet" in methods[0]["signature"]


def test_extract_singleton_method(tmp_path):
    """Test extracting a class method (singleton method)."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def self.count
    @@count
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    singleton_methods = [s for s in symbols if s["type"] == "singleton_method"]
    assert len(singleton_methods) == 1
    assert singleton_methods[0]["name"] == "self.count"
    assert singleton_methods[0]["signature"] is not None
    assert "def self.count" in singleton_methods[0]["signature"]


def test_extract_multiple_symbols(sample_file):
    """Test extracting multiple symbols from sample file."""
    extractor = RubySymbolExtractor()
    symbols = extractor.extract(sample_file)

    # Count symbol types
    classes = [s for s in symbols if s["type"] == "class"]
    modules = [s for s in symbols if s["type"] == "module"]
    methods = [s for s in symbols if s["type"] == "method"]
    singleton_methods = [s for s in symbols if s["type"] == "singleton_method"]

    # sample.rb should have multiple classes
    assert len(classes) >= 3  # User, AdminUser, Post, etc.
    # sample.rb should have multiple modules
    assert len(modules) >= 2  # Authentication, Timestampable
    # sample.rb should have many methods
    assert len(methods) >= 5
    # sample.rb should have singleton methods
    assert len(singleton_methods) >= 2


# ===========================
# 3. Ruby-Specific Features
# ===========================


def test_inheritance(tmp_path):
    """Test extracting class with inheritance."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
end

class AdminUser < User
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 2

    user_class = next(s for s in classes if s["name"] == "User")
    admin_class = next(s for s in classes if s["name"] == "AdminUser")

    assert user_class is not None
    assert admin_class is not None


def test_module_methods(tmp_path):
    """Test extracting module methods."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
module Auth
  def self.login(user)
    puts "Logging in: #{user}"
  end

  def self.logout
    puts "Logging out"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    modules = [s for s in symbols if s["type"] == "module"]
    singleton_methods = [s for s in symbols if s["type"] == "singleton_method"]

    assert len(modules) == 1
    assert modules[0]["name"] == "Auth"

    assert len(singleton_methods) == 2
    method_names = [s["name"] for s in singleton_methods]
    assert "self.login" in method_names
    assert "self.logout" in method_names


def test_initialize_method(tmp_path):
    """Test extracting initialize method (Ruby constructor)."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def initialize(name, email)
    @name = name
    @email = email
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    initialize_methods = [s for s in methods if s["name"] == "initialize"]

    assert len(initialize_methods) == 1
    assert "def initialize" in initialize_methods[0]["signature"]


def test_private_methods(tmp_path):
    """Test extracting private methods (currently extracted)."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def public_method
    "public"
  end

  private

  def private_method
    "private"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]

    # Both public and private methods should be extracted
    assert len(methods) == 2
    method_names = [s["name"] for s in methods]
    assert "public_method" in method_names
    assert "private_method" in method_names


def test_line_numbers(tmp_path):
    """Test line number accuracy."""
    file = tmp_path / "test.rb"
    file.write_text(
        """# Line 1: Comment
class User  # Line 2
  def greet  # Line 3
    "hello"  # Line 4
  end  # Line 5
end  # Line 6
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    methods = [s for s in symbols if s["type"] == "method"]

    assert len(classes) == 1
    assert classes[0]["line_start"] == 2
    assert classes[0]["line_end"] == 6

    assert len(methods) == 1
    assert methods[0]["line_start"] == 3
    assert methods[0]["line_end"] == 5


# ===========================
# 4. Advanced Features
# ===========================


def test_nested_classes(tmp_path):
    """Test extracting nested classes."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class Outer
  class Inner
    def method
      "inner"
    end
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]

    # Both Outer and Inner classes should be extracted
    assert len(classes) == 2
    class_names = [s["name"] for s in classes]
    assert "Outer" in class_names
    assert "Inner" in class_names


def test_multiple_modules(tmp_path):
    """Test extracting multiple modules."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
module Auth
end

module Logging
end

module Cache
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    modules = [s for s in symbols if s["type"] == "module"]
    assert len(modules) == 3

    module_names = [s["name"] for s in modules]
    assert "Auth" in module_names
    assert "Logging" in module_names
    assert "Cache" in module_names


def test_method_with_parameters(tmp_path):
    """Test extracting method with parameters."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class Calculator
  def add(a, b)
    a + b
  end

  def multiply(x, y = 1)
    x * y
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 2

    add_method = next((s for s in methods if s["name"] == "add"), None)
    multiply_method = next((s for s in methods if s["name"] == "multiply"), None)

    assert add_method is not None
    assert "def add(a, b)" in add_method["signature"]

    assert multiply_method is not None
    assert "def multiply" in multiply_method["signature"]


def test_standalone_methods(tmp_path):
    """Test extracting standalone methods (not in a class)."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
def helper_function
  "helper"
end

def another_helper
  "another"
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 2

    method_names = [s["name"] for s in methods]
    assert "helper_function" in method_names
    assert "another_helper" in method_names


# ===========================
# 5. Edge Cases & Integration
# ===========================


def test_empty_file(empty_file):
    """Test extracting from empty file."""
    extractor = RubySymbolExtractor()
    symbols = extractor.extract(empty_file)

    assert symbols == []


def test_unicode_symbols(unicode_file):
    """Test extracting Unicode symbols (Japanese, emoji)."""
    extractor = RubySymbolExtractor()
    symbols = extractor.extract(unicode_file)

    # Should extract some symbols from Unicode file
    assert len(symbols) > 0

    # Check for Japanese class name (ユーザー)
    classes = [s for s in symbols if s["type"] == "class"]
    class_names = [s["name"] for s in classes]

    # At minimum, should extract some classes
    # (tree-sitter may have difficulty with Unicode class names)
    assert len(classes) > 0, f"Expected at least 1 class, got classes: {class_names}"

    # Check for methods (should extract some methods regardless of Unicode issues)
    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) > 0, "Expected at least some methods to be extracted"


def test_file_not_found(tmp_path):
    """Test handling of non-existent file."""
    file = tmp_path / "nonexistent.rb"

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    # Should return empty list instead of raising exception
    assert symbols == []


def test_parser_unavailable():
    """Test fallback when tree-sitter-ruby is unavailable."""
    with patch("clauxton.intelligence.parser.RubyParser") as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser.available = False
        mock_parser_class.return_value = mock_parser

        extractor = RubySymbolExtractor()
        symbols = extractor.extract(Path("test.rb"))

        # Should return empty list
        assert symbols == []


def test_integration_with_repository_map(sample_file):
    """Test integration with RepositoryMap."""
    from clauxton.intelligence.symbol_extractor import SymbolExtractor

    dispatcher = SymbolExtractor()
    symbols = dispatcher.extract(sample_file, language="ruby")

    # Should return symbols from sample file
    assert len(symbols) > 0

    # Verify symbol structure
    for symbol in symbols:
        assert "name" in symbol
        assert "type" in symbol
        assert "file_path" in symbol
        assert "line_start" in symbol
        assert "line_end" in symbol


# ===========================
# 6. Additional Ruby-Specific Tests
# ===========================


def test_attr_accessor(tmp_path):
    """Test that attr_accessor is recognized in class context."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  attr_accessor :name, :email
  attr_reader :id

  def initialize(id)
    @id = id
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    # Should extract class and initialize method
    classes = [s for s in symbols if s["type"] == "class"]
    methods = [s for s in symbols if s["type"] == "method"]

    assert len(classes) == 1
    assert classes[0]["name"] == "User"
    assert len(methods) >= 1  # initialize method


def test_mixin_include(tmp_path):
    """Test class with module inclusion."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
module Loggable
  def log(message)
    puts message
  end
end

class Service
  include Loggable

  def run
    log("Running...")
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    modules = [s for s in symbols if s["type"] == "module"]
    classes = [s for s in symbols if s["type"] == "class"]

    assert len(modules) == 1
    assert modules[0]["name"] == "Loggable"
    assert len(classes) == 1
    assert classes[0]["name"] == "Service"


def test_class_methods_multiple_styles(tmp_path):
    """Test different styles of defining class methods."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  # Style 1: def self.method
  def self.create(name)
    new(name)
  end

  # Style 2: class << self
  class << self
    def find(id)
      # find logic
    end
  end

  def initialize(name)
    @name = name
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    singleton_methods = [s for s in symbols if s["type"] == "singleton_method"]

    # Should extract at least the "def self.create" style
    assert len(singleton_methods) >= 1
    assert any(s["name"] == "self.create" for s in singleton_methods)


def test_multiple_classes_one_file(tmp_path):
    """Test extracting multiple top-level classes."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def greet
    "Hello"
  end
end

class Admin
  def greet
    "Hello, Admin"
  end
end

class Guest
  def greet
    "Hello, Guest"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 3

    class_names = sorted([c["name"] for c in classes])
    assert class_names == ["Admin", "Guest", "User"]


def test_method_with_default_parameters(tmp_path):
    """Test method with default parameter values."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class Calculator
  def add(a, b = 0)
    a + b
  end

  def multiply(x, y = 1, z = 1)
    x * y * z
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 2

    method_names = [m["name"] for m in methods]
    assert "add" in method_names
    assert "multiply" in method_names


def test_method_with_keyword_arguments(tmp_path):
    """Test method with keyword arguments (Ruby 2.0+)."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def initialize(name:, email:, age: 18)
    @name = name
    @email = email
    @age = age
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "initialize"


def test_empty_class(tmp_path):
    """Test extracting empty class definition."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class EmptyClass
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 1
    assert classes[0]["name"] == "EmptyClass"


def test_syntax_error_handling(tmp_path):
    """Test graceful handling of syntax errors."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
class User
  def broken_method
    # Missing end statement
  # end

  def valid_method
    "I'm valid"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    # Should still extract some symbols despite syntax error
    # At minimum, tree-sitter should parse what it can
    assert isinstance(symbols, list)


def test_comments_ignored(tmp_path):
    """Test that comments are properly ignored."""
    file = tmp_path / "test.rb"
    file.write_text(
        """
# This is a comment
# class FakeClass
#   def fake_method
#   end
# end

class RealClass
  # Comment inside class
  def real_method
    # Comment inside method
    "real"
  end
end
"""
    )

    extractor = RubySymbolExtractor()
    symbols = extractor.extract(file)

    classes = [s for s in symbols if s["type"] == "class"]
    methods = [s for s in symbols if s["type"] == "method"]

    # Should only extract RealClass, not FakeClass
    assert len(classes) == 1
    assert classes[0]["name"] == "RealClass"

    # Should extract real_method
    assert len(methods) == 1
    assert methods[0]["name"] == "real_method"
