# shellcheck shell=bash

ensure_this_file_sourced

sshf() {
  local ssh_hosts_cmd="${SSH_HOSTS_CMD:-$HOME/.local/scripts/ssh_hosts.py}"
  mapfile -t HOSTS < <("$ssh_hosts_cmd")

  local selected
  selected="$(printf '%s\n' "${HOSTS[@]}" | fzf --prompt='ssh host> ')" || return 130

  ssh "$selected" "$@"
}
