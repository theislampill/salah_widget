"""Serialized actual-widget font controls. Retain failures and private contexts."""
from pathlib import Path
import hashlib,json,os,subprocess

RUN=Path(__file__).resolve().parent
PYTHON=r'C:\workspace\ai\cp9-integration-20261005\venv\Scripts\python.exe'
DRIVER=RUN/'workers/clock_date/font-driver-r5'
OUT=RUN/'evidence/PR43-review/R2-font-final-04'
seal=json.loads((DRIVER/'SEAL.json').read_text())
for name,pin in seal['files'].items():assert hashlib.sha256((DRIVER/name).read_bytes()).hexdigest()==pin['sha256'],name
OUT.mkdir(exist_ok=False)
ledger=RUN/'ACTIVE_LEDGER.json'
d=json.loads(ledger.read_text());assert d['resourceLeases']['heavy-browser']['status']=='FREE'
remaining='split-face-forenoon,delayed-css-forenoon,missing,delayed-bytes-forenoon,loaded-forenoon,permanent-bytes-forenoon,warm-cache-forenoon,loaded-sunrise,loaded-maghrib'
rows=[]
try:
 for engine in ['chromium','firefox']:
  executable=Path(os.environ['LOCALAPPDATA'])/'ms-playwright'/('chromium-1223/chrome-win64/chrome.exe' if engine=='chromium' else 'firefox-1522/firefox/firefox.exe')
  for stage,root,index in [('green',RUN/'candidates/pr43-r1r2-04','67e2ff84eb1e7422bfc390f98b641c8e3f93f76a77400401681be10676eb8d3d')]:
   name=engine+'-'+stage;target=OUT/name
   d=json.loads(ledger.read_text());d['resourceLeases']['heavy-browser'].update(holder='root',status='RUNNING',scope='PR43 R2 actual font matrix',currentCase=name,leaseId='root-pr43-font-final-04');ledger.write_text(json.dumps(d,indent=2)+'\n')
   command=[PYTHON,'-B','-X','utf8',str(DRIVER/'rlgwo_date_disclosure_check.py'),'--root',str(root),'--engine',engine,'--cases','font','--expected-source-sha256',index,'--node',r'C:\Users\theis\AppData\Local\OpenAI\Codex\bin\node.exe','--output',str(target),'--execute','--lease-id','root-pr43-font-final-04']
   command+=['--variants',remaining]
   env={**os.environ,'SALAH_BROWSER':engine,'SALAH_BROWSER_EXECUTABLE':str(executable)}
   result=subprocess.run(command,env=env,capture_output=True,text=True,encoding='utf-8')
   (OUT/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
   manifest=json.loads((target/'manifest.json').read_text()) if (target/'manifest.json').exists() else {}
   rows.append({'stage':stage,'engine':engine,'exitCode':result.returncode,'command':command,'results':manifest.get('results',[])})
   (OUT/'receipt.json').write_text(json.dumps({'jobs':rows,'complete':False},indent=2)+'\n');print(json.dumps({'job':name,'exitCode':result.returncode,'results':manifest.get('results',[])}),flush=True)
finally:
 d=json.loads(ledger.read_text());d['resourceLeases']['heavy-browser'].update(holder=None,status='FREE',currentCase=None,lastResult=str(OUT/'receipt.json'));ledger.write_text(json.dumps(d,indent=2)+'\n')
(OUT/'receipt.json').write_text(json.dumps({'jobs':rows,'complete':len(rows)==2,'reusedRed':'R2-font-matrix-02 and R2-intermediate-controls-01 retain exact earlier RED; not rerun here','scope':'Typography with native FontFaceSet and real Google font bytes; controlled clock/providers/storage and observation wrappers. Not startup or whole-renderer qualification.'},indent=2)+'\n')
