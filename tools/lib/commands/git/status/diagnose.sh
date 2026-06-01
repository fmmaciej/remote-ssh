# shellcheck shell=bash
# shellcheck disable=SC2034,SC2153

ensure_this_file_sourced

remote_ssh_cmd_git_status_diagnose_agent() {
  remote_ssh_cmd_ssh_status_diagnose_agent
  REMOTE_SSH_GIT_STATUS_AGENT_STATUS="$REMOTE_SSH_STATUS_AGENT_STATUS"
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
