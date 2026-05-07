# shellcheck shell=bash
# shellcheck disable=SC2034,SC2153

ensure_this_file_sourced

remote_ssh_cmd_git_status_diagnose_agent() {
  local output="$REMOTE_SSH_GIT_STATUS_SSH_ADD_OUTPUT"

  if [[ "$REMOTE_SSH_GIT_STATUS_SSH_ADD_FOUND" -ne 1 ]]; then
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="ssh-add-missing"
  elif [[ "$REMOTE_SSH_GIT_STATUS_SSH_ADD_EXIT" -eq 0 ]]; then
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="ok"
  elif grep -qi 'no identities' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="no-keys"
  elif [[ -z "$REMOTE_SSH_GIT_STATUS_SSH_AUTH_SOCK" ]]; then
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="missing-sock"
  elif [[ ! -e "$REMOTE_SSH_GIT_STATUS_SSH_AUTH_SOCK" && ! -S "$REMOTE_SSH_GIT_STATUS_SSH_AUTH_SOCK" ]]; then
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="stale-sock"
  elif grep -Eqi 'error connecting to agent|could not open a connection' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="unreachable"
  else
    REMOTE_SSH_GIT_STATUS_AGENT_STATUS="unreachable"
  fi
}

remote_ssh_cmd_git_status_diagnose_auth() {
  local output="$REMOTE_SSH_GIT_STATUS_SSH_OUTPUT"

  if [[ -z "$REMOTE_SSH_GIT_STATUS_SSH_HOST" ]]; then
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="skipped"
  elif grep -qi 'successfully authenticated' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="ok"
  elif grep -qi 'Permission denied (publickey)' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="denied-publickey"
  elif grep -Eqi 'Could not resolve hostname|Name or service not known|nodename nor servname|Temporary failure in name resolution' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="host-unresolved"
  elif grep -Eqi 'Host key verification failed|REMOTE HOST IDENTIFICATION HAS CHANGED|Offending .* key' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="host-key-failed"
  elif grep -Eqi 'Connection timed out|Operation timed out|Connection refused|No route to host|Network is unreachable|Connection reset|Connection closed' <<<"$output"; then
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="network-failed"
  else
    REMOTE_SSH_GIT_STATUS_AUTH_STATUS="failed"
  fi
}

remote_ssh_cmd_git_status_diagnose() {
  remote_ssh_cmd_git_status_diagnose_agent
  remote_ssh_cmd_git_status_diagnose_auth
}
