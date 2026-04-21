# shellcheck shell=bash

ensure_this_file_sourced

if have nvim; then
  export EDITOR="nvim"
  export VISUAL="nvim"
elif have vim; then
  export EDITOR="vim"
  export VISUAL="vim"
else
  unset EDITOR
  unset VISUAL

  case $- in
    *i*)
      if [[ -z "${REMOTE_SSH_EDITOR_WARNED:-}" ]]; then
        printf '[WARN] No vim/nvim found in PATH. Install one manually if you want an editor.\n' >&2
        export REMOTE_SSH_EDITOR_WARNED=1
      fi
      ;;
  esac
fi

if have bat; then
  export PAGER="bat"
else
  export PAGER="less"
fi
