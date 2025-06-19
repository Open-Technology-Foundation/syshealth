#!/usr/bin/env python3

"""Storage information collector."""

from typing import Dict
from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig

class StorageInfoCollector(SystemInfoCollector):
  """Collects storage and filesystem information.
  
  This collector gathers information about disk usage, block devices,
  storage health, and filesystem configuration.
  """
  
  def __init__(self, executor, config: SystemInfoConfig = None):
    """Initialize the storage info collector.
    
    Args:
        executor: Command executor instance
        config (SystemInfoConfig, optional): Command configuration
    """
    super().__init__(executor)
    self.config = config or SystemInfoConfig()
    
  def collect(self) -> Dict[str, str]:
    """Collect storage information.
    
    Returns:
        Dict[str, str]: Dictionary containing storage information
    """
    return {
      "disk_usage": self._safe_execute(self.config.disk_usage_command),
      "block_devices": self._safe_execute(
        self.config.block_devices_command, 
        "lsblk not available"
      ),
      "disk_health": self._safe_execute(
        self.config.disk_health_command,
        "Disk health information not available (requires root)"
      ),
      "fstab": self._safe_execute(
        self.config.fstab_command,
        "fstab not available"
      ),
    }

#fin