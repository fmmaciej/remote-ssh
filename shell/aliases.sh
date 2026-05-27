# shellcheck shell=bash

ensure_this_file_sourced

alias rcrc='source "$REMOTE_SHELL_DIR/rc.sh"'

alias rhelp='remote-ssh guide'

alias rssh="cd ~/.local/share/remote-ssh"

alias l="ls"
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

if have eza; then
  alias ls="eza"
  alias ll="eza -alF --group-directories-first"
  alias la="eza -a --group-directories-first"
else
  alias ll="ls -alF"
  alias la="ls -A"
fi

if have nvim; then
  alias nvim='command nvim -u ${REMOTE_DOTS_DIR}/vimrc'
  alias vim='command nvim -u ${REMOTE_DOTS_DIR}/vimrc'
elif have vim; then
  alias vim='command vim -u ${REMOTE_DOTS_DIR}/vimrc'
fi

have ripgrep && alias rg="ripgrep"
have yazi && alias y="yazi"
have tmux && alias tmux='tmux -f "$REMOTE_DOTS_DIR/tmux.conf"'

alias f2='find . -mindepth 1 -maxdepth 2 -not -path "./.git*" -print'
