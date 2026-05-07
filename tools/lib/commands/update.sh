# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_update_main() {
  local repo_dir="$1"
  shift

  (($# == 0)) || {
    remote_ssh_usage >&2
    return 1
  }

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required for remote-ssh update.\n' >&2
    return 127
  }

  [[ -d "$repo_dir/.git" ]] || {
    printf '[ERROR] %s is not a Git checkout.\n' "$repo_dir" >&2
    return 1
  }

  git -C "$repo_dir" pull --ff-only
  remote_ssh_cmd_install_main "$repo_dir"
}
