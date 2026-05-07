#!/usr/bin/env bash

test_checksum_manifest_contract() {
  log "tool checksum manifest"

  source_tool_libs

  # shellcheck disable=SC2329
  check_tool_checksums() {
    local _def="$1"
    local rec asset checksum asset_rec found

    for rec in "${CHECKSUMS[@]}"; do
      asset="${rec%%|*}"
      checksum="${rec#*|}"

      [[ $checksum =~ ^[0-9a-f]{64}$ ]] || {
        printf 'Invalid checksum for %s: %s\n' "$asset" "$checksum" >&2
        return 1
      }

      found=0
      for asset_rec in "${ASSETS[@]}"; do
        [[ ${asset_rec#*|} == "$asset" ]] || continue
        found=1
        break
      done

      ((found == 1)) || {
        printf 'Checksum references unknown asset: %s\n' "$asset" >&2
        return 1
      }
    done
  }

  with_each_tool_def check_tool_checksums
}

register_test test_checksum_manifest_contract
