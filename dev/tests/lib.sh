#!/usr/bin/env bash

: "${TEST_LOG_PREFIX:=smoke}"

SMOKE_TESTS=()

register_test() {
  SMOKE_TESTS+=("$1")
}

log() {
  printf '[%s] %s\n' "$TEST_LOG_PREFIX" "$*" >&2
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required developer command: %s\n' "$1" >&2
    return 1
  }
}

assert_eq() {
  local label="$1" expected="$2" got="$3"

  [[ "$got" == "$expected" ]] || {
    printf 'Unexpected %s:\n' "$label" >&2
    printf '%s\n%s\n' '--- expected ---' "$expected" >&2
    printf '%s\n%s\n' '--- got ---' "$got" >&2
    return 1
  }
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"

  grep -F -- "$needle" <<<"$haystack" >/dev/null || {
    printf 'Expected %s to contain:\n%s\n' "$label" "$needle" >&2
    printf '%s\n%s\n' '--- got ---' "$haystack" >&2
    return 1
  }
}
