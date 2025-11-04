"""System information collectors module.

This module provides specialized collectors for different aspects of system information.
Each collector focuses on a specific category of system data, making the code more
modular, testable, and maintainable.
"""

from .base import SystemInfoCollector
from .basic import BasicSystemInfoCollector
from .hardware import HardwareInfoCollector
from .network import NetworkInfoCollector
from .process import ProcessInfoCollector
from .security import SecurityInfoCollector
from .storage import StorageInfoCollector

__all__ = [
    "SystemInfoCollector",
    "BasicSystemInfoCollector",
    "HardwareInfoCollector",
    "StorageInfoCollector",
    "ProcessInfoCollector",
    "NetworkInfoCollector",
    "SecurityInfoCollector",
]

# fin
