# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

remote_ssh_cmd_ssh_status_usage() {
  cat <<'EOF'
Usage: remote-ssh ssh status [host]

Shows SSH config include state, SSH agent state, and local ssh -G resolution
for host when provided. It does not open an SSH connection.
EOF
}

remote_ssh_cmd_ssh_status_collect_config() {
  REMOTE_SSH_STATUS_HOME_SSH_CONFIG="${HOME}/.ssh/config"
  REMOTE_SSH_STATUS_CONFIG_LOCAL="$(remote_ssh_cmd_ssh_config_local)"
  REMOTE_SSH_STATUS_INCLUDE_LINE="Include ${REMOTE_SSH_STATUS_CONFIG_LOCAL}"
  REMOTE_SSH_STATUS_HOME_CONFIG_EXISTS=0
  REMOTE_SSH_STATUS_HOME_CONFIG_READABLE=0
  REMOTE_SSH_STATUS_INCLUDE_PRESENT=0
  REMOTE_SSH_STATUS_LOCAL_CONFIG_EXISTS=0
  REMOTE_SSH_STATUS_LOCAL_CONFIG_READABLE=0

  [[ -e "$REMOTE_SSH_STATUS_HOME_SSH_CONFIG" ]] && REMOTE_SSH_STATUS_HOME_CONFIG_EXISTS=1
  [[ -r "$REMOTE_SSH_STATUS_HOME_SSH_CONFIG" ]] && REMOTE_SSH_STATUS_HOME_CONFIG_READABLE=1
  if [[ "$REMOTE_SSH_STATUS_HOME_CONFIG_READABLE" -eq 1 ]] &&
    grep -Fxq "$REMOTE_SSH_STATUS_INCLUDE_LINE" "$REMOTE_SSH_STATUS_HOME_SSH_CONFIG"; then
    REMOTE_SSH_STATUS_INCLUDE_PRESENT=1
  fi

  [[ -e "$REMOTE_SSH_STATUS_CONFIG_LOCAL" ]] && REMOTE_SSH_STATUS_LOCAL_CONFIG_EXISTS=1
  [[ -r "$REMOTE_SSH_STATUS_CONFIG_LOCAL" ]] && REMOTE_SSH_STATUS_LOCAL_CONFIG_READABLE=1
}

remote_ssh_cmd_ssh_status_parse_ssh_g() {
  local line key value

  REMOTE_SSH_STATUS_RESOLVED_HOSTNAME=""
  REMOTE_SSH_STATUS_RESOLVED_USER=""
  REMOTE_SSH_STATUS_RESOLVED_PORT=""
  REMOTE_SSH_STATUS_RESOLVED_PROXYJUMP=""
  REMOTE_SSH_STATUS_RESOLVED_IDENTITYFILES=""

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    key="${line%%[[:space:]]*}"
    value="${line#"$key"}"
    value="${value#"${value%%[![:space:]]*}"}"
    case "$key" in
      hostname)
        [[ -z "$REMOTE_SSH_STATUS_RESOLVED_HOSTNAME" ]] &&
          REMOTE_SSH_STATUS_RESOLVED_HOSTNAME="$value"
        ;;
      user)
        [[ -z "$REMOTE_SSH_STATUS_RESOLVED_USER" ]] &&
          REMOTE_SSH_STATUS_RESOLVED_USER="$value"
        ;;
      port)
        [[ -z "$REMOTE_SSH_STATUS_RESOLVED_PORT" ]] &&
          REMOTE_SSH_STATUS_RESOLVED_PORT="$value"
        ;;
      proxyjump)
        [[ "$value" != "none" && -z "$REMOTE_SSH_STATUS_RESOLVED_PROXYJUMP" ]] &&
          REMOTE_SSH_STATUS_RESOLVED_PROXYJUMP="$value"
        ;;
      identityfile)
        if [[ -z "$REMOTE_SSH_STATUS_RESOLVED_IDENTITYFILES" ]]; then
          REMOTE_SSH_STATUS_RESOLVED_IDENTITYFILES="$value"
        else
          REMOTE_SSH_STATUS_RESOLVED_IDENTITYFILES="${REMOTE_SSH_STATUS_RESOLVED_IDENTITYFILES}"$'\n'"$value"
        fi
        ;;
    esac
  done <<<"$REMOTE_SSH_STATUS_SSH_G_OUTPUT"
}

remote_ssh_cmd_ssh_status_collect_host() {
  local host="$1"

  REMOTE_SSH_STATUS_HOST="$host"
  REMOTE_SSH_STATUS_SSH_G_OUTPUT=""
  REMOTE_SSH_STATUS_SSH_G_EXIT=0
  REMOTE_SSH_STATUS_SSH_FOUND=0

  [[ -n "$host" ]] || return 0

  if ! command -v ssh >/dev/null 2>&1; then
    REMOTE_SSH_STATUS_SSH_G_OUTPUT="ssh not found"
    REMOTE_SSH_STATUS_SSH_G_EXIT=127
    return 0
  fi

  REMOTE_SSH_STATUS_SSH_FOUND=1
  set +e
  REMOTE_SSH_STATUS_SSH_G_OUTPUT="$(ssh -G "$host" 2>&1)"
  REMOTE_SSH_STATUS_SSH_G_EXIT=$?
  set -e

  [[ "$REMOTE_SSH_STATUS_SSH_G_EXIT" -eq 0 ]] && remote_ssh_cmd_ssh_status_parse_ssh_g
}

remote_ssh_cmd_ssh_status_collect() {
  local host="$1"

  remote_ssh_cmd_ssh_status_collect_config
  remote_ssh_cmd_ssh_status_collect_agent
  remote_ssh_cmd_ssh_status_diagnose_agent
  remote_ssh_cmd_ssh_status_collect_host "$host"
}

remote_ssh_cmd_ssh_status_config_state() {
  local exists="$1" readable="$2"

  if [[ "$exists" -eq 0 ]]; then
    printf '[missing]\n'
  elif [[ "$readable" -eq 0 ]]; then
    printf '[not readable]\n'
  else
    printf '[readable]\n'
  fi
}

remote_ssh_cmd_ssh_status_render_config() {
  printf 'SSH config\n'
  printf '  %-18s %s %s\n' 'home config:' "$REMOTE_SSH_STATUS_HOME_SSH_CONFIG" "$(
    remote_ssh_cmd_ssh_status_config_state \
      "$REMOTE_SSH_STATUS_HOME_CONFIG_EXISTS" \
      "$REMOTE_SSH_STATUS_HOME_CONFIG_READABLE"
  )"
  printf '  %-18s %s\n' 'include:' "$REMOTE_SSH_STATUS_INCLUDE_LINE"
  if [[ "$REMOTE_SSH_STATUS_INCLUDE_PRESENT" -eq 1 ]]; then
    printf '  %-18s present\n' 'include status:'
  else
    printf '  %-18s missing\n' 'include status:'
  fi
  printf '  %-18s %s %s\n' 'local config:' "$REMOTE_SSH_STATUS_CONFIG_LOCAL" "$(
    remote_ssh_cmd_ssh_status_config_state \
      "$REMOTE_SSH_STATUS_LOCAL_CONFIG_EXISTS" \
      "$REMOTE_SSH_STATUS_LOCAL_CONFIG_READABLE"
  )"
}

remote_ssh_cmd_ssh_status_render_host() {
  local line

  [[ -n "$REMOTE_SSH_STATUS_HOST" ]] || return 0

  printf '\nSSH host\n'
  printf '  %-18s %s\n' 'host:' "$REMOTE_SSH_STATUS_HOST"
  printf '  %-18s ssh -G %s\n' 'command:' "$REMOTE_SSH_STATUS_HOST"
  if [[ "$REMOTE_SSH_STATUS_SSH_G_EXIT" -eq 0 ]]; then
    printf '  %-18s ok\n' 'status:'
    [[ -n "$REMOTE_SSH_STATUS_RESOLVED_HOSTNAME" ]] &&
      printf '  %-18s %s\n' 'hostname:' "$REMOTE_SSH_STATUS_RESOLVED_HOSTNAME"
    [[ -n "$REMOTE_SSH_STATUS_RESOLVED_USER" ]] &&
      printf '  %-18s %s\n' 'user:' "$REMOTE_SSH_STATUS_RESOLVED_USER"
    [[ -n "$REMOTE_SSH_STATUS_RESOLVED_PORT" ]] &&
      printf '  %-18s %s\n' 'port:' "$REMOTE_SSH_STATUS_RESOLVED_PORT"
    while IFS= read -r line; do
      [[ -n "$line" ]] && printf '  %-18s %s\n' 'identityfile:' "$line"
    done <<<"$REMOTE_SSH_STATUS_RESOLVED_IDENTITYFILES"
    [[ -n "$REMOTE_SSH_STATUS_RESOLVED_PROXYJUMP" ]] &&
      printf '  %-18s %s\n' 'proxyjump:' "$REMOTE_SSH_STATUS_RESOLVED_PROXYJUMP"
  else
    printf '  %-18s exit %s\n' 'status:' "$REMOTE_SSH_STATUS_SSH_G_EXIT"
    while IFS= read -r line; do
      [[ -n "$line" ]] && printf '  output:           %s\n' "$line"
    done <<<"$REMOTE_SSH_STATUS_SSH_G_OUTPUT"
  fi
}

remote_ssh_cmd_ssh_status_print_hints() {
  local printed=0

  printf '\nNext steps\n'

  if [[ "$REMOTE_SSH_STATUS_INCLUDE_PRESENT" -ne 1 ||
    "$REMOTE_SSH_STATUS_LOCAL_CONFIG_READABLE" -ne 1 ]]; then
    printf '  - Run remote-ssh ssh setup to install the SSH config include.\n'
    printed=1
  fi

  if remote_ssh_cmd_ssh_status_agent_needs_fix; then
    remote_ssh_cmd_ssh_status_print_agent_hint
    printed=1
  fi

  if [[ -n "$REMOTE_SSH_STATUS_HOST" && "$REMOTE_SSH_STATUS_SSH_G_EXIT" -ne 0 ]]; then
    printf '  - Inspect SSH config for %s; ssh -G failed before any connection was opened.\n' "$REMOTE_SSH_STATUS_HOST"
    printed=1
  fi

  [[ "$printed" -eq 1 ]] || printf '  [none]\n'
}

remote_ssh_cmd_ssh_status_render() {
  printf 'remote-ssh ssh status\n\n'
  remote_ssh_cmd_ssh_status_render_config
  remote_ssh_cmd_ssh_status_render_agent
  remote_ssh_cmd_ssh_status_render_host
  printf '\nDiagnosis\n'
  printf '  %-18s %s\n' 'ssh config:' "$(
    if [[ "$REMOTE_SSH_STATUS_INCLUDE_PRESENT" -eq 1 &&
      "$REMOTE_SSH_STATUS_LOCAL_CONFIG_READABLE" -eq 1 ]]; then
      printf 'ok'
    else
      printf 'missing'
    fi
  )"
  printf '  %-18s %s\n' 'ssh agent:' "$REMOTE_SSH_STATUS_AGENT_STATUS"
  remote_ssh_cmd_ssh_status_print_hints
}

remote_ssh_cmd_ssh_status() {
  local host="${1:-}"

  case "${1:-}" in
    -h | --help)
      remote_ssh_cmd_ssh_status_usage
      return 0
      ;;
  esac
  (($# <= 1)) || {
    remote_ssh_cmd_ssh_status_usage >&2
    return 1
  }

  remote_ssh_cmd_ssh_status_collect "$host"
  remote_ssh_cmd_ssh_status_render
}
