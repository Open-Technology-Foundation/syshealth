#!/usr/bin/env python3

"""Claude API Client for SysHealth

This module provides a client for interacting with the Claude AI API,
specifically for analyzing system health information and generating
comprehensive health reports. It handles communication with the Anthropic API,
prompt generation, and response processing.

The client requires an Anthropic API key, which can be provided during
instantiation or via the ANTHROPIC_API_KEY environment variable.
"""

import json
import logging
import os
import sys
from typing import Dict, Optional, Union

# Import the Anthropic library
import anthropic

# Import configuration management
from config import get_config, get_claude_model, get_claude_timeout

# Configure logging - will inherit level from parent logger
logger = logging.getLogger("syshealth.claude_client")

class ClaudeClient:
  """Client for interacting with the Claude API to analyze system health information.
  
  This client handles authentication with the Anthropic API, generates appropriate
  prompts for system health analysis, and processes the responses. It's designed
  to work with the system information collected by the SysHealth tool.
  """
  
  def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
    """Initialize the Claude client with API key and model selection.
    
    Args:
        api_key (Optional[str], optional): Anthropic API key. If None, will attempt to
            use the ANTHROPIC_API_KEY environment variable. Defaults to None.
        model (Optional[str], optional): The Claude model to use. If None, uses configured default.
    
    Raises:
        RuntimeError: If client initialization fails, typically due to invalid API key
            or network issues
    """
    self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    self.model = model or get_claude_model()
    self.timeout = get_claude_timeout()
    
    if not self.api_key:
      logger.error("No API key provided and ANTHROPIC_API_KEY environment variable not set")
      raise RuntimeError("API key is required. Set ANTHROPIC_API_KEY environment variable or provide api_key parameter")
    
    # Create the client
    try:
      self.client = anthropic.Anthropic(api_key=self.api_key)
      logger.info(f"Claude client initialized with model: {self.model}")
    except Exception as e:
      logger.error(f"Error initializing Anthropic client: {e}")
      raise RuntimeError(f"Failed to initialize Claude client: {e}")
  
  def analyze_system(self, system_info: Dict, language: str = "en") -> str:
    """Analyze system information using Claude API and generate a health report.
    
    This method takes the collected system information, generates an appropriate prompt
    for Claude, sends the request to the API, and returns the generated health report.
    
    Args:
        system_info (Dict): Dictionary containing all the collected system information
        language (str, optional): The language code for the report. Defaults to "en" (English).
            Can be any language code supported by Claude (e.g., "es", "fr", "de", etc.)
    
    Returns:
        str: The markdown-formatted system health report generated by Claude
    
    Raises:
        RuntimeError: If the API call fails for any reason
    """
    # Generate the prompt for Claude
    prompt = self._generate_prompt(system_info, language)
    
    # Log the prompt in debug mode
    logger.debug(f"Prompt sent to Claude API:\n{'-'*40}\n{prompt}\n{'-'*40}")
    
    # Call the API
    try:
      logger.info(f"Calling Claude API with model: {self.model}")
      
      config = get_config()
      max_tokens = config.get('claude.max_tokens', 4000)
      temperature = config.get('claude.temperature', 0.1)
      
      response = self.client.messages.create(
        model=self.model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=self.timeout,
        messages=[
          {
            "role": "user",
            "content": prompt
          }
        ]
      )
      
      logger.info("Claude API response received successfully")
      
      # In debug mode, we can also log the response length
      logger.debug(f"Received response of {len(response.content[0].text)} characters from Claude API")
      
      return response.content[0].text
    except Exception as e:
      logger.error(f"Error calling Claude API: {e}")
      raise RuntimeError(f"Failed to get response from Claude API: {e}")
  
  def _generate_prompt(self, system_info: Dict, language: str) -> str:
    """Generate a detailed prompt for Claude to analyze system health.
    
    Creates a prompt instructing Claude to act as a system administrator,
    analyze the provided system information, and generate a comprehensive
    health report in the specified language. The prompt defines the expected
    report structure and criteria for identifying issues.
    
    Args:
        system_info (Dict): The collected system information dictionary
        language (str): The language code for the output report
    
    Returns:
        str: The formatted prompt to send to Claude API
    
    Report sections defined in the prompt:
        1. System Overview
        2. Hardware Configuration
        3. Storage Status
        4. Memory Usage
        5. CPU Performance
        6. Network Configuration
        7. System Health
        8. Critical Issues
        9. Warnings
        10. Recommendations
    """
    config = get_config()
    sections = config.get('report.sections', [
        "system_overview", "hardware_config", "storage_status", "memory_usage",
        "cpu_performance", "network_config", "system_health", "critical_issues",
        "warnings", "recommendations"
    ])
    
    thresholds = config.get_section('report.thresholds')
    disk_warning = thresholds.get('disk_usage_warning', 80)
    disk_critical = thresholds.get('disk_usage_critical', 90)
    memory_warning = thresholds.get('memory_usage_warning', 85)
    memory_critical = thresholds.get('memory_usage_critical', 95)
    cpu_warning = thresholds.get('cpu_load_warning', 2.0)
    cpu_critical = thresholds.get('cpu_load_critical', 4.0)
    
    prompt = f"""
You are a skilled system administrator tasked with analyzing a Linux system's health.
Analyze the following system information and create a comprehensive health report.

The report should be in markdown format with these sections:
1. System Overview - Brief overview of the system (hostname, OS version, uptime)
2. Hardware Configuration - Details about CPU, memory, and other hardware components
3. Storage Status - Disk usage, mount points, block devices, and potential issues
4. Memory Usage - RAM and swap usage, memory allocation, and potential issues
5. CPU Performance - CPU load, utilization, top processes, and potential bottlenecks
6. Network Configuration - Network interfaces, listening ports, and potential issues
7. System Health - Failed services, system errors, auth failures, available updates
8. Critical Issues - Highlight any critical issues that need immediate attention
9. Warnings - Highlight potential problems that aren't yet critical
10. Recommendations - Specific suggestions for improving system health and performance

Be direct and critical in your assessment. Focus on potential problems and their solutions.

Look for these critical issues (include in Critical Issues section):
- Very high disk usage (>{disk_critical}% is critical)
- Critical memory shortage (<{100-memory_critical}% available)
- High swap usage (>80% used)
- Failed system services
- Root or privileged access attempts
- Signs of system compromise
- Disk health problems (SMART errors)
- Kernel-level errors
- Authentication security issues

Look for these warning signs (include in Warnings section):
- High disk usage (>{disk_warning}% is concerning)
- Low memory availability (<{100-memory_warning}% available)
- Moderate swap usage
- High CPU load sustained over time (>{cpu_warning} load average)
- Unusual network connections or listening ports
- Multiple authentication failures
- Outdated packages with security implications
- Unusual cron jobs or scheduled tasks

Recommendations should be specific to the system's issues, not generic advice.
For example, if a specific partition is running out of space, recommend actions for that partition.

Output language: {language}

System Information:
-------------------
{json.dumps(system_info, indent=2)}
"""
    return prompt
  
# Removed simulate_response method - now using real API calls only

#fin