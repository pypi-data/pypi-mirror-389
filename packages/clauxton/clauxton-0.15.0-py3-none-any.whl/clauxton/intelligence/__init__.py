"""
Clauxton Intelligence Module.

This module provides automatic codebase understanding through:
- Repository Map: File structure indexing and symbol extraction
- Symbol Extraction: Parse functions, classes, and dependencies
- Dependency Graph: Analyze import relationships
- Code Analysis: Quality metrics and patterns

Available for v0.11.0+
"""

from clauxton.intelligence.repository_map import RepositoryMap
from clauxton.intelligence.symbol_extractor import PythonSymbolExtractor, SymbolExtractor

__all__ = [
    "RepositoryMap",
    "SymbolExtractor",
    "PythonSymbolExtractor",
]
