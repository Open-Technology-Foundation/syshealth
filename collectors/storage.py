#!/usr/bin/env python3

"""Storage information collector."""


from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig
from executors.base import CommandExecutor


class StorageInfoCollector(SystemInfoCollector):
    """Collects storage and filesystem information.

    This collector gathers information about disk usage, block devices,
    storage health, and filesystem configuration.
    """

    def __init__(
        self, executor: CommandExecutor, config: SystemInfoConfig | None = None
    ):
        """Initialize the storage info collector.

        Args:
            executor: Command executor instance
            config (SystemInfoConfig, optional): Command configuration
        """
        super().__init__(executor)
        self.config = config or SystemInfoConfig()

    def collect(self) -> dict[str, str]:
        """Collect storage information.

        Returns:
            dict[str, str]: Dictionary containing storage information
        """
        return {
            "disk_usage": self._safe_execute(self.config.disk_usage_command),
            "block_devices": self._safe_execute(
                self.config.block_devices_command, "lsblk not available"
            ),
            "disk_health": self._safe_execute(
                self.config.disk_health_command,
                "Disk health information not available (requires root)",
            ),
            "fstab": self._safe_execute(
                self.config.fstab_command, "fstab not available"
            ),
        }


# fin
