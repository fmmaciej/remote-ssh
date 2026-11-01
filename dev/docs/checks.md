# Checks And Tests

Back: [Developer tooling](../README.md)

`just smoke` is the default verification for normal changes:

```bash
just smoke
```

It runs static Bash checks, `shellcheck`, `ruff`, `mypy`, and the pytest suite
under `dev/tests/`.

## Focused Checks

```bash
just lint
just fmt
just type
just test
```

From `dev/`, the same checks can be split further:

```bash
just py-lint
just py-fmt
just py-type
just py-test
just sh-lint
just sh-fmt
```

## Test Guidance

Prefer pytest tests under `dev/tests/` for new behavior that can exercise public
commands as subprocesses. Tests may launch Bash subprocesses when they need to
source shell functions, rc files, aliases, or tool definitions.

Keep developer-only helpers in `dev/`; do not make remote runtime shell code
depend on `dev/` files.

## Navi And Skim

The session integration targets the versions pinned in `tools/defs/navi.sh`
and `tools/defs/sk.sh` (currently navi 2.23.0 and skim 5.9.0). It supports:

- Snippet selection and ordinary commands returned by `navi --print`.
- Suggested or free-text parameters, Enter/Tab acceptance, cancellation, and
  automatic acceptance of a single match.
- Spaces and apostrophes in parameter values, with appropriately quoted
  cheatsheet placeholders. Navi substitutes text; the adapter does not add
  shell quoting to cheatsheets.
- Nested navi execution within the original process tree.
- Top-level explicit native fzf selection, without requiring skim.

This is a bounded adapter for navi, not a general implementation of fzf's CLI.
Mixed finders at arbitrary nesting levels, shell widgets, other upstream
versions, and arbitrary fzf options are outside the contract. A nested navi
command emitted by `--print` contains the original executable's absolute path.
Running it later in the parent shell loses the scoped adapter environment and
can produce empty parameter values. Do not rewrite arbitrary returned commands
to cover this limitation.

### Adapter Responsibilities

`shell/navi-bin/navi` resolves real binaries, preserves CLI values as data,
and scopes the private PATH to navi and its children. It selects navi's fzf
protocol because the pinned native skim path omits the free-text input flags.
`NAVI_FINDER=fzf` and `REMOTE_SSH_NAVI_PROTOCOL=skim` preserve that protocol in
absolute self-invocations. They do not change the calling shell.

`shell/navi-bin/fzf` translates the expected-key bindings and single-result
output needed by that protocol. Navi supplies CLI arguments for its own finder
overrides. Global `SKIM_DEFAULT_OPTIONS` and `SKIM_OPTIONS_FILE` are deliberately
isolated: they can add query/key output or automatic selection behind navi's
back. The adapter sets `--height=40% --reverse --border` instead of duplicating
skim's configuration parser. Standalone `sk` keeps its normal settings.

### Offline Acceptance Tests

The default pytest suite uses stubs for argument forwarding, exit status,
process scoping, and native finder bypass. Real-binary tests are separate and
skipped with an explicit reason unless both executable paths are supplied:

```bash
cd dev
uv run pytest -q tests/test_navi_skim_real.py \
  --navi-bin /absolute/path/to/navi \
  --skim-bin /absolute/path/to/sk
```

No binaries are downloaded and there is no PATH fallback. Supplying only one
path, an invalid executable, or a version different from the tool definition
fails the run. Use binaries from the pinned releases and a host that permits
PTY applications. A picker crash or missing terminal support is a failed
verification, not a passing test or a reason to substitute a stub.

The tests use isolated HOME/configuration and the shared PTY helper, run on
each available runtime Bash, and check real snippet selection, parameter input,
Enter/Tab, cancellation, single matches, ordinary printed command execution,
and nested execution. Parameter acceptance is checked both with navi's default
`--select-1` and with automatic selection disabled, including Enter, Tab,
custom text, and cancellation with multiple suggestions. Conflicting global
skim defaults are deliberately set to verify that navi remains isolated.
Native fzf bypass is covered by the default subprocess tests.

Finish changes with this acceptance suite and a complete `just smoke`. Fix
failures within this contract; record new out-of-scope requirements in
`docs/TODO.md` instead of extending the adapter during every review round.
