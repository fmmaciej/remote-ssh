# shellcheck shell=bash

ensure_this_file_sourced

have git || return 0

remote_git_config_add pull.rebase true
remote_git_config_add rebase.autoStash true
remote_git_config_add fetch.prune true
remote_git_config_add push.autoSetupRemote true
remote_git_config_add init.defaultBranch main
remote_git_config_add core.editor "${EDITOR:-vim}"
