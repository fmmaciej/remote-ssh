#!/usr/bin/env bash

write_fake_update_git() {
  local bin_dir="$1"

  cat >"$bin_dir/git" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "-C" ]]; then
  shift 2
fi

case "${1:-}" in
  pull)
    exit 0
    ;;
  rev-parse)
    case "${2:-}" in
      --is-inside-work-tree)
        printf 'true\n'
        exit 0
        ;;
      HEAD)
        printf '%s\n' "${FAKE_LOCAL_HEAD:-local-head}"
        exit 0
        ;;
      --abbrev-ref)
        if [[ "${FAKE_NO_UPSTREAM:-0}" == "1" ]]; then
          exit 1
        fi
        printf '%s\n' "${FAKE_UPSTREAM:-origin/main}"
        exit 0
        ;;
    esac
    ;;
  symbolic-ref)
    printf '%s\n' "${FAKE_BRANCH:-main}"
    exit 0
    ;;
  ls-remote)
    if [[ "${FAKE_LS_REMOTE_FAIL:-0}" == "1" ]]; then
      printf 'network down\n' >&2
      exit 128
    fi
    printf '%s\trefs/heads/main\n' "${FAKE_REMOTE_HEAD:-${FAKE_LOCAL_HEAD:-local-head}}"
    exit 0
    ;;
esac

printf 'unexpected git args: %s\n' "$*" >&2
exit 99
EOF

  chmod +x "$bin_dir/git"
}

test_remote_ssh_update_check_reports_current() {
  log "remote-ssh update check reports current checkout"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"
  write_fake_update_git "$tmp/bin"

  got="$(
    FAKE_LOCAL_HEAD="aaaaaaaa" \
      FAKE_REMOTE_HEAD="aaaaaaaa" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" update check
  )"

  assert_contains "update check title" "remote-ssh update check" "$got"
  assert_contains "update check upstream" "upstream: origin/main" "$got"
  assert_contains "update check current" "status:   current" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_update_check_reports_update_available() {
  log "remote-ssh update check reports changed upstream"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"
  write_fake_update_git "$tmp/bin"

  got="$(
    FAKE_LOCAL_HEAD="aaaaaaaa" \
      FAKE_REMOTE_HEAD="bbbbbbbb" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" update check
  )"

  assert_contains "update check available" "status:   update-available" "$got"
  assert_contains "update check next" "next:     remote-ssh update" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_update_check_reports_missing_upstream() {
  log "remote-ssh update check reports missing upstream"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"
  write_fake_update_git "$tmp/bin"

  got="$(
    FAKE_NO_UPSTREAM=1 \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" update check 2>&1
  )" && {
    printf 'Expected remote-ssh update check to fail without upstream\n' >&2
    return 1
  }

  assert_contains "update check missing upstream status" "status:   error" "$got"
  assert_contains "update check missing upstream message" "No upstream branch is configured" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_update_check_writes_cached_message() {
  log "remote-ssh update check writes cache and renders cached notification"

  local tmp got cache
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"
  write_fake_update_git "$tmp/bin"

  REMOTE_SSH_UPDATE_CHECK_STATE_DIR="$tmp/state" \
    FAKE_LOCAL_HEAD="aaaaaaaa" \
    FAKE_REMOTE_HEAD="bbbbbbbb" \
    PATH="$tmp/bin:/usr/bin:/bin" \
    bash "$REPO_DIR/bin/remote-ssh" update check --quiet --write-cache

  cache="$tmp/state/update-check"
  assert_contains "update check cache status" "status=update-available" "$(sed -n '1,20p' "$cache")"

  got="$(
    REMOTE_SSH_UPDATE_CHECK_STATE_DIR="$tmp/state" \
      PATH="$tmp/bin:/usr/bin:/bin" \
      bash "$REPO_DIR/bin/remote-ssh" update check --cached-message
  )"

  assert_eq "update check cached message" "remote-ssh: update available. Run: remote-ssh update" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_update_runs_install_without_tool_arguments() {
  log "remote-ssh update delegates to install without tool arguments"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/repo/.git"
  write_fake_update_git "$tmp/bin"

  got="$(
    PATH="$tmp/bin:/usr/bin:/bin" \
      bash -c '
        set -euo pipefail
        source "$1/tools/lib/env.sh"
        source "$TOOLS_LIB_DIR/commands.lib.sh"
        remote_ssh_cmd_install_main() {
          printf "argc=%s\n" "$#"
          printf "repo=%s\n" "${1:-}"
        }
        remote_ssh_cmd_update_run "$2"
      ' _ "$REPO_DIR" "$tmp/repo"
  )"

  assert_contains "update install argc" "argc=1" "$got"
  assert_contains "update install repo" "repo=$tmp/repo" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_update_check_reports_current
register_test test_remote_ssh_update_check_reports_update_available
register_test test_remote_ssh_update_check_reports_missing_upstream
register_test test_remote_ssh_update_check_writes_cached_message
register_test test_remote_ssh_update_runs_install_without_tool_arguments
