"""Check actual vi-edited arguments using the benchmark's isolated PTY setup."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from benchmark import PROMPT, Session, config, environment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bash", "zsh", "artifacts", "flyline", "repo", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for case in ("bash", "ble-minimal", "flyline-minimal", "zsh-highlighting"):
        with tempfile.TemporaryDirectory(prefix="editor-vi-probe-") as directory:
            home = Path(directory)
            for name in ("config", "data", "state", "cache"):
                (home / name).mkdir()
            rc = home / (".zshrc" if case.startswith("zsh") else "rc.sh")
            rc.write_text(
                "pilot_capture() { printf '\\036ARG:%s\\037\\n' \"$1\"; }\n"
                + config(case, args.artifacts, args.flyline, args.repo)
            )
            command = (
                [str(args.zsh), "-d", "-i"]
                if case.startswith("zsh")
                else [str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"]
            )
            session = Session(command, environment(home, args.artifacts), home)
            try:
                session.expect(PROMPT)
                session.quiet(0.15)
                session.send(b"pilot_capture ac")
                session.quiet(0.2)
                session.send(b"\x1b")
                session.quiet(0.2)
                session.send(b"hrbA")
                session.quiet(0.2)
                session.send(b"\r")
                session.expect(b"\x1f", raw=True)
                found = re.findall(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript)
                actual = found[-1].decode() if found else "[no argument]"
                results.append(
                    {"case": case, "expected": "bc", "actual": actual, "passed": actual == "bc"}
                )
            finally:
                session.close()
                (args.output / f"vi-{case}.txt").write_text(
                    json.dumps(session.transcript.decode(errors="replace")) + "\n"
                )
    (args.output / "vi-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
