# shellcheck shell=bash

remote_ssh_config_entries() {
  cat <<'EOF'
REMOTE_SSH_WELCOME|1
REMOTE_SSH_WELCOME_BANNER|1
REMOTE_SSH_WELCOME_COLOR|1
REMOTE_SSH_WELCOME_DEBUG|0
REMOTE_SSH_WELCOME_USER|1
REMOTE_SSH_UPDATE_CHECK|1
REMOTE_SSH_UPDATE_CHECK_INTERVAL|86400
REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY|1
NO_COLOR|[unset]
EOF
}

remote_ssh_config_key_allowed() {
  local wanted="$1" key _default

  while IFS='|' read -r key _default; do
    [[ "$key" == "$wanted" ]] && return 0
  done < <(remote_ssh_config_entries)
  return 1
}
