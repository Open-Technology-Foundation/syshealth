#!/usr/bin/env python3

"""Base system information collector class."""

from abc import ABC, abstractmethod
from typing import Dict
from executors.base import CommandExecutor

class SystemInfoCollector(ABC):
  """Abstract base class for system information collectors.
  
  This class defines the interface that all specialized collectors must implement.
  It uses dependency injection to receive a command executor, enabling better
  testing and flexibility.
  """
  
  def __init__(self, executor: CommandExecutor):
    """Initialize the collector with a command executor.
    
    Args:
        executor (CommandExecutor): The command executor to use for running commands
    """
    self.executor = executor
    
  @abstractmethod
  def collect(self) -> Dict[str, str]:
    """Collect system information for this collector's domain.
    
    Returns:
        Dict[str, str]: Dictionary containing the collected information
            with descriptive keys and string values (command outputs)
    """
    pass
    
  def _safe_execute(self, command: str, fallback: str = "Information not available") -> str:
    """Safely execute a command with fallback handling.
    
    Args:
        command (str): The command to execute
        fallback (str): Fallback message if command fails
        
    Returns:
        str: Command output or fallback message
    """
    try:
      result = self.executor.execute(command)
      if result.startswith("Error"):
        return fallback
      return result
    except Exception:
      return fallback

#fin