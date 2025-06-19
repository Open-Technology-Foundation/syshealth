#!/usr/bin/env python3

"""Remote command executor implementation."""

import logging
import subprocess
import socket
from typing import Optional

logger = logging.getLogger("syshealth.executors.remote")

class RemoteCommandExecutor:
  """Executes commands on a remote system via SSH.
  
  This executor runs commands on remote hosts using SSH with key-based
  authentication. It handles SSH connection failures gracefully.
  """
  
  def __init__(self, hostname: str):
    """Initialize the remote executor.
    
    Args:
        hostname (str): The remote hostname to connect to
    """
    self.hostname = hostname
    
  def execute(self, command: str) -> str:
    """Execute a command on the remote host.
    
    Args:
        command (str): The command to execute
        
    Returns:
        str: The command output or error message
    """
    try:
      # For SSH remote execution, pass the command as an argument
      full_cmd = ["ssh", self.hostname, command]
      
      result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        check=False,
        shell=False
      )
      
      if result.returncode != 0:
        logger.warning(f"Remote command on {self.hostname} returned non-zero exit status: {command}")
        return f"Error: {result.stderr}"
      
      return result.stdout
    except Exception as e:
      logger.warning(f"Remote command failed on {self.hostname}: {command} - {e}")
      return f"Error executing remote command: {str(e)}"

#fin