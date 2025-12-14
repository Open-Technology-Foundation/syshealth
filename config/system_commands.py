#!/usr/bin/env python3

"""System command configuration management.

This module defines all system commands used for health monitoring. All commands
are validated against a whitelist before execution and are categorized by their
security requirements.

Security Architecture:
    - Simple commands: Executed with shell=False for maximum security
    - Shell commands: Require shell features, validated with allow_shell_features=True
    - All commands use only whitelisted base commands (uname, lshw, ps, grep, etc.)
    - Commands use defensive patterns (error suppression, fallbacks, timeouts)

Command Categories:
    1. SIMPLE COMMANDS (shell=False):
       - No pipes, redirects, or wildcards
       - Executed directly via subprocess with argument arrays
       - Examples: uname -a, uptime, free -h, df -h

    2. SHELL COMMANDS requiring pipes (|):
       - Used for filtering output (grep, head, tail)
       - Required for process sorting and limiting
       - Examples: ps | head, cat | grep

    3. SHELL COMMANDS requiring fallbacks (||):
       - Handle different distributions/configurations
       - Provide graceful degradation when tools missing
       - Examples: lshw || echo 'unavailable'

    4. SHELL COMMANDS requiring redirects (2>/dev/null):
       - Suppress expected error messages
       - Keep output clean and focused
       - Combined with fallback chains

    5. SHELL COMMANDS requiring timeouts:
       - Prevent commands from hanging
       - Essential for network and journalctl operations
       - Examples: timeout 30s smartctl

Security Notes:
    - All base commands (first word) must be in CommandValidator whitelist
    - Shell metacharacters only allowed in validated shell commands
    - No user input is incorporated into these commands
    - Commands are static, defined at module load time
    - Fallback messages use echo (safe, no command injection risk)
"""

from dataclasses import dataclass


@dataclass
class SystemInfoConfig:
    """Configuration class for system information collection commands.

    This class centralizes all command definitions used for system information
    collection. Commands are designed with security in mind:
    - Only use whitelisted system monitoring tools
    - Minimize shell feature usage where possible
    - Use defensive patterns (timeouts, error suppression, fallbacks)
    - Provide graceful degradation when tools are unavailable

    All commands defined here are trusted and static - no user input is ever
    incorporated into these command strings.

    Attributes:
        Each attribute is a command string that will be validated before execution.
        Commands are categorized by the information they collect.
    """

    # =========================================================================
    # BASIC SYSTEM INFORMATION COMMANDS
    # =========================================================================

    # SIMPLE: No shell features required
    uname_command: str = "uname -a"

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # Tries lsb_release first, falls back to reading /etc/*release files
    # Wildcard in /etc/*release is necessary for distribution compatibility
    os_release_command: str = (
        "lsb_release -a 2>/dev/null || cat /etc/*release 2>/dev/null"
    )

    # SIMPLE: No shell features required
    uptime_command: str = "uptime"

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # Tries systemd timedatectl first, then chrony, then ntpd, finally fallback
    # Time synchronization is critical for logs, authentication, distributed systems
    time_sync_command: str = (
        "timedatectl status 2>/dev/null || "
        "chronyc tracking 2>/dev/null || "
        "ntpq -p 2>/dev/null || "
        "echo 'Time synchronization information not available'"
    )

    # =========================================================================
    # HARDWARE INFORMATION COMMANDS
    # =========================================================================

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # lshw may not be installed, provide helpful fallback message
    hardware_list_command: str = (
        "lshw -short 2>/dev/null || echo 'Hardware listing unavailable (install: sudo apt install lshw)'"
    )

    # SHELL: Requires pipes (|) and fallback (||)
    # Filters lscpu output or falls back to /proc/cpuinfo with multiple filters
    # Multiple greps and head needed for reliable CPU model extraction
    cpu_model_command: str = (
        "lscpu | grep 'Model name' 2>/dev/null || grep -i cpu /proc/cpuinfo | grep -i model | head -1"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # Tries lscpu, falls back to /proc/cpuinfo, finally to error message
    cpu_info_command: str = (
        "lscpu 2>/dev/null || cat /proc/cpuinfo || echo 'CPU information unavailable (install: sudo apt install util-linux)'"
    )

    # SHELL: Requires wildcard (*), fallback (||), and redirect (2>/dev/null)
    # Tries lm-sensors first, falls back to thermal zones, finally to error message
    # Thermal monitoring is critical for detecting overheating and throttling
    temperature_command: str = (
        "sensors 2>/dev/null || "
        "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null || "
        "echo 'Temperature information not available (install: sudo apt install lm-sensors)'"
    )

    # =========================================================================
    # MEMORY INFORMATION COMMANDS
    # =========================================================================

    # SIMPLE: No shell features required
    memory_command: str = "free -h"

    # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
    # Filters swap info from /proc/swaps with fallback message
    swap_info_command: str = (
        "grep -i swap /proc/swaps 2>/dev/null || echo 'Swap information not available'"
    )

    # =========================================================================
    # STORAGE INFORMATION COMMANDS
    # =========================================================================

    # SIMPLE: No shell features required
    disk_usage_command: str = "df -h"

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # lsblk may not be available on all systems
    block_devices_command: str = (
        "lsblk --noheadings --output NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null || echo 'Block device information not available (install util-linux)'"
    )

    # NOTE: disk_health_command removed - StorageInfoCollector now performs
    # dynamic disk detection using lsblk and checks SMART on each physical disk.
    # This eliminates the hardcoded /dev/nvme0n1 path and supports multiple disks.

    # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
    # Filters out comments and empty lines from fstab
    # grep -vE requires shell for pattern matching
    fstab_command: str = (
        "cat /etc/fstab | grep -vE '^(#|$)' 2>/dev/null || echo 'fstab not available'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # Software RAID status from /proc/mdstat
    raid_status_command: str = (
        "cat /proc/mdstat 2>/dev/null || echo 'No software RAID configured'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # Detailed RAID configuration using mdadm
    # Requires mdadm package and may need root permissions
    raid_detail_command: str = (
        "mdadm --detail --scan 2>/dev/null || echo 'mdadm not available or no RAID configured'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # LVM logical volume status
    lvm_volumes_command: str = (
        "lvs --noheadings 2>/dev/null || echo 'LVM not configured or lvs not available'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # LVM volume group status
    lvm_groups_command: str = (
        "vgs --noheadings 2>/dev/null || echo 'LVM not configured or vgs not available'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # LVM physical volume status
    lvm_physical_command: str = (
        "pvs --noheadings 2>/dev/null || echo 'LVM not configured or pvs not available'"
    )

    # =========================================================================
    # PROCESS INFORMATION COMMANDS
    # =========================================================================

    # SHELL: Requires pipe (|) for output limiting
    # ps --sort requires sorting in ps itself, but head limits output
    # Cannot avoid pipe without reading full process list
    top_cpu_processes_command: str = (
        "ps --no-headers -eo pid,pcpu,pmem,comm --sort=-%cpu | head -n 10"
    )

    # SHELL: Requires pipe (|) for output limiting
    # Same rationale as top_cpu_processes_command
    top_mem_processes_command: str = (
        "ps --no-headers -eo pid,pcpu,pmem,comm --sort=-%mem | head -n 10"
    )

    # =========================================================================
    # NETWORK INFORMATION COMMANDS
    # =========================================================================

    # SHELL: Requires multiple fallbacks (||) and redirects (2>/dev/null)
    # Tries modern ip command (brief and full), falls back to legacy ifconfig,
    # then to /proc/net/dev, finally error message
    # Multiple fallbacks essential for cross-distribution compatibility
    network_interfaces_command: str = (
        "ip -br addr show 2>/dev/null || ip addr show 2>/dev/null || ifconfig 2>/dev/null || cat /proc/net/dev 2>/dev/null || echo 'Network information not available'"
    )

    # SHELL: Requires timeout, fallbacks (||), and redirect (2>/dev/null)
    # Network commands can hang, timeout essential
    # ss is modern, netstat is legacy fallback
    listening_ports_command: str = (
        "timeout 15s ss -tuln 2>/dev/null || timeout 15s netstat -tuln 2>/dev/null || echo 'Port information not available (install: sudo apt install iproute2 or net-tools)'"
    )

    # =========================================================================
    # SYSTEM HEALTH COMMANDS
    # =========================================================================

    # SHELL: Requires timeout, fallback (||), and redirect (2>/dev/null)
    # systemctl can hang on some systems, timeout essential
    failed_services_command: str = (
        "timeout 15s systemctl list-units --state=failed 2>/dev/null || echo 'Failed services information not available'"
    )

    # SHELL: Requires timeout, fallback (||), and redirect (2>/dev/null)
    # journalctl can be very slow on systems with large logs, timeout essential
    recent_errors_command: str = (
        "timeout 30s journalctl -p err --lines=20 --no-pager -q 2>/dev/null || echo 'Error logs not available'"
    )

    # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
    # Filters auth.log for failures, limits output with tail
    auth_failures_command: str = (
        "grep -i fail /var/log/auth.log 2>/dev/null | tail -20 || echo 'Authentication logs not available'"
    )

    # =========================================================================
    # SECURITY AND MAINTENANCE COMMANDS
    # =========================================================================

    # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
    # Limits update list to 20 items, varies by distribution
    available_updates_command: str = (
        "apt list --upgradable 2>/dev/null | head -20 || echo 'Update information not available'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # chkrootkit may not be installed or run
    rootkit_check_command: str = (
        "cat /var/log/chkrootkit/log.today 2>/dev/null || echo 'Rootkit check logs not available (install: sudo apt install chkrootkit)'"
    )

    # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
    # Filters out comments and empty lines from crontab
    cron_jobs_command: str = (
        "crontab -l | grep -vE '^(#|$)' 2>/dev/null || echo 'Crontab information not available'"
    )

    # SHELL: Requires fallback (||) and redirect (2>/dev/null)
    # Tries Ubuntu's ufw first, falls back to generic iptables
    # Firewall status is critical for security posture assessment
    # May require root permissions for full output
    firewall_command: str = (
        "ufw status verbose 2>/dev/null || "
        "iptables -L -n -v 2>/dev/null || "
        "echo 'Firewall information not available (requires root)'"
    )

    # =========================================================================
    # VIRTUALIZATION AND CONTAINER DETECTION COMMANDS
    # =========================================================================

    # SHELL: Requires pipes (|), fallbacks (||), and redirects (2>/dev/null)
    # Tries systemd-detect-virt first, falls back to dmesg grep with head limit
    virtualization_command: str = (
        "systemd-detect-virt 2>/dev/null || dmesg | grep -i hypervisor | head -5 2>/dev/null || echo 'Virtualization info not available (install: sudo apt install systemd)'"
    )

    # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
    # Checks cgroup info (indicates container), limits output
    container_info_command: str = (
        "cat /proc/1/cgroup 2>/dev/null | head -5 || echo 'Container information not available'"
    )

    @classmethod
    def for_distribution(cls, distro: str | None = None) -> "SystemInfoConfig":
        """Create a configuration instance optimized for a specific Linux distribution.

        This method creates distribution-specific command configurations while maintaining
        the same security properties as the default commands.

        Args:
            distro (str | None): The distribution name (e.g., 'ubuntu', 'centos', 'debian')

        Returns:
            SystemInfoConfig: Configuration instance with distribution-specific optimizations

        Security Notes:
            - All distribution-specific overrides maintain same security level as defaults
            - Use same defensive patterns (fallbacks, error suppression, timeouts)
            - All base commands remain whitelisted
        """
        config = cls()

        # Use pattern matching for distribution-specific configuration
        match distro.lower() if distro else None:
            case "centos" | "rhel" | "fedora":
                # Red Hat-based distributions use different package management
                # SHELL: Requires pipes (|), fallbacks (||), and redirects (2>/dev/null)
                # Tries yum first, falls back to dnf (newer RHEL/Fedora)
                config.available_updates_command = (
                    "yum check-update 2>/dev/null | head -20 || "
                    "dnf check-update 2>/dev/null | head -20 || "
                    "echo 'Update information not available'"
                )

                # SHELL: Requires fallback (||) and redirect (2>/dev/null)
                # Red Hat uses /etc/redhat-release instead of lsb_release
                config.os_release_command = (
                    "cat /etc/redhat-release 2>/dev/null || cat /etc/*release 2>/dev/null"
                )

            case "arch" | "manjaro":
                # Arch-based distributions use pacman
                # SHELL: Requires pipe (|), fallback (||), and redirect (2>/dev/null)
                # pacman -Qu lists available updates
                config.available_updates_command = (
                    "pacman -Qu 2>/dev/null | head -20 || "
                    "echo 'Update information not available'"
                )

            case _:
                # Default configuration (Debian/Ubuntu or unknown distribution)
                # No changes needed - use default commands from class definition
                pass

        return config

    def get_simple_commands(self) -> list[str]:
        """Get list of commands that don't require shell features.

        These commands can be executed with shell=False for maximum security.

        Returns:
            List of command attribute names that are simple commands
        """
        return [
            "uname_command",
            "uptime_command",
            "memory_command",
            "disk_usage_command",
        ]

    def get_shell_commands(self) -> list[str]:
        """Get list of commands that require shell features.

        These commands must be executed with shell=True (via SecureShellExecutor)
        because they use pipes, redirects, wildcards, or other shell features.

        Returns:
            List of command attribute names that require shell features
        """
        return [
            "os_release_command",
            "time_sync_command",
            "hardware_list_command",
            "cpu_model_command",
            "cpu_info_command",
            "temperature_command",
            "swap_info_command",
            "block_devices_command",
            "fstab_command",
            "raid_status_command",
            "raid_detail_command",
            "lvm_volumes_command",
            "lvm_groups_command",
            "lvm_physical_command",
            "top_cpu_processes_command",
            "top_mem_processes_command",
            "network_interfaces_command",
            "listening_ports_command",
            "failed_services_command",
            "recent_errors_command",
            "auth_failures_command",
            "available_updates_command",
            "rootkit_check_command",
            "cron_jobs_command",
            "firewall_command",
            "virtualization_command",
            "container_info_command",
        ]


# =============================================================================
# SECURITY SUMMARY
# =============================================================================

"""
Command Security Analysis (24 total commands):

SIMPLE COMMANDS (4 commands - shell=False):
    ✓ uname_command - No shell features
    ✓ uptime_command - No shell features
    ✓ memory_command - No shell features
    ✓ disk_usage_command - No shell features

SHELL COMMANDS (20 commands - shell=True via SecureShellExecutor):
    All validated against whitelist before execution

    Fallback chains (||) for graceful degradation:
        ✓ os_release_command - Distribution detection
        ✓ hardware_list_command - Hardware listing
        ✓ cpu_model_command - CPU identification
        ✓ cpu_info_command - CPU details
        ✓ swap_info_command - Swap information
        ✓ block_devices_command - Block devices
        ✓ disk_health_command - SMART status
        ✓ fstab_command - Filesystem table
        ✓ network_interfaces_command - Network config
        ✓ listening_ports_command - Open ports
        ✓ failed_services_command - Failed systemd units
        ✓ recent_errors_command - System errors
        ✓ auth_failures_command - Authentication failures
        ✓ available_updates_command - Pending updates
        ✓ rootkit_check_command - Rootkit scan results
        ✓ cron_jobs_command - Scheduled tasks
        ✓ virtualization_command - VM detection
        ✓ container_info_command - Container detection

    Pipes (|) for filtering/limiting:
        ✓ cpu_model_command - grep filtering
        ✓ fstab_command - grep filtering
        ✓ top_cpu_processes_command - head limiting
        ✓ top_mem_processes_command - head limiting
        ✓ auth_failures_command - tail limiting
        ✓ available_updates_command - head limiting
        ✓ cron_jobs_command - grep filtering
        ✓ virtualization_command - grep + head
        ✓ container_info_command - head limiting

    Timeouts for hang prevention:
        ✓ disk_health_command - 30s timeout
        ✓ listening_ports_command - 15s timeout
        ✓ failed_services_command - 15s timeout
        ✓ recent_errors_command - 30s timeout

Security Guarantees:
    1. All base commands in CommandValidator whitelist
    2. No user input incorporated into commands
    3. Commands are static (defined at module load)
    4. Shell commands validated with allow_shell_features=True
    5. Simple commands executed with shell=False (more secure)
    6. Defensive patterns prevent common issues
    7. Fallbacks ensure graceful degradation
    8. Timeouts prevent resource exhaustion
    9. Error suppression (2>/dev/null) keeps output clean
   10. All commands are read-only monitoring tools

Distribution Support:
    - Ubuntu/Debian: apt, lsb_release
    - RHEL/CentOS/Fedora: yum, dnf, /etc/redhat-release
    - Arch/Manjaro: pacman
    - Universal fallbacks: /proc, /etc/*release, basic tools
"""


# fin
