#!/usr/bin/env bash

test_log_filter_writes_explicit_file() {
  log "log helper writes stdin to explicit file"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin"
  cat >"$tmp/bin/tspin" <<'EOF'
#!/usr/bin/env bash
cat
EOF
  chmod +x "$tmp/bin/tspin"

  local got
  got="$(
    PATH="$tmp/bin:$PATH" REPO_DIR="$REPO_DIR" bash -c '
      . "$REPO_DIR/lib/guards.sh"
      . "$REPO_DIR/lib/helpers.sh"
      . "$REPO_DIR/shell/rc.d/25-log.sh"
      printf "one\ntwo\n" | log "$1"
    ' _ "$tmp/out.log"
  )"

  assert_eq "log filter output" $'one\ntwo' "$got"
  assert_eq "log file" $'one\ntwo' "$(cat "$tmp/out.log")"

  trap - RETURN
  rm -rf "$tmp"
}

test_logrun_writes_default_file_and_preserves_status() {
  log "logrun captures stdout and stderr"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/bin" "$tmp/work"
  cat >"$tmp/bin/tspin" <<'EOF'
#!/usr/bin/env bash
cat
EOF
  cat >"$tmp/bin/failcmd" <<'EOF'
#!/usr/bin/env bash
printf 'out\n'
printf 'err\n' >&2
exit 7
EOF
  chmod +x "$tmp/bin/tspin" "$tmp/bin/failcmd"

  local got status
  set +e
  got="$(
    PATH="$tmp/bin:$PATH" REPO_DIR="$REPO_DIR" bash -c '
      cd "$1" || exit
      . "$REPO_DIR/lib/guards.sh"
      . "$REPO_DIR/lib/helpers.sh"
      . "$REPO_DIR/shell/rc.d/25-log.sh"
      logrun failcmd
    ' _ "$tmp/work"
  )"
  status=$?
  set -e

  assert_eq "logrun status" "7" "$status"
  assert_eq "logrun output" $'out\nerr' "$got"
  assert_eq "logrun file" $'out\nerr' "$(cat "$tmp/work/failcmd.log")"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_log_filter_writes_explicit_file
register_test test_logrun_writes_default_file_and_preserves_status
