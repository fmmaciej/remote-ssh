# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_ssh_setup_usage() {
  local ssh_config_local

  ssh_config_local="$(remote_ssh_cmd_ssh_config_local)"

  cat <<EOF
Usage: remote-ssh ssh setup

Creates account-specific SSH aliases from:
  $(remote_ssh_cmd_ssh_config_example)

Then includes them from:
  ${HOME}/.ssh/config

Include line:
  Include ${ssh_config_local}
EOF
}

remote_ssh_cmd_ssh_setup() {
  local ssh_config_local ssh_config_example ssh_config_dir
  local home_ssh_dir home_ssh_config include_line tmp_ssh_config

  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    remote_ssh_cmd_ssh_setup_usage
    return 0
  fi
  (($# == 0)) || {
    remote_ssh_cmd_ssh_setup_usage >&2
    return 1
  }

  ssh_config_local="$(remote_ssh_cmd_ssh_config_local)"
  ssh_config_example="$(remote_ssh_cmd_ssh_config_example)"
  ssh_config_dir="${ssh_config_local%/*}"
  home_ssh_dir="${HOME}/.ssh"
  home_ssh_config="${home_ssh_dir}/config"

  if [[ ! -e "$ssh_config_local" ]]; then
    [[ -r "$ssh_config_example" ]] || {
      printf '[ERROR] Missing SSH config example: %s\n' "$ssh_config_example" >&2
      return 1
    }
    mkdir -p "$ssh_config_dir"
    cp "$ssh_config_example" "$ssh_config_local"
    printf '[INFO] Created %s from example.\n' "$ssh_config_local" >&2
  fi

  [[ -r "$ssh_config_local" ]] || {
    printf '[ERROR] SSH config is not readable: %s\n' "$ssh_config_local" >&2
    return 1
  }

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

  printf 'remote-ssh ssh config is active.\n'
  printf 'SSH aliases: %s\n' "$ssh_config_local"
  printf 'Home config: %s\n' "$home_ssh_config"
}
