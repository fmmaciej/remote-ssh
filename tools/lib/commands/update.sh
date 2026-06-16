# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_update_usage() {
  cat <<'EOF'
Usage:
  remote-ssh update
  remote-ssh update check [--quiet] [--write-cache]

Commands:
  update  Refresh this checkout from upstream, then run install
  check   Check whether the configured upstream branch has changed
EOF
}

remote_ssh_cmd_update_refresh_checkout() {
  local repo_dir="$1"
  local upstream remote remote_branch untracked

  if ! git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf '[ERROR] %s is not a valid Git work tree.\n' "$repo_dir" >&2
    return 1
  fi

  if ! upstream="$(git -C "$repo_dir" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"; then
    printf '[ERROR] No upstream branch is configured for %s.\n' "$repo_dir" >&2
    return 1
  fi

  if [[ "$upstream" != */* ]]; then
    printf '[ERROR] Unsupported upstream name: %s\n' "$upstream" >&2
    return 1
  fi

  remote="${upstream%%/*}"
  remote_branch="${upstream#*/}"

  printf '[*] Fetching %s/%s\n' "$remote" "$remote_branch"
  git -C "$repo_dir" fetch "$remote" "$remote_branch"

  printf '[*] Resetting tracked files to %s\n' "$upstream"
  git -C "$repo_dir" reset --hard "$upstream"

  untracked="$(git -C "$repo_dir" ls-files --others --exclude-standard 2>/dev/null || true)"
  if [[ -n "$untracked" ]]; then
    printf '[WARN] Untracked files were left in place:\n'
    printf '%s\n' "$untracked" | sed 's/^/  /'
  fi
}

remote_ssh_cmd_update_run() {
  local repo_dir="$1"
  shift

  (($# == 0)) || {
    remote_ssh_cmd_update_usage >&2
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

  remote_ssh_cmd_update_refresh_checkout "$repo_dir" || return $?
  remote_ssh_cmd_update_check_cache_mark_current "$repo_dir" || true
  remote_ssh_cmd_install_main "$repo_dir"
}

# shellcheck source=/dev/null
. "$TOOLS_COMMANDS_DIR/update/check.sh"

remote_ssh_cmd_update_main() {
  local repo_dir="$1"
  shift

  case "${1:-}" in
    '')
      remote_ssh_cmd_update_run "$repo_dir"
      ;;
    check)
      shift
      remote_ssh_cmd_update_check_main "$repo_dir" "$@"
      ;;
    -h | --help)
      remote_ssh_cmd_update_usage
      ;;
    *)
      printf 'Unknown remote-ssh update command: %s\n' "$1" >&2
      remote_ssh_cmd_update_usage >&2
      return 1
      ;;
  esac
}
