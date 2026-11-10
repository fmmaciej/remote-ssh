# Atuin Bash integration fixture

v18.24.6/atuin.bash assembles the exact upstream include guard and Bash
integration pinned by tools/defs/atuin.sh, using the initializer's
<include guard> && { <main script> } wrapper. The two source contents are
unchanged; their trailing whitespace is trimmed as in the upstream generator.

- Main source: https://github.com/atuinsh/atuin/blob/v18.24.6/crates/atuin/src/shell/atuin.bash
- Guard: https://github.com/atuinsh/atuin/blob/v18.24.6/crates/atuin/src/shell/atuin.bash.d/include-guard.bash
- Tag: v18.24.6
- Assembled SHA-256: 218292a6b25b40a2b63ca1696105abf123e5d12b38dc98136f5b895041afd2a2
- License: MIT; the upstream notice is retained in v18.24.6/LICENSE.

The fake CLI supplies binding flags and deterministic UUID/history responses,
including the new history start/end --hook arguments. Tests use this source
offline to exercise initialization, history ownership, hook arrays and Readline
bindings. The real CLI test additionally checks generated initialization and AI
suppression when REMOTE_SSH_TEST_ATUIN_BIN is provided.

When changing the pinned version, refresh the source, guard and license, then
update the hash and version assertions in test_atuin_lifecycle.py and
test_atuin_real.py. This fixture is developer-only data.
