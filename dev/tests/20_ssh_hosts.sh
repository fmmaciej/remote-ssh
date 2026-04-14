#!/usr/bin/env bash

test_ssh_hosts_parser() {
  log "ssh_hosts.py parses includes"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home/.ssh/config.d"
  cat >"$tmp/home/.ssh/config" <<'EOF'
Host direct
  HostName direct.example

Include config.d/*.conf

Host *
  User ignored
EOF
  cat >"$tmp/home/.ssh/config.d/10-lab.conf" <<'EOF'
Host lab-a lab-b
  HostName lab.example

Host *.wildcard
  HostName ignored.example
EOF

  local got expected
  got="$(HOME="$tmp/home" PYTHONDONTWRITEBYTECODE=1 "$REPO_DIR/scripts/ssh_hosts.py")"
  expected=$'direct\nlab-a\nlab-b'

  assert_eq "hosts output" "$expected" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_ssh_hosts_parser
