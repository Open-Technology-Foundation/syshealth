#!/usr/bin/env python3

"""System command configuration management."""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class SystemInfoConfig:
  """Configuration class for system information collection commands.
  
  This class centralizes all command definitions used for system information
  collection, allowing for easy customization and distribution-specific overrides.
  """
  
  # Basic system information commands
  uname_command: str = "uname -a"
  os_release_command: str = "lsb_release -a 2>/dev/null || cat /etc/*release 2>/dev/null"
  uptime_command: str = "uptime"
  
  # Hardware information commands
  hardware_list_command: str = "lshw -short 2>/dev/null || echo 'Hardware listing unavailable (install: sudo apt install lshw)'"
  cpu_model_command: str = "lscpu | grep 'Model name' 2>/dev/null || grep -i cpu /proc/cpuinfo | grep -i model | head -1"
  cpu_info_command: str = "lscpu 2>/dev/null || cat /proc/cpuinfo || echo 'CPU information unavailable (install: sudo apt install util-linux)'"
  
  # Memory information commands
  memory_command: str = "free -h"
  swap_info_command: str = "grep -i swap /proc/swaps 2>/dev/null || echo 'Swap information not available'"
  
  # Storage information commands
  disk_usage_command: str = "df -h"
  block_devices_command: str = "lsblk --noheadings --output NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null || echo 'Block device information not available (install util-linux)'"
  disk_health_command: str = "timeout 30s smartctl -H /dev/nvme0n1 2>/dev/null || echo 'Disk health information not available (requires root)'"
  fstab_command: str = "cat /etc/fstab | grep -vE '^(#|$)' 2>/dev/null || echo 'fstab not available'"
  
  # Process information commands
  top_cpu_processes_command: str = "ps --no-headers -eo pid,pcpu,pmem,comm --sort=-%cpu | head -n 10"
  top_mem_processes_command: str = "ps --no-headers -eo pid,pcpu,pmem,comm --sort=-%mem | head -n 10"
  
  # Network information commands
  network_interfaces_command: str = "ip -br addr show 2>/dev/null || ip addr show 2>/dev/null || ifconfig 2>/dev/null || cat /proc/net/dev 2>/dev/null || echo 'Network information not available'"
  listening_ports_command: str = "timeout 15s ss -tuln 2>/dev/null || timeout 15s netstat -tuln 2>/dev/null || echo 'Port information not available (install: sudo apt install iproute2 or net-tools)'"
  
  # System health commands
  failed_services_command: str = "timeout 15s systemctl list-units --state=failed 2>/dev/null || echo 'Failed services information not available'"
  recent_errors_command: str = "timeout 30s journalctl -p err --lines=20 --no-pager -q 2>/dev/null || echo 'Error logs not available'"
  auth_failures_command: str = "grep -i fail /var/log/auth.log 2>/dev/null | tail -20 || echo 'Authentication logs not available'"
  
  # Security and maintenance commands
  available_updates_command: str = "apt list --upgradable 2>/dev/null | head -20 || echo 'Update information not available'"
  rootkit_check_command: str = "cat /var/log/chkrootkit/log.today 2>/dev/null || echo 'Rootkit check logs not available (install: sudo apt install chkrootkit)'"
  cron_jobs_command: str = "crontab -l | grep -vE '^(#|$)' 2>/dev/null || echo 'Crontab information not available'"
  
  # Virtualization and container detection commands  
  virtualization_command: str = "systemd-detect-virt 2>/dev/null || dmesg | grep -i hypervisor | head -5 2>/dev/null || echo 'Virtualization info not available (install: sudo apt install systemd)'"
  container_info_command: str = "cat /proc/1/cgroup 2>/dev/null | head -5 || echo 'Container information not available'"
  
  @classmethod
  def for_distribution(cls, distro: Optional[str] = None) -> "SystemInfoConfig":
    """Create a configuration instance optimized for a specific Linux distribution.
    
    Args:
        distro (Optional[str]): The distribution name (e.g., 'ubuntu', 'centos', 'debian')
        
    Returns:
        SystemInfoConfig: Configuration instance with distribution-specific optimizations
    """
    config = cls()
    
    if distro and distro.lower() in ['centos', 'rhel', 'fedora']:
      # Red Hat-based distributions use different package management
      config.available_updates_command = "yum check-update 2>/dev/null | head -20 || dnf check-update 2>/dev/null | head -20 || echo 'Update information not available'"
      config.os_release_command = "cat /etc/redhat-release 2>/dev/null || cat /etc/*release 2>/dev/null"
    elif distro and distro.lower() in ['arch', 'manjaro']:
      # Arch-based distributions use pacman
      config.available_updates_command = "pacman -Qu 2>/dev/null | head -20 || echo 'Update information not available'"
    
    return config

#fin