# Developer Commands

Back: [Developer tooling](../README.md)

Use root `just` commands for normal repository work. They delegate to
`dev/justfile` while keeping the command entrypoint stable from the repo root.

## Root Recipes

```bash
just lint
just fmt
just type
just test
just smoke
just pre-commit-install
just pre-commit
just test-assets-live
just bench-shell
```

## `dev/` Recipes

When working inside `dev/`, these lower-level recipes are available:

```bash
just py-lint
just py-fmt
just py-type
just py-test
just sh-lint
just sh-fmt
just test
just smoke
just bench-shell
just pre-commit-install
just pre-commit
just test-assets-live
```

Prefer the root recipes unless you specifically need a `py-*` or `sh-*`
subcheck.
