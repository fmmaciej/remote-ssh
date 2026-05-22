# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_guide_usage() {
  cat <<'EOF' >&2
Usage: remote-ssh guide [all|commands|aliases|functions|paths|git|tools|scripts|starship|post-install]
EOF
}

remote_ssh_cmd_guide_repo_dir() {
  cd "${REMOTE_ENV_DIR:-$REPO_DIR}" && pwd
}

remote_ssh_cmd_guide_dots_dir() {
  printf '%s\n' "${REMOTE_DOTS_DIR:-$(remote_ssh_cmd_guide_repo_dir)/dots}"
}

remote_ssh_cmd_guide_shell_dir() {
  printf '%s\n' "${REMOTE_SHELL_DIR:-$(remote_ssh_cmd_guide_repo_dir)/shell}"
}

remote_ssh_cmd_guide_bin_dir() {
  printf '%s\n' "${REMOTE_BIN_DIR:-$(remote_ssh_cmd_guide_repo_dir)/bin}"
}

remote_ssh_cmd_guide_cheats_dir() {
  printf '%s\n' "$(remote_ssh_cmd_guide_dots_dir)/navi/cheats"
}

remote_ssh_cmd_guide_atuin_marker() {
  printf '%s\n' "${XDG_STATE_HOME:-$HOME/.local/state}/remote-ssh/atuin-import-auto.done"
}

remote_ssh_cmd_guide_starship_config() {
  printf '%s\n' "${STARSHIP_CONFIG:-$(remote_ssh_cmd_guide_dots_dir)/starship.toml}"
}

remote_ssh_cmd_guide_print_prefixed_lines() {
  local text="$1"

  if [[ -z "$text" ]]; then
    printf '  [none]\n'
    return 0
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] && printf '  %s\n' "$line"
  done <<<"$text"
}
