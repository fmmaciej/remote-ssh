# shellcheck shell=bash

ensure_this_file_sourced

alias rcrc='source "$REMOTE_SHELL_DIR/rc.sh"'

alias l="ls"

if have eza; then
  alias ls="eza"
  alias ll="eza -alF --group-directories-first"
  alias la="eza -a --group-directories-first"
else
  alias ll="ls -alF"
  alias la="ls -A"
fi

if have ripgrep; then
  alias rg="ripgrep"
fi

if have bat; then
  alias cat="bat"
fi

if have zoxide; then
  # bash, potem zsh; jak oba zawiodą, nie krzycz.
  eval "$(zoxide init bash 2>/dev/null || zoxide init zsh 2>/dev/null || true)"
fi

if have btop; then
  alias top="btop"
fi

alias f2='find . -mindepth 1 -maxdepth 2 -not -path "./.git*" -print'
