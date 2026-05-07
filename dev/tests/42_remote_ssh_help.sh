#!/usr/bin/env bash

test_remote_ssh_help_lists_core_entries() {
  log "remote-ssh-help lists core entries"

  local got
  got="$(
    HOME=/tmp/remote-ssh-help-test \
      bash "$REPO_DIR/bin/remote-ssh-help"
  )"

  grep -q '^remote-ssh help$' <<<"$got"
  grep -q '^  remote-ssh             Main entrypoint for install/check/update/doctor/prune$' <<<"$got"
  grep -q '^  sshf                   Pick an SSH host with fzf and connect$' <<<"$got"
  grep -q '^  starship-help          Explain remote-ssh prompt and Git status symbols$' <<<"$got"
  grep -q '^  remote-ssh-check       Report pinned tools vs local bin and PATH$' <<<"$got"
  grep -q '^  remote-ssh-git-identity$' <<<"$got"
  grep -q '^  cheats                 Open private navi cheatsheets$' <<<"$got"
  grep -q '^  rcrc                   Reload remote-ssh shell config$' <<<"$got"
  grep -q '^  cheats                 Open private navi cheatsheets$' <<<"$got"
  grep -q '^  log                    Save stdin to a log file and show highlighted output$' <<<"$got"
  grep -q '^  logrun                 Run a command, capture stdout/stderr, and save a log$' <<<"$got"
  grep -q '^  remote_atuin_debug     Print current Atuin integration state$' <<<"$got"
  grep -q '^Git SSH flow$' <<<"$got"
  grep -q '^    /tmp/remote-ssh-help-test/.local/share/remote-ssh/dots/git/user.local$' <<<"$got"
  grep -q '^    git remote set-url origin git@github.com-myuser:OWNER/REPO.git$' <<<"$got"
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

test_remote_ssh_help_supports_git_section() {
  log "remote-ssh-help supports git section"

  local got
  got="$(
    HOME=/tmp/remote-ssh-help-test \
      bash "$REPO_DIR/bin/remote-ssh-help" git
  )"

  grep -q '^Git SSH flow$' <<<"$got"
  grep -q '^    remote-ssh-git-setup$' <<<"$got"
  grep -q '^    /tmp/remote-ssh-help-test/.local/share/remote-ssh/dots/git/user.local$' <<<"$got"
  grep -q '^    remote-ssh-git-identity github.com-myuser$' <<<"$got"
  grep -q '^    /tmp/remote-ssh-help-test/.local/share/remote-ssh/dots/ssh/config.local$' <<<"$got"
  grep -q '^    ssh -T git@github.com-myuser$' <<<"$got"
  ! grep -q '^Commands$' <<<"$got"
}

register_test test_remote_ssh_help_lists_core_entries
register_test test_remote_ssh_help_supports_sections
register_test test_remote_ssh_help_supports_git_section
