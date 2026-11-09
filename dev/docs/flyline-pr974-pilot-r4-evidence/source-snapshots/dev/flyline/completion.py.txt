"""Offline four-way editor/provider pilot using one Carapace default handler."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "docs/interactive-tools-performance-evidence"))
sys.path.insert(0, str(ROOT.parent / "docs/completion-provider-pilot-evidence"))
from benchmark import PROMPT, Session, config, environment  # noqa: E402
from compare import CASES, controls, fixture_repository, rcfile, request  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="flyline-completion-") as directory:
        base = Path(directory)
        fixture = base / "fixture"
        fixture_repository(fixture, {"PATH": f"{args.tools}:/usr/bin:/bin", "HOME": str(base)})
        library = base / args.library.name
        library.write_bytes(args.library.read_bytes())
        for editor in ("readline", "flyline"):
            for provider in (False, True):
                name = f"{editor}-carapace-{int(provider)}"
                home = base / name
                home.mkdir()
                for sub in ("config", "data", "state", "cache", "bin"):
                    (home / sub).mkdir()
                count = home / "provider-calls"
                wrapper = home / "bin/carapace"
                wrapper.write_text(
                    "#!/bin/bash\n"
                    + f"printf 'call\\n' >> {shlex.quote(str(count))}\n"
                    + f'exec {shlex.quote(str((args.tools / "carapace").resolve()))} "$@"\n'
                )
                wrapper.chmod(0o755)
                setup = rcfile("baseline", args.tools.parent).replace(
                    'spec=$(complete -p "${COMP_WORDS[0]}")', "spec=$(complete -p -D)"
                )
                setup += config(
                    "flyline-minimal" if editor == "flyline" else "bash",
                    args.tools,
                    library,
                    base,
                )
                if editor == "flyline":
                    setup += (
                        "flyline key --vim-mode true\nflyline suggestions --use-flycomp false\n"
                    )
                if provider:
                    setup += (ROOT / "carapace-pilot.sh").read_text()
                    setup += "\ncomplete -D -o default -o bashdefault -F _pilot_carapace_complete\n"
                setup += "printf '\\036READY\\037\\n'\n"
                rc = home / "rc.sh"
                rc.write_text(setup)
                env = environment(home, args.tools)
                env.update(
                    PATH=f"{home / 'bin'}:{env['PATH']}",
                    GIT_CONFIG_NOSYSTEM="1",
                    GIT_TERMINAL_PROMPT="0",
                )
                session = Session(
                    [str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"], env, fixture
                )
                result: dict[str, Any] = {"case": name}
                try:
                    session.expect(b"\x1eREADY\x1f", raw=True)
                    session.expect(PROMPT)
                    session.send(b": TYPING_ONLY")
                    session.quiet(0.25)
                    result["provider_called_during_startup_or_typing"] = count.exists()
                    session.clear()
                    if provider:
                        result["queries"] = [request(session, i) for i in range(len(CASES))]
                        result["controls"] = controls(session)
                        result["passed"] = (
                            all(q["passed"] for q in result["queries"])
                            and all(t["passed"] for t in result["controls"]["tabs"])
                            and result["controls"]["vi_passed"]
                            and not result["provider_called_during_startup_or_typing"]
                        )
                    else:
                        session.send(b"cat fixture_uni\t")
                        session.expect(b"fixture_unique.txt")
                        result["passed"] = not count.exists()
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
        "library_sha256": digest(args.library),
        "script_sha256": digest(Path(__file__)),
        "adapter_sha256": digest(ROOT / "carapace-pilot.sh"),
        "carapace_version": subprocess.check_output(
            [args.tools / "carapace", "--version"], text=True
        ).strip(),
        "results": results,
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
