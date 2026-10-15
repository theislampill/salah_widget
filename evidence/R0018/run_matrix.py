"""Finite, serial R0018 calls to the existing native collector; no retry loop."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys

ROOT=Path(r'C:\Users\theis\.codex\worktrees\r0018-readability\salah_widget')
OUT=Path(__file__).resolve().parent
PY=Path(r'C:\Users\theis\.codex\tmp\r000d-runtime-20261014\Scripts\python.exe')
NODE=Path(r'C:\workspace\ai\cp9-integration-20261005\toolchain\node-v22.16.0-win-x64\node.exe')
BROWSERS={'chromium':Path(r'C:\Users\theis\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'),'firefox':Path(r'C:\Users\theis\AppData\Local\ms-playwright\firefox-1522\firefox\firefox.exe')}

def cases():
    rows=[]
    for scene in ['noon','sunrise','sunset','night','broken','overcast']:
        rows.append(dict(scene=scene,view='desktop',dpr=1,date='compact',appearance='default',stress=False))
    for view in ['desktop','constrained']:
        for dpr in [1,2]:
            for date in ['compact','long','stale']:
                if (view,dpr,date)==('desktop',1,'compact'):continue
                rows.append(dict(scene='noon',view=view,dpr=dpr,date=date,appearance='default',stress=False))
    for appearance in ['default','contrast']:
        rows.append(dict(scene='noon',view='constrained',dpr=2,date='compact',appearance=appearance,stress=True))
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['red','green','mutant']);p.add_argument('--engine',choices=list(BROWSERS));p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int);a=p.parse_args()
    population=cases() if a.stage!='mutant' else [dict(scene='noon',view='desktop',dpr=1,date='compact',appearance='default',stress=True,mutant=m) for m in ['default-past','default-base','default-on']]
    all_rows=[]
    for engine in ([a.engine] if a.engine else BROWSERS):
        for c in population[a.start:a.stop]:
            name='-'.join([a.stage,engine,c['scene'],c['view'],'dpr'+str(c['dpr']),c['date'],c['appearance']]+(['white'] if c['stress'] else [])+([c['mutant']] if c.get('mutant') else []))
            target=OUT/'matrix'/name
            if target.exists():raise RuntimeError('Existing attempt must be reconciled, never overwritten: '+name)
            width,height=(1100,900) if c['view']=='desktop' else (375,800)
            command=[str(PY),'-I','-B',str(ROOT/'tests/r0018-default-readability.py'),'--workspace',str(ROOT if a.stage!='red' else OUT/'baseline'),'--output',str(target),'--stage',a.stage,'--scene',c['scene'],'--width',str(width),'--height',str(height),'--dpr',str(c['dpr']),'--date-case',c['date'],'--appearance',c['appearance'],'--font-fixture',str(OUT/'fonts'),'--node',str(NODE)]
            if c['stress']:command.append('--stress')
            if c.get('mutant'):command+=['--mutant',c['mutant']]
            env={**os.environ,'SALAH_BROWSER':engine,'SALAH_BROWSER_EXECUTABLE':str(BROWSERS[engine])}
            proc=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=210)
            target.mkdir(parents=True,exist_ok=True)
            (target/'command.json').write_text(json.dumps({'argv':command,'browser':str(BROWSERS[engine]),'returncode':proc.returncode},indent=2)+'\n')
            (target/'stdout.log').write_bytes(proc.stdout);(target/'stderr.log').write_bytes(proc.stderr)
            result=json.loads((target/'results.json').read_text()) if (target/'results.json').exists() else {}
            failures=result.get('failures',[])
            semantic_only=bool(failures) and all(x.startswith('text-') and (x.endswith('-opacity1') or x.endswith('-intended-contrast')) for x in failures)
            expected_fail=a.stage=='mutant' or (a.stage=='red' and c['appearance']=='default')
            reached=(result.get('status')=='FAIL' and semantic_only) if expected_fail else result.get('status')=='PASS_SCOPED'
            row={'id':name,'case':c,'engine':engine,'status':result.get('status'),'expectedSemanticFailure':expected_fail,'reachedExpected':reached,'failures':failures,'result':str(target/'results.json'),'resultSha256':hashlib.sha256((target/'results.json').read_bytes()).hexdigest() if result else None,'minIntendedContrast':min([x['minimumIntendedContrast'] for x in result.get('texts',[])],default=None)}
            all_rows.append(row);(OUT/(a.stage+'-'+(a.engine or 'both')+'-from'+str(a.start)+'-progress.json')).write_text(json.dumps(all_rows,indent=2)+'\n')
            print(json.dumps(row),flush=True)
            if not reached:raise RuntimeError('Unqualified attempt retained; diagnose before further execution: '+name)

if __name__=='__main__':main()
