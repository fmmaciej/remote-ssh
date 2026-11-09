"""Opt-in local PTY editor benchmarks and separate completion-provider timings.

Requires explicit local artifacts. No downloads or user startup files are used.
"""

from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import os
import platform
import pty
import random
import re
import select
import shlex
import signal
import statistics
import subprocess
import tempfile
import termios
import time
import unicodedata
from pathlib import Path
from typing import Any

ANSI = re.compile(rb"\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]")
PROMPT = b"BMARK> "
READY = b"\x1eREADY\x1f"


class Screen:
    """Track fixture redraws and answer terminal probes at their cursor position."""

    def __init__(self) -> None:
        self.rows = [[" "] * 120 for _ in range(30)]
        self.row = 0
        self.col = 0
        self.saved = (0, 0)
        self.state = "text"
        self.sequence = ""
        self.top = 0
        self.bottom = 29
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.responses = bytearray()
        self.probes = {"DA2": 0, "CPR": 0}

    def newline(self) -> None:
        if self.row == self.bottom:
            self.rows.pop(self.top)
            self.rows.insert(self.bottom, [" "] * 120)
        else:
            self.row = min(29, self.row + 1)

    def csi(self, final: str) -> None:
        raw = self.sequence.lstrip("?>=")
        parts = raw.split(";")
        nums = [int(p) if p.isdigit() else 0 for p in parts]
        n = nums[0] or 1
        if final in ("H", "f"):
            self.row = min(29, n - 1)
            self.col = min(119, (nums[1] or 1) - 1) if len(nums) > 1 else 0
        elif final == "A":
            self.row = max(0, self.row - n)
        elif final in ("B", "e"):
            limit = self.bottom if self.top <= self.row <= self.bottom else 29
            self.row = min(limit, self.row + n)
        elif final in ("C", "a"):
            self.col = min(119, self.col + n)
        elif final == "D":
            self.col = max(0, self.col - n)
        elif final in ("G", "`"):
            self.col = min(119, n - 1)
        elif final == "d":
            self.row = min(29, n - 1)
        elif final in ("E", "F"):
            self.row = max(0, min(29, self.row + (n if final == "E" else -n)))
            self.col = 0
        elif final == "K":
            start = 0 if nums[0] in (1, 2) else self.col
            end = min(120, self.col + 1) if nums[0] == 1 else 120
            self.rows[self.row][start:end] = [" "] * (end - start)
        elif final == "J":
            if nums[0] in (2, 3):
                self.rows = [[" "] * 120 for _ in range(30)]
            elif nums[0] == 0:
                self.rows[self.row][self.col :] = [" "] * (120 - self.col)
                for row in range(self.row + 1, 30):
                    self.rows[row] = [" "] * 120
        elif final == "P":
            line = self.rows[self.row]
            line[self.col :] = (line[self.col + n :] + [" "] * n)[: 120 - self.col]
        elif final == "@":
            line = self.rows[self.row]
            line[self.col :] = ([" "] * n + line[self.col :])[: 120 - self.col]
        elif final == "X":
            end = min(120, self.col + n)
            self.rows[self.row][self.col : end] = [" "] * (end - self.col)
        elif final == "L" and self.top <= self.row <= self.bottom:
            for _ in range(min(n, self.bottom - self.row + 1)):
                self.rows.insert(self.row, [" "] * 120)
                self.rows.pop(self.bottom + 1)
        elif final == "M" and self.top <= self.row <= self.bottom:
            for _ in range(min(n, self.bottom - self.row + 1)):
                self.rows.pop(self.row)
                self.rows.insert(self.bottom, [" "] * 120)
        elif final == "s":
            self.saved = (self.row, self.col)
        elif final == "u":
            self.row, self.col = self.saved
        elif final == "r":
            self.top = max(0, min(29, n - 1))
            self.bottom = max(self.top, min(29, (nums[1] or 30) - 1)) if len(nums) > 1 else 29
            self.row = self.col = 0
        elif final == "n" and nums[0] == 6:
            self.probes["CPR"] += 1
            self.responses.extend(f"\x1b[{self.row + 1};{self.col + 1}R".encode())
        elif final == "c":
            if self.sequence.startswith(">"):
                self.probes["DA2"] += 1
                self.responses.extend(b"\x1b[>0;370;0c")
            elif not self.sequence:
                self.responses.extend(b"\x1b[?1;2c")

    def feed(self, data: bytes) -> None:
        for char in self.decoder.decode(data):
            if self.state == "csi":
                if "@" <= char <= "~":
                    self.csi(char)
                    self.state = "text"
                else:
                    self.sequence += char
                continue
            if self.state == "osc":
                if char == "\x07":
                    self.state = "text"
                elif char == "\x1b":
                    self.state = "osc-escape"
                continue
            if self.state == "osc-escape":
                self.state = "text" if char == "\\" else "osc"
                continue
            if self.state == "charset":
                self.state = "text"
                continue
            if self.state == "escape":
                self.state = "text"
                if char == "[":
                    self.state, self.sequence = "csi", ""
                elif char in ("]", "P", "_", "^"):
                    self.state = "osc"
                elif char in ("(", ")", "*", "+"):
                    self.state = "charset"
                elif char == "7":
                    self.saved = (self.row, self.col)
                elif char == "8":
                    self.row, self.col = self.saved
                elif char == "D":
                    self.newline()
                continue
            if char == "\x1b":
                self.state = "escape"
            elif char == "\r":
                self.col = 0
            elif char == "\n":
                self.newline()
            elif char == "\b":
                self.col = max(0, self.col - 1)
            elif char == "\t":
                self.col = min(119, (self.col // 8 + 1) * 8)
            elif char >= " " and char != "\x7f":
                width = (
                    0
                    if unicodedata.combining(char)
                    else (2 if unicodedata.east_asian_width(char) in ("W", "F") else 1)
                )
                if not width:
                    continue
                if self.col >= 120:
                    self.col = 0
                    self.newline()
                self.rows[self.row][self.col] = char
                self.col += width

    def contains(self, needle: bytes) -> bool:
        if needle == PROMPT:
            return "".join(self.rows[self.row]).rstrip() == PROMPT.decode().rstrip()
        return needle.decode() in "".join("".join(row) for row in self.rows)


def environment(home: Path, artifacts: Path) -> dict[str, str]:
    return {
        "HOME": str(home),
        "ZDOTDIR": str(home),
        "XDG_CONFIG_HOME": str(home / "config"),
        "XDG_DATA_HOME": str(home / "data"),
        "XDG_STATE_HOME": str(home / "state"),
        "XDG_CACHE_HOME": str(home / "cache"),
        "PATH": f"{artifacts}:/usr/bin:/bin",
        "TERM": "xterm-256color",
        "LANG": "en_US.UTF-8",
        "USER": "benchmark",
        "LOGNAME": "benchmark",
        "HISTFILE": "/dev/null",
        "REMOTE_SSH_WELCOME": "0",
        "REMOTE_SSH_UPDATE_CHECK": "0",
        "REMOTE_SSH_ENABLE_ATUIN": "0",
        "REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT": "0",
    }


def config(case: str, artifacts: Path, flyline: Path, repo: Path) -> str:
    ble = shlex.quote(str(artifacts / "ble-nightly/ble.sh"))
    highlighter = shlex.quote(
        str(artifacts / "zsh-syntax-highlighting-0.8.0/zsh-syntax-highlighting.zsh")
    )
    lines = ["PS1='BMARK> '", "set -o vi" if "zsh" not in case else "bindkey -v"]
    if "ble" in case:
        lines += [f"source {ble} --attach=none || exit 41"]
        if "minimal" in case or "remote" in case:
            lines += ["bleopt complete_auto_complete= complete_auto_menu= complete_menu_filter="]
    if "carapace" in case:
        lines += ["source <(carapace _carapace bash) || exit 42"]
    if case == "bash-flycomp":
        lines += [
            f"source {shlex.quote(str(artifacts / 'generated-rg-completion.bash'))} || exit 42"
        ]
    if "remote" in case:
        lines += [f"source {shlex.quote(str(repo / 'shell/rc.sh'))} || exit 43"]
    if "flyline" in case:
        lines += [
            f"builtin enable -f {shlex.quote(str(flyline))} flyline || exit 44",
            "flyline run-tutorial false || exit 45",
            "flyline --show-animations false --enable-easter-eggs false "
            "--enable-extended-key-codes false --send-shell-integration-codes none "
            "--set-mouse-mode disabled || exit 46",
            "flyline set-cursor --backend terminal || exit 47",
            "flyline suggestions --auto-suggest false --auto-suggest-inline false || exit 48",
        ]
    if case == "zsh-highlighting":
        lines += [f"source {highlighter} || exit 49"]
    if "remote" in case:
        lines += ["unset PROMPT_COMMAND"]
    lines += ["PS1='BMARK> '"]
    if "ble" in case:
        lines += ["ble-attach || exit 50"]
    return "\n".join(lines) + "\n"


class Session:
    def __init__(self, args: list[str], env: dict[str, str], cwd: Path) -> None:
        self.pending = bytearray()
        self.transcript = bytearray()
        self.responses = bytearray()
        self.screen = Screen()
        self.started = time.perf_counter()
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            try:
                termios.tcsetwinsize(0, (30, 120))
                os.chdir(cwd)
                os.execve(args[0], args, env)
            finally:
                os._exit(127)
        os.set_blocking(self.fd, False)

    def send(self, data: bytes) -> None:
        offset = 0
        deadline = time.monotonic() + 15
        while offset < len(data):
            if time.monotonic() > deadline:
                raise RuntimeError("PTY input write timed out")
            readable, writable, _ = select.select([self.fd], [self.fd], [], 0.01)
            if readable:
                self.read(0)
            if writable:
                try:
                    offset += os.write(self.fd, data[offset : offset + 256])
                except BlockingIOError:
                    pass

    def read(self, timeout: float) -> bool:
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return True
        try:
            chunk = os.read(self.fd, 65536)
        except BlockingIOError:
            return True
        except OSError:
            return False
        if not chunk:
            return False
        self.pending.extend(chunk)
        self.transcript.extend(chunk)
        self.screen.feed(chunk)
        self.responses.extend(self.screen.responses)
        self.screen.responses.clear()
        if self.responses:
            try:
                sent = os.write(self.fd, self.responses)
                del self.responses[:sent]
            except BlockingIOError:
                pass
        return True

    def expect(self, needle: bytes, *, raw: bool = False, timeout: float = 15) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = bytes(self.pending)
            if (needle in value) if raw else self.screen.contains(needle):
                if raw:
                    del self.pending[: value.index(needle) + len(needle)]
                else:
                    self.pending.clear()
                return
            if not self.read(0.005):
                break
        raise RuntimeError(f"missing {needle!r}: {bytes(self.pending[-3000:])!r}")

    def quiet(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if not self.read(min(0.01, max(0, deadline - time.monotonic()))):
                break

    def exchange(self, text: bytes, needle: bytes) -> float:
        self.pending.clear()
        start = time.perf_counter()
        self.send(text)
        self.expect(needle)
        return (time.perf_counter() - start) * 1000

    def clear(self) -> None:
        self.quiet(0.015)
        self.exchange(b"\x15", PROMPT)
        self.quiet(0.015)

    def close(self) -> dict[str, float]:
        try:
            os.kill(self.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.close(self.fd)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            waited, _, usage = os.wait4(self.pid, os.WNOHANG)
            if waited:
                scale = 1024 * 1024 if platform.system() == "Darwin" else 1024
                return {
                    "shell_cpu_ms": (usage.ru_utime + usage.ru_stime) * 1000,
                    "shell_peak_rss_mib": usage.ru_maxrss / scale,
                }
            time.sleep(0.005)
        raise RuntimeError("PTY child did not exit after SIGKILL")


def editor_sample(
    case: str, home: Path, fixture: Path, args: argparse.Namespace, logs: Path, *, stress: bool
) -> dict[str, Any]:
    home.mkdir(parents=True, exist_ok=True)
    for name in ("config", "data", "state", "cache"):
        (home / name).mkdir(exist_ok=True)
    rc = home / (".zshrc" if case.startswith("zsh") else "rc.sh")
    rc.write_text(config(case, args.artifacts, args.flyline, args.repo))
    command = (
        [str(args.zsh), "-d", "-i"]
        if case.startswith("zsh")
        else [str(args.bash), "--noprofile", "--rcfile", str(rc), "-i"]
    )
    session = Session(command, environment(home, args.artifacts), fixture)
    result: dict[str, Any] = {"case": case}
    try:
        session.send(b"printf '\\036READY\\037\\n'\r")
        session.expect(READY, raw=True)
        result["ready_ms"] = (time.perf_counter() - session.started) * 1000
        session.expect(PROMPT)
        session.quiet(0.05)
        rss = subprocess.run(
            ["/bin/ps", "-o", "rss=", "-p", str(session.pid)],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        result["ready_rss_mib"] = int(rss.stdout.strip()) / 1024
        result["short_render_ms"] = []
        result["single_key_ms"] = []
        result["long_render_ms"] = []
        for index in range(3):
            token = f"BENCH_INPUT_{index}_END".encode()
            result["short_render_ms"].append(session.exchange(b": " + token, token))
            result["single_key_ms"].append(session.exchange(b"X", token + b"X"))
            session.clear()
        result["file_tab_ms"] = session.exchange(
            b"cat fixture_uni\t", b"fixture_unique_completion_target"
        )
        session.clear()
        if stress:
            token = b"BENCH_LONG_END"
            result["long_render_ms"].append(
                session.exchange(b": " + b"x" * 4096 + b" " + token, token)
            )
        result["stress"] = stress
        result["terminal_probes_answered"] = session.screen.probes
        session.quiet(0.15)
        result["ok"] = True
    except (RuntimeError, subprocess.SubprocessError, ValueError) as error:
        result["ok"] = False
        result["error"] = str(error)
    finally:
        result.update(session.close())
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f"{case}.txt").write_text(
            json.dumps(session.transcript.decode(errors="replace"), ensure_ascii=True) + "\n"
        )
    return result


def summary(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    return {
        "n": len(values),
        "median": statistics.median(values),
        "p95": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))],
        "min": ordered[0],
        "max": ordered[-1],
    }


def provider_samples(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    env = environment(root / "provider-home", args.artifacts)
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    carapace = str(args.artifacts / "carapace")
    flycomp = str(args.artifacts / "flycomp")
    commands = {
        "carapace_rg_candidates": [carapace, "rg", "export", "rg", "--reg"],
        "carapace_init_script": [carapace, "_carapace", "bash"],
        "flycomp_generate_rg": [
            flycomp,
            "rg",
            "--strategy",
            "run-help",
            "--recurse-limit",
            "0",
            "--no-sandbox",
        ],
    }
    result: dict[str, Any] = {}
    generated = root / "rg-completion.bash"
    for name, command in commands.items():
        samples = []
        for index in range(args.iterations + args.warmup):
            start = time.perf_counter()
            proc = subprocess.run(
                command, env=env, cwd=root, capture_output=True, text=True, timeout=20, check=True
            )
            duration = (time.perf_counter() - start) * 1000
            if name == "carapace_rg_candidates":
                assert any(v["value"] == "--regexp" for v in json.loads(proc.stdout)["values"])
            elif name == "flycomp_generate_rg":
                generated.write_text(proc.stdout)
                (args.output / "generated-rg-completion.bash.txt").write_text(proc.stdout)
                assert "--regexp" in proc.stdout and "_rg()" in proc.stdout, repr(
                    proc.stdout[:1500]
                )
            else:
                assert "complete" in proc.stdout
            samples.append({"warmup": index < args.warmup, "ms": duration})
        result[name] = {
            "samples": samples,
            "summary_ms": summary([s["ms"] for s in samples if not s["warmup"]]),
        }
    shell_script = """source "$1" || exit 1
for ((i=0;i<100;i++)); do
    COMP_WORDS=(rg --reg); COMP_CWORD=1; COMP_LINE='rg --reg'; COMP_POINT=8
    start=${EPOCHREALTIME/./}
    _rg rg --reg rg
    finish=${EPOCHREALTIME/./}
    [[ " ${COMPREPLY[*]} " == *' --regexp '* ]] || exit 2
    printf '%s\\n' "$((finish-start))"
done
"""
    proc = subprocess.run(
        [str(args.bash), "--noprofile", "--norc", "-c", shell_script, "bench", str(generated)],
        env=env,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    times = [int(line) / 1000 for line in proc.stdout.splitlines()]
    result["flycomp_generated_rg_query"] = {"samples_ms": times, "summary_ms": summary(times[5:])}
    (args.output / "generated-rg-completion.bash.txt").write_text(generated.read_text())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--zsh", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--flyline", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--cases", nargs="*")
    args = parser.parse_args()
    if args.iterations < 1 or args.warmup < 0:
        parser.error("iterations must be positive and warmup nonnegative")
    for key in ("bash", "zsh", "artifacts", "flyline", "repo"):
        setattr(args, key, getattr(args, key).resolve(strict=True))
    args.output.mkdir(parents=True, exist_ok=True)
    cases = args.cases or [
        "bash",
        "bash-carapace",
        "bash-flycomp",
        "ble-default",
        "ble-minimal",
        "ble-minimal-carapace",
        "flyline-minimal",
        "zsh",
        "zsh-highlighting",
        "remote-min",
        "remote-min-ble",
    ]
    samples: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="remote-ssh-tools-benchmark-") as directory:
        root = Path(directory)
        fixture = root / "fixture"
        fixture.mkdir()
        (fixture / "fixture_unique_completion_target").touch()
        rng = random.Random(20261108)
        for index in range(args.iterations + args.warmup):
            order = cases[:]
            rng.shuffle(order)
            for case in order:
                for cache in ("fresh-home", "warm-home"):
                    home = root / case / (f"fresh-{index}" if cache == "fresh-home" else "warm")
                    sample = editor_sample(
                        case,
                        home,
                        fixture,
                        args,
                        args.output / "transcripts",
                        stress=args.warmup <= index < args.warmup + 2,
                    )
                    sample.update({"round": index, "warmup": index < args.warmup, "home": cache})
                    samples.append(sample)
                    print(f"round={index} {case} {cache} ok={sample['ok']}", flush=True)
                    if not sample["ok"]:
                        (args.output / "samples.json").write_text(
                            json.dumps(samples, indent=2) + "\n"
                        )
                        raise RuntimeError(sample["error"])
            (args.output / "samples.json").write_text(json.dumps(samples, indent=2) + "\n")
        providers = provider_samples(args, root)
    metrics = [
        "ready_ms",
        "ready_rss_mib",
        "short_render_ms",
        "single_key_ms",
        "long_render_ms",
        "file_tab_ms",
        "shell_cpu_ms",
        "shell_peak_rss_mib",
    ]
    summaries: dict[str, Any] = {}
    for case in cases:
        for cache in ("fresh-home", "warm-home"):
            selected = [
                s for s in samples if s["case"] == case and s["home"] == cache and not s["warmup"]
            ]
            ok = [s for s in selected if s["ok"]]
            key = f"{case}/{cache}"
            summaries[key] = {"failures": len(selected) - len(ok), "metrics": {}}
            if ok:
                for metric in metrics:
                    values = [
                        value
                        for s in ok
                        for value in (s[metric] if isinstance(s[metric], list) else [s[metric]])
                    ]
                    if values:
                        summaries[key]["metrics"][metric] = summary(values)
    metadata = {
        "host": platform.platform(),
        "python": platform.python_version(),
        "bash": subprocess.check_output([str(args.bash), "--version"], text=True).splitlines()[0],
        "zsh": subprocess.check_output([str(args.zsh), "--version"], text=True).strip(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "iterations": args.iterations,
        "warmup_rounds": args.warmup,
        "terminal": "120x30 xterm-256color model; DA2 0;370;0; cursor-position replies",
    }
    report = {"metadata": metadata, "editors": summaries, "providers": providers}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {args.output / 'report.json'}", flush=True)


if __name__ == "__main__":
    main()
