# Pinned Tool Checksums

Back: [Tool definitions](tools.md)

## Verified Sources

The following exact releases were checked on 2026-11-02 using the official
GitHub Releases API endpoints linked below. For each declared asset, its name
was matched literally against `assets[].name`, and `assets[].digest` was required
to contain `sha256:` followed by 64 hexadecimal digits. The SHA-256 value is
pinned in the tool definition's `CHECKSUMS` array without the `sha256:` prefix.

| Tool | Repository | Pinned release / API source | Covered assets |
| --- | --- | --- | ---: |
| bat | `sharkdp/bat` | [v0.26.1](https://api.github.com/repos/sharkdp/bat/releases/tags/v0.26.1) | 6/6 |
| eza | `eza-community/eza` | [v0.23.4](https://api.github.com/repos/eza-community/eza/releases/tags/v0.23.4) | 3/3 |
| fd | `sharkdp/fd` | [v10.3.0](https://api.github.com/repos/sharkdp/fd/releases/tags/v10.3.0) | 6/6 |
| fzf | `junegunn/fzf` | [v0.67.0](https://api.github.com/repos/junegunn/fzf/releases/tags/v0.67.0) | 4/4 |
| nu | `nushell/nushell` | [0.112.2](https://api.github.com/repos/nushell/nushell/releases/tags/0.112.2) | 6/6 |
| nvim | `neovim/neovim` | [v0.11.5](https://api.github.com/repos/neovim/neovim/releases/tags/v0.11.5) | 4/4 |
| zoxide | `ajeetdsouza/zoxide` | [v0.9.9](https://api.github.com/repos/ajeetdsouza/zoxide/releases/tags/v0.9.9) | 4/4 |
| navi | `denisidoro/navi` | [v2.23.0](https://api.github.com/repos/denisidoro/navi/releases/tags/v2.23.0) | 0/4 |
| yazi | `sxyazi/yazi` | [v25.5.31](https://api.github.com/repos/sxyazi/yazi/releases/tags/v25.5.31) | 0/6 |

This adds 33 pinned checksums across seven definitions. The other twelve
definitions already cover 56 assets, bringing the repository total to **89 of
99 declared assets covered**, with ten explicit exceptions below. Tool versions,
platform mappings, aliases, and Neovim's bundle layout are unchanged.

Only release metadata was retrieved for this verification. Release archives
were not downloaded, locally computed hashes were not substituted for upstream
digests, and `just test-assets-live` was not run.

## Exact Exceptions

For the two releases below, `assets[].digest` is `null` for the declared assets.
Their complete release asset lists contain no checksum files, and the release
descriptions contain no SHA-256 values. These are exceptions based on the
checked official sources for these exact releases, not a claim that no hashes
exist elsewhere.

### navi: `denisidoro/navi`, `v2.23.0`

- `navi-v2.23.0-aarch64-apple-darwin.tar.gz`
- `navi-v2.23.0-x86_64-apple-darwin.tar.gz`
- `navi-v2.23.0-aarch64-unknown-linux-gnu.tar.gz`
- `navi-v2.23.0-x86_64-unknown-linux-musl.tar.gz`

### yazi: `sxyazi/yazi`, `v25.5.31`

- `yazi-aarch64-apple-darwin.zip`
- `yazi-x86_64-apple-darwin.zip`
- `yazi-aarch64-unknown-linux-musl.zip`
- `yazi-x86_64-unknown-linux-musl.zip`
- `yazi-aarch64-unknown-linux-gnu.zip`
- `yazi-x86_64-unknown-linux-gnu.zip`

These definitions retain optional checksum behavior. Recheck official sources
when updating either release or when upstream publishes additional metadata.
Do not carry an exception to a different tag or asset automatically.

## Offline Contract and Runtime Behavior

`dev/tests/test_tool_assets.py` requires valid SHA-256 values, unique checksum
names, references to declared assets, and full coverage except for the exact
repository/tag/asset tuples above. Obsolete exceptions also fail the check, so
adding a checksum requires removing its exception. Routine tests use local
manifests and do not query GitHub.

The existing installer verifies a selected pinned checksum before extraction
or installation. A mismatch or unavailable/failed hash command stops the
installation before active links are switched. The bad-checksum regression in
`dev/tests/test_install_failures.py` traces the extractor and checks that no
extraction or new release publication occurs, while the previous binary and
alias remain usable.
