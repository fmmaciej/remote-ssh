#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_remote_ssh_git_identity_reports_git_and_ssh_state() {
  log "remote-ssh-git-identity reports Git and SSH state"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/repo"

  cat >"$tmp/bin/ssh-add" <<'EOF'
#!/usr/bin/env bash
printf '256 SHA256:testkey forwarded-key (ED25519)\n'
EOF
  chmod +x "$tmp/bin/ssh-add"

  cat >"$tmp/bin/ssh" <<'EOF'
#!/usr/bin/env bash
printf 'Hi test-user! You'\''ve successfully authenticated, but GitHub does not provide shell access.\n' >&2
exit 1
EOF
  chmod +x "$tmp/bin/ssh"

  local got
  got="$(
    export HOME="$tmp/home"
    export PATH="$tmp/bin:$PATH"
    export SSH_AUTH_SOCK="$tmp/agent.sock"
    mkdir -p "$HOME"

    cd "$tmp/repo" || exit
    git init -q
    git config user.name "Test User"
    git config user.email "test@example.com"
    git config user.useConfigOnly true
    git remote add origin git@github.com-myuser:fmmaciej/remote-ssh.git

    "$REPO_DIR/bin/remote-ssh-git-identity"
  )"

  grep -q '^remote-ssh git identity$' <<<"$got"
  grep -q '^  user.name:         Test User ' <<<"$got"
  grep -q '^  user.email:        test@example.com ' <<<"$got"
  grep -q '^  user.useConfigOnly: true ' <<<"$got"
  grep -q '^  origin:            git@github.com-myuser:fmmaciej/remote-ssh.git$' <<<"$got"
  grep -q '^  ssh host:          github.com-myuser$' <<<"$got"
  grep -q "^  SSH_AUTH_SOCK:     $tmp/agent.sock$" <<<"$got"
  grep -q '^  key:              256 SHA256:testkey forwarded-key (ED25519)$' <<<"$got"
  grep -q '^  command:           ssh -T git@github.com-myuser$' <<<"$got"
  grep -q '^  status:            ok$' <<<"$got"
  grep -q '^  output:           Hi test-user!' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_identity_accepts_explicit_host_without_remote() {
  log "remote-ssh-git-identity accepts explicit host without origin"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/repo"

  cat >"$tmp/bin/ssh-add" <<'EOF'
#!/usr/bin/env bash
printf 'Could not open a connection to your authentication agent.\n' >&2
exit 2
EOF
  chmod +x "$tmp/bin/ssh-add"

  cat >"$tmp/bin/ssh" <<'EOF'
#!/usr/bin/env bash
printf 'Permission denied (publickey).\n' >&2
exit 255
EOF
  chmod +x "$tmp/bin/ssh"

  local got
  got="$(
    export HOME="$tmp/home"
    export PATH="$tmp/bin:$PATH"
    unset SSH_AUTH_SOCK
    mkdir -p "$HOME"

    cd "$tmp/repo" || exit
    git init -q

    "$REPO_DIR/bin/remote-ssh-git-identity" github.com-myuser
  )"

  grep -q '^  origin:            \[missing\]$' <<<"$got"
  grep -q '^  ssh host:          github.com-myuser$' <<<"$got"
  grep -q '^  SSH_AUTH_SOCK:     \[missing\]$' <<<"$got"
  grep -q '^  keys:              Could not open a connection to your authentication agent\.$' <<<"$got"
  grep -q '^  status:            exit 255$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_git_identity_reports_git_and_ssh_state
register_test test_remote_ssh_git_identity_accepts_explicit_host_without_remote
