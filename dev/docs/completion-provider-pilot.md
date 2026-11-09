# Bash completion provider pilot

Executed: 2026-11-08. Developer pilot; no installer or shell runtime changes.

Retaining Bash/Readline meets the editing-speed and vi requirements in this
pilot. Completion coverage and the cost of dynamic callbacks determine the
choice of provider. Rust alone did not predict the fastest complete response:
argc was fast and compact for simple requests, but its Git definitions needed
GNU awk and were slower than Carapace for branch completion.

## Tested configuration

MacBookPro18,3, macOS 27.2 arm64, 10 physical cores, 16 GiB RAM; Bash 5.3.20(1),
Apple Git 2.54.0 (Apple Git-157), ripgrep 15.2.0, fd 10.5.1, Python 3.15.2.

- argc 1.24.0, with argc-completions commit
  `19b70387dc288f2018d80a99062a62d2e5965ab2`.
- Carapace Bin 1.8.2, command-specific Bash initialization for `git`, `rg`, `fd`.
- Native scripts: the installed Apple Git completion script, plus output from
  `rg --generate complete-bash` and `fd --gen-completions bash`.
- Additional argc control: GNU Awk 5.4.1 added only to that case's PATH.

The baseline PATH contains the tested executables and `/usr/bin:/bin`, with
no GNU awk or yq. System awk, jq, and python3 are available on this host; the
test does not establish operation on hosts lacking those system executables.
Other Homebrew tools are excluded. The GNU awk variant adds only gawk. Each
session has temporary HOME/XDG
directories and an isolated Git repository with two branches, tracked files,
a modified file, and a directory containing a space. No SSH connection, real
history, user rcfiles, remote APIs, or shell frameworks are involved.

Exact hashes and input sizes are in the
[manifest](completion-provider-pilot-evidence/input-manifest.json).
argc was extracted from the checksum-verified official Homebrew bottle because
GitHub Release downloads repeatedly failed. It was not installed. An attempted
source build failed because the existing Cargo 1.78 cannot build the release's
dependencies; no Rust toolchain was updated. The argc runtime result uses the
prebuilt bottle, not that attempted build.

GNU awk was also extracted into a temporary directory. Its four Homebrew library
paths were relocated to already installed libraries, then its binary was signed
locally. The manifest records both the original bottle hash and the resulting
binary/library hashes. This is developer preparation, not a proposed remote
installer mechanism or an addition to the project's runtime dependencies.

## Startup, input, and memory

Medians from 15 measured fresh sessions per configuration; two warmup sessions
excluded. Startup ends when an initial queued command executes. Input latency
measures one appended ASCII character appearing in the PTY screen model.

| Configuration | Startup (ms) | One key (ms) | Shell RSS (MiB) |
| --- | ---: | ---: | ---: |
| Bash / Readline baseline | 11.09 | 0.065 | 7.08 |
| Native completion scripts | 16.81 | 0.069 | 8.12 |
| argc | 14.66 | 0.070 | 7.25 |
| argc + GNU awk | 14.57 | 0.066 | 7.25 |
| Carapace | 54.06 | 0.063 | 7.30 |

None of these providers replaces Readline or processes ordinary typing in this
configuration. The small differences in key latency should not be ranked.
Carapace startup here includes three separate `carapace <command> bash`
initializations; argc uses one initializer for the three commands. These are
the tested registration strategies, not intrinsic startup lower bounds. In
particular, this Carapace startup number is not the earlier pilot's single
`carapace _carapace bash` initialization.

Shell RSS excludes short-lived completion processes. A separate macOS
`/usr/bin/time -l` probe for a valid `rg --ver` candidate request measured median
maximum RSS of **2.77 MiB for argc** and **26.58 MiB for Carapace** (five samples
after one warmup). Sourcing the native script in a fresh Bash process used
7.06 MiB. That last process is only a measurement control: actual native static
completion runs inside the already existing shell. These memory observations
cover one static request, not peak memory across dynamic Git callbacks.

## Candidate latency and coverage

Each row checks that the required candidates occur as intact candidate values.
Times below are medians of 15 calls to the registered Bash callback, including
its subprocesses. `FAIL` denotes a consistently missing or broken required
candidate; failed responses are not ranked by speed.

| Request | Required candidate(s) | Native (ms) | argc (ms) | argc + gawk (ms) | Carapace (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| `rg --ver` | `--version` | 1.32 | 4.24 | 4.30 | 16.28 |
| `rg --color a` | `always`, `auto` | 1.22 | 20.66 | 20.71 | 15.85 |
| `rg --type py` | `py` | FAIL | 22.09 | 21.65 | 20.00 |
| `rg --file fixture_uni` | `fixture_unique.txt` | 2.11 | 4.37 | 4.48 | 15.66 |
| `rg --file fixture\ space/ma` | intact path to `match.txt` | FAIL | 4.45 | 4.37 | 15.50 |
| `fd --col` | `--color` | 1.08 | 3.89 | 3.83 | 15.52 |
| `fd --color a` | `always`, `auto` | 0.97 | FAIL | FAIL | 15.11 |
| `git swi` | `switch` | 16.07 | 59.53 | 54.53 | 53.87 |
| `git switch --det` | `--detach` | 30.41 | 11.62 | 11.31 | 24.72 |
| `git switch bench-` | both fixture branches | 54.03 | FAIL | 87.04 | 40.47 |
| `git restore fixture_uni` | modified tracked file | 16.94 | FAIL | 57.08 | 53.85 |

Each case produced the same pass/fail outcome in all 15 measured repetitions:

- Native scripts: **9/11** cases met the candidate expectations.
- argc without gawk: **8/11**.
- argc with gawk: **10/11**.
- Carapace: **11/11**.

This is a small fixture suite, not a percentage of all supported commands or a
guarantee of exhaustive correctness. It does not test descriptions, aliases,
Unicode, remote service completions, or all argument combinations.

The native ripgrep script splits the path containing a space into two candidate
values, and supplies no Python type candidate. The argc fd definition declares
`--color` without enumerating its values. argc's Git definitions call utility
functions using `gawk`; adding that executable makes both tested dynamic Git
cases pass. Thus the missing dependency and missing fd values are distinct
issues. The underlying definitions are retained unchanged throughout the pilot.

For Bash, argc uses `ARGC_COMPGEN_DESCRIPTION=0` here. With default descriptions,
some candidates include display prose in the returned strings. A preflight
caught this; the measured configuration disables descriptions rather than
stripping them in the benchmark or patching the provider.

## Real Tab and vi controls

One measured session per provider also exercised genuine Readline Tab, with
the resulting shell words checked from the modeled input line. This permits
equivalent quoting styles, while rejecting a path split into separate words.

| Provider | Version flag | fd option | Git branch | Plain path | Path with space | vi argument |
| --- | --- | --- | --- | --- | --- | --- |
| Native | Pass | Pass | Pass | Pass | Fail | `bc`, Pass |
| argc | Pass | Pass | Fail | Pass | Pass | `bc`, Pass |
| argc + gawk | Pass | Pass | Pass | Pass | Pass | `bc`, Pass |
| Carapace | Pass | Pass | Pass | Pass | Pass | `bc`, Pass |

The modal editing sequence is `pilot_capture ac`, Escape, `hrbA`, Enter. The
shell function must actually receive `bc`. All four provider configurations
passed. This covers that editing operation, not a complete vi compatibility
suite or the project's Atuin/skim bindings.

## Implication for remote-ssh

Keep Bash/Readline as the editor. These configurations preserve the tested vi
behavior and avoid the per-key cost seen with ble.sh.

For weak hosts, native completions remain attractive where their correctness
has been checked. A program-generated script still needs acceptance tests:
the ripgrep path example shows why generation alone is insufficient.

Carapace is the strongest ready-to-use candidate for broad coverage among the
tested choices. Its standalone completion process uses more memory, and its
simple flag requests are slower, but ordinary typing remains in Readline.
It is a reasonable optional provider where richer completion is wanted.

argc is compact and worth considering for selected commands, especially when
Rust is preferred. The tested collection is not a dependency-free, uniformly
complete replacement: dynamic Git needs GNU awk and fd needs a better value
definition. Prefer native Git/fd scripts where they work better. A mixed setup
is a possible follow-up, but that combined configuration was not benchmarked
here. No additional provider is being installed or selected as a default by
this report.

flycomp was already measured in the [earlier editor pilot](interactive-tools-performance.md#completion-providers).
Its pre-generated `rg` script was fast but omitted an option known to the real
program. It was not included in this new three-command suite. Generating and
validating scripts during development remains a possible way to keep generator
work away from weak hosts.

## Method, reproduction, and evidence

The [comparison script](completion-provider-pilot-evidence/compare.py) reuses the
previous pilot's [PTY helper](interactive-tools-performance-evidence/benchmark.py).
Both source hashes are recorded in the report. All 85 sessions completed;
candidate failures are explicitly retained in the data. There are 660 measured
callback requests, plus 88 warmup requests, 225 single-character observations,
20 real Tab controls, and four vi controls.

Providers run sequentially in seeded random order on a multitasking laptop.
Every session has a new HOME, so these are fresh configuration/cache directories;
the OS page cache was not flushed. No exclusive CPU reservation was made.

The callback timer uses Bash `EPOCHREALTIME`; it excludes terminal rendering and
callback lookup. During manual callback probes, `compopt` is a no-op because it
requires Readline's actual completion context. Only the file fallback relevant
to these fixtures is modeled. Manual `COMP_*` globals are cleared before the
separate real Tab controls, where the real `compopt` is used. Actual Tab timings
are retained as single observations, not reported as repeated latency estimates.
The candidate checks require expected values but do not exhaustively reject all
possible extra suggestions. The PTY model handles these ASCII fixtures and
cursor/erase operations; it does not measure terminal pixel painting.

Unverified: slow Linux servers, SSH RTT/bandwidth, glibc/musl support, Bash 3.2,
large repositories/directories, long input lines, tmux/zellij, and integration
with Atuin or skim. Existing macOS GNU-library availability should not be
assumed on remote hosts. The new results support a local architectural choice;
they do not establish performance budgets for weak remote machines.

Prepare an artifact root with `bin/{bash,git,rg,fd,argc,carapace}`, pinned
`definitions/`, `native/{git,rg,fd}.bash`, and `gnu-bin/gawk`. The manifest and
recorded native script snapshots identify the tested inputs. The script performs
no downloading, installation, or edits to user startup files.

```bash
python3 dev/docs/completion-provider-pilot-evidence/compare.py \
  --bash /absolute/path/to/bash \
  --root /absolute/path/to/artifacts \
  --output /absolute/path/to/new-results --iterations 15 --warmup 2
```

`--providers baseline native argc carapace` omits the GNU awk variant. Run
`memory_probe.py --root <artifacts> --output <new-memory.json>` separately on
macOS to repeat the static-query memory probe. Native PTY/usage inspection
required permission outside the execution sandbox in this environment.

Evidence: [summary](completion-provider-pilot-evidence/report.json),
[raw sessions and candidates](completion-provider-pilot-evidence/samples.json),
[memory probe](completion-provider-pilot-evidence/memory.json),
[input manifest](completion-provider-pilot-evidence/input-manifest.json), and
[fingerprints](completion-provider-pilot-evidence/fingerprints.json).
Escaped transcripts retain the first measured session per provider, including
real Tab and vi controls. Download credentials/tokens and binary archives are
not included in the repository.

## Repository verification

- Both developer scripts pass Ruff check/format and mypy, including the imported
  PTY helper in the type-check search path.
- Source fingerprints, session/sample counts, stable candidate outcomes, native
  script hashes, real Tab/vi observations, and local Markdown links checked.
- `git diff --check` passes.
- `just smoke` passes: **1406 passed, 30 skipped**, 325.77 seconds. It ran with
  an allowlisted environment to avoid passing unrelated credentials to test
  subprocesses. See the [recorded log](completion-provider-pilot-evidence/smoke.log).
  The two Atuin PTY failures in the earlier pilot were not reproduced in this
  run; this pilot did not change those tests or their runtime implementation.
- `just test-assets-live` was not run.

Upstream references: [argc](https://github.com/sigoden/argc),
[pinned completion definitions](https://github.com/sigoden/argc-completions/tree/19b70387dc288f2018d80a99062a62d2e5965ab2),
[Carapace setup](https://carapace-sh.github.io/carapace-bin/setup.html), and
[Bash programmable completion](https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion.html).
