#!/usr/bin/env python3

"""Process information collector."""


from collectors.base import SystemInfoCollector
from config.system_commands import SystemInfoConfig
from executors.base import CommandExecutor


class ProcessInfoCollector(SystemInfoCollector):
    """Collects process and performance information.

    This collector gathers information about running processes,
    including top CPU and memory consuming processes.
    """

    def __init__(
        self, executor: CommandExecutor, config: SystemInfoConfig | None = None
    ):
        """Initialize the process info collector.

        Args:
            executor: Command executor instance
            config (SystemInfoConfig, optional): Command configuration
        """
        super().__init__(executor)
        self.config = config or SystemInfoConfig()

    def collect(self) -> dict[str, str]:
        """Collect process information.

        Returns:
            dict[str, str]: Dictionary containing process information
        """
        return {
            "top_cpu_processes": self._safe_execute(
                self.config.top_cpu_processes_command
            ),
            "top_mem_processes": self._safe_execute(
                self.config.top_mem_processes_command
            ),
        }


# fin
