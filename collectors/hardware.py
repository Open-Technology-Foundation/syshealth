#!/usr/bin/env python3

"""Hardware information collector."""

from typing import Dict
from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig

class HardwareInfoCollector(SystemInfoCollector):
  """Collects hardware and CPU information.
  
  This collector gathers detailed information about the system's hardware
  components including CPU details, model information, and general hardware listing.
  """
  
  def __init__(self, executor, config: SystemInfoConfig = None):
    """Initialize the hardware info collector.
    
    Args:
        executor: Command executor instance
        config (SystemInfoConfig, optional): Command configuration
    """
    super().__init__(executor)
    self.config = config or SystemInfoConfig()
    
  def collect(self) -> Dict[str, str]:
    """Collect hardware information.
    
    Returns:
        Dict[str, str]: Dictionary containing hardware information
    """
    info = {}
    
    # Hardware listing with fallback
    try:
      hardware_output = self.executor.execute(self.config.hardware_list_command)
      if not hardware_output.startswith("Error"):
        info["hardware"] = hardware_output
      else:
        info["hardware"] = "lshw not available"
    except Exception:
      info["hardware"] = "lshw not available"
    
    # CPU information
    info["cpu_model"] = self._safe_execute(self.config.cpu_model_command)
    info["cpu_info"] = self._safe_execute(self.config.cpu_info_command)
    
    # Memory information
    info["memory"] = self._safe_execute(self.config.memory_command)
    info["swap_info"] = self._safe_execute(self.config.swap_info_command)
    
    return info

#fin