#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_sshf_default_flow() {
  log "sshf uses repo ssh_hosts.py by default"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/home/.ssh"
  cat >"$tmp/home/.ssh/config" <<'EOF'
Host devbox
  HostName devbox.example
EOF

  cat >"$tmp/bin/fzf" <<'EOF'
#!/usr/bin/env bash
sed -n '1p'
EOF
  chmod +x "$tmp/bin/fzf"

  cat >"$tmp/bin/ssh" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >"${SSH_STUB_OUT:?}"
EOF
  chmod +x "$tmp/bin/ssh"

  local out="$tmp/ssh.out"
  (
    export HOME="$tmp/home"
    export PATH="$tmp/bin:$PATH"
    export SSH_STUB_OUT="$out"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/shell/env.sh"
    # shellcheck source=/dev/null
    . "$REPO_DIR/shell/rc.d/30-sshf.sh"
    sshf -- true
  )

  assert_eq "ssh invocation" "devbox -- true" "$(cat "$out")"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_sshf_default_flow
