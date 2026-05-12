# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_doctor_path_contains_install_bin() {
  local part
  local -a path_parts

  IFS=':' read -r -a path_parts <<<"${PATH:-}"
  for part in "${path_parts[@]}"; do
    [[ "$part" == "$INSTALL_BIN_DIR" ]] && return 0
  done
  return 1
}

remote_ssh_cmd_doctor_git_output() {
  local repo_dir="$1"
  shift

  git -C "$repo_dir" "$@" 2>/dev/null || true
}

remote_ssh_cmd_doctor_shell_rc_loads() {
  local repo_dir="$1"

  REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT=0 \
    bash --noprofile --norc -c 'source "$1"' _ "$repo_dir/shell/rc.sh" >/dev/null 2>&1
}

remote_ssh_cmd_doctor_collect_tool_statuses() {
  local def_dir="$TOOLS_DIR/defs"
  local tool status

  REMOTE_SSH_DOCTOR_TOOL_STATUSES=()

  read_expected_tools_for_current_platform || return 0
  for tool in "${REMOTE_SSH_EXPECTED_TOOLS[@]}"; do
    remote_ssh_tool_status_load "$tool" "$def_dir"
    for status in "${REMOTE_SSH_TOOL_STATUS_STATUSES[@]}"; do
      REMOTE_SSH_DOCTOR_TOOL_STATUSES+=("$status")
    done
  done
}

remote_ssh_cmd_doctor_has_tool_status() {
  local wanted="$1" status

  for status in ${REMOTE_SSH_DOCTOR_TOOL_STATUSES[@]+"${REMOTE_SSH_DOCTOR_TOOL_STATUSES[@]}"}; do
    [[ "$status" == "$wanted" ]] && return 0
  done

  return 1
}

remote_ssh_cmd_doctor_has_install_hint_status() {
  remote_ssh_cmd_doctor_has_tool_status missing ||
    remote_ssh_cmd_doctor_has_tool_status external-only ||
    remote_ssh_cmd_doctor_has_tool_status stale-local ||
    remote_ssh_cmd_doctor_has_tool_status unmanaged-local
}

remote_ssh_cmd_doctor_main() {
  remote_ssh_cmd_require_install_libs

  local repo_dir="$1" script_repo_dir="$2" requested_repo_dir="$3"
  local failed=0 branch commit dirty requested_status
  local git_status check_output check_status

  printf 'remote-ssh doctor\n\n'

  printf 'Runtime requirements\n'
  if check_req_tools; then
    printf '  status: ok\n'
  else
    printf '  status: failed\n'
    failed=1
  fi

  printf '\nRepository\n'
  printf '  path:   %s\n' "$repo_dir"
  printf '  script: %s\n' "$script_repo_dir"
  if [[ -n "$requested_repo_dir" ]]; then
    printf '  env:    %s\n' "$requested_repo_dir"
    if [[ "$requested_repo_dir" == "$script_repo_dir" ]]; then
      requested_status="ok"
    else
      requested_status="mismatch"
      failed=1
    fi
  else
    requested_status="derived"
  fi
  printf '  env status: %s\n' "$requested_status"
  if [[ -d "$repo_dir/.git" ]] && git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf '  git:    ok\n'
    branch="$(remote_ssh_cmd_doctor_git_output "$repo_dir" symbolic-ref --short HEAD)"
    commit="$(remote_ssh_cmd_doctor_git_output "$repo_dir" rev-parse --short HEAD)"
    git_status="$(remote_ssh_cmd_doctor_git_output "$repo_dir" status --porcelain)"
    if [[ -n "$git_status" ]]; then
      dirty="yes"
    else
      dirty="no"
    fi
    printf '  branch: %s\n' "${branch:-[detached]}"
    printf '  commit: %s\n' "${commit:-[unknown]}"
    printf '  dirty:  %s\n' "$dirty"
  else
    printf '  git:    missing-or-invalid\n'
    failed=1
  fi

  printf '\nPATH\n'
  printf '  bin:    %s\n' "$INSTALL_BIN_DIR"
  if remote_ssh_cmd_doctor_path_contains_install_bin; then
    printf '  status: ok\n'
  else
    printf '  status: missing-from-PATH\n'
    failed=1
  fi

  printf '\nShell rc\n'
  printf '  file:   %s\n' "$repo_dir/shell/rc.sh"
  if [[ -r "$repo_dir/shell/rc.sh" ]] && remote_ssh_cmd_doctor_shell_rc_loads "$repo_dir"; then
    printf '  status: ok\n'
  else
    printf '  status: failed\n'
    failed=1
  fi

  printf '\nOptional helpers\n'
  if command -v python3 >/dev/null 2>&1; then
    printf '  sshf python3: ok\n'
  else
    printf '  sshf python3: missing-optional\n'
  fi

  printf '\nTool check\n'
  if [[ "$requested_status" == "mismatch" ]]; then
    printf '  summary: skipped-env-mismatch\n'
    failed=1
  else
    set +e
    check_output="$(remote_ssh_cmd_check_main --strict 2>&1)"
    check_status=$?
    set -e

    if ((check_status == 0)); then
      printf '  summary: ok\n\n'
    else
      printf '  summary: failed\n\n'
      failed=1
    fi

    printf '%s\n' "$check_output"

    if ((check_status != 0)); then
      remote_ssh_cmd_doctor_collect_tool_statuses

      printf '\nNext steps\n'
      if ! expected_tools_exists; then
        printf '  choose tools: remote-ssh install fd rg fzf\n'
        printf '  or install all supported tools: remote-ssh install --full --yes\n'
      elif remote_ssh_cmd_doctor_has_install_hint_status; then
        printf '  run: remote-ssh install\n'
      fi
      if remote_ssh_cmd_doctor_has_tool_status path-shadowed; then
        printf '  check PATH order: %s should come before external tool directories\n' "$INSTALL_BIN_DIR"
      fi
      printf '  inspect: remote-ssh check --strict\n'
    fi
  fi

  ((failed == 0))
}
