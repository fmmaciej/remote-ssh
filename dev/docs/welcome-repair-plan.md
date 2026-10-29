# Welcome repair plan

Created: 2026-10-28
Round: R1 after initial implementation audit R0
Status: ready for the implementer; neither repair nor acceptance is complete
Pinned baseline: `39226a2d9074acf08279e7c3edde6a51cc2a629c`

Back: [Developer tooling](../README.md)
Related: [Accepted implementation plan](welcome-implementation-plan.md),
[implementation audit](welcome-implementation-audit.md),
[execution record](welcome-implementation-record.md),
[measurement evidence](welcome-measurements/README.md)

## Findings and unchanged contract

R0 is **NOT ACCEPTED**. Measurement acceptance and runtime review are separate.
The auditor supplied W0 and W1 before any R1 implementation. Both belong to
this one repair round. Later findings do not restart the limit: only R2 and R3
remain after R1; unresolved R3 or a required scope expansion goes to ROOT.

**W0 — asymmetric measurement inputs.** The R0 candidate was copied from the
workspace, including the ignored private `dots/git/user.local`, which the pinned
`git archive` baseline does not contain. The full rc Git identity hook therefore
consumed different inputs. `tools/defs/atuin.sh` also had mode 0600 instead of
baseline 0644, with identical bytes. The retained
[paired metadata](welcome-measurements/paired-r0-attempt-1.metadata.json)
confirms that these are the only manifest differences outside the seven
authorized welcome runtime paths. Do not print or copy private file contents
into evidence.

The [first paired attempt](welcome-measurements/paired-r0-attempt-1.jsonl)
contains 139 successful records and then stops with status 1 at the first
candidate Bash 3.2/actionable/PTY warmup. The
[failure log](welcome-measurements/paired-r0-attempt-1.log) retains its full
screen (`git config invalid` instead of the required `git config missing`).
Frozen `sample()` asserts before constructing and returning the record, so that
rejected sample's ready/total timings were not persisted. They cannot be
reconstructed from this log. The entire partial attempt is rejected as a
performance comparison.

**W1 — incomplete library passes worker preflight.** The independent
[R0 fault probe](welcome-audit-evidence/worker-preflight-r0.json) removes only
`shell/welcome/hw.sh` in a disposable runtime copy. On both actual Bash versions,
`welcome.lib.sh` reports the failed source but later successful operations mask
its status. The worker's six orchestration checks then pass: status is 0 and a
partial panel is displayed. The accepted contract requires library/preflight
failure to return reserved status 125 before any display, allowing the parent
to fall back once. A renderer's own exit 125 must never trigger group replay.

Keep all panel/provider work, status semantics, lazy status-library loading,
one fresh worker and one welcome-library load, three isolated captures, external
user modules, canonical qualification and existing fallback scopes. Do not
change provider files, rc hooks, runtime configuration, caches, Atuin, fixture
bytes, expected screens, the frozen measurement harness or acceptance criteria.

## Ownership and permitted changes

The repair planner owns only this document and does not implement fixes.
The implementer owns:

- `shell/welcome/bundled-runner.sh`: the W1 pre-display check only.
- `dev/tests/test_welcome_bundled.py`: focused W1 regressions.
- `dev/docs/welcome-implementation-record.md` and new R1 evidence under
  `dev/docs/welcome-measurements/`: materialization recipe, manifests, checks,
  preserved-attempt accounting, final source fingerprints and results.
- New isolated baseline/candidate directories in `/private/tmp`.

ROOT owns privileged checks and timings, coordinated with the implementer. The
auditor owns its report and independent probes. Everyone shares the checkout;
preserve others' edits. Do not stage, commit, push, edit the accepted plan,
modify the frozen harness/fixtures/screens, or run live asset checks.

## Ordered repair

1. Preserve existing R0 JSONL, metadata, logs, source manifests and snapshot.
   Record their hashes and rejected status; do not overwrite them with R1.
   Add an explicit rejected-sample accounting entry identifying its cell and
   output log, with ready/total marked unavailable because assertion preceded
   record creation. Keep the 139 records intact and exclude all of them from
   performance acceptance. Do not invent a successful or timed replacement
   record for the rejected sample.
2. Add W1 tests before changing the worker. On each actual interpreter, delete
   `hw.sh` only in a disposable copy and invoke the real worker directly with
   canonical wrapper arguments. R0 must reproduce status 0/nonempty stdout;
   the regression assertion requires status 125/empty stdout. Keep stderr
   separately. Add a missing lower-level helper case while its top-level
   renderer is still declared, so checking only the three renderer names
   cannot satisfy the test.
3. Extend worker-only preflight to check the complete fixed required library
   surface before its first capture/replay. Check required loader/helper file
   availability and the declared functions used by the renderers and their
   welcome/update helper dependencies; keep the current orchestration checks.
   Missing source files must not be concealed by inherited exported functions.
   Use private locals and Bash builtins; do not call providers as a check,
   parse/eval source, launch a second Bash, load the library twice, or preload
   `tools/lib/status.lib.sh`. That optional lazy load retains its existing
   tools/scripts fallback. Do not change `welcome.lib.sh` or a provider to
   alter their general failure semantics. If this cannot meet W1 within the
   worker, return the evidence to the planner before expanding scope.
4. Test parent recovery with a disposable worker-only helper omission: the
   external wrappers must remain usable. Assert one worker attempt, exactly
   one ordered external group, the expected panel once, continued user module
   and caller command, and existing quiet/debug stderr policy. A separate
   direct-worker missing-file case retains the exact auditor reproduction.
   Recheck existing renderer exit 125 and post-display worker-failure cases:
   neither may replay the group. Normal complete-library execution must still
   use one worker and no wrapper executions.
5. After correctness checks, freeze the final seven welcome source paths and
   modes. Create a new candidate at
   `/private/tmp/remote-ssh-welcome-candidate-r1` from an archive of the full
   pinned baseline, then overlay only the explicit allowlist below from the
   reviewed final working source. Never copy the workspace directory or
   arbitrary ignored/untracked files. Use a fresh pinned baseline archive or
   verify the existing isolated baseline against a fresh archive. Preserve the
   R0 snapshot as rejected evidence; do not repair it in place.

   | Authorized runtime path | Candidate mode |
   | --- | --- |
   | `shell/welcome.lib.sh` | 0644 |
   | `shell/welcome/runner.sh` | 0644 |
   | `shell/welcome/bundled.sh` | 0644 |
   | `shell/welcome/bundled-runner.sh` | 0755 |
   | `shell/welcome.d/00-remote-ssh.sh` | 0755 |
   | `shell/welcome.d/10-hw.sh` | 0755 |
   | `shell/welcome.d/20-sw.sh` | 0755 |

   Only the worker's bytes may change from the R0 seven-file snapshot in this
   repair. Both materialized trees must lack `dots/git/user.local` and retain
   baseline `tools/defs/atuin.sh` bytes/mode 0644. Do not remove or chmod those
   pre-existing workspace files. Record the exact archive/overlay recipe,
   allowlist, final diff, per-file source SHA-256/modes and aggregate hash.
6. Establish a deterministic materialization gate outside timed samples. Its
   red result on the retained R0 manifests must identify the two unauthorized
   differences. Its green result on the new physical trees must show exactly
   the authorized seven-path delta and no other content, path, file-kind,
   symlink-target or mode differences. Keep a complete tree manifest in addition
   to the unchanged frozen harness's runtime fingerprint, which covers
   `shell`, `lib`, `tools`, `bin`, `dots`, and `scripts`. Verify the candidate's
   seven paths against the reviewed working source, rather than claiming the
   whole snapshot equals a workspace containing private configuration.
7. Verify frozen harness, fixed `frozen_bench` files, fixtures and all 12 screen
   files against their R0 hashes. In particular, harness SHA-256 remains
   `6ae3e4a291a06e9a63b233d054584da3c6b75a45a09cd586eaa8d13536b6dfcc`
   and fixture SHA-256 remains
   `93ea13874f28c0f49b9a78360f26002bf8dd7cdce60162245e50d49f5c6c6f71`.
   Using that same frozen `sample()` and separate diagnostic sample IDs,
   recheck baseline and candidate Bash 3.2/actionable/PTY against the unchanged
   screen. Exclude these diagnostic launches from the principal results.
8. Run focused welcome tests, syntax checks on both actual Bash versions,
   `git diff --check`, and one final R1 `just smoke` before timings. ROOT's
   current smoke session 22270 belongs to R0; do not duplicate it while it is
   running. Coordinate the final R1 check after the worker edit and before
   measurement. No tests or heavy probes may run concurrently with timings.
   Retain an untimed final-source trace proving one worker/one library load,
   three captures and actual external fallback/user execution. An evidence
   driver may change only its candidate path for this trace; keep the frozen
   timed harness and fixtures untouched.
9. ROOT runs the unchanged harness in `paired` mode from the beginning, using
   the pinned baseline and corrected R1 candidate, outside the sandbox with
   the same recorded interpreter paths and environment. Write new
   `paired-r1.jsonl`, metadata and complete process log; retain exit status.
   Run both full paired principal batches and the first-batch controls:
   3 warmups + 20 measured samples per tree/cell, alternating order, fresh HOME
   per sample. A complete run has 920 records (736 principal, 184 controls),
   including warmups. Never resume from or splice in the 139 R0 records.
   Keep complete output/hashes, statuses, timeout flags and timings. Verify
   the fixed cache remains fresh for the entire run without changing its bytes.
   If it cannot, stop and report; do not refresh fixtures silently.
10. Recheck source/mode and frozen-input fingerprints after checks, immediately
    before timings and after timings. Any runtime edit invalidates affected
    after measurements. Summarize each batch/cell with median, p95, min/max
    and absolute/percentage changes for ready and total time using the frozen
    summarizer. Keep isolated and full PTY first-command-ready results separate.
    Any new assertion failure rejects the attempted series; retain its output
    and explicitly account for timings unavailable under the unchanged harness.

## R1 re-audit gate

Hand the final diff and all new evidence to the independent auditor. W0 closes
only when the clean archive/allowlist manifests, identical frozen inputs,
successful former-failure diagnostic and complete new paired series establish
symmetry. W1 closes only when the direct missing-helper failure returns 125
with no display on both Bash versions, parent fallback happens once before
display, and normal rendering/renderer-exit/post-display behavior still passes.

The final trace, focused tests, syntax checks, smoke log and measured source
fingerprints must refer to the same R1 source. All principal populated cells
must still show repeatably lower isolated and full PTY ready medians on both
interpreters in both batches, with p95/spread and controls reviewed under the
accepted criteria. Neither passing tests nor repaired materialization proves a
performance win. If preflight overhead removes that win, report the actual
results to ROOT for a bounded revision/removal decision; do not change work,
fixtures or thresholds to obtain acceptance.
