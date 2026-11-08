# SysHealth

SysHealth collects a Linux host's health data, locally or over SSH, and has
an LLM write the report: findings ranked by severity, each with the evidence
behind it and the command to check or fix it. It is one Bash script. Claude
is the default model; OpenAI, Google Gemini, DeepSeek, xAI and a local Ollama
model also work.

```bash
syshealth -v                                  # this host, report printed
syshealth -L id --mail ops@example.com srv1   # a remote host, in Indonesian, mailed
syshealth -n srv1 | less                      # see exactly what would be sent
```

## Features

- **One SSH connection per host.** The collector travels as a single base64
  command line, so a command on the host that reads stdin cannot swallow the
  rest of the script, and the login shell's quoting never touches it.
- **Evidence the model can trust.** Each section is framed by a marker that
  carries a random 128-bit value, new for every run, so text already on the
  host (a log line, a file name) cannot pass itself off as a section, and the
  prompt tells the model the data is untrusted.
- **Compact data.** Each section keeps at most 200 lines and each line 500
  characters; a socket shared by many worker processes is one line with a
  PID count, so a busy web server costs tokens for its findings, not its
  process table.
- **CPU figures that mean something.** Busy processes come from a 2-second
  `top` sample, not lifetime averages, and the collector's own processes and
  anything younger than 60 seconds are left out.
- **Context from the operators.** Per-host notes (`CONTEXT_DIR`) tell the
  model what is intentional and which alerts are known false positives.
- **Cut-off reports are flagged.** When the model hits its output limit, the
  report is still saved, but it carries a banner, the mail subject says
  `[TRUNCATED]` and the run exits 1.
- **Current Claude API.** `anthropic-version: 2026-10-21`, adaptive thinking,
  optional effort, and server-side refusal fallback on the models that
  support it.

## Requirements

On the machine that runs `syshealth`:

| Tool | For |
|------|-----|
| Bash 5.2+ | everything |
| `curl`, `jq` | the API call (not needed for `-n`) |
| `ssh` | remote hosts: key authentication, host keys already known |
| `sendmail` | `--mail` (any MTA that provides it) |
| `pandoc` | optional: HTML mail; without it the mail is plain text |

On each analysed host: Bash and the standard Linux tools. These add data
when present: `smartctl` (smartmontools), `sensors` (lm-sensors), `lshw`,
`chkrootkit`, `mdadm`, LVM tools, `zpool`, `docker`, `fail2ban-client`.
Missing tools show up in the report as data gaps, not as faults.

Run it as root, or SSH in as root, for the full picture: SMART data, the
owning process of each listening socket, every crontab and the whole
journal need it. Nothing is written on the analysed host.

## Installation

```bash
install -m 0755 syshealth /usr/local/bin/syshealth
# or keep it in the checkout:
ln -s "$PWD"/syshealth /usr/local/bin/syshealth
```

## Usage

```
syshealth [OPTIONS] [HOST...]
```

With no host, this host is analysed. A host is an SSH destination
(`srv1`, `root@srv1.example.com`, or a `Host` alias from `~/.ssh/config`).

| Option | Meaning |
|--------|---------|
| `-m, --model MODEL` | Model; the provider follows from its name (default `claude-sonnet-5-5`) |
| `-e, --effort LEVEL` | Claude effort: `low`, `medium`, `high`, `xhigh`, `max` (default: the model's own) |
| `-L, --language LANG` | Report language, a name or a code such as `id` or `de` (default `en`) |
| `-o, --output-dir DIR` | Where reports go (default `~/syshealth`) |
| `--mail ADDRESSES` | Mail each report to these comma-separated addresses |
| `-n, --dry-run` | Collect and print the prompt; no API call, no report, no mail |
| `-v, --verbose` | More progress detail, and print each report |
| `-q, --quiet` | Only warnings and errors |
| `-D, --debug` | Name the config files read, and keep the collected data, prompt and API response in `OUTPUT_DIR/debug/` |
| `-V, --version` | Show the version |
| `-h, --help` | Show the help |

Short options can be bundled (`-qn`).

### Examples

```bash
syshealth -v                                   # this host
syshealth -q -o /var/reports srv1 srv2         # two hosts, for cron
syshealth -m claude-opus-5-5 -e high srv1      # a larger Claude model, more effort
syshealth -m gpt-5.2 srv1                      # OpenAI
syshealth -m qwen3 srv1                        # a local Ollama model, no key
syshealth -D srv1                              # keep everything for debugging
```

### Exit status

| Code | Meaning |
|------|---------|
| 0 | every report written |
| 1 | a host failed, or its report was cut off at the output limit |
| 2 | Bash older than 5.2 |
| 18 | a required tool is missing |
| 22 | usage error: missing option argument, invalid option, host or setting |

## Configuration

Settings come from, lowest to highest: the built-in defaults, the config
files, the environment, the command line.

### Config files

`/etc/syshealth/syshealth.conf`, then `~/.config/syshealth/syshealth.conf`
(see `syshealth.conf.example`). They are sourced as Bash, so a file is used
only when it is owned by root or by you and nobody else can write to it; an
unsafe or unreadable file is skipped with a warning. Use plain assignments
(`MODEL=...`, `EXTRA_COMMANDS=(...)`), not `declare`.

`SYSHEALTH_CONF=/path/to/file` reads that one file instead of the two above;
`SYSHEALTH_CONF=` reads none.

| Setting | Default | Meaning |
|---------|---------|---------|
| `MODEL` | `claude-sonnet-5-5` | model, and so the provider |
| `MAX_TOKENS` | `0` | output limit; 0 means 32000 for Claude, 16384 for OpenAI, 8192 for the others |
| `EFFORT` | empty | Claude effort; empty leaves the model's default |
| `TEMPERATURE` | `0.1` | sent to OpenAI-compatible providers only (see below) |
| `API_TIMEOUT` | `900` | seconds for the API call |
| `COLLECT_TIMEOUT` | `600` | seconds for collecting one host |
| `OUTPUT_DIR` | `~/syshealth` | report directory |
| `LANGUAGE` | `en` | report language |
| `MAIL_RECIPIENTS` | empty | as `--mail` |
| `MAIL_FROM` | `SysHealth <syshealth@HOSTNAME>` | mail sender |
| `CONTEXT_DIR` | `/etc/syshealth/hosts` | operator notes, see below |
| `EXTRA_COMMANDS` | `()` | extra commands run on every host, see below |
| `DISK_WARN`, `DISK_CRIT` | `80`, `90` | filesystem use, % |
| `MEM_WARN`, `MEM_CRIT` | `85`, `95` | memory use, % |
| `LOAD_WARN` | `1.0` | sustained load average per CPU core |
| `MAX_SECTION_LINES` | `200` | lines kept from each collected section |
| `MAX_LINE_CHARS` | `500` | characters kept from each collected line |

### Environment

| Variable | Meaning |
|----------|---------|
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `XAI_API_KEY` | the provider's key |
| `ANTHROPIC_BASE_URL` | Claude API base URL (default `https://api.anthropic.com`) |
| `OLLAMA_HOST` | Ollama URL (default `http://localhost:11434`) |
| `SYSHEALTH_MODEL`, `SYSHEALTH_MAX_TOKENS`, `SYSHEALTH_TEMPERATURE`, `SYSHEALTH_EFFORT`, `SYSHEALTH_TIMEOUT`, `SYSHEALTH_OUTPUT_DIR`, `SYSHEALTH_LANGUAGE`, `SYSHEALTH_CONTEXT_DIR` | override the setting of the same name (`SYSHEALTH_TIMEOUT` sets `API_TIMEOUT`) |
| `SYSHEALTH_CONF` | the one config file to read, or empty for none |

A key or URL set in the environment wins over one in a config file. For
Claude, when no key is set anywhere, `~/.config/anthropic/api_key` and then
`/etc/anthropic/api_key` are read. The key reaches `curl` through a file
descriptor, never its command line, and is never printed.

### Providers and models

| Model name | Provider | Key |
|------------|----------|-----|
| `claude-*` | Anthropic | `ANTHROPIC_API_KEY` |
| `gpt-*`, `chatgpt-*`, `o1`, `o3`, ... | OpenAI | `OPENAI_API_KEY` |
| `gemini-*` | Google Gemini (OpenAI-compatible endpoint) | `GEMINI_API_KEY` |
| `deepseek-*` | DeepSeek | `DEEPSEEK_API_KEY` |
| `grok-*` | xAI | `XAI_API_KEY` |
| anything else | Ollama | none |

For Claude, the request uses API version `2026-10-21`, which rejects
`temperature`, `top_p` and `top_k` on every model, so none is sent. Thinking
is adaptive and counts against `MAX_TOKENS`, hence the 32000 default. On
`claude-opus-5`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-fable-5-1`
and `claude-mythos-5-1` the request also asks for the server-side refusal
fallback (`fallbacks: "default"`); the provenance line under each report names
the model that actually answered.

For OpenAI's GPT-5 and o-series models, `max_completion_tokens` is sent and
the temperature is not; other providers get `max_tokens` and `TEMPERATURE`.

### Operator notes: `CONTEXT_DIR`

Markdown files the model reads as trusted context, ahead of the data:

- `CONTEXT_DIR/common.md`, for every host;
- `CONTEXT_DIR/HOST.md`, for one host (for `root@srv1.example.com`, both
  `srv1.example.com.md` and `srv1.md` are read).

Use them for what the data cannot tell the model: the host's role, what is
intentional, and alerts already verified as false positives.

```markdown
srv1 is the backup target. /backup-offline is a removable disk, noauto
in fstab and normally not mounted. The chkrootkit "suspicious file" line
for /usr/lib/debug/.build-id is a known false positive.
```

### Extra commands: `EXTRA_COMMANDS`

Each entry runs on every host with `bash -c` and becomes its own section,
with a 120-second limit:

```bash
EXTRA_COMMANDS=(
  'systemctl status --no-pager myapp'
  'cat /etc/myapp/schedule.conf'
)
```

## What is collected

Collection time and user; host, uptime and CPU count; pressure stall
information; boot history (wtmp reboot records and the journal); kernel, reboot-required flag and Livepatch; time
sync; CPU; memory and swap; OOM kills (7 days); hardware; temperatures;
filesystems and inodes; block devices; fstab; network mounts and automount
units; RAID; LVM; ZFS; SMART per disk; busiest processes (2-second sample);
largest processes by memory; zombie processes; interfaces and default route;
listening sockets with their owning process; socket summary; firewall (ufw,
nftables or iptables) and fail2ban; failed units; units with errors in the
last 24 hours and their state now; error-level journal entries (24 hours);
SSH and sudo authentication (24 hours); recent logins; pending updates;
chkrootkit's daily log against its baseline and, when it changed, the files
behind each changed warning from `log.today.raw` (with owner, mode and mtime;
lines `/etc/chkrootkit/chkrootkit.ignore` hides are only counted); crontabs
and systemd timers; docker containers; then any `EXTRA_COMMANDS`.

▲ This data goes to the model's provider. It includes host names, IP
addresses, user names and log lines. Process command lines are not sent,
only process names, and passwords, tokens and keys in crontab lines are
masked, but masking is best effort. Run `syshealth -n` to see exactly what
leaves the machine.

## Reports and mail

Reports are Markdown files named `HOST-LANG-YYYYmmdd-HHMMSS.md` in
`OUTPUT_DIR`, ending with a provenance line: the syshealth version, the
model that answered, the collection time and the token counts.

With `--mail`, each report goes out with the subject `System Health Report
for HOST` (plus `[TRUNCATED]` when cut off). The body is HTML when `pandoc`
is installed, and the Markdown file is attached. Every part is base64, so
the message is plain ASCII on the wire.

## Tests

```bash
bats tests/
```

Needs `bats`, `jq` and `python3`. The suite runs the collector on this host
and answers API calls from a local stub (`tests/stub_api.py`), so it needs no
key and no network.

## Troubleshooting

- ◉ **See what is sent:** `syshealth -n HOST`.
- ✗ **`SSH failed`:** the host must accept key authentication without a
  prompt and its host key must already be in `known_hosts`
  (`ssh HOST true` should succeed silently).
- ✗ **`... is not set`:** set the provider's key in the environment or a
  config file; check with `syshealth -D` that the file you expect was used.
- ▲ **Report cut off:** raise `MAX_TOKENS`, or lower `EFFORT`, so thinking
  leaves room for the report.
- ▲ **API timeout:** raise `SYSHEALTH_TIMEOUT`, or choose a faster model.
- ◉ **A section says `[timed out after Ns]`:** the host was too slow to
  answer that command; the model reports it as a data gap.

## License

GPLv3. See `LICENSE`.
