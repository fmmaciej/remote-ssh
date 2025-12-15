# shellcheck shell=bash

ensure_this_file_sourced

bootstrap_print_post_install() {
  local template_file="$REPO_DIR/POST_INSTALL.txt"

  if [[ -f "$template_file" ]]; then
    echo
    echo "================= POST INSTALL ================="
    echo
    sed "s|@INSTALL_DIR@|$REPO_DIR|g" "$template_file"
    echo
    echo "================================================"
    echo
  fi
}
