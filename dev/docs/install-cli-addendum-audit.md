# Install CLI addendum — independent scope audit

Date: 2026-10-28  
Verdict: **ACCEPTED**  
Blocking findings: **none**

Audited [`install-cli-implementation-addendum.md`](install-cli-implementation-addendum.md),
SHA-256 `ceddfb157e3bb6709d08b09b3d01f6eae1d1c205d7f9c3505749e3e6302bd09f`,
against the accepted plan's failure contract, the current install facade,
[`install_tools` and `install_tool`](../../tools/lib/install/install.sh), their
call sites, and the relevant install fixtures/tests. This accepts the narrow
scope addition before editing the helper; it is not implementation acceptance.

## Findings

The addition is necessary and appropriately limited. The current
`install_tools` has an unguarded directory creation followed by a loop whose
result is the result of its last tool call. Guarding the function invocation
with `|| return 1` suppresses Bash errexit within that function, so a later
successful call can hide an earlier failure. The same context can allow tool
attempts after failed directory preparation. Explicit checks at these two
boundaries are required to satisfy the accepted plan's lines 128–137 and
230–235 independently of errexit.

The proposed change is minimal: extend ownership only to `install_tools` in
`tools/lib/install/install.sh`, guard its `mkdir`, guard each existing ordered
`install_tool` call, and retain a single complete-array call in the already-owned
facade. The temporary per-tool facade loop does not fix a suppressed directory
failure and changes the previous batch interaction. The full-array recording
stubs in [`test_install_expected_tools.py`](../tests/test_install_expected_tools.py)
independently confirm that interaction; retaining them unchanged avoids
adjusting tests to conceal that change.

Successful selection and ordering, per-tool staging, diagnostics, confirmations,
and options remain intact. Stopping at the first failure is consistent with the
previous normal `set -e` invocation and strengthens behavior in conditional
contexts. Existing successful tools remain installed, and the previously
published management CLI remains available. The addendum introduces no rollback
or transaction, no additional dependency, and no change to the shell activation
boundary. The other `install_tools` caller in `commands/tool.sh` also benefits
from explicit failure returns without requiring an additional runtime edit.

## Evidence required from implementation

The addendum's test obligations are sufficient and feasible in the already-owned
`test_install_cli.py`:

- Use the real facade and batch helper under Bash 3.2 and 5.x, with an observable
  ordered three-tool fixture. Separate first- and middle-failure cases must
  assert the exact attempted prefix, no subsequent attempt, and preservation
  of the first completed installation in the middle-failure case.
- Make `INSTALL_PREFIX` invalid while keeping CLI publication possible. Assert
  that directory failure returns nonzero before any tool attempt.
- In all failure cases, verify no post-tool environment preparation, no
  expected-tools creation or modification, and no completion footer; execute
  help through the retained installed CLI. An existing expected-tools sentinel
  is suitable evidence for the no-modification branch.
- Keep existing complete-array stubs unchanged, include these regressions in
  the final required smoke run, and record distinct interpreter versions.

The in-progress fixture already copies the real runtime tree, offers three
fixture definitions, isolates HOME/XDG and startup files, binds child Bash, and
uses bounded subprocesses. The additional tests can stay within the authorized
test file and avoid network access. They must observe failures rather than
replace the batch helper being tested.

## Limits and ownership

No blocking correction is required to the addendum. This review did not certify
the in-progress implementation or inspect unrelated changes as deliverables.
No runtime tests, full smoke, network operations, installation, source/test
edits, staging, or commits were performed. Only this new audit report was
written. The accepted original plan and its R0 audit remain unchanged; the
independent implementation audit must still verify the helper and test evidence.
