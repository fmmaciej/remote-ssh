# Repair01 technical result — ready for independent re-audit

Repair round 1 implements preserved repair-plan0.1 for A0-001/A0-002 without changing
SPEC0.3, PLAN0.2 or product requirements. Required targeted verification passed 272
cases. The repaired subject's full `just smoke` passed **1891 cases,
56 skipped,0 failed**. Both completed with source_unchanged=true
and no timeout. The final subject is frozen; independent acceptance remains pending.
Original round 0/audit 0 artifacts and its1863 passed/56 skipped result remain immutable historical
evidence, not a result for this repaired subject.

## Correction

A shared read-only `ms_tool_uninstall_terminal` predicate requires no membership
and this tool's actual completed uninstall. Current item takes precedence over
archived results; queued/running/failed/not-run never qualify. Uninstall ignores
those terminal historical release receipts and absent-selector root fallback.
Selector collection ignores terminal historical custom selector rows, while current
names/declared aliases and full live inventory/claims/guards remain applicable.
A newly proven active/inactive release still enters explicit uninstall scope with
live C; foreign required selectors still abort the whole selection.

`ms_journal_prepare` normalizes a settled prior journal in memory under prefix lock
and the passed current-generation gate, BEFORE definitive preflight builds new
receipts. Install/uninstall facades and the new-update entry call it in that order;
continuation of the current update does not. `ms_journal_begin` now rejects an
unprepared prior journal rather than silently invalidating a collected receipt.
The archive is persisted only with actual new work. A repeated completed uninstall
returns0 before locks/root creation/new journal, preserving complete bytes/modes/
mtime snapshots. Real unresolved journals and failed/partial evidence retain their
existing gate/refusal, membership and protection.

Reports use the same terminal qualification for historical root/B fallback, while
checking actual selectors/collisions first. Immediately after successful uninstall,
supported catalog entries are unmanaged+available, absent from --installed; explicit
check still returns1 with missing/external-only. Reports never archive, recover or
commit state to correct the view. Actual managed missing/broken, retired/unsupported,
failed/not-run and pending remain per-tool. No B/C, all-slot claims, prune, asset,
version, native runtime, consent or no-resurrection requirement was weakened.

## Exact subject and preservation

R1 verified88/88 audit 0 source entries before editing. Twelve exact public before
snapshots and before-inventory.json were published first and verified by the
coordinator. Seven production source files changed: managed journal/install/
uninstall/update, commands install/uninstall/tool_status. Five existing verification
files changed: test_managed_uninstall/reports/public_faults/recovery and
managed_fixture. The latter two explicitly prepare the private journal before a
new final preflight/begin; recovery also asserts an unprepared begin is refused.
There are no new runtime/test source paths. Source-hashes.json records the union
of all 88 original paths, including original absences; delta.json records all
12before/after changes and immutable snapshot references. The other
76subject entries are unchanged. No source edit occurred during
final tests or after this freeze. HEAD remains9a223dcca76072eb9035316d25abf972902d3289.

Preservation.json freshly confirms 28 public pin/adapter/production-identity file
hashes match audit 0. User tool-version/fixture work, original accepted source and
snapshot bytes, private Navi adapters, fzf definition/host gate and production
identity defaults are unchanged. Root-owned plan/assignment/execution/events,
audit0 and prior reports were not edited. No real checkout Git mutation, network,
asset download/build, host install, SSH operation or user/global config edit occurred.
Authorized local-upstream Git mutations ran only in synthetic test repositories.

## Actual checks

All functional tests used the immutable published fixed-allowlist
increment-03/run_isolated_verification.py with fresh output labels/HOME. Exact
commands/timeouts/environment provenance and source fences are in each result JSON.

- New red:24 failed/4 passed.16 failures demonstrate the actual terminal scope,
  immediate report, mixed and live-inactive/custom-history regressions. Eight
  pending-substitution cases already refused correctly but an extra whole-HOME
  mtime assertion incorrectly rejected permitted lock-directory bookkeeping.
  That new oracle alone was corrected to retain journal/payload/path snapshots,
  current-running/member assertions and foreign bytes/mode/mtime checks. All 8
  guards then passed BEFORE production correction. Full no-op/report bytes,
  modes and mtime oracles were retained unchanged.
- Targeted: 272 passed in1260.07s pytest, result0/source_unchanged=true. Required
  uninstall/reports/recovery/public_faults/update/prune plus lifecycle/install-engine
  and separate identity/B/C guards are included. All 28 new parametrized public
  cases passed on Bash 3.2.57 and 5.3.20.
- Static: 14 Bash syntax checks, shellcheck and Ruff passed; diff-check returned 0.
  The required final smoke additionally passed its current static stages.
- Full repaired smoke: 1891passed/56skipped/0 failed;
  runner elapsed2833.17s, no timeout, source_unchanged=true.
  Full-smoke.log/xml/result and source-hashes are safe fresh allowlisted evidence.

Coverage.json maps all 22 REQ/24 AC to actual final parametrized cases and adds both
repair findings' 28 new regression cases. Cases.json gives the complete final suite;
skips.json lists every actual ID/reason. These are implementer evidence, not an
independent completeness or Pass certification. The acceptance sequences cover
immediate repeat and later fd install/update without rg resurrection; readonly
catalog/check variants; mixed preflight/foreign refusal; newly live inactive C;
historical custom paths; per-tool missing/broken/failed/not-run; and pending
foreign member/parent/marker/selector protection after SIGKILL. Existing complete/
partial unlink/rm recovery, retired/missing C, all-slot/pending prune and report
fence cases remain passing in the targeted/full suites.

## Limits and handoff

Native Flyline ABI qualification remains unrun/unverifiable, with no new artifact
discovery/download or claim based on probe stubs. Actual optional skips remain
explicit; controlled native Git tests are not native-library qualification.
Restricted smoke01/02, older scratch captures/private archive and actual private
configuration were not opened, hashed or promoted in this repair. Earlier
provenance incidents remain disclosed by the original integration/quarantine
records; this clean repair does not erase those uncertainties.

Only safe current repair evidence is published under repair-01/. The same report
content is staged as repair-01-result.md for coordinator-owned report publication.
No subject edits will occur while independent repair-01-audit runs. Coordinator
must activate the separate auditor; no independent Pass is claimed here.
