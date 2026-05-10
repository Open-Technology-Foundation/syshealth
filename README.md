# SysHealth - AI-Powered System Health Monitor

SysHealth is a single-file Bash tool that collects comprehensive Linux system information and uses Claude AI to generate detailed health reports with diagnostics and recommendations.

## Features

- **Single-file tool** -- no frameworks, no package managers, just Bash
- **Comprehensive collection** -- hardware, storage, memory, CPU, network, and security data
- **AI-powered analysis** -- Claude AI identifies issues and provides actionable recommendations
- **Multi-host support** -- analyze local and remote systems in a single run
- **Multi-language reports** -- generate reports in any language
- **Email delivery** -- optional email reports with HTML formatting (via pandoc) or plain text
- **Environment variable configuration** -- no config files to manage
- **Debug mode** -- save prompts and enable verbose diagnostics
- **Security hardened** -- PATH lockdown, API key protection via process substitution, input sanitization

## Requirements

- **Bash** 5.2+
- **curl** -- API communication
- **jq** -- JSON construction and parsing
- **Anthropic API key** -- for Claude AI analysis
- **ssh** -- for remote host analysis (key-based authentication)

### Recommended Tools

These are optional but provide richer system data:

| Tool | Purpose | Install |
|------|---------|---------|
| `lshw` | Hardware listing | `sudo apt install lshw` |
| `lscpu` | CPU details | (usually pre-installed) |
| `df` | Disk usage | (usually pre-installed) |
| `free` | Memory usage | (usually pre-installed) |
| `ss` | Network sockets | (usually pre-installed) |
| `lsblk` | Block devices | (usually pre-installed) |
| `smartctl` | Disk SMART health | `sudo apt install smartmontools` |
| `pandoc` | HTML email conversion | `sudo apt install pandoc` |
| `chkrootkit` | Rootkit scanning | `sudo apt install chkrootkit` |
| `sensors` | Temperature monitoring | `sudo apt install lm-sensors` |

## Installation

Copy the script and make it executable:

```bash
cp syshealth /usr/local/bin/syshealth
chmod +x /usr/local/bin/syshealth
```

Or symlink from the repository:

```bash
ln -s /path/to/syshealth /usr/local/bin/syshealth
```

No virtual environments, no pip, no dependencies beyond `curl` and `jq`.

## Configuration

### API Key

SysHealth looks for the Anthropic API key in this order:

1. `ANTHROPIC_API_KEY` environment variable
2. `/etc/anthropic/api_key` (system-wide)
3. `~/.config/anthropic/api_key` (per-user, takes precedence)

Set via environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a key file:

```bash
mkdir -p ~/.config/anthropic
echo "sk-ant-..." > ~/.config/anthropic/api_key
chmod 600 ~/.config/anthropic/api_key
```

### Environment Variables

All settings are configured via environment variables. No config files needed.

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key (required) | -- |
| `SYSHEALTH_MODEL` | Claude model | `claude-sonnet-4-5` |
| `SYSHEALTH_MAX_TOKENS` | Max response tokens | `32000` |
| `SYSHEALTH_TEMPERATURE` | Response temperature | `0.1` |
| `SYSHEALTH_TIMEOUT` | API timeout in seconds | `420` |
| `SYSHEALTH_OUTPUT_DIR` | Report output directory | `~/syshealth` |
| `SYSHEALTH_LANGUAGE` | Default report language | `en` |

## Usage

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-v, --verbose` | Print report to terminal | off |
| `-d, --debug` | Save prompts, implies `-v` | off |
| `-q, --quiet` | Suppress info messages | off |
| `-L, --language LANG` | Report language | `en` |
| `-m, --model MODEL` | Claude model | `claude-sonnet-4-5` |
| `-o, --output-dir DIR` | Output directory | `~/syshealth` |
| `--mail EMAILS` | Comma-separated email recipients | -- |
| `-V, --version` | Show version | -- |
| `-h, --help` | Show help | -- |

### Examples

```bash
# Analyze local system
syshealth -v

# Remote host, Spanish report
syshealth -v -L spanish server1

# Multiple hosts with a specific model
syshealth -v -m claude-sonnet-4-5 host1 host2

# Debug mode with email delivery
syshealth -d -v --mail admin@example.com server1

# Quiet mode to custom directory
syshealth -q -o /var/reports server1 server2
```

## Report Structure

Each generated report contains 10 sections:

1. **System Overview** -- hostname, OS version, uptime
2. **Hardware Configuration** -- CPU, memory, hardware components
3. **Storage Status** -- disk usage, mount points, block devices, SMART health
4. **Memory Usage** -- RAM and swap utilization
5. **CPU Performance** -- load averages, top processes, bottlenecks
6. **Network Configuration** -- interfaces, listening ports
7. **System Health** -- failed services, errors, auth failures, updates
8. **Critical Issues** -- problems requiring immediate attention
9. **Warnings** -- potential issues not yet critical
10. **Recommendations** -- specific improvement suggestions

Reports are saved as markdown: `hostname-language-timestamp.md`

### Thresholds

The AI analysis uses these built-in thresholds:

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk usage | >80% | >90% |
| Memory usage | >85% | >95% |
| CPU load average | >2.0 | -- |

## How It Works

```
CLI arguments → parse options and hosts
                    │
                    ▼
            check_dependencies()
            (curl, jq, API key)
                    │
          ┌─────────┴─────────┐
          │   For each host:  │
          │                   │
          │  collect_basic()  │  OS, hostname, uptime, virtualization
          │  collect_hardware()  CPU, memory, temperature
          │  collect_storage()   disks, RAID, LVM, SMART
          │  collect_process()   top CPU/memory processes
          │  collect_network()   interfaces, ports
          │  collect_security()  services, logs, firewall, updates
          │         │         │
          │         ▼         │
          │  Assemble JSON    │
          │         │         │
          │         ▼         │
          │  call_claude_api()│  curl → Anthropic Messages API
          │         │         │
          │         ▼         │
          │  save_report()    │  ~/syshealth/host-lang-timestamp.md
          │  send_email()     │  (if --mail specified)
          └───────────────────┘
```

For remote hosts, all collection commands run via `ssh`. For the local host, commands execute directly.

## Troubleshooting

**API key not found:**
```bash
# Check if set
echo "$ANTHROPIC_API_KEY"

# Or check key file
cat ~/.config/anthropic/api_key
```

**SSH connection failures:**
- Verify key-based authentication: `ssh hostname whoami`
- Ensure the remote user has permission to run system commands

**Missing tools warning:**
```bash
# Install recommended tools
sudo apt install lshw smartmontools lm-sensors
```

**API timeout errors:**
- Increase timeout: `export SYSHEALTH_TIMEOUT=600`
- Use a faster model: `syshealth -m claude-haiku-4-5 -v`

**Debug mode for diagnostics:**
```bash
syshealth -d -v hostname
# Prompts saved to ~/syshealth/debug/
```

## License

GPLv3 -- see LICENSE file for details.

#fin
