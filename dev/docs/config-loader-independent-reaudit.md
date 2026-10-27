# Independent configuration-loader re-audit

**Current verdict: ACCEPTED after R1. R0-F1 is closed; no open regression finding remains.**
See the [final R1 verification](#r1-independent-repair-verification).
The R0 section below is preserved audit history, including the original finding.

## R0 — 2026-10-27

**Result: one confirmed P3 failure-status regression; no configuration-value or
ownership regression found in the completed normal-mode probes.** The large
speedup is compatible with preserving the actual loading work: every populated
parser fixture verifies loaded settings and ownership, rather than accepting a
fast no-op. Failure reporting is not completely equivalent, as detailed below.

This review was performed by a fresh auditor who did not implement the change
or participate in the earlier audit. AGENTS.md, the three-file diff, the pinned
baseline, callers, documentation, and tests were read before forming the
verdict. Earlier implementation/audit reports were not used as evidence. No
runtime or test files were changed, staged, committed, or pushed. No live asset
checker or full smoke was run during R0. The separately coordinated timing
investigation is recorded in [the performance re-audit](config-loader-reaudit-performance.md).

### Confirmed regression R0-F1 — P3: failed catalog initialization reports success

Location: [parse.sh:44](../../shell/config/parse.sh#L44), with propagation through
[load.sh:9](../../shell/config/load.sh#L9) and its final `return 0`.

The old loader exposes failure of the `while ... done < <(remote_ssh_config_entries)`
redirection as its function status. The new initializer continues after the same
failure, assigns the count, and returns zero. The loader then processes zero
entries and also returns zero. This is an initialization failure, distinct from
the deliberately tolerated absence or unreadability of the optional config file.

Minimal reproduction, using a valid config and either isolated source tree:

```bash
audit_home=$(mktemp -d)
mkdir -p "$audit_home/.config/remote-ssh"
printf 'REMOTE_SSH_WELCOME_USER=0\n' >"$audit_home/.config/remote-ssh/config"
env HOME="$audit_home" XDG_CONFIG_HOME="$audit_home/.config" PATH=/usr/bin:/bin \
  /bin/bash --noprofile --norc -c '
    . "$1/shell/config.lib.sh"
    set -o posix
    remote_ssh_config_load
    printf "load=%s value=%s\n" "$?" "${REMOTE_SSH_WELCOME_USER-unset}"
  ' _ /path/to/tree
```

On `/bin/bash` 3.2.57:

| Context | Baseline | R0 current |
| --- | --- | --- |
| Ordinary caller | `load=1 value=unset` | `load=0 value=unset` |
| Add `set -euo pipefail` before load | process exits 1 before the printf | process continues, prints `load=0 value=unset`, exits 0 |
| Load real `shell/rc.sh` normally, edit the file, enable POSIX, call the loader | loader returns 1; previous config value remains | loader returns 0; the same previous value remains |

Both versions emit a redirection diagnostic on stderr. This is false success,
not intrinsically silent operation. A caller relying on status or `errexit` now
continues after a failed initialization and may trust unchanged settings or an
ineffective disable/reload operation. The files and values are valid; the
trigger is enabling Bash 3.2 POSIX mode after the functions have been sourced.

Priority is P3 because this is a narrow reporting regression in an already
nonworking mode, rather than a new failure of ordinary supported Bash loading.
Full `rc.sh` sourced while already in Bash 3.2 POSIX mode fails with status 2 in
both versions; public `guide config` with inherited `POSIXLY_CORRECT` or exported
POSIX `SHELLOPTS` also fails with status 2 in both, before this loader is reached.
A normal guide child launched from a POSIX parent without exporting POSIX mode
works in both. Bash 5.3 does not reproduce this catalog-redirection failure.

Repair acceptance: retain and propagate catalog-initialization failure through
the loader in ordinary and strict callers. Do not add POSIX support or change
literal parsing, optional-file absence handling, or ownership rules. Add a
regression that checks the function's own status, not merely the last printf's
status. The repair should be independently checked on both required Bash
versions and followed by the repository's default smoke verification.

A further [eight gate/API pairs](config-loader-reaudit-evidence/behavior-independent/posix-gate-R0-results.json)
verify a baseline nuance: the old disabled branch's explicit `return 0` masks
the same initialization error in both ordinary and strict callers. R0 current
does too. An early planning assumption that disabled strict callers aborted was
incorrect. Initial R1 planning considered removing both forms of masking, but
the final R1 scope explicitly preserves disabled status zero and existing state
after initialization failure, without a POSIX/version-specific exception.
Enabled failure/status restoration is the confirmed regression being repaired;
the old disabled limitation is not an additional cleanup task.

Evidence: `helper-after-enabling-posix` and
`helper-after-real-rc-then-posix` in
[posix-results.json](config-loader-reaudit-evidence/behavior-independent/posix-results.json).
The simpler parser matrix also caught this as its sole state/status delta.

### Reconstructed baseline contract

- The path uses nonempty `XDG_CONFIG_HOME`, otherwise nonempty `HOME`; neither
  means unavailable. Only lowercase `0`, `false`, `no`, and `off` disable the
  gate. Empty `REMOTE_SSH_CONFIG` enables it.
- There are nine canonical keys. Parsing trims the line, key, and value with
  the current locale's `[:space:]`, splits at the first `=`, removes one
  matching outer quote pair, and does not evaluate shell code. Whole-line
  comments and malformed/unallowed keys are ignored; inline `#`, additional
  `=`, pipes, backslashes, and unmatched quotes are literal. Last matching
  assignment wins, including an empty assignment and a final line without LF.
- Raw lookup bypasses the enable gate and returns zero for present empty
  values, one for absence. Gated lookup returns one when disabled. Calls must
  inspect current file content; there is no persistent value cache.
- Existing set variables, including empty or unexported variables, win unless
  both canonical ownership markers exist, source is `config`, and current
  value equals the last loaded value. Identically reassigned values remain
  owned; a different manual value loses ownership.
- Present config values replace unset or still-owned variables and export the
  value plus both markers. Missing keys/files or disabling removes only
  still-owned values and clears canonical markers. True overrides survive.
  Exported markers allow children to retain provenance and reload ownership.
  Legacy differently prefixed markers are not canonical ownership.

The new code retains that state machine. It enumerates the catalog once and
reads one invocation-local snapshot for `load`, rather than separately parsing
the file for each key. Raw lookup creates its own fresh local snapshot. The
marker simplification preserves canonical key/name mapping. Private snapshot
outputs are dynamically scoped locals of the two public callers; the probes
also checked restoration of outer locals with those names and absence of
private variables after return.

### Independent evidence and completed checks

Source: [behavior_probe.py](config-loader-reaudit-evidence/behavior-independent/behavior_probe.py).
Each principal phase builds two fresh `git archive` trees from
`c41cbc4820594de95e2035cfc5ab896e16db9e70`; current overlays only
`shell/config/{parse,load,markers}.sh`. JSON records SHA-256 for all three files
in both trees and the actual shell version. Every version/case/shell/mode uses
a separate HOME and a fresh Bash process. The only output normalization replaces
temporary tree/HOME path prefixes.
The R0 gate follow-up reused the already frozen, checksum-verified R0 trees;
its shell processes and HOME directories were still fresh.

The NUL-delimited state output includes all nine values with set/unset flags,
both canonical markers with set/unset flags, `declare -p` attributes/export
state, ownership predicates, helper outputs, lookup return codes, and private
variable leakage. Populated parser cases additionally require real `config`
ownership, preventing two empty executions from passing as equivalent.

Required shells were `/bin/bash` **3.2.57** and `/opt/homebrew/bin/bash`
**5.3.20**. Each differential case ran both normally and with
`set -euo pipefail`.

| Evidence | Pairs | Result |
| --- | ---: | --- |
| [Parser matrix](config-loader-reaudit-evidence/behavior-independent/parser-results.json) | 88 | 87 identical state/status pairs; Bash 3.2 POSIX strict exposes R0-F1. Two stderr differences concern the same POSIX failure. |
| [Lifecycle matrix](config-loader-reaudit-evidence/behavior-independent/lifecycle-results.json) | 60 | Identical settings, markers, attributes, statuses, and stderr. |
| [Failure matrix](config-loader-reaudit-evidence/behavior-independent/failure-results.json) | 36 | 35 identical state/status pairs; one preexisting raw-directory crash is improved. Sixteen stderr differences concern guarded open/read diagnostics. |
| [Integration matrix](config-loader-reaudit-evidence/behavior-independent/integration-results.json) | 8 | Equal outcomes. Normal full rc/reload/disable reaches all three state checkpoints in both shells; the strict full-rc probe fails before its first checkpoint in both versions, so that pair is not a startup success. |
| [POSIX follow-up](config-loader-reaudit-evidence/behavior-independent/posix-results.json) | 24 | Three state/status differences isolate R0-F1; other pairs establish its practical limits. |
| [POSIX disabled/raw/gated follow-up](config-loader-reaudit-evidence/behavior-independent/posix-gate-R0-results.json) | 8 | State/status equal; confirms disabled baseline masking under both caller modes and preserved raw/gated absence statuses. |

The parser fixtures include 36 fixed byte/value forms and six seeded generated
files with two shuffled assignments per key, plus duplicate-empty and shell
option/locale profiles. Inputs include tabs/CR/vertical tab/form feed,
whitespace within quotes, single unmatched quote characters, multiple `=`,
shell-code-looking strings with execution sentinels, ESC/control bytes, NUL,
invalid UTF-8, Unicode whitespace, and missing final LF. Profiles cover custom
and empty IFS, `noglob`, `extglob`, `nullglob`, `failglob`, `nocaseglob`,
`nocasematch`, `allexport`, available `localvar_inherit`/`localvar_unset` and
`inherit_errexit`, POSIX mode, and C/en_US.UTF-8/pl_PL.UTF-8/C.UTF-8 locales.

Lifecycle probes cover changed/repeated reload, removal of keys and the file,
disable/re-enable, different/empty/identical manual values, incomplete/stale
and legacy markers, child inheritance and reload, readonly and unexported
existing overrides, conventional outer locals, and outer snapshot locals.

Failure probes cover missing/empty files, symlink loops, unreadable files,
directories (`read` EISDIR), `/dev/tty` open failure, absent HOME/XDG, and an
injected read failure after a parsed prefix, including a direct raw lookup with
`errexit` active. They compare loaded values and markers after failure as well
as statuses and diagnostics.

The targeted command in [pytest-results.txt](config-loader-reaudit-evidence/behavior-independent/pytest-results.txt)
passed **50 tests, 38 deselected, in 8.28 s**:

```text
dev/.venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/config-reaudit-pytest dev/tests/test_config.py dev/tests/test_welcome.py dev/tests/test_guide.py -k config
```

`test_config.py` explicitly selects both Bash versions, including env-bash
children, and adds useful value/status/export lifecycle coverage. Existing
welcome tests exercise config before welcome rendering and provenance on
reload. Guide tests cover file/environment/default sources, stale provenance,
post-load file changes, empty values, and entry-list sharing. The new guide
test deliberately preserves the existing pipe-display defect described below.
These tests did not cover R0-F1, and equal outcomes from an already-failed rc
probe were not counted as successful integration coverage.

### Existing limitations and intentional error-handling differences

- **Bash 3.2 POSIX loading was already broken.** Functions sourced before the
  toggle cannot use the catalog process substitution after it; sourcing files
  already in POSIX mode also encounters syntax errors. R0-F1 concerns newly
  lost error status, not the preexisting inability to load there.
- **A raw directory read under Bash 5.3 nounset previously killed the caller.**
  Baseline `line` can remain unset after EISDIR, and the loop tests `$line`.
  Current initializes its line variable and returns normal absence. In the
  guarded lookup caller the old process exits 1; current returns lookup 1 and
  the caller completes 0. Loader values and cleared markers agree. This is a
  useful robustness improvement consistent with an optional config file.
- **Read/open diagnostics are now suppressed by the guarded scan.** Directory,
  `/dev/tty`, and injected-prefix read failures demonstrate this explicitly.
  Ordinary loader absence/cleanup behavior is preserved. A parsed prefix is
  retained after the injected failure in both versions; neither version offers
  a transactional all-or-nothing read guarantee.
- **NUL handling differs between the required Bash versions, not the two
  implementations.** Bash 3.2 truncates the stored line at NUL; Bash 5.3 omits
  NUL and retains following bytes. Both implementations agree within each Bash.
- **Guide's pipe-delimited display is already lossy.** With
  `REMOTE_SSH_WELCOME_COLOR=left|right`, both print
  `REMOTE_SSH_WELCOME_COLOR=left [right|config]`. The parser/load state retains
  `left|right`; the guide's unchanged delimiter protocol splits it. This is an
  existing reporting defect, now explicitly preserved by the new guide test.
- **Identical manual reassignment is indistinguishable from ownership.** The
  old and current marker contracts both intentionally treat it as still owned.
- **The full sourced rc is not generally strict-shell-safe.** This audit's
  strict rc probes fail before the first post-rc checkpoint in both source
  trees, without a loader difference. A follow-up
  [trace](config-loader-reaudit-evidence/behavior-independent/strict-rc-trace-results.json)
  identifies the unchanged `24-navi.sh` hook's final `have navi && alias ...`
  returning one when navi is absent; `errexit` then stops the sourced hook.
  Ordinary interactive-style rc and the strict standalone config/guide paths
  were checked separately. This unrelated existing issue is outside R0-F1's
  repair scope.

### Limits of the R0 conclusion

This is finite differential and integration evidence, not a proof for every
Bash option combination, every locale/filesystem, or asynchronous modification
of the file. It does not establish atomicity across concurrent edits, actual
device/network-filesystem EIO after a prefix, signal-interrupted reads, or
arbitrary user overrides of Bash builtins/functions and variable attributes.
The partial-read probe is fault injection; directory and tty failures are real
OS errors. No heavy timing workload was run concurrently with the root's
measurements. The shared strict-rc failure is an explicit coverage limitation.

R0-F1 requires the authorized planner → implementer → fresh audit round before
this review can be closed. Other observed deltas above are retained rather than
discarded because most ordinary tests passed.

## R1 independent repair verification

**ACCEPTED. R0-F1 is closed after independent probes and the new successful smoke.**
The enabled initialization failure now matches baseline status and strict
termination, and the old disabled status-zero behavior remains intact. No new
finding was identified in the repeated probes.

The repair followed the separate [R1 plan](config-loader-repair-plan.md).
The auditor did not edit runtime or tests. The final diff was independently
reviewed: initialization preserves its consuming loop/redirection failure
before assigning count; raw lookup stops before path resolution on init
failure; load saves the actual failure status, returns it when enabled, and
returns zero without read/application when disabled. This is an enable-gate
policy for initialization failure, with no Bash-version or POSIX detection.
The successful reader, literal parsing, marker helpers, and normal application
loop remain unchanged by R1.

The implementer's initial disabled-case oracle was superseded within the same
R1 after the auditor's R0 gate evidence disproved its strict-mode assumption.
The final tests preserve old disabled behavior. The implementation record keeps
the earlier red/green outputs as superseded history and records corrected red
**5 failed / 9 passed**, then corrected green **14 passed**. These implementer
results supplement the auditor's fresh runs below; they were not substituted
for independent verification.

Final runtime source fingerprints, matched by every R1 evidence record:

| File | SHA-256 |
| --- | --- |
| `shell/config/parse.sh` | `b478dca2f276abd625a721d0a839ada1b793c19764416cb452387ce39cb7465d` |
| `shell/config/load.sh` | `bfee6c32ce4b94cb7526acd5926cf8df6e44fe60b5dc898d3e706d3d6d470dea` |
| `shell/config/markers.sh` | `7591de066e72d9674f32677f32258ddafca53d149d72a541a3760ba9099dd0af` |

[source-snapshots.json](config-loader-reaudit-evidence/behavior-independent/source-snapshots.json)
retains the exact checksum-verified baseline, R0, and final R1 contents of these
files, so reviewing the evidence does not require the temporary trees to remain.

| Fresh independent R1 evidence | Pairs/cases | Outcome |
| --- | ---: | --- |
| [Parser](config-loader-reaudit-evidence/behavior-independent/parser-R1-results.json) | 88 pairs | All state/status pairs match baseline, including restored enabled POSIX failure status. |
| [Lifecycle](config-loader-reaudit-evidence/behavior-independent/lifecycle-R1-results.json) | 60 pairs | All settings, markers, ownership, attributes, statuses, and stderr match. |
| [Failure](config-loader-reaudit-evidence/behavior-independent/failure-R1-results.json) | 36 pairs | The sole state/status difference remains the intentional raw-directory robustness improvement documented in R0. |
| [Integration](config-loader-reaudit-evidence/behavior-independent/integration-R1-results.json) | 8 pairs | Same normal rc/guide behavior; same explicitly excluded preexisting strict-rc failure. |
| [POSIX](config-loader-reaudit-evidence/behavior-independent/posix-R1-results.json) | 24 pairs | All state/status pairs match baseline; R0-F1 no longer reproduces. |
| [Disabled/raw/gated](config-loader-reaudit-evidence/behavior-independent/posix-gate-R1-results.json) | 8 pairs | All state/status pairs match baseline, including disabled ordinary and strict success with unchanged state. |
| [Generic initialization fault](config-loader-reaudit-evidence/behavior-independent/initialization-fault-R1-results.json) | 24 cases | All explicit assertions pass; tests actual status 7 without POSIX mode. |

The [generic fault probe source](config-loader-reaudit-evidence/behavior-independent/initialization_fault_probe.py)
injects initialization status 7 in the final current implementation and checks
both shells, ordinary/strict callers, both enable gates, and load/raw/gated
APIs. Enabled load and raw return exactly 7; disabled load returns zero; disabled
gated lookup returns one without initializing. Strict callers stop only for
nonzero statuses. Previous value and canonical markers remain intact, and no
case resolves a config path. This verifies general propagation and gate policy,
rather than an implementation tailored to the POSIX reproduction.

The auditor's [fresh targeted pytest run](config-loader-reaudit-evidence/behavior-independent/pytest-R1-results.json)
passed **64 tests, 38 deselected, in 7.23 s**, using the same three test files
and `-k config`, a separate temporary base directory, and no pytest cache.
The new tests check actual loader status and state for fresh load/reload/disable
on both interpreters, including standalone strict execution and an EXIT-trap
state checkpoint. Raw failure additionally proves absence of path lookup.

The implementer's new [corrected R1 smoke log](config-loader-measurements/repair-r1-smoke.txt)
records `just smoke` **exit 0: 765 passed, 57 skipped, 308.64 s**, with Bash
syntax, ShellCheck, Ruff, and mypy checks also passing. The auditor read the
actual captured log after completion, rechecked `git diff --check`, and verified
that the final runtime and test fingerprints still match the independently
tested R1. This acceptance does not reuse the earlier R0 smoke result.

All R0 limitations above remain explicit: equal already-failed rc/POSIX paths
do not establish successful startup in those modes, the guide delimiter defect
remains, and finite probes do not guarantee concurrent-read atomicity or every
filesystem/signal failure. There is no additional open behavior finding.
