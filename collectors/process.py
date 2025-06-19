#!/usr/bin/env python3

"""Process information collector."""

from typing import Dict
from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig

class ProcessInfoCollector(SystemInfoCollector):
  """Collects process and performance information.
  
  This collector gathers information about running processes,
  including top CPU and memory consuming processes.
  """
  
  def __init__(self, executor, config: SystemInfoConfig = None):
    """Initialize the process info collector.
    
    Args:
        executor: Command executor instance
        config (SystemInfoConfig, optional): Command configuration
    """
    super().__init__(executor)
    self.config = config or SystemInfoConfig()
    
  def collect(self) -> Dict[str, str]:
    """Collect process information.
    
    Returns:
        Dict[str, str]: Dictionary containing process information
    """
    return {
      "top_cpu_processes": self._safe_execute(self.config.top_cpu_processes_command),
      "top_mem_processes": self._safe_execute(self.config.top_mem_processes_command),
    }

#fin