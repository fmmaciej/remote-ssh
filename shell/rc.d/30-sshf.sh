# shellcheck shell=bash

ensure_this_file_sourced

sshf() {
  local ssh_hosts_cmd="${SSH_HOSTS_CMD:-$REMOTE_ENV_DIR/scripts/ssh_hosts.py}"
  local hosts

  local selected
  hosts="$("$ssh_hosts_cmd" 2>&1)" || {
    printf '[WARN] sshf could not list SSH hosts.\n' >&2
    printf '[WARN] sshf currently requires python3 for scripts/ssh_hosts.py.\n' >&2
    [[ -n "$hosts" ]] && printf '%s\n' "$hosts" >&2
    return 1
  }

  [[ -n "$hosts" ]] || {
    printf '[WARN] sshf found no SSH hosts.\n' >&2
    return 1
  }

  selected="$(printf '%s\n' "$hosts" | fzf --prompt='ssh host> ')" || return 130

  # shellcheck disable=SC2029
  ssh "$selected" "$@"
}
