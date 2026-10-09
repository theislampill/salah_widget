"""Serial native entry controls; a held transfer is not ordinary startup timing."""
import hashlib,json,os,pathlib,shutil,subprocess,datetime
R=pathlib.Path(__file__).resolve().parent
OUT=R/'evidence/PR43-review/R1-entry-final-04'
OUT.mkdir(exist_ok=False)
driver=pathlib.Path(r'C:\Users\theis\.codex\worktrees\pr43-review-revision\salah_widget\tools\cp9\pr43_entry_stream.py')
PY=r'C:\workspace\ai\cp9-integration-20261005\venv\Scripts\python.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pin=sha(driver);rows=[];cases=[]
for engine in ['chromium','firefox']:
 for scene in ['night','day']:
  for mode in ['held-tail','held-core','compressed']:
   extra=['--kib-per-second','512'] if mode=='compressed' else ['--wait-final'] if mode=='held-tail' and scene=='night' else []
   cases.append((engine,'green',mode,scene,extra))
ledger=R/'ACTIVE_LEDGER.json'
try:
 for number,(engine,stage,mode,scene,extra) in enumerate(cases,1):
  assert sha(driver)==pin,'harness changed during matrix'
  name=f'{number:02}-{engine}-{stage}-{mode}-{scene}'
  site=R/('snapshots/pr43' if stage=='red' else 'candidates/pr43-r1r2-04')
  cmd=[PY,'-B','-X','utf8',str(driver),'--root',str(site),'--out',str(OUT/name),'--mode',mode,'--scene',scene,*extra]
  d=json.loads(ledger.read_text());q=d['resourceLeases']['heavy-browser'];assert q['holder'] in [None,'root']
  q.update(holder='root',status='RUNNING',scope='PR43 R1 actual entry matrix',leaseId='root-pr43-entry-final-04',currentCase=name,command=cmd,completedCases=number-1,totalCases=len(cases));ledger.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
  env={**os.environ,'SALAH_BROWSER':engine,'SALAH_BROWSER_EXECUTABLE':str(pathlib.Path(os.environ['LOCALAPPDATA'])/'ms-playwright'/('chromium-1223/chrome-win64/chrome.exe' if engine=='chromium' else 'firefox-1522/firefox/firefox.exe'))}
  result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',env=env)
  (OUT/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
  report=json.loads((OUT/name/'results.json').read_text()) if (OUT/name/'results.json').exists() else {}
  expected=False if stage=='red' and mode=='held-tail' else True if mode.startswith('held-') else None
  row={'name':name,'command':cmd,'exitCode':result.returncode,'status':report.get('status'),'causalPass':report.get('causalPass'),
       'expectedCausalPass':expected,'expectedOutcomeObserved':report.get('causalPass')==expected if expected is not None else None,
       'runtime':report.get('runtime',{}).get('treeSha256'),'entrySha256':report.get('entrySha256'),'errors':report.get('pageErrors'),'finalRefinement':{k:report.get('finalRefinement',{}).get(k) for k in ['at','moon','moonDetail']},
       'byteCounts':{k:report.get(k) for k in ['decodedEntryBytes','gzipEntityBytes']}}
  rows.append(row);(OUT/'receipt.json').write_text(json.dumps({'complete':False,'cases':rows,'harnessSha256':pin},indent=2)+'\n');print(json.dumps({k:row.get(k) for k in ['name','exitCode','status','causalPass','errors']}),flush=True)
  if result.returncode or report.get('status')=='HARNESS_OR_READINESS_FAILURE':break
finally:
 d=json.loads(ledger.read_text());d['resourceLeases']['heavy-browser'].update(holder=None,status='FREE',currentCase=None,command=None,lastResult=str(OUT/'receipt.json'));ledger.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(OUT/'receipt.json').write_text(json.dumps({'complete':len(rows)==len(cases),'cases':rows,'harnessSha256':pin,'scope':'Actual entry causal/current typography/context captures. Held timing excludes ordinary S1 budget claims. Full terrain refinement remains separate.'},indent=2)+'\n')
