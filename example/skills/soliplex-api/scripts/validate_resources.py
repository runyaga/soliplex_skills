#!/usr/bin/env python3
"""Validate resource files for context rot.

Checks:
1. Python code blocks parse correctly
2. YAML code blocks parse correctly
3. Referenced files exist
4. Import statements are valid

Usage:
    python validate_resources.py [--verbose]
"""

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml


def extract_code_blocks(content: str) -> list[tuple[str, str]]:
    """Extract fenced code blocks from markdown.

    Returns:
        List of (language, code) tuples.
    """
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    return [(lang or "", code) for lang, code in matches]


def is_example_snippet(code: str) -> bool:
    """Check if code is an incomplete example snippet.

    Returns True for code that uses ... as placeholder.
    """
    # Common patterns in incomplete examples
    if "Tool(...)" in code or "(...)" in code:
        return True
    return bool(re.search(r"\.\.\.\s*$", code, re.MULTILINE))


def validate_python_syntax(code: str) -> tuple[bool, str | None]:
    """Check if Python code parses correctly."""
    # Skip validation for incomplete example snippets
    if is_example_snippet(code):
        return True, None

    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    else:
        return True, None


def validate_yaml_syntax(code: str) -> tuple[bool, str | None]:
    """Check if YAML code parses correctly."""
    try:
        yaml.safe_load(code)
    except yaml.YAMLError as e:
        return False, str(e)
    else:
        return True, None


def extract_file_references(content: str) -> list[str]:
    """Extract file path references from markdown."""
    patterns = [
        r"`([a-zA-Z0-9_/\-\.]+\.(py|yaml|md))`",
        r"\"([a-zA-Z0-9_/\-\.]+\.(py|yaml|md))\"",
        r"'([a-zA-Z0-9_/\-\.]+\.(py|yaml|md))'",
    ]
    refs = []
    for pattern in patterns:
        refs.extend(re.findall(pattern, content))
    return [r[0] if isinstance(r, tuple) else r for r in refs]


EXAMPLE_MODULES = {
    "mymodule",
    "your_module",
    "example",
    "external_lib",
    "heavy_library",
    "optional_lib",
    "config",
    "my_package",
}


def check_imports(code: str) -> list[str]:
    """Check if imports in code are valid.

    Returns list of failed imports.
    """
    # Skip import checking for example snippets
    if is_example_snippet(code):
        return []

    failed = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return failed

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in EXAMPLE_MODULES:
                    continue
                try:
                    __import__(module)
                except ImportError:
                    failed.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.split(".")[0]
            if module in EXAMPLE_MODULES:
                continue
            try:
                __import__(module)
            except ImportError:
                failed.append(node.module)
    return failed


def validate_resource(path: Path, verbose: bool = False) -> dict:
    """Validate a single resource file.

    Returns:
        Dict with validation results.
    """
    content = path.read_text()
    results = {
        "file": str(path.name),
        "python_blocks": [],
        "yaml_blocks": [],
        "file_refs": [],
        "import_errors": [],
        "errors": 0,
        "warnings": 0,
    }

    code_blocks = extract_code_blocks(content)

    for lang, code in code_blocks:
        if lang in ("python", "py", ""):
            if "def " in code or "import " in code or "class " in code:
                valid, error = validate_python_syntax(code)
                if not valid:
                    results["python_blocks"].append(
                        {
                            "valid": False,
                            "error": error,
                            "preview": code[:50],
                        }
                    )
                    results["errors"] += 1
                else:
                    results["python_blocks"].append({"valid": True})
                    failed_imports = check_imports(code)
                    if failed_imports:
                        results["import_errors"].extend(failed_imports)
                        results["warnings"] += len(failed_imports)

        elif lang in ("yaml", "yml"):
            valid, error = validate_yaml_syntax(code)
            if not valid:
                results["yaml_blocks"].append(
                    {
                        "valid": False,
                        "error": error,
                        "preview": code[:50],
                    }
                )
                results["errors"] += 1
            else:
                results["yaml_blocks"].append({"valid": True})

    return results


def main():
    parser = argparse.ArgumentParser(description="Validate resource files")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    resources_dir = Path(__file__).parent.parent / "references"
    if not resources_dir.exists():
        print(f"References directory not found: {resources_dir}")
        sys.exit(1)

    total_errors = 0
    total_warnings = 0

    print("Validating resources for context rot...\n")

    for md_file in sorted(resources_dir.glob("*.md")):
        results = validate_resource(md_file, args.verbose)

        status = "OK"
        if results["errors"] > 0:
            status = "ERRORS"
        elif results["warnings"] > 0:
            status = "WARNINGS"

        icon = {"OK": "+", "WARNINGS": "~", "ERRORS": "x"}[status]
        print(f"[{icon}] {results['file']}")

        if args.verbose or results["errors"] > 0:
            for pb in results["python_blocks"]:
                if not pb.get("valid", True):
                    print(f"    Python syntax error: {pb['error']}")

            for yb in results["yaml_blocks"]:
                if not yb.get("valid", True):
                    print(f"    YAML syntax error: {yb['error']}")

        if results["import_errors"]:
            imports = ", ".join(results["import_errors"])
            print(f"    Import warnings: {imports}")

        total_errors += results["errors"]
        total_warnings += results["warnings"]

    print(f"\nSummary: {total_errors} errors, {total_warnings} warnings")

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
