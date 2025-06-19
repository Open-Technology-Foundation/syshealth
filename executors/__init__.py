"""Command execution module.

This module provides abstractions for executing system commands both locally
and remotely, enabling dependency injection and easier testing.
"""

from .base import CommandExecutor
from .local import LocalCommandExecutor
from .remote import RemoteCommandExecutor

__all__ = [
  "CommandExecutor",
  "LocalCommandExecutor", 
  "RemoteCommandExecutor",
]

#fin