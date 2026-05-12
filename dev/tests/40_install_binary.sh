#!/usr/bin/env bash
# shellcheck disable=SC2030,SC2031

test_install_binary_aliases() {
  log "install creates configured binary aliases"

  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt" "$tmp/extract/bin"
  printf '#!/usr/bin/env bash\n' >"$tmp/extract/bin/nu"
  chmod +x "$tmp/extract/bin/nu"

  (
    export HOME="$tmp/home"
    export INSTALL_PREFIX="$tmp/opt"
    export INSTALL_BIN_DIR="$tmp/bin"
    cd "$REPO_DIR" || exit
    # shellcheck source=/dev/null
    . "$REPO_DIR/tools/lib/env.sh"
    # shellcheck source=/dev/null
    . "$TOOLS_LIB_DIR/install-tool.lib.sh"
    install_binary nu nu 1.2.3 "$tmp/extract" nushell

    assert_eq "primary binary symlink" "$tmp/opt/nu-1.2.3/nu" "$(readlink "$tmp/bin/nu")"
    assert_eq "binary alias symlink" "$tmp/opt/nu-1.2.3/nu" "$(readlink "$tmp/bin/nushell")"
  )

  trap - RETURN
  rm -rf "$tmp"
}

test_install_binary_preserves_existing_version_on_failure() {
  log "install keeps existing version when replacement fails"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/demo-1.0.0" "$tmp/extract/bin"
  printf '#!/usr/bin/env bash\nprintf old\n' >"$tmp/opt/demo-1.0.0/demo"
  chmod +x "$tmp/opt/demo-1.0.0/demo"
  ln -s "$tmp/opt/demo-1.0.0/demo" "$tmp/bin/demo"

  printf '#!/usr/bin/env bash\nprintf new\n' >"$tmp/extract/bin/demo"
  chmod 111 "$tmp/extract/bin/demo"

  got="$(
    (
      export HOME="$tmp/home"
      export INSTALL_PREFIX="$tmp/opt"
      export INSTALL_BIN_DIR="$tmp/bin"
      cd "$REPO_DIR" || exit
      # shellcheck source=/dev/null
      . "$REPO_DIR/tools/lib/env.sh"
      # shellcheck source=/dev/null
      . "$TOOLS_LIB_DIR/install-tool.lib.sh"
      install_binary demo demo 1.0.0 "$tmp/extract"
    ) 2>&1
  )" && {
    printf 'Expected replacement install to fail\n' >&2
    return 1
  }

  assert_eq "existing symlink target" "$tmp/opt/demo-1.0.0/demo" "$(readlink "$tmp/bin/demo")"
  assert_eq "existing binary output" "old" "$("$tmp/bin/demo")"
  assert_contains "copy failure output" "Permission denied" "$got"

  chmod +r "$tmp/extract/bin/demo"
  trap - RETURN
  rm -rf "$tmp"
}

test_install_binary_rejects_unmanaged_alias_without_switching_primary() {
  log "install rejects unmanaged alias without switching primary"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/nu-1.0.0" "$tmp/extract/bin"
  printf '#!/usr/bin/env bash\nprintf old\n' >"$tmp/opt/nu-1.0.0/nu"
  chmod +x "$tmp/opt/nu-1.0.0/nu"
  ln -s "$tmp/opt/nu-1.0.0/nu" "$tmp/bin/nu"
  printf 'not managed\n' >"$tmp/bin/nushell"

  printf '#!/usr/bin/env bash\nprintf new\n' >"$tmp/extract/bin/nu"
  chmod +x "$tmp/extract/bin/nu"

  got="$(
    (
      export HOME="$tmp/home"
      export INSTALL_PREFIX="$tmp/opt"
      export INSTALL_BIN_DIR="$tmp/bin"
      cd "$REPO_DIR" || exit
      # shellcheck source=/dev/null
      . "$REPO_DIR/tools/lib/env.sh"
      # shellcheck source=/dev/null
      . "$TOOLS_LIB_DIR/install-tool.lib.sh"
      install_binary nu nu 2.0.0 "$tmp/extract" nushell
    ) 2>&1
  )" && {
    printf 'Expected unmanaged alias install to fail\n' >&2
    return 1
  }

  assert_contains "unmanaged alias output" "Refusing to replace unmanaged path: $tmp/bin/nushell" "$got"
  assert_eq "primary remains old after unmanaged alias" "$tmp/opt/nu-1.0.0/nu" "$(readlink "$tmp/bin/nu")"

  trap - RETURN
  rm -rf "$tmp"
}

test_install_binary_rejects_alias_directory_without_switching_primary() {
  log "install rejects alias directory without switching primary"

  local tmp got
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  mkdir -p "$tmp/home" "$tmp/bin" "$tmp/opt/nu-1.0.0" "$tmp/extract/bin" "$tmp/bin/nushell"
  printf '#!/usr/bin/env bash\nprintf old\n' >"$tmp/opt/nu-1.0.0/nu"
  chmod +x "$tmp/opt/nu-1.0.0/nu"
  ln -s "$tmp/opt/nu-1.0.0/nu" "$tmp/bin/nu"

  printf '#!/usr/bin/env bash\nprintf new\n' >"$tmp/extract/bin/nu"
  chmod +x "$tmp/extract/bin/nu"

  got="$(
    (
      export HOME="$tmp/home"
      export INSTALL_PREFIX="$tmp/opt"
      export INSTALL_BIN_DIR="$tmp/bin"
      cd "$REPO_DIR" || exit
      # shellcheck source=/dev/null
      . "$REPO_DIR/tools/lib/env.sh"
      # shellcheck source=/dev/null
      . "$TOOLS_LIB_DIR/install-tool.lib.sh"
      install_binary nu nu 2.0.0 "$tmp/extract" nushell
    ) 2>&1
  )" && {
    printf 'Expected alias directory install to fail\n' >&2
    return 1
  }

  assert_contains "alias directory output" "Refusing to replace unmanaged path: $tmp/bin/nushell" "$got"
  assert_eq "primary remains old after alias directory" "$tmp/opt/nu-1.0.0/nu" "$(readlink "$tmp/bin/nu")"

  trap - RETURN
  rm -rf "$tmp"
}

register_test test_install_binary_aliases
register_test test_install_binary_preserves_existing_version_on_failure
register_test test_install_binary_rejects_unmanaged_alias_without_switching_primary
register_test test_install_binary_rejects_alias_directory_without_switching_primary
