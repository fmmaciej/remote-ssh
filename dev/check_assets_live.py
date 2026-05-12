import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"\b([0-9a-fA-F]{64})\b")


@dataclass(frozen=True)
class ToolDef:
    name: str
    repo: str
    tag: str
    assets: tuple[str, ...]
    checksums: dict[str, str]


class LiveCheckError(RuntimeError):
    pass


def repo_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def load_tool_defs(root: Path) -> list[ToolDef]:
    script = r"""
    set -euo pipefail
    repo="$1"

    for def in "$repo"/tools/defs/*.sh; do
      unset TOOL_NAME GH_REPO RELEASE_TAG VERSION BINARY_NAME BINARY_ALIASES ASSETS CHECKSUMS
      . "$def"
      printf 'TOOL\t%s\t%s\t%s\n' "$TOOL_NAME" "$GH_REPO" "$RELEASE_TAG"
      for rec in "${ASSETS[@]}"; do
        printf 'ASSET\t%s\n' "${rec#*|}"
      done
      for rec in "${CHECKSUMS[@]}"; do
        printf 'CHECKSUM\t%s\t%s\n' "${rec%%|*}" "${rec#*|}"
      done
      printf 'END\n'
    done
    """
    result = subprocess.run(
        ["bash", "-c", script, "_", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise LiveCheckError(
            "Could not load tool definitions\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    return parse_tool_defs(result.stdout)


def parse_tool_defs(output: str) -> list[ToolDef]:
    defs: list[ToolDef] = []
    current: tuple[str, str, str] | None = None
    assets: list[str] = []
    checksums: dict[str, str] = {}

    for line in output.splitlines():
        parts = line.split("\t")
        kind = parts[0] if parts else ""

        if kind == "TOOL" and len(parts) == 4:
            if current is not None:
                raise LiveCheckError("Malformed tool definition stream: nested TOOL record")
            current = (parts[1], parts[2], parts[3])
            assets = []
            checksums = {}
        elif kind == "ASSET" and len(parts) == 2 and current is not None:
            assets.append(parts[1])
        elif kind == "CHECKSUM" and len(parts) == 3 and current is not None:
            checksums[parts[1]] = parts[2]
        elif kind == "END" and len(parts) == 1 and current is not None:
            name, repo, tag = current
            defs.append(
                ToolDef(
                    name=name,
                    repo=repo,
                    tag=tag,
                    assets=tuple(assets),
                    checksums=dict(checksums),
                )
            )
            current = None
            assets = []
            checksums = {}
        else:
            raise LiveCheckError(f"Malformed tool definition stream line: {line}")

    if current is not None:
        raise LiveCheckError("Malformed tool definition stream: missing END record")

    return defs


def request_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "remote-ssh-assets-live-check",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers=request_headers())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LiveCheckError(f"HTTP {exc.code} for {url}: {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise LiveCheckError(f"Could not fetch {url}: {exc.reason}") from exc


def release_json(repo: str, tag: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    raw = fetch_text(url)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LiveCheckError(f"Invalid GitHub JSON for {repo} {tag}") from exc
    if not isinstance(data, dict):
        raise LiveCheckError(f"Unexpected GitHub JSON for {repo} {tag}")
    return data


def release_asset_names(data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for asset in data.get("assets", []):
        if isinstance(asset, dict) and isinstance(asset.get("name"), str):
            names.add(asset["name"])
    return names


def release_asset_digests(data: dict[str, Any]) -> dict[str, str]:
    digests: dict[str, str] = {}
    for asset in data.get("assets", []):
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        digest = asset.get("digest")
        if not isinstance(name, str) or not isinstance(digest, str):
            continue
        prefix = "sha256:"
        if digest.lower().startswith(prefix):
            value = digest[len(prefix) :].lower()
            if SHA256_RE.fullmatch(value):
                digests[name] = value
    return digests


def parse_sha256_text(text: str) -> str:
    match = SHA256_RE.search(text)
    return match.group(1).lower() if match else ""


def live_checksum(repo: str, tag: str, asset: str) -> str:
    url = f"https://github.com/{repo}/releases/download/{tag}/{asset}.sha256"
    return parse_sha256_text(fetch_text(url))


def check_tool(tool: ToolDef) -> bool:
    print(f"[assets-live] {tool.name}: {tool.repo}@{tool.tag}", file=sys.stderr)

    try:
        data = release_json(tool.repo, tool.tag)
    except LiveCheckError as exc:
        print(f"Could not fetch GitHub release metadata for {tool.repo} {tool.tag}", file=sys.stderr)
        print(f"  {exc}", file=sys.stderr)
        return False

    ok = True
    live_assets = release_asset_names(data)
    for asset in tool.assets:
        if asset not in live_assets:
            print(f"Missing asset for {tool.repo} {tool.tag}: {asset}", file=sys.stderr)
            ok = False

    live_digests = release_asset_digests(data)
    for asset, expected in tool.checksums.items():
        got = live_digests.get(asset, "")
        if not got:
            try:
                got = live_checksum(tool.repo, tool.tag, asset)
            except LiveCheckError:
                got = ""

        if not got:
            print(
                f"Could not fetch live checksum for {tool.repo} {tool.tag}: {asset}",
                file=sys.stderr,
            )
            ok = False
            continue

        if got != expected:
            print(f"Checksum mismatch for {tool.repo} {tool.tag}: {asset}", file=sys.stderr)
            print(f"  expected: {expected}", file=sys.stderr)
            print(f"  live:     {got}", file=sys.stderr)
            ok = False

    return ok


def main() -> int:
    root = repo_dir()
    load_dotenv(root / "dev" / ".env")

    try:
        tools = load_tool_defs(root)
    except LiveCheckError as exc:
        print(exc, file=sys.stderr)
        return 1

    ok = True
    for tool in tools:
        ok = check_tool(tool) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
