#!/usr/bin/env python3
"""
Benchmark repository indexing performance for Clauxton v0.11.0.

This script measures:
- File scanning speed
- tree-sitter symbol extraction performance
- Overall indexing throughput

Usage:
    python benchmark_indexing.py ~/clauxton-benchmarks/small-project
    python benchmark_indexing.py ~/clauxton-benchmarks/medium-project
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


def count_files(root: Path, pattern: str = "*.py") -> int:
    """Count files matching pattern."""
    return len(list(root.rglob(pattern)))


def count_lines(root: Path, pattern: str = "*.py") -> int:
    """Count total lines of code."""
    total = 0
    for file_path in root.rglob(pattern):
        try:
            with open(file_path) as f:
                total += len(f.readlines())
        except Exception:
            pass
    return total


def benchmark_tree_sitter(root: Path) -> Dict:
    """Benchmark tree-sitter parsing performance."""
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_python as tspython
    except ImportError:
        return {"error": "tree-sitter not available"}

    # Initialize parser
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    # Get Python files (exclude venv, .venv, node_modules)
    files = []
    for file_path in root.rglob("*.py"):
        path_str = str(file_path)
        if any(exclude in path_str for exclude in ["venv", ".venv", "node_modules", "__pycache__"]):
            continue
        files.append(file_path)

    if not files:
        return {"error": "no Python files found"}

    start = time.time()

    symbols_found = 0
    files_parsed = 0
    parse_errors = 0

    for file_path in files:
        try:
            with open(file_path, "rb") as f:
                tree = parser.parse(f.read())

            # Count function/class definitions
            def count_defs(node):
                count = 0
                if node.type in ("function_definition", "class_definition"):
                    count = 1
                for child in node.children:
                    count += count_defs(child)
                return count

            symbols_found += count_defs(tree.root_node)
            files_parsed += 1

        except Exception:
            parse_errors += 1

    duration = time.time() - start

    return {
        "files_total": len(files),
        "files_parsed": files_parsed,
        "parse_errors": parse_errors,
        "symbols_found": symbols_found,
        "duration_seconds": round(duration, 2),
        "files_per_second": round(files_parsed / duration, 1) if duration > 0 else 0,
        "avg_ms_per_file": round(duration / files_parsed * 1000, 1) if files_parsed > 0 else 0
    }


def get_project_category(file_count: int) -> Tuple[str, float]:
    """Determine project category and target time."""
    if file_count < 2000:
        return "Small", 2.0
    elif file_count < 15000:
        return "Medium", 10.0
    else:
        return "Large", 60.0


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_indexing.py <project-root>")
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"Error: {root} does not exist")
        sys.exit(1)

    print(f"📊 Benchmarking: {root.name}")
    print("=" * 70)

    # Count files and lines
    print("📁 Analyzing project structure...")
    py_files = count_files(root)
    py_lines = count_lines(root)
    print(f"  Python files: {py_files:,}")
    print(f"  Lines of code: {py_lines:,}")
    print()

    # Benchmark tree-sitter
    print("🔬 Benchmarking tree-sitter parsing...")
    result = benchmark_tree_sitter(root)

    if "error" in result:
        print(f"  ❌ {result['error']}")
        sys.exit(1)

    print(f"  ✅ Files parsed: {result['files_parsed']:,} / {result['files_total']:,}")
    if result['parse_errors'] > 0:
        print(f"  ⚠️  Parse errors: {result['parse_errors']:,}")
    print(f"  ✅ Symbols found: {result['symbols_found']:,}")
    print(f"  ⏱️  Duration: {result['duration_seconds']}s")
    print(f"  🚀 Speed: {result['files_per_second']} files/sec")
    print(f"  ⚡ Avg: {result['avg_ms_per_file']}ms per file")
    print()

    # Check against targets
    category, target = get_project_category(result['files_total'])
    print("🎯 Performance vs Targets:")
    status = "✅" if result['duration_seconds'] <= target else "❌"
    percentage = round((result['duration_seconds'] / target) * 100, 1)
    print(f"  {status} {category} project: {result['duration_seconds']}s / {target}s target ({percentage}%)")

    if status == "✅":
        improvement = round((target - result['duration_seconds']) / target * 100, 1)
        print(f"  💚 {improvement}% faster than target!")
    else:
        slowdown = round((result['duration_seconds'] - target) / target * 100, 1)
        print(f"  ⚠️  {slowdown}% slower than target")

    print()
    print("=" * 70)

    # Summary for automation
    exit_code = 0 if result['duration_seconds'] <= target else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
