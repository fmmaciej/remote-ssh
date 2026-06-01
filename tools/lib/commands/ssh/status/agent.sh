# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

remote_ssh_cmd_ssh_status_collect_agent() {
  REMOTE_SSH_STATUS_SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-}"
  REMOTE_SSH_STATUS_SSH_ADD_FOUND=0
  REMOTE_SSH_STATUS_SSH_ADD_OUTPUT=""
  REMOTE_SSH_STATUS_SSH_ADD_EXIT=127
  REMOTE_SSH_STATUS_AGENT_STATUS="ssh-add-missing"

  command -v ssh-add >/dev/null 2>&1 || return 0
  REMOTE_SSH_STATUS_SSH_ADD_FOUND=1

  set +e
  REMOTE_SSH_STATUS_SSH_ADD_OUTPUT="$(ssh-add -l 2>&1)"
  REMOTE_SSH_STATUS_SSH_ADD_EXIT=$?
  set -e
}

remote_ssh_cmd_ssh_status_diagnose_agent() {
  local output="$REMOTE_SSH_STATUS_SSH_ADD_OUTPUT"

  if [[ "$REMOTE_SSH_STATUS_SSH_ADD_FOUND" -ne 1 ]]; then
    REMOTE_SSH_STATUS_AGENT_STATUS="ssh-add-missing"
  elif [[ "$REMOTE_SSH_STATUS_SSH_ADD_EXIT" -eq 0 ]]; then
    REMOTE_SSH_STATUS_AGENT_STATUS="ok"
  elif grep -qi 'no identities' <<<"$output"; then
    REMOTE_SSH_STATUS_AGENT_STATUS="no-keys"
  elif [[ -z "$REMOTE_SSH_STATUS_SSH_AUTH_SOCK" ]]; then
    REMOTE_SSH_STATUS_AGENT_STATUS="missing-sock"
  elif [[ ! -e "$REMOTE_SSH_STATUS_SSH_AUTH_SOCK" && ! -S "$REMOTE_SSH_STATUS_SSH_AUTH_SOCK" ]]; then
    REMOTE_SSH_STATUS_AGENT_STATUS="stale-sock"
  elif grep -Eqi 'error connecting to agent|could not open a connection' <<<"$output"; then
    REMOTE_SSH_STATUS_AGENT_STATUS="unreachable"
  else
    REMOTE_SSH_STATUS_AGENT_STATUS="unreachable"
  fi
}

remote_ssh_cmd_ssh_status_agent_needs_fix() {
  case "$REMOTE_SSH_STATUS_AGENT_STATUS" in
    missing-sock | stale-sock | unreachable | no-keys | ssh-add-missing) return 0 ;;
  esac
  return 1
}

remote_ssh_cmd_ssh_status_print_agent_hint() {
  case "$REMOTE_SSH_STATUS_AGENT_STATUS" in
    missing-sock)
      printf '  - Start or forward an SSH agent, then reopen this shell.\n'
      ;;
    stale-sock)
      printf '  - SSH_AUTH_SOCK points to a dead socket; reconnect or refresh agent forwarding.\n'
      ;;
    unreachable)
      printf '  - ssh-add cannot talk to the agent; reconnect, restart the agent, or fix agent forwarding.\n'
      ;;
    no-keys)
      printf '  - Load a key with ssh-add, or check that your forwarded agent has identities.\n'
      ;;
    ssh-add-missing)
      printf '  - ssh-add is missing, so remote-ssh cannot inspect loaded keys.\n'
      ;;
  esac
}

remote_ssh_cmd_ssh_status_render_agent() {
  printf '\nSSH agent\n'
  if [[ -n "$REMOTE_SSH_STATUS_SSH_AUTH_SOCK" ]]; then
    printf '  %-18s %s\n' 'SSH_AUTH_SOCK:' "$REMOTE_SSH_STATUS_SSH_AUTH_SOCK"
  else
    printf '  %-18s [missing]\n' 'SSH_AUTH_SOCK:'
  fi

  if [[ "$REMOTE_SSH_STATUS_SSH_ADD_FOUND" -eq 1 ]]; then
    if [[ "$REMOTE_SSH_STATUS_SSH_ADD_EXIT" -eq 0 ]]; then
      while IFS= read -r line; do
        [[ -n "$line" ]] && printf '  key:              %s\n' "$line"
      done <<<"$REMOTE_SSH_STATUS_SSH_ADD_OUTPUT"
    else
      printf '  %-18s %s\n' 'keys:' "$REMOTE_SSH_STATUS_SSH_ADD_OUTPUT"
    fi
  else
    printf '  %-18s [ssh-add not found]\n' 'keys:'
  fi
}
