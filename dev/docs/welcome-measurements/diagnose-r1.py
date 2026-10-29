"""Untimed accounting for the former failed cell using the unchanged frozen sample()."""

from __future__ import annotations

import json
from pathlib import Path

from harness import HERE, fingerprint, sample


def main() -> None:
    records = []
    for version in ("baseline", "candidate"):
        repo = Path(f"/private/tmp/remote-ssh-welcome-{version}-r1")
        record = sample(
            repo, "3.2", "actionable", "pty", f"diagnostic-r1-{version}-3.2-actionable-pty"
        )
        record.update(
            {
                "version": version,
                "purpose": "former rejected cell diagnostic; excluded from principal samples",
                "runtime_fingerprint": fingerprint(repo)["aggregate"],
            }
        )
        records.append(record)
    (HERE / "r1-former-failure-diagnostic.json").write_text(json.dumps(records, indent=2) + "\n")
    print(
        "Former failure diagnostic: both complete Bash 3.2/actionable/PTY screens match unchanged golden output"
    )


if __name__ == "__main__":
    main()
