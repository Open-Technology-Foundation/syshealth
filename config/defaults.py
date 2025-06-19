#!/usr/bin/env python3

"""Default command configurations for system information collection."""

from config.system_commands import SystemInfoConfig

# Default configuration instance for Ubuntu/Debian systems
DEFAULT_COMMANDS = SystemInfoConfig()

# Distribution-specific configurations can be added here as needed
UBUNTU_COMMANDS = SystemInfoConfig.for_distribution("ubuntu")
CENTOS_COMMANDS = SystemInfoConfig.for_distribution("centos") 
ARCH_COMMANDS = SystemInfoConfig.for_distribution("arch")

#fin