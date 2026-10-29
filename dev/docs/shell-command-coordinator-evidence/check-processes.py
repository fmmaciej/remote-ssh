import json
import subprocess
from pathlib import Path

rows = subprocess.check_output(["/bin/ps", "-axo", "pid=,ppid=,pgid=,command="], text=True)
found = []
for line in rows.splitlines():
    parts = line.strip().split(None, 3)
    if len(parts) != 4:
        continue
    pid, parent, group, command = parts
    if ("shell-command-implementation-evidence/run-focused.py" in command
        or "pytest-0/test_pty_" in command
        or "pytest-0/test_exec_pid_" in command):
        found.append(dict(pid=int(pid), parent=int(parent), group=int(group), command=command))
Path(__file__).with_name("sandbox-focused-process-check.json").write_text(json.dumps(found, indent=2)+"\n")
print(json.dumps(found, indent=2))
