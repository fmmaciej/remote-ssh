"""Offline recovery check against the exact documented Git revision."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

repo=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
pin='c5fa54c70fba2ca931af5b241f166fb6bec98a06'
base=output/'pinned-recovery'
base.mkdir()
recovery=base/'checkout'
clone=subprocess.run(['git','clone','--no-local',str(repo),str(recovery)],capture_output=True,text=True)
(base/'clone.log').write_text(clone.stdout+clone.stderr)
assert clone.returncode==0,clone.stderr
checkout=subprocess.run(['git','-C',str(recovery),'checkout','--detach',pin],capture_output=True,text=True)
assert checkout.returncode==0,checkout.stderr
actual=subprocess.check_output(['git','-C',str(recovery),'rev-parse','HEAD'],text=True).strip()
assert actual==pin
results=[]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for index,bash in enumerate(dict.fromkeys([str(Path('/bin/bash').resolve()),str(Path(shutil.which('bash')).resolve())])):
    home=base/f'case-{index}'
    for name in ('bin','opt with space','external','config/remote-ssh','state','cache'):
        (home/name).mkdir(parents=True,exist_ok=True)
    prefix=home/'opt with space'
    bindir=home/'bin'
    (bindir/'bash').symlink_to(bash)
    owned={}
    for tool,version in (('fzf','0.67.0'),('sk','5.9.0')):
        release=prefix/f'{tool}-{version}'
        release.mkdir()
        executable=release/tool
        executable.write_text('#!/bin/sh\nexit 0\n')
        executable.chmod(0o755)
        (release/'.remote-ssh-release').write_text(f'format=1\ntool={tool}\nversion={version}\nlayout=binary\nexecutable={tool}\n')
        (bindir/tool).symlink_to(executable)
        owned[tool]=executable
    external=home/'external/fzf'
    external.write_text('external fzf: keep\n')
    external.chmod(0o755)
    expected=home/'config/remote-ssh/expected-tools'
    expected.write_text('fzf\nsk\n')
    expected_before=expected.read_bytes()
    active=prefix/'.active'
    active.write_text('unrelated active path\n')
    latest=home/'latest-without-definition'
    for name in ('lib','tools','shell','bin','dots'):
        shutil.copytree(repo/name,latest/name)
    (latest/'tools/defs/fzf.sh').unlink()
    env={
        'HOME':str(home),'XDG_CONFIG_HOME':str(home/'config'),
        'XDG_STATE_HOME':str(home/'state'),'XDG_CACHE_HOME':str(home/'cache'),
        'PATH':f'{home / "external"}:{bindir}:/usr/bin:/bin',
        'INSTALL_PREFIX':str(prefix),'INSTALL_BIN_DIR':str(bindir),
        'REMOTE_ENV_DIR':str(latest),'REMOTE_SSH_UPDATE_CHECK':'0',
        'REMOTE_SSH_WELCOME':'0','REMOTE_SSH_ENABLE_ATUIN_AUTO_IMPORT':'0',
    }
    checks=[]
    for label,entry in (('latest',latest),('inherited-env',recovery)):
        result=subprocess.run([bash,str(entry/'bin/remote-ssh'),'uninstall','--yes','fzf'],env=env,capture_output=True,text=True,timeout=15)
        assert result.returncode!=0 and 'Unknown tool: fzf' in result.stderr,(label,result)
        assert owned['fzf'].exists() and expected.read_bytes()==expected_before
        checks.append({'case':label,'exit':result.returncode,'preserved':True})
    keep={str(path):digest(path) for path in (owned['sk'],external,active)}
    result=subprocess.run([bash,str(recovery/'bin/remote-ssh'),'uninstall','--yes','fzf'],env=env|{'REMOTE_ENV_DIR':str(recovery)},capture_output=True,text=True,timeout=15)
    (base/f'case-{index}.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    assert not owned['fzf'].parent.exists() and not (bindir/'fzf').is_symlink()
    assert (bindir/'sk').is_symlink()
    assert all(digest(Path(path))==value for path,value in keep.items())
    assert [line for line in expected.read_text().splitlines() if line and not line.startswith('#')]==['sk']
    checks.append({'case':'pinned-recovery','exit':0,'removed':'managed fzf only','preserved':['skim','external fzf','unrelated .active'],'expected_tools':['sk']})
    results.append({'bash':subprocess.check_output([bash,'--version'],text=True).splitlines()[0],'passed':True,'checks':checks})
report={'status':'PASS','revision':actual,'source':'local Git clone of documented revision; no network','results':results}
(output/'pinned-recovery.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
