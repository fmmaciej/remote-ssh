# shellcheck shell=bash
# shellcheck disable=SC2153

ensure_this_file_sourced

remote_ssh_cmd_git_status_agent_needs_fix() {
  case "$REMOTE_SSH_GIT_STATUS_AGENT_STATUS" in
    missing-sock|stale-sock|unreachable|no-keys|ssh-add-missing) return 0 ;;
  esac
  return 1
}

remote_ssh_cmd_git_status_print_agent_hint() {
  case "$REMOTE_SSH_GIT_STATUS_AGENT_STATUS" in
    missing-sock)
      printf '  - Start or forward an SSH agent, then reopen this shell.\n'
      ;;
    stale-sock)
      printf '  - SSH_AUTH_SOCK points to a dead socket; reconnect or refresh agent forwarding.\n'
      ;;
    unreachable)
      printf '  - ssh-add cannot talk to the agent; reconnect, restart the agent, or fix agent forwarding.\n'
      ;;
    no-keys)
      printf '  - Load a key with ssh-add, or check that your forwarded agent has identities.\n'
      ;;
    ssh-add-missing)
      printf '  - ssh-add is missing, so remote-ssh cannot inspect loaded keys.\n'
      ;;
  esac
}

remote_ssh_cmd_git_status_print_auth_hint() {
  case "$REMOTE_SSH_GIT_STATUS_AUTH_STATUS" in
    skipped)
      printf '  - Pass a host, e.g. remote-ssh git status github.com-myuser, or configure origin.\n'
      ;;
    denied-publickey)
      if remote_ssh_cmd_git_status_agent_needs_fix; then
        printf '  - Fix the SSH agent first, then retry remote-ssh git status %s.\n' "$REMOTE_SSH_GIT_STATUS_SSH_HOST"
      else
        printf '  - Check the SSH alias, IdentityFile, and whether the public key is registered with your Git provider.\n'
        printf '  - Run remote-ssh git setup if the Git SSH aliases are not configured yet.\n'
      fi
      ;;
    host-unresolved)
      printf '  - Check the SSH host alias in dots/ssh/config.local or pass a valid host.\n'
      ;;
    host-key-failed)
      printf '  - Verify known_hosts for this host before accepting or removing any host key.\n'
      ;;
    network-failed)
      printf '  - Check network, VPN, firewall, and whether the SSH host is reachable.\n'
      ;;
    failed)
      printf '  - Inspect SSH output above; retry with ssh -Tv git@%s for verbose details.\n' "$REMOTE_SSH_GIT_STATUS_SSH_HOST"
      ;;
  esac
}

remote_ssh_cmd_git_status_print_hints() {
  local printed=0

  printf '\nNext steps\n'

  if remote_ssh_cmd_git_status_agent_needs_fix; then
    remote_ssh_cmd_git_status_print_agent_hint
    printed=1
  fi

  if [[ "$REMOTE_SSH_GIT_STATUS_AUTH_STATUS" != "ok" ]]; then
    remote_ssh_cmd_git_status_print_auth_hint
    printed=1
  fi

  if [[ "$printed" -eq 0 ]]; then
    printf '  [none]\n'
  fi
}
