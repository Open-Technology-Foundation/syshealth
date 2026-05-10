#!/usr/bin/bash
#shellcheck disable=SC2155,SC2046,SC2015,SC2034
set -euo pipefail
shopt -s inherit_errexit shift_verbose extglob nullglob

# syshealth.x — Agentic system health monitor
# Uses Claude CLI to investigate system health and produce a markdown report

readonly -- PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
export PATH
IFS=$' \t\n'

declare -r VERSION=1.0.0
declare -r SCRIPT_PATH=$(realpath -- "$0")
declare -r SCRIPT_DIR=${SCRIPT_PATH%/*} SCRIPT_NAME=${SCRIPT_PATH##*/}

# Defaults
declare -- MODEL=sonnet
declare -- OUTPUT_DIR="$HOME/syshealth"
declare -- LANGUAGE=en
declare -- MAX_BUDGET=1.00

# Thresholds
declare -i DISK_WARN=80 DISK_CRIT=90
declare -i MEM_WARN=85 MEM_CRIT=95
declare -- CPU_WARN=2.0

# Environment variable overrides
[[ -n "${SYSHEALTH_MODEL:-}" ]]      && MODEL=$SYSHEALTH_MODEL
[[ -n "${SYSHEALTH_OUTPUT_DIR:-}" ]] && OUTPUT_DIR=$SYSHEALTH_OUTPUT_DIR
[[ -n "${SYSHEALTH_LANGUAGE:-}" ]]   && LANGUAGE=$SYSHEALTH_LANGUAGE
[[ -n "${SYSHEALTH_MAX_BUDGET:-}" ]] && MAX_BUDGET=$SYSHEALTH_MAX_BUDGET

# Flags
declare -i VERBOSE=0 DEBUG=0 QUIET=0

# TTY-aware colors
if [[ -t 1 && -t 2 ]]; then
  declare -r NC=$'\033[0m'
  declare -r RED=$'\033[0;31m' GREEN=$'\033[0;32m'
  declare -r YELLOW=$'\033[0;33m' CYAN=$'\033[0;36m'
else
  declare -r NC='' RED='' GREEN='' YELLOW='' CYAN=''
fi

# --------------------------------------------------------------------------------
# Messaging functions
# --------------------------------------------------------------------------------

_msg() {
  local -- caller=${FUNCNAME[1]:-info}
  local -- prefix icon color
  case $caller in
    info)    icon='◉'; color="$CYAN" ;;
    warn)    icon='▲'; color="$YELLOW" ;;
    error)   icon='✗'; color="$RED" ;;
    success) icon='✓'; color="$GREEN" ;;
    vecho)   icon='◉'; color="$CYAN" ;;
    debug)   icon='⦿'; color="$CYAN" ;;
    *)       icon='◉'; color="$CYAN" ;;
  esac
  prefix="${color}${icon}${NC}"
  >&2 printf '%s %s\n' "$prefix" "$*"
}

vecho()   { ((VERBOSE)) || return 0; _msg "$@"; }
info()    { ((QUIET)) && return 0 ||:; _msg "$@"; }
warn()    { _msg "$@"; }
error()   { _msg "$@"; }
success() { _msg "$@"; }
debug()   { ((DEBUG)) || return 0; _msg "$@"; }
die()     { (($# < 2)) || error "${@:2}"; exit "${1:-0}"; }
noarg()   { (($# > 1)) && [[ ${2:0:1} != '-' ]] || die 2 "Option ${1@Q} requires an argument"; }

# --------------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------------

show_help() {
  cat <<EOT
$SCRIPT_NAME $VERSION - Agentic System Health Monitor

Uses Claude CLI to investigate system health and produce a markdown report.
Claude runs diagnostic commands itself — no manual data collection needed.

Usage: $SCRIPT_NAME [OPTIONS]

Options:
  -v, --verbose        Print report to terminal after saving
  -d, --debug          Debug mode (implies -v)
  -q, --quiet          Suppress info messages
  -L, --language LANG  Report language (default: $LANGUAGE)
  -m, --model MODEL    Claude model alias or ID (default: $MODEL)
  -o, --output-dir DIR Output directory (default: $OUTPUT_DIR)
  -b, --budget AMOUNT  Max API budget in USD (default: $MAX_BUDGET)
  -V, --version        Show version
  -h, --help           Show this help

Environment variables:
  SYSHEALTH_MODEL        Default model
  SYSHEALTH_OUTPUT_DIR   Default output directory
  SYSHEALTH_LANGUAGE     Default language
  SYSHEALTH_MAX_BUDGET   Max API budget in USD

Examples:
  $SCRIPT_NAME -v                     # Verbose report with default model
  $SCRIPT_NAME -m opus               # Use Opus model
  $SCRIPT_NAME -L indonesian -v      # Indonesian language report
  $SCRIPT_NAME -b 0.50 -q            # Budget cap \$0.50, quiet
EOT
}

# --------------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------------

check_dependencies() {
  command -v claude >/dev/null || die 18 "'claude' CLI required (npm install -g @anthropic-ai/claude-code)"
}

# --------------------------------------------------------------------------------
# System prompt builder
# --------------------------------------------------------------------------------

build_system_prompt() {
  cat <<PROMPT
You are a senior Linux system administrator performing a comprehensive health check on this machine.

## Investigation Checklist

Run the following diagnostic commands (use sudo where needed). If a command fails or is unavailable, note it and move on.

### Basic System Info
- uname -a
- lsb_release -a  OR  cat /etc/os-release
- uptime
- timedatectl status
- hostnamectl

### Hardware & Resources
- lscpu
- free -h
- sensors  OR  cat /sys/class/thermal/thermal_zone*/temp
- lshw -short (if available)

### Storage
- df -h
- lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
- cat /proc/mdstat (RAID status)
- lvs, vgs, pvs (LVM, if configured)
- smartctl -H /dev/<disk> for each physical disk

### Processes & Services
- ps --no-headers -eo pid,pcpu,pmem,comm --sort=-%cpu | head -15
- ps --no-headers -eo pid,pcpu,pmem,comm --sort=-%mem | head -15
- systemctl list-units --state=failed
- systemctl list-units --type=service --state=running | head -30

### Network
- ip -brief addr
- ss -tlnp (listening TCP ports)
- ip route show default
- cat /etc/resolv.conf

### Security & Logs
- last -n 5
- journalctl -p err --since "24 hours ago" --no-pager | tail -30
- Check if unattended-upgrades is active
- ufw status  OR  iptables -L -n | head -20

## Report Format

Produce a well-structured markdown report with these sections:

# System Health Report: <hostname>
**Date**: <current date/time>
**OS**: <distro and version>
**Uptime**: <uptime>

## Executive Summary
One paragraph overall assessment. State whether the system is healthy, degraded, or critical.

## Findings

### Critical Issues
Items requiring immediate attention. If none, write "No critical issues found."

### Warnings
Items that may need attention soon.

### Observations
Notable but non-urgent findings.

## Resource Usage
Table or summary of CPU, memory, disk, and swap utilisation.

## Recommendations
Numbered list of actionable recommendations, ordered by priority.

## Thresholds Used
- Disk warning: ${DISK_WARN}% / critical: ${DISK_CRIT}%
- Memory warning: ${MEM_WARN}% / critical: ${MEM_CRIT}%
- CPU load warning: ${CPU_WARN} (per core)

## Rules
1. Only run READ-ONLY commands. Never modify system state.
2. If a command fails or requires unavailable privileges, note the gap and continue.
3. Be specific — cite actual numbers, paths, and service names. Avoid generic advice.
4. Write the report in ${LANGUAGE}.
PROMPT
}

# --------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------

main() {
  while (($#)); do
    case $1 in
      -h|--help)       show_help; exit 0 ;;
      -V|--version)    echo "$SCRIPT_NAME $VERSION"; exit 0 ;;
      -v|--verbose)    VERBOSE+=1 ;;
      -d|--debug)      DEBUG=1; VERBOSE=1 ;;
      -q|--quiet)      QUIET=1 ;;
      -L|--language)   noarg "$@"; shift; LANGUAGE=$1 ;;
      -m|--model)      noarg "$@"; shift; MODEL=$1 ;;
      -o|--output-dir) noarg "$@"; shift; OUTPUT_DIR=$1 ;;
      -b|--budget)     noarg "$@"; shift; MAX_BUDGET=$1 ;;
      -[vdqVh]*)       set -- '' $(printf -- '-%c ' $(grep -o . <<< "${1:1}")) "${@:2}" ;;
      -*)              die 22 "Invalid option ${1@Q}" ;;
      *)               die 22 "Unexpected argument ${1@Q}" ;;
    esac
    shift
  done

  readonly -- MODEL LANGUAGE OUTPUT_DIR MAX_BUDGET
  readonly -- VERBOSE DEBUG QUIET

  check_dependencies

  mkdir -p -- "$OUTPUT_DIR" || die 1 "Cannot create output directory ${OUTPUT_DIR@Q}"

  info "Starting system health analysis (model=$MODEL, budget=\$$MAX_BUDGET)"

  local -- system_prompt
  system_prompt=$(build_system_prompt)

  debug "System prompt: ${#system_prompt} bytes"

  # Build claude command
  local -a cmd=(
    env -u CLAUDECODE
    claude --print
    --model "$MODEL"
    --system-prompt "$system_prompt"
    --allowedTools "Bash,Read"
    --dangerously-skip-permissions
    --no-session-persistence
    --max-budget-usd "$MAX_BUDGET"
  )

  debug "Command: ${cmd[*]}"

  # Run claude and capture report
  local -- report
  info "Claude is investigating system health..."
  report=$("${cmd[@]}" "Investigate this system's health and produce a markdown report.") \
    || die 1 'Claude analysis failed'

  # Save report
  local -- timestamp hostname_safe report_path
  timestamp=$(date +%Y%m%d-%H%M%S)
  hostname_safe=${HOSTNAME//[^a-zA-Z0-9._-]/}
  report_path="${OUTPUT_DIR}/${hostname_safe}-${LANGUAGE}-${timestamp}.md"

  printf '%s\n' "$report" > "$report_path"
  success "Report saved: $report_path"

  # Display if verbose
  if ((VERBOSE)); then
    printf '\n%s\n' '================================================================================'
    printf 'HEALTH REPORT FOR %s:\n' "$HOSTNAME"
    printf '%s\n' '================================================================================'
    printf '%s\n' "$report"
    printf '%s\n' '================================================================================'
  fi
}

main "$@"

#fin
