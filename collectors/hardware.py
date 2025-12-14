#!/usr/bin/env python3

"""Hardware information collector."""

from typing import override

from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig
from executors.base import CommandExecutor


class HardwareInfoCollector(SystemInfoCollector):
    """Collects hardware and CPU information.

    This collector gathers detailed information about the system's hardware
    components including CPU details, model information, and general hardware listing.
    """

    def __init__(
        self, executor: CommandExecutor, config: SystemInfoConfig | None = None
    ):
        """Initialize the hardware info collector.

        Args:
            executor: Command executor instance
            config (SystemInfoConfig, optional): Command configuration
        """
        super().__init__(executor)
        self.config = config or SystemInfoConfig()

    @override
    def collect(self) -> dict[str, str]:
        """Collect hardware information.

        Returns:
            dict[str, str]: Dictionary containing hardware information
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

        # Temperature monitoring
        info["temperature"] = self._safe_execute(
            self.config.temperature_command,
            "Temperature information not available (install: sudo apt install lm-sensors)",
        )

        return info


# fin
