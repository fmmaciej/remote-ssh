#!/usr/bin/env bash

test_starship_help_explains_git_status_symbols() {
  log "starship-help explains Git status symbols"

  local got
  got="$(
    HOME=/tmp/starship-help-test \
      REMOTE_ENV_DIR=/opt/remote-ssh \
      REMOTE_DOTS_DIR=/opt/remote-ssh/dots \
      bash "$REPO_DIR/bin/starship-help"
  )"

  grep -Fxq 'remote-ssh Starship prompt' <<<"$got"
  grep -Fxq '  git::<branch>          Current branch' <<<"$got"
  grep -Fxq '  [!]                    Merge conflict' <<<"$got"
  grep -Fxq '  [+]                    Staged changes' <<<"$got"
  grep -Fxq '  [~]                    Modified tracked files' <<<"$got"
  grep -Fxq '  [?]                    Untracked files' <<<"$got"
  grep -Fxq '  [$]                    Stashed changes' <<<"$got"
  grep -Fxq '  [<>A/B]                Local branch has A ahead and B behind commits' <<<"$got"
  grep -Fxq '  /opt/remote-ssh/dots/starship.toml' <<<"$got"
  grep -Fxq '  starship explain' <<<"$got"
}

register_test test_starship_help_explains_git_status_symbols
