#!/usr/bin/env python3

"""Command validation for SysHealth.

This module provides validation utilities to prevent command injection attacks
and ensure only approved commands are executed.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("syshealth.executors.validators")

# Shell metacharacters that could be used for injection
SHELL_METACHARACTERS = {
    ";",
    "&",
    "|",
    "`",
    "$",
    "(",
    ")",
    "<",
    ">",
    "\n",
    "\r",
}


@dataclass
class CommandValidator:
    """Validator for command execution security.

    This class provides methods to validate commands before execution,
    preventing command injection and ensuring only approved commands
    are run.

    Attributes:
        allowed_commands: Set of command names that are whitelisted
        allow_shell_features: Whether to allow commands with shell features
            (pipes, redirects) - these require special handling
    """

    allowed_commands: set[str] = field(default_factory=set)
    allow_shell_features: bool = False

    def __post_init__(self) -> None:
        """Initialize validator with default allowed commands if empty."""
        if not self.allowed_commands:
            self.allowed_commands = self._get_default_allowed_commands()
            logger.debug(
                f"Initialized CommandValidator with {len(self.allowed_commands)} "
                f"default commands"
            )

    @staticmethod
    def _get_default_allowed_commands() -> set[str]:
        """Get the default set of allowed commands for system monitoring.

        Returns:
            Set of command names that are safe for system monitoring

        Security Notes:
            - Only includes read-only system monitoring commands
            - No commands that modify system state
            - No commands that can execute other programs
            - All commands are standard Linux utilities
        """
        return {
            # System information
            "uname",
            "hostname",
            "uptime",
            "date",
            # Hardware
            "lshw",
            "lscpu",
            "lspci",
            "lsusb",
            "dmidecode",
            # Memory
            "free",
            "vmstat",
            # Storage
            "df",
            "lsblk",
            "mount",
            "smartctl",
            # Processes
            "ps",
            "top",
            "pgrep",
            # Network
            "ip",
            "ifconfig",
            "netstat",
            "ss",
            # System logs
            "dmesg",
            "journalctl",
            "last",
            "lastlog",
            # Security
            "chkrootkit",
            "rkhunter",
            # Package management (read-only)
            "apt-get",  # Only with specific safe arguments
            "dpkg",
            "rpm",
            "yum",
            # File operations (read-only)
            "cat",
            "grep",
            "head",
            "tail",
            "wc",
            # System status
            "systemctl",
            "service",
        }

    def validate_command(self, command: str) -> tuple[bool, str]:
        """Validate a command string for safe execution.

        Args:
            command: The command string to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if command is safe to execute
            - error_message: Empty string if valid, error description if invalid

        Security Checks:
            1. Command is not empty
            2. Base command is in allowed list
            3. No shell metacharacters (unless shell features allowed)
            4. No suspicious patterns (command substitution, etc.)
            5. No null bytes or non-printable characters

        Examples:
            >>> validator = CommandValidator()
            >>> validator.validate_command("df -h")
            (True, '')

            >>> validator.validate_command("rm -rf /")
            (False, 'Command not in allowed list: rm')

            >>> validator.validate_command("ps aux; rm -rf /")
            (False, 'Command contains dangerous shell metacharacter: ;')
        """
        # Check for empty command
        if not command or not command.strip():
            return False, "Command cannot be empty"

        # Check for null bytes (can bypass some security checks)
        if "\x00" in command:
            logger.error(f"Null byte detected in command: {repr(command[:50])}")
            return False, "Command contains null bytes"

        # Check for non-printable characters (except space and tab)
        if any(ord(c) < 32 and c not in (" ", "\t") for c in command):
            logger.error(f"Non-printable characters in command: {repr(command[:50])}")
            return False, "Command contains non-printable characters"

        # Extract base command (first word)
        base_command = command.strip().split()[0] if command.strip() else ""

        # Remove sudo/doas prefix if present
        if base_command in ("sudo", "doas"):
            parts = command.strip().split()
            if len(parts) > 1:
                base_command = parts[1]
            else:
                return False, "sudo/doas without command"

        # Check if base command is in allowed list
        if base_command not in self.allowed_commands:
            logger.warning(f"Command not in allowed list: {base_command}")
            return False, f"Command not in allowed list: {base_command}"

        # Check for shell metacharacters
        if not self.allow_shell_features:
            for char in SHELL_METACHARACTERS:
                if char in command:
                    logger.error(
                        f"Shell metacharacter '{char}' detected in: {command[:50]}"
                    )
                    return (
                        False,
                        f"Command contains dangerous shell metacharacter: {char}",
                    )

        # Check for command substitution patterns
        if "$(" in command or "`" in command:
            logger.error(f"Command substitution detected in: {command[:50]}")
            return False, "Command substitution not allowed"

        # Check for suspicious patterns
        suspicious_patterns = [
            r"\$\{",  # Variable expansion ${var}
            r"\beval\b",  # eval command
            r"\bexec\b",  # exec command
            r"\bsource\b",  # source command
            r"\b\.\s+",  # dot command (. script.sh)
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, command):
                logger.error(f"Suspicious pattern detected in: {command[:50]}")
                return False, f"Command contains suspicious pattern: {pattern}"

        # All checks passed
        logger.debug(f"Command validation passed: {command[:50]}")
        return True, ""

    def requires_shell(self, command: str) -> bool:
        """Determine if a command requires shell features.

        Args:
            command: The command string to check

        Returns:
            True if command requires shell=True for execution

        Shell features include:
            - Pipes (|)
            - Redirects (<, >, >>)
            - Command chaining (;, &&, ||)
            - Background execution (&)
            - Command substitution ($(...), `...`)

        Examples:
            >>> validator = CommandValidator()
            >>> validator.requires_shell("ps aux")
            False

            >>> validator.requires_shell("ps aux | grep python")
            True

            >>> validator.requires_shell("cat file > output.txt")
            True
        """
        # Check for pipe
        if "|" in command:
            return True

        # Check for redirects
        if any(op in command for op in ("<", ">", ">>")):
            return True

        # Check for command chaining
        if any(op in command for op in (";", "&&", "||")):
            return True

        # Check for background execution
        if command.strip().endswith("&"):
            return True

        # Check for command substitution
        if "$(" in command or "`" in command:
            return True

        # Check for wildcards (some implementations need shell)
        if any(wildcard in command for wildcard in ("*", "?", "[")):
            return True

        return False

    def add_allowed_command(self, command: str) -> None:
        """Add a command to the allowed list.

        Args:
            command: Command name to allow

        Security Notes:
            - Use sparingly - only add commands you trust
            - Consider implications of allowing new commands
            - Log all additions for audit trail
        """
        if command not in self.allowed_commands:
            self.allowed_commands.add(command)
            logger.info(f"Added command to allowed list: {command}")

    def remove_allowed_command(self, command: str) -> None:
        """Remove a command from the allowed list.

        Args:
            command: Command name to disallow
        """
        if command in self.allowed_commands:
            self.allowed_commands.remove(command)
            logger.info(f"Removed command from allowed list: {command}")


# Default global validator instance
_default_validator: CommandValidator | None = None


def get_default_validator() -> CommandValidator:
    """Get the default command validator instance.

    Returns:
        Shared CommandValidator instance with default settings
    """
    global _default_validator
    if _default_validator is None:
        _default_validator = CommandValidator()
    return _default_validator


# fin
