# shellcheck shell=bash

ensure_this_file_sourced

# shellcheck source=/dev/null
. "$SHELL_DIR/update-check.lib.sh"

remote_ssh_cmd_update_check_usage() {
  cat <<'EOF'
Usage:
  remote-ssh update check [--quiet] [--write-cache]
  remote-ssh update check --cached-message

Checks whether the configured upstream branch points at a different commit.
This does not fetch, pull, or modify the working tree.
EOF
}

remote_ssh_cmd_update_check_cache_write() {
  local file tmp

  file="$(remote_ssh_update_check_cache_file)" || return 0
  mkdir -p "${file%/*}" || return 0

  tmp="${file}.$$"
  {
    printf 'checked_at=%s\n' "${REMOTE_SSH_UPDATE_CHECK_CHECKED_AT:-}"
    printf 'checked_at_text=%s\n' "${REMOTE_SSH_UPDATE_CHECK_CHECKED_AT_TEXT:-unknown}"
    printf 'status=%s\n' "${REMOTE_SSH_UPDATE_CHECK_STATUS:-error}"
    printf 'repo=%s\n' "${REMOTE_SSH_UPDATE_CHECK_REPO:-}"
    printf 'branch=%s\n' "${REMOTE_SSH_UPDATE_CHECK_BRANCH:-}"
    printf 'upstream=%s\n' "${REMOTE_SSH_UPDATE_CHECK_UPSTREAM:-}"
    printf 'local_head=%s\n' "${REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD:-}"
    printf 'remote_head=%s\n' "${REMOTE_SSH_UPDATE_CHECK_REMOTE_HEAD:-}"
    printf 'message=%s\n' "${REMOTE_SSH_UPDATE_CHECK_MESSAGE:-}"
  } >"$tmp" && mv "$tmp" "$file"
}

remote_ssh_cmd_update_check_set_error() {
  REMOTE_SSH_UPDATE_CHECK_STATUS="error"
  REMOTE_SSH_UPDATE_CHECK_MESSAGE="$1"
  return 1
}

remote_ssh_cmd_update_check_collect() {
  local repo_dir="$1"
  local local_head branch upstream remote remote_branch remote_line remote_head

  REMOTE_SSH_UPDATE_CHECK_REPO="$repo_dir"
  REMOTE_SSH_UPDATE_CHECK_CHECKED_AT="$(date +%s 2>/dev/null || printf '0')"
  REMOTE_SSH_UPDATE_CHECK_CHECKED_AT_TEXT="$(remote_ssh_update_check_checked_at_text)"
  REMOTE_SSH_UPDATE_CHECK_STATUS="error"
  REMOTE_SSH_UPDATE_CHECK_BRANCH=""
  REMOTE_SSH_UPDATE_CHECK_UPSTREAM=""
  REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD=""
  REMOTE_SSH_UPDATE_CHECK_REMOTE_HEAD=""
  REMOTE_SSH_UPDATE_CHECK_MESSAGE=""

  command -v git >/dev/null 2>&1 ||
    remote_ssh_cmd_update_check_set_error "git is required for remote-ssh update check." || return 1

  [[ -d "$repo_dir/.git" ]] ||
    remote_ssh_cmd_update_check_set_error "$repo_dir is not a Git checkout." || return 1

  git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    remote_ssh_cmd_update_check_set_error "$repo_dir is not a valid Git work tree." || return 1

  if ! local_head="$(git -C "$repo_dir" rev-parse HEAD 2>/dev/null)"; then
    remote_ssh_cmd_update_check_set_error "Could not resolve local HEAD."
    return 1
  fi

  branch="$(git -C "$repo_dir" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"

  if ! upstream="$(git -C "$repo_dir" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"; then
    remote_ssh_cmd_update_check_set_error "No upstream branch is configured for ${branch:-this checkout}."
    REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD="$local_head"
    REMOTE_SSH_UPDATE_CHECK_BRANCH="$branch"
    return 1
  fi

  if [[ "$upstream" != */* ]]; then
    remote_ssh_cmd_update_check_set_error "Unsupported upstream name: $upstream"
    REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD="$local_head"
    REMOTE_SSH_UPDATE_CHECK_BRANCH="$branch"
    REMOTE_SSH_UPDATE_CHECK_UPSTREAM="$upstream"
    return 1
  fi

  remote="${upstream%%/*}"
  remote_branch="${upstream#*/}"

  if ! remote_line="$(git -C "$repo_dir" ls-remote "$remote" "refs/heads/$remote_branch" 2>&1)"; then
    remote_ssh_cmd_update_check_set_error "Could not check upstream: $remote_line"
    REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD="$local_head"
    REMOTE_SSH_UPDATE_CHECK_BRANCH="$branch"
    REMOTE_SSH_UPDATE_CHECK_UPSTREAM="$upstream"
    return 1
  fi

  remote_line="${remote_line%%$'\n'*}"
  remote_head="${remote_line%%[[:space:]]*}"
  if [[ -z "$remote_head" || "$remote_head" == "$remote_line" ]]; then
    remote_ssh_cmd_update_check_set_error "Could not resolve remote branch refs/heads/$remote_branch."
    REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD="$local_head"
    REMOTE_SSH_UPDATE_CHECK_BRANCH="$branch"
    REMOTE_SSH_UPDATE_CHECK_UPSTREAM="$upstream"
    return 1
  fi

  REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD="$local_head"
  REMOTE_SSH_UPDATE_CHECK_REMOTE_HEAD="$remote_head"
  REMOTE_SSH_UPDATE_CHECK_BRANCH="$branch"
  REMOTE_SSH_UPDATE_CHECK_UPSTREAM="$upstream"

  if [[ "$local_head" == "$remote_head" ]]; then
    REMOTE_SSH_UPDATE_CHECK_STATUS="current"
    REMOTE_SSH_UPDATE_CHECK_MESSAGE="remote-ssh is current."
  else
    REMOTE_SSH_UPDATE_CHECK_STATUS="update-available"
    REMOTE_SSH_UPDATE_CHECK_MESSAGE="remote-ssh upstream has changed."
  fi
}

remote_ssh_cmd_update_check_cache_mark_current() {
  local repo_dir="$1"
  local local_head branch upstream

  REMOTE_SSH_UPDATE_CHECK_REPO="$repo_dir"
  REMOTE_SSH_UPDATE_CHECK_CHECKED_AT="$(date +%s 2>/dev/null || printf '0')"
  REMOTE_SSH_UPDATE_CHECK_CHECKED_AT_TEXT="$(remote_ssh_update_check_checked_at_text)"
  REMOTE_SSH_UPDATE_CHECK_STATUS="current"
  REMOTE_SSH_UPDATE_CHECK_BRANCH=""
  REMOTE_SSH_UPDATE_CHECK_UPSTREAM=""
  REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD=""
  REMOTE_SSH_UPDATE_CHECK_REMOTE_HEAD=""
  REMOTE_SSH_UPDATE_CHECK_MESSAGE="remote-ssh is current."

  local_head="$(git -C "$repo_dir" rev-parse HEAD 2>/dev/null || true)"
  branch="$(git -C "$repo_dir" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  upstream="$(git -C "$repo_dir" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"

  REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD="$local_head"
  REMOTE_SSH_UPDATE_CHECK_REMOTE_HEAD="$local_head"
  REMOTE_SSH_UPDATE_CHECK_BRANCH="$branch"
  REMOTE_SSH_UPDATE_CHECK_UPSTREAM="$upstream"

  remote_ssh_cmd_update_check_cache_write
}

remote_ssh_cmd_update_check_render() {
  printf 'remote-ssh update check\n\n'
  printf 'Repository\n'
  printf '  path:     %s\n' "${REMOTE_SSH_UPDATE_CHECK_REPO:-}"
  printf '  branch:   %s\n' "${REMOTE_SSH_UPDATE_CHECK_BRANCH:-[detached]}"
  printf '  upstream: %s\n' "${REMOTE_SSH_UPDATE_CHECK_UPSTREAM:-[missing]}"
  printf '\nCommits\n'
  printf '  local:    %s\n' "${REMOTE_SSH_UPDATE_CHECK_LOCAL_HEAD:-[unknown]}"
  printf '  remote:   %s\n' "${REMOTE_SSH_UPDATE_CHECK_REMOTE_HEAD:-[unknown]}"
  printf '\nStatus\n'
  printf '  status:   %s\n' "${REMOTE_SSH_UPDATE_CHECK_STATUS:-error}"
  printf '  message:  %s\n' "${REMOTE_SSH_UPDATE_CHECK_MESSAGE:-unknown}"

  if [[ "${REMOTE_SSH_UPDATE_CHECK_STATUS:-}" == "update-available" ]]; then
    printf '  next:     remote-ssh update\n'
  fi
}

remote_ssh_cmd_update_check_cached_message() {
  local file status

  file="$(remote_ssh_update_check_cache_file)" || return 0
  status="$(remote_ssh_update_check_cache_get "$file" status 2>/dev/null || true)"

  if [[ "$status" == "update-available" ]]; then
    printf 'remote-ssh: update available. Run: remote-ssh update\n'
  fi
}

remote_ssh_cmd_update_check_main() {
  local repo_dir="$1"
  shift

  local quiet=0 write_cache=0 cached_message=0 arg status restore_errexit=0

  while (($# > 0)); do
    arg="$1"
    case "$arg" in
      --quiet)
        quiet=1
        shift
        ;;
      --write-cache)
        write_cache=1
        shift
        ;;
      --cached-message)
        cached_message=1
        shift
        ;;
      -h | --help)
        remote_ssh_cmd_update_check_usage
        return 0
        ;;
      *)
        printf 'Unknown remote-ssh update check option: %s\n' "$arg" >&2
        remote_ssh_cmd_update_check_usage >&2
        return 2
        ;;
    esac
  done

  if ((cached_message == 1)); then
    remote_ssh_cmd_update_check_cached_message
    return 0
  fi

  case $- in
    *e*) restore_errexit=1 ;;
  esac

  set +e
  remote_ssh_cmd_update_check_collect "$repo_dir"
  status=$?
  if ((restore_errexit == 1)); then
    set -e
  fi

  if ((write_cache == 1)); then
    remote_ssh_cmd_update_check_cache_write
  fi

  if ((quiet == 0)); then
    remote_ssh_cmd_update_check_render
  fi

  return "$status"
}
