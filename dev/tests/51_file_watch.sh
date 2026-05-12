#!/usr/bin/env bash

file_watch_script() {
  printf '%s/scripts/file-watch.sh\n' "$REPO_DIR"
}

file_watch_create_repo() {
  local tmp="$1"
  local source_dir="$tmp/source"
  local remote_dir="$tmp/remote.git"

  mkdir -p "$source_dir"

  (
    cd "$source_dir" || exit
    git init -q
    git checkout -q -b main
    git config user.name "Test User"
    git config user.email "test@example.com"
    mkdir -p docs
    printf 'hello\n' >docs/get-started.md
    git add docs/get-started.md
    git commit -q -m "initial"
    git tag v1.0.0
  )

  git clone -q --bare "$source_dir" "$remote_dir"
  git -C "$source_dir" remote add origin "$remote_dir"
}

file_watch_commit_change() {
  local source_dir="$1"

  (
    cd "$source_dir" || exit
    printf 'hello\nworld\n' >docs/get-started.md
    git add docs/get-started.md
    git commit -q -m "update get started"
    git push -q origin main
  )
}

file_watch_write_config() {
  local output="$1" repo="$2" cache_dir="$3" state_file="$4" fail_on_diff="$5"

  jq -n \
    --arg repo "$repo" \
    --arg cache_dir "$cache_dir" \
    --arg state_file "$state_file" \
    --argjson fail_on_diff "$fail_on_diff" \
    '{
      cache_dir: $cache_dir,
      state_file: $state_file,
      pointers: {
        "get-started-v1": {
          type: "git",
          repo: $repo,
          ref: "v1.0.0",
          file: "docs/get-started.md"
        },
        "get-started-main": {
          type: "git",
          repo: $repo,
          ref: "main",
          file: "docs/get-started.md"
        }
      },
      watches: [
        {
          name: "get-started-watch",
          left: "get-started-v1",
          right: "get-started-main",
          fail_on_diff: $fail_on_diff
        }
      ]
    }' >"$output"
}

test_file_watch_reports_no_differences() {
  log "file watch reports no differences"
  require_cmd git
  require_cmd jq

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  file_watch_create_repo "$tmp"
  file_watch_write_config "$tmp/config.json" "$tmp/remote.git" "$tmp/cache" "$tmp/state/state.json" false

  got="$("$BASH" "$(file_watch_script)" run "$tmp/config.json")"

  assert_contains "file watch no diff" "no differences" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_file_watch_prints_diff_and_skips_seen_inputs() {
  log "file watch prints diff and skips already checked inputs"
  require_cmd git
  require_cmd jq

  local tmp got skipped
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  file_watch_create_repo "$tmp"
  file_watch_commit_change "$tmp/source"
  file_watch_write_config "$tmp/config.json" "$tmp/remote.git" "$tmp/cache" "$tmp/state/state.json" false

  got="$("$BASH" "$(file_watch_script)" run "$tmp/config.json")"
  assert_contains "file watch diff header" "differences found" "$got"
  assert_contains "file watch diff body" "+world" "$got"

  skipped="$("$BASH" "$(file_watch_script)" run "$tmp/config.json")"
  assert_contains "file watch skip" "already checked" "$skipped"
  assert_contains "file watch skip message" "skipping diff" "$skipped"

  trap - RETURN
  rm -rf "$tmp"
}

test_file_watch_fail_on_diff_returns_one() {
  log "file watch fail_on_diff returns one"
  require_cmd git
  require_cmd jq

  local tmp got status
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  file_watch_create_repo "$tmp"
  file_watch_commit_change "$tmp/source"
  file_watch_write_config "$tmp/config.json" "$tmp/remote.git" "$tmp/cache" "$tmp/state/state.json" true

  set +e
  got="$("$BASH" "$(file_watch_script)" run "$tmp/config.json" 2>&1)"
  status=$?
  set -e

  assert_eq "file watch fail_on_diff status" "1" "$status"
  assert_contains "file watch fail_on_diff output" "differences found" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_file_watch_missing_config_field_returns_two() {
  log "file watch missing config field returns two"
  require_cmd jq

  local tmp got status
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  printf 'left\n' >"$tmp/a"
  jq -n \
    --arg left "$tmp/a" \
    '{
      cache_dir: "/tmp/cache",
      state_file: "/tmp/state.json",
      watches: [
        {
          name: "broken-watch",
          left: { type: "file", path: $left },
          right: { type: "git", ref: "main", file: "docs/get-started.md" }
        }
      ]
    }' >"$tmp/config.json"

  set +e
  got="$("$BASH" "$(file_watch_script)" run "$tmp/config.json" 2>&1)"
  status=$?
  set -e

  assert_eq "file watch missing field status" "2" "$status"
  assert_contains "file watch missing field output" "Missing required non-empty string config field: watches[0].right.repo" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_file_watch_missing_file_returns_three() {
  log "file watch missing file returns three"
  require_cmd git
  require_cmd jq

  local tmp got status
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  file_watch_create_repo "$tmp"
  (
    cd "$tmp/source" || exit
    git rm -q docs/get-started.md
    git commit -q -m "remove get started"
    git push -q origin main
  )
  file_watch_write_config "$tmp/config.json" "$tmp/remote.git" "$tmp/cache" "$tmp/state/state.json" false

  set +e
  got="$("$BASH" "$(file_watch_script)" run "$tmp/config.json" 2>&1)"
  status=$?
  set -e

  assert_eq "file watch missing file status" "3" "$status"
  assert_contains "file watch missing file output" "Target file does not exist" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_file_watch_compare_local_file_to_pointer() {
  log "file watch compares local file to named pointer"
  require_cmd git
  require_cmd jq

  local tmp got status
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  file_watch_create_repo "$tmp"
  file_watch_commit_change "$tmp/source"
  file_watch_write_config "$tmp/config.json" "$tmp/remote.git" "$tmp/cache" "$tmp/state/state.json" false
  printf 'hello\nlocal\n' >"$tmp/local.md"

  set +e
  got="$("$BASH" "$(file_watch_script)" compare "$tmp/local.md" get-started-main "$tmp/config.json" 2>&1)"
  status=$?
  set -e

  assert_eq "file watch compare status" "1" "$status"
  assert_contains "file watch compare diff" "differences found for ad hoc compare" "$got"
  assert_contains "file watch compare local line" "-local" "$got"
  assert_contains "file watch compare pointer line" "+world" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_file_watch_reports_no_differences
register_test test_file_watch_prints_diff_and_skips_seen_inputs
register_test test_file_watch_fail_on_diff_returns_one
register_test test_file_watch_missing_config_field_returns_two
register_test test_file_watch_missing_file_returns_three
register_test test_file_watch_compare_local_file_to_pointer
