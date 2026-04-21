#!/usr/bin/env bash

test_tmux_conf_uses_modern_copy_mode_api() {
  log "tmux config uses modern copy-mode api"

  local conf="$REPO_DIR/dots/tmux.conf"

  rg -q 'bind -T copy-mode-vi v send -X begin-selection' "$conf"
  rg -q 'bind -T copy-mode-vi y send -X copy-selection-and-cancel' "$conf"
  rg -q 'bind -T copy-mode-vi Escape send -X cancel' "$conf"
  ! rg -q 'vi-copy' "$conf"
}

test_tmux_conf_reloads_project_config() {
  log "tmux reload points at project config"

  local conf="$REPO_DIR/dots/tmux.conf"

  rg -q 'source-file ~/.local/share/remote-ssh/dots/tmux.conf' "$conf"
}

register_test test_tmux_conf_uses_modern_copy_mode_api
register_test test_tmux_conf_reloads_project_config
