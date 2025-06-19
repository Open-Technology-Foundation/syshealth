#!/usr/bin/env python3

"""Configuration management for SysHealth.

This module provides centralized configuration management with support for:
- YAML configuration files
- Environment variable overrides
- Default fallback values
- Type validation and conversion
- Nested configuration access
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger("syshealth.config")


class ConfigManager:
  """Manages SysHealth configuration from multiple sources.
  
  Configuration sources in order of precedence (highest to lowest):
  1. Environment variables (SYSHEALTH_<section>_<key>)
  2. YAML configuration file
  3. Default hardcoded values
  
  Example usage:
      config = ConfigManager()
      model = config.get('claude.model')
      timeout = config.get('commands.timeout', 30)
  """
  
  def __init__(self, config_path: Optional[str] = None):
    """Initialize configuration manager.
    
    Args:
        config_path (Optional[str]): Path to YAML config file. If None,
            looks for config/syshealth.yaml relative to the script location.
    """
    self._config = {}
    self._config_path = config_path
    self._load_config()
  
  def _get_default_config_path(self) -> str:
    """Get the default configuration file path."""
    script_dir = Path(__file__).parent.parent
    return str(script_dir / "config" / "syshealth.yaml")
  
  def _load_config(self):
    """Load configuration from file and environment variables."""
    # Determine config file path
    if self._config_path is None:
      self._config_path = self._get_default_config_path()
    
    # Load from YAML file
    self._load_yaml_config()
    
    # Apply environment variable overrides
    self._apply_env_overrides()
  
  def _load_yaml_config(self):
    """Load configuration from YAML file."""
    try:
      config_path = Path(self._config_path)
      if config_path.exists():
        with open(config_path, 'r') as f:
          self._config = yaml.safe_load(f) or {}
        logger.debug(f"Loaded configuration from {config_path}")
      else:
        logger.warning(f"Configuration file not found: {config_path}")
        self._config = {}
    except Exception as e:
      logger.error(f"Failed to load configuration file: {e}")
      self._config = {}
  
  def _apply_env_overrides(self):
    """Apply environment variable overrides to configuration.
    
    Environment variables follow the format: SYSHEALTH_<section>_<key>
    Examples:
      SYSHEALTH_CLAUDE_MODEL overrides claude.model
      SYSHEALTH_OUTPUT_DEFAULT_DIRECTORY overrides output.default_directory
    """
    env_prefix = "SYSHEALTH_"
    
    for env_key, env_value in os.environ.items():
      if not env_key.startswith(env_prefix):
        continue
      
      # Convert environment variable name to config path
      config_path = env_key[len(env_prefix):].lower().replace('_', '.')
      
      # Convert string value to appropriate type
      converted_value = self._convert_env_value(env_value)
      
      # Set the configuration value
      self._set_nested_value(config_path, converted_value)
      logger.debug(f"Applied environment override: {config_path} = {converted_value}")
  
  def _convert_env_value(self, value: str) -> Any:
    """Convert environment variable string to appropriate type.
    
    Args:
        value (str): The environment variable value
        
    Returns:
        Any: Converted value (bool, int, float, or str)
    """
    # Handle boolean values
    if value.lower() in ('true', 'yes', '1', 'on'):
      return True
    elif value.lower() in ('false', 'no', '0', 'off'):
      return False
    
    # Handle numeric values
    try:
      if '.' in value:
        return float(value)
      else:
        return int(value)
    except ValueError:
      pass
    
    # Return as string
    return value
  
  def _set_nested_value(self, path: str, value: Any):
    """Set a nested configuration value using dot notation.
    
    Args:
        path (str): Dot-separated path (e.g., 'claude.model')
        value (Any): Value to set
    """
    keys = path.split('.')
    current = self._config
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
      if key not in current:
        current[key] = {}
      current = current[key]
    
    # Set the final value
    current[keys[-1]] = value
  
  def get(self, path: str, default: Any = None) -> Any:
    """Get a configuration value using dot notation.
    
    Args:
        path (str): Dot-separated path (e.g., 'claude.model')
        default (Any): Default value if path not found
        
    Returns:
        Any: Configuration value or default
    """
    keys = path.split('.')
    current = self._config
    
    try:
      for key in keys:
        current = current[key]
      return current
    except (KeyError, TypeError):
      return default
  
  def get_section(self, section: str) -> Dict[str, Any]:
    """Get an entire configuration section.
    
    Args:
        section (str): Section name (e.g., 'claude')
        
    Returns:
        Dict[str, Any]: Configuration section or empty dict
    """
    return self._config.get(section, {})
  
  def set(self, path: str, value: Any):
    """Set a configuration value using dot notation.
    
    Args:
        path (str): Dot-separated path (e.g., 'claude.model')
        value (Any): Value to set
    """
    self._set_nested_value(path, value)
  
  def has(self, path: str) -> bool:
    """Check if a configuration path exists.
    
    Args:
        path (str): Dot-separated path (e.g., 'claude.model')
        
    Returns:
        bool: True if path exists, False otherwise
    """
    keys = path.split('.')
    current = self._config
    
    try:
      for key in keys:
        current = current[key]
      return True
    except (KeyError, TypeError):
      return False
  
  def expand_path(self, path: str) -> str:
    """Expand a file path with user home directory and environment variables.
    
    Args:
        path (str): Path to expand (may contain ~ or environment variables)
        
    Returns:
        str: Expanded absolute path
    """
    # Expand user home directory
    expanded = os.path.expanduser(path)
    # Expand environment variables
    expanded = os.path.expandvars(expanded)
    # Convert to absolute path
    return os.path.abspath(expanded)
  
  def get_expanded_path(self, path: str, default: str = None) -> str:
    """Get a configuration path value and expand it.
    
    Args:
        path (str): Configuration path (e.g., 'output.default_directory')
        default (str): Default path if not found
        
    Returns:
        str: Expanded absolute path
    """
    config_path = self.get(path, default)
    if config_path is None:
      return None
    return self.expand_path(config_path)
  
  def reload(self):
    """Reload configuration from file and environment variables."""
    self._load_config()
  
  def to_dict(self) -> Dict[str, Any]:
    """Get the entire configuration as a dictionary.
    
    Returns:
        Dict[str, Any]: Complete configuration dictionary
    """
    return self._config.copy()
  
  def __str__(self) -> str:
    """String representation of the configuration."""
    return f"ConfigManager(config_path='{self._config_path}')"
  
  def __repr__(self) -> str:
    """Detailed string representation of the configuration."""
    return f"ConfigManager(config_path='{self._config_path}', keys={list(self._config.keys())})"


# Global configuration instance
_global_config = None


def get_config() -> ConfigManager:
  """Get the global configuration instance.
  
  Returns:
      ConfigManager: Global configuration instance
  """
  global _global_config
  if _global_config is None:
    _global_config = ConfigManager()
  return _global_config


def reload_config():
  """Reload the global configuration."""
  global _global_config
  if _global_config is not None:
    _global_config.reload()


# Convenience functions for common configuration values
def get_claude_model() -> str:
  """Get the Claude model name."""
  return get_config().get('claude.model', 'claude-3-7-sonnet-20250219')


def get_default_language() -> str:
  """Get the default report language."""
  return get_config().get('language.default', 'en')


def get_output_directory() -> str:
  """Get the default output directory (expanded)."""
  return get_config().get_expanded_path('output.default_directory', '~/syshealth')


def get_command_timeout() -> int:
  """Get the default command timeout."""
  return get_config().get('commands.timeout', 30)


def get_claude_timeout() -> int:
  """Get the Claude API timeout."""
  return get_config().get('claude.timeout', 300)


def get_log_format() -> str:
  """Get the logging format string."""
  return get_config().get('logging.format', '%(asctime)s - %(levelname)s - %(message)s')


def get_smtp_settings() -> Dict[str, Any]:
  """Get SMTP configuration settings."""
  return get_config().get_section('email.smtp')


def get_report_thresholds() -> Dict[str, Any]:
  """Get report threshold settings."""
  return get_config().get_section('report.thresholds')


#fin