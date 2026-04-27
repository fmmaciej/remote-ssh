#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_git_session_identity_overrides_repo_local_config() {
  log "git session identity overrides repo local config"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/dots/git" "$tmp/repo"
  cat >"$tmp/dots/git/user.local" <<'EOF'
[user]
    name = Session User
    email = session@example.com
EOF

  local got
  got="$(
    unset GIT_CONFIG_COUNT
    unset REMOTE_SSH_GIT_SESSION_IDENTITY
    export REMOTE_DOTS_DIR="$tmp/dots"

    cd "$tmp/repo" || exit
    git init -q
    git config --local user.name "Repo User"
    git config --local user.email "repo@example.com"

    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/guards.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/helpers.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/shell/rc.d/07-git-session-identity.sh"

    printf 'name=%s\n' "$(git config user.name)"
    printf 'email=%s\n' "$(git config user.email)"
    printf 'useConfigOnly=%s\n' "$(git config user.useConfigOnly)"
    printf 'local_name=%s\n' "$(git config --local user.name)"
    printf 'local_email=%s\n' "$(git config --local user.email)"
    printf 'enabled=%s\n' "$REMOTE_SSH_GIT_SESSION_IDENTITY"
    printf 'count=%s\n' "$GIT_CONFIG_COUNT"
  )"

  assert_eq "git session identity" "name=Session User
email=session@example.com
useConfigOnly=true
local_name=Repo User
local_email=repo@example.com
enabled=1
count=3" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_git_session_identity_can_be_disabled() {
  log "git session identity can be disabled"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/dots/git" "$tmp/repo"
  cat >"$tmp/dots/git/user.local" <<'EOF'
[user]
    name = Session User
    email = session@example.com
EOF

  local got
  got="$(
    unset GIT_CONFIG_COUNT
    unset REMOTE_SSH_GIT_SESSION_IDENTITY
    export REMOTE_DOTS_DIR="$tmp/dots"
    export REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY=0

    cd "$tmp/repo" || exit
    git init -q
    git config --local user.name "Repo User"
    git config --local user.email "repo@example.com"

    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/guards.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/lib/helpers.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/shell/rc.d/07-git-session-identity.sh"

    printf 'name=%s\n' "$(git config user.name)"
    printf 'email=%s\n' "$(git config user.email)"
    printf 'enabled=%s\n' "${REMOTE_SSH_GIT_SESSION_IDENTITY:-0}"
    printf 'count=%s\n' "${GIT_CONFIG_COUNT:-0}"
  )"

  assert_eq "disabled git session identity" "name=Repo User
email=repo@example.com
enabled=0
count=0" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_git_session_identity_overrides_repo_local_config
register_test test_git_session_identity_can_be_disabled
