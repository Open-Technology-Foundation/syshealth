#!/usr/bin/env python3

"""Email validation functions for SysHealth.

This module provides functions to validate email addresses and prevent
email header injection attacks.
"""

import logging
import re

from security.sanitizers import sanitize_email_recipient

logger = logging.getLogger("syshealth.security.email_validators")

# RFC 5322 compliant email regex (simplified but secure)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"  # Local part
    r"@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"  # Domain part
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"  # TLD
)


def validate_email_address(email: str) -> str:
    """Validate email address format according to RFC 5322.

    This function performs both sanitization and format validation to ensure
    the email address is valid and safe for use in email operations.

    Args:
        email: Email address to validate

    Returns:
        Validated and sanitized email address

    Raises:
        ValueError: If email address format is invalid

    Security Notes:
        - Sanitizes input first to prevent header injection
        - Validates RFC 5322 compliance (simplified)
        - Limits email length to prevent buffer issues
        - Logs all validation failures

    Examples:
        >>> validate_email_address("user@example.com")
        'user@example.com'

        >>> validate_email_address("invalid-email")
        ValueError: Invalid email address format

        >>> validate_email_address("user@example.com\\nBcc: attacker")
        ValueError: Invalid email address format (after sanitization)
    """
    # First sanitize to prevent header injection
    try:
        sanitized = sanitize_email_recipient(email)
    except ValueError as e:
        raise ValueError(f"Invalid email address: {e}") from e

    # Check length (RFC 5321 limits local to 64, domain to 255)
    if len(sanitized) > 320:  # 64 + 1 (@) + 255
        raise ValueError(
            f"Email address too long (max 320 characters): {len(sanitized)}"
        )

    # Validate format with regex
    if not EMAIL_REGEX.match(sanitized):
        logger.warning(f"Invalid email address format: '{email[:50]}'")
        raise ValueError(f"Invalid email address format: '{email}'")

    # Additional checks
    local, _, domain = sanitized.partition("@")

    if not local or not domain:
        raise ValueError(f"Email must contain local and domain parts: '{email}'")

    if len(local) > 64:
        raise ValueError(f"Email local part too long (max 64 chars): '{local}'")

    if len(domain) > 255:
        raise ValueError(f"Email domain part too long (max 255 chars): '{domain}'")

    # Domain must have at least one dot
    if "." not in domain:
        raise ValueError(f"Email domain must contain at least one dot: '{domain}'")

    logger.debug(f"Email validation successful: '{email}'")
    return sanitized


def validate_recipient_list(recipients: list[str]) -> list[str]:
    """Validate a list of email recipient addresses.

    Args:
        recipients: List of email addresses to validate

    Returns:
        List of validated email addresses

    Raises:
        ValueError: If any email address is invalid
        ValueError: If recipient list is empty

    Security Notes:
        - Validates each email individually
        - Removes duplicates
        - Limits total number of recipients
        - Logs validation results

    Examples:
        >>> validate_recipient_list(["user1@example.com", "user2@example.com"])
        ['user1@example.com', 'user2@example.com']

        >>> validate_recipient_list([])
        ValueError: Recipient list cannot be empty
    """
    if not recipients:
        raise ValueError("Recipient list cannot be empty")

    # Limit number of recipients to prevent abuse
    MAX_RECIPIENTS = 100
    if len(recipients) > MAX_RECIPIENTS:
        raise ValueError(
            f"Too many recipients (max {MAX_RECIPIENTS}): {len(recipients)}"
        )

    validated = []
    seen = set()

    for email in recipients:
        try:
            # Validate each email
            valid_email = validate_email_address(email)

            # Skip duplicates
            if valid_email.lower() in seen:
                logger.debug(f"Skipping duplicate recipient: '{valid_email}'")
                continue

            seen.add(valid_email.lower())
            validated.append(valid_email)

        except ValueError as e:
            logger.error(f"Invalid recipient email: '{email}', error: {e}")
            raise ValueError(f"Invalid recipient '{email}': {e}") from e

    logger.info(f"Validated {len(validated)} recipient(s)")
    return validated


def sanitize_subject(subject: str) -> str:
    """Sanitize email subject line to prevent header injection.

    This function removes characters that could be used in email header
    injection attacks, particularly newlines.

    Args:
        subject: Email subject line to sanitize

    Returns:
        Sanitized subject line

    Security Notes:
        - Removes all newline characters (\\r, \\n)
        - Removes null bytes
        - Limits subject length
        - Logs sanitization actions

    Examples:
        >>> sanitize_subject("System Health Report")
        'System Health Report'

        >>> sanitize_subject("Report\\nBcc: attacker@evil.com")
        'Report Bcc: attacker@evil.com'
    """
    if not subject:
        return "No Subject"

    original_subject = subject

    # Remove null bytes
    subject = subject.replace("\x00", "")

    # Remove all types of newlines (prevents header injection)
    # Replace with space to maintain readability
    subject = subject.replace("\r", " ").replace("\n", " ")

    # Collapse multiple spaces
    subject = re.sub(r"\s+", " ", subject)

    # Strip leading/trailing whitespace
    subject = subject.strip()

    # Limit subject length (RFC 5322 recommends max 78 characters per line)
    MAX_SUBJECT_LENGTH = 200
    if len(subject) > MAX_SUBJECT_LENGTH:
        subject = subject[:MAX_SUBJECT_LENGTH] + "..."
        logger.warning(f"Subject line truncated to {MAX_SUBJECT_LENGTH} characters")

    # Use fallback if subject is empty after sanitization
    if not subject:
        subject = "No Subject"

    # Log if sanitization changed the subject
    if subject != original_subject:
        logger.warning(
            f"Subject line sanitized (potential header injection attempt): "
            f"'{original_subject[:50]}'"
        )

    return subject


# fin
