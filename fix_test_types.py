#!/usr/bin/env python3
"""Script to add return type annotations to test functions.

This script adds '-> None' return type annotations to test functions
that are missing them, which is required for mypy --strict compliance.
"""
import re
from pathlib import Path


def fix_test_file(filepath: Path) -> bool:
    """Add return type annotations to test functions in a file.

    Args:
        filepath: Path to the test file to fix

    Returns:
        True if file was modified, False otherwise
    """
    print(f"Processing: {filepath}")
    content = filepath.read_text(encoding="utf-8")
    original_content = content

    # Pattern to match function definitions without return type annotations
    # Matches: def test_something(...): or def fixture_name(...):
    # But not: def something() -> ReturnType:
    pattern = r"^(\s*def\s+\w+\s*\([^)]*\))(\s*):"

    lines = content.splitlines()
    new_lines = []
    changes = 0

    for i, line in enumerate(lines):
        # Check if this is a function definition without a return type
        match = re.match(pattern, line)
        if match and "->" not in line:
            # Add -> None before the colon
            indent_and_def = match.group(1)
            spaces = match.group(2)
            new_line = f"{indent_and_def} -> None:"
            new_lines.append(new_line)
            changes += 1
            print(f"  Line {i+1}: {line.strip()[:60]}...")
            print(f"        → {new_line.strip()[:60]}...")
        else:
            new_lines.append(line)

    new_content = "\n".join(new_lines)

    # Only write if changes were made
    if new_content != original_content:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  ✓ Fixed {changes} functions in {filepath.name}")
        return True
    else:
        print("  - No changes needed")
        return False


def main() -> None:
    """Run return type annotation fixes on all test files."""
    print("=" * 70)
    print(" " * 10 + "Test Function Return Type Annotation Fixer")
    print("=" * 70)
    print()

    test_dir = Path("tests")
    if not test_dir.exists():
        print("Error: tests directory not found")
        return

    files_processed = 0
    files_modified = 0

    for test_file in sorted(test_dir.glob("*.py")):
        files_processed += 1
        if fix_test_file(test_file):
            files_modified += 1
        print()  # Blank line between files

    print("=" * 70)
    print("Complete!")
    print(f"  Files processed: {files_processed}")
    print(f"  Files modified:  {files_modified}")
    print(f"  Files unchanged: {files_processed - files_modified}")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review changes: git diff tests/")
    print("  2. Run tests: pytest")
    print("  3. Check types: mypy tests/*.py --strict")
    print()


if __name__ == "__main__":
    main()

# fin
