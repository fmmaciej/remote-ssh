# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_cmd_shell_usage() {
  cat <<'USAGE'
Usage: remote-ssh shell

Start an interactive Bash with the remote-ssh environment.
Use exit to return to the calling shell.
USAGE
}

remote_ssh_cmd_shell_main() {
  local repo_dir="$1"
  shift

  if (($# > 0)); then
    if (($# == 1)) && [[ "$1" == '-h' || "$1" == '--help' ]]; then
      remote_ssh_cmd_shell_usage
      return 0
    fi
    printf 'remote-ssh shell: does not accept arguments.\n' >&2
    remote_ssh_cmd_shell_usage >&2
    return 1
  fi

  local rcfile="$repo_dir/shell/rc.sh" child_bash
  if [[ ! -f "$rcfile" || ! -r "$rcfile" ]]; then
    printf 'remote-ssh shell: rcfile is not a readable regular file: %s\n' "$rcfile" >&2
    return 1
  fi
  if ! child_bash="$(type -P bash)"; then
    printf 'remote-ssh shell: cannot find an executable Bash in PATH.\n' >&2
    return 127
  fi

  exec "$child_bash" --rcfile "$rcfile" -i
}
