# Atuin simplification — independent initial audit

Date: 2026-11-01

Verdict: **FIX REQUIRED**

Repair rounds used: **0 / 2**

This auditor did not implement the change. Review baseline:
`/tmp/remote-ssh-atuin-before`, including its saved working-tree diff/status;
implementation delta: `/tmp/remote-ssh-atuin-implementation.diff`;
frozen 16-file manifest: `/tmp/remote-ssh-atuin-frozen-sha256.json`.
Existing skim and other unrelated working-tree changes are not findings.
No runtime, tests, vendor, fixture, or plan files were edited during this audit.

## Blocking findings

### A1 — P2: an existing `bind` alias prevents history setup, including disabled Atuin

Location: `shell/rc.d/23-atuin.sh:34`, inside the newly introduced
`remote_atuin_bash_init` definition.

An interactive user shell can legitimately contain:

```bash
alias bind='builtin bind'
```

Bash expands this alias while parsing the nested `bind() {` declaration. Both
Bash 3.2.57 and 5.3.20 report a syntax error at that declaration. Parsing stops
before the final backend selection and fallback binding. This happens even
when `REMOTE_SSH_ENABLE_ATUIN=0` or no Atuin executable exists, because the
function body must be parsed before those execution-time conditions matter.
`REMOTE_SSH_HISTORY_BACKEND` remains unset; the skim fallback is not finalized.
Subsequent full reloads encounter the same error.

Minimal isolated reproduction, using either Bash interpreter:

```bash
audit_home=$(mktemp -d)
env HOME="$audit_home" PATH=/usr/bin:/bin \
  REPO=/Users/fm/Programming/00_Other/remote-ssh \
  REMOTE_SSH_ENABLE_ATUIN=0 REMOTE_SSH_CONFIG=0 \
  REMOTE_SSH_UPDATE_CHECK=0 REMOTE_SSH_WELCOME=0 \
  REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY=0 \
  /bin/bash --noprofile --norc -ic '
alias bind="builtin bind"
. "$REPO/shell/rc.sh"
printf "backend=%s\n" "${REMOTE_SSH_HISTORY_BACKEND:-UNSET}"
'
```

Observed: a syntax error at line 34 and `backend=UNSET`. The same isolated
alias/disabled/absent-binary startup against the pre-change snapshot has no
syntax error. The snapshot used different lifecycle state variables, so its
lack of the new backend variable is not itself evidence of failure.

Expected contract: initial disabled/absent Atuin must select usable Bash/skim
or native fallback; pre-existing user shell configuration must not prevent
parsing the module. Make temporary interception safe in the presence of an
alias, preserving that alias, and cover disabled as well as eligible startup.

### A2 — P2: a readonly user `bind` function silently bypasses rollback isolation

Locations: `shell/rc.d/23-atuin.sh:34`, `:60`, `:61`, and `:78`.

The implementation assumes it can replace and then unset any existing `bind`
function. Bash permits a user function to be readonly. With such a function,
the attempted definition of the queue wrapper fails, but initialization
continues through the original user function. Upstream binding writes then
reach the parent's Readline maps immediately. The subsequent `unset -f bind`
and restore also fail; these errors are ignored. An init failure restores the
callback arrays and selects Bash, but the keys have already changed without
passing through either the queue or its subshell preflight.

This is a deterministic preflight bypass, distinct from a transient failure
after a successful preflight. It was reproduced on both Bash versions with
the unchanged pinned fixture followed by `false`, a failure form already used
by the regression suite. No `eval` or builtin fault injection is needed.

Isolated reproduction:

```bash
audit_root=$(mktemp -d)
mkdir -p "$audit_root/home" "$audit_root/bin"
cat > "$audit_root/bin/atuin" <<'CLI'
#!/bin/sh
case "$1" in
  init)
    printf '__atuin_bind_ctrl_r=false\n__atuin_bind_up_arrow=false\n'
    cat "$ATUIN_SOURCE"
    printf '\nfalse\n'
    ;;
  uuid) printf 'audit-session\n' ;;
esac
CLI
chmod +x "$audit_root/bin/atuin"
env HOME="$audit_root/home" PATH="$audit_root/bin:/usr/bin:/bin" \
  REPO=/Users/fm/Programming/00_Other/remote-ssh \
  ATUIN_SOURCE=/Users/fm/Programming/00_Other/remote-ssh/dev/tests/fixtures/atuin/v18.14.1/atuin.bash \
  REMOTE_SSH_CONFIG=0 REMOTE_SSH_UPDATE_CHECK=0 REMOTE_SSH_WELCOME=0 \
  REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY=0 \
  REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT=0 \
  /bin/bash --noprofile --norc -ic '
builtin bind -m emacs '\''"\C-x\C-_A0\a":"my-original"'\''
bind() { builtin bind "$@"; }
readonly -f bind
. "$REPO/shell/rc.sh"
printf "backend=%s\n" "$REMOTE_SSH_HISTORY_BACKEND"
builtin bind -m emacs -s | grep -E "my-original|A0"
'
```

Observed: readonly-function errors, `backend=bash`, and the user's macro
replaced by `"\C-x\C-_A0\C-g": ""`. `\C-g` is Readline's printed spelling
of the same BEL terminator as `\a`. Callback arrays and HISTFILE do recover;
that does not recover the overwritten key.

Expected contract: bounded failed-init rollback must preserve pre-existing
user bindings and functions. Verify interception is available before evaluating
code that writes keys; otherwise select clean startup fallback. The required
fix need not support changing a readonly function. This example concerns an
upstream private dispatch key, not the preserved Up/k/`/`/redo group, but those
private keys can already belong to the user and the startup rollback contract
does not exempt them.

## Four agreed requirements

| Requirement | Assessment |
| --- | --- |
| Select history backend once per Bash process | Implemented through the early request and final backend guards; initial success/fallback/reload behavior is well covered. A1 prevents reaching selection for a supported user shell configuration. |
| Ctrl-R is the only managed Atuin search shortcut | Normal initialization uses both disable flags plus `--disable-ai`, then explicit emacs and vi-insert Ctrl-R. ATUIN_NOBIND, external ownership, and normal Up/k/`/`/vi-command redo are preserved in the inspected path. |
| Disable automatic synchronization | `auto_sync = false`; obsolete sync frequency and up-search settings removed. Paths, manual sync capability and import remain. |
| Load bash-preexec only when needed, before Starship | Early selector skips disabled/missing/external Atuin, reuses an existing library, and precedes prompt initialization. A late Atuin failure may retain the library, as permitted by the plan. |

The major simplification is substantive: `23-atuin.sh` falls from 575 to 108
lines, with no equivalent lifecycle module moved elsewhere. Owned live
detach/reattach, pending-entry completion and prompt prologue machinery are
removed. Vendored bash-preexec, pinned Atuin source fixture, and tool definition
are byte-for-byte unchanged against the pre-change snapshot.

## Tests and evidence

- Independently reran the failed-init and real pinned CLI tests:
  **11 passed, 14 deselected**. This includes deterministic invalid keymaps,
  partial eval, explicit return, and missing helpers, on both Bash interpreters.
- An additional isolated successful-init probe verified Readline query calls
  are executed and an ordinary pre-existing `bind` function is restored on
  Bash 3.2 and 5.3. The missing cases are the alias and readonly attributes
  demonstrated above, rather than all user functions being mishandled.
- Independently reran `dev/verify_atuin_recording.py` with real pinned Atuin
  18.14.1 on Bash 3.2.57 and 5.3.20. Both passed: two isolated sessions share
  their DB, use distinct session IDs, retain cwd/nonempty host, complete
  toggle/reload commands with exit 7 and nonnegative duration, preserve `?`,
  and exercise `$?`. Audit outputs are
  `/tmp/atuin-audit-recording-bash32.json` and `...-bash53.json`.
- The inspected suite covers selection/freeze in both directions, explicit
  HISTFILE default/custom/empty/null, external ownership, real PTY Ctrl-R in
  emacs/vi insert, custom vi-command keypresses, import markers/retry, and
  prompt callback status/pipeline handling. Normal Up/k/`/`/redo preservation
  is primarily established by map assertions; this is accurately scoped.
- The full real CLI adds AI glue outside the unchanged `atuin.bash` fixture.
  The separate real-CLI test confirms `--disable-ai` suppresses it. This is a
  justified implementation adjustment to achieve the original single-shortcut
  contract, not an arbitrary feature addition.
- The coordinator reports the prior full diagnostic smoke at 1222 passed /
  30 skipped, and the final focused run at 174 passed / 4 skipped. The final
  frozen full smoke subsequently completed with **1228 passed / 30 skipped**,
  exit 0, in 384.93 seconds; Bash syntax, shellcheck, ruff and mypy were green.
  It was not duplicated by the auditor. The suite does not cover A1/A2.

## Nonblocking boundaries and measurement limitations

The queue/preflight mechanism correctly avoids parent key mutation for the
tested deterministic application failures when interception is actually in
effect. A separately injected `eval` function failing only the second managed
bind during parent replay reproduces the documented residual partial-key
state on both Bash versions. HISTFILE and callback arrays recover. No ordinary
runtime trigger for that parent-only failure was found: with normal builtin
behavior the same queued operations use the same inherited maps during
preflight/replay. This remains an explicit bounded-recovery limitation, not an
additional must-fix request for an absolute transaction guarantee. A2 differs:
it bypasses the preflight deterministically with ordinary Bash function
attributes and must be addressed.

All retained measurement source fingerprints were checked against the proper
before snapshot or current tree: no mismatches. Each of the four scenarios
has 15 recorded samples per interpreter; two warmups are declared but discarded
warmup timings are not retained. The final before/after series reuses the saved
baseline; an additional original pre-edit Bash 3.2 baseline is retained.

The wrapper uses the existing benchmark runner/scenario environment with fresh
isolated HOME/XDG data, fixed PATH, real pinned binary and disabled surrounding
network/welcome features. Each working-preseed case has a marker but starts
without a DB; each first-import case has one history line. This measures
startup with empty data and full generated CLI initialization, not only the
offline fixture. It does not demonstrate performance with large databases or
measure per-command recording latency. OS caches were not flushed, and serial
before/after ordering remains a noise source, as documented.

The reported working-preseed medians, 357.2 → 141.9 ms on Bash 3.2 and
363.0 → 149.3 ms on Bash 5.3, match the raw evidence. Disabled/absent movements
should be read with the spread; there is no universal timing guarantee.
The performance evidence remains useful despite the narrowly triggered startup
defects above.

## Disposition

**FIX REQUIRED for A1 and A2.** The normal startup-only design and its four
primary behavior changes otherwise follow the plan. Send these concrete
interception defects to a new planner, then let the implementer make the first
repair round and submit the result for another independent audit. No unrelated
skim work, vendor edits, pin changes, or broader lifecycle redesign is needed.
