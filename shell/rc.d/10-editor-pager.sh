# shellcheck shell=bash

ensure_this_file_sourced

if have nvim; then
  export EDITOR="nvim"
elif have vim; then
  export EDITOR="vim"
else
  export EDITOR="vi"
fi

if have bat; then
  export PAGER="bat"
else
  export PAGER="less"
fi
