# Flyline integration audit and commit proposal

Date: 2026-11-09. Scope: the current uncommitted remote-ssh integration,
its installer dependencies, and the already built R5 macOS arm64 library.
Repository HEAD: `34ff644314ab068631ad583949ae24df0cb43d44`.

**Result: fix three P2 findings and one P3 finding before preparing commits.**
The native editor qualification remains useful, but does not cover these
integration edge cases. This audit changed documentation/evidence only. It did
not fix implementation, stage files, create commits, push, create a release tag,
publish a Release, or enable a production tool definition.

## Confirmed findings

### F1 — P2: finalization misses an external Atuin initialized by a late hook

In [29-flyline.sh](../../shell/rc.d/29-flyline.sh), lines 71–75 use the
previously selected `REMOTE_SSH_HISTORY_BACKEND` to decide whether history is
external. The early selector and module 23 run before OS/host hooks; Flyline
finalization runs after them. An OS/host hook can therefore initialize external
Atuin after the cached backend has become `bash`.

The reproduction uses the actual local Atuin 18.14.1 initializer in an isolated
Darwin hook, with remote-ssh's Atuin toggle off. The hook reports
`__atuin_initialized=true`, yet finalization reports `active:managed` and history
`bash:true`. Flyline takes over the editor and selects its Bash/skim binding
path even though external Atuin has just installed its own history bindings.
The plan requires preserving external history ownership.

**Fix direction:** recheck actual ownership at finalization, distinguishing
remote-ssh's own successful Atuin initialization from an external initializer.
Cover both OS and host ordering without changing the once-per-process backend
selection or breaking managed Atuin's Flyline adapter.

Evidence: [native transcript](flyline-integration-audit-evidence/late-external-atuin.pty.txt)
and [startup fixture](flyline-integration-audit-evidence/late-external-atuin.rc.txt).

### F2 — P2: a disabled external Flyline builtin is re-enabled and reconfigured

In [29-flyline.sh](../../shell/rc.d/29-flyline.sh), lines 73–75 only inspect
`type -t flyline`. Bash does not report a disabled builtin through that lookup.
Disabling a dynamic builtin with `enable -n flyline` does not unload its library
or establish that remote-ssh owns it.

The native reproduction first loads R5 outside remote-ssh, selects its non-Vim
mode, and disables the command. `enable -a` still lists `enable -n flyline`,
while `type -t` is empty. Remote-ssh subsequently calls `enable -f` (Bash warns
`dynamic builtin already loaded`), reports `active:managed`, and reconfigures
the existing instance. This violates the external editor ownership guard.

**Fix direction:** detect disabled as well as enabled builtins with Bash builtin
introspection before loading. Keep function/alias detection, and do not treat
inherited `FLYLINE_*` environment strings alone as proof of a loaded editor.

Evidence: [native transcript](flyline-integration-audit-evidence/disabled-external-builtin.pty.txt)
and [startup fixture](flyline-integration-audit-evidence/disabled-external-builtin.rc.txt).

### F3 — P2: an unrelated `.active` file blocks ordinary binary uninstall

In [uninstall.sh](../../tools/lib/commands/uninstall.sh), lines 255–260
validate `$INSTALL_PREFIX/.active` before the requested tools are selected.
An existing ordinary file at that newly reserved location aborts even explicit
`remote-ssh uninstall --yes bat`, although no library is selected and Bat's
managed release/link are valid.

The current command exits 1 and preserves Bat. A control run that substitutes
only HEAD's uninstall facade, retaining the same current shared helpers and
equivalent isolated fixture, exits 0 and removes Bat. Both preserve the unrelated
`.active` file. This isolates the regression to the new uninstall guard.

**Fix direction:** scope validation to operations that need library-link
inspection, preserving conservative deletion and handling genuine inspection
failures. Add an ordinary binary uninstall regression with an unmanaged file
at `.active`; retain the invalid-library-directory safety tests.

Evidence: [current log](flyline-integration-audit-evidence/uninstall-current.log)
and [control log](flyline-integration-audit-evidence/uninstall-head-facade-control.log).

### F4 — P3: failed activation restores variable values but changes export flags

In [29-flyline.sh](../../shell/rc.d/29-flyline.sh), lines 79–80 save variable
existence and values. Lines 101–102 restore those values without their export
attributes. The loader and unload hook also modify these variables.

The native reproduction starts with an unexported `FLYLINE_LOAD_DIR` and exported
`FLYLINE_VERSION`, injects a settings failure, and observes the opposite export
flags after successful unloading. Values are preserved and Readline is selected,
but subsequent child processes receive a different environment.

**Fix direction:** preserve set/unset state, value, and export attributes for
both variables across failed loading/configuration. Test unset, empty, exported,
and unexported cases. Do not restore inherited marker values on successful
activation, where managed values are intentional.

Evidence: [native transcript](flyline-integration-audit-evidence/rollback-attributes.pty.txt)
and [startup fixture](flyline-integration-audit-evidence/rollback-attributes.rc.txt).

## Validation and limits

The [reproduction script](flyline-integration-audit-evidence/reproduce.py.txt)
ran locally with Bash 5.3.20 on macOS arm64, using the existing R5 library whose
SHA-256 is
`ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`.
It ran the real managed installer against a local archive fixture before each
PTY probe. All three native probes completed and reproduced their suspected
failure. Two uninstall runs establish F3's current/control behavior.
[Results](flyline-integration-audit-evidence/results.json) include exact states.
Recorded child resource counters are incidental, not performance measurements.

To repeat from the repository root with the same existing local prerequisites:

```bash
python3 dev/docs/flyline-integration-audit-evidence/reproduce.py.txt \
  --repo "$PWD" --output /private/tmp/flyline-audit-repeat
```

The script requires the ignored R5 payload under `dev/flyline/dist/`, Homebrew
Bash at `/opt/homebrew/bin/bash`, and the local Atuin path recorded in its source.
It creates/removes isolated temporary HOME/prefix/checkout directories. It does
not download anything or touch user startup files. The saved fixtures contain
temporary paths that no longer exist; the script recreates equivalent fixtures.
This is frozen audit evidence, not a newly passing feature regression suite.

The earlier full smoke result was **1467 passed, 30 skipped**, as recorded in the
[R5 integration record](flyline-fork-integration-record.md#checks-and-evidence).
Those tests did not cover these four scenarios. No implementation changed in
this audit, so the full smoke suite was not rerun. Once fixes are made, add the
missing focused regressions, rerun native lifecycle/ownership probes against
the same library, then run `just smoke`. No live asset checker was run.

Only local macOS validation is authorized. Linux ABI, weak remote host behavior,
other architectures, and SSH latency remain unverified. Publication remains
deferred; `tools/defs/flyline.sh` is absent and Flyline stays off by default.
The fork checkout at `/private/tmp/remote-ssh-flyline-build/fork-r5` is clean at
`d037c075ed30a61080873985ea2621d743ddfc64`; this audit used no network operations.

Reviewed source snapshots and evidence hashes are listed in the
[inventory](flyline-integration-audit-evidence/fingerprints.json). Historical
R1/R4/R5 evidence was not rewritten.

## Proposed commit boundaries

These are **review groups**, not created or staged commits. The current working
tree contains work predating Flyline. Taking all modified files in one commit
would combine independent changes. Some prerequisites and Flyline changes also
occupy the same files and adjacent hunks, so file selection alone is insufficient.

| Order | Proposed subject | Scope and dependencies |
| --- | --- | --- |
| A | `Make executable selection deterministic and honor explicit paths` | Earlier installer work: path/name validation, explicit `BINARY_PATH` state, exactly one valid candidate, safe source validation; executable tests and documentation. Independent of Flyline. |
| B | `Pin available upstream tool checksums` | Earlier checksum work: seven tool definitions, checksum coverage/exception contract and checksum documentation. Independent of A. |
| C | `Manage Bash builtin library releases` | New `bash-builtin` layout, exact library members/checksums/libc selection, child load probe, format-2 records, active links, management and generator support. Depends on A; include the F3 fix and regression here. |
| D | `Add opt-in Flyline session activation` | Runtime finalizer, configuration allowlist/guide, history adapter and lifecycle tests/docs. Depends on C; include F1, F2 and F4 fixes and regressions here. No production Flyline definition. |
| E | `Add pinned Flyline fork build and local qualification tools` | Developer build/pilot tools, source pins/patches, draft release packet, explicit startup benchmark and related tests/check wiring. Runtime integration depends on C/D for managed native probes. |
| F | `Record Flyline qualification and integration follow-ups` | Current plan, audit and R5 record/evidence; preserve separately labeled historical pilot evidence referenced by these records. Link from developer docs. Depends on the relevant sources/tools above. |

Group A owns the executable portions of `tools/lib/install-tool/defs.sh` and
`install.sh`: `install_tool_binary_path_valid`, `install_tool_binary_name_valid`,
`REMOTE_SSH_BINARY_PATH_EXPLICIT`, executable `install_binary_check_path`,
`find_binary_path_by_name`, and `install_binary` changes. Include the existing
changes in `test_install_binary.py`, `test_install_bundle.py`, and
`test_install_failures.py`, plus explicit-path/name tests in `test_tool_assets.py`
and the “Single-binary selection” section in `docs/tools.md`.

Group B owns checksum additions in `tools/defs/{bat,eza,fd,fzf,nu,nvim,zoxide}.sh`,
`docs/tool-checksums.md`, `CHECKSUM_EXCEPTIONS`/checksum-contract changes in
`test_tool_assets.py`, and the corresponding paragraph in `docs/tools.md`.

Group C owns the remaining library additions in `install-tool/{defs,install}.sh`,
including the readable-library mode in `install_binary_check_path`; changes in
`install-tool/{assets,download,main}.sh`, `common/{release,extract}.sh`,
`install/{install,tool_inventory}.sh`, commands `{tool_status,prune,uninstall}.sh`,
`tools/generate-def.sh`, `generate-def/render.sh`, `dev/check_assets_live.py`,
`test_install_library.py`, `test_generate_def.py`, and the exact-libc test in
`test_tool_assets.py`. Include the library contract sections in `AGENTS.md` and
`docs/tools.md`. The shared source hunks must be split from A rather than copied
wholesale into both commits.

Group D owns `shell/rc.d/29-flyline.sh`, `shell/rc.sh`,
`shell/config/entries.sh`, `tools/lib/commands/guide/sections.sh`,
`test_flyline_lifecycle.py`, the Flyline config test delta, and the related
`docs/{install,shell}.md`, `docs/shell/{config,helpers,flyline}.md`, and
`shell/rc.d/README.md` documentation.

Group E owns `dev/flyline/` excluding ignored `dist/`,
`test_flyline_candidate.py`, `.gitignore`'s payload rule, `dev/{smoke.sh,justfile}`,
`dev/bench/scenarios.py`, its startup test delta and `dev/docs/bench-shell.md`.
The six patches and legacy `inputs.json` remain required by the existing source
preparation tests; `fork.json` pins the current build path.
Several native tools import `benchmark.py` from
`dev/docs/interactive-tools-performance-evidence/`, and completion probes import
`compare.py` from `dev/docs/completion-provider-pilot-evidence/`. Include both
helper modules with E, or deliberately relocate/update imports before splitting.
Do not commit tools while leaving their imports only in untracked evidence.

Group F should include the historical files actually linked by its records,
including frozen source snapshots used by evidence inventories. Keep binary
payloads out of Git. The old performance/provider comparison reports and the
Carapace implementation plan can be an additional, independent documentation
commit; their existence does not mean the Carapace runtime is implemented.

`dev/README.md`, `docs/TODO.md`, `docs/tools.md`, and `test_tool_assets.py`
contain mixed-purpose edits. Select their relevant paragraphs/tests separately.
Keep `docs/multi-agent-workflow.md`, `docs/plans/`, unrelated TODO reorganization,
and other pre-existing work outside the Flyline groups. Before making real
commits, verify each cumulative state in an isolated checkout and check local
documentation links; current combined-tree tests do not prove each proposed
boundary is self-contained.

## Next action

Fix F1–F4 with targeted regressions, then validate the cumulative groups above.
Keep Release publication and production manifest promotion deferred. Creating
or pushing commits is outside this audit's authorized scope.
