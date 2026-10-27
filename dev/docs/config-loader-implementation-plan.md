# Config Loader Implementation Plan

Created: 2026-10-27
Status: implemented and independently audited; see the implementation record
Plan review: ACCEPTED at initial independent audit (R0); no repair rounds required
Fresh implementation re-audit: R0-F1 repaired and independently ACCEPTED at R1

Back: [Developer tooling](../README.md)
Related: [Startup benchmark](bench-shell.md),
[deferred optimization notes](../todo-bench.md),
[runtime config contract](../../docs/shell/config.md),
[independent plan audit](config-loader-plan-audit.md),
[implementation record](config-loader-implementation-record.md),
[initial implementation audit](config-loader-implementation-audit.md),
[fresh behavior re-audit](config-loader-independent-reaudit.md),
[independent performance verification](config-loader-reaudit-performance.md),
[repair plan](config-loader-repair-plan.md)

## Goal and boundary

Reduce configuration work performed by `shell/env.sh` before the shell hooks
start. Read the optional runtime config once per `remote_ssh_config_load`, keep
the parsed values only for that invocation, and remove command substitutions
from per-line parsing and per-key ownership bookkeeping.

Implement this in two measurable stages: first the parser and load flow, then
marker operations. Preserve Bash 3.2 and modern Bash, including callers using
`set -euo pipefail`. Do not add runtime dependencies, a persistent cache, new
configuration syntax, new validation rules, or a general shell-startup refactor.
Welcome, Atuin, tool installation, and the abandoned archive proposal are outside
this work. This document authorizes no runtime edits by its author.

## Current flow and compatibility boundary

`shell/rc.sh` sources `shell/env.sh`, which sources `shell/config.lib.sh` and
calls `remote_ssh_config_load`. The loader iterates over the nine entries emitted
by `remote_ssh_config_entries`. For each key it calls
`remote_ssh_config_file_value_raw` through command substitution; that lookup
resolves and rereads the file, trims each line and key through more command
substitutions, and reconstructs the allowlist for candidate assignments.
Ownership helpers also build marker names through nested command substitutions.

The loader exports only values found in the file; it does not assign defaults.
Defaults remain with consumers and the guide. Preserve these existing rules:

| Situation | Required result |
| --- | --- |
| Nonempty XDG config directory | Use its `remote-ssh/config`; otherwise fall back to nonempty HOME. |
| Neither directory available, missing/unreadable file, or no accepted entry | Treat the corresponding key as absent, without a new startup error. |
| Config disabled by `0`, `false`, `no`, or `off` | Do not inspect the config file; release only still-owned values and clear canonical markers. Other spellings and an empty toggle retain current behavior. |
| Existing shell variable, including an empty string | It wins unless current canonical markers prove that this exact value is config-owned. |
| Owned value and new file entry | Replace and export the value; update both exported markers. |
| Owned value and removed entry/file, or disabled config | Unset the value and clear its canonical markers. |
| Manually changed value | Preserve it and clear canonical markers, including when the file disappears or config is disabled. |
| Manual assignment of the same value as the recorded loaded value | It remains owned, as today; do not invent a way to distinguish this assignment. |
| Stale/incomplete/legacy markers | They do not establish ownership; preserve the existing variable as an environment value and clear canonical markers. Do not add cleanup of legacy marker names. |

Parsing remains literal: trim surrounding `[[:space:]]` from the physical line,
ignore empty lines and lines beginning with `#` after that trim, require `=`,
split at its first occurrence, trim the key and value, and remove one matched
pair of outer single or double quotes from the value. Do not trim again after
unquoting. An inline `#`, further `=`, backslashes, dollar signs, backticks,
unmatched/mixed quotes, and whitespace inside matched quotes remain literal.
Ignore unknown keys and shell-like `export KEY=...` lines. The last accepted
entry wins, even when its value is empty. Retain the final physical line without
a trailing LF. Do not `source` or `eval` the config, perform shell expansion, or
add multiline/escape interpretation.

## Stage A: one invocation-local snapshot

### Storage and helper boundaries

Keep `remote_ssh_config_entries` in `shell/config/entries.sh` as the only
allowlist/default definition. Do not repeat its nine key names in the parser,
loader, or a second runtime table. Its public stdout format and
`remote_ssh_config_key_allowed` stay available.

In `shell/config/parse.sh`, add two private helpers with an explicit, documented
caller-local output contract:

- `remote_ssh_config_snapshot_init` initializes indexed arrays named
  `__remote_ssh_config_snapshot_keys`, `__remote_ssh_config_snapshot_values`, and
  `__remote_ssh_config_snapshot_present`, plus scalar
  `__remote_ssh_config_snapshot_count`. Read `remote_ssh_config_entries` once
  through the existing process-substitution pattern, recording keys in order;
  initialize each value to `''` and presence to `0`.
- `remote_ssh_config_snapshot_read` resolves the path once with the existing
  `remote_ssh_config_file` API, then uses one redirected
  `while IFS= read -r ... || [[ -n ... ]]` loop to scan it. Trim and unquote by
  Bash parameter expansion in the same process. Find an allowed key by comparing
  against the in-memory keys, using a bounded numeric index, then replace that
  slot's value and set its presence to `1`. Do not call
  `remote_ssh_config_key_allowed` for each line: that would regenerate the table.

The path lookup may retain one command substitution per invocation, and
allowlist enumeration may retain one process substitution per invocation. The
performance requirement concerns repeated config reads and per-line/per-key
subprocesses, not removal of all constant library-load work.

Use no associative arrays, namerefs, `mapfile`, external parser, serialized
key/value delimiter, or data-derived arithmetic subscript. Values containing
`|`, `=`, whitespace, or quotes must remain strings in array slots. Presence is
independent of content: `present[index]=1` with `values[index]=''` is a configured
empty value, whereas `present[index]=0` is absence.

Both `remote_ssh_config_load` and the single-key compatibility lookup declare
these arrays locally before calling the helpers. The helpers intentionally write
those dynamically scoped locals; they must never redeclare the four output
names. All helper scratch variables use distinct private names such as
`__remote_ssh_config_scan_line` and `__remote_ssh_config_init_index`, never generic
`key`, `value`, or an output variable's name. This avoids shadowing output slots
or caller variables in Bash's dynamic scope. There is no general arbitrary-name
output parameter or global snapshot. Add a concise comment documenting this
contract next to the helpers.

Initialize arrays and count explicitly. Iterate using the scalar count and
only slots initialized by `snapshot_init`, avoiding empty-array expansion under
Bash 3.2 `nounset`. Use assignment-form counter increments, not a bare
`((index++))` whose initial status can trip `errexit`. End successful helpers
and loads explicitly with status zero. Guard path/readability/open failures so
they leave absent slots and do not abort `set -e` callers; retain existing benign
lookup diagnostic suppression. Do not introduce an all-or-nothing parse error
policy: process successfully read physical lines just as the current parser does.

### Applying the snapshot

In `shell/config/load.sh`:

1. Declare and initialize the caller-local snapshot, then enumerate entries once.
2. If enabled, read the file into it; if disabled, skip path resolution and file
   I/O entirely, leaving all presence flags zero.
3. Iterate over the stored keys in their existing order. For each key use the
   presence flag and the existing ownership predicate, applying the table above.
   For a present value, distinguish unset from set-but-empty with `${!key+x}`,
   not `${!key:-}`. Export accepted values before marking ownership.
4. Let the locals disappear on return. Every later load, including `rcrc`,
   creates a fresh snapshot and sees current file contents.

Do not call the single-key file lookup from this loop. A present snapshot entry
does not itself establish ownership of an existing shell value.

### Compatibility APIs and guide

Reimplement `remote_ssh_config_file_value_raw <key>` using its own local
snapshot and the shared reader. It remains an on-demand, read-only lookup:
stdout is the final value plus LF with status zero for a found key, including
an empty value; a missing/unknown key returns nonzero without a value. It
ignores the config-enabled toggle, as today. `remote_ssh_config_file_value`
continues to enforce that toggle before delegating. Keep the existing stdout
interfaces of `remote_ssh_config_trim` and `remote_ssh_config_unquote` available;
the hot read loop no longer uses command substitution to call them.

`tools/lib/commands/guide/sections.sh` can stay unchanged. Its current calls to
the raw/gated lookups and current-ownership predicate must continue to work,
including the distinction between `[env]`, `[config]`, and `[default]` when the
file changes after startup. The one-file-read guarantee is per loader call;
optimizing the guide's separate per-key reporting is outside this change.

## Stage B: marker operations in the current shell

In `shell/config/markers.sh`, derive the suffix using `${1#REMOTE_SSH_}` and
construct canonical source/loaded variable names by ordinary local assignment
inside each marker operation. This produces the current `WELCOME_USER` suffix
and leaves `NO_COLOR` intact. Use private scratch names that cannot coincide
with any allowlisted setting or marker. There is no output-parameter helper
that can shadow a caller's `value` or require a nested command substitution.

Keep stdout APIs (`marker_key`, `source_var`, `loaded_value_var`, `source`, and
`loaded_value`) and their existing return behavior, but compute names directly.
Hot `mark_owned`, `clear_source`, and ownership checks use local assignments
and indirect expansions, never `$(...)`. Preserve the exported canonical names
and values exactly: `REMOTE_SSH_CONFIG_SOURCE_<suffix>=config` and
`REMOTE_SSH_CONFIG_LOADED_VALUE_<suffix>=<value>`.

Ownership still requires all three facts: the setting is set, canonical source
is `config`, and a loaded-value marker is set and equals the current setting.
The marker's presence check must accept an empty loaded value. Export markers
when marking ownership so a child `remote-ssh guide config` process can report
provenance. Unset both canonical markers when clearing; retain the existing
`remote_ssh_config_value_is_owned` alias.

## Files and implementation sequence

| File | Planned work |
| --- | --- |
| `shell/config/parse.sh` | Snapshot initialization/read helpers; reuse them behind existing single-key APIs. |
| `shell/config/load.sh` | Read once, apply per-key state machine from local arrays; disabled path has no file I/O. |
| `shell/config/markers.sh` | Replace nested name-building substitutions with current-shell assignments. |
| `dev/tests/test_welcome.py` | Focused parser, lifecycle, environment, and child-process regression coverage. |
| `dev/tests/test_guide.py` | Preserve reporting and provenance across the compatibility APIs and reload. |
| This plan and `dev/docs/bench-shell.md` | Record actual verification, measurement procedure, and before/after results after implementation. |

Keep `entries.sh`, `path.sh`, `config.lib.sh`, `env.sh`, and the guide call sites
unchanged unless a demonstrated compatibility failure requires a narrowly
documented adjustment. No other runtime modules or public command behavior
need to change. Do not edit the unrelated archive-plan changes already present
in the worktree.

1. Add missing behavior tests, confirm their expected results on the existing
   runtime, and capture baseline measurements. Some parser/ownership cases
   already exist; extend those cases rather than multiplying equivalent tests.
2. Implement Stage A, run the focused config tests on both Bash versions, and
   measure again before touching marker operations.
3. Implement Stage B, repeat focused verification and measurements, then inspect
   the combined diff for parser and ownership equivalence.
4. Run `just smoke` once after both stages pass, check Bash 3.2 syntax and
   `git diff --check`, verify local documentation links, and record the results.
   Do not run `just test-assets-live`.

## Behavioral verification

Use the existing `runtime_bash` fixture for focused cases on `/bin/bash` and
the discovered modern Bash; invoke that interpreter explicitly rather than
assuming `bash` in the test runner's PATH is modern. Where an integration case
spawns `#!/usr/bin/env bash` children, put a symlink to the chosen interpreter
in the isolated test bin directory. Sanitize inherited `REMOTE_SSH_*` and
`NO_COLOR` settings/markers when testing defaults. Run direct loader cases with
`set -euo pipefail`, asserting normal return status as well as values, set/unset
state, exported values, and canonical marker state.

Add or extend these behavior groups:

- Parsing: a single fixture with all emitted keys, duplicates ending in an empty
  value, comments/blank/malformed/unknown lines, first-`=` splitting, outer
  whitespace (including tabs and CRLF), matched/mismatched quotes, quoted inner
  whitespace, and the final line without LF. Probe literal `$()` and backticks
  with a sentinel file to prove no execution; include literal `|`, `#`, and
  backslashes. Compare raw/gated single-key lookup status and output, including
  found-empty versus missing/unknown and disabled-raw versus disabled-gated.
- Locations and availability: XDG precedence, HOME fallback, neither directory
  set, absent and empty files, and deterministic unreadability/open failure.
  Tests running as a privileged user must not claim unreadability from chmod
  alone; skip that case or use a reliably unavailable path.
- Precedence: preexisting nonempty and empty values remain untouched, while
  initially unset settings load correctly. Defaults are never exported by the
  loader. Include `NO_COLOR`, whose marker suffix differs from the prefixed keys.
- Lifecycle in one process: initial load, changed file, changed-to-empty,
  unchanged reload, removed option, removed file, disable/re-enable, and repeated
  cycles. Assert owned values disappear, while manually changed values (also
  changed to empty) survive and lose canonical markers. An identically assigned
  value keeps current ownership behavior. Include manually unset settings so a
  remaining entry can be loaded again.
- Ownership/export: canonical source without loaded value, loaded value without
  source, mismatched value, unrelated/legacy markers, and a valid empty marker.
  Start a child shell after loading; verify exported values and markers, reload
  from changed/removed config, and validate the source shown by the guide.
- Integration: preserve the existing welcome-hook tests and guide config cases
  for duplicates, environment overrides, disable-after-load, stale sources,
  config provenance, and the shared entries/default list. Add file-change after
  load and empty-value reporting where missing. Preserve current guide behavior
  for literal delimiter characters; changing its display protocol is out of scope.

The focused invocation is:

```bash
(cd dev && uv run pytest -q tests/test_welcome.py tests/test_guide.py -k config)
```

Validate the single-pass requirement by reviewing that the loader has one call
to the reader before its apply loop, and that the reader has one config-file
input loop and no command/process substitution inside its per-line logic.
Combined multi-key behavior tests and the measurements support that structural
review; do not add timing thresholds to pytest or tests that copy the parser.

## Measurements and acceptance

Pre-implementation loader measurements supplied by the coordinating agent on
2026-10-27 used one warmup and seven samples per case, a fresh
`bash --noprofile --norc`, isolated HOME/XDG, `PATH=/usr/bin:/bin`, and `LC_ALL=C`.
They include process startup plus sourcing `config.lib.sh` and one load:

| Case | Bash 3.2 median | Bash 5.3 median |
| --- | ---: | ---: |
| Baseline process only | 5.6 ms | 10.3 ms |
| Config disabled | 40.4 ms | 51.7 ms |
| Missing config | 52.4 ms | 67.6 ms |
| Empty config | 54.7 ms | 66.9 ms |
| All nine keys | 421.8 ms | 384.8 ms |

These are reference observations, not full-startup timings or promised savings.
Recreate the fixtures and record their exact content before the first code edit;
do not present a later prototype as a change to the installed/runtime code.

Use the same temporary developer-only Python measurement harness at baseline,
after Stage A, and after Stage B. Keep its source and raw JSON with the execution
record so the procedure is reproducible; no permanent benchmark CLI or runtime
dependency change is needed. Measure:

1. The isolated loader cases in the table with at least the same 1+7 sampling
   scheme on both actual interpreter paths. Time process creation to exit with a
   monotonic clock, excluding fixture setup. Record samples, median, and range.
2. Full interactive startup in a PTY with both missing and all-nine-key config,
   reusing `bench.scenarios.scenario_environment`, `scenario_args`, and
   `bench.pty_runner.run_pty_sample`. Cover `remote-ssh-min` and
   `remote-ssh-welcome` to retain whole-startup behavior with and without welcome.
   They disable network update checks; do not enable user welcome modules.
   Run the matched `bash-baseline` control too. Use three warmups and twenty
   measured samples, recording both ready and total time, median and p95.

The existing benchmark creates isolated HOME/XDG for every sample. Therefore the
temporary harness must call `scenario_environment` first, then explicitly write
the chosen config fixture into that returned `XDG_CONFIG_HOME` before invoking
`run_pty_sample`; putting a file in the developer's usual HOME does not work.
Generate the all-key fixture from `remote_ssh_config_entries` outside the timed
section: use each current default, mapping the guide's `[unset]` sentinel to an
empty `NO_COLOR=` entry. Freeze that fixture for all three checkpoints. For a
missing-file sample create no config file. Replace the returned command's Bash
executable with the selected absolute interpreter path, and use a temporary
PATH shim for env-Bash children; keep the optional-tool PATH identical across
matched baseline/after samples. Clear inherited settings and markers through
the existing environment cleaner. Record Bash versions, OS, tool availability,
config bytes, environment overrides, and whether HOME is fresh for each sample.

Accept only when behavior and `just smoke` pass, the reader/marker structural
requirements hold, and repeated local measurement shows lower populated-config
loader cost without a reproducible regression for missing/disabled config or
full startup. Compare each after case to its matching before case, not the
missing-file scenario to a fixture that changes effective settings. If a result
is noisy, repeat the affected matched comparison; do not widen the runtime scope
or introduce caching to force a numeric target. Publish measured stage results
and any remaining uncertainty separately from correctness verification.
