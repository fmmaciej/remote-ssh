# shellcheck shell=bash

ensure_this_file_sourced

# Prefer skim in remote-ssh sessions; an explicit user selection still wins.
: "${NAVI_FINDER:=skim}"
export NAVI_FINDER

if [[ -d "$REMOTE_DOTS_DIR/navi/cheats" ]]; then
  case ":${NAVI_PATH:-}:" in
    *":$REMOTE_DOTS_DIR/navi/cheats:"*) ;;
    *)
      if [[ -n "${NAVI_PATH:-}" ]]; then
        export NAVI_PATH="$REMOTE_DOTS_DIR/navi/cheats:$NAVI_PATH"
      else
        export NAVI_PATH="$REMOTE_DOTS_DIR/navi/cheats"
      fi
      ;;
  esac
fi

if have navi; then
  navi() {
    "$REMOTE_SHELL_DIR/navi-bin/navi" "$@"
  }
  alias cheats='navi'
fi
