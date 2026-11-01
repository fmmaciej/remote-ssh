"""Check a local pinned Atuin against isolated real interactive Bash sessions."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "tests"))
from pty_shell import PtyShell  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", required=True)
    parser.add_argument("--atuin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="atuin-recording-verify.") as tmp:
        home = Path(tmp)
        bindir = home / ".local/bin"
        bindir.mkdir(parents=True)
        (bindir / "atuin").symlink_to(args.atuin.resolve())
        env = {
            "HOME": tmp,
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_STATE_HOME": str(home / ".local/state"),
            "XDG_DATA_HOME": str(home / ".local/share"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "PATH": f"{bindir}:/usr/bin:/bin",
            "TERM": "xterm-256color",
            "REPO": str(repo),
            "REMOTE_SSH_CONFIG": "0",
            "REMOTE_SSH_UPDATE_CHECK": "0",
            "REMOTE_SSH_WELCOME": "0",
            "REMOTE_SSH_ENABLE_GIT_SESSION_IDENTITY": "0",
            "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
        }
        database = home / ".local/share/atuin/history.db"

        def rows() -> list[tuple]:
            with sqlite3.connect(database) as db:
                return db.execute(
                    "SELECT command,cwd,hostname,exit,duration,session FROM history WHERE command LIKE '%real-recording-%' ORDER BY timestamp"
                ).fetchall()

        for session in range(2):
            with PtyShell(args.bash, env) as shell:
                shell.command(
                    'bind -m emacs \'"?":self-insert\'; . "$REPO/shell/rc.sh"; [[ "$(bind -m emacs -p)" == *\'"?": self-insert\'* ]]'
                )
                shell.command('cd "$HOME"')
                shell.command(
                    f": real-recording-{session}; REMOTE_SSH_ENABLE_ATUIN=0; rcrc; (exit 7)",
                    status=7,
                )
                shell.until(
                    lambda session=session: (
                        len([row for row in rows() if row[3] == 7 and row[4] >= 0]) == session + 1
                    )
                )
                shell.command('[[ "$REMOTE_SSH_HISTORY_BACKEND" == atuin && "$HISTFILE" == "" ]]')
        result = rows()
        assert len(result) == 2
        assert all(row[1] == tmp and row[2] and row[3] == 7 and row[4] >= 0 for row in result)
        assert result[0][5] != result[1][5]
        args.output.write_text(
            json.dumps(
                {"bash": args.bash, "atuin": str(args.atuin.resolve()), "rows": result}, indent=2
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
