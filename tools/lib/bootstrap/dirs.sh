# shellcheck shell=bash

ensure_this_file_sourced

bootstrap_shell_dir() {
  log_info "  shell/..."

  [[ -f "$SHELL_DIR/rc.sh" ]] && chmod +x "$SHELL_DIR/rc.sh"

  # [ -d "$SHELL_DIR" ] && find "$SHELL_DIR" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
}

bootstrap_bin_dir() {
  log_info "  bin/..."

  [[ -d "$BIN_DIR" ]] && find "$BIN_DIR" -maxdepth 1 -type f -name '*.sh' -exec chmod +x {} +
}

bootstrap_dots_dir() {
  log_info "  dots/..."

  [[ -f "$DOTS_DIR/starship.toml" ]] && log_info "    Found dots/starship.toml"
}
