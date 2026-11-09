"""Offline native regressions for library load probes and Readline restoration."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "docs/interactive-tools-performance-evidence")
)
from benchmark import PROMPT, Session, config, environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bash", "library", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="flyline-lifecycle-") as directory:
        root = Path(directory)
        library = root / args.library.name
        library.write_bytes(args.library.read_bytes())
        for name in ("probe-load", "probe-unload", "startup-rollback", "later-unload"):
            home = root / name
            home.mkdir()
            for sub in ("config", "data", "state", "cache"):
                (home / sub).mkdir()
            env = environment(home, Path("/usr/bin"))
            result: dict[str, Any] = {"case": name}
            if name.startswith("probe-"):
                code = 'builtin enable -f "$1" flyline && builtin flyline key --vim-mode true'
                if name == "probe-unload":
                    code += " && builtin enable -d flyline"
                code += " && printf AFTER_PROBE"
                probe = subprocess.run(
                    [
                        str(args.bash),
                        "--noprofile",
                        "--norc",
                        "-i",
                        "-c",
                        code,
                        "probe",
                        str(library),
                    ],
                    env=env,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                result.update(
                    exit=probe.returncode,
                    stdout=probe.stdout,
                    stderr=probe.stderr,
                    passed=probe.returncode == 0 and "AFTER_PROBE" in probe.stdout,
                )
            else:
                rc = home / "rc.sh"
                setup = (
                    "capture() { printf '\\036ARG:%s\\037\\n' \"$*\"; }\n"
                    + config("flyline-minimal", Path("/usr/bin"), library, root)
                    + "builtin flyline key --vim-mode true\n"
                )
                if name == "startup-rollback":
                    setup += "builtin enable -d flyline\n"
                setup += "printf '\\036LOADED\\037\\n'\n"
                rc.write_text(setup)
                session = Session(
                    [str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, home
                )
                try:
                    session.expect(b"\x1eLOADED\x1f", raw=True)
                    session.expect(PROMPT)
                    if name == "later-unload":
                        session.send(b"printf '\\036WARMED\\037\\n'\r")
                        session.expect(b"\x1eWARMED\x1f", raw=True)
                        session.expect(PROMPT)
                        session.send(b"builtin enable -d flyline; printf '\\036UNLOADED\\037\\n'\r")
                        session.expect(b"\x1eUNLOADED\x1f", raw=True)
                        session.expect(PROMPT)
                    session.send(b"capture ac")
                    session.quiet(0.1)
                    session.send(b"\x1b")
                    session.quiet(0.15)
                    session.send(b"hrbA\r")
                    session.expect(b"\x1f", raw=True)
                    found = re.findall(rb"\x1eARG:([^\x1f]*)\x1f", session.transcript)
                    actual = found[-1].decode() if found else "[no argument]"
                    result.update(actual=actual, passed=actual == "bc")
                except (RuntimeError, OSError) as exc:
                    result.update(passed=False, error=str(exc)[:600])
                finally:
                    result["resources"] = session.close()
                    (args.output / f"{name}.txt").write_text(
                        json.dumps(session.transcript.decode(errors="replace")) + "\n"
                    )
            results.append(result)
            print(json.dumps(result), flush=True)
    report = {
        "library_sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": results,
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
