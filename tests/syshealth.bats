#!/usr/bin/env bats
# Tests for syshealth. Run from the project directory: bats tests/
#
# Bats sources this file inside a function, so the script's file-scope
# 'declare' statements would make every setting local to that function and
# lose it. The tests therefore source a copy whose file-scope declarations
# carry -g; the code under test is otherwise unchanged.
# API calls go to tests/stub_api.py on 127.0.0.1; nothing reaches a provider.
#
#shellcheck source-path=SCRIPTDIR
#shellcheck disable=SC2030,SC2031  # each @test is its own subshell: intended
#shellcheck disable=SC2034  # the settings set here are read by the sourced functions

SCRIPT=$(realpath -- "$BATS_TEST_DIRNAME"/../syshealth)
_src=$(mktemp -d "$BATS_RUN_TMPDIR"/src.XXXXXX)
sed -E 's/^( *)declare (-[-ria]+ )/\1declare -g \2/' "$SCRIPT" > "$_src"/syshealth
#shellcheck source=../syshealth
source "$_src"/syshealth

setup_file() {
  export STUB_DIR=$BATS_FILE_TMPDIR/stub STUB_KEY=sk-ant-stub-0000
  mkdir -p -- "$STUB_DIR"
  python3 -I "$BATS_TEST_DIRNAME"/stub_api.py "$STUB_DIR" 3>&- &
  printf '%s\n' "$!" > "$STUB_DIR"/pid
  local -i i
  for ((i = 0; i < 50; i++)); do
    [[ -s $STUB_DIR/port ]] && break
    sleep 0.1
  done
  [[ -s $STUB_DIR/port ]]
}

teardown_file() {
  kill "$(<"$STUB_DIR"/pid)" 2>/dev/null || true
}

setup() {
  # Keep the host's config files, keys and operator notes out of every test
  export SYSHEALTH_CONF=''
  export HOME=$BATS_TEST_TMPDIR/home
  export XDG_CONFIG_HOME=$HOME/.config
  export SYSHEALTH_CONTEXT_DIR=$BATS_TEST_TMPDIR/context
  export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
  unset -v ANTHROPIC_API_KEY ANTHROPIC_BASE_URL OPENAI_API_KEY GEMINI_API_KEY \
    DEEPSEEK_API_KEY XAI_API_KEY OLLAMA_HOST SYSHEALTH_MODEL SYSHEALTH_MAX_TOKENS \
    SYSHEALTH_TEMPERATURE SYSHEALTH_EFFORT SYSHEALTH_TIMEOUT SYSHEALTH_OUTPUT_DIR \
    SYSHEALTH_LANGUAGE
  W=$BATS_TEST_TMPDIR/work
  mkdir -p -- "$HOME" "$W"
}

# Succeeds when the command fails ('! cmd' never fails a bats test)
refute() {
  if "$@"; then return 1; fi
}

prompt_files() {
  printf 'SYSTEM TEXT\n' > "$W"/system.txt
  printf 'USER TEXT "quoted" \\ back\n' > "$W"/user.txt
}

stub_url() {
  printf 'http://127.0.0.1:%s' "$(<"$STUB_DIR"/port)"
}

# --------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------

@test "-V prints the version, also bundled" {
  run "$SCRIPT" -V
  [[ $status -eq 0 && $output == "syshealth $VERSION" ]]
  run "$SCRIPT" -qV
  [[ $status -eq 0 && $output == "syshealth $VERSION" ]]
}

@test "-h shows the usage and the environment" {
  run "$SCRIPT" -h
  [[ $status -eq 0 ]]
  [[ $output == *'Usage: syshealth [OPTIONS] [HOST...]'* ]]
  [[ $output == *SYSHEALTH_CONF* ]]
}

@test "an unknown option exits 22, including the old -d" {
  run "$SCRIPT" --bogus
  [[ $status -eq 22 && $output == *"Invalid option '--bogus'"* ]]
  run "$SCRIPT" -d
  [[ $status -eq 22 ]]
}

@test "an option missing its argument exits 22; a dash value is checked as a value" {
  run "$SCRIPT" -m
  [[ $status -eq 22 && $output == *"Option '-m' requires an argument"* ]]
  run "$SCRIPT" -L -n
  [[ $status -eq 22 && $output == *"Invalid language '-n'"* ]]
  run "$SCRIPT" -m -n
  [[ $status -eq 22 && $output == *"Invalid model name '-n'"* ]]
}

@test "the file can be sourced twice without readonly errors" {
  run bash -c 'source "$1"; source "$1"; echo "sourced $VERSION"' _ "$SCRIPT"
  [[ $status -eq 0 && $output == "sourced $VERSION" ]]
}

@test "a VERSION exported in the environment does not break the script" {
  run env VERSION=9.9 "$SCRIPT" -V
  [[ $status -eq 0 && $output == "syshealth $VERSION" ]]
  run env VERSION=9.9 "$SCRIPT" --bogus
  [[ $status -eq 22 && $output == *"Invalid option '--bogus'"* ]]
}

@test "a host that looks like an ssh option is refused" {
  run "$SCRIPT" -n -- -oProxyCommand=x
  [[ $status -eq 22 && $output == *'Invalid host'* ]]
}

@test "bad settings are refused before any work" {
  run "$SCRIPT" -n -e extreme
  [[ $status -eq 22 && $output == *Effort* ]]
  run env SYSHEALTH_MAX_TOKENS=lots "$SCRIPT" -n
  [[ $status -eq 22 && $output == *MAX_TOKENS* ]]
  run "$SCRIPT" -n --mail 'ops@example.com,not an address'
  [[ $status -eq 22 && $output == *'Invalid mail address'* ]]
}

# --------------------------------------------------------------------------------
# Utilities and settings
# --------------------------------------------------------------------------------

@test "valid_host accepts SSH destinations and rejects options and shell text" {
  valid_host srv3
  valid_host root@srv3
  valid_host srv1.example.com
  refute valid_host -oProxyCommand=x
  refute valid_host 'a;b'
  refute valid_host 'two words'
  refute valid_host '@host'
  refute valid_host ''
}

@test "sanitize_filename never returns a path or a dot name" {
  [[ $(sanitize_filename 'a/b c') == abc ]]
  [[ $(sanitize_filename ..) == unknown ]]
  [[ $(sanitize_filename '') == unknown ]]
  [[ $(sanitize_filename srv1.example.com) == srv1.example.com ]]
}

@test "language_name spells out common codes and passes others through" {
  LANGUAGE=id
  [[ $(language_name) == 'Indonesian (Bahasa Indonesia)' ]]
  LANGUAGE=EN
  [[ $(language_name) == English ]]
  LANGUAGE=Tagalog
  [[ $(language_name) == Tagalog ]]
}

@test "validate_settings accepts the defaults and refuses bad values" {
  validate_settings
  MAX_TOKENS='1+1'
  run validate_settings
  [[ $status -eq 22 && $output == *MAX_TOKENS* ]]
  MAX_TOKENS=0 TEMPERATURE=hot
  run validate_settings
  [[ $status -eq 22 && $output == *TEMPERATURE* ]]
  TEMPERATURE=0.1 MAIL_FROM=$'SysHealth <a@b>\nBcc: x@y'
  run validate_settings
  [[ $status -eq 22 && $output == *MAIL_FROM* ]]
  MAIL_FROM='SysHealth <a@b>' MAIL_RECIPIENTS='ops@example.com, admin@example.com'
  validate_settings
  LANGUAGE='id; rm -rf /'
  run validate_settings
  [[ $status -eq 22 ]]
}

@test "load_config: the environment's key beats the file's, SYSHEALTH_* beats both" {
  cat > "$W"/c.conf <<'EOF'
MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=from-config
LANGUAGE=id
EXTRA_COMMANDS=('uptime -p')
EOF
  chmod 600 "$W"/c.conf
  export SYSHEALTH_CONF=$W/c.conf ANTHROPIC_API_KEY=from-env SYSHEALTH_LANGUAGE=nl
  load_config
  [[ ${CONF_READ[*]} == "$W"/c.conf ]]
  [[ $MODEL == claude-sonnet-4-6 ]]
  [[ $ANTHROPIC_API_KEY == from-env ]]
  [[ $LANGUAGE == nl ]]
  [[ ${EXTRA_COMMANDS[0]} == 'uptime -p' ]]
}

@test "load_config ignores a config file others can write" {
  printf 'MODEL=evil-model\n' > "$W"/c.conf
  chmod 666 "$W"/c.conf
  export SYSHEALTH_CONF=$W/c.conf
  run load_config
  [[ $output == *Ignoring* ]]
  load_config 2>/dev/null
  [[ $MODEL == claude-sonnet-5-5 ]]
}

@test "load_config skips an unreadable config file instead of dying" {
  ((EUID)) || skip 'root can read any file'
  printf 'MODEL=x\n' > "$W"/c.conf
  chmod 000 "$W"/c.conf
  export SYSHEALTH_CONF=$W/c.conf
  run load_config
  [[ $status -eq 0 && $output == *'not readable'* ]]
}

# --------------------------------------------------------------------------------
# Provider, key and request bodies
# --------------------------------------------------------------------------------

@test "claude models go to the Messages API with a 32000-token default" {
  MODEL=claude-opus-5-5 MAX_TOKENS=0
  resolve_provider
  [[ $PROVIDER == anthropic ]]
  [[ $API_URL == https://api.anthropic.com/v1/messages ]]
  [[ $MAX_TOKENS == 32000 ]]
}

@test "ANTHROPIC_BASE_URL and OLLAMA_HOST are honoured, trailing slash or not" {
  MODEL=claude-sonnet-5-5 ANTHROPIC_BASE_URL=http://127.0.0.1:9/
  resolve_provider
  [[ $API_URL == http://127.0.0.1:9/v1/messages ]]
  MODEL=llama3.3 OLLAMA_HOST=http://gpu1:11434/
  resolve_provider
  [[ $PROVIDER == ollama && $API_URL == http://gpu1:11434/v1/chat/completions ]]
}

@test "other model names pick their provider and output default" {
  local -A want=(
    [gpt-5.2]='openai 16384' [o3]='openai 16384' [gemini-3-pro]='gemini 8192'
    [deepseek-chat]='deepseek 8192' [grok-4]='xai 8192' [qwen3]='ollama 8192'
  )
  local -- m
  for m in "${!want[@]}"; do
    MODEL=$m MAX_TOKENS=0
    resolve_provider
    [[ "$PROVIDER $MAX_TOKENS" == "${want[$m]}" ]]
  done
  MODEL=claude-opus-5-5 MAX_TOKENS=64000
  resolve_provider
  [[ $MAX_TOKENS == 64000 ]]
}

@test "the refusal fallback goes only to the models that accept it" {
  local -- m
  for m in claude-opus-5 claude-opus-5-5 claude-sonnet-5-5 claude-fable-5-1 claude-mythos-5-1; do
    MODEL=$m
    claude_fallback_supported
  done
  for m in claude-haiku-5-5 claude-sonnet-4-6 claude-opus-4-8; do
    MODEL=$m
    refute claude_fallback_supported
  done
}

@test "resolve_api_key: environment first, then the key file; odd characters refused" {
  PROVIDER=anthropic
  export ANTHROPIC_API_KEY=sk-ant-test_123
  resolve_api_key
  [[ $API_KEY == sk-ant-test_123 ]]
  unset -v ANTHROPIC_API_KEY
  mkdir -p -- "$XDG_CONFIG_HOME"/anthropic
  printf 'sk-from-file\n' > "$XDG_CONFIG_HOME"/anthropic/api_key
  resolve_api_key
  [[ $API_KEY == sk-from-file ]]
  export ANTHROPIC_API_KEY='sk-bad"quote'
  run resolve_api_key
  [[ $status -eq 22 && $output == *'unexpected characters'* ]]
  [[ $output != *quote* ]]
}

@test "the Claude request has no sampling parameters, no effort by default, and the fallback" {
  prompt_files
  MODEL=claude-opus-5-5 MAX_TOKENS=32000 EFFORT='' TEMPERATURE=0.1
  build_payload_anthropic "$W"/system.txt "$W"/user.txt > "$W"/p.json
  jq -e '.model == "claude-opus-5-5" and .max_tokens == 32000' "$W"/p.json
  jq -e 'has("temperature") or has("top_p") or has("top_k") | not' "$W"/p.json
  jq -e 'has("output_config") or has("thinking") | not' "$W"/p.json
  jq -e '.fallbacks == "default"' "$W"/p.json
  jq -e '.system == "SYSTEM TEXT\n" and .messages[0].role == "user"' "$W"/p.json
  jq -e '.messages[0].content == "USER TEXT \"quoted\" \\ back\n"' "$W"/p.json
}

@test "effort is sent when set; no fallback for a model without it" {
  prompt_files
  MODEL=claude-haiku-5-5 MAX_TOKENS=8000 EFFORT=high
  build_payload_anthropic "$W"/system.txt "$W"/user.txt > "$W"/p.json
  jq -e '.output_config.effort == "high"' "$W"/p.json
  jq -e 'has("fallbacks") | not' "$W"/p.json
}

@test "OpenAI GPT-5 and o-series get max_completion_tokens and no temperature" {
  prompt_files
  PROVIDER=openai MODEL=gpt-5.2 MAX_TOKENS=16384 TEMPERATURE=0.1
  build_payload_openai "$W"/system.txt "$W"/user.txt > "$W"/p.json
  jq -e '.max_completion_tokens == 16384 and (has("max_tokens") | not)' "$W"/p.json
  jq -e 'has("temperature") | not' "$W"/p.json
  jq -e '.messages[0].role == "system" and .messages[1].role == "user"' "$W"/p.json
}

@test "other OpenAI-compatible providers get max_tokens and the temperature" {
  prompt_files
  PROVIDER=deepseek MODEL=deepseek-chat MAX_TOKENS=8192 TEMPERATURE=0.1
  build_payload_openai "$W"/system.txt "$W"/user.txt > "$W"/p.json
  jq -e '.max_tokens == 8192 and .temperature == 0.1' "$W"/p.json
}

# --------------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------------

@test "a Claude answer that starts with a thinking block yields all its text" {
  cat > "$W"/r.json <<'EOF'
{"model": "claude-opus-5-5", "stop_reason": "end_turn",
 "content": [{"type": "thinking", "thinking": "hm", "signature": "s"},
             {"type": "text", "text": "# Report\n"}, {"type": "text", "text": "part two\n"}],
 "usage": {"input_tokens": 10, "output_tokens": 5}}
EOF
  parse_anthropic "$W"/r.json "$W"/report.md
  [[ $(<"$W"/report.md) == $'# Report\npart two' ]]
  [[ $RESP_MODEL == claude-opus-5-5 && $RESP_USAGE == '10 in, 5 out' ]]
}

@test "a Claude answer cut off at max_tokens returns 3" {
  cat > "$W"/r.json <<'EOF'
{"model": "claude-opus-5-5", "stop_reason": "max_tokens",
 "content": [{"type": "text", "text": "# Report, half"}], "usage": {}}
EOF
  run parse_anthropic "$W"/r.json "$W"/report.md
  [[ $status -eq 3 ]]
  [[ $(<"$W"/report.md) == '# Report, half' ]]
}

@test "a Claude refusal returns 1 and names its category" {
  cat > "$W"/r.json <<'EOF'
{"model": "claude-opus-5-5", "stop_reason": "refusal",
 "stop_details": {"type": "refusal", "category": "cyber"}, "content": []}
EOF
  run parse_anthropic "$W"/r.json "$W"/report.md
  [[ $status -eq 1 && $output == *'refusal category: cyber'* ]]
}

@test "an answer with no text returns 1" {
  cat > "$W"/r.json <<'EOF'
{"stop_reason": "end_turn", "content": [{"type": "thinking", "thinking": "x", "signature": "s"}]}
EOF
  run parse_anthropic "$W"/r.json "$W"/report.md
  [[ $status -eq 1 && $output == *'no report text'* ]]
}

@test "an API error is reported by its message, or the start of the body" {
  cat > "$W"/e.json <<'EOF'
{"type": "error", "error": {"type": "invalid_request_error", "message": "temperature: not supported"}}
EOF
  [[ $(api_error_message "$W"/e.json) == 'temperature: not supported' ]]
  printf '<html>bad gateway</html>' > "$W"/e.html
  [[ $(api_error_message "$W"/e.html) == '<html>bad gateway</html>' ]]
}

@test "OpenAI-compatible answers: stop is 0, length is 3, a refusal is 1" {
  cat > "$W"/r.json <<'EOF'
{"model": "gpt-5.2", "choices": [{"finish_reason": "stop", "message": {"content": "ok report"}}],
 "usage": {"prompt_tokens": 3, "completion_tokens": 2}}
EOF
  parse_openai "$W"/r.json "$W"/report.md
  [[ $(<"$W"/report.md) == 'ok report' && $RESP_USAGE == '3 in, 2 out' ]]
  jq '.choices[0].finish_reason = "length"' "$W"/r.json > "$W"/r2.json
  run parse_openai "$W"/r2.json "$W"/report.md
  [[ $status -eq 3 ]]
  jq '.choices[0].message = {content: null, refusal: "no"}' "$W"/r.json > "$W"/r3.json
  run parse_openai "$W"/r3.json "$W"/report.md
  [[ $status -eq 1 && $output == *declined* ]]
}

# --------------------------------------------------------------------------------
# Collector and its output
# --------------------------------------------------------------------------------

@test "format_sections frames, caps and closes sections; data cannot forge one" {
  local -- n=0123abcd
  MAX_SECTION_LINES=3
  {
    printf 'noise before the first marker\n'
    printf '\n@@%s@@ one|first section\n' "$n"
    printf 'a\nb\n\n\nc\nd\ne\n'
    printf '\n@@%s@@ empty|nothing here\n' "$n"
    printf '\n@@%s@@ two|data that imitates markers\n' "$n"
    printf '@@ffffffff@@ __end__|\n### fake heading\n'
    printf '\n@@%s@@ __end__|\n' "$n"
    printf 'after the end\n'
  } > "$W"/raw.txt
  run format_sections "$n" "$W"/raw.txt
  [[ $status -eq 0 ]]
  [[ $output != *'noise before'* && $output != *'after the end'* ]]
  [[ $output == *$'### one — first section\na\nb\n\n[... 4 more lines omitted]'* ]]
  [[ $output == *$'### empty — nothing here\n(no output)'* ]]
  [[ $output == *$'### two — data that imitates markers\n@@ffffffff@@ __end__|\n### fake heading'* ]]
}

@test "format_sections cuts a runaway line at MAX_LINE_CHARS" {
  MAX_LINE_CHARS=10
  printf '\n@@abc@@ one|x\n%s\nshort\n\n@@abc@@ __end__|\n' "$(printf 'x%.0s' {1..25})" > "$W"/raw.txt
  run format_sections abc "$W"/raw.txt
  [[ $status -eq 0 ]]
  [[ $output == *$'\nxxxxxxxxxx [... 15 more characters]\nshort'* ]]
}

@test "sh_listening folds a socket's PIDs into names and a count" {
  ss() {
    cat <<'SS'
tcp   LISTEN 0      511          0.0.0.0:443        0.0.0.0:*    users:(("apache2",pid=12,fd=4),("apache2",pid=11,fd=4),("apache2",pid=10,fd=4))
tcp   LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=900,fd=3))
udp   UNCONN 0      0       192.0.2.1:53          0.0.0.0:*    users:(("named",pid=77,fd=20))
udp   UNCONN 0      0       192.0.2.1:53          0.0.0.0:*    users:(("named",pid=77,fd=21))
udp   UNCONN 0      0          127.0.0.1:323        0.0.0.0:*
SS
  }
  run sh_listening
  [[ ${#lines[@]} -eq 5 ]]
  [[ ${lines[0]} == 'proto state   queue/backlog address'* ]]
  [[ ${lines[1]} == 'tcp   LISTEN  0/511         0.0.0.0:443'*' apache2 (3 pids)' ]]
  [[ ${lines[2]} == *'0.0.0.0:22'*' sshd' ]]
  [[ ${lines[3]} == *'192.0.2.1:53'*' named [2 sockets]' ]]
  [[ ${lines[4]} == 'udp   UNCONN  0/0           127.0.0.1:323' ]]
}

# A chkrootkit log directory as the Debian cron job leaves it: today's warning
# is new against the baseline, and the raw log holds the files behind it. The
# filtered log.today keeps the lines the ignore file does not hide: $W/known
# was there yesterday too, $W/stray is new; the ifpromisc block is unchanged.
chkrootkit_fixture() {
  local -- d=$W/ck
  mkdir -p "$d"
  : > "$W"/stray; : > "$W"/known; chmod 0755 "$W"/stray "$W"/known
  printf '%s\n' 'Searching for Linux.Xor.DDoS...      not found' "$W"/known \
    'WARNING: Output from ifpromisc:' 'lo: not promisc and no packet sniffer sockets' > "$d"/log.expected
  printf '%s\n' 'Searching for Linux.Xor.DDoS...      WARNING' 'WARNING: Possible Linux.Xor.DDoS installed:' \
    "$W"/known "$W"/stray \
    'WARNING: Output from ifpromisc:' 'lo: not promisc and no packet sniffer sockets' > "$d"/log.today
  {
    printf 'Searching for Linux.Xor.DDoS...      WARNING\n\nWARNING: Possible Linux.Xor.DDoS installed:\n'
    printf '/tmp/claude-1000/s%d/tool\n' 1 2 3
    printf '%s\n' "$W"/known "$W"/stray
    printf 'Searching for Linux.Proxy.1.0...     not found\n'
    printf 'WARNING: Output from ifpromisc:\nlo: not promisc and no packet sniffer sockets\n'
    printf "Checking \`w55808'...                 not found\n"
  } > "$d"/log.today.raw
  printf '^/tmp/claude-[0-9]+/\n^$\n' > "$d"/ignore
}

@test "sh_chkrootkit lists the files behind a new warning, counting what the ignore file hides" {
  chkrootkit_fixture
  run sh_chkrootkit "$W"/ck "$W"/ck/ignore
  [[ $status -eq 0 ]]
  [[ $output == *'> WARNING: Possible Linux.Xor.DDoS installed:'* ]]
  [[ $output == *$'\nWARNING: Possible Linux.Xor.DDoS installed: 5 lines, 3 hidden by the ignore file\n'* ]]
  [[ $output == *$'\n  hidden: 3 under /tmp/claude-1000\n'* ]]
  # a new file comes with owner, mode and mtime (a quoted =~ pattern is literal, hence the variable)
  local -- re="  $W/stray  \\[[^]]+ -rwxr-xr-x [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}\\]"
  [[ $output =~ $re ]]
  refute grep -q 'claude-1000/s1' <<< "$output"
}

@test "sh_chkrootkit counts a warning's unchanged lines and skips blocks today did not change" {
  chkrootkit_fixture
  run sh_chkrootkit "$W"/ck "$W"/ck/ignore
  [[ $status -eq 0 ]]
  [[ $output == *$'\n  [1 more line unchanged since the baseline]'* ]]
  refute grep -qF -- "  $W/known" <<< "$output"
  refute grep -q 'Output from ifpromisc: ' <<< "$output"
}

@test "sh_chkrootkit with no baseline lists every warning block in full" {
  chkrootkit_fixture
  rm -- "$W"/ck/log.expected
  run sh_chkrootkit "$W"/ck "$W"/ck/ignore
  [[ $status -eq 0 ]]
  [[ $output == *"  $W/known  ["* && $output == *"  $W/stray  ["* ]]
  [[ $output == *$'\nWARNING: Output from ifpromisc: 1 line, 0 hidden by the ignore file\n'* ]]
}

@test "sh_chkrootkit says so when the ignore file cannot be applied, and hides nothing" {
  chkrootkit_fixture
  printf '(\n' > "$W"/ck/ignore             # not a valid ERE: grep exits 2
  rm -- "$W"/ck/log.expected
  run sh_chkrootkit "$W"/ck "$W"/ck/ignore
  [[ $status -eq 0 ]]
  [[ $output == *$'\nWARNING: Possible Linux.Xor.DDoS installed: 5 lines, 0 hidden by the ignore file\n'* ]]
  [[ $output == *'  [the ignore file could not be applied (grep exit 2): nothing hidden]'* ]]
  [[ $output == *'/tmp/claude-1000/s1/tool'* && $output == *"  $W/stray  ["* ]]
}

@test "sh_chkrootkit adds no file lists when today matches the baseline" {
  chkrootkit_fixture
  cp -- "$W"/ck/log.today "$W"/ck/log.expected
  run sh_chkrootkit "$W"/ck "$W"/ck/ignore
  [[ $status -eq 0 ]]
  [[ $output == *'matches the accepted baseline'* ]]
  refute grep -q 'hidden by the ignore file' <<< "$output"
}

@test "format_sections fails when the end marker is missing" {
  printf '\n@@abc@@ one|x\ndata\n' > "$W"/raw.txt
  run format_sections abc "$W"/raw.txt
  [[ $status -eq 3 ]]
}

@test "sh_mask hides credentials in command lines" {
  run sh_mask <<'EOF'
0 2 * * * mysqldump -uroot -pS3cret db > /x
PASSWORD=hunter2 /usr/local/bin/thing
curl -H "token: abc123" https://example.com
api_key=XYZ789 run
0 3 * * * /usr/local/bin/backup -v
EOF
  [[ $output != *S3cret* && $output != *hunter2* && $output != *abc123* && $output != *XYZ789* ]]
  [[ $output == *'-p*****'* && $output == *'PASSWORD=*****'* ]]
  [[ $output == *'0 3 * * * /usr/local/bin/backup -v'* ]]
}

@test "host_context reads common.md, the host's file and its short name's file" {
  CONTEXT_DIR=$SYSHEALTH_CONTEXT_DIR
  mkdir -p -- "$CONTEXT_DIR"
  printf 'fleet note\n' > "$CONTEXT_DIR"/common.md
  printf 'short note\n' > "$CONTEXT_DIR"/srv1.md
  printf 'fqdn note\n' > "$CONTEXT_DIR"/srv1.example.com.md
  run host_context root@srv1.example.com
  [[ $output == *'## common.md'*'fleet note'*'## srv1.example.com.md'*'fqdn note'*'## srv1.md'*'short note'* ]]
  run host_context other
  [[ $output == *'fleet note'* && $output != *'short note'* ]]
}

@test "build_collector ships the nonce, the extra commands quoted, and the end marker" {
  EXTRA_COMMANDS=('uptime -p' "echo \"it's\" \$HOME")
  run build_collector deadbeef
  [[ $output == *$'\nSH_NONCE=deadbeef\nsh_collect\n'* ]]
  [[ $output == *'sh_run extra_1 120 '*'sh_run extra_2 120 '* ]]
  [[ ${lines[-1]} == 'sh_section __end__' ]]
}

@test "a dry run collects every section and prints both prompts" {
  cat > "$W"/test.conf <<'EOF'
LANGUAGE=id
EXTRA_COMMANDS=('echo extra-ok')
EOF
  chmod 600 "$W"/test.conf
  run env SYSHEALTH_CONF="$W"/test.conf "$SCRIPT" -n -q localhost
  [[ $status -eq 0 ]]
  [[ $output == *'===== SYSTEM PROMPT (localhost) ====='* ]]
  [[ $output == *'===== USER PROMPT (localhost) ====='* ]]
  [[ $output == *'this language: Indonesian (Bahasa Indonesia).'* ]]
  [[ $output == *'----- BEGIN SYSTEM DATA '* && $output == *'----- END SYSTEM DATA '* ]]
  [[ $(awk '/^### [a-z0-9_]+ — /{ n++ } END { print n + 0 }' <<< "$output") -eq 37 ]]
  [[ $output == *$'### extra_1 — extra command: echo extra-ok\nextra-ok'* ]]
}

# --------------------------------------------------------------------------------
# Output and end-to-end runs against the stub
# --------------------------------------------------------------------------------

@test "save_report adds the truncation banner and the provenance line" {
  OUTPUT_DIR=$W/out
  mkdir -p -- "$OUTPUT_DIR"
  printf '# Body\n' > "$W"/report.md
  RESP_MODEL=claude-opus-5-5 RESP_USAGE='1 in, 2 out' MAX_TOKENS=32000
  COLLECTED_AT=2026-11-08T12:00:00+07:00
  local -- path
  path=$(save_report root@srv1 "$W" 1)
  [[ $path == "$OUTPUT_DIR"/srv1-en-*.md ]]
  [[ $(head -n 1 -- "$path") == '> ▲ **TRUNCATED**'* ]]
  [[ $(tail -n 1 -- "$path") == "_syshealth $VERSION · claude-opus-5-5 · collected 2026-11-08T12:00:00+07:00 · 1 in, 2 out tokens_" ]]
}

@test "the mail has ASCII headers, marks truncation and attaches the report" {
  mkdir -p -- "$W"/bin
  printf '#!/bin/bash\ncat > %q\n' "$W"/mail.eml > "$W"/bin/sendmail
  chmod +x "$W"/bin/sendmail
  PATH=$W/bin:$PATH
  printf '# Report\nÜnïcode body ✓\n' > "$W"/srv1-en-20261108-120000.md
  MAIL_RECIPIENTS=ops@example.com MAIL_FROM='SysHealth <syshealth@test>'
  send_report root@srv1 "$W"/srv1-en-20261108-120000.md 1 2>/dev/null
  local -- headers
  headers=$(sed '/^$/q' "$W"/mail.eml)
  [[ $headers == *'Subject: System Health Report for srv1 [TRUNCATED]'* ]]
  [[ $headers == *'To: ops@example.com'* && $headers == *'Auto-Submitted: auto-generated'* ]]
  # base64 parts keep the whole message ASCII
  [[ -z $(LC_ALL=C tr -d '\000-\177' < "$W"/mail.eml) ]]
  run python3 -I -c '
import email, sys
from email import policy
m = email.message_from_binary_file(open(sys.argv[1], "rb"), policy=policy.default)
sys.stdout.write(next(p for p in m.walk() if p.get_filename()).get_content())
' "$W"/mail.eml
  [[ $output == "$(<"$W"/srv1-en-20261108-120000.md)" ]]
}

@test "end to end: the request is a valid Claude request and the report is saved" {
  printf 'ok\n' > "$STUB_DIR"/mode
  run env ANTHROPIC_BASE_URL="$(stub_url)" ANTHROPIC_API_KEY="$STUB_KEY" \
    "$SCRIPT" -q -o "$W"/out localhost
  [[ $status -eq 0 ]]
  local -- req=$STUB_DIR/request
  jq -e '.path == "/v1/messages" and ."anthropic-version" == "2026-10-21"' "$req"
  jq -e '."anthropic-beta" == "server-side-fallback-2026-07-01" and .key_ok' "$req"
  jq -e '.body.model == "claude-sonnet-5-5" and .body.max_tokens == 32000' "$req"
  jq -e '.body | has("temperature") | not' "$req"
  jq -e '.body.messages[0].content | contains("----- BEGIN SYSTEM DATA ")' "$req"
  local -a reports=("$W"/out/localhost-en-*.md)
  [[ ${#reports[@]} -eq 1 && -f ${reports[0]} ]]
  [[ $(<"${reports[0]}") == *'stub answer'*"_syshealth $VERSION · claude-sonnet-5-5 · collected "*' · 1234 in, 56 out tokens_' ]]
}

@test "end to end: a report cut off at max_tokens is kept, flagged and exits 1" {
  printf 'truncated\n' > "$STUB_DIR"/mode
  run env ANTHROPIC_BASE_URL="$(stub_url)" ANTHROPIC_API_KEY="$STUB_KEY" \
    "$SCRIPT" -q -o "$W"/out localhost
  [[ $status -eq 1 && $output == *'cut off'* ]]
  local -a reports=("$W"/out/localhost-en-*.md)
  [[ $(head -n 1 -- "${reports[0]}") == '> ▲ **TRUNCATED**'* ]]
}

@test "call_api: a refusal fails the host" {
  printf 'refusal\n' > "$STUB_DIR"/mode
  prompt_files
  PROVIDER=anthropic MODEL=claude-opus-5-5 MAX_TOKENS=32000 API_KEY=$STUB_KEY API_TIMEOUT=30
  API_URL=$(stub_url)/v1/messages
  run call_api "$W"
  [[ $status -eq 1 && $output == *'refusal category: cyber'* ]]
}

#fin
