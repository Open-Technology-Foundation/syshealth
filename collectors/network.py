#!/usr/bin/env python3

"""Network information collector."""

from typing import Dict
from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig

class NetworkInfoCollector(SystemInfoCollector):
  """Collects network configuration information.
  
  This collector gathers information about network interfaces,
  listening ports, and network connectivity.
  """
  
  def __init__(self, executor, config: SystemInfoConfig = None):
    """Initialize the network info collector.
    
    Args:
        executor: Command executor instance
        config (SystemInfoConfig, optional): Command configuration
    """
    super().__init__(executor)
    self.config = config or SystemInfoConfig()
    
  def collect(self) -> Dict[str, str]:
    """Collect network information.
    
    Returns:
        Dict[str, str]: Dictionary containing network information
    """
    return {
      "network_interfaces": self._safe_execute(
        self.config.network_interfaces_command,
        "Network information not available"
      ),
      "listening_ports": self._safe_execute(
        self.config.listening_ports_command,
        "Port information not available"
      ),
    }

#fin