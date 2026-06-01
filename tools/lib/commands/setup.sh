# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_setup_usage() {
  cat <<'EOF'
Usage: remote-ssh setup

Runs the default remote-ssh setup flow:
  remote-ssh ssh setup
  remote-ssh git setup
EOF
}

remote_ssh_cmd_setup_main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    remote_ssh_cmd_setup_usage
    return 0
  fi
  (($# == 0)) || {
    remote_ssh_cmd_setup_usage >&2
    return 1
  }

  printf '==> remote-ssh ssh setup\n'
  remote_ssh_cmd_ssh_setup || return $?
  printf '\n==> remote-ssh git setup\n'
  remote_ssh_cmd_git_setup || return $?
  printf '\nremote-ssh setup complete.\n'
}
