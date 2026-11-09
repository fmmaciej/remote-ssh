from pathlib import Path
from urllib.parse import unquote
import json, re, sys

repo = Path.cwd().resolve()
evidence = repo / "dev/docs/flyline-integration-repair-r1-evidence"
history = evidence / "history/flyline-repair-20261109-r1"
baseline = history / "baseline-1"
manifest = json.loads((baseline / "baseline.json").read_text())
snapshots = {d["source"]: baseline / d["snapshot"] for d in manifest["documents"]}
paths = [
    repo / "dev/docs/flyline-implementation-plan.md",
    repo / "dev/docs/flyline-integration-repair-r1-record.md",
    repo / "dev/flyline/README.md",
    *history.glob("*.md"),
]
paths += [evidence / "repair-01/result.md"]
paths += list(snapshots.values())
checks = []
errors = []
for path in paths:
    origin = next((repo / k for k, v in snapshots.items() if v == path), path)
    if not path.is_file():
        errors.append({"source": str(path.relative_to(repo)), "error": "missing document"})
        continue
    text = path.read_text()
    # Fenced examples are not current document links.
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for match in re.finditer(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", text):
        href = match[1].strip()
        if href.startswith("<") and href.endswith(">"):
            href = href[1:-1]
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
            continue
        target, _, anchor = href.partition("#")
        destination = (origin.parent / unquote(target)).resolve() if target else origin
        try:
            relative = str(destination.relative_to(repo))
        except ValueError:
            errors.append(
                {"source": str(path.relative_to(repo)), "href": href, "error": "outside project"}
            )
            continue
        actual = snapshots.get(relative, destination)
        okay = actual.exists()
        # Also check ordinary heading anchors in Markdown targets.
        if okay and anchor and actual.suffix == ".md":
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*$", actual.read_text(), flags=re.M)
            slugs = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
            okay = unquote(anchor) in slugs
        check = {
            "source": str(path.relative_to(repo)),
            "href": href,
            "target": relative,
            "passed": okay,
        }
        checks.append(check)
        if not okay:
            errors.append(check)
report = {
    "documents": len(paths),
    "checks": len(checks),
    "passed": not errors,
    "errors": errors,
    "links": checks,
}
(evidence / "repair-01/local-links.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        {"documents": len(paths), "checks": len(checks), "passed": not errors, "errors": errors},
        indent=2,
    )
)
sys.exit(0 if not errors else 1)
