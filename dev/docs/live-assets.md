# Live Asset Checks

Back: [Developer tooling](../README.md)

`just test-assets-live` is optional and uses the network plus GitHub Releases
API to verify that pinned release assets exist:

```bash
just test-assets-live
```

It does not download release archives. It loads tool definitions from
`tools/defs/*.sh`, checks release asset names, and validates published SHA-256
digests when GitHub exposes them.

Run it only when you explicitly want live asset validation, especially after
adding or updating tool definitions.

If GitHub API rate limits are a problem, copy `dev/.env.example` to `dev/.env`
and set `GITHUB_TOKEN` or `GH_TOKEN`. `dev/.env` is local-only and ignored by
git.
