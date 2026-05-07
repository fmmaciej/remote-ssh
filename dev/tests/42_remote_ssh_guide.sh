#!/usr/bin/env bash

REMOTE_SSH_GUIDE_TEST_REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

remote_ssh_guide_repo_dir() {
  printf '%s\n' "$REMOTE_SSH_GUIDE_TEST_REPO_DIR"
}

test_remote_ssh_guide_lists_core_entries() {
  log "remote-ssh guide lists core entries"

  local got repo_dir
  repo_dir="$(remote_ssh_guide_repo_dir)"
  got="$(
    HOME=/tmp/remote-ssh-guide-test \
      bash "$repo_dir/bin/remote-ssh" guide
  )"

  grep -q '^remote-ssh guide$' <<<"$got"
  grep -q '^Commands$' <<<"$got"
  grep -q '^  remote-ssh guide \[section\]  Show this configuration guide$' <<<"$got"
  grep -q '^  remote-ssh git setup        Add remote-ssh Git config via include.path$' <<<"$got"
  grep -q '^  remote-ssh git status       Check Git identity, SSH agent, and Git SSH auth$' <<<"$got"
  grep -q '^  sshf                        Pick an SSH host with fzf and connect$' <<<"$got"
  grep -q '^  starship-help               Explain prompt and Git status symbols$' <<<"$got"
  grep -q "^  alias rhelp='remote-ssh guide'$" <<<"$got"
  grep -q '^  log$' <<<"$got"
  grep -q '^  logrun$' <<<"$got"
  grep -q '^  remote_atuin_debug$' <<<"$got"
  grep -q '^Git SSH flow$' <<<"$got"
  grep -q '^Tools$' <<<"$got"
  grep -Fq "    $repo_dir/dots/git/user.local" <<<"$got"
  grep -q '^    git remote set-url origin git@github.com-myuser:OWNER/REPO.git$' <<<"$got"
}

test_remote_ssh_guide_supports_aliases_section() {
  log "remote-ssh guide supports aliases section"

  local got repo_dir
  repo_dir="$(remote_ssh_guide_repo_dir)"
  got="$(
    HOME=/tmp/remote-ssh-guide-test \
      bash "$repo_dir/bin/remote-ssh" guide aliases
  )"

  grep -q '^Aliases$' <<<"$got"
  grep -q "^  alias rcrc='source \"\$REMOTE_SHELL_DIR/rc.sh\"'$" <<<"$got"
  grep -q "^  alias rhelp='remote-ssh guide'$" <<<"$got"
  ! grep -q '^Commands$' <<<"$got"
}

test_remote_ssh_guide_supports_functions_section() {
  log "remote-ssh guide supports functions section"

  local got repo_dir
  repo_dir="$(remote_ssh_guide_repo_dir)"
  got="$(
    HOME=/tmp/remote-ssh-guide-test \
      bash "$repo_dir/bin/remote-ssh" guide functions
  )"

  grep -q '^Functions$' <<<"$got"
  grep -q '^  log$' <<<"$got"
  grep -q '^  logrun$' <<<"$got"
  grep -q '^  sshf$' <<<"$got"
  grep -q '^  remote_atuin_debug$' <<<"$got"
  ! grep -q '^Commands$' <<<"$got"
}

test_remote_ssh_guide_supports_git_section() {
  log "remote-ssh guide supports git section"

  local got repo_dir
  repo_dir="$(remote_ssh_guide_repo_dir)"
  got="$(
    HOME=/tmp/remote-ssh-guide-test \
      bash "$repo_dir/bin/remote-ssh" guide git
  )"

  grep -q '^Git SSH flow$' <<<"$got"
  grep -q '^    remote-ssh git setup$' <<<"$got"
  grep -Fq "    $repo_dir/dots/git/user.local" <<<"$got"
  grep -q '^    remote-ssh git status github.com-myuser$' <<<"$got"
  grep -Fq "    $repo_dir/dots/ssh/config.local" <<<"$got"
  grep -q '^    ssh -T git@github.com-myuser$' <<<"$got"
  ! grep -q '^Commands$' <<<"$got"
}

test_remote_ssh_guide_supports_tools_section() {
  log "remote-ssh guide supports tools section"

  local got repo_dir
  repo_dir="$(remote_ssh_guide_repo_dir)"
  got="$(
    HOME=/tmp/remote-ssh-guide-test \
      bash "$repo_dir/bin/remote-ssh" guide tools
  )"

  grep -q '^Tools$' <<<"$got"
  grep -q '^  install      remote-ssh install$' <<<"$got"
  grep -q '^Default tools on this platform$' <<<"$got"
  grep -q '^  rg$' <<<"$got"
  ! grep -q '^Commands$' <<<"$got"
}

register_test test_remote_ssh_guide_lists_core_entries
register_test test_remote_ssh_guide_supports_aliases_section
register_test test_remote_ssh_guide_supports_functions_section
register_test test_remote_ssh_guide_supports_git_section
register_test test_remote_ssh_guide_supports_tools_section
