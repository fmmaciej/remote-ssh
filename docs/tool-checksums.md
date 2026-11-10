# Pinned Tool Checksums

Back: [Tool definitions](tools.md)

## Verified Sources

The following 16 definitions were updated on 2026-11-10 using the official
GitHub Releases API. Every declared asset name was matched literally and its
assets[].digest required a sha256: prefix and 64 hexadecimal digits.
Platform mappings, binary aliases and Neovim's bundle layout are preserved.

| Tool | Version update | Exact API source | Covered assets |
| --- | --- | --- | ---: |
| atuin | 18.14.1 → 18.24.6 | [v18.24.6](https://api.github.com/repos/atuinsh/atuin/releases/tags/v18.24.6) | 5/5 |
| bottom | 0.12.3 → 0.15.0 | [0.15.0](https://api.github.com/repos/ClementTsang/bottom/releases/tags/0.15.0) | 6/6 |
| bssh | 2.2.3 → 2.4.3 | [v2.4.3](https://api.github.com/repos/lablup/bssh/releases/tags/v2.4.3) | 5/5 |
| dust | 1.2.4 → 1.2.7 | [v1.2.7](https://api.github.com/repos/bootandy/dust/releases/tags/v1.2.7) | 5/5 |
| eza | 0.23.4 → 0.23.5 | [v0.23.5](https://api.github.com/repos/eza-community/eza/releases/tags/v0.23.5) | 3/3 |
| fd | 10.3.0 → 10.5.2 | [v10.5.2](https://api.github.com/repos/sharkdp/fd/releases/tags/v10.5.2) | 6/6 |
| nu | 0.112.2 → 0.117.0 | [0.117.0](https://api.github.com/repos/nushell/nushell/releases/tags/0.117.0) | 6/6 |
| nvim | 0.11.5 → 0.12.6 | [v0.12.6](https://api.github.com/repos/neovim/neovim/releases/tags/v0.12.6) | 4/4 |
| procs | 0.14.11 → 0.14.12 | [v0.14.12](https://api.github.com/repos/dalance/procs/releases/tags/v0.14.12) | 2/2 |
| rg | 15.1.0 → 15.2.0 | [15.2.0](https://api.github.com/repos/BurntSushi/ripgrep/releases/tags/15.2.0) | 4/4 |
| starship | 1.24.1 → 1.27.0 | [v1.27.0](https://api.github.com/repos/starship/starship/releases/tags/v1.27.0) | 5/5 |
| tspin | 6.0.0 → 7.0.0 | [7.0.0](https://api.github.com/repos/bensadeh/tailspin/releases/tags/7.0.0) | 4/4 |
| vector | 0.55.0 → 0.61.0 | [v0.61.0](https://api.github.com/repos/vectordotdev/vector/releases/tags/v0.61.0) | 5/5 |
| yazi | 25.5.31 → 26.9.1 | [v26.9.1](https://api.github.com/repos/sxyazi/yazi/releases/tags/v26.9.1) | 6/6 |
| zellij | 0.44.2 → 0.45.1 | [v0.45.1](https://api.github.com/repos/zellij-org/zellij/releases/tags/v0.45.1) | 4/4 |
| zoxide | 0.9.9 → 0.10.0 | [v0.10.0](https://api.github.com/repos/ajeetdsouza/zoxide/releases/tags/v0.10.0) | 4/4 |

Yazi now has complete upstream SHA-256 coverage; its six old checksum
exceptions were removed. The 16 updated definitions cover 74/74 assets.
Across all 22 definitions, checksums cover 96/100 declared assets.
Bat, sd, skim, fzf, navi and the custom Flyline release retain their existing pins.

Only the four exact Navi exceptions below remain. Release metadata is checked
separately from archive contents and native integration tests; neither proves
that an executable works on every declared platform. The optional
just test-assets-live check was not invoked for this update.

## Exact Exceptions

### navi: denisidoro/navi, v2.23.0

The official metadata, asset list and release body checked on 2026-11-02
provided no SHA-256 for these assets:

- navi-v2.23.0-aarch64-apple-darwin.tar.gz
- navi-v2.23.0-x86_64-apple-darwin.tar.gz
- navi-v2.23.0-aarch64-unknown-linux-gnu.tar.gz
- navi-v2.23.0-x86_64-unknown-linux-musl.tar.gz

[Exact release metadata](https://api.github.com/repos/denisidoro/navi/releases/tags/v2.23.0).
The definition remains pinned because v2.24.0 lacks the macOS release assets
and the Navi/skim protocol adapter is qualified against the existing pin.
Recheck official sources when changing the release; do not carry exceptions
to a different tag or asset automatically.

## Offline Contract and Runtime Behavior

dev/tests/test_tool_assets.py requires valid, unique SHA-256 entries referring
to declared assets, and full coverage except for the exact Navi tuples above.
Obsolete exceptions fail the check.

The installer verifies a selected pinned checksum before extraction or
installation. A mismatch or failed hash command stops before active links
switch. Download, extraction and installation failures preserve the previous
working release; updates do not automatically delete old versions.

## Upgrade Compatibility

- Starship 1.27.0 includes security fixes and changes Bash initialization.
  Recheck prompt status/timing and Atuin/Flyline hook ownership.
- Atuin 18.24.6 retains the initialization flags used by remote-ssh. Its
  upstream fixture now includes the separate include guard and the new
  history start/end --hook arguments.
- zoxide 0.10.0 changes the import CLI. remote-ssh uses init and query;
  its skim picker must still replace upstream interactive completion.
- bssh intentionally targets 2.4.3. Version 3 changes short-option meanings,
  and 3.1.2 currently lacks the macOS asset.
- Tailspin 7 renames --config-path to --theme, replaces
  --disable-builtin-keywords with --disable keywords, changes completion
  flags and rejects unknown theme keys. The bundled log helpers use plain
  tspin pipelines and the cheatsheet uses supported --exec mode.
- Vector 0.61 changes scheme-less vector sink endpoints to HTTPS. Review
  existing host configurations and intermediate release upgrade guides before
  updating a running pipeline.
- Nushell, Neovim and Yazi cross releases with configuration or API changes.
  The bundled Vim configuration uses basic options, and this checkout does not
  ship custom Nushell or Yazi configuration/plugins. Review user-owned
  configuration separately before host deployment.

Sources: the exact releases in the table, [Tailspin 7 notes](https://github.com/bensadeh/tailspin/releases/tag/7.0.0),
[Vector upgrade guide](https://vector.dev/highlights/2026-10-29-0-61-0-upgrade-guide/),
[Yazi changelog](https://github.com/sxyazi/yazi/blob/v26.9.1/CHANGELOG.md)
and [Neovim news](https://github.com/neovim/neovim/blob/v0.12.6/runtime/doc/news.txt).
