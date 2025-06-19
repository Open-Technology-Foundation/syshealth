"""Configuration management module.

This module provides configuration classes and default command definitions
for system information collection across different Linux distributions.
"""

from .system_commands import SystemInfoConfig
from .defaults import DEFAULT_COMMANDS
from .config_manager import (
    ConfigManager, 
    get_config, 
    reload_config,
    get_claude_model,
    get_default_language,
    get_output_directory,
    get_command_timeout,
    get_claude_timeout,
    get_log_format,
    get_smtp_settings,
    get_report_thresholds
)

__all__ = [
  "SystemInfoConfig",
  "DEFAULT_COMMANDS",
  "ConfigManager",
  "get_config",
  "reload_config",
  "get_claude_model",
  "get_default_language", 
  "get_output_directory",
  "get_command_timeout",
  "get_claude_timeout",
  "get_log_format",
  "get_smtp_settings",
  "get_report_thresholds"
]

#fin