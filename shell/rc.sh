#!/usr/bin/env bash

if [[ -z ${BASH_VERSION:-} ]]; then
  printf 'ERROR: remote-ssh shell/rc.sh must be loaded by bash.\n' >&2
  printf 'Use: bash --rcfile /path/to/remote-ssh/shell/rc.sh -i\n' >&2
  return 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

REMOTE_SHELL_DIR="$SCRIPT_DIR"

# shellcheck disable=SC1091
[ -f "$REMOTE_SHELL_DIR/env.sh" ] && . "$REMOTE_SHELL_DIR/env.sh"

# shellcheck disable=SC1091
[ -f "$REMOTE_SHELL_DIR/aliases.sh" ] && . "$REMOTE_SHELL_DIR/aliases.sh"

RC_D_DIR="$REMOTE_SHELL_DIR/rc.d"

remote_source_dir "$RC_D_DIR"
remote_source_file "$RC_D_DIR/os.d/$(remote_os_id).sh"

REMOTE_HOSTNAME="$(remote_hostname_short)"
if [[ -n $REMOTE_HOSTNAME ]]; then
  remote_source_file "$RC_D_DIR/host.d/${REMOTE_HOSTNAME}.sh"
fi

unset REMOTE_HOSTNAME
