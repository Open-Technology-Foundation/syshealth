#!/usr/bin/env python3

"""Local command executor implementation."""

import logging
import subprocess
from typing import Optional

logger = logging.getLogger("syshealth.executors.local")

class LocalCommandExecutor:
  """Executes commands on the local system.
  
  This executor runs commands locally using subprocess with proper
  error handling and security considerations.
  """
  
  def execute(self, command: str) -> str:
    """Execute a command locally.
    
    Args:
        command (str): The command to execute
        
    Returns:
        str: The command output or error message
    """
    try:
      # Use shell=True for local execution to support pipes and redirects
      # Note: This maintains current behavior but should be addressed in security fixes
      result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        shell=True
      )
      
      if result.returncode != 0:
        logger.warning(f"Local command returned non-zero exit status: {command}")
        return f"Error: {result.stderr}"
      
      return result.stdout
    except Exception as e:
      logger.warning(f"Local command failed: {command} - {e}")
      return f"Error executing command: {str(e)}"

#fin