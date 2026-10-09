"""Seal the final-source font fork; no native execution or source writes."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
WORK=HERE.parent;RUN=HERE.parents[2]
PYTHON=Path(r'C:\workspace\ai\cp9-integration-20261005\venv\Scripts\python.exe')
NODE=Path(r'C:\Users\theis\AppData\Local\OpenAI\Codex\bin\node.exe')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
binding=read(HERE/'SOURCE_BINDING.json');source=binding['sources']['04'];base=read(WORK/'font-driver-r4/SEAL.json')
files=list(base['files'])
for name in files:
    if name.endswith('.py'):ast.parse((HERE/name).read_text(encoding='utf-8'))
    if name!='rlgwo-clock-date-fixture.cjs':assert sha(HERE/name)==base['files'][name]['sha256']
variants=['missing','delayed-css-forenoon','delayed-bytes-forenoon','split-face-forenoon','loaded-forenoon','permanent-bytes-forenoon','warm-cache-forenoon','loaded-sunrise','loaded-maghrib']
commands=[];rows=[]
for engine,exe in [('chromium',r'C:\Users\theis\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'),('firefox',r'C:\Users\theis\AppData\Local\ms-playwright\firefox-1522\firefox\firefox.exe')]:
    prepared=read(HERE/('prepared-'+engine)/'manifest.json');assert prepared['execution']=='NOT_EXECUTED' and len(prepared['inputs'])==9
    assert prepared['driverSha256']==sha(HERE/'rlgwo_native_checks.py') and prepared['adapterSha256']==sha(HERE/'rlgwo-clock-date-fixture.cjs')
    assert prepared['runtimeIdentity']['treeSha256']==source['runtimeTreeSha256']
    for item in prepared['inputs']:
        assert item['identity']['sourceSha256']==source['indexSha256'] and item['identity']['runtimeTreeSha256']==source['runtimeTreeSha256']
        assert item['identity']['sourceMutation'] is None
        metadata=read(Path(item['metadata']));assert metadata['identity']==item['identity']
        assert sha(Path(item['metadata']).with_suffix('.html'))==item['identity']['fixtureSha256']
        rows.append({'engine':engine,'case':item['case'],'variant':item['variant'],'preparedMetadata':item['metadata'],'identity':item['identity']})
    output=RUN/'evidence/PR43-review/R2-final-font-04'/(engine+'-green')
    command=[str(PYTHON),'-B','-X','utf8',str(HERE/'rlgwo_date_disclosure_check.py'),'--root',source['root'],'--engine',engine,'--node',str(NODE),'--cases','font','--variants',','.join(variants),'--expected-source-sha256',source['indexSha256'],'--output',str(output),'--execute','--lease-id','<ROOT_ISSUED_CAPACITY_ONE_LEASE>']
    commands.append({'engine':engine,'environment':{'SALAH_BROWSER':engine,'SALAH_BROWSER_EXECUTABLE':exe},'command':command,'requires':'Root recorded capacity-one lease; candidates only, engines sequential; fresh output identity; reuse reviewed-source failures rather than replay'})
old=[]
for version in ['r1','r2','r3','r4']:
    seal_path=WORK/('font-driver-'+version)/'SEAL.json';seal=read(seal_path)
    for name,identity in seal['files'].items():assert sha(seal_path.parent/name)==identity['sha256']
    old.append({'version':version,'path':str(seal_path),'sha256':sha(seal_path),'unchanged':True})
date_seal=WORK/'r0018-date-geometry-r1/SEAL.json'
for name,identity in read(date_seal)['files'].items():assert sha(date_seal.parent/name)==identity['sha256']
write(HERE/'CASE_MANIFEST.json',{'schema':'clock-date-font-final04-cases/1','status':'PREPARED_NOT_EXECUTED','workerNativeLaunches':0,'requiredRows':18,'rows':rows,'commands':commands,'sourceBinding':str(HERE/'SOURCE_BINDING.json'),'scope':'Final-source candidate-only font qualification; no original/intermediate source replay, decoder benchmark, font repair or native node completion'})
names=files+['SOURCE_BINDING.json','runtime-identity.json','CHANGES.json','CASE_MANIFEST.json','NEXT_NATIVE_COMMANDS.ps1','README.md','admission-controls.cjs','acquire_binding.py','fork_driver.py','seal_and_report.py']
seal={'schema':'clock-date-font-driver-seal/5','status':'PREPARED_NOT_EXECUTED','files':{name:{'bytes':(HERE/name).stat().st_size,'sha256':sha(HERE/name)} for name in names},
    'sourceIndexSha256':source['indexSha256'],'runtimeTreeSha256':source['runtimeTreeSha256'],'sourceBindingSha256':sha(HERE/'SOURCE_BINDING.json'),'controls':{'path':str(HERE/'admission-controls-green.log'),'sha256':sha(HERE/'admission-controls-green.log'),'assertions':74},'preparedManifests':[str(HERE/('prepared-'+e)/'manifest.json') for e in ['chromium','firefox']],
    'oldSeals':old,'admittedDateSealUnchanged':{'path':str(date_seal),'sha256':sha(date_seal)},'naturalObservationCodeUnchanged':True,'pythonDriverBytesUnchanged':True,'workerNativeLaunches':0}
write(HERE/'SEAL.json',seal)
report={'status':'READY_FOR_ROOT_SERIAL_CANDIDATE_FONT_EXECUTION','nodeComplete':False,'workerNativeLaunches':0,'preparedRows':18,'actualNativeRowsExecutedByWorker':0,'seal':str(HERE/'SEAL.json'),'sealSha256':sha(HERE/'SEAL.json'),'sourceIndexSha256':source['indexSha256'],'runtimeTreeSha256':source['runtimeTreeSha256'],
    'sourceBinding':str(HERE/'SOURCE_BINDING.json'),'unchangedOwners':binding['unchanged'],'rootBuildReceipt':binding['rootBuildReceipt'],'rootBuildReceiptSha256':binding['rootBuildReceiptSha256'],'cheapControlAssertions':74,'commands':commands,'oldSeals':old,
    'preservedFailures':[{'path':str(HERE/name),'sha256':sha(HERE/name),'reason':reason} for name,reason in [('admission-controls-red.log','Control syntax typo; repaired before implementation'),('admission-controls-missing-red.log','Expected missing r5 adapter RED'),('prepare-chromium.log','Preparation incorrectly used -I, which disables wrapper sibling import; corrected command only'),('prepare-firefox.log','Same incorrect -I preparation command; no browser/effect occurred')]],
    'limits':['No actual font/browser/decoder/timing proof from this worker. Root owns serialized final-source native execution and independent pixel/closure review.','This is a strict admission fork only: all observation/action bodies and Python bytes remain those of r4.','Encoded/manifest bytes are read equal; decoded identity is bound to retained root11codec controls, not a new worker decoder run.','The running/admitted date r1 driver is immutable; its newly returned network-abort failures require separate source/lifecycle diagnosis, with no gate waiver or native replay.']}
write(HERE/'REPORT.json',report)
(HERE/'REPORT.md').write_text('Sealed r5 is ready for root candidate-only final-source font qualification: nine variants in Chromium then Firefox,18 prepared rows and zero worker browser launches.\n\nCandidate04 index67e2ff84... and runtime040192b5... are bound after the root PASS deterministic-build/V1 receipt. Only Moon-initial ordered script2 changed; authored nativea81b32..., generated corea36585..., CSS35be2e... and font owneraf5ebb... remain exact. The font owner also matches candidate02. Encoded/manifest bytes match; root11codec controls bind decoded identity.\n\n74 cheap exact admission/compile/loss assertions passed. Python and natural observation/action bodies remain byte-identical to r4. Unknown scripts/bodies/documents/runtime inventories reject. r1-r4 and the admitted date driver seals remain unchanged.\n\nExact commands are in NEXT_NATIVE_COMMANDS.ps1/CASE_MANIFEST.json after root acquires its actual capacity-one lease. Reviewed original and intermediate failures are reused, not replayed. Final native fonts/pixels/source qualification and node closure remain pending.\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','preparedRows','workerNativeLaunches','seal','sealSha256','sourceIndexSha256','runtimeTreeSha256']}))
