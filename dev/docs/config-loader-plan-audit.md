# Config loader implementation plan audit

Verdict: **ACCEPTED (R0)**, 2026-10-27.

Scope: review the implementation plan, not implement runtime changes.

Reviewed: [Config Loader Implementation Plan](config-loader-implementation-plan.md),
initial version R0 (315 lines). No blocking correctness or feasibility findings
were identified. No repair round is required.

## Assessment

| Area | Evidence in the plan | Result |
| --- | --- | --- |
| Scope and stages | Lines 13-25 and 176-202 separate the parser/load stage from marker operations, name the affected files, require tests and measurements after each stage, and exclude unrelated runtime work. | Pass |
| Single file read | Lines 72-134 define one invocation-local snapshot, one redirected input loop, in-memory allowlist matching, independent presence flags, and applying values only after the scan. Per-line substitutions and per-key raw lookups are excluded. | Pass |
| Bash 3.2 and strict mode | Lines 94-117 use indexed arrays, documented caller-local dynamic scope, initialized slots and count, guarded failures, safe increments, and explicit successful returns. No Bash 4+ feature is required. | Pass |
| Parsing equivalence | Lines 52-61 and 217-223 preserve first-`=` splitting, trimming, outer-quote removal, literal data, comments, allowlisting, duplicates including empty values, and a final line without LF. | Pass |
| Environment and reload | Lines 37-50, 121-134, and 224-240 preserve set-but-empty precedence, absence without default exports, changed/removed config, disable/re-enable, manual overrides, and current equality-based ownership. | Pass |
| Marker compatibility | Lines 153-174 retain canonical names, exported status, empty loaded markers, the current ownership predicate, and existing stdout helpers while removing hot nested substitutions. | Pass |
| Guide compatibility | Lines 136-151 and 241-245 preserve raw/gated lookup behavior and guide source attribution through inherited markers, changed files, overrides, disabled config, and shared entries. The guide's existing display protocol remains out of scope. | Pass |
| Verification | Lines 193-257 extend existing subprocess tests, explicitly select both interpreters and env-Bash children, run strict-mode cases, require structural review of the single-pass path, and end with `just smoke`. No live asset checker is requested. | Pass |
| Measurements | Lines 259-315 specify the same harness and frozen fixtures at baseline and after both stages, actual interpreter paths, loader and full PTY startup, missing and populated config, isolated HOME, warmups, repeated samples, and matched comparisons without fixed timing gates. | Pass |

## Feasibility evidence

The proposed fixed-name caller-local output contract is feasible in the actual
available interpreters. A small, standalone probe was run under `/bin/bash`
3.2.57 and `/opt/homebrew/bin/bash` 5.3.20 with `set -euo pipefail`. It declared
local indexed arrays and a local count in a caller, updated those slots in
nested helpers without redeclaring their names, preserved an empty slot and a
literal value containing `|`, `=`, and `$()`, and verified that the locals did
not remain after the caller returned. Both probes exited zero. This validates
the mechanism; it is not an implementation or parser correctness test.

The benchmark approach also matches the existing code: `scenario_environment`
creates a fresh isolated HOME/XDG and returns the environment;
`scenario_args` supplies the command; `run_pty_sample` accepts both as explicit
arguments. A temporary harness can therefore create the config after environment
preparation and select an absolute Bash path without modifying the permanent
benchmark CLI. The chosen min/welcome scenarios suppress update-check network
work and user welcome modules during measurement.

No implementation, full test run, or speed improvement is claimed by this
review. Runtime, tests, and the author's plan were not changed by the auditor.

## Acceptance criteria

1. The plan identifies concrete files, implementation stages, and verification
   after each stage. One invocation of `remote_ssh_config_load` reads the config
   file once; per-line parsing and per-key ownership operations avoid unnecessary
   command substitutions and subprocesses.
2. Config syntax remains literal: the existing allowlist, whitespace trimming,
   first `=` separator, matching outer quotes, last duplicate wins, comments,
   unknown/malformed lines, and final line without LF retain their behavior.
   Values must never be executed or expanded as shell code.
3. Environment values, including an explicitly empty value, retain precedence.
   Missing files and keys do not cause defaults to be exported by the loader.
4. Reload preserves the existing ownership contract: update config-owned values;
   clear them when removed or disabled; preserve manual overrides; clear stale
   canonical markers. Canonical marker names and their exported status remain
   compatible with child processes. Ownership continues to require the current
   value to equal the recorded loaded value.
5. `remote-ssh guide config` retains effective values and source attribution,
   including inherited config ownership, manual overrides, stale/legacy markers,
   and disabled loading. Shared entries remain the source of allowed keys and
   displayed defaults.
6. The design works in Bash 3.2 and newer Bash with `set -euo pipefail`. It does
   not require associative arrays, namerefs, new runtime dependencies, a lasting
   parsed cache, or changes to unrelated startup integrations.
7. Verification covers the semantic boundaries above, reuses the existing
   subprocess tests, and ends with `just smoke`. The live asset checker is out of
   scope.
8. Measurements compare before and after on the same machine, interpreter, and
   tool/state setup, with warmups and repeated samples. Both the isolated loader
   and complete startup are measured with absent and populated config. Populated
   startup config is created in the benchmark's isolated HOME, not the real
   user's HOME. Results are diagnostic, without arbitrary timing thresholds.

## Sources reviewed

- `shell/config/{entries,path,parse,load,markers}.sh`
- `shell/config.lib.sh` and the caller in `shell/env.sh`
- `tools/lib/commands/guide/sections.sh`
- Config tests in `dev/tests/test_welcome.py` and `dev/tests/test_guide.py`
- `dev/tests/conftest.py` (`runtime_bash` interpreter fixture)
- `dev/todo-bench.md`, `dev/docs/bench-shell.md`, and `dev/bench/`

## Review history

| Round | Verdict | Blocking findings | Action |
| --- | --- | --- | --- |
| R0 | ACCEPTED | None | Plan can proceed to implementation when requested. |

The agreed maximum of three repair/review rounds was not needed. Cosmetic
preferences were not treated as blockers.
