#!/usr/bin/env python3

"""Storage information collector."""

from typing import override

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

    def _get_physical_disks(self) -> list[str]:
        """Discover all physical disks on the system.

        Uses lsblk to detect all physical disk devices, excluding partitions,
        loop devices, and other non-disk block devices.

        Returns:
            list[str]: List of disk device names (e.g., ['nvme0n1', 'sda', 'sdb'])
                      Returns ['nvme0n1'] as fallback if detection fails
        """
        result = self._safe_execute(
            "lsblk --noheadings --output NAME,TYPE 2>/dev/null", ""
        )

        if not result or result == "":
            # Fallback to single disk if detection fails
            return ["nvme0n1"]

        disks = []
        for line in result.strip().split("\n"):
            if "disk" in line:
                parts = line.strip().split()
                if parts and not parts[0].startswith("zd"):
                    disks.append(parts[0])

        # Return fallback if no disks detected
        return disks if disks else ["nvme0n1"]

    def _collect_disk_health(self) -> str:
        """Collect SMART health status for all physical disks.

        Discovers all physical disks using lsblk, then checks SMART health
        for each disk. Handles different disk types (NVMe, SATA) automatically.

        Returns:
            str: Combined SMART health status for all disks, with clear
                 separation between each disk's results
        """
        disks = self._get_physical_disks()

        if not disks:
            return "No physical disks detected"

        results = []
        for disk in disks:
            health = self._safe_execute(
                f"timeout 30s smartctl -H /dev/{disk} 2>/dev/null",
                f"SMART data unavailable for {disk} (requires root or smartctl not installed)",
            )
            results.append(f"=== /dev/{disk} ===\n{health}")

        return "\n\n".join(results)

    @override
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
            "disk_health": self._collect_disk_health(),
            "fstab": self._safe_execute(
                self.config.fstab_command, "fstab not available"
            ),
            "raid_status": self._safe_execute(
                self.config.raid_status_command, "RAID information not available"
            ),
            "raid_detail": self._safe_execute(
                self.config.raid_detail_command, "RAID details not available"
            ),
            "lvm_volumes": self._safe_execute(
                self.config.lvm_volumes_command, "LVM information not available"
            ),
            "lvm_groups": self._safe_execute(
                self.config.lvm_groups_command, "LVM information not available"
            ),
            "lvm_physical": self._safe_execute(
                self.config.lvm_physical_command, "LVM information not available"
            ),
        }


# fin
