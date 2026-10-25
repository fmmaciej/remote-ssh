# Atuin Bash integration fixture

`v18.14.1/atuin.bash` is the unmodified Bash integration from the Atuin version
pinned by `tools/defs/atuin.sh`.

- Source: https://github.com/atuinsh/atuin/blob/v18.14.1/crates/atuin/src/shell/atuin.bash
- Tag: `v18.14.1`
- SHA-256: `60dde7dd731f9963b19f313c9b44870b1b0a6836c38bf22e96134251cc834d5a`
- License: MIT; the upstream notice is retained in `v18.14.1/LICENSE`.

The fake CLI in the integration tests supplies the same binding flags as
`atuin init bash` and deterministic UUID/history responses. Tests use this
source offline, including its initialization guard, hook arrays, and Readline
bindings. It is developer-only data, never a remote runtime dependency.

When changing the pinned Atuin version, refresh the source and license here,
then update the source hash and version assertion in `test_atuin_lifecycle.py`.
