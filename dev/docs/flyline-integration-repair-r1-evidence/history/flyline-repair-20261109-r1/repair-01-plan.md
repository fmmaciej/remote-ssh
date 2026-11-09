# Repair 01 — reduce equivalent initialization work

Basis: unchanged accepted R5 [manifest](baseline-1/baseline.json), original [execution mapping](plan-r0.md), and independent [audit 0](audit-0.md), finding `VAL-4-BUDGET`. This is an ordinary technical correction under the same requirements, not a new cycle or threshold waiver. Planner: `/root/flyline_planner`; implementer and integration owner: `/root/flyline_implementer`; independent auditor: `/root/flyline_auditor`; coordinator: `/root`.

## Cause and hypothesis

Two valid startup gates fail cold Atuin overhead. Repeated native configuration calls each rebuild and parse FlylineArgs. Exact pinned source at commit `d037c075ed30a61080873985ea2621d743ddfc64`, `src/cli.rs` SHA-256 `7974da24e519bf24e9d5f49f71050736b6ee322eaaf9e8e7788bd91bd221995e`, supports equivalent batching: globals apply before SetCursor; Key applies vim_mode before Bind. Removing two native calls on bound profiles and one captured type subprocess may improve startup. No speedup or complete root cause is claimed before measurement.

## Changes and ownership

1. Keep `flyline run-tutorial false` first. Combine the existing global options with following `set-cursor --backend terminal`, preserving order and all option values.
2. For managed Atuin or Bash/skim, combine `key --vim-mode true` with the first existing `vimInsertMode` Ctrl-R binding; retain its exact callback/action and subsequent Emacs binding. For NOBIND or no widget, retain standalone explicit Vim enable. Bound profiles use six native calls rather than eight; unbound profiles use five rather than six.
3. Replace captured `type -t flyline` with direct read-only builtin `declare -F flyline` and `alias flyline` guards. Retain exact enabled/disabled `enable -a` inspection. Ordinary executables do not imply external builtin ownership.
4. Leave F4 attribute snapshots and restoration unchanged. Direct `${var@a}` is excluded because GNU Bash history changes exported-unset behavior after 4.4 and nounset expansion is not equivalent.

Implementer owns `shell/rc.d/29-flyline.sh`, necessary `dev/tests/test_flyline_lifecycle.py` changes, native ownership/settings equivalence probe additions, repair results/evidence and current status documentation. No uninstall change is needed. Evidence belongs under `dev/docs/flyline-integration-repair-r1-evidence/repair-01/`; earlier evidence and audited round-0 subject stay immutable. Coordinator owns cycle history and permission-conduit execution.

## Ordered verification

1. Default subprocess/PTY matrix on system Bash 3.2 and Homebrew Bash 5.3: all F1–F4 contracts, real function/alias exclusion, enabled/disabled builtin, late Atuin, reload, nested shell, stale markers, exact variable rollback and failed unload. Add combined global/cursor and Vim/bind failure cases with fallback/rollback.
2. With exact unchanged R5 library, compare actual `flyline settings --all` and key bindings between frozen round-0 module and repaired module for managed Atuin, skim, ATUIN_NOBIND and no-widget profiles. Verify effective state and behavior, not call counts alone.
3. Native ownership gate, lifecycle/Readline recovery and managed Bash/skim/Atuin history. Verify R5 library SHA remains `ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57`. Semantic/native checks precede sampling.
4. Exactly one complete acceptance measurement on changed source: eight scenarios, 20 measured rounds, two warmups, original 30 ms median / 60 ms p95 overhead limits, budgets saved before sampling. No concurrent tests, dropped samples, pooling, unchanged retries or threshold changes.
5. Full `just smoke`, diff check and applicable local document links; update repair-01 result and source fingerprints with all actual results, including failure if present.
6. Independent round-1 re-audit against R5 and this plan; no concurrent subject edits.

## Limits and completion

Preserve settings, behavior, F1–F4 ownership/rollback, Bash 3.2 parse/skip and qualified >=4.4 use, opt-in/once-per-process operation, no new runtime dependencies or per-command hooks. No native code, bytes, pin, build, release, production definition, SSH/Linux, live assets, startup-file edits or Git mutations. A native/requirement/scope change returns to the human.

Success requires every semantic/native/full check, all original startup comparisons and independent audit Pass. A failed gate remains a finding. Round 1 starts when implementation is assigned; at most one additional automatic repair round remains afterward. The existing cycle and failure history do not reset.
