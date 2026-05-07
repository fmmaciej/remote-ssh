#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_remote_ssh_git_identity_reports_git_and_ssh_state() {
  log "remote-ssh git status reports Git and SSH state"

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

    "$REPO_DIR/bin/remote-ssh" git status
  )"

  grep -q '^remote-ssh git status$' <<<"$got"
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
  grep -q '^Diagnosis$' <<<"$got"
  grep -q '^  ssh agent:[[:space:]]*ok$' <<<"$got"
  grep -q '^  ssh auth:[[:space:]]*ok$' <<<"$got"
  grep -q '^Next steps$' <<<"$got"
  grep -q '^  \[none\]$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_identity_accepts_explicit_host_without_remote() {
  log "remote-ssh git status accepts explicit host without origin"

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

    "$REPO_DIR/bin/remote-ssh" git status github.com-myuser
  )"

  grep -q '^  origin:            \[missing\]$' <<<"$got"
  grep -q '^  ssh host:          github.com-myuser$' <<<"$got"
  grep -q '^  SSH_AUTH_SOCK:     \[missing\]$' <<<"$got"
  grep -q '^  keys:              Could not open a connection to your authentication agent\.$' <<<"$got"
  grep -q '^  status:            exit 255$' <<<"$got"
  grep -q '^  ssh agent:[[:space:]]*missing-sock$' <<<"$got"
  grep -q '^  ssh auth:[[:space:]]*denied-publickey$' <<<"$got"
  grep -q '^  - Start or forward an SSH agent, then reopen this shell\.$' <<<"$got"
  grep -q '^  - Fix the SSH agent first, then retry remote-ssh git status github.com-myuser\.$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_identity_reports_stale_agent_socket() {
  log "remote-ssh git status reports stale SSH agent socket"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/repo"

  cat >"$tmp/bin/ssh-add" <<'EOF'
#!/usr/bin/env bash
printf 'Error connecting to agent: No such file or directory\n' >&2
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
    export SSH_AUTH_SOCK="$tmp/missing-agent.sock"
    mkdir -p "$HOME"

    cd "$tmp/repo" || exit
    git init -q

    "$REPO_DIR/bin/remote-ssh" git status github.com-myuser
  )"

  grep -q "^  SSH_AUTH_SOCK:     $tmp/missing-agent.sock$" <<<"$got"
  grep -q '^  keys:              Error connecting to agent: No such file or directory$' <<<"$got"
  grep -q '^  ssh agent:[[:space:]]*stale-sock$' <<<"$got"
  grep -q '^  ssh auth:[[:space:]]*denied-publickey$' <<<"$got"
  grep -q '^  - SSH_AUTH_SOCK points to a dead socket; reconnect or refresh agent forwarding\.$' <<<"$got"
  grep -q '^  - Fix the SSH agent first, then retry remote-ssh git status github.com-myuser\.$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_identity_reports_agent_without_keys() {
  log "remote-ssh git status reports SSH agent without keys"

  require_cmd git

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/repo"

  cat >"$tmp/bin/ssh-add" <<'EOF'
#!/usr/bin/env bash
printf 'The agent has no identities.\n' >&2
exit 1
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
    export SSH_AUTH_SOCK="$tmp/agent.sock"
    mkdir -p "$HOME"

    cd "$tmp/repo" || exit
    git init -q

    "$REPO_DIR/bin/remote-ssh" git status github.com-myuser
  )"

  grep -q '^  keys:              The agent has no identities\.$' <<<"$got"
  grep -q '^  ssh agent:[[:space:]]*no-keys$' <<<"$got"
  grep -q '^  ssh auth:[[:space:]]*denied-publickey$' <<<"$got"
  grep -q '^  - Load a key with ssh-add, or check that your forwarded agent has identities\.$' <<<"$got"
  grep -q '^  - Fix the SSH agent first, then retry remote-ssh git status github.com-myuser\.$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_identity_reports_publickey_denied_with_keys() {
  log "remote-ssh git status reports publickey denial with loaded keys"

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
printf 'Permission denied (publickey).\n' >&2
exit 255
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

    "$REPO_DIR/bin/remote-ssh" git status github.com-myuser
  )"

  grep -q '^  key:              256 SHA256:testkey forwarded-key (ED25519)$' <<<"$got"
  grep -q '^  ssh agent:[[:space:]]*ok$' <<<"$got"
  grep -q '^  ssh auth:[[:space:]]*denied-publickey$' <<<"$got"
  grep -q '^  - Check the SSH alias, IdentityFile, and whether the public key is registered with your Git provider\.$' <<<"$got"
  grep -q '^  - Run remote-ssh git setup if the Git SSH aliases are not configured yet\.$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_remote_ssh_git_identity_reports_session_override() {
  log "remote-ssh git status reports session override"

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
    export REMOTE_SSH_GIT_SESSION_IDENTITY=1
    export GIT_CONFIG_COUNT=3
    export GIT_CONFIG_KEY_0=user.name
    export GIT_CONFIG_VALUE_0="Session User"
    export GIT_CONFIG_KEY_1=user.email
    export GIT_CONFIG_VALUE_1=session@example.com
    export GIT_CONFIG_KEY_2=user.useConfigOnly
    export GIT_CONFIG_VALUE_2=true
    mkdir -p "$HOME"

    cd "$tmp/repo" || exit
    git init -q
    git config --local user.name "Repo User"
    git config --local user.email "repo@example.com"

    "$REPO_DIR/bin/remote-ssh" git status github.com-myuser
  )"

  grep -q '^  user.name:         Session User ' <<<"$got"
  grep -q '^  user.email:        session@example.com ' <<<"$got"
  grep -q '^Git session override$' <<<"$got"
  grep -q '^  enabled:           1$' <<<"$got"
  grep -q '^  GIT_CONFIG_COUNT:  3$' <<<"$got"
  grep -q '^  session name:      Session User$' <<<"$got"
  grep -q '^  session email:     session@example.com$' <<<"$got"
  grep -q '^  session useConfigOnly: true$' <<<"$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_remote_ssh_git_identity_reports_git_and_ssh_state
register_test test_remote_ssh_git_identity_accepts_explicit_host_without_remote
register_test test_remote_ssh_git_identity_reports_stale_agent_socket
register_test test_remote_ssh_git_identity_reports_agent_without_keys
register_test test_remote_ssh_git_identity_reports_publickey_denied_with_keys
register_test test_remote_ssh_git_identity_reports_session_override
