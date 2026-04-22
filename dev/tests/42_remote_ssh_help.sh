#!/usr/bin/env bash

test_remote_ssh_help_lists_core_entries() {
  log "remote-ssh-help lists core entries"

  local got
  got="$(
    HOME=/tmp/remote-ssh-help-test \
      bash "$REPO_DIR/bin/remote-ssh-help"
  )"

  grep -q '^remote-ssh help$' <<<"$got"
  grep -q '^  sshf                   Pick an SSH host with fzf and connect$' <<<"$got"
  grep -q '^  rcrc                   Reload remote-ssh shell config$' <<<"$got"
  grep -q '^  remote_atuin_debug     Print current Atuin integration state$' <<<"$got"
}

test_remote_ssh_help_supports_sections() {
  log "remote-ssh-help supports sections"

  local got
  got="$(
    HOME=/tmp/remote-ssh-help-test \
      bash "$REPO_DIR/bin/remote-ssh-help" aliases
  )"

  grep -q '^Aliases$' <<<"$got"
  grep -q '^  rhelp                  Show remote-ssh help$' <<<"$got"
  ! grep -q '^Commands$' <<<"$got"
}

register_test test_remote_ssh_help_lists_core_entries
register_test test_remote_ssh_help_supports_sections
