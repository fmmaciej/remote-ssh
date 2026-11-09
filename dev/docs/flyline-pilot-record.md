# Flyline Compatibility Pilot

Status: stopped at the vi compatibility gate; runtime integration not shipped
Candidate: Flyline v1.9.0, upstream build commit `3b9e900`
Executed: 2026-11-08

The native library loads and accepts ordinary input on the tested modern Bash.
It does not preserve the project's vi editing behavior. The implementation
plan explicitly requires resolving that behavior before shipping Flyline.
This result stops the pilot before installer and session integration changes.

## Reproducible result

The [pilot script](flyline-pilot-evidence/pilot.py) runs four isolated PTY
scenarios. Each child has a temporary HOME, XDG directories, history file,
fixed `xterm-256color` terminal, and a Bash rcfile that enables `set -o vi`.
No user startup files are loaded. No completion providers or other shell
integrations are installed or initialized by the script.

| Editor | Input | Expected captured argument | Actual | Result |
| --- | --- | --- | --- | --- |
| Readline | `pilot_capture ac`, Enter | `ac` | `ac` | Pass |
| Readline | `pilot_capture ac`, Escape, `hrbA`, Enter | `bc` | `bc` | Pass |
| Flyline | `pilot_capture ac`, Enter | `ac` | `ac` | Pass |
| Flyline | `pilot_capture ac`, Escape, `hrbA`, Enter | `bc` | `achrbA` | Fail |

In vi command mode the cursor starts on `c`; `h` moves to `a`, `rb` replaces
that character with `b`, and `A` resumes insertion at the end. The same keys
are inserted as text by Flyline. The test checks the argument actually received
by a Bash function, rather than inferring behavior from terminal rendering.
The passing Readline comparison validates the input sequence and PTY setup.

See [results.json](flyline-pilot-evidence/results.json) and the
[escaped PTY transcripts](flyline-pilot-evidence/transcripts.txt). The Flyline
version output identifies the actual loaded library and upstream build.
The script and captured files have recorded
[SHA-256 fingerprints](flyline-pilot-evidence/fingerprints.json).

## Tested support row

| Platform | Bash | Artifact | Load/plain input | vi editing |
| --- | --- | --- | --- | --- |
| macOS arm64, kernel 27.2.0 | Homebrew Bash 5.3.20(1), aarch64 | `libflyline-v1.9.0-aarch64-apple-darwin.tar.gz` | Pass | Fail |

Linux glibc, Linux musl, macOS x86_64, legacy Bash, SSH, tmux, and zellij are
unverified. Atuin, skim, Starship, history persistence, completion behavior,
unload/reload, and performance remain unverified because the vi gate failed
first. This is not a completed support matrix or a performance claim.

The first native attempt inside the execution sandbox was denied terminal
initialization by the OS and did not reach the editor. It is recorded in
[sandbox-load.txt](flyline-pilot-evidence/sandbox-load.txt). After explicit
permission, the PTY comparison ran outside that sandbox and produced the
results above. The sandbox error is distinct from the reproducible vi failure.

## Artifacts and source evidence

Downloaded into a temporary developer directory, never installed into the
user's managed tool prefix:

| Input | SHA-256 |
| --- | --- |
| Release archive | `e91b4738a62221dba93ab166ca3dbea131f81fb7690e8c838145690742cb6932` |
| Extracted `libflyline.dylib.1.9.0` | `d0026255e9e288aba220301b0b7ef1fdbcdbe6f321f0b0665136de0a07d09fca` |
| Tagged source archive from GitHub codeload | `7d0af846bbfaa48f4ebe3c78f24135f3a6298990cd98903c39601be89e510b71` |

The release archive digest matches its upstream `.sha256` sidecar. The archive
contains one member, `libflyline.dylib.1.9.0`. No upstream installer was run and
no source build was performed. Source inspection corroborates the native
result: the tagged default Escape binding toggles mouse behavior; it does not
enter Readline vi command mode. The declared binding contexts do not provide
that modal editing contract. See the tagged
[keyboard implementation](https://github.com/HalFrgrd/flyline/blob/v1.9.0/src/app/actions/keyboard.rs#L2445).

Reproduction, after separately downloading and verifying the named archive
and extracting its library into a temporary directory:

```bash
python3 dev/docs/flyline-pilot-evidence/pilot.py \
  --bash /absolute/path/to/compatible/bash \
  --library /absolute/path/to/libflyline.dylib.1.9.0 \
  --output-dir /absolute/path/to/new/pilot-results
```

The script intentionally reports individual outcomes in JSON instead of
treating the expected negative pilot result as a successful compatibility
check. It does not download or install anything. Binary artifacts are not
committed. Captured output uses an isolated home and contains no real command
history or credentials.

## Decision

The accepted [plan](flyline-implementation-plan.md#stage-0-build-and-validate-the-pr-candidate)
requires keeping vi behavior, with an explicit stop if it is unavailable.
After reviewing the native result, the user explicitly chose to retain vi and
end this task at the pilot report. Flyline v1.9.0 is therefore not being added
to the installer or session runtime. Revisit integration only with a compatible
candidate or a separately agreed change to the editing-mode requirement.

Subsequent direction: the user requested a new candidate based on the latest
stable release (1.10.0 on 2026-11-08) with a port of Vim PR #974. The updated
plan requires separate backport/build/native acceptance. This does not change
the 1.9.0 observations or establish support for the new candidate.

## Repository verification

- Pilot script: Ruff check/format and mypy pass.
- Local Markdown links, evidence fingerprints, result consistency, and
  `git diff --check` pass.
- `just smoke`: static checks pass; pytest reports 1326 passed, 30 skipped,
  and 2 failed. Both failures are in the existing
  `test_alias_failed_setup_preserves_private_shell_action_in_real_pty`
  test on Homebrew Bash 5.3.20 (`partial` and `readonly` variants), timing out
  while checking the preserved Ctrl-R action. That test and the shell runtime
  were not changed by this pilot; these failures remain unresolved.
- `just test-assets-live` was not run.

Upstream sources: [release](https://github.com/HalFrgrd/flyline/releases/tag/v1.9.0),
[archive checksum](https://github.com/HalFrgrd/flyline/releases/download/v1.9.0/libflyline-v1.9.0-aarch64-apple-darwin.tar.gz.sha256),
and [tagged README](https://github.com/HalFrgrd/flyline/blob/v1.9.0/README.md).
