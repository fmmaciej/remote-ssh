# shellcheck shell=bash
# shellcheck disable=SC2154

ensure_this_file_sourced

remote_log_usage() {
  cat <<'EOF' >&2
Usage:
  command 2>&1 | log [--append] [file.log]
  logrun [--append] [--output file.log] command [arg ...]

Notes:
  log reads stdin. It cannot capture stderr unless the caller redirects it.
  logrun runs the command and captures both stdout and stderr.
EOF
}

remote_log_default_file() {
  printf 'log-%s.log\n' "$(date +%Y%m%d-%H%M%S)"
}

remote_log_prepare_file() {
  local file="$1"
  local dir="${file%/*}"

  if [[ $dir != "$file" ]]; then
    mkdir -p "$dir" || return
  fi
}

remote_log_sink() {
  local file="$1" append="$2"

  remote_log_prepare_file "$file" || return

  if have tspin; then
    if [[ $append == 1 ]]; then
      tee -a "$file" | tspin
    else
      tee "$file" | tspin
    fi
  else
    if [[ $append == 1 ]]; then
      tee -a "$file"
    else
      tee "$file"
    fi
  fi
}

log() {
  local append=0 file=""

  while (($# > 0)); do
    case "$1" in
      -a | --append)
        append=1
        shift
        ;;
      -h | --help)
        remote_log_usage
        return 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        printf 'log: unknown option: %s\n' "$1" >&2
        remote_log_usage
        return 2
        ;;
      *)
        file="$1"
        shift
        break
        ;;
    esac
  done

  if (($# > 0)); then
    printf 'log: expected at most one file path\n' >&2
    remote_log_usage
    return 2
  fi

  file="${file:-$(remote_log_default_file)}"
  remote_log_sink "$file" "$append"
}

logrun() {
  local append=0 file=""

  while (($# > 0)); do
    case "$1" in
      -a | --append)
        append=1
        shift
        ;;
      -o | --output)
        if (($# < 2)); then
          printf 'logrun: --output requires a file path\n' >&2
          return 2
        fi
        file="$2"
        shift 2
        ;;
      -h | --help)
        remote_log_usage
        return 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        printf 'logrun: unknown option: %s\n' "$1" >&2
        remote_log_usage
        return 2
        ;;
      *)
        break
        ;;
    esac
  done

  if (($# == 0)); then
    printf 'logrun: command is required\n' >&2
    remote_log_usage
    return 2
  fi

  file="${file:-${1##*/}.log}"
  remote_log_prepare_file "$file" || return

  if have tspin; then
    if [[ $append == 1 ]]; then
      "$@" 2>&1 | tee -a "$file" | tspin
    else
      "$@" 2>&1 | tee "$file" | tspin
    fi
  else
    if [[ $append == 1 ]]; then
      "$@" 2>&1 | tee -a "$file"
    else
      "$@" 2>&1 | tee "$file"
    fi
  fi

  local bash_status="${PIPESTATUS[0]:-0}" zsh_status="${pipestatus[1]:-0}"

  if [[ -n ${BASH_VERSION:-} ]]; then
    return "$bash_status"
  fi
  if [[ -n ${ZSH_VERSION:-} ]]; then
    return "$zsh_status"
  fi
  return "$bash_status"
}
