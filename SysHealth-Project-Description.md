# Project SysHealth 

- initial instructions to Claude Code

## System Health Report

Create a system called `syshealth` that examines a specified Ubuntu Linux machine (via `ssh`), or by default, the current machine, for its current hardware configuration and system status.
Information is first collated using standard programs (eg, `lshw`, `top`, `df`, `lsblk`, and any others you deem useful).

This informataion is then sent to an LLM for analysis (default claude-3.7-sonnet), and a comprehensive system status/health report generated.  This program should probably be run as the root user.

## Possible External Dependencies

    python3 pip3 top pandoc lshw uname ssh git curl wget unzip

## _Examples_ of External Program Use

These are just some *examples* of possible commands to use to analyse systems.

    apt list --upgradable 2>/dev/null | head -20
    cat -s /etc/fstab
    cat /var/log/chkrootkit/log.today
    df --all --output --total
    df -h
    free -h
    grep -i cpu /proc/cpuinfo | grep -i model | head -1
    grep -i fail /var/log/auth.log | tail -20
    grep -i swap /var/log/syslog | tail -5
    journalctl -p err -n 30
    lsblk
    lsb_release -a
    lscpu | grep "Model name"
    lshw -short -quiet
    ps aux --sort=-%mem | head -10
    sudo crontab -l
    sudo smartctl -H /dev/nvme0n1
    sudo ss -tuln
    systemctl list-units --state=failed
    systemctl status --failed
    top -b -n 1 -o %CPU |grep -v " top" | head -n20
    uname --all
    uptime


NOTE:
  * These are *only suggestions* from an inexperienced system administrator. 
  * Use *any* publically available external programs that you deem fit to obtain the best possible results.

## Reports

`syshealth` should generate a consistent. structured report.

The language of the report should be specified on the command line (default en).

The report should be in markdown format, and possibly displayed using `nano -Saxv "$report.md"`. But I shall leave this up to you.

The report should give a good overview of the current hardware and software installed.

It should point out any potential problems. Some contraints may need to be defined on the command line or config file as to what constitutes a problem, eg, minimum diskspace %)

Overall, what is condition of the machine being examined?

Be critical and direct.

## Possible Example Usage:

```bash
# Most simple, for getting diagnoses of the current host with default settings:
syshealth -v 

# For better results, monitor the activity of another remote host (requires 
# ssh key access), thus not interferring with the cpu usage or load on the machine:
syshealth -v server2

# More complex, with primary language Indonesian, and reporting on multiple hosts:
syshealth -v -L indonesian $HOSTNAME server0 server1

```


