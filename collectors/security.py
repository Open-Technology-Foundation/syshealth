#!/usr/bin/env python3

"""Security and system health information collector."""

from typing import Dict
from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig

class SecurityInfoCollector(SystemInfoCollector):
  """Collects security and system health information.
  
  This collector gathers information about system services, logs,
  security updates, and maintenance tasks.
  """
  
  def __init__(self, executor, config: SystemInfoConfig = None):
    """Initialize the security info collector.
    
    Args:
        executor: Command executor instance
        config (SystemInfoConfig, optional): Command configuration
    """
    super().__init__(executor)
    self.config = config or SystemInfoConfig()
    
  def collect(self) -> Dict[str, str]:
    """Collect security and system health information.
    
    Returns:
        Dict[str, str]: Dictionary containing security information
    """
    return {
      # System services
      "failed_services": self._safe_execute(
        self.config.failed_services_command,
        "Failed services information not available"
      ),
      
      # System logs
      "recent_errors": self._safe_execute(
        self.config.recent_errors_command,
        "Error logs not available"
      ),
      "auth_failures": self._safe_execute(
        self.config.auth_failures_command,
        "Authentication logs not available"
      ),
      
      # Security and maintenance
      "available_updates": self._safe_execute(
        self.config.available_updates_command,
        "Update information not available"
      ),
      "rootkit_check": self._safe_execute(
        self.config.rootkit_check_command,
        "Rootkit check logs not available"
      ),
      "cron_jobs": self._safe_execute(
        self.config.cron_jobs_command,
        "Crontab information not available"
      ),
    }

#fin