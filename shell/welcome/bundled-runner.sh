#!/usr/bin/env bash
# shellcheck source=/dev/null

# 125 is reserved for preflight failure. Nothing after preflight returns it.
remote_ssh_welcome_bundled_worker_main() {
  local __rs_worker_shell_dir __rs_worker_dir __rs_worker_path __rs_worker_renderer
  local __rs_worker_selected_dir __rs_worker_function __rs_worker_count=0 __rs_worker_index
  local __rs_worker_file
  local -a __rs_worker_paths=() __rs_worker_renderers=()

  __rs_worker_shell_dir="$(builtin cd -P -- "${BASH_SOURCE[0]%/*}/.." && builtin pwd -P)" || return 125
  # The loader's final status can hide an earlier failed source. Check files
  # independently, so inherited exported functions cannot conceal a missing one.
  for __rs_worker_file in welcome.lib.sh update-check.lib.sh \
    update-check/toggle.sh update-check/state.sh update-check/time.sh \
    welcome/base.sh welcome/toggles.sh welcome/issues.sh welcome/banner.sh \
    welcome/host.sh welcome/update.sh welcome/commands.sh welcome/hw.sh \
    welcome/sw.sh welcome/bundled.sh welcome/runner.sh; do
    if [[ ! -f "$__rs_worker_shell_dir/$__rs_worker_file" || ! -r "$__rs_worker_shell_dir/$__rs_worker_file" ]]; then
      printf 'remote-ssh welcome: required library unavailable: %s\n' "$__rs_worker_file" >&2
      return 125
    fi
  done
  # Suppress loader stdout until preflight has completed, including load errors.
  . "$__rs_worker_shell_dir/welcome.lib.sh" >/dev/null || return 125
  # Validate the fixed welcome/update helper surface without invoking providers.
  # tools/lib/status.lib.sh remains a lazy load inside the first capture.
  for __rs_worker_function in remote_ssh_welcome_loader_dir remote_ssh_update_check_lib_dir \
    remote_ssh_update_check_enabled remote_ssh_update_check_state_dir \
    remote_ssh_update_check_cache_file remote_ssh_update_check_cache_get \
    remote_ssh_update_check_interval remote_ssh_update_check_now \
    remote_ssh_update_check_checked_at_text remote_ssh_update_check_is_stale \
    remote_ssh_welcome_lib_dir remote_ssh_welcome_repo_dir remote_ssh_welcome_bundled_dir \
    remote_ssh_welcome_bool_disabled remote_ssh_welcome_trim \
    remote_ssh_welcome_color_enabled remote_ssh_welcome_banner_enabled remote_ssh_welcome_debug_enabled \
    remote_ssh_welcome_issue_allowed remote_ssh_welcome_issue \
    remote_ssh_welcome_green remote_ssh_welcome_print_full_banner remote_ssh_welcome_print_banner \
    remote_ssh_welcome_host_ip_from_hostname remote_ssh_welcome_host_ip_from_ip_route \
    remote_ssh_welcome_host_ip_from_ifconfig remote_ssh_welcome_host_ip remote_ssh_welcome_print_host \
    remote_ssh_welcome_print_update remote_ssh_welcome_load_commands remote_ssh_welcome_print_tools \
    remote_ssh_welcome_requirement_ok remote_ssh_welcome_path_ok remote_ssh_welcome_print_scripts \
    remote_ssh_welcome_cpu_count remote_ssh_welcome_ram_gib remote_ssh_welcome_print_hw \
    remote_ssh_welcome_ssh_agent_status remote_ssh_welcome_git_user_config_status remote_ssh_welcome_print_sw \
    remote_ssh_welcome_render_remote_ssh remote_ssh_welcome_render_hw remote_ssh_welcome_render_sw \
    remote_ssh_welcome_bundled_shell_dir remote_ssh_welcome_bundled_renderer \
    remote_ssh_welcome_bundled_options_unexported remote_ssh_welcome_bundled_render \
    remote_ssh_welcome_enabled remote_ssh_welcome_user_enabled remote_ssh_welcome_print_line \
    remote_ssh_welcome_note_issue remote_ssh_welcome_remove_temp_file remote_ssh_welcome_cleanup_issues \
    remote_ssh_welcome_run_module remote_ssh_welcome_run_external_paths remote_ssh_welcome_run_dir \
    remote_ssh_welcome_run_bundled remote_ssh_welcome_user_dir remote_ssh_welcome_collect_issues \
    remote_ssh_welcome_next_command remote_ssh_welcome_print_next remote_ssh_welcome_run remote_ssh_welcome_main; do
    if ! builtin declare -F "$__rs_worker_function" >/dev/null; then
      printf 'remote-ssh welcome: required function unavailable: %s\n' "$__rs_worker_function" >&2
      return 125
    fi
  done
  [[ "${1:-}" == -- ]] || return 125
  shift
  (($# > 0)) || return 125
  __rs_worker_dir="${1%/*}"
  __rs_worker_selected_dir="$(builtin cd -P -- "$__rs_worker_dir/.." && builtin pwd -P)" || return 125
  [ "$__rs_worker_shell_dir" = "$__rs_worker_selected_dir" ] || return 125

  for __rs_worker_path in "$@"; do
    __rs_worker_renderer="$(remote_ssh_welcome_bundled_renderer "$__rs_worker_dir" "$__rs_worker_path")" || return 125
    __rs_worker_paths[__rs_worker_count]="$__rs_worker_path"
    __rs_worker_renderers[__rs_worker_count]="$__rs_worker_renderer"
    __rs_worker_count=$((__rs_worker_count + 1))
  done

  # Each renderer has its own capture subshell/file/replay. In particular, status
  # library globals loaded by the first renderer never reach its siblings.
  for ((__rs_worker_index=0; __rs_worker_index<__rs_worker_count; __rs_worker_index++)); do
    remote_ssh_welcome_run_module "${__rs_worker_paths[__rs_worker_index]}" \
      "${__rs_worker_renderers[__rs_worker_index]}" || true
  done
  return 0
}

remote_ssh_welcome_bundled_worker_main "$@"
