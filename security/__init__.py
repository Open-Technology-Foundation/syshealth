#!/usr/bin/env python3

"""Security module for SysHealth.

This module provides input sanitization, validation, and security utilities
to prevent common vulnerabilities including:
- Path traversal attacks
- Command injection
- Email header injection
- Input validation bypass

All user-provided input should be validated using utilities from this module
before being used in file operations, command execution, or external communication.
"""

from security.email_validators import (
    sanitize_subject,
    validate_email_address,
    validate_recipient_list,
)
from security.path_validators import validate_output_path
from security.sanitizers import sanitize_hostname, sanitize_language

__all__ = [
    "sanitize_hostname",
    "sanitize_language",
    "validate_output_path",
    "validate_email_address",
    "validate_recipient_list",
    "sanitize_subject",
]

# fin
