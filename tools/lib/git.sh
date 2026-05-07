# shellcheck shell=bash

ensure_this_file_sourced

remote_ssh_git_repo_dir() {
  cd "${REMOTE_ENV_DIR:-$REPO_DIR}" && pwd
}

remote_ssh_git_usage() {
  cat <<'EOF'
Usage: remote-ssh git <command> [args]

Commands:
  setup              Enable bundled Git defaults and SSH alias includes
  status [ssh-host]  Report Git identity, SSH agent, and Git SSH auth
EOF
}

remote_ssh_git_setup_usage() {
  local repo_dir config_base user_local user_local_example ssh_config_local

  repo_dir="$(remote_ssh_git_repo_dir)"
  config_base="${repo_dir}/dots/git/config.base"
  user_local="${repo_dir}/dots/git/user.local"
  user_local_example="${repo_dir}/dots/git/user.local.example"
  ssh_config_local="${repo_dir}/dots/ssh/config.local"

  cat <<EOF
Usage: remote-ssh git setup

Adds remote-ssh Git defaults to the global Git config via:
  include.path = ${config_base}

If ${user_local} does not exist, it is created from:
  ${user_local_example}

Also prepares SSH config includes for account-specific Git aliases:
  Include ${ssh_config_local}

In remote-ssh shells, ${user_local} is also used as a session Git identity
override. It does not write to per-repository .git/config files.
EOF
}

remote_ssh_git_setup() {
  local repo_dir config_base user_local user_local_example
  local ssh_config_dir ssh_config_local ssh_config_example
  local home_ssh_dir home_ssh_config include_line tmp_ssh_config

  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    remote_ssh_git_setup_usage
    return 0
  fi
  (($# == 0)) || {
    remote_ssh_git_setup_usage >&2
    return 1
  }

  repo_dir="$(remote_ssh_git_repo_dir)"
  config_base="${repo_dir}/dots/git/config.base"
  user_local="${repo_dir}/dots/git/user.local"
  user_local_example="${repo_dir}/dots/git/user.local.example"
  ssh_config_dir="${repo_dir}/dots/ssh"
  ssh_config_local="${ssh_config_dir}/config.local"
  ssh_config_example="${ssh_config_dir}/config.example"
  home_ssh_dir="${HOME}/.ssh"
  home_ssh_config="${home_ssh_dir}/config"

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required for remote-ssh git setup.\n' >&2
    return 1
  }

  [[ -r "$config_base" ]] || {
    printf '[ERROR] Missing config base: %s\n' "$config_base" >&2
    return 1
  }

  if [[ ! -e "$user_local" && -r "$user_local_example" ]]; then
    cp "$user_local_example" "$user_local"
    printf '[INFO] Created %s from example.\n' "$user_local" >&2
  fi

  if [[ ! -e "$ssh_config_local" && -r "$ssh_config_example" ]]; then
    mkdir -p "$ssh_config_dir"
    cp "$ssh_config_example" "$ssh_config_local"
    printf '[INFO] Created %s from example.\n' "$ssh_config_local" >&2
  fi

  if git config --global --get-all include.path 2>/dev/null | grep -Fxq "$config_base"; then
    printf '[INFO] Git include already present: %s\n' "$config_base" >&2
  else
    git config --global --add include.path "$config_base"
    printf '[INFO] Added Git include: %s\n' "$config_base" >&2
  fi

  if [[ -r "$ssh_config_local" ]]; then
    mkdir -p "$home_ssh_dir"
    chmod 700 "$home_ssh_dir" 2>/dev/null || true
    touch "$home_ssh_config"
    chmod 600 "$home_ssh_config" 2>/dev/null || true

    include_line="Include ${ssh_config_local}"
    if grep -Fxq "$include_line" "$home_ssh_config"; then
      printf '[INFO] SSH include already present: %s\n' "$ssh_config_local" >&2
    else
      tmp_ssh_config="$(mktemp "${home_ssh_config}.remote-ssh.XXXXXX")"
      printf '%s\n' "$include_line" >"$tmp_ssh_config"
      if [[ -s "$home_ssh_config" ]]; then
        printf '\n' >>"$tmp_ssh_config"
        cat "$home_ssh_config" >>"$tmp_ssh_config"
      fi
      cat "$tmp_ssh_config" >"$home_ssh_config"
      rm -f "$tmp_ssh_config"
      chmod 600 "$home_ssh_config" 2>/dev/null || true
      printf '[INFO] Added SSH include: %s\n' "$ssh_config_local" >&2
    fi
  fi

  printf 'remote-ssh git config is active.\n'
  printf 'Base config: %s\n' "$config_base"
  printf 'User overrides: %s\n' "$user_local"
  printf 'Session identity: enabled in remote-ssh shells when user overrides are set.\n'
  printf 'SSH aliases: %s\n' "$ssh_config_local"
  printf 'After editing SSH aliases, use remotes like:\n'
  printf '  git remote set-url origin git@github.com-myuser:OWNER/REPO.git\n'
}

remote_ssh_git_status_usage() {
  cat <<'EOF'
Usage: remote-ssh git status [ssh-host]

Shows the Git author config, origin remote, SSH agent state, and the SSH
account that will be used for Git operations.

If ssh-host is omitted, the command tries to infer it from origin.
EOF
}

remote_ssh_git_status_print_git_config_value() {
  local key="$1" value origin

  value="$(git config --get "$key" 2>/dev/null || true)"
  origin="$(git config --show-origin --get "$key" 2>/dev/null | sed 's/[[:space:]].*$//' || true)"

  if [[ -n "$value" ]]; then
    if [[ -n "$origin" ]]; then
      printf '  %-18s %s (%s)\n' "${key}:" "$value" "$origin"
    else
      printf '  %-18s %s\n' "${key}:" "$value"
    fi
  else
    printf '  %-18s [missing]\n' "${key}:"
  fi
}

remote_ssh_git_status_print_session_identity() {
  local count="${GIT_CONFIG_COUNT:-0}" i key_var value_var key value found

  printf '\nGit session override\n'
  printf '  %-18s %s\n' 'enabled:' "${REMOTE_SSH_GIT_SESSION_IDENTITY:-0}"
  printf '  %-18s %s\n' 'GIT_CONFIG_COUNT:' "$count"

  case "$count" in
    ''|*[!0-9]*) return 0 ;;
  esac

  found=0
  for ((i = 0; i < count; i++)); do
    key_var="GIT_CONFIG_KEY_${i}"
    value_var="GIT_CONFIG_VALUE_${i}"
    key="${!key_var:-}"
    value="${!value_var:-}"
    case "$key" in
      user.name|user.email|user.useConfigOnly)
        printf '  session %-10s %s\n' "${key#user.}:" "$value"
        found=1
        ;;
    esac
  done

  [[ "$found" -eq 1 ]] || printf '  %-18s [none]\n' 'session keys:'
}

remote_ssh_git_status_infer_ssh_host_from_remote() {
  local remote_url="$1"

  case "$remote_url" in
    git@*:*)
      printf '%s\n' "${remote_url#git@}" | sed 's/:.*$//'
      ;;
    ssh://git@*)
      printf '%s\n' "${remote_url#ssh://git@}" | sed 's/[/:].*$//'
      ;;
  esac
}

remote_ssh_git_status() {
  local ssh_host="${1:-}"
  local author_ident committer_ident origin_url ssh_add_output ssh_add_status
  local ssh_output ssh_status

  case "${1:-}" in
    -h|--help)
      remote_ssh_git_status_usage
      return 0
      ;;
  esac
  (($# <= 1)) || {
    remote_ssh_git_status_usage >&2
    return 1
  }

  command -v git >/dev/null 2>&1 || {
    printf '[ERROR] git is required.\n' >&2
    return 1
  }

  printf 'remote-ssh git status\n\n'

  printf 'Git config\n'
  remote_ssh_git_status_print_git_config_value user.name
  remote_ssh_git_status_print_git_config_value user.email
  remote_ssh_git_status_print_git_config_value user.useConfigOnly

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    author_ident="$(git var GIT_AUTHOR_IDENT 2>/dev/null || true)"
    committer_ident="$(git var GIT_COMMITTER_IDENT 2>/dev/null || true)"
    [[ -n "$author_ident" ]] && printf '  %-18s %s\n' 'author ident:' "$author_ident"
    [[ -n "$committer_ident" ]] && printf '  %-18s %s\n' 'committer ident:' "$committer_ident"
  else
    printf '  %-18s [not inside a Git work tree]\n' 'work tree:'
  fi

  remote_ssh_git_status_print_session_identity

  printf '\nGit remote\n'
  origin_url="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -n "$origin_url" ]]; then
    printf '  %-18s %s\n' 'origin:' "$origin_url"
  else
    printf '  %-18s [missing]\n' 'origin:'
  fi

  if [[ -z "$ssh_host" && -n "$origin_url" ]]; then
    ssh_host="$(remote_ssh_git_status_infer_ssh_host_from_remote "$origin_url")"
  fi

  if [[ -n "$ssh_host" ]]; then
    printf '  %-18s %s\n' 'ssh host:' "$ssh_host"
  else
    printf '  %-18s [missing; pass one, e.g. github.com-myuser]\n' 'ssh host:'
  fi

  printf '\nSSH agent\n'
  if [[ -n "${SSH_AUTH_SOCK:-}" ]]; then
    printf '  %-18s %s\n' 'SSH_AUTH_SOCK:' "$SSH_AUTH_SOCK"
  else
    printf '  %-18s [missing]\n' 'SSH_AUTH_SOCK:'
  fi

  if command -v ssh-add >/dev/null 2>&1; then
    set +e
    ssh_add_output="$(ssh-add -l 2>&1)"
    ssh_add_status=$?
    set -e
    if [[ "$ssh_add_status" -eq 0 ]]; then
      while IFS= read -r line; do
        [[ -n "$line" ]] && printf '  key:              %s\n' "$line"
      done <<<"$ssh_add_output"
    else
      printf '  %-18s %s\n' 'keys:' "$ssh_add_output"
    fi
  else
    printf '  %-18s [ssh-add not found]\n' 'keys:'
  fi

  if [[ -z "$ssh_host" ]]; then
    printf '\nSSH auth\n'
    printf '  %-18s [skipped]\n' 'status:'
    return 0
  fi

  printf '\nSSH auth\n'
  printf '  %-18s ssh -T git@%s\n' 'command:' "$ssh_host"

  set +e
  ssh_output="$(
    ssh -o BatchMode=yes -o ConnectTimeout=10 -T "git@${ssh_host}" 2>&1
  )"
  ssh_status=$?
  set -e

  if grep -qi 'successfully authenticated' <<<"$ssh_output"; then
    printf '  %-18s ok\n' 'status:'
  else
    printf '  %-18s exit %s\n' 'status:' "$ssh_status"
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] && printf '  output:           %s\n' "$line"
  done <<<"$ssh_output"
}

remote_ssh_git_main() {
  local subcommand="${1:-}"

  case "$subcommand" in
    ''|-h|--help)
      remote_ssh_git_usage
      ;;
    setup)
      shift
      remote_ssh_git_setup "$@"
      ;;
    status)
      shift
      remote_ssh_git_status "$@"
      ;;
    *)
      printf 'Unknown remote-ssh git command: %s\n' "$subcommand" >&2
      remote_ssh_git_usage >&2
      return 1
      ;;
  esac
}
