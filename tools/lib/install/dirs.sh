# shellcheck shell=bash

ensure_this_file_sourced

install_shell_dir() {
  log_info "  shell/..."

  [[ -f "$SHELL_DIR/rc.sh" ]] && chmod +x "$SHELL_DIR/rc.sh"

  # [ -d "$SHELL_DIR" ] && find "$SHELL_DIR" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
}

# Ownership deliberately accepts only our literal canonical target. Bootstrap
# resolution is more permissive so users can invoke the CLI through other links.
install_cli_check_destination() {
  local command_path="$INSTALL_BIN_DIR/remote-ssh"
  if [[ -e "$command_path" || -L "$command_path" ]]; then
    if [[ ! -L "$command_path" ]] || [[ "$(readlink "$command_path")" != "$INSTALL_CLI_SOURCE" ]]; then
      printf 'Cannot install remote-ssh: refusing to replace %s\nExpected source: %s\nNo replacement was made. Inspect and move or remove the existing entry deliberately, or select a different INSTALL_BIN_DIR.\n' \
        "$command_path" "$INSTALL_CLI_SOURCE" >&2
      return 1
    fi
  fi
}

# No mkdir, chmod, config write or tool installation is allowed in preflight.
install_cli_preflight() {
  INSTALL_CLI_SOURCE="$(cd -- "$BIN_DIR" && pwd -P)/remote-ssh" || return 1
  if [[ ! -f "$INSTALL_CLI_SOURCE" ]] || [[ ! -x "$INSTALL_CLI_SOURCE" && ! -O "$INSTALL_CLI_SOURCE" ]]; then
    printf 'Cannot prepare remote-ssh executable: %s\n' "$INSTALL_CLI_SOURCE" >&2
    return 1
  fi
  case "$INSTALL_BIN_DIR" in
    /*) ;;
    *) INSTALL_BIN_DIR="$PWD/$INSTALL_BIN_DIR" ;;
  esac
  export INSTALL_BIN_DIR
  install_cli_check_destination
}

install_cli_publish() {
  mkdir -p "$INSTALL_BIN_DIR" || return 1
  # Canonicalize after creation; the preflight absolute path preserves the
  # caller's relative override even if another helper changes directories.
  INSTALL_BIN_DIR="$(cd -- "$INSTALL_BIN_DIR" && pwd -P)" || return 1
  export INSTALL_BIN_DIR
  install_cli_check_destination || return 1
  chmod +x "$INSTALL_CLI_SOURCE" || return 1
  if [[ ! -L "$INSTALL_BIN_DIR/remote-ssh" ]]; then
    # Directory operand prevents a newly occupied final directory from getting
    # a nested link. Never overwrite an existing entry, even after the recheck.
    ln -s "$INSTALL_CLI_SOURCE" "$INSTALL_BIN_DIR/" || {
      install_cli_check_destination || return 1
      printf 'Cannot publish remote-ssh: %s -> %s\n' "$INSTALL_BIN_DIR/remote-ssh" "$INSTALL_CLI_SOURCE" >&2
      return 1
    }
  fi
  [[ -L "$INSTALL_BIN_DIR/remote-ssh" ]] &&
    [[ "$(readlink "$INSTALL_BIN_DIR/remote-ssh")" == "$INSTALL_CLI_SOURCE" ]] || return 1
}

install_bin_dir() {
  log_info "  bin/..."
  [[ ! -d $BIN_DIR ]] || find "$BIN_DIR" -maxdepth 1 -type f -exec chmod +x {} +
}

install_dots_dir() {
  log_info "  dots/..."

  [[ -d "$DOTS_DIR" ]] || return 0

  log_info "    App configs:"
  [[ -f "$DOTS_DIR/starship.toml" ]] && log_info "      dots/starship.toml"
  [[ -f "$DOTS_DIR/tmux.conf" ]] && log_info "      dots/tmux.conf"
  [[ -f "$DOTS_DIR/vimrc" ]] && log_info "      dots/vimrc"
  [[ -f "$DOTS_DIR/atuin/config.toml" ]] && log_info "      dots/atuin/config.toml"

  log_info "    Setup templates:"
  [[ -f "$DOTS_DIR/git/config.base" ]] && log_info "      dots/git/config.base"
  [[ -f "$DOTS_DIR/git/user.local.example" ]] && log_info "      dots/git/user.local.example"
  [[ -f "$DOTS_DIR/ssh/config.example" ]] && log_info "      dots/ssh/config.example"

  log_info "    Cheatsheets:"
  [[ -d "$DOTS_DIR/navi/cheats" ]] && log_info "      dots/navi/cheats/*.cheat"
}
