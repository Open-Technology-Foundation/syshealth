#!/usr/bin/env python3

"""Basic system information collector."""

import datetime

from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig
from executors.base import CommandExecutor


class BasicSystemInfoCollector(SystemInfoCollector):
    """Collects basic system information like OS, hostname, and uptime.

    This collector handles fundamental system identification information
    that forms the foundation of any system health report.
    """

    def __init__(
        self,
        executor: CommandExecutor,
        hostname: str,
        config: SystemInfoConfig | None = None,
    ):
        """Initialize the basic system info collector.

        Args:
            executor: Command executor instance
            hostname (str): The system hostname
            config (SystemInfoConfig, optional): Command configuration
        """
        super().__init__(executor)
        self.hostname = hostname
        self.config = config or SystemInfoConfig()

    def collect(self) -> dict[str, str]:
        """Collect basic system information.

        Returns:
            dict[str, str]: Dictionary containing basic system information
        """
        return {
            "hostname": self.hostname,
            "timestamp": datetime.datetime.now().isoformat(),
            "uname": self._safe_execute(self.config.uname_command),
            "os_release": self._safe_execute(self.config.os_release_command),
            "uptime": self._safe_execute(self.config.uptime_command),
            "virtualization": self._safe_execute(self.config.virtualization_command),
            "container_info": self._safe_execute(self.config.container_info_command),
        }


# fin
