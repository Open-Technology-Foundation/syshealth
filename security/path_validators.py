#!/usr/bin/env python3

"""Path validation functions for SysHealth.

This module provides functions to validate file paths and prevent
directory traversal attacks and other path-based vulnerabilities.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger("syshealth.security.path_validators")


def validate_output_path(base_dir: str, filename: str) -> str:
    """Validate that the output file path stays within the base directory.

    This function prevents directory traversal attacks by ensuring that
    the resolved absolute path of the output file is within the base
    directory. It uses Path.resolve() to handle symbolic links and
    relative path components.

    Args:
        base_dir: The base directory that the file must be within
        filename: The filename to write (should already be sanitized)

    Returns:
        The validated absolute file path as a string

    Raises:
        ValueError: If the resolved path is outside base_dir
        ValueError: If base_dir does not exist or is not a directory
        PermissionError: If base_dir is not writable

    Security Notes:
        - Uses Path.resolve() to get absolute path and resolve symlinks
        - Checks Path.is_relative_to() to ensure path stays within base_dir
        - Validates base directory exists and is writable
        - Logs all validation failures for security audit
        - Prevents both absolute and relative path traversal

    Examples:
        >>> validate_output_path("/tmp/reports", "server1-en-20251104.md")
        '/tmp/reports/server1-en-20251104.md'

        >>> validate_output_path("/tmp/reports", "../../../etc/passwd")
        ValueError: Path traversal detected: ../../../etc/passwd

        >>> validate_output_path("/tmp/reports", "/etc/passwd")
        ValueError: Path traversal detected: /etc/passwd
    """
    try:
        # Convert base_dir to Path and resolve it (handles symlinks)
        base_path = Path(base_dir).resolve()

        # Validate base directory exists
        if not base_path.exists():
            raise ValueError(f"Base directory does not exist: {base_dir}")

        # Validate base directory is actually a directory
        if not base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {base_dir}")

        # Check if base directory is writable
        if not os.access(str(base_path), os.W_OK):
            # Raise as OSError so it's caught by the exception handler below
            raise OSError(f"Base directory is not writable: {base_dir}")

        # Construct target path and resolve it
        # This handles any ".." or "." components and resolves symlinks
        target_path = (base_path / filename).resolve()

        # Check if target path is within base directory
        # is_relative_to() returns True if target_path is within base_path
        if not target_path.is_relative_to(base_path):
            logger.error(
                f"Path traversal attempt detected: "
                f"base='{base_dir}', filename='{filename}', "
                f"resolved='{target_path}'"
            )
            raise ValueError(
                f"Path traversal detected: '{filename}' resolves to location "
                f"outside base directory '{base_dir}'"
            )

        # Additional safety check: ensure target is not the base directory itself
        if target_path == base_path:
            raise ValueError(f"Cannot write to base directory itself: '{filename}'")

        # Log successful validation in debug mode
        logger.debug(
            f"Path validation successful: base='{base_dir}', "
            f"filename='{filename}', validated='{target_path}'"
        )

        return str(target_path)

    except (OSError, RuntimeError, PermissionError) as e:
        # Handle Path.resolve() errors (broken symlinks, permission issues)
        # Wrap all exceptions in ValueError for consistent error handling
        logger.error(
            f"Path validation error: base='{base_dir}', filename='{filename}', "
            f"error={e}"
        )
        raise ValueError(f"Invalid path configuration: {e}") from e


def validate_directory_path(directory: str) -> str:
    """Validate that a directory path is safe for use.

    This function validates directory paths to ensure they are:
    - Absolute paths (not relative)
    - Existing directories or creatable locations
    - Not pointing to sensitive system directories

    Args:
        directory: The directory path to validate

    Returns:
        The validated absolute directory path

    Raises:
        ValueError: If directory path is invalid or unsafe
        PermissionError: If directory cannot be accessed

    Security Notes:
        - Rejects relative paths (must be absolute)
        - Warns if directory is in sensitive locations
        - Resolves symlinks to check actual location
        - Validates parent directory exists if creating new dir

    Examples:
        >>> validate_directory_path("/tmp/reports")
        '/tmp/reports'

        >>> validate_directory_path("../reports")
        ValueError: Directory path must be absolute

        >>> validate_directory_path("/etc/")
        ValueError: Cannot write to sensitive system directory
    """
    # Sensitive directories that should not be written to
    SENSITIVE_DIRS = {
        "/etc",
        "/bin",
        "/sbin",
        "/usr/bin",
        "/usr/sbin",
        "/boot",
        "/sys",
        "/proc",
        "/dev",
    }

    try:
        # Convert to Path object
        dir_path = Path(directory)

        # Reject relative paths
        if not dir_path.is_absolute():
            raise ValueError(f"Directory path must be absolute, got: '{directory}'")

        # Resolve to handle symlinks
        resolved_path = dir_path.resolve()

        # Check if it's pointing to a sensitive directory
        for sensitive in SENSITIVE_DIRS:
            sensitive_path = Path(sensitive).resolve()
            if resolved_path == sensitive_path or resolved_path.is_relative_to(
                sensitive_path
            ):
                raise ValueError(
                    f"Cannot write to sensitive system directory: '{directory}' "
                    f"resolves to '{resolved_path}'"
                )

        # If directory exists, verify it's actually a directory
        if resolved_path.exists():
            if not resolved_path.is_dir():
                raise ValueError(f"Path exists but is not a directory: '{directory}'")
        else:
            # Directory doesn't exist - check if parent exists and is writable
            parent = resolved_path.parent
            if not parent.exists():
                raise ValueError(f"Parent directory does not exist: '{parent}'")
            if not parent.is_dir():
                raise ValueError(f"Parent path is not a directory: '{parent}'")
            if not os.access(str(parent), os.W_OK):
                # Raise as OSError so it's caught by the exception handler below
                raise OSError(
                    f"Cannot create directory - parent not writable: '{parent}'"
                )

        logger.debug(f"Directory validation successful: '{directory}'")
        return str(resolved_path)

    except (OSError, RuntimeError, PermissionError) as e:
        # Wrap all exceptions in ValueError for consistent error handling
        logger.error(f"Directory validation error: '{directory}', error={e}")
        raise ValueError(f"Invalid directory path: {e}") from e


# fin
