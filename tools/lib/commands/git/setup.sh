# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_git_setup_usage() {
  local repo_dir config_base user_local user_local_example

  repo_dir="$(remote_ssh_cmd_git_repo_dir)"
  config_base="${repo_dir}/dots/git/config.base"
  user_local="${repo_dir}/dots/git/user.local"
  user_local_example="${repo_dir}/dots/git/user.local.example"

  cat <<EOF
Usage: remote-ssh git setup

Adds remote-ssh Git defaults to the global Git config via:
  include.path = ${config_base}

If ${user_local} does not exist, it is created from:
  ${user_local_example}

In remote-ssh shells, ${user_local} is also used as a session Git identity
override. It does not write to per-repository .git/config files.
EOF
}

remote_ssh_cmd_git_setup() {
  local repo_dir config_base user_local user_local_example

  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    remote_ssh_cmd_git_setup_usage
    return 0
  fi
  (($# == 0)) || {
    remote_ssh_cmd_git_setup_usage >&2
    return 1
  }

  repo_dir="$(remote_ssh_cmd_git_repo_dir)"
  config_base="${repo_dir}/dots/git/config.base"
  user_local="${repo_dir}/dots/git/user.local"
  user_local_example="${repo_dir}/dots/git/user.local.example"

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required for remote-ssh git setup.\n' >&2
    return 1
  }

  [[ -r "$config_base" ]] || {
    printf '[ERROR] Missing config base: %s\n' "$config_base" >&2
    return 1
  }

  if [[ ! -e "$user_local" && -r "$user_local_example" ]]; then
    cp "$user_local_example" "$user_local"
    printf '[INFO] Created %s from example.\n' "$user_local" >&2
  fi

  if git config --global --get-all include.path 2>/dev/null | grep -Fxq "$config_base"; then
    printf '[INFO] Git include already present: %s\n' "$config_base" >&2
  else
    git config --global --add include.path "$config_base"
    printf '[INFO] Added Git include: %s\n' "$config_base" >&2
  fi

  printf 'remote-ssh git config is active.\n'
  printf 'Base config: %s\n' "$config_base"
  printf 'User overrides: %s\n' "$user_local"
  printf 'Session identity: enabled in remote-ssh shells when user overrides are set.\n'
  printf 'For SSH aliases, run: remote-ssh ssh setup\n'
}
