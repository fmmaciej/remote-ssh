# shellcheck shell=bash

ensure_this_file_sourced

install_shell_dir() {
  log_info "  shell/..."

  [[ -f "$SHELL_DIR/rc.sh" ]] && chmod +x "$SHELL_DIR/rc.sh"

  # [ -d "$SHELL_DIR" ] && find "$SHELL_DIR" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
}

install_bin_dir() {
  log_info "  bin/..."

  [[ -d $BIN_DIR ]] && find "$BIN_DIR" -maxdepth 1 -type f -exec chmod +x {} +
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
