# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_help_main() {
  if (($# == 0)); then
    remote_ssh_usage
    return 0
  fi

  printf 'remote-ssh help does not accept sections.\n' >&2
  printf 'Use: remote-ssh guide %s\n' "$*" >&2
  return 1
}
