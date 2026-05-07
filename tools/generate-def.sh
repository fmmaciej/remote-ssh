#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$SCRIPT_DIR/lib/env.sh"

if [[ -f "$REPO_DIR/dev/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "$REPO_DIR/dev/.env"
  set +a
fi

# shellcheck source=/dev/null
. "$TOOLS_LIB_DIR/generate-def.lib.sh"

usage() {
  cat <<EOF >&2
Usage:
  $0 <owner>/<repo> [--tool <name>] [--tag <tag>]
  $0 <owner>/<repo> [--tool <name>] [--version <tag>]
  $0 <owner>/<repo> --list

Compatibility:
  $0 <owner>/<repo> <tool>
EOF
  exit 1
}

parse_args() {
  [[ $# -gt 0 ]] || usage

  repo=""
  tool=""
  tag=""
  list=0

  repo="$1"
  shift

  case "$repo" in
    -h | --help) usage ;;
    */*) ;;
    *)
      echo "ERROR: repo must be in owner/repo form: $repo" >&2
      usage
      ;;
  esac

  while (($# > 0)); do
    case "$1" in
      --tool)
        [[ $# -ge 2 ]] || {
          echo "ERROR: --tool requires a name" >&2
          usage
        }
        tool="$2"
        shift 2
        ;;
      --tag | --version)
        [[ $# -ge 2 ]] || {
          echo "ERROR: $1 requires a release tag" >&2
          usage
        }
        tag="$2"
        shift 2
        ;;
      --list)
        list=1
        shift
        ;;
      -h | --help)
        usage
        ;;
      --)
        shift
        break
        ;;
      -*)
        echo "ERROR: unknown option: $1" >&2
        usage
        ;;
      *)
        if [[ -n $tool ]]; then
          echo "ERROR: unexpected argument: $1" >&2
          usage
        fi
        tool="$1"
        shift
        ;;
    esac
  done

  (($# == 0)) || {
    echo "ERROR: unexpected argument: $1" >&2
    usage
  }

  tool="${tool:-$(infer_tool_name_from_repo "$repo")}"
}

main() {
  local repo tool tag list

  parse_args "$@"

  if ((list == 1)); then
    github_list_release_tags "$repo"
    return
  fi

  if [[ -n $tag ]]; then
    github_release_by_tag "$repo" "$tag"
  else
    github_latest_release "$repo"
  fi

  # echo "ASSETS count: ${#GITHUB_ASSETS[@]}" >&2
  # printf '  - [%s]\n' "${GITHUB_ASSETS[@]}" >&2

  tag_prefix_and_version "$GITHUB_TAG"

  detect_asset_prefix "$tool" "$VERSION" "${GITHUB_ASSETS[@]}"

  build_assets_from_assets "${GITHUB_ASSETS[@]}"
  build_checksums_from_emitted_assets
  render_defs "$tool" "$repo" "$GITHUB_TAG"
}

main "$@"
