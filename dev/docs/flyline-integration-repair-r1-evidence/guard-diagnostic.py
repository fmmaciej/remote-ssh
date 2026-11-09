"""Bounded paired diagnostic of the repair's enabled guard path, no native load."""
from __future__ import annotations
import argparse, hashlib, json, re, statistics, sys, tempfile
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--bash',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--rounds',type=int,default=3)
p.add_argument('--loops',type=int,default=100)
a=p.parse_args()
a.repo=a.repo.resolve();a.output=a.output.resolve();a.bash=a.bash.resolve()
sys.path.insert(0,str(a.repo/'dev/docs/interactive-tools-performance-evidence'))
from benchmark import Session, environment
modules={'before':a.repo/'dev/docs/flyline-integration-repair-r1-evidence/source-before/files/shell/rc.d/29-flyline.sh','current':a.repo/'shell/rc.d/29-flyline.sh'}
a.output.mkdir(parents=True,exist_ok=False)
results=[]
for round_no in range(a.rounds):
    order=('before','current') if round_no%2==0 else ('current','before')
    for variant in order:
        with tempfile.TemporaryDirectory(prefix='flyline-guard-profile-') as d:
            home=Path(d)
            env=environment(home,Path('/usr/bin'))
            env.update(MODULE=str(modules[variant]),LOOPS=str(a.loops))
            rc=home/'rc.sh'
            rc.write_text(r'''
source "$MODULE"
REMOTE_SSH_ENABLE_FLYLINE=1
REMOTE_SSH_HISTORY_BACKEND=bash
remote_flyline_library() { return 1; }
TIMEFORMAT=$'\036TIMING:%R\037'
time for ((i=0; i<LOOPS; i++)); do
  unset REMOTE_SSH_FLYLINE_PID
  remote_flyline_finalize
done
printf '\036DONE:%s:%s\037\n' "$REMOTE_SSH_FLYLINE_STATE" "$REMOTE_SSH_FLYLINE_REASON"
PS1='GUARD> '
''')
            session=Session([str(a.bash),'--noprofile','--rcfile',str(rc),'-i'],env,home)
            row={'round':round_no,'variant':variant}
            try:
                session.expect(b'\x1eDONE:skipped:unavailable\x1f',raw=True)
                session.expect(b'GUARD> ')
                timing=re.findall(rb'\x1eTIMING:([0-9.]+)\x1f',session.transcript)
                row.update(ms_per_guard=float(timing[-1])*1000/a.loops,passed=True)
            except (RuntimeError,ValueError,IndexError) as exc:
                row.update(passed=False,error=str(exc))
            finally:
                row['resources']=session.close()
                (a.output/f'{round_no}-{variant}.txt').write_text(json.dumps(session.transcript.decode(errors='replace'))+'\n')
            results.append(row)
            print(json.dumps(row),flush=True)
medians={key:statistics.median(r['ms_per_guard'] for r in results if r['variant']==key and r['passed']) for key in modules}
report={'rounds':a.rounds,'loops_per_run':a.loops,'source_sha256':{key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in modules.items()},'results':results,'medians_ms':medians,'increment_ms':medians['current']-medians['before'],'passed':all(r['passed'] for r in results),'scope':'Guard-only diagnostic, not startup acceptance or native compatibility'}
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
raise SystemExit(0 if report['passed'] else 1)
