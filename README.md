# SysHealth - System Health Report Generator

SysHealth is a powerful tool that examines Linux systems (local or remote) and generates comprehensive health reports using Claude AI. It analyzes hardware configurations, system performance, resource usage, and potential issues to provide actionable insights and recommendations.

## Features

- Analyze local or remote Linux machines
- Gather detailed hardware and system information
- Identify critical issues and warning signs
- Generate comprehensive health reports in markdown format
- Email reports to specified recipients
- Support for multiple languages
- Debug mode for troubleshooting

## Requirements

- **Operating System**: Ubuntu/Debian Linux (primary target, other distros may work)
- **Python**: Version 3.12+ recommended
- **API Key**: Anthropic API key for Claude AI
- **Dependencies**: Standard Linux system tools (details below)
- **SSH Access**: For analyzing remote hosts (key-based authentication)

## Installation

### Option 1: Automatic Installation (Recommended)

Use the provided installation script to install SysHealth system-wide:

```bash
# Clone the repository
git clone https://github.com/yourusername/syshealth.git
cd syshealth

# Run the installer script (requires sudo permissions)
./install.sh
```

The installer will:
1. Copy files to `/usr/local/syshealth`
2. Create a symlink in `/usr/local/bin`
3. Set up a Python virtual environment
4. Install required dependencies

### Option 2: Manual Installation

1. Clone this repository
2. Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Make sure the scripts are executable:

```bash
chmod +x syshealth.py syshealth
```

## API Key Setup

SysHealth requires a Claude API key from Anthropic to generate health reports. Set your API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

This is a required step - the tool will not run without a valid API key (except when displaying help information).

For persistent use, add this to your `~/.bashrc` or `~/.profile` file.

## Usage

### Basic Usage

```bash
# Analyze the local machine with verbose output
syshealth -v                     # If installed with install.sh
./syshealth -v                   # If running from the source directory

# Analyze a remote host (requires SSH key access)
syshealth -v remote-server

# Analyze multiple hosts with a specific language
syshealth -v -L spanish host1 host2 host3

# Specify an output directory
syshealth -v -o /path/to/reports host1
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output (displays report in terminal) |
| `-d, --debug` | Enable debug mode (logs prompts sent to Claude) |
| `-L, --language LANG` | Specify report language (default: en) |
| `-m, --model MODEL` | Specify Claude model to use (default: claude-3-7-sonnet-20250219) |
| `-o, --output-dir DIR` | Directory to save reports (default: ~/syshealth) |
| `--mail EMAILS` | Comma-separated list of email addresses to send reports to |
| `hosts` | Space-separated list of hosts to analyze (default: current host) |

### Email Reports

To send reports via email, use the `--mail` option:

```bash
syshealth -v --mail admin@example.com,alert@example.com server1
```

This requires a properly configured local SMTP server.

## Report Format

The health report is generated in markdown format and includes the following sections:

1. **System Overview** - Brief overview of the system (hostname, OS version, uptime)
2. **Hardware Configuration** - Details about CPU, memory, and other hardware components
3. **Storage Status** - Disk usage, mount points, block devices, and potential issues
4. **Memory Usage** - RAM and swap usage, memory allocation, and potential issues
5. **CPU Performance** - CPU load, utilization, top processes, and potential bottlenecks
6. **Network Configuration** - Network interfaces, listening ports, and potential issues
7. **System Health** - Failed services, system errors, auth failures, available updates
8. **Critical Issues** - Highlight any critical issues that need immediate attention
9. **Warnings** - Highlight potential problems that aren't yet critical
10. **Recommendations** - Specific suggestions for improving system health and performance

Reports are saved to the specified output directory (default: `~/syshealth`) with filenames in the format: `hostname-language-timestamp.md`.

## Dependencies

### Python Dependencies
- anthropic>=0.49.0 (Anthropic Python SDK)

### System Tools
The following standard Linux tools are used to gather system information:
- lshw - Hardware listing
- df - Disk space usage
- ps - Process status
- free - Memory usage
- lsblk - Block device listing
- smartctl - Disk health (optional)
- journalctl - System logs (optional)
- ssh - Remote host connection
- pandoc - For email HTML conversion (optional)

Most tools are available by default. Missing recommended tools will generate warnings but won't prevent the tool from running.

## Troubleshooting

### Debug Mode

Enable debug mode to save the prompts sent to Claude:

```bash
syshealth -d -v myserver
```

Debug files are saved in the `reports/debug` directory.

### Common Issues

- **API Key Errors**: Ensure your Anthropic API key is set correctly
- **SSH Connection Issues**: Verify SSH key-based authentication is set up for remote hosts
- **Missing Dependencies**: Install recommended tools for better results
- **Permission Errors**: Some system information may require root access

## License

MIT