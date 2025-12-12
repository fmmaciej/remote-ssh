# shellcheck shell=bash

ensure_this_file_sourced

if have fzf; then
  : "${FZF_DEFAULT_OPTS:=--height=40% --reverse --border}"
  export FZF_DEFAULT_OPTS
fi
