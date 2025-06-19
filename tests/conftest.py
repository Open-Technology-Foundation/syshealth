#!/usr/bin/env python3

"""Shared test fixtures and utilities for SysHealth test suite."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from typing import Dict, Any

# Test fixtures for common mock objects and test data

@pytest.fixture
def mock_command_responses():
    """Standard mock command responses for testing."""
    return {
        # Basic system commands
        "uname -a": "Linux testhost 5.4.0-test #1 SMP x86_64 GNU/Linux",
        "uptime": "up 10 minutes, 1 user, load average: 0.1, 0.2, 0.3",
        "lsb_release -a 2>/dev/null || cat /etc/*release 2>/dev/null": "Ubuntu 24.04 LTS",
        
        # Hardware commands  
        "lshw -short 2>/dev/null": "H/W path     Device     Class      Description\n/0           system     Computer",
        "lscpu | grep 'Model name' 2>/dev/null || grep -i cpu /proc/cpuinfo | grep -i model | head -1": "Model name: Intel Core i7-9700K",
        "lscpu 2>/dev/null || cat /proc/cpuinfo": "Architecture: x86_64\nCPU(s): 8",
        "free -h": "              total        used        free      shared  buff/cache   available\nMem:           16Gi       8.0Gi       2.0Gi",
        "grep -i swap /proc/swaps 2>/dev/null || echo 'Swap information not available'": "Filename Type Size Used Priority",
        
        # Storage commands
        "df -h": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   50G   50G  50% /",
        "lsblk 2>/dev/null || echo 'lsblk not available'": "NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT\nsda      8:0    0  100G  0 disk",
        "smartctl -H /dev/nvme0n1 2>/dev/null || echo 'Disk health information not available (requires root)'": "SMART overall-health self-assessment test result: PASSED",
        "cat /etc/fstab |grep -v '^$' |grep -v '^#' 2>/dev/null || echo 'fstab not available'": "/dev/sda1 / ext4 defaults 0 1",
        
        # Process commands
        "ps aux --sort=-%cpu | head -n 10": "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.1  0.1 168548 11984 ?        Ss   10:00   0:01 systemd",
        "ps aux --sort=-%mem | head -n 10": "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.1  0.1 168548 11984 ?        Ss   10:00   0:01 systemd",
        
        # Network commands
        "ip -br address 2>/dev/null || ifconfig -a 2>/dev/null || echo 'Network information not available'": "lo               UNKNOWN        127.0.0.1/8 ::1/128\neth0             UP             192.168.1.100/24",
        "ss -tuln 2>/dev/null || netstat -tuln 2>/dev/null || echo 'Port information not available'": "State      Recv-Q Send-Q Local Address:Port  Peer Address:Port\nLISTEN     0      128    0.0.0.0:22           0.0.0.0:*",
        
        # Security commands
        "systemctl list-units --state=failed 2>/dev/null || echo 'Failed services information not available'": "  UNIT LOAD ACTIVE SUB DESCRIPTION\n0 loaded units listed.",
        "journalctl -p err -n 20 2>/dev/null || echo 'Error logs not available'": "-- No entries --",
        "grep -i fail /var/log/auth.log 2>/dev/null | tail -20 || echo 'Authentication logs not available'": "Authentication logs not available",
        "apt list --upgradable 2>/dev/null | head -20 || echo 'Update information not available'": "Listing... Done",
        "cat /var/log/chkrootkit/log.today 2>/dev/null || echo 'Rootkit check logs not available'": "Rootkit check logs not available",
        "crontab -l |grep -v '^$' |grep -v '^#' 2>/dev/null || echo 'Crontab information not available'": "Crontab information not available",
    }

@pytest.fixture  
def mock_command_executor(mock_command_responses):
    """Mock command executor with predefined responses."""
    from tests.test_collectors import MockCommandExecutor
    return MockCommandExecutor(mock_command_responses)

@pytest.fixture
def test_system_info():
    """Sample system information dictionary for testing."""
    return {
        "hostname": "testhost",
        "timestamp": "2025-01-01T12:00:00",
        "uname": "Linux testhost 5.4.0-test",
        "memory": "Total: 16GB, Used: 8GB",
        "disk_usage": "/ 50% full",
        "network_interfaces": "eth0: 192.168.1.100"
    }

@pytest.fixture
def temp_directory():
    """Temporary directory for test file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client for testing."""
    with patch('anthropic.Anthropic') as mock_client:
        # Mock the messages.create method
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "# Test Health Report\n\nThis is a test report."
        
        mock_client.return_value.messages.create.return_value = mock_response
        yield mock_client

@pytest.fixture
def mock_environment_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'ANTHROPIC_API_KEY': 'test-api-key-12345',
        'HOME': '/tmp/test-home'
    }):
        yield

@pytest.fixture
def sample_report_content():
    """Sample report content for testing file operations."""
    return """# System Health Report

## System Overview
- **Hostname:** testhost
- **OS:** Ubuntu 24.04 LTS
- **Uptime:** 10 minutes

## Critical Issues
None detected.

## Recommendations
System appears healthy.
"""

# Helper functions for tests

def create_mock_subprocess_result(returncode=0, stdout="", stderr=""):
    """Create a mock subprocess result."""
    result = Mock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result

def assert_collector_keys(result, expected_keys):
    """Assert that collector result contains expected keys."""
    for key in expected_keys:
        assert key in result, f"Expected key '{key}' not found in collector result"

#fin