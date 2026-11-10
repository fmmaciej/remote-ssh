# Final technical integration contract — T1–T7

This continues increment01/02 against SPEC-MANAGED-TOOL-LIFECYCLE0.3 and
PLAN-MANAGED-TOOL-LIFECYCLE0.2. It describes the integrated subject for independent
audit, not an independent acceptance result.

## Public commands and read-only model

The dispatcher exposes install, uninstall, update, list and merged check.
The tool/doctor namespaces, --full, --skip-unsupported and --strict are rejected;
there are no aliases, parent-detection exceptions or hidden compatibility flags.
Install/uninstall validate the whole argv before consent or mutation; no-argument
install/uninstall show usage/1. The low-level installer uses the same engine,
ownership, consent and prior-journal gate.

`ms_report_model` combines current platform catalog definitions, recorded members,
recorded failed/not-run scope and proven legacy active installs. It never adopts
or writes state. Aliases map to one tool. `ms_status_load` separates membership,
support and structural/selector/PATH health; missing, broken, stale, retired and
unsupported members remain visible. List output is alphabetic. --installed uses
membership, --all adds unsupported catalog entries, and default catalog output is
platform-filtered. Profiles and legacy expected-tools never select the managed set.

List/check validate all arguments, begin a generation/child-ticket fence, build
the complete result in memory, and print only after the final fence succeeds.
They do not initialize state/tickets, execute managed payloads, load libraries,
source rc/hooks or write an update cache. Check's rc test is syntax-only with
BASH_ENV/ENV suppressed. Git environment diagnosis disables optional index/cache
writes, fsmonitor, untracked cache, automatic diff refresh and hooks for those
queries. PATH tests account for physical aliases, relative/empty entries,
shadowing and shell functions; a library has no executable PATH requirement.
Required unhealthy selected scope and required environment errors return1;
optional helpers/fzf hints are informational. An empty managed set is not an error.

The login welcome summary lazily loads only state/inventory/lock proof helpers.
It reports a cheap managed count or uninitialized/unavailable hint, preserving
existing toggles, deduplication and issue replay. It never runs full check,
installation, payload probes or network and creates no desired-list/cache.

## Prune

Dry-run is read-only. Apply resolves/acquires only PREFIX's bakery root, without
requiring writable bin/checkout and without unrelated journal recovery. Before
any deletion it completes all-slot claims plus live bin/active-link inventories;
I/O/corrupt claims fail closed. Other-pair claims and all pending/protected release
intentions remain protected. Completed current-pair history does not pin every
old release forever. Immediately before each registered rm, prune rechecks live
current-definition C, complete claims and references. A receipt never authorizes
recursive deletion after payload loss. Custom aliases (including unusual names)
and libraries retain the same conservative reference protection.

## Registered Git operations and metadata revisions

Fetch/reset remain external execs under the existing registered-child lease in
every held root. Each command supplies maintenance.auto=false, gc.auto=0,
core.fsmonitor=false and core.untrackedCache=false, without persisting config.
This prevents native detached maintenance from escaping the lease after fetch's
PID exits. Guard queries use GIT_OPTIONAL_LOCKS=0 and disable fsmonitor,
untracked cache and automatic diff refresh. Fault stubs identify fetch/reset by
operation rather than positional arguments. Native local-upstream regression
forces the loose-object maintenance heuristic and verifies no auto-maintenance
child/hook, no fsmonitor callback and unchanged local config bytes.

Current saved required-bundle metadata replaces the tool's prior definition
requirements; per-release typed manifests remain immutable. A newer definition
can remove required data without imposing that obsolete requirement on a new
release, while old manifests still describe their original release.

## Verification isolation and evidence

Use the accompanying `run_isolated_verification.py` for audit subprocesses:

```sh
uv run --offline --no-project --cache-dir /private/tmp/remote-ssh-uv-cache python \
  dev/docs/history/managed-tool-lifecycle-implementation-20261110/increment-03/run_isolated_verification.py \
  --repo /Users/fm/Programming/00_Other/remote-ssh \
  --output /private/tmp/remote-ssh-managed-audit0 --label audit --timeout 3000 \
  pytest tests/test_managed_reports.py tests/test_managed_prune.py
```

Choose `smoke` without test paths for full just smoke. Labels/output HOME must be
new; the runner refuses to overwrite evidence and bounds its owned process group.
It constructs a fixed public environment and never copies ambient application or
credential variables, disables dotenv/startup identity and uses synthetic
HOME/XDG/Git config paths. Common fixture subprocesses likewise construct a fixed
public environment and bind global Git config to their own synthetic HOME.
Dedicated identity tests opt in only with synthetic ROOT/DOTS/HOME. The tracked
public copier excludes local/env/credential files before reading and adds only
explicitly owned public runtime paths. A synthetic denied credential variable and
Git --file deny-before-read sentinel exercise these boundaries.

Earlier broad-copy and identity-test isolation mistakes remain disclosed in
result/evidence records. Smoke01 and smoke02 raw captures and23earlier raw logs
are restricted and excluded from audit/publication/hash work. Their safe structured
aggregate metadata remains available; clean allowlisted reruns provide publishable
diagnostics. Original private configuration values were not displayed or inspected in model
context; the copy/subprocess reads remain disclosed. Earlier subprocess exposure
cannot be ruled out by later isolation fixes.

Offline controlled qualification probes establish protocol and failure handling,
not native Flyline ABI compatibility. Native library qualification was not
performed; actual optional skips and reasons accompany final JUnit coverage.
