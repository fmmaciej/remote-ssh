# File Watch

`file-watch.sh` compares files from simple pointers. A pointer can be a local
file on disk or a file inside a Git repository at a branch, tag, full ref, or
commit SHA.

The intended periodic runner is cron. There is no daemon and no systemd timer.
The script keeps local bare Git caches and a JSON state file so repeated runs
can skip watches whose inputs were already checked.

## Requirements

Required commands:

- `git`
- `jq`
- `diff`

The script also uses standard Unix utilities such as `bash`, `cp`, `mkdir`,
`mktemp`, `date`, `mv`, and `stat`.

## Configuration

The default config lives in:

```text
dots/file-watch.json
```

Minimal shape:

```json
{
  "cache_dir": "~/.cache/remote-ssh/file-watch",
  "state_file": "~/.local/state/remote-ssh/file-watch/state.json",
  "pointers": {
    "get-started-v1": {
      "type": "git",
      "repo": "https://github.com/example/example-repo.git",
      "ref": "v1.0.0",
      "file": "docs/get-started.md"
    },
    "get-started-main": {
      "type": "git",
      "repo": "https://github.com/example/example-repo.git",
      "ref": "main",
      "file": "docs/get-started.md"
    }
  },
  "watches": [
    {
      "name": "get-started-watch",
      "left": "get-started-v1",
      "right": "get-started-main",
      "fail_on_diff": false
    }
  ]
}
```

Pointer types:

```json
{ "type": "file", "path": "/absolute/or/relative/path" }
```

```json
{
  "type": "git",
  "repo": "git@github.com:org/repo.git",
  "ref": "main",
  "file": "docs/get-started.md"
}
```

`ref` may be a branch, tag, full ref, or commit SHA. Local file pointers can
point at tracked or untracked files.

`watches[].left` and `watches[].right` can be either named pointers:

```json
"left": "get-started-v1"
```

or inline pointer objects:

```json
"right": {
  "type": "file",
  "path": "/tmp/local-copy.md"
}
```

For private repositories, prefer SSH URLs and existing SSH configuration:

```text
git@github.com:org/repo.git
```

Do not put tokens or credentials in JSON.

## Manual Usage

Run all configured watches:

```bash
./scripts/file-watch.sh run dots/file-watch.json
```

The config path is optional when using the default:

```bash
./scripts/file-watch.sh run
```

Ad hoc compare supports file paths and pointer names:

```bash
./scripts/file-watch.sh compare /path/to/local/file get-started-main dots/file-watch.json
```

When differences are found, the script prints a unified diff.

Exit codes:

- `0`: no differences, already checked, or all configured watches passed.
- `1`: differences detected where `fail_on_diff` is `true`, or ad hoc compare differs.
- `2`: configuration, dependency, Git, cache, or state error.
- `3`: a target file does not exist.

## Cache, State, And Many Watches

By default, the example uses:

```text
~/.cache/remote-ssh/file-watch
~/.local/state/remote-ssh/file-watch/state.json
```

The cache contains bare Git repositories named by a stable hash of the repo URL.
Within one run, the script resolves and fetches each unique `repo + ref`
combination once, then reuses the local bare cache for all file comparisons.

The state file is JSON keyed by watch `name`. Each entry stores fingerprints for
both sides and the last result. If both fingerprints match the previous run, the
watch skips the diff.

## Cron

Edit your crontab:

```bash
crontab -e
```

Paste an entry with absolute paths. Cron has a minimal environment, so avoid
`~`, `$HOME`, and relative paths in the cron line itself.

Example:

```cron
*/30 * * * * mkdir -p /home/YOUR_USER/.local/state/remote-ssh/file-watch && /home/YOUR_USER/.local/share/remote-ssh/scripts/file-watch.sh run /home/YOUR_USER/.local/share/remote-ssh/dots/file-watch.json >> /home/YOUR_USER/.local/state/remote-ssh/file-watch/watch.log 2>&1
```

Replace `/home/YOUR_USER/.local/share/remote-ssh` and `/home/YOUR_USER` with the
real absolute paths for the target machine.
