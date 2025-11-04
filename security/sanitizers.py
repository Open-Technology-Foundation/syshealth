#!/usr/bin/env python3

"""Input sanitization functions for SysHealth.

This module provides functions to sanitize user-provided input to prevent
path traversal, injection attacks, and other security vulnerabilities.
"""

import logging
import re

logger = logging.getLogger("syshealth.security.sanitizers")

# Maximum length for hostname and language to prevent buffer issues
MAX_HOSTNAME_LENGTH = 255
MAX_LANGUAGE_LENGTH = 10


def sanitize_hostname(hostname: str) -> str:
    """Sanitize hostname to prevent path traversal and injection attacks.

    This function removes or replaces characters that could be used in
    path traversal attacks or command injection attempts. Only alphanumeric
    characters, hyphens, underscores, and dots are allowed.

    Args:
        hostname: The hostname string to sanitize

    Returns:
        Sanitized hostname safe for use in filenames and paths

    Raises:
        ValueError: If hostname is empty after sanitization or exceeds length limit

    Security Notes:
        - Removes path separators (/, \\)
        - Removes parent directory references (..)
        - Removes null bytes
        - Removes shell metacharacters
        - Limits length to prevent buffer issues
        - Logs all sanitization actions for audit trail

    Examples:
        >>> sanitize_hostname("server1.example.com")
        'server1.example.com'
        >>> sanitize_hostname("../../etc/passwd")
        'etc_passwd'
        >>> sanitize_hostname("server; rm -rf")
        'server_rm_-rf'
    """
    if not hostname:
        raise ValueError("Hostname cannot be empty")

    original_hostname = hostname

    # Remove null bytes (can bypass some security checks)
    hostname = hostname.replace("\x00", "")

    # Replace path separators with underscores
    hostname = hostname.replace("/", "_").replace("\\", "_")

    # Remove parent directory references
    hostname = hostname.replace("..", "")

    # Replace shell metacharacters and special characters with underscores
    # Allow only: alphanumeric, hyphen, underscore, dot
    hostname = re.sub(r"[^a-zA-Z0-9._-]", "_", hostname)

    # Remove leading/trailing dots and underscores (can cause issues)
    hostname = hostname.strip("._")

    # Collapse multiple underscores/dots into single character
    hostname = re.sub(r"_+", "_", hostname)
    hostname = re.sub(r"\.+", ".", hostname)

    # Enforce maximum length
    if len(hostname) > MAX_HOSTNAME_LENGTH:
        hostname = hostname[:MAX_HOSTNAME_LENGTH]
        logger.warning(
            f"Hostname truncated to {MAX_HOSTNAME_LENGTH} characters: "
            f"{original_hostname[:50]}..."
        )

    # Verify we still have a valid hostname after sanitization
    if not hostname:
        raise ValueError(
            f"Hostname '{original_hostname}' contains only invalid characters"
        )

    # Log if sanitization changed the hostname
    if hostname != original_hostname:
        logger.info(f"Hostname sanitized: '{original_hostname}' → '{hostname}'")

    return hostname


def sanitize_language(language: str) -> str:
    """Sanitize language code to prevent path traversal and injection attacks.

    This function sanitizes language codes to ensure they contain only
    safe characters. Language codes should be 2-5 character codes like
    "en", "es", "zh-CN", etc.

    Args:
        language: The language code to sanitize

    Returns:
        Sanitized language code safe for use in filenames

    Raises:
        ValueError: If language code is empty after sanitization or too long

    Security Notes:
        - Allows only alphanumeric and hyphen characters
        - Limits length to prevent abuse
        - Removes path separators and special characters
        - Logs all sanitization actions

    Examples:
        >>> sanitize_language("en")
        'en'
        >>> sanitize_language("zh-CN")
        'zh-CN'
        >>> sanitize_language("../../../etc")
        'etc'
        >>> sanitize_language("en; rm -rf")
        'en_rm_-rf'
    """
    if not language:
        raise ValueError("Language code cannot be empty")

    original_language = language

    # Remove null bytes
    language = language.replace("\x00", "")

    # Replace path separators with underscores
    language = language.replace("/", "_").replace("\\", "_")

    # Remove parent directory references
    language = language.replace("..", "")

    # Allow only alphanumeric, hyphen, and underscore
    # Standard language codes use only letters and hyphens
    language = re.sub(r"[^a-zA-Z0-9_-]", "_", language)

    # Remove leading/trailing hyphens and underscores
    language = language.strip("_-")

    # Collapse multiple underscores/hyphens
    language = re.sub(r"_+", "_", language)
    language = re.sub(r"-+", "-", language)

    # Enforce maximum length
    if len(language) > MAX_LANGUAGE_LENGTH:
        language = language[:MAX_LANGUAGE_LENGTH]
        logger.warning(
            f"Language code truncated to {MAX_LANGUAGE_LENGTH} characters: "
            f"{original_language}"
        )

    # Verify we still have a valid language code
    if not language:
        raise ValueError(
            f"Language code '{original_language}' contains only invalid characters"
        )

    # Log if sanitization changed the language code
    if language != original_language:
        logger.info(f"Language code sanitized: '{original_language}' → '{language}'")

    return language


def sanitize_email_recipient(email: str) -> str:
    """Sanitize email address to prevent header injection.

    This function removes newlines and other characters that could be used
    for email header injection attacks.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email address

    Raises:
        ValueError: If email is empty after sanitization

    Security Notes:
        - Removes all newline characters (\\r, \\n)
        - Removes null bytes
        - Strips whitespace
        - Does NOT validate RFC 5322 compliance (use validate_email_address)

    Examples:
        >>> sanitize_email_recipient("user@example.com")
        'user@example.com'
        >>> sanitize_email_recipient("user@example.com\\nBcc: attacker@evil.com")
        'user@example.comBcc: attacker@evil.com'
    """
    if not email:
        raise ValueError("Email address cannot be empty")

    original_email = email

    # Remove null bytes
    email = email.replace("\x00", "")

    # Remove all types of newlines (prevents header injection)
    email = email.replace("\r", "").replace("\n", "")

    # Strip whitespace
    email = email.strip()

    # Verify we still have an email after sanitization
    if not email:
        raise ValueError(f"Email '{original_email}' contains only invalid characters")

    # Log if sanitization changed the email
    if email != original_email:
        logger.warning(
            f"Email address sanitized (potential header injection attempt): "
            f"'{original_email[:50]}'"
        )

    return email


# fin
