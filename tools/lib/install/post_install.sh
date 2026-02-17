# shellcheck shell=bash

ensure_this_file_sourced

install_print_post_install() {
  local template_file="$REPO_DIR/docs/POST_INSTALL"

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
