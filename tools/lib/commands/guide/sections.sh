# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_guide_print_commands() {
  cat <<'EOF'
Commands
  remote-ssh --help           Show concise CLI usage
  remote-ssh install [tool]   Install default or selected remote-ssh tools
  remote-ssh tool install     Install selected pinned tools
  remote-ssh check --strict   Report pinned tools vs local bin and PATH
  remote-ssh git setup        Add remote-ssh Git config via include.path
  remote-ssh git status       Check Git identity, SSH agent, and Git SSH auth
  remote-ssh update           Git pull this checkout, then run install
  remote-ssh doctor           Check runtime requirements and installed tools
  remote-ssh prune [--apply]  Report or remove unused installed releases
  remote-ssh guide [section]  Show this configuration guide
  starship-help               Explain prompt and Git status symbols
  sshf                        Pick an SSH host with fzf and connect
  cheats                      Open private navi cheatsheets
EOF
}

remote_ssh_cmd_guide_print_aliases() {
  local got

  printf 'Aliases\n'
  if got="$(remote_ssh_cmd_guide_remote_shell_snapshot aliases 2>&1)"; then
    remote_ssh_cmd_guide_print_prefixed_lines "$got"
  else
    printf '  [failed to load shell/rc.sh]\n'
    remote_ssh_cmd_guide_print_prefixed_lines "$got"
  fi
}

remote_ssh_cmd_guide_print_functions() {
  local got

  printf 'Functions\n'
  if got="$(remote_ssh_cmd_guide_remote_shell_snapshot functions 2>&1)"; then
    remote_ssh_cmd_guide_print_prefixed_lines "$got"
  else
    printf '  [failed to load shell/rc.sh]\n'
    remote_ssh_cmd_guide_print_prefixed_lines "$got"
  fi
}

remote_ssh_cmd_guide_print_paths() {
  cat <<EOF
Paths
  repo          $(remote_ssh_cmd_guide_repo_dir)
  bin           $(remote_ssh_cmd_guide_bin_dir)
  dots          $(remote_ssh_cmd_guide_dots_dir)
  shell         $(remote_ssh_cmd_guide_shell_dir)
  cheats        $(remote_ssh_cmd_guide_cheats_dir)
  atuin marker  $(remote_ssh_cmd_guide_atuin_marker)
EOF
}

remote_ssh_cmd_guide_print_git() {
  local dots_dir

  dots_dir="$(remote_ssh_cmd_guide_dots_dir)"

  cat <<EOF
Git SSH flow
  Run setup:
    remote-ssh git setup
  Edit your remote-ssh Git identity:
    $dots_dir/git/user.local
  Edit your account-specific SSH alias:
    $dots_dir/ssh/config.local
  The Git identity file is applied as a session override in remote-ssh shells,
  so it can override repository .git/config without writing to it.
  Use that alias in repository remotes:
    git remote set-url origin git@github.com-myuser:OWNER/REPO.git
  Verify the Git account used by SSH:
    ssh -T git@github.com-myuser
  Check Git config, SSH agent, and SSH auth together:
    remote-ssh git status github.com-myuser
  Disable the session identity override before rc.sh loads:
    export REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY=0
EOF
}

remote_ssh_cmd_guide_print_notes() {
  cat <<EOF
Notes
  remote-ssh --help is intentionally short.
  remote-ssh guide shows the loaded shell configuration.
  remote-ssh prune is dry-run by default; use --apply to remove candidates.
  Use logrun make build to save make.log, or command 2>&1 | log file.log.
  vim/nvim and tmux are not installed by remote-ssh.
  sshf currently requires python3 for SSH config parsing.
EOF
}

remote_ssh_cmd_guide_print_all() {
  printf 'remote-ssh guide\n\n'
  remote_ssh_cmd_guide_print_commands
  printf '\n'
  remote_ssh_cmd_guide_print_aliases
  printf '\n'
  remote_ssh_cmd_guide_print_functions
  printf '\n'
  remote_ssh_cmd_guide_print_paths
  printf '\n'
  remote_ssh_cmd_guide_print_tools
  printf '\n'
  remote_ssh_cmd_guide_print_git
  printf '\n'
  remote_ssh_cmd_guide_print_notes
}
