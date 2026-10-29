# Install CLI addendum: explicit tool-batch failure propagation

Status: proposed for independent plan audit before editing the additional helper.
The accepted implementation plan and its R0 audit remain unchanged.

## Reason and verified source dependency

The approved plan requires explicit failure propagation from the install facade
and no configuration/success footer after tool installation fails. In
`tools/lib/install/install.sh`, `install_tools` currently runs an unguarded
`mkdir -p` followed by a loop of unguarded `install_tool` calls. If invoked as
`install_tools ... || return 1`, Bash suppresses errexit inside the function.
A failed early tool can therefore be followed by a successful tool, producing
a successful batch result; directory preparation failure can also be ignored.

The in-progress facade uses one `install_tools` invocation per tool to stop
after a failure. This changes the existing single-batch interaction, including
the stubs in `dev/tests/test_install_expected_tools.py` that capture the full
argument list with `>` and would retain only the final call. Fix the batch
helper itself and retain the single-batch facade call. Do not rewrite those
existing stubs to accommodate a different interaction.

## Narrow scope and intended behavior

Extend the implementer's ownership by exactly one runtime file:
`tools/lib/install/install.sh`, limited to `install_tools`.

- Guard `mkdir -p "$INSTALL_PREFIX" "$INSTALL_BIN_DIR"` with `|| return 1`.
- Guard every `install_tool "$t"` inside the existing ordered loop with
  `|| return 1`. Stop immediately; do not start subsequent tools.
- Keep one facade invocation with the complete selected array:
  `install_tools ... || return 1`, using the existing Bash 3.2-safe expansion.
- Successful batches retain their order and behavior. Failed batches return
  nonzero explicitly even in conditional contexts. Do not change selection,
  confirmation, staging, per-tool diagnostics, or public CLI options.
- On failure, already completed tools remain installed. Skip environment
  preparation, expected-tools writes, and success/footer output. The CLI link
  published earlier remains available for diagnosis and retry. Do not add
  rollback or batch transactions.

This is a correction needed to implement the approved error-handling contract,
not a new feature or permission to refactor adjacent helpers. Preserve all
other worktree changes and accepted scope boundaries.

## Required evidence and audit

Add focused regression cases in the already-owned
`dev/tests/test_install_cli.py`. Use isolated temporary HOME/XDG/checkouts and
an ordered three-tool fixture. Record each tool-install attempt and make the
first tool, then the middle tool, fail in separate cases. Exercise the real
facade and real `install_tools` through the guarded call on Bash 3.2 and 5.x.
Assert nonzero status, exact attempted prefix of the selected list, no later
attempt, no post-tool configuration/preparation marker, no expected-tools
creation or modification, and no completion footer. The published CLI must
remain present and execute help. In the middle-failure case, preserve the first
tool's successful installation.

Also cover directory preparation failure with an invalid temporary
`INSTALL_PREFIX` while the CLI bin directory is valid: no tool starts, no
configuration/footer follows, and the published CLI remains usable. Keep the
existing full-array expected-tools tests passing without changing their batch
stubs. Include these cases in the final required `just smoke` and record both
interpreter versions and results in implementation evidence.

The coordinator and an independent plan auditor must accept this addendum
before the added helper edit. The fresh implementation audit must assess this
helper and its evidence alongside the approved plan. Existing audit/repair
round limits and restrictions on real-HOME installs, network/live checks,
staging, commits, and publication still apply. No runtime test was run to
prepare this addendum.
