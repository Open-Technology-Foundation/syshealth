#!/usr/bin/env python3
"""Script to modernize type hints to Python 3.12+ syntax.

This script performs the following transformations:
- X | None → X | None (PEP 604)
- X | Y → X | Y (PEP 604)
- list[X] → list[X] (PEP 585)
- dict[K, V] → dict[K, V] (PEP 585)
- set[X] → set[X] (PEP 585)
- Removes unnecessary typing imports
"""
import re
from pathlib import Path


def modernize_file(filepath: Path) -> bool:
    """Modernize type hints in a Python file.

    Args:
        filepath: Path to the Python file to modernize

    Returns:
        True if file was modified, False otherwise
    """
    print(f"Processing: {filepath}")
    content = filepath.read_text(encoding="utf-8")
    original_content = content

    # Replace X | None with X | None
    content = re.sub(r"Optional\[([^\]]+)\]", r"\1 | None", content)

    # Replace X | Y with X | Y (handles more complex unions)
    content = re.sub(r"Union\[([^,]+),\s*([^\]]+)\]", r"\1 | \2", content)

    # Replace list[X] with list[X]
    content = re.sub(r"\bList\[", "list[", content)

    # Replace dict[K, V] with dict[K, V]
    content = re.sub(r"\bDict\[", "dict[", content)

    # Replace set[X] with set[X]
    content = re.sub(r"\bSet\[", "set[", content)

    # Remove unnecessary imports
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if "from typing import" in line:
            # Remove Optional, Union, List, Dict, Set from imports
            original_line = line
            line = re.sub(r",?\s*Optional\b", "", line)
            line = re.sub(r",?\s*Union\b", "", line)
            line = re.sub(r",?\s*List\b", "", line)
            line = re.sub(r",?\s*Dict\b", "", line)
            line = re.sub(r",?\s*Set\b", "", line)

            # Clean up malformed import lines
            line = re.sub(r"import\s*,", "import", line)
            line = re.sub(r",\s*,+", ",", line)
            line = re.sub(r",\s*\)", ")", line)
            line = re.sub(r"\(\s*,", "(", line)
            line = re.sub(r",\s*$", "", line)

            # Skip if import line is now empty
            if line.strip() in [
                "from typing import" "from typing import ()" "from typing import ("
            ]:
                print("  - Removed empty import line")
                continue

            # Only include if line was actually changed
            if line != original_line:
                print(f"  - Updated import: {original_line.strip()} → {line.strip()}")

        new_lines.append(line)

    new_content = "\n".join(new_lines)

    # Only write if changes were made
    if new_content != original_content:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  ✓ Modernized: {filepath.name}")
        return True
    else:
        print("  - No changes needed")
        return False


def main() -> None:
    """Run type hint modernization on all Python files."""
    print("=" * 70)
    print(" " * 10 + "Type Hint Modernization to Python 3.12+ Syntax")
    print("=" * 70)
    print()

    # Find all Python files excluding venv and htmlcov
    files_processed = 0
    files_modified = 0

    for pyfile in sorted(Path(".").rglob("*.py")):
        if ".venv" not in str(pyfile) and "htmlcov" not in str(pyfile):
            files_processed += 1
            if modernize_file(pyfile):
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
    print("  1. Review changes: git diff")
    print("  2. Run tests: pytest")
    print("  3. Check types: mypy . --strict")
    print()


if __name__ == "__main__":
    main()

# fin
