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

  [[ -d "$DOTS_DIR" ]] && log_info "    Found bundled dotfiles and app configs"
}
