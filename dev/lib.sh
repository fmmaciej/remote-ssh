#!/usr/bin/env bash
# shellcheck shell=bash

dev_log() {
  printf '[%s] %s\n' "${DEV_LOG_PREFIX:-dev}" "$*" >&2
}

dev_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required developer command: %s\n' "$1" >&2
    return 1
  }
}
