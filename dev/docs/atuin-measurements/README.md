# Atuin startup simplification evidence — measurements before repair 1

The startup `before-*.json` / `after-*.json` series measures the initial
implementation **before repair round 1 (A1/A2)**. Its after-series source matches
`/tmp/remote-ssh-atuin-pre-repair1`, not the repaired runtime. Raw samples and
fingerprints remain historical evidence; no repaired-state startup speedup is
claimed. The old `recording-bash*.json` files also describe the initial revision.

Measured locally on 2026-11-01 using real pinned Atuin 18.14.1, macOS arm64,
Bash 3.2.57 and 5.3.20. The paired `before-*.json` and `after-*.json` files
retain every measured sample, output tails, source SHA-256 fingerprints,
interpreter version, Atuin version and binary SHA-256. No tests or other agent
work ran concurrently with this final serial before/after measurement pass.
`initial-before-bash32.json` is the additional baseline captured before any
runtime edits; the final paired baseline reruns its saved source snapshot.

The developer-only wrapper [measure_atuin_startup.py](../../measure_atuin_startup.py)
reuses the existing `just bench-shell` PTY runner, `remote-ssh-min` arguments,
and environment builder. It does not change public benchmark scenarios. Each
case has two discarded warmups followed by 15 recorded samples, with a fresh
isolated HOME/XDG tree per sample. Warmups warm process/file caches; they do
not pre-initialize the subsequently measured HOME or first-use import state.
The recorded `warmup` field is the count; discarded warmup timings are not
included in the JSON distributions.

PATH contains only the sample's Bash/optional Atuin symlinks and `/usr/bin:/bin`.
Welcome, update checks, Git identity injection and user config loading are off.
No user history or credentials are used. Atuin-disabled still has the binary;
absent omits it; working-preseed has the auto-import marker and an initially
absent database; first-import has no marker and exactly one Bash history line.
All cases begin without credentials, sessions, caches, or existing DB records.
The samples compare startup/source cost with empty data; they do not benchmark
large databases or per-command recording. Operating-system caches are not
flushed, and before/after order can still affect host-level noise.

Ready time in milliseconds: median (interquartile range).

| Bash | Case | Before | After |
| --- | --- | --- | --- |
| bash32 | disabled | 100.4 (99.9–102.5) | 99.8 (97.9–103.4) |
| bash32 | absent | 102.1 (100.6–105.0) | 99.4 (96.5–104.8) |
| bash32 | working-preseed | 357.2 (351.1–364.3) | 141.9 (135.9–148.3) |
| bash32 | first-import | 387.5 (375.0–399.3) | 158.5 (155.4–161.6) |
| bash53 | disabled | 116.9 (111.1–124.4) | 111.6 (109.4–118.5) |
| bash53 | absent | 111.9 (110.0–119.8) | 107.9 (106.4–110.9) |
| bash53 | working-preseed | 363.0 (358.2–374.5) | 149.3 (147.8–160.9) |
| bash53 | first-import | 383.5 (372.2–393.1) | 170.1 (155.1–174.7) |

The working Atuin startup distribution is substantially lower on this host.
Disabled/absent results should be read with their spread and host noise; there
is no universal threshold or promised speedup. Per-command duration collection
and database recording remain upstream behavior and were not timed as latency
benchmarks.

The source snapshot is `/tmp/remote-ssh-atuin-before`; it contains the original
working tree including the ongoing skim migration, plus its Git diff/status.
`/tmp/remote-ssh-atuin-implementation.diff` separates this implementation from
that baseline. The snapshot is local review evidence, not a portable checkout.
The JSON fingerprints let a reviewer verify the specific measured shell state.

The isolated [verify_atuin_recording.py](../../verify_atuin_recording.py) check
used two real PTY sessions sharing one temporary HOME/database on each Bash.
`recording-*.json` records the two completed rows: distinct session IDs, shared
history DB, directory, nonempty host, exit status 7 and nonnegative duration.
Commands containing toggle changes and `rcrc` finish through upstream hooks.
The check also preserves the user-facing `?` binding and exercises literal `$?`.

The full 18.14.1 CLI appends AI glue to the shell source unless `--disable-ai`
is passed. That suffix is outside the unmodified offline `atuin.bash` fixture.
`test_atuin_real.py` separately checks the full generated initializer with an
explicit local pinned binary. No Atuin/vendor fixture was edited.

Reproduce one pair after preserving a baseline checkout:

```bash
python3 dev/measure_atuin_startup.py --repo /tmp/remote-ssh-atuin-before --bash /bin/bash --atuin /path/to/atuin --output /tmp/before.json
python3 dev/measure_atuin_startup.py --repo . --bash /bin/bash --atuin /path/to/atuin --output /tmp/after.json
python3 dev/verify_atuin_recording.py --bash /bin/bash --atuin /path/to/atuin --output /tmp/recording.json
REMOTE_SSH_TEST_ATUIN_BIN=/path/to/atuin UV_CACHE_DIR=/tmp/remote-ssh-uv-cache uv run --project dev pytest -q dev/tests/test_atuin_real.py
```


## Repair round 1 validation

Repair 1 makes temporary bind interception safe for a `bind` alias and rejects
a readonly `bind` function before requesting Atuin init code. It preserves the
alias, `expand_aliases`, function definition and existing export attribute.
`test_atuin_bind_ownership.py` adds the A1/A2 matrix plus actual private-key and
Ctrl-R actions after failed/rejected startup, exported-function preservation,
and exit-7 recording after successful aliased startup/reload. Tests use Bash
3.2.57 and 5.3.20, the unmodified offline fixture, and the existing PTY helper.
A reload deliberately restores the module's vi editing mode, so the emacs-map
keypress checks select emacs again before invoking that map's private action.

`recording-round1-bash32.json` and `recording-round1-bash53.json` refresh the
isolated real 18.14.1 shared-database/two-session check on the repaired runtime.
The separate full real-CLI test still checks all three disable flags, including
the AI suffix outside the offline fixture. Startup timings were not repeated
for repair 1. The previously documented transient parent-only replay limitation
remains outside this repair; deterministic interception failures are covered.
