# shellcheck shell=bash
# shellcheck disable=SC2034

ensure_this_file_sourced

build_checksums_from_assets() {
  local selected=("$@")
  CHECKSUMS_EMIT=()

  if ! declare -p GITHUB_ASSET_DIGESTS >/dev/null 2>&1; then
    return 0
  fi
  ((${#GITHUB_ASSET_DIGESTS[@]} > 0)) || return 0

  local rec asset digest selected_asset
  for rec in "${GITHUB_ASSET_DIGESTS[@]}"; do
    asset="${rec%%|*}"
    digest="${rec#*|}"

    for selected_asset in "${selected[@]}"; do
      [[ $asset == "$selected_asset" ]] || continue
      CHECKSUMS_EMIT+=("\"${asset}|${digest}\"")
      break
    done
  done
}

build_checksums_from_emitted_assets() {
  local selected=()
  local rec

  for rec in "${ASSETS_EMIT[@]}"; do
    rec="${rec%\"}"
    rec="${rec#\"}"
    selected+=("${rec#*|}")
  done

  build_checksums_from_assets "${selected[@]}"
}
