#!/usr/bin/env python3

"""Base command executor protocol for dependency injection."""

from abc import ABC, abstractmethod
from typing import Protocol

class CommandExecutor(Protocol):
  """Protocol for command execution abstraction.
  
  This protocol defines the interface for executing system commands,
  enabling dependency injection and easier testing through mocking.
  """
  
  def execute(self, command: str) -> str:
    """Execute a command and return its output.
    
    Args:
        command (str): The command to execute
        
    Returns:
        str: The command output or error message
    """
    ...

#fin