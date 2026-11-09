# Interactive editor and completion performance pilot

Executed: 2026-11-08. Local developer measurements; no runtime integration shipped.

On this macOS host, ble.sh adds measurable startup, memory, and input costs.
Its warm-cache startup is substantially faster than its first-home startup.
Disabling automatic completion did not materially improve this fixture's input
latency. Zsh with a highlighting plugin was lighter in this comparison and
preserved the tested vi operation. Flyline was faster than ble.sh for ordinary
input but still failed that operation. These are local observations, not Linux
or SSH performance guarantees.

Carapace and flycomp provide completions; they are not alternative syntax
highlighters. Their costs are measured separately below.

The later [completion-provider pilot](completion-provider-pilot.md) compares
argc, Carapace, and native scripts across Git, ripgrep, and fd with genuine Tab
and vi controls, candidate coverage checks, and a static-query memory probe.

## Host and inputs

- MacBookPro18,3, arm64, 10 physical CPU cores, 16 GiB RAM; macOS 27.2.
- Homebrew Bash 5.3.20(1), system zsh 5.9, Python 3.15.2, ripgrep 15.2.0.
- ble.sh `0.4.0-nightly+1529427`, downloaded built nightly package.
- Flyline 1.9.0, native macOS arm64 Bash library.
- Carapace Bin 1.8.2; flycomp 1.1.2 (`9840f7b`).
- zsh-syntax-highlighting 0.8.0, sourced directly with its default highlighters.

Exact archive and executable hashes, release asset identifiers, the generated
completion input, and checkout shell-file hashes are in
[input-manifest.json](interactive-tools-performance-evidence/input-manifest.json).
The nightly release label is mutable: its package digest and embedded commit,
rather than the label alone, identify the tested ble.sh input. No source builds
or upstream installers were used. Binaries stayed in a temporary developer
directory, outside the managed installation prefix.

## Editor results

Medians; lower is faster. Startup is elapsed time from PTY creation until an
initial queued `printf` command executes. Key latency is time until one appended
ASCII character appears in the terminal model, not completion of every later
highlighting or background task. RSS is the resident memory of the shell
process after startup, including a loaded native library, excluding transient
child processes. MiB means 1024 squared bytes.

| Session | Startup, fresh HOME (ms) | Startup, reused HOME (ms) | One key, reused HOME (ms) | Shell RSS, reused HOME (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Bash / Readline | 20.1 | 23.9 | 0.11 | 7.1 |
| Bash + Carapace | 36.9 | 41.8 | 0.09 | 7.7 |
| Bash + pre-generated flycomp `rg` completion | 22.2 | 24.1 | 0.10 | 7.3 |
| Bash + ble.sh defaults | 1730.3 | 398.1 | 14.60 | 23.3 |
| Bash + ble.sh, automatic completion disabled | 1735.6 | 407.5 | 14.27 | 23.2 |
| Bash + minimal ble.sh + Carapace | 1759.4 | 414.7 | 14.84 | 23.4 |
| Bash + minimal Flyline | 35.5 | 32.7 | 0.35 | 10.9 |
| Zsh / ZLE | 22.2 | 22.4 | 0.11 | 3.1 |
| Zsh + zsh-syntax-highlighting | 49.9 | 50.2 | 1.44 | 4.1 |
| Controlled remote-ssh Bash session | 174.5 | 130.8 | 0.07 | 7.9 |
| Controlled remote-ssh + minimal ble.sh | 1911.2 | 513.1 | 14.52 | 23.6 |

The controlled remote-ssh case uses the checkout's `shell/rc.sh`, a fixed prompt,
and disabled welcome, update check, Atuin, and history import. The restricted
PATH excludes installed Starship, skim, zoxide, and other optional integrations.
It is a bounded integration comparison, not the normal fully equipped session.
Adding minimal ble.sh increased its median reused-HOME startup by about 382 ms
and shell RSS by about 15.7 MiB.

The reused-HOME ble.sh default startup observations ranged from 391 to 420 ms.
The fresh-HOME median was 1730 ms. A single first-run measurement would therefore
misrepresent subsequent launches. Fresh HOME does not mean a cold OS page cache.

### Raw-input stress fixture

An unbracketed burst containing 4096 `x` characters plus an end marker was sent
through the PTY. Reused-HOME medians: Readline 16.8 ms; ble.sh defaults 2503 ms;
minimal ble.sh 2480 ms; Flyline 1186 ms; ZLE 217 ms; ZLE with highlighting 918 ms.
There are only two stress observations per case/HOME state. This intentionally
unfavorable input stream is not a normal bracketed clipboard paste benchmark.
It does show that short-input results cannot predict long-line behavior.

## Completion providers

The controlled candidate request is `rg --reg`, requiring `--regexp` in the
result. Each result was checked, rather than accepting a fast empty response.
The same installed `rg` was used for both providers.

| Operation | Median (ms) | Samples | What is included |
| --- | ---: | ---: | --- |
| Carapace `rg export rg --reg` | 13.24 | 10 | Fresh process and JSON candidates |
| Carapace Bash initialization script | 11.82 | 10 | Fresh process; script generation, excluding shell evaluation |
| flycomp generates Bash completion from `rg --help` | 36.71 | 10 | Fresh process, help execution, parsing, output |
| Calling the generated flycomp `_rg` function | 1.00 | 95 | Candidate calculation inside an existing Bash process |

The last two rows describe different stages. A generated script can be sourced
once and reused; generation need not happen on every Tab. Carapace's process
cost also does not occur on every ordinary keystroke. These figures do not
compare complete interactive Tab menus or dynamic completions across programs.

flycomp used `--strategy run-help --recurse-limit 0 --no-sandbox` for the known
local `rg --help` invocation. No agent or LLM was used. The generated fixture
omitted `--version` even though ripgrep supports it: the initial `--ver` validity
check failed, and the shared supported `--reg` prefix was selected instead.
Low latency does not establish equivalent coverage or completion quality.

The editor benchmark also checked a single local filename completion. Its raw
results include shell dispatch and rendering; it is a different workload from
the provider-only `rg` request above.

## vi compatibility control

The [separate probe](interactive-tools-performance-evidence/vi_probe.py) types
`pilot_capture ac`, Escape, `hrbA`, Enter. The command must receive `bc`.
It checks the actual argument emitted by a shell function.

| Editor | Actual argument | Result |
| --- | --- | --- |
| Readline | `bc` | Pass |
| Minimal ble.sh | `bc` | Pass |
| Minimal Flyline | `achrbA` | Fail |
| ZLE + zsh-syntax-highlighting | `bc` | Pass |

See [vi-results.json](interactive-tools-performance-evidence/vi-results.json).
This is one modal editing operation, not a complete vi compatibility suite.
The previous [Flyline pilot decision](flyline-pilot-record.md) remains in force.

## Method and limits

The [standard-library benchmark](interactive-tools-performance-evidence/benchmark.py)
runs 11 cases in separate 120-column, 30-row PTYs. Each has a minimal allowlisted
environment, temporary HOME/XDG directories, empty history, and vi requested.
The terminal model responds to DA2 as xterm `0;370;0` and to cursor-position
queries at the actual modeled cursor position. All ble.sh samples recorded one
DA2 reply and 20 cursor-position replies. This avoids measuring a deliberately
unanswered terminal probe. Parser controls covered cursor position and scroll
regions. The model is sufficient for these ASCII fixtures, not a complete
terminal emulator or a pixel-rendering measurement.

There are two excluded warmup rounds and ten measured rounds, with deterministic
random case order. Each round uses both a new HOME and a persistent per-case
HOME. Startup/RSS have ten measured observations per case/HOME state; short
bursts and individual keys have thirty; long input has two. All 264 editor
sessions completed the execution, input-rendering, and file-completion checks.
The provider loop then uses fresh processes and a shared isolated HOME; its two
warmup calls are excluded. Generated-script queries run in one Bash process,
with the first five of 100 calls excluded.

This was a multitasking developer laptop, without CPU pinning, repeated host
runs, or exclusive resource reservation. The short vi control ran independently
during the series. Small sub-millisecond differences should not be ranked.
Summary JSON includes p95, but ten startup samples are too few for robust tail
latency claims. Session CPU and peak RSS are retained as diagnostic data; the
sessions include different stress workloads and are killed after observation,
so those totals are not idle CPU or clean-shutdown measurements.

Unverified: Linux glibc/musl, low-power servers, Bash 3.2, SSH RTT/bandwidth,
tmux/zellij, long history, large directories, network filesystems, real terminal
painting, Atuin/Starship/skim interactions, and full zsh completion initialization.
No zsh framework, `compinit`, or Carapace zsh integration was loaded. Remote-ssh
currently requires Bash in `shell/rc.sh`; the isolated zsh result does not
establish that the project's runtime can be switched to zsh.

## Decision for remote-ssh

Keep the existing runtime while evaluating alternatives. If retaining Bash
and vi is required, ble.sh is a plausible optional pilot, with a clear toggle
and a Linux benchmark before making it a default. The measured startup and
per-key costs argue against treating it as free on small remote hosts.

If changing the interactive shell is acceptable, a separate zsh backend with
zsh-syntax-highlighting merits investigation: it was materially lighter here
and passed the tested vi operation. That requires an explicit project design
for shell availability and compatibility. Flyline 1.9.0 remains unsuitable for
the accepted vi requirement. Carapace can be evaluated independently when richer
completion coverage is needed; flycomp can fill gaps through generated scripts,
with correctness checks for the commands selected.

## Reproduction and evidence

First obtain and verify the inputs named in the manifest. The scripts do not
download, install, edit startup files, or access real history. Set up an artifact
directory containing `ble-nightly/ble.sh`, `carapace`, `flycomp`, the tagged
`zsh-syntax-highlighting-0.8.0/` directory, and symlinks named `bash` and `rg`
to the tested executables. Copy the recorded
[pre-generated script](interactive-tools-performance-evidence/installed-rg-completion.bash.txt)
to `generated-rg-completion.bash` there.

```bash
python3 dev/docs/interactive-tools-performance-evidence/benchmark.py \
  --bash /absolute/path/to/bash --zsh /absolute/path/to/zsh \
  --artifacts /absolute/path/to/artifacts \
  --flyline /absolute/path/to/libflyline.dylib.1.9.0 \
  --repo /absolute/path/to/remote-ssh \
  --output /absolute/path/to/new-results --iterations 10 --warmup 2
```

Run `vi_probe.py` with the same path arguments and a separate `--output` directory
to reproduce the modal check. Native Flyline required an unrestricted local PTY;
the execution sandbox rejected terminal initialization in the earlier pilot.

Recorded evidence: [summary](interactive-tools-performance-evidence/report.json),
[raw samples](interactive-tools-performance-evidence/samples.json),
[fingerprints](interactive-tools-performance-evidence/fingerprints.json), and
escaped last-sample transcripts in `interactive-tools-performance-evidence/transcripts/`.
Transcripts retain only the last session per case, not every repetition.
Preflight runs, including an earlier incomplete terminal-response model, are
excluded from the published measurements.

Verification: Ruff format/check and mypy pass for both developer scripts;
terminal parser controls, sample-count/probe checks, evidence hashes, local
Markdown links, and `git diff --check` pass. This documentation/developer-only
pilot adds no runtime code. `just smoke` was not repeated; the existing two
Atuin PTY failures from the [prior run](flyline-pilot-record.md#repository-verification)
remain unresolved. `just test-assets-live` was not run.

Upstream references: [ble.sh performance guidance](https://github.com/akinomyoga/ble.sh/wiki/Performance),
[ble.sh nightly](https://github.com/akinomyoga/ble.sh/releases/tag/nightly),
[zsh highlighting](https://github.com/zsh-users/zsh-syntax-highlighting/tree/0.8.0),
[Carapace setup](https://carapace-sh.github.io/carapace-bin/setup.html),
[flycomp](https://github.com/HalFrgrd/flycomp), and
[Flyline 1.9.0](https://github.com/HalFrgrd/flyline/releases/tag/v1.9.0).
