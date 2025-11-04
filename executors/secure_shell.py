#!/usr/bin/env python3

"""Secure shell command executor for SysHealth.

This module provides a secure command executor that uses shell=True
only for validated commands that absolutely require shell features
(pipes, redirects, etc.).
"""

import logging
import subprocess

from executors.validators import CommandValidator, get_default_validator

logger = logging.getLogger("syshealth.executors.secure_shell")


class SecureShellExecutor:
    """Secure command executor with shell=True for validated commands only.

    This executor is used ONLY for commands that require shell features
    such as pipes, redirects, or wildcards. All commands are validated
    against a whitelist before execution.

    Security Features:
        - Command validation against whitelist
        - Logging of all shell command executions
        - Timeout enforcement
        - Error handling and sanitization

    Usage:
        This executor should be used sparingly and only when:
        1. Command requires shell features (pipes, redirects, wildcards)
        2. Command comes from trusted source (config file, not user input)
        3. Command has been validated by CommandValidator

    Example:
        >>> executor = SecureShellExecutor()
        >>> result = executor.execute("cat /proc/cpuinfo | grep processor")
    """

    def __init__(self, validator: CommandValidator | None = None, timeout: int = 30):
        """Initialize secure shell executor.

        Args:
            validator: CommandValidator instance (uses default if None)
            timeout: Command timeout in seconds (default: 30)
        """
        self.validator = validator or get_default_validator()
        self.timeout = timeout
        logger.debug(
            f"Initialized SecureShellExecutor with timeout={timeout}s, "
            f"allowed_commands={len(self.validator.allowed_commands)}"
        )

    def execute(self, command: str) -> str:
        """Execute a validated shell command.

        Args:
            command: Shell command to execute

        Returns:
            Command output (stdout) on success, error message on failure

        Raises:
            ValueError: If command validation fails
            RuntimeError: If command execution fails catastrophically

        Security:
            - Validates command before execution
            - Uses shell=True (necessary for shell features)
            - Enforces timeout
            - Logs all executions for audit trail

        Examples:
            >>> executor = SecureShellExecutor()
            >>> result = executor.execute("ps aux | grep python")
            >>> result = executor.execute("df -h | grep /dev")
        """
        # Validate command first
        is_valid, error_msg = self.validator.validate_command(command)
        if not is_valid:
            logger.error(
                f"Command validation failed: {error_msg}, command: {command[:50]}"
            )
            raise ValueError(f"Command validation failed: {error_msg}")

        # Verify command actually requires shell features
        if not self.validator.requires_shell(command):
            logger.warning(
                f"Command does not require shell features, consider using "
                f"LocalCommandExecutor instead: {command[:50]}"
            )

        # Log shell command execution (security audit trail)
        logger.info(f"Executing shell command (shell=True): {command[:100]}")

        try:
            # Execute with shell=True (validated and necessary for shell features)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True,  # Required for pipes/redirects/wildcards
                timeout=self.timeout,
                check=False,  # Don't raise on non-zero exit
            )

            if result.returncode == 0:
                logger.debug(
                    f"Shell command succeeded: {command[:50]}, "
                    f"output_length={len(result.stdout)}"
                )
                return result.stdout

            # Non-zero exit code
            logger.warning(
                f"Shell command returned non-zero exit code "
                f"{result.returncode}: {command[:50]}"
            )
            return f"Error (exit {result.returncode}): {result.stderr}"

        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {self.timeout} seconds"
            logger.error(f"{error_msg}: {command[:50]}")
            return f"Error: {error_msg}"

        except Exception as e:
            error_msg = f"Command execution failed: {e}"
            logger.error(f"{error_msg}: {command[:50]}")
            return f"Error: {error_msg}"

    def execute_if_valid(self, command: str) -> tuple[bool, str]:
        """Execute command if valid, return success status and output.

        This is a safer wrapper around execute() that returns success/failure
        instead of raising exceptions.

        Args:
            command: Shell command to execute

        Returns:
            Tuple of (success, output)
            - success: True if command was validated and executed
            - output: Command output or error message

        Examples:
            >>> executor = SecureShellExecutor()
            >>> success, output = executor.execute_if_valid("ps aux | grep python")
            >>> if success:
            ...     print(output)
        """
        try:
            output = self.execute(command)
            # Check if output indicates error
            if output.startswith("Error"):
                return False, output
            return True, output
        except (ValueError, RuntimeError) as e:
            return False, f"Error: {e}"


# fin
