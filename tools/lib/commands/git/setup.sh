# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_git_setup_usage() {
  local repo_dir config_base user_local user_local_example ssh_config_local

  repo_dir="$(remote_ssh_cmd_git_repo_dir)"
  config_base="${repo_dir}/dots/git/config.base"
  user_local="${repo_dir}/dots/git/user.local"
  user_local_example="${repo_dir}/dots/git/user.local.example"
  ssh_config_local="${repo_dir}/dots/ssh/config.local"

  cat <<EOF
Usage: remote-ssh git setup

Adds remote-ssh Git defaults to the global Git config via:
  include.path = ${config_base}

If ${user_local} does not exist, it is created from:
  ${user_local_example}

Also prepares SSH config includes for account-specific Git aliases:
  Include ${ssh_config_local}

In remote-ssh shells, ${user_local} is also used as a session Git identity
override. It does not write to per-repository .git/config files.
EOF
}

remote_ssh_cmd_git_setup() {
  local repo_dir config_base user_local user_local_example
  local ssh_config_dir ssh_config_local ssh_config_example
  local home_ssh_dir home_ssh_config include_line tmp_ssh_config

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
  ssh_config_dir="${repo_dir}/dots/ssh"
  ssh_config_local="${ssh_config_dir}/config.local"
  ssh_config_example="${ssh_config_dir}/config.example"
  home_ssh_dir="${HOME}/.ssh"
  home_ssh_config="${home_ssh_dir}/config"

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

  if [[ ! -e "$ssh_config_local" && -r "$ssh_config_example" ]]; then
    mkdir -p "$ssh_config_dir"
    cp "$ssh_config_example" "$ssh_config_local"
    printf '[INFO] Created %s from example.\n' "$ssh_config_local" >&2
  fi

  if git config --global --get-all include.path 2>/dev/null | grep -Fxq "$config_base"; then
    printf '[INFO] Git include already present: %s\n' "$config_base" >&2
  else
    git config --global --add include.path "$config_base"
    printf '[INFO] Added Git include: %s\n' "$config_base" >&2
  fi

  if [[ -r "$ssh_config_local" ]]; then
    mkdir -p "$home_ssh_dir"
    chmod 700 "$home_ssh_dir" 2>/dev/null || true
    touch "$home_ssh_config"
    chmod 600 "$home_ssh_config" 2>/dev/null || true

    include_line="Include ${ssh_config_local}"
    if grep -Fxq "$include_line" "$home_ssh_config"; then
      printf '[INFO] SSH include already present: %s\n' "$ssh_config_local" >&2
    else
      tmp_ssh_config="$(mktemp "${home_ssh_config}.remote-ssh.XXXXXX")"
      printf '%s\n' "$include_line" >"$tmp_ssh_config"
      if [[ -s "$home_ssh_config" ]]; then
        printf '\n' >>"$tmp_ssh_config"
        cat "$home_ssh_config" >>"$tmp_ssh_config"
      fi
      cat "$tmp_ssh_config" >"$home_ssh_config"
      rm -f "$tmp_ssh_config"
      chmod 600 "$home_ssh_config" 2>/dev/null || true
      printf '[INFO] Added SSH include: %s\n' "$ssh_config_local" >&2
    fi
  fi

  printf 'remote-ssh git config is active.\n'
  printf 'Base config: %s\n' "$config_base"
  printf 'User overrides: %s\n' "$user_local"
  printf 'Session identity: enabled in remote-ssh shells when user overrides are set.\n'
  printf 'SSH aliases: %s\n' "$ssh_config_local"
  printf 'After editing SSH aliases, use remotes like:\n'
  printf '  git remote set-url origin git@github.com-myuser:OWNER/REPO.git\n'
}
