# fzf retirement phase 1 evidence

Date: 2026-11-10. This verifies the migration window; host migration is pending.

- [Validation summary](validation.json) and [smoke log](smoke.log): 1615 passed, 56 skipped.
- [Pinned recovery](pinned-recovery.json) verifies the exact documented revision
  `c5fa54c70fba2ca931af5b241f166fb6bec98a06` on Bash 3.2.57 and 5.3.20.
- [Probe source](probe.py) is the exact script used, including the local Git clone.
- [Bash 3.2 cleanup log](case-0.log) and [Bash 5.3 cleanup log](case-1.log)
  retain the selected files and expected-tools update. `$RUNTIME` replaces
  the disposable run directory.

The probe simulates a latest checkout without the fzf definition. Its uninstall
rejects the unknown tool without mutation. Invoking the old CLI with the latest
REMOTE_ENV_DIR also rejects it; explicitly selecting the pinned recovery checkout
removes only owned fzf. Skim, external fzf, a custom prefix with spaces and the
unrelated .active sentinel remain intact. Expected-tools becomes sk.

The clone is local and offline. No real host, installed tool or user configuration
is migrated. The two CLI cases use synthetic executables and ownership records.
The real Navi/skim integration is unchanged in this phase.

To reproduce, use a local checkout whose history contains the pinned revision
and select a new output directory:

```bash
mkdir -p /private/tmp/fzf-retirement-recovery-check
python3 dev/docs/fzf-retirement-evidence/probe.py \
  "$PWD" /private/tmp/fzf-retirement-recovery-check
```
