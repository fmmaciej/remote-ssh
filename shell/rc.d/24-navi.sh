# shellcheck shell=bash

ensure_this_file_sourced

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

have navi && alias cheats='navi'
