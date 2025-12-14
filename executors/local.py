#!/usr/bin/env python3

"""Local command executor implementation with security validation.

This module provides a secure local command executor that validates all
commands before execution and uses shell=True only for validated commands
that require shell features.
"""

import logging
import shlex
import subprocess

from executors.secure_shell import SecureShellExecutor
from executors.validators import CommandValidator, get_default_validator

logger = logging.getLogger("syshealth.executors.local")


class LocalCommandExecutor:
    """Executes commands on the local system with security validation.

    This executor validates all commands before execution using a whitelist-based
    validator. Commands requiring shell features (pipes, redirects, etc.) are
    routed to SecureShellExecutor, while simple commands are executed with
    shell=False for improved security.

    Security Features:
        - Command validation against whitelist
        - Automatic detection of shell feature requirements
        - Routing to SecureShellExecutor for shell commands
        - shell=False for simple commands (prevents injection)
        - Comprehensive logging for audit trail

    Attributes:
        validator: CommandValidator instance for validating commands
        shell_executor: SecureShellExecutor for commands requiring shell features
        timeout: Command timeout in seconds

    Example:
        >>> executor = LocalCommandExecutor()
        >>> result = executor.execute("df -h")  # Simple command, shell=False
        >>> result = executor.execute("ps aux | grep python")  # Shell command, validated
    """

    def __init__(
        self,
        validator: CommandValidator | None = None,
        timeout: int = 30,
    ):
        """Initialize local command executor.

        Args:
            validator: CommandValidator instance (uses default if None)
            timeout: Command timeout in seconds (default: 30)

        Note:
            Creates two validators:
            - self.validator: allow_shell_features=False for simple commands
            - shell_executor.validator: allow_shell_features=True for shell commands
        """
        self.validator = validator or get_default_validator()
        # Don't pass validator to SecureShellExecutor - let it create its own
        # with allow_shell_features=True
        self.shell_executor = SecureShellExecutor(timeout=timeout)
        self.timeout = timeout
        logger.debug(
            f"Initialized LocalCommandExecutor with timeout={timeout}s, "
            f"validator with {len(self.validator.allowed_commands)} allowed commands"
        )

    def execute(self, command: str) -> str:
        """Execute a command locally with security validation.

        This method determines if the command requires shell features, then routes it
        to the appropriate executor. Commands with shell features are routed to
        SecureShellExecutor (which validates with allow_shell_features=True), while
        simple commands are validated and executed with shell=False.

        Args:
            command: The command to execute

        Returns:
            Command output on success, error message on failure

        Security:
            - Detects shell feature requirements first
            - Routes shell commands to SecureShellExecutor for validation
            - Validates simple commands then executes with shell=False
            - Logs all executions for audit trail

        Examples:
            >>> executor = LocalCommandExecutor()
            >>> executor.execute("uptime")  # Simple command, shell=False
            >>> executor.execute("ps aux | grep python")  # Shell command, validated
        """
        if not command or not command.strip():
            logger.error("Empty command provided to LocalCommandExecutor")
            return "Error: Command cannot be empty"

        # Check if command requires shell features FIRST
        # This determines which validator to use (allow_shell_features or not)
        if self.validator.requires_shell(command):
            # Route to SecureShellExecutor for shell commands
            # SecureShellExecutor will validate with allow_shell_features=True
            logger.debug(f"Routing shell command to SecureShellExecutor: {command[:50]}")
            return self.shell_executor.execute(command)

        # For simple commands: validate with allow_shell_features=False
        is_valid, error_msg = self.validator.validate_command(command)
        if not is_valid:
            logger.error(f"Command validation failed: {error_msg}, command: {command[:50]}")
            return f"Error: Command validation failed: {error_msg}"

        # Execute simple command with shell=False (more secure)
        return self._execute_simple_command(command)

    def _execute_simple_command(self, command: str) -> str:
        """Execute a simple command without shell features using shell=False.

        This method is used for commands that don't require shell features,
        providing better security by avoiding shell=True.

        Args:
            command: The command to execute (no pipes, redirects, etc.)

        Returns:
            Command output on success, error message on failure

        Security:
            - Uses shell=False to prevent injection
            - Uses shlex.split() for safe argument parsing
            - Enforces timeout
            - Logs execution for audit
        """
        try:
            # Split command into arguments safely
            # shlex.split handles quoted arguments correctly
            cmd_args = shlex.split(command)

            logger.info(f"Executing simple command (shell=False): {command[:100]}")
            logger.debug(f"Command arguments: {cmd_args}")

            # Execute without shell for better security
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                shell=False,  # More secure for simple commands
                timeout=self.timeout,
                check=False,  # Don't raise on non-zero exit
            )

            if result.returncode != 0:
                logger.warning(
                    f"Simple command returned non-zero exit code "
                    f"{result.returncode}: {command[:50]}"
                )
                return f"Error (exit {result.returncode}): {result.stderr}"

            logger.debug(
                f"Simple command succeeded: {command[:50]}, "
                f"output_length={len(result.stdout)}"
            )
            return result.stdout

        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {self.timeout} seconds"
            logger.error(f"{error_msg}: {command[:50]}")
            return f"Error: {error_msg}"

        except FileNotFoundError as e:
            # Command executable not found
            logger.error(f"Command not found: {command[:50]}, error={e}")
            return f"Error: Command not found: {e}"

        except Exception as e:
            logger.error(f"Command execution failed: {command[:50]}, error={e}")
            return f"Error executing command: {str(e)}"


# fin
