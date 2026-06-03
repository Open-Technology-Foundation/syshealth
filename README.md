# SysHealth - AI-Powered System Health Monitor

SysHealth is a single-file Bash tool that collects comprehensive Linux system information and uses an LLM API -- Anthropic Claude by default, or OpenAI, Google Gemini, DeepSeek, xAI/Grok, or a local Ollama model -- to generate detailed health reports with diagnostics and recommendations.

## Features

- **Single-file tool** -- no frameworks, no package managers, just Bash
- **Comprehensive collection** -- hardware, storage, memory, CPU, network, and security data
- **AI-powered analysis** -- the configured LLM identifies issues and provides actionable recommendations
- **Multi-provider** -- Anthropic, OpenAI, Gemini, DeepSeek, xAI/Grok, and Ollama, auto-detected from the model name
- **Multi-host support** -- analyze local and remote systems in a single run
- **Multi-language reports** -- generate reports in any language
- **Email delivery** -- optional email reports with HTML formatting (via pandoc) or plain text
- **Flexible configuration** -- environment variables, CLI flags, or an optional system config file
- **Debug mode** -- save prompts and enable verbose diagnostics
- **Security hardened** -- PATH lockdown, API key protection via process substitution, input sanitization

## Requirements

- **Bash** 5.2+
- **curl** -- API communication
- **jq** -- JSON construction and parsing
- **An LLM API key** -- for the chosen provider (e.g. `ANTHROPIC_API_KEY`); not required for a local Ollama model
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

Settings are resolved with this precedence (highest first):

**CLI flags > environment variables > system config file > built-in defaults**

The optional system config file is `/etc/syshealth/syshealth.conf` (see
`syshealth.conf.example`). It is sourced at startup; a real environment variable
still overrides a value set in the file.

### Provider and API Key

The provider is auto-detected from the model name (`-m` / `SYSHEALTH_MODEL`):

| Model name | Provider | API key variable |
|------------|----------|------------------|
| `claude-*` | Anthropic (default) | `ANTHROPIC_API_KEY` |
| `gpt-*`, `chatgpt-*`, `o1`/`o3`/… (o-series) | OpenAI | `OPENAI_API_KEY` |
| `gemini-*` | Google Gemini | `GEMINI_API_KEY` |
| `deepseek-*` | DeepSeek | `DEEPSEEK_API_KEY` |
| `grok-*` | xAI / Grok | `XAI_API_KEY` |
| anything else | Ollama (local) | none -- uses `OLLAMA_HOST` |

For **Anthropic**, the key is resolved in this order:

1. `ANTHROPIC_API_KEY` environment variable
2. config file (`/etc/syshealth/syshealth.conf`)
3. `/etc/anthropic/api_key` (system-wide)
4. `~/.config/anthropic/api_key` (per-user; wins over `/etc` if both exist)

Other providers read their key from the environment (or the config file) only.
Ollama needs no key.

Set via environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a key file (Anthropic only):

```bash
mkdir -p ~/.config/anthropic
echo "sk-ant-..." > ~/.config/anthropic/api_key
chmod 600 ~/.config/anthropic/api_key
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | -- |
| `OPENAI_API_KEY` | OpenAI API key | -- |
| `GEMINI_API_KEY` | Google Gemini API key | -- |
| `DEEPSEEK_API_KEY` | DeepSeek API key | -- |
| `XAI_API_KEY` | xAI / Grok API key | -- |
| `OLLAMA_HOST` | Ollama base URL | `http://localhost:11434` |
| `SYSHEALTH_MODEL` | AI model (provider auto-detected from name) | `claude-sonnet-4-5` |
| `SYSHEALTH_MAX_TOKENS` | Max response tokens | `8192` |
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
| `-m, --model MODEL` | AI model (provider auto-detected from name) | `claude-sonnet-4-5` |
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

# Other providers (auto-detected from the model name)
syshealth -v -m gpt-4o server1                 # OpenAI
syshealth -v -m gemini-2.0-flash host1         # Google Gemini
syshealth -v -m llama3.1                        # local Ollama (no API key)

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
          │  call_api()       │  curl → provider LLM API
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
