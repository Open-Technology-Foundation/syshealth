# SysHealth - AI-Powered System Health Monitor

SysHealth is a comprehensive Linux system health monitoring tool that combines traditional system information gathering with advanced AI analysis. It examines local or remote systems, collects detailed hardware and performance data, and uses Claude AI to generate intelligent health reports with actionable insights and recommendations.

## Features

- **Comprehensive System Analysis**: Collects hardware, storage, memory, CPU, network, and security information
- **AI-Powered Insights**: Uses Claude AI to analyze data and identify potential issues
- **Multi-Host Support**: Analyze multiple systems simultaneously 
- **Remote Analysis**: Monitor remote systems via SSH (key-based authentication)
- **Multi-Language Reports**: Generate reports in multiple languages
- **Flexible Output**: Markdown reports with optional email delivery
- **Modular Architecture**: Extensible collector-based design
- **YAML Configuration**: Centralized configuration with environment variable overrides
- **Debug Mode**: Detailed logging and troubleshooting capabilities

## Requirements

- **Operating System**: Ubuntu/Debian Linux (primary), other distributions supported
- **Python**: Version 3.8+ (3.12+ recommended)
- **API Key**: Anthropic API key for Claude AI analysis
- **SSH Access**: For remote host analysis (key-based authentication required)

### System Dependencies

**Required:**
- `python3` - Core runtime

**Recommended (for optimal functionality):**
- `lshw` - Hardware information listing
- `df` - Disk space usage
- `ps` - Process information
- `free` - Memory usage
- `lsblk` - Block device listing
- `ss` or `netstat` - Network statistics

**Optional (for enhanced features):**
- `pandoc` - Email HTML conversion
- `smartctl` - Disk health monitoring
- `chkrootkit` - Security scanning

## Installation

### Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/syshealth.git
cd syshealth

# Install system-wide (requires sudo)
sudo ./install.sh
```

The installer will:
1. Copy files to `/usr/local/syshealth`
2. Create symlink in `/usr/local/bin/syshealth`
3. Set up Python virtual environment
4. Install Python dependencies

### Manual Installation

```bash
# Clone repository
git clone https://github.com/yourusername/syshealth.git
cd syshealth

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x syshealth syshealth.py
```

## Configuration

### API Key Setup

Set your Anthropic API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

For persistent use, add to your `~/.bashrc` or `~/.profile`.

### Configuration File

SysHealth uses a YAML configuration file located at `config/syshealth.yaml`. Key settings include:

- **Claude Model**: Default AI model (`claude-sonnet-4-0`)
- **Report Thresholds**: Warning and critical levels for disk, memory, CPU
- **Output Settings**: File formats, directories, naming patterns
- **Email Configuration**: SMTP settings for report delivery
- **Command Timeouts**: Execution limits for system commands

Settings can be overridden with environment variables using the format:
`SYSHEALTH_<section>_<key>` (e.g., `SYSHEALTH_CLAUDE_MODEL`)

## Usage

### Basic Usage

```bash
# Analyze local system with verbose output
syshealth -v

# Analyze remote host
syshealth -v remote-server

# Analyze multiple hosts with Spanish reports
syshealth -v -L spanish server1 server2 server3

# Custom output directory
syshealth -v -o /path/to/reports hostname
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-v, --verbose` | Enable verbose output (show reports in terminal) | `false` |
| `-d, --debug` | Enable debug mode (save API prompts and details) | `false` |
| `-L, --language LANG` | Report language | `en` |
| `-m, --model MODEL` | Claude model to use | `claude-sonnet-4-0` |
| `-o, --output-dir DIR` | Report output directory | `~/syshealth` |
| `--mail EMAILS` | Comma-separated email recipients | `none` |
| `hosts` | Space-separated list of hosts to analyze | `current host` |

### Email Reports

Send reports via email using local SMTP:

```bash
# Single recipient
syshealth -v --mail admin@example.com server1

# Multiple recipients
syshealth -v --mail "admin@example.com,ops@example.com" server1 server2
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
syshealth -d -v hostname
```

Debug files are saved to `reports/debug/` and include:
- Full prompts sent to Claude API
- Command execution timings
- API response metadata

## Report Structure

Generated reports include the following sections:

1. **System Overview** - Hostname, OS version, uptime, basic status
2. **Hardware Configuration** - CPU, memory, storage components
3. **Storage Status** - Disk usage, mount points, filesystem health
4. **Memory Usage** - RAM and swap utilization and allocation
5. **CPU Performance** - Load averages, top processes, bottlenecks
6. **Network Configuration** - Interfaces, listening ports, connections
7. **System Health** - Failed services, logs, authentication issues
8. **Critical Issues** - High-priority problems requiring immediate attention
9. **Warnings** - Potential issues that aren't yet critical
10. **Recommendations** - Specific improvement suggestions

Reports are saved as markdown files with format: `hostname-language-timestamp.md`

## Architecture

SysHealth uses a modular architecture for maintainability and extensibility:

### Core Components

- **Main Script** (`syshealth.py`) - Entry point and workflow orchestration
- **Claude Client** (`claude_client.py`) - AI API integration
- **Collectors** - Specialized system information gathering modules
- **Executors** - Command execution abstraction (local/remote)
- **Configuration** - YAML-based settings management

### Collectors

- `BasicSystemInfoCollector` - OS, hostname, uptime
- `HardwareInfoCollector` - CPU, memory, hardware listing
- `StorageInfoCollector` - Disks, filesystems, health
- `ProcessInfoCollector` - Running processes, resource usage
- `NetworkInfoCollector` - Interfaces, ports, connectivity
- `SecurityInfoCollector` - Services, logs, updates, security checks

### Executors

- `LocalCommandExecutor` - Local command execution
- `RemoteCommandExecutor` - SSH-based remote execution

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run tests
pytest

# Run with coverage
pytest --cov=syshealth
```

### Code Quality

```bash
# Format code
black .

# Check style
flake8

# Sort imports
isort .
```

### Project Structure

```
syshealth/
├── syshealth.py           # Main application entry point
├── claude_client.py       # Claude AI integration
├── syshealth              # Bash wrapper script
├── install.sh             # Installation script
├── requirements.txt       # Python dependencies
├── config/                # Configuration management
│   ├── syshealth.yaml    # Main configuration file
│   └── *.py              # Config modules
├── collectors/            # System information collectors
├── executors/             # Command execution abstractions
├── tests/                 # Unit tests
└── reports/              # Generated health reports
```

## Troubleshooting

### Common Issues

**API Key Errors:**
- Verify `ANTHROPIC_API_KEY` is set: `echo $ANTHROPIC_API_KEY`
- Ensure API key is valid and has sufficient credits

**SSH Connection Failures:**
- Verify SSH key-based authentication is configured
- Test SSH access: `ssh hostname`
- Check SSH permissions and host key verification

**Missing Dependencies:**
- Install recommended packages: `sudo apt-get install lshw df ps free lsblk`
- Check dependency status in verbose mode

**Virtual Environment Issues:**
- Recreate environment: `rm -rf .venv && python3 -m venv .venv`
- Reinstall dependencies: `source .venv/bin/activate && pip install -r requirements.txt`

### Debug Information

Use debug mode (`-d`) to troubleshoot issues:
- API communication problems
- Command execution failures
- Configuration issues
- Performance bottlenecks

Debug files are saved to `reports/debug/` with detailed information about:
- Prompts sent to Claude API
- Command execution timings
- Error messages and stack traces

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run code quality checks
5. Submit a pull request

For development setup and contribution guidelines, see `CLAUDE.md`.