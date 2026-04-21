#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_bash_preexec_loads_in_rc_flow() {
  log "bash-preexec loads in rc flow"

  local got
  got="$(
    REPO_DIR="$REPO_DIR" bash --noprofile --norc -ic '
      . "$REPO_DIR/shell/rc.sh"
      printf "%s\n" "${bash_preexec_imported:-missing}"
    ' 2>/dev/null
  )"

  assert_eq "bash-preexec import" "defined" "$got"
}

register_test test_bash_preexec_loads_in_rc_flow
