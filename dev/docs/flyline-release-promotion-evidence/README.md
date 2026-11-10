# Public Flyline R5 installation evidence

Date: 2026-11-10. Platform: macOS arm64, Homebrew Bash 5.3.20.

- [Validation summary](validation.json) and [full smoke log](full-smoke.log): final 1593 passed, 56 skipped.
- [Release input](release-input.json): public release metadata and exact tag commit.
- [Definition comparison](definition-comparison.json): generated fields match the prepared candidate.
- [Native lifecycle](public-release-lifecycle.json): 22 checks passed with the unchanged production definition.
- [Probe source](probe.py): the exact script used for this native run.
- Logs retain install, skipped reinstall, forced reinstall, checksum rejection and uninstall.
  `$RUNTIME` replaces the disposable runtime path in saved logs.

The probe copies the checkout into an isolated home, prefix and XDG configuration,
uses the real launcher and installer, and forwards the exact release URL to real
curl. It records the downloaded archive's hash and observes the production library.
A fixture-only OS hook supplies a known prompt, capture function and completion;
the production definition, installer and editor modules are copied unchanged.
The corrupted-download case intercepts curl in this disposable environment only.

The public CLI correctly skips an already valid pinned installation. The separate
pinned installer entrypoint is used to force a same-version reinstall and to
exercise checksum rollback. The old library remains intact until uninstall.
Fresh shells verify explicit disable and missing-library Readline recovery.

To reproduce on the qualified local platform, choose a new, empty output directory:

```bash
mkdir -p /private/tmp/flyline-r5-public-check
python3 dev/docs/flyline-release-promotion-evidence/probe.py \
  "$PWD" /private/tmp/flyline-r5-public-check
```

The probe uses network access and disposable PTYs. It does not establish Linux,
Intel macOS, other Bash builds, SSH transport or performance qualification.
Native bytes and previous qualification evidence are unchanged.
