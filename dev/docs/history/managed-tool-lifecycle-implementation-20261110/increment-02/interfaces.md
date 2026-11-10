# Increment02 integration contract — T3/T4/T5

Continue from increment01/interfaces.md and the exact accepted combined baseline.
This is a verified intermediate worktree, not final T6/T7 routing/report/prune or
independent-audit acceptance. The sole technical integration owner is unchanged.

## Engine and public mutators

`remote_ssh_cmd_require_managed_libs` loads install helpers and the managed
foundation/engines once. New install/uninstall/update and tools/install-tool.sh
share those engines; there is no staging route through the public wrapper.
The wrapper validates its optional exact pinned version, then requires the same
confirmation/preflight/adoption/journal gate. It has no new hidden public flags.

`ms_install_preflight TOOLS...` builds the full selected collision plan in memory.
It validates definitions, platform mapping, library checksum/member, all current
and saved required selectors, other-slot claims and reserved management CLI path.
`MS_PREFLIGHT` is a flat NUL-safe snapshot; `MS_APPROVED` must match after locks,
prior-journal normalization and a fresh preflight. Changed scope fails for retry.
The facade validates all argv, profile/dedup/support and readable preview before
TTY/default-deny confirmation. No-args/help/errors do not initialize state.

After consent, create/re-resolve the same physical roots, acquire the complete
command-specific lock set, reload state and call the common gate. A changed lock
set requires release/re-acquire before dependent mutation. Initial adoption and
legacy fzf advisory hint are committed before the new batch. Expected-tools is
never selected or written by these mutators. Profiles are not stored.

`ms_install_batch` records ordered queued tools and then `ms_install_one` records
running/staging, complete old selector states and allowed publication paths before
creating its private stage. `ms_stage_build` is a child: existing checksum,
extraction and library qualification finish before publication. Its download EXIT
trap stays in that child and cannot replace owner ticket cleanup. The downloader
no longer creates prefix/bin; only the owning engine prepares selected roots.

Binary installs retain existing executable selection and flattening; bundles and
libraries retain their explicit layout. A typed complete file/directory manifest
and exact marker receipt are committed before stage-to-final guarded rename.
Every selector intention precedes its guarded publication and checkpoint. Current
literal target/proof is checked again in the registered child before exec.
Only full structural health, required data and all aliases permit member+completed
in one generation. A healthy pinned install uses a durable reuse goal and no
asset download/probe. Recovery also saves exact new selector receipts, preserving
later B repair if a recovered payload goes missing.

`ms_uninstall_preflight` collects the whole selection, all proven own active and
inactive releases, current/saved/custom owned selectors, protected leftovers and
membership changes. Foreign required selectors or insufficient C for required
saved live scope stop before deletion. Preview shows the owned selectors, release
scope, membership and protected entries before confirmation. Known absent is a
read-only no-op. Only the selected member's scope is changed.

`ms_uninstall_one` persists complete per-path intentions and ordinary manifest
before unlink/rm, revalidates each guard and checkpoints each deletion. Missing
paths count only with the durable intention. Complete absence retires membership
in the same generation as completion. A partial rm that lost payload but retains
an exact live identity and only recognized ordinary manifest remainder can settle
failed with member/protected evidence retained. That classification grants no
recursive deletion authority. Foreign/unknown/symlinked remainder stays unresolved
and blocks every later lifecycle journal replacement. Install/update can repair
an absent selector after a safely classified partial uninstall, preserving the
old protected remainder.

The CLI itself has a durable intention before first link/mode publication. Its
canonical source/collision guard and registered utility lease cover that work.
No startup file, user/global configuration or other checkout helper is published.

## Additional state rows

All use the existing strict typed NUL schema. Old records remain readable; unknown
or malformed records remain errors. remove-intent uniqueness includes its actual
path, permitting several releases/aliases for one tool.

| Tag | Exact fields |
| --- | --- |
| cli-intent | batch, bin/remote-ssh, absolute checkout CLI source, intended/done |
| reuse-intent | batch, tool, root, version, layout, member |
| refresh-intent | batch, physical checkout, upstream name, old HEAD OID, target OID or empty before fetch, planned/fetched/resetting/reset-done |

Historical completed/failed/not-run outcomes survive the next journal. Failed
publication roots remain protected evidence. Migration excludes paths already
claimed by another pair, including shared `.active` libraries and inactive roots;
sharing a prefix does not borrow the other pair's membership.

## Fresh-code update

`ms_update_run` inventories/reconciles/adopts before fetch and persists the whole
managed set plus refresh intention. It takes prefix, required executable bin and
checkout roots, including unresolved prior-journal needs. It never uses a bare
install, profile or expected-tools selection.

Git fetch/reset are guarded registered children. The old and fetched target OIDs
are durable. Reset revalidates the same checkout and allowed HEAD, complete NUL
Git target/current/untracked inventories and managed-data separation. It refuses
to overwrite untracked obstructions or state/ticket/release claims when overrides
share the checkout. Stable validation failure settles before reset starts;
uncertain/resetting work remains recoverable under its frozen intention.

A proven reset stores reset-done/refreshed and execs private continue-update.sh
in the same owner PID. It passes pair/generation/batch and exact roots/tokens/
tickets as separate argv fields. Fresh code validates every binding/ticket and
reinstalls signal cleanup before it changes state or selectors. It recomputes
current metadata/support/lock needs while retaining exactly the managed members.
Retired/unsupported entries retain management and produce nonzero failed/not-run
outcomes. An empty set refreshes only the project. Informational update-check and
its existing best-effort cache behavior are retained.

The common gate can settle planned/fetched refresh failures as tools not-run.
For resetting/reset-done it requires checkout lock, exact HEAD/index/tracked proof;
only update may retry an incomplete reset against the frozen old/target binding.
Other commands protect an unresolved reset. Completed-on-disk uninstall/install
is always normalized before any unrelated new batch, avoiding resurrection or
loss of earlier real success.

## Test and remaining integration boundaries

New CLI helper/private calls have 120-second outer test bounds; explicit writer
waits remain 60 seconds and bakery acquisition 15 seconds. Tests use isolated
HOME/prefix/bin/XDG/REMOTE_ENV_DIR and local assets/Git repositories. Native ABI
compatibility is not established by the controlled qualification stubs.

T6/T7 still own top-level list/check, environment rendering, removal of tool/doctor
and obsolete expected-tools imports, dispatcher/help/guide/bootstrap/docs, prune
prefix-only locking and complete claims/pending protection, remaining old grammar
regression migration and final smoke. Do not treat current legacy report/prune
facades as accepted final behavior or run concurrent real-host prune yet.

Before broader legacy actual-source tests, sanitize direct broad dots copies in:
`test_install_cli.prepare_cli_install`, test_fzf_retirement.py,
test_flyline_lifecycle.py and test_welcome_bundled.py. They were source-audited but
not executed in increment02. The shared conftest copy helper, new managed fixture
and selected library payload helper are already sanitized. Keep synthetic local
config generation after copying; never copy actual ignored user.local/.env data.
