# Refactor Audit Stage 4: Developer And Helper Scripts

Date: 2026-06-01

This report audits developer-only and optional helper scripts for refactor
readiness. It covers `scripts/ci_run.sh`, `scripts/helm_chart_diff.sh`,
`scripts/ssh_hosts.py`, `tools/generate-def.sh`, `tools/lib/generate-def/`,
and the GitHub helper boundary in `tools/lib/common/github.sh`. It does not
apply code changes.

## Findings

### 1. `tools/generate-def.sh --help` exits as a failure

Risk: low

References:

- `tools/generate-def.sh:20-31` implements `usage()` and always exits `1`.
- `tools/generate-def.sh:44-45` routes `-h|--help` through `usage`.
- `tools/generate-def.sh:75-76` does the same after a valid repo argument.

This is a developer CLI rather than a runtime command, but help should be a
successful path. The current shape also makes usage printing hard to reuse from
tests because parse errors and help both terminate the process directly.

Suggested order:

1. Add a focused test for `tools/generate-def.sh --help` returning `0`.
2. Split help printing from error exits.
3. Keep invalid argument paths returning non-zero.

### 2. GitHub release asset parsing can collect non-asset `name` fields

Risk: medium

References:

- `tools/lib/common/github.sh:55-61` extracts every JSON `"name"` field after
  splitting the response on commas.
- `tools/lib/common/github.sh:114-116` stores those parsed names in
  `GITHUB_ASSETS` for latest releases.
- `tools/lib/common/github.sh:145-147` uses the same parser for tagged
  releases.
- `tools/lib/generate-def/assets.sh:39-67` assumes the input list is release
  asset names and maps matching names into `ASSETS`.

GitHub release JSON has `"name"` fields outside `assets[]`, such as release
display names and user names. Those can enter `GITHUB_ASSETS`. The asset
filtering step often discards them, but the generator is still relying on a
non-asset-aware parser for the core release manifest contract.

Suggested order:

1. Add a fixture with release-level and uploader-level `"name"` fields.
2. Replace the heuristic parser with a scoped parser for `assets[].name`, using
   a developer-only dependency if the project accepts one.
3. Preserve the existing digest behavior and exact manifest rendering.

### 3. `ci-run` normalizes repositories for the API but not for suggested log commands

Risk: medium

References:

- `scripts/ci_run.sh:82-99` normalizes repository inputs into `owner/repo` for
  GitHub API paths.
- `scripts/ci_run.sh:202-207` rejects unsupported repository formats after
  normalization.
- `scripts/ci_run.sh:247-252` prints the normalized `repo_path` in the report.
- `scripts/ci_run.sh:291-293` builds suggested `gh run view` commands with
  the original `repo` value.

When the user passes a supported non-canonical value such as
`github.com/owner/repo`, the API call uses `owner/repo`, but the suggested
commands can still include the original form. When repo is inferred from Git,
the suggested commands omit `--repo` entirely and rely on the current working
directory. That may be acceptable inside the checkout, but it is different
from the normalized report output and makes copied commands less portable.

Suggested order:

1. Add tests for log command output with `--repo github.com/owner/repo` and
   inferred repos.
2. Decide whether suggested commands should always use normalized `owner/repo`.
3. Keep API endpoint normalization behavior unchanged.

### 4. `helm-chart-diff` normalized mode is a line-oriented heuristic that can hide YAML semantics

Risk: medium

References:

- `scripts/helm_chart_diff.sh:124-132` removes comments and blank lines, trims
  trailing whitespace, and sorts each YAML file line-by-line.
- `scripts/helm_chart_diff.sh:135-153` copies non-YAML files but applies that
  normalization to every `*.yaml` and `*.yml` file.
- `scripts/helm_chart_diff.sh:484-489` makes normalized mode the default.
- `scripts/helm_chart_diff.sh:382-384` exposes `--raw` as the escape hatch.

This behavior is useful for noisy generated charts, and existing tests lock in
the current order/comment normalization. It is still not YAML-aware: quoted
hashes, block scalars, duplicate keys, multi-document files, and list ordering
can be changed or hidden by sorting and comment stripping. That makes the
default diff potentially misleading for charts where ordering or quoted content
matters.

Suggested order:

1. Add tests for quoted `#`, lists, block scalars, and duplicate keys to define
   expected normalized-mode limits.
2. Decide whether normalized mode should stay the default or become explicitly
   labeled as heuristic in output/docs.
3. Consider a parser-backed normalizer only if developer dependency policy
   allows it.

### 5. `helm-chart-diff` mixes execution, manual command rendering, and parsed GitHub state

Risk: low

References:

- `scripts/helm_chart_diff.sh:44-104` renders manual commands and duplicates
  pull, extract, fetch, normalize, and diff command knowledge.
- `scripts/helm_chart_diff.sh:60-70` reads `GITHUB_CHART_REPO` and
  `GITHUB_CHART_PATH` globals instead of deriving everything from parameters.
- `scripts/helm_chart_diff.sh:188-203` parses `--github-chart` by mutating
  those same globals.
- `scripts/helm_chart_diff.sh:424-432` parses GitHub chart state before
  execution, and `scripts/helm_chart_diff.sh:479` later renders manual
  commands from that state.

The helper is well tested, but the main script still concentrates CLI parsing,
IO, network fetch, archive handling, normalization, diff execution, and
manual-command rendering in one file. The global GitHub state is a refactor
risk because the command renderer is coupled to an earlier parse side effect.

Suggested order:

1. Keep current behavior while adding tests for manual command output when the
   GitHub chart parser changes.
2. Move GitHub chart parsing to return explicit `repo|path` data before
   extracting rendering helpers.
3. Split command rendering from execution only after output tests are stable.

### 6. `ssh_hosts.py` is script-shaped but has library-shaped global state

Risk: low

References:

- `scripts/ssh_hosts.py:10` defines module-global `SEEN_FILES`.
- `scripts/ssh_hosts.py:13-28` mutates that global while parsing includes.
- `scripts/ssh_hosts.py:42-53` strips comments with `raw.split("#", 1)` before
  shell-style parsing.
- `scripts/ssh_hosts.py:98` calls `parse_config` once in normal script usage.

The current `ssh-pick` flow executes the parser as a separate process, so the
global state does not leak between invocations. If this code is imported or
unit-tested more directly later, repeated parser calls in one process can
reuse stale visited-file state. The comment stripping also ignores quoted `#`
characters even though `shlex.split` would otherwise handle shell quoting.

Suggested order:

1. Keep the explicit optional `python3` dependency documented.
2. Add parser tests for quoted `#`, repeated calls in one process, and include
   cycles before making parser changes.
3. Pass a `seen` set through recursive parsing if the parser becomes a reusable
   library function.

## Refactor Candidates

- Normalize help/error handling in `tools/generate-def.sh` so help returns
  success and parse errors remain failures.
- Replace release JSON name scraping with asset-scoped parsing in
  `tools/lib/common/github.sh`.
- Make `ci-run` suggested log commands use the same normalized repository value
  as API calls and report output.
- Give `helm-chart-diff` explicit seams for GitHub chart parsing, source
  fetching, chart normalization, and manual command rendering.
- Define and document the limits of `helm-chart-diff` normalized mode before
  changing its default behavior.
- Make `ssh_hosts.py` parser state local to one parse operation if it becomes
  importable library code.

## Risk

| Area | Risk | Why |
| --- | --- | --- |
| GitHub asset parsing | medium | A broad `"name"` parser can pollute generated exact manifests before human review catches it. |
| `ci-run` log command repo normalization | medium | Suggested commands may not match the normalized repo used for the API call. |
| Helm YAML normalization | medium | Default normalized diffs can hide ordering or quoted-content differences. |
| Helm helper module boundaries | low | Existing tests are broad, but global parsed state makes extraction fragile. |
| `generate-def --help` exit status | low | Developer-only CLI consistency issue with a small fix surface. |
| `ssh_hosts.py` parser state | low | Current subprocess use is safe; import-style reuse would be fragile. |
| Runtime dependency boundary | low | Developer-only dependencies stay in `scripts/` and generator code; no Stage 4 issue requires runtime dependency changes. |

## Test Coverage Needed

Existing useful coverage:

- `dev/tests/test_ci_run.py` covers help, missing repo, pass/fail/pending/no
  match statuses, literal filtering, API endpoint construction, log command
  rendering for canonical repos, `--all`, missing `gh`, and `gh` failures.
- `dev/tests/test_helm_chart_diff.py` covers help, source validation,
  local-chart and GitHub-chart flows, raw and normalized diffs, non-YAML files,
  `Chart.yaml` path inputs, `~` expansion, missing paths, GitHub token handling,
  missing chart dirs, and missing `helm`.
- `dev/tests/test_ssh_helpers.py` covers SSH config parsing with includes,
  `ssh-pick` default flow, and parser failure warnings.
- `dev/tests/test_generate_def.py` covers the Atuin render fixture, digest
  parsing, inferred tool names, and release tag parsing.
- `dev/tests/test_scripts_command.py` covers the public scripts listing and
  moved scripts guide message.

Targeted tests to add before follow-up refactors:

- `tools/generate-def.sh --help` returns `0`; invalid generator arguments keep
  returning non-zero.
- GitHub release parsing ignores release-level, author-level, and uploader
  `"name"` fields while preserving `assets[].name`.
- `ci-run` suggested log commands use normalized `owner/repo` for URL-style
  `--repo` inputs and for inferred GitHub remotes if that policy is chosen.
- `helm-chart-diff` normalized mode handles or explicitly exposes limitations
  for quoted `#`, list ordering, block scalars, duplicate keys, and
  multi-document YAML.
- `helm-chart-diff` manual command output stays stable while GitHub parsing and
  command rendering are split.
- `ssh_hosts.py` handles quoted `#` as part of tokens and repeated
  `parse_config` calls in one process.

No `just smoke` or `just test-assets-live` was run for this audit-only stage.

## Suggested Order

1. Fix `generate-def --help` exit status with a narrow subprocess test.
2. Add GitHub JSON fixtures and replace broad `"name"` scraping with scoped
   asset parsing.
3. Normalize `ci-run` suggested repository arguments after tests cover
   canonical, URL-style, and inferred repos.
4. Define `helm-chart-diff` normalized-mode limits with edge-case tests before
   changing its implementation or output language.
5. Refactor `helm-chart-diff` parsing and manual-command rendering into smaller
   functions once output tests pin the behavior.
6. Make `ssh_hosts.py` parser state local if the parser grows beyond
   subprocess-only use.
7. Keep Stage 4 developer dependencies isolated from runtime install and shell
   startup paths.
