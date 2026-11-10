from test_audit_sequences import audit_engine
from test_managed_lifecycle import command


def test_repeat_uninstall_does_not_block_later_unrelated_install(audit_engine):
    e = audit_engine
    e.asset('rg')
    e.asset('fd')
    for args in [('install', 'rg', '--yes'), ('uninstall', 'rg', '--yes')]:
        result = command(e, *args)
        assert result.returncode == 0, (result.stdout, result.stderr)
    repeat = command(e, 'uninstall', 'rg', '--yes')
    later = command(e, 'install', 'fd', '--yes')
    journal = e.private('ms_state_load\nms_journal_active\nprintf "phase=%s\\n" "$MS_BATCH_PHASE"\n')
    assert later.returncode == 0, (repeat.returncode, later.stdout, later.stderr, journal.stdout)
