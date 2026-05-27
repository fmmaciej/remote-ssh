#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/../welcome.lib.sh"

remote_ssh_welcome_print_banner
remote_ssh_welcome_print_host
remote_ssh_welcome_print_update

if remote_ssh_welcome_load_commands; then
  remote_ssh_welcome_print_tools
  remote_ssh_welcome_print_scripts
else
  printf 'tools:   0 checked / 0 ok\n'
  printf 'scripts: 0 checked / 0 ok\n'
  remote_ssh_welcome_issue doctor
fi
