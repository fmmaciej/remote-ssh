#!/usr/bin/env bash

write_fake_runme_git() {
  local bin_dir="$1"

  cat >"$bin_dir/git" <<'EOF'
#!/usr/bin/env bash
if [[ -n "${RUNME_GIT_LOG:-}" ]]; then
  printf 'git %s\n' "$*" >>"$RUNME_GIT_LOG"
fi

if [[ "${1:-}" == "-C" && "${3:-}" == "pull" && "${4:-}" == "--ff-only" ]]; then
  exit 0
fi

if [[ "${1:-}" == "-C" && "${3:-}" == "fetch" && "${4:-}" == "--depth" && "${5:-}" == "1" && "${6:-}" == "origin" && -n "${7:-}" ]]; then
  exit 0
fi

if [[ "${1:-}" == "-C" && "${3:-}" == "checkout" && "${4:-}" == "--detach" && "${5:-}" == "FETCH_HEAD" ]]; then
  exit 0
fi

printf 'unexpected git args: %s\n' "$*" >&2
exit 99
EOF

  chmod +x "$bin_dir/git"
}

prepare_runme_install_dir() {
  local install_dir="$1" output_file="$2"

  mkdir -p "$install_dir/.git" "$install_dir/bin"
  cat >"$install_dir/bin/remote-ssh" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" >"$output_file"
EOF
  chmod +x "$install_dir/bin/remote-ssh"
}

test_runme_uses_default_tool_selection() {
  log "runme uses editable default tool selection"

  local tmp install_dir args expected
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" PATH="$tmp/bin:/usr/bin:/bin" bash "$REPO_DIR/runme.sh" >/dev/null

  args="$(cat "$tmp/args")"
  expected="$(
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install.lib.sh"
    printf '%s\n' install "${DEFAULT_TOOLS[@]}"
  )"

  assert_eq "runme default tools" "$expected" "$args"

  trap - RETURN
  rm -rf "$tmp"
}

test_runme_uses_argument_tool_selection() {
  log "runme uses argument tool selection"

  local tmp install_dir args
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" PATH="$tmp/bin:/usr/bin:/bin" bash "$REPO_DIR/runme.sh" fd rg >/dev/null

  args="$(cat "$tmp/args")"
  assert_eq "runme selected tools" $'install\nfd\nrg' "$args"

  trap - RETURN
  rm -rf "$tmp"
}

test_runme_forwards_yes_verbatim() {
  log "runme forwards --yes verbatim"

  local tmp install_dir args
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" PATH="$tmp/bin:/usr/bin:/bin" bash "$REPO_DIR/runme.sh" --yes >/dev/null

  args="$(cat "$tmp/args")"
  assert_eq "runme --yes passthrough" $'install\n--yes' "$args"

  trap - RETURN
  rm -rf "$tmp"
}

test_runme_forwards_yes_to_argument_tool_selection() {
  log "runme forwards --yes to argument tool selection"

  local tmp install_dir args
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" PATH="$tmp/bin:/usr/bin:/bin" bash "$REPO_DIR/runme.sh" --yes fd rg >/dev/null

  args="$(cat "$tmp/args")"
  assert_eq "runme --yes selected tools" $'install\n--yes\nfd\nrg' "$args"

  trap - RETURN
  rm -rf "$tmp"
}

test_runme_forwards_full_install() {
  log "runme forwards --full install"

  local tmp install_dir args
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" PATH="$tmp/bin:/usr/bin:/bin" bash "$REPO_DIR/runme.sh" --full --yes >/dev/null

  args="$(cat "$tmp/args")"
  assert_eq "runme --full --yes" $'install\n--full\n--yes' "$args"

  trap - RETURN
  rm -rf "$tmp"
}

test_runme_updates_existing_checkout_by_default() {
  log "runme updates existing checkout by default"

  local tmp install_dir got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" \
    RUNME_GIT_LOG="$tmp/git.log" \
    PATH="$tmp/bin:/usr/bin:/bin" \
    bash "$REPO_DIR/runme.sh" fd >/dev/null

  got="$(cat "$tmp/git.log")"
  assert_contains "runme pull" "pull --ff-only" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

test_runme_checks_out_requested_ref() {
  log "runme checks out REMOTE_SSH_REF"

  local tmp install_dir got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  install_dir="$tmp/home/.local/share/remote-ssh"
  mkdir -p "$tmp/bin"
  write_fake_runme_git "$tmp/bin"
  prepare_runme_install_dir "$install_dir" "$tmp/args"

  HOME="$tmp/home" \
    REMOTE_SSH_REF="v1.2.3" \
    RUNME_GIT_LOG="$tmp/git.log" \
    PATH="$tmp/bin:/usr/bin:/bin" \
    bash "$REPO_DIR/runme.sh" fd >/dev/null

  got="$(cat "$tmp/git.log")"
  assert_contains "runme ref fetch" "fetch --depth 1 origin v1.2.3" "$got"
  assert_contains "runme ref checkout" "checkout --detach FETCH_HEAD" "$got"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_runme_uses_default_tool_selection
register_test test_runme_uses_argument_tool_selection
register_test test_runme_forwards_yes_verbatim
register_test test_runme_forwards_yes_to_argument_tool_selection
register_test test_runme_forwards_full_install
register_test test_runme_updates_existing_checkout_by_default
register_test test_runme_checks_out_requested_ref
