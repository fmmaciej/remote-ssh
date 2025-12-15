# shellcheck shell=bash

ensure_this_file_sourced

# get_latest_github_tag <owner/repo>
# Input:  repo ("owner/repo")
# Output: echoes latest release tag_name (string), empty on parse failure.
get_latest_github_tag() {
  local repo="$1"
  local addr="https://api.github.com/repos/${repo}/releases/latest"

  curl -fsS "$addr" \
      | sed -n 's@.*"tag_name":[[:space:]]*"\([^"]*\)".*@\1@p'
}

# github_fetch_latest_json <owner/repo>
# Input:  repo ("owner/repo")
# Output: echoes raw JSON response from GitHub Releases API (latest).
github_fetch_latest_json() {
  local repo="${1:?repo required}"
  local api="https://api.github.com/repos/${repo}/releases/latest"

  fetch_json "$api"
}

# github_parse_tag_name <json>
# Input:  JSON string
# Output: echoes tag_name (e.g. "v1.2.3"), empty if not found.
github_parse_tag_name() {
  local json="${1:?json required}"

  printf '%s\n' "$json" \
    | sed -n 's@.*"tag_name":[[:space:]]*"\([^"]*\)".*@\1@p' \
    | head -n1
}

# github_parse_asset_names <json>
# Input:  JSON string
# Output: echoes one asset "name" per line (non-empty).
# Notes:  heuristic parser; good enough for GitHub API "assets[].name".
github_parse_asset_names() {
  local json="${1:?json required}"

  printf '%s\n' "$json" \
    | tr ',' '\n' \
    | sed -n 's@.*"name":[[:space:]]*"\([^"]*\)".*@\1@p' \
    | sed '/^$/d'
}

# github_latest_release <owner/repo>
# Input:  repo ("owner/repo")
# Output: echoes tag_name; sets globals: GITHUB_TAG (string), GITHUB_ASSETS (array of asset names).
# Errors: returns non-zero if tag or assets cannot be parsed / are empty.
github_latest_release() {
  local repo="${1:?repo required}"
  local json tag

  json="$(github_fetch_latest_json "$repo")" || return 1

  tag="$(github_parse_tag_name "$json")"
  [[ -n "$tag" ]] || { echo "ERROR: cannot read tag_name from GitHub API" >&2; return 1; }

  # shellcheck disable=SC2034
  GITHUB_TAG="$tag"
  GITHUB_ASSETS=()

  while IFS= read -r line; do
    [[ -n "$line" ]] && GITHUB_ASSETS+=("$line")
  done < <(github_parse_asset_names "$json")

  ((${#GITHUB_ASSETS[@]} > 0)) || { echo "ERROR: no assets in latest release" >&2; return 1; }
}
