#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_remote_ssh_git_setup_adds_include_once() {
  log "remote-ssh git setup adds include path once"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local repo_copy="$tmp/repo"
  mkdir -p "$repo_copy"
  cp -R "$REPO_DIR/." "$repo_copy"

  local got
  got="$(
    export HOME="$tmp/home"
    mkdir -p "$HOME"

    bash "$repo_copy/bin/remote-ssh" git setup >/dev/null
    bash "$repo_copy/bin/remote-ssh" git setup >/dev/null

    git config --global --get-all include.path
  )"

  assert_eq "git include path" "$repo_copy/dots/git/config.base" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_setup_creates_user_local_example() {
  log "remote-ssh git setup creates local examples"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local repo_copy="$tmp/repo"
  mkdir -p "$repo_copy"
  cp -R "$REPO_DIR/." "$repo_copy"
  rm -f "$repo_copy/dots/git/user.local"

  local got
  got="$(
    export HOME="$tmp/home"
    mkdir -p "$HOME"

    bash "$repo_copy/bin/remote-ssh" git setup >/dev/null
    cat "$repo_copy/dots/git/user.local"
    printf '%s\n' '--- ssh ---'
    cat "$repo_copy/dots/ssh/config.local"
  )"

  grep -q '^\[user\]$' <<<"$got"
  grep -q '^    name = Your Name$' <<<"$got"
  grep -q '^    email = your.email@example.com$' <<<"$got"
  grep -q '^Host github.com-myuser$' <<<"$got"
  grep -q '^  IdentitiesOnly no$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_setup_adds_ssh_include_once() {
  log "remote-ssh git setup adds SSH include once"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local repo_copy="$tmp/repo"
  mkdir -p "$repo_copy"
  cp -R "$REPO_DIR/." "$repo_copy"

  local got
  got="$(
    export HOME="$tmp/home"
    mkdir -p "$HOME/.ssh"
    cat >"$HOME/.ssh/config" <<'EOF'
Host existing
  HostName example.com
EOF

    bash "$repo_copy/bin/remote-ssh" git setup >/dev/null
    bash "$repo_copy/bin/remote-ssh" git setup >/dev/null

    cat "$HOME/.ssh/config"
    printf 'mode:%s\n' "$(stat -f '%Lp' "$HOME/.ssh/config" 2>/dev/null || stat -c '%a' "$HOME/.ssh/config")"
  )"

  assert_eq "ssh config include" "Include $repo_copy/dots/ssh/config.local

Host existing
  HostName example.com
mode:600" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_setup_exposes_base_defaults_via_include() {
  log "remote-ssh git setup exposes base defaults via include"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  local repo_copy="$tmp/repo"
  mkdir -p "$repo_copy"
  cp -R "$REPO_DIR/." "$repo_copy"

  cat >"$repo_copy/dots/git/user.local" <<'EOF'
[user]
    name = Test User
    email = test@example.com

[core]
    editor = vim
EOF

  local got
  got="$(
    export HOME="$tmp/home"
    mkdir -p "$HOME"

    bash "$repo_copy/bin/remote-ssh" git setup >/dev/null

    printf '%s\n' "$(git config init.defaultBranch)"
    printf '%s\n' "$(git config fetch.prune)"
    printf '%s\n' "$(git config pull.rebase)"
    printf '%s\n' "$(git config rebase.autoStash)"
    printf '%s\n' "$(git config push.autoSetupRemote)"
    printf '%s\n' "$(git config rerere.enabled)"
    printf '%s\n' "$(git config merge.conflictStyle)"
    printf '%s\n' "$(git config diff.algorithm)"
    printf '%s\n' "$(git config help.autoCorrect)"
    printf '%s\n' "$(git config user.useConfigOnly)"
    printf '%s\n' "$(git config user.name)"
    printf '%s\n' "$(git config core.editor)"
  )"

  assert_eq "git included defaults" $'main\ntrue\ntrue\ntrue\ntrue\ntrue\nzdiff3\nhistogram\nprompt\ntrue\nTest User\nvim' "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_git_setup_adds_include_once
register_test test_remote_ssh_git_setup_creates_user_local_example
register_test test_remote_ssh_git_setup_exposes_base_defaults_via_include
register_test test_remote_ssh_git_setup_adds_ssh_include_once
