from pathlib import Path
import sys

import pytest

REPO = Path('/Users/fm/Programming/00_Other/remote-ssh')
sys.path.insert(0, str(REPO / 'dev/tests'))
import conftest
from managed_fixture import make_engine
from test_managed_lifecycle import command, snapshot


@pytest.fixture(params=['/bin/bash', '/opt/homebrew/bin/bash'])
def audit_engine(tmp_path, request):
    isolated = conftest.isolated_env.__wrapped__(tmp_path)
    return make_engine(REPO, isolated, str(Path(request.param).resolve()))


def test_repeated_successful_uninstall_is_readonly_noop(audit_engine):
    e = audit_engine
    e.asset('rg')
    first = command(e, 'install', 'rg', '--yes')
    assert first.returncode == 0, (first.stdout, first.stderr)
    first = command(e, 'uninstall', 'rg', '--yes')
    assert first.returncode == 0, (first.stdout, first.stderr)
    before = snapshot(e)
    again = command(e, 'uninstall', 'rg', '--yes')
    assert again.returncode == 0, (again.stdout, again.stderr)
    assert snapshot(e) == before


def test_successfully_uninstalled_tool_is_available_in_catalog(audit_engine):
    e = audit_engine
    e.asset('rg')
    for args in [('install', 'rg', '--yes'), ('uninstall', 'rg', '--yes')]:
        result = command(e, *args)
        assert result.returncode == 0, (result.stdout, result.stderr)
    result = command(e, 'list')
    assert result.returncode == 0, (result.stdout, result.stderr)
    row = next(line for line in result.stdout.splitlines() if line.startswith('rg '))
    assert 'unmanaged' in row
    assert 'available' in row and 'missing' not in row and 'broken' not in row, row
