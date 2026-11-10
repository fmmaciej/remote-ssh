"""Verify a production Flyline definition in a disposable local installation."""

import hashlib
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
bash = Path('/opt/homebrew/bin/bash').resolve()
sys.path.insert(0, str(repo / 'dev/docs/interactive-tools-performance-evidence'))
from benchmark import PROMPT, Session, environment

archive_name = 'flyline-1.10.0-pr974.aae68bb4.r5-aarch64-apple-darwin.tar.gz'
archive_hash = '38a7c65eb6e3c8c7458cdebea36607ae2e5577279b96ce2f6e2907b5ff9afaf3'
library_hash = 'ac989a041026f49df1d3b544290ee3e67b497a0d3f82fe4785cd3c106e431d57'
url = 'https://github.com/fmmaciej/flyline/releases/download/remote-ssh-v1.10.0-pr974.aae68bb4.r5/' + archive_name
home = output / 'native'
home.mkdir()
for subdir in ('config', 'data', 'state', 'cache', 'bin', 'downloads'):
    (home / subdir).mkdir()
checkout = home / 'checkout'
for directory in ('lib', 'tools', 'shell', 'bin', 'dots'):
    shutil.copytree(repo / directory, checkout / directory)
(home / 'bin/bash').symlink_to(bash)
env = environment(home, home / 'bin')
env.update(INSTALL_PREFIX=str(home / 'custom prefix'), INSTALL_BIN_DIR=str(home / 'bin'))
cli = [str(bash), str(checkout / 'bin/remote-ssh')]
checks = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(name, args, expected=0, installer=False):
    entrypoint = [str(bash), str(checkout / 'tools/install-tool.sh')] if installer else cli
    result = subprocess.run(entrypoint + args, env=env, text=True, capture_output=True, timeout=60)
    (output / (name + '.log')).write_text(result.stdout + result.stderr)
    checks.append({'case': name, 'exit': result.returncode, 'passed': result.returncode == expected})
    if result.returncode != expected:
        raise AssertionError(name + ': ' + result.stdout + result.stderr)
    return result


curl = home / 'bin/curl'
curl_text = (
    '#!/bin/sh\n'
    f'[ "$#" -eq 3 ] && [ "$1" = -fsSLo ] && [ "$3" = {shlex.quote(url)} ] || exit 99\n'
    '/usr/bin/curl "$@" || exit $?\n'
    f'/usr/bin/shasum -a 256 "$2" >> {shlex.quote(str(home / "curl-audit"))}\n'
    f'cp "$2" {shlex.quote(str(home / "downloads" / archive_name))}\n'
)
curl.write_text(curl_text)
curl.chmod(0o755)

# The fixture adds only a prompt/observation hook. The production definition,
# launcher, editor settings, installer and session modules are copied unchanged.
hook = checkout / 'shell/rc.d/os.d/darwin.sh'
hook.parent.mkdir(exist_ok=True)
hook.write_text((hook.read_text() if hook.exists() else '') + r'''
capture() { printf '\036ARG:%s\037\n' "$*"; }
complete -W 'alpha beta' capture
history -s 'capture older'
history -s 'capture seeded'
PS1='BMARK> '
__release_probe_ready() {
    printf '\036STATE:%s:%s\037\n' "$REMOTE_SSH_FLYLINE_STATE" "$REMOTE_SSH_FLYLINE_REASON"
    printf '\036READY\037\n'
}
PROMPT_COMMAND+=(__release_probe_ready)
''')


def shell(name, enabled, expected_state, cases):
    session = Session(cli + ['shell'], env | {'REMOTE_SSH_ENABLE_FLYLINE': enabled}, home)
    try:
        session.expect(b'\x1eREADY\x1f', raw=True)
        session.expect(PROMPT)
        state = re.search(rb'\x1eSTATE:([^:\x1f]*):([^\x1f]*)\x1f', session.transcript)
        assert state and state[1].decode() == expected_state, bytes(session.transcript[-2000:])
        checks.append({'case': name, 'state': state[1].decode(), 'reason': state[2].decode(), 'passed': True})
        for label, text, keys, expected in cases:
            session.quiet(0.05)
            start = len(session.transcript)
            if text is not None:
                session.send(('capture ' + text).encode())
            session.quiet(0.1)
            for key in keys:
                session.send(key)
                session.quiet(0.12)
            assert not re.search(rb'\x1eARG:', session.transcript[start:]), 'early submission'
            session.send(b'\r')
            session.expect(b'\x1f', raw=True, timeout=4)
            session.expect(PROMPT)
            found = re.findall(rb'\x1eARG:([^\x1f]*)\x1f', session.transcript[start:])
            actual = found[-1].decode() if found else '[missing capture]'
            checks.append({'case': name + '/' + label, 'expected': expected, 'actual': actual, 'passed': actual == expected})
            assert actual == expected, (label, actual, expected)
    finally:
        session.close()
        (output / (name + '.pty.json')).write_text(json.dumps(session.transcript.decode(errors='replace')) + '\n')


try:
    assert platform.system() == 'Darwin' and platform.machine() == 'arm64'
    version = subprocess.check_output([bash, '--version'], text=True).splitlines()[0]
    assert '5.3.20' in version
    command('install', ['tool', 'install', 'flyline'])
    link = Path(env['INSTALL_PREFIX']) / '.active/flyline'
    assert link.is_symlink() and link.readlink().is_absolute()
    first = link.resolve()
    assert sha(first) == library_hash
    assert sha(home / 'downloads' / archive_name) == archive_hash
    assert not (home / 'bin/flyline').exists()
    command('check', ['check', '--strict', 'flyline'])
    listing = command('list', ['tool', 'list'])
    assert 'flyline' in listing.stdout and 'installed' in listing.stdout
    shell('active', '1', 'active', [
        ('history', None, [b'\x1b', b'kA'], 'seeded'),
        ('replace', 'ac', [b'\x1b', b'hrbA'], 'bc'),
        ('undo', 'ac', [b'\x1b', b'hrbuA'], 'ac'),
        ('redo', 'ac', [b'\x1b', b'hrbu', b'\x12', b'A'], 'bc'),
        ('dot-repeat', 'abcd', [b'\x1b', b'0wlx.A'], 'ad'),
        ('tab', 'al', [b'\t'], 'alpha'),
    ])
    shell('disabled', '0', 'disabled', [('readline', 'ac', [b'\x1b', b'hrbA'], 'bc')])
    command('reinstall', ['tool', 'install', 'flyline'])
    assert link.resolve() == first and sha(first) == library_hash, 'CLI reinstall must skip a valid pinned install'
    checks.append({'case': 'idempotent-cli-reinstall', 'passed': True})
    command('forced-reinstall', ['flyline'], installer=True)
    second = link.resolve()
    assert second != first and first.exists() and sha(second) == sha(first) == library_hash
    checks.append({'case': 'immutable-reinstall', 'passed': True})
    shell('after-reinstall', '1', 'active', [('replace', 'ac', [b'\x1b', b'hrbA'], 'bc')])
    curl.write_text('#!/bin/sh\nprintf corrupted > "$2"\n')
    failed = subprocess.run([str(bash), str(checkout / 'tools/install-tool.sh'), 'flyline'], env=env, text=True, capture_output=True, timeout=20)
    (output / 'checksum-rollback.log').write_text(failed.stdout + failed.stderr)
    assert failed.returncode != 0 and link.resolve() == second and sha(second) == library_hash
    checks.append({'case': 'checksum-rollback', 'passed': True})
    curl.write_text(curl_text)
    command('uninstall', ['uninstall', '--yes', 'flyline'])
    assert not link.is_symlink() and not first.exists() and not second.exists()
    shell('after-uninstall', '1', 'skipped', [('readline', 'ac', [b'\x1b', b'hrbA'], 'bc')])
    report = {'status': 'PASS', 'platform': 'macOS arm64', 'bash': version,
              'archive_sha256': archive_hash, 'library_sha256': library_hash,
              'definition_sha256': sha(checkout / 'tools/defs/flyline.sh'),
              'public_downloads': (home / 'curl-audit').read_text().splitlines(),
              'results': checks}
except Exception as exc:
    report = {'status': 'FAIL', 'error': str(exc), 'results': checks}
    raise
finally:
    (output / 'public-release-lifecycle.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
