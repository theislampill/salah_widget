"""Exact affected successor source admission review. No native/real-ledger/public effects."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent
RUN=OUT.parents[2]
A=RUN/'workers/r0010_delivered_native_closure_r2'
P=RUN/'workers/r0010_delivered_native_closure_r1'
Q=RUN/'workers/r0010_isolated_release_review_r1/delivered-native-source-admission-r1'
HEAD='88926dd12d22a6a8c1cd369d4823750778fccb48'
RUNTIME='f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
PIN='7261e6808570fd8dedac479a55d872bada63f3c3605030ab43ee8bc222523f69'
CASES=['fresh-2-f','fresh-2-c','fresh-4-f','fresh-4-c','generic-local','saved-native-reload','prefer-local-fresh','prefer-local-saved','mutant-omitMethod','mutant-omitUnits']
checks=[]
commands=[]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
now=lambda:datetime.now(timezone.utc).isoformat()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def h(p):
    digest=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(4194304),b''):digest.update(data)
    return digest.hexdigest()
def ref(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':h(p)}
def ck(name,condition,details=None):
    checks.append({'claim':name,'passed':bool(condition),'details':details})
    if not condition:raise AssertionError(name)
def exact(row):
    value=ref(row['path']);ck('exact ref '+row['path'],value['sha256']==row['sha256'] and ('bytes' not in row or value['bytes']==row['bytes']));return value
def packet(root,pin):
    ck('packet seal '+str(root),h(root/'SEAL.json')==pin)
    seal=read(root/'SEAL.json');ck('packet manifest '+str(root),h(root/'MANIFEST.json')==seal['manifestSha256'])
    manifest=read(root/'MANIFEST.json');rows=manifest['files'];seen=set()
    for row in rows:
        rel=row['path'];p=(root/rel).resolve()
        ck('manifest confinement '+rel,rel not in seen and p.is_relative_to(root.resolve()) and '..' not in Path(rel).parts);seen.add(rel)
        exact({**row,'path':str(p)})
    ck('packet member count '+str(root),len(rows)==seal.get('fileCount',len(rows)))
    return seal
def command(name,args):
    started=now();env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
    done=subprocess.run([str(x) for x in args],cwd=OUT,env=env,capture_output=True,timeout=60)
    raw=OUT/'raw';raw.mkdir(exist_ok=True)
    for s in ['stdout','stderr']:(raw/(name+'.'+s)).write_bytes(getattr(done,s))
    record={'name':name,'argv':[str(x) for x in args],'startedAtUtc':started,'finishedAtUtc':now(),'exitCode':done.returncode,'stdout':ref(raw/(name+'.stdout')),'stderr':ref(raw/(name+'.stderr'))};commands.append(record)
    ck('command '+name,done.returncode==0,record);return done.stdout

seal=packet(A,PIN)
ck('expected successor manifest/report',seal['manifestSha256']=='046e9e375396c8b46f063b8b879f3a60d31f5016abde04dcabe4cdff3ab25109' and h(A/'REPORT.json')==seal['reportSha256']=='2e3deebd7979c7076edfd400054ba57e9a6b67789fbf9edbabbd9e5c33566b89')
packet(P,'b959e853461371845d1bc67bc0bd6852104cf2114784437c9c18e7a5db2a6efa')
packet(Q,'9ce4b2f3b5ca83bf38d056d28d06e3f0c5eb38a0698d010c1f683c05d09647c4')
report=read(A/'REPORT.json');binding=read(A/'native/source-binding.json');runtime=read(A/'RUNTIME.json');boundary=read(A/'BOUNDARY.json');selection=read(A/'CASE_SELECTION.json');queue=read(A/'ROOT_QUEUE.json');rootcmd=read(A/'ROOT_COMMAND.json');correction=read(A/'CORRECTION.json')
for row in [report['sourceSnapshotPredecessorSeal'],report['requestChangesReviewSeal'],report['correction'],boundary['ownerAuthority']]:exact(row)
ck('same directly confirmed authority',boundary['ownerAuthority']['sha256']=='dfbb98a6f3812d299b77315c5a62c3b24c19691b7b50a851003596a9a4c4c48f')
for name in ['native/residual-location-native.py','native/residual-location-actions.cjs','native/residual-location-native.html','native/source-binding.json','RUNTIME.json']:
    ck('protected raw source byte equality '+name,(A/name).read_bytes()==(P/name).read_bytes())
snapshot=Path(binding['candidateRoot'])
ck('same immutable delivered snapshot',snapshot==P/'input/main' and binding['sourceRef']==binding['producerHead']==selection['sourceRef']==selection['deliveredHead']==boundary['deliveredMain']==report['sourceHead']==HEAD)
ck('case manifest target mismatch repaired',selection['sourceRoot']==binding['candidateRoot'] and selection['runtimeSha256']==binding['runtimeSha256']==RUNTIME and 'ten explicit --only selectors' in selection['selection'])
ck('native case objects preserved', [{k:v for k,v in row.items() if k!='rawReceiptExpected'} for row in selection['cases']]==[{k:v for k,v in row.items() if k!='rawReceiptExpected'} for row in read(P/'CASE_SELECTION.json')['cases']])
ck('root queue command and manifest exact original ten',queue['exactCases']==[c['name'] for c in selection['cases']]==CASES and [rootcmd['argvTemplate'][i+1] for i,x in enumerate(rootcmd['argvTemplate']) if x=='--only']==CASES)
ck('command target/ref/head exact',rootcmd['argvTemplate'][rootcmd['argvTemplate'].index('--source-root')+1]==str(snapshot) and rootcmd['argvTemplate'][rootcmd['argvTemplate'].index('--source-ref')+1]==HEAD)
ck('runtime canonical binding',runtime['files']==binding['runtimeRows'] and hashlib.sha256(''.join(row['sha256']+'  '+name+'\n' for name,row in sorted(runtime['files'].items())).encode()).hexdigest()==RUNTIME and len(runtime['files'])==135)
for name,row in runtime['files'].items():exact({**row,'path':str(snapshot/name)})
ck('one correction charged without reset',correction['maximumPerOriginalCase']==2 and set(correction['cyclesUsedPerOriginalCase'])==set(CASES) and all(x==1 for x in correction['cyclesUsedPerOriginalCase'].values()) and report['additionalCorrectionReviewCyclesSpentPerOriginalCase']==correction['cyclesUsedPerOriginalCase'] and correction['diagnosticsResetLimit'] is False and correction['nativeAcquisitionAttempts']==0)
for row in list(rootcmd['toolIdentities'].values())+[rootcmd[k] for k in ['driverIdentity','actionsIdentity','fixtureIdentity','bindingIdentity']]:exact(row)
old_source=(P/'root_dispatch_proposal.py').read_text(encoding='utf-8');new_source=(A/'root_dispatch_proposal.py').read_text(encoding='utf-8')
old_tree=ast.parse(old_source);new_tree=ast.parse(new_source)
old_main=next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');new_main=next(n for n in new_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
i=next(i for i,n in enumerate(new_main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='selection' for t in n.targets))
nodes=new_main.body[i:i+2]
ck('new guard is assign and assert',isinstance(nodes[0],ast.Assign) and isinstance(nodes[1],ast.Assert))
raw_i=next(i for i,n in enumerate(new_main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='raw' for t in n.targets))
ck('actual guard before any ledger read',i<raw_i)
guard_code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(A/'root_dispatch_proposal.py')+' [actual guard only]','exec')
inputs=[('old historical header refused',read(P/'CASE_SELECTION.json'),False),('exact delivered header accepted',selection,True)]
for key,value in [('sourceRoot','wrong-historical-root'),('runtimeSha256','0'*64),('sourceRef','18ff14860ff41c084b1db5f396bb62aa9c22b1be'),('group','r0011')]:
    value_input=copy.deepcopy(selection);value_input[key]=value;inputs.append((key+' drift refused',value_input,False))
reordered=copy.deepcopy(selection);reordered['cases'][0],reordered['cases'][1]=reordered['cases'][1],reordered['cases'][0];inputs.append(('case order drift refused',reordered,False))
guard_rows=[]
for label,value_input,expected in inputs:
    error=None
    try:exec(guard_code,{'W':A,'read':lambda p:value_input,'binding':binding,'boundary':boundary,'CASES':CASES})
    except AssertionError as exc:error=str(exc)
    ck('actual new prelease guard '+label,(error is None)==expected,error)
    guard_rows.append({'name':label,'expectedAccepted':expected,'actualAccepted':error is None,'error':error,'passed':True,'realLedgerReadOrWrite':False})
new_main.body[i:i+2]=[]
ck('only these two launcher AST statements changed',ast.dump(new_tree,include_attributes=False)==ast.dump(old_tree,include_attributes=False))
old_life=next(n for n in old_main.body if isinstance(n,ast.Try));new_life=next(n for n in new_main.body if isinstance(n,ast.Try))
ck('custody lifecycle AST raw unchanged',ast.dump(old_life,include_attributes=False)==ast.dump(new_life,include_attributes=False))
lifecycle=read(A/'lifecycle-controls-01/LIFECYCLE_CONTROL.json')
ck('eleven author inert lifecycle controls bound',lifecycle['sourceSha256']==h(A/'root_dispatch_proposal.py') and lifecycle['passed']==11 and all(x['safetyGuardPass'] and x['nativeProcessesExecuted']==x['realLedgerWrites']==0 for x in lifecycle['rows']))
for key in ['driver','actions','fixture','binding','launcher','caseManifest','command','queue']:
    exact(report[key])
for key in ['connected','lifecycle','actualReadOnlyPreflight','selection']:exact(report['controls'][key])
ck('native output and dispatch fresh',not Path(queue['freshOutput']).exists() and not Path(queue['freshDispatch']).exists())
node=rootcmd['toolIdentities']['Node22']['path']
command('connected-exact-successor-source',[node,OUT/'connected_replay.cjs'])
controls=read(OUT/'CONNECTED_REPLAY.json')
ck('fresh 23 connected controls no native',controls['passed']==23 and all(x['status']=='PASS' for x in controls['records']) and not any(controls[x] for x in ['nativeExecuted','browserLaunched','serverStarted','realLedgerWrites']))
ck('final source predecessor and subject seals unchanged',h(A/'SEAL.json')==PIN and h(P/'SEAL.json')=='b959e853461371845d1bc67bc0bd6852104cf2114784437c9c18e7a5db2a6efa' and h(Q/'SEAL.json')=='9ce4b2f3b5ca83bf38d056d28d06e3f0c5eb38a0698d010c1f683c05d09647c4')
write(OUT/'SELECTION_REPLAY.json',{'source':ref(A/'root_dispatch_proposal.py'),'actualStatementLines':[nodes[0].lineno,nodes[1].lineno],'records':guard_rows,'passed':7,'nativeExecuted':False,'realLedgerReadOrWrite':False})
write(OUT/'VERIFICATION.json',{'schema':'r0010-successor-independent-source-verification/1','atUtc':now(),'checks':checks,'commands':commands,'authorSeal':ref(A/'SEAL.json'),'sourceHead':HEAD,'runtimeSha256':RUNTIME,'runtimeFiles':135,'sourceMembersVerified':85,'predecessorSourceMembersVerified':229,'guardControls':ref(OUT/'SELECTION_REPLAY.json'),'connectedControls':ref(OUT/'CONNECTED_REPLAY.json'),'unchangedLifecycleRetained':ref(A/'lifecycle-controls-01/LIFECYCLE_CONTROL.json'),'allPassed':True,'actualNative':'NOT_RUN','canonicalWrites':False})
print(json.dumps({'allPassed':True,'checks':len(checks),'guardControls':7,'connectedControls':23,'unchangedInertLifecycleControls':11,'nativeExecuted':False}))
