"""Existing root preference launcher rebound to the authorized delivered ten-case batch."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,os,subprocess,sys
W=Path(__file__).resolve().parent;R=W.parents[1];A=R/'workers/preferences_native';Q=R/'workers/preferences_actual_review_r1'
DRIVER=W/'native/residual-location-native.py';L=R/'ACTIVE_LEDGER.json';CASES=['fresh-2-f', 'fresh-2-c', 'fresh-4-f', 'fresh-4-c', 'generic-local', 'saved-native-reload', 'prefer-local-fresh', 'prefer-local-saved', 'mutant-omitMethod', 'mutant-omitUnits']
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def encoded(v):return (json.dumps(v,indent=2)+'\n').encode()
def save(p,v):p.write_bytes(encoded(v))
def verify(root,pin):
 root=root.resolve();assert sha(root/'SEAL.json')==pin,'sealed packet pin differs'
 seal=read(root/'SEAL.json');assert sha(root/'MANIFEST.json')==seal['manifestSha256'],'manifest differs'
 rows=read(root/'MANIFEST.json')['files']
 if isinstance(rows,dict):rows=[{'path':k,**({'sha256':v} if isinstance(v,str) else v)} for k,v in rows.items()]
 seen=set()
 for row in rows:
  rel=row['path'];assert rel and '\\' not in rel and ':' not in rel and all(c not in ('','..','.') for c in rel.split('/')),'unsafe manifest member'
  p=(root/rel).resolve();assert p.is_relative_to(root) and rel not in seen,'manifest escaped or repeated';seen.add(rel)
  assert sha(p)==row['sha256'],'packet member differs: '+rel
  if 'bytes' in row:assert p.stat().st_size==row['bytes'],'packet member length differs'
 return seal,seen

def fresh_paths(out,dispatch):
 out=out.resolve();dispatch=dispatch.resolve();base=(R/'evidence/R0010').resolve()
 assert out.is_relative_to(base) and dispatch.is_relative_to(base) and out!=base and dispatch!=base,'outputs must be root-owned R0010 children'
 assert out!=dispatch and not out.is_relative_to(dispatch) and not dispatch.is_relative_to(out),'separate retained dispatch and consumer outputs required'
 assert not out.exists() and not dispatch.exists(),'fresh output/dispatch required; preserve prior attempts'
 return out,dispatch

def free_ledger(raw,expected_sha):
 assert hashlib.sha256(raw).hexdigest()==expected_sha,'root FREE-ledger CAS pin differs'
 ledger=json.loads(raw);assert ledger['schema']=='salah-active-execution/1' and Path(ledger['runRoot']).resolve()==R.resolve(),'wrong root ledger'
 lease=ledger['resourceLeases']['heavy-browser'];assert lease['status']=='FREE' and lease['holder'] is None and lease['capacity']==1,'capacity-one FREE lease required'
 return ledger

def cas_replace(ledger_path,expected_bytes,value,staging):
 assert not staging.exists(),'fresh CAS staging required'
 staging.write_bytes(encoded(value))
 assert ledger_path.read_bytes()==expected_bytes,'root ledger changed before CAS write'
 os.replace(staging,ledger_path)
 assert ledger_path.read_bytes()==encoded(value),'ledger post-write bytes differ'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--execute-authorized-by-root',action='store_true',required=True)
 p.add_argument('--expected-author-seal',required=True);p.add_argument('--review-root',type=Path,required=True);p.add_argument('--expected-review-seal',required=True)
 p.add_argument('--expected-free-ledger-sha256',required=True);p.add_argument('--lease-id',required=True)
 p.add_argument('--out',type=Path,required=True);p.add_argument('--dispatch',type=Path,required=True)
 x=p.parse_args();assert x.execute_authorized_by_root
 verify(W,x.expected_author_seal)
 _,members=verify(x.review_root,x.expected_review_seal);assert 'ADMISSION.json' in members,'independent sealed ADMISSION required'
 admission=read(x.review_root/'ADMISSION.json');assert admission['schema']=='r0010-delivered-native-source-admission/1' and admission['authorSealSha256']==x.expected_author_seal and admission['sourceAdmission']=='PASS' and admission['nativeApplicability'] is True and admission['actualNative']=='NOT_RUN' and admission['nodeComplete'] is False,'independent source admission insufficient'
 boundary=read(W/'BOUNDARY.json');grant_ref=boundary['ownerAuthority'];assert sha(Path(grant_ref['path']))==grant_ref['sha256']=='dfbb98a6f3812d299b77315c5a62c3b24c19691b7b50a851003596a9a4c4c48f' and Path(grant_ref['path']).stat().st_size==grant_ref['bytes'],'exact owner delegation changed'
 grant=read(Path(grant_ref['path']));assert grant['R0010']['worker']=='/root/r0010_isolated_release_path_r1' and grant['R0010']['maximumOriginalContexts']==len(CASES)==10 and grant['R0010']['deliveredHead']==boundary['deliveredMain']=='88926dd12d22a6a8c1cd369d4823750778fccb48','whole original closure grant differs'
 assert admission['reviewer']=='/root/r0010_isolated_release_review_r1' and admission['scope']==CASES and admission['deliveredHead']==boundary['deliveredMain'],'exact delivered source review scope differs'
 verify(A,'080bdee8790d7f9b2363b2eb8bcdb09001244dac760cbe3c31cce4523ea2445d');verify(Q,'bafc77f648cf67a61a68b0314222e0a350df8e9bd92397f83d6143bda203e8d9')
 assert sha(Q/'REPORT.json')=='71e437c51786015a81462502f7531c5c10f47a437bb99e9793d64b25e1f3b88b'
 prepared=read(W/'ROOT_COMMAND.json');out,dispatch=fresh_paths(x.out,x.dispatch)
 cmd=[x.lease_id if a=='ROOT_ACTUAL_LEASE_ID_REQUIRED' else str(out) if a=='ROOT_FRESH_CONSUMER_OUT_REQUIRED' else a for a in prepared['argvTemplate']]
 assert [cmd[i+1] for i,v in enumerate(cmd) if v=='--only']==CASES,'only the original ten delivered-source contexts'
 for row in list(prepared['toolIdentities'].values())+[prepared['driverIdentity'],prepared['actionsIdentity'],prepared['fixtureIdentity'],prepared['bindingIdentity']]:
  assert sha(Path(row['path']))==row['sha256'] and Path(row['path']).stat().st_size==row['bytes'],'driver/tool/fixture drift'
 binding=read(W/'native/source-binding.json');candidate=Path(binding['candidateRoot']);assert candidate==Path(cmd[cmd.index('--source-root')+1])
 selection=read(W/'CASE_SELECTION.json')
 assert selection['sourceRoot']==binding['candidateRoot'] and selection['runtimeSha256']==binding['runtimeSha256'] and selection['sourceRef']==binding['sourceRef']==boundary['deliveredMain'] and selection['group']=='r0010' and [c['name'] for c in selection['cases']]==CASES,'case selection differs from delivered executable binding'
 for rel,row in binding['runtimeRows'].items():assert sha(candidate/rel)==row['sha256'] and (candidate/rel).stat().st_size==row['bytes'],'runtime drift: '+rel
 raw=L.read_bytes();ledger=free_ledger(raw,x.expected_free_ledger_sha256);assert x.lease_id and x.lease_id!=ledger['resourceLeases']['heavy-browser'].get('leaseId'),'fresh root-issued lease identity required'
 fresh_paths(out,dispatch);dispatch.mkdir(parents=True,exist_ok=False);(dispatch/'ACTIVE_LEDGER.before.json').write_bytes(raw)
 lease=ledger['resourceLeases']['heavy-browser'];lease.update(holder='root',status='ACTIVE',capacity=1,leaseId=x.lease_id,command=str(DRIVER),scope='R0010 delivered main88926dd original A02-A05 ten-case matrix; original healthy zones plus two UTC omission controls; no Riyadh-control replay, product repair or node closure.',currentCase='R0010-delivered-stop-on-first-FAIL',sessionId=None,startedAtUtc=now(),completedCases=0,totalCases=10,delegatedOperator='/root/r0010_isolated_release_path_r1',delegation=boundary['ownerAuthority'])
 ledger['updatedAtUtc']=now()
 receipt={'schema':'root-r0010-delivered-native-dispatch/1','status':'RUNNING','atUtc':now(),'command':cmd,'cwd':str(W),'leaseId':x.lease_id,'freeLedgerSha256':x.expected_free_ledger_sha256,'activeLedgerSha256':hashlib.sha256(encoded(ledger)).hexdigest(),'authorSealSha256':x.expected_author_seal,'independentSourceReviewSealSha256':x.expected_review_seal,'sourceRuntime':binding['runtimeSha256'],'output':str(out),'scope':CASES,'originalRetained':{'positivePASS':8,'semanticCAUGHT':2,'negativeContext':'Asia/Riyadh'},'automaticRetries':0,'nodeCredit':False}
 cas_replace(L,raw,ledger,dispatch/'ACTIVE_LEDGER.acquire-CAS.json')
 launchAttempted=False;childReturned=False;returnedCode=None
 try:
  (dispatch/'ACTIVE_LEDGER.active.json').write_bytes(L.read_bytes())
  save(dispatch/'dispatch.json',receipt)
  assert sha(L)==receipt['activeLedgerSha256'],'root active ledger changed before driver launch'
  assert not out.exists(),'consumer output ceased to be fresh'
  with (dispatch/'stdout.log').open('xb') as stdout,(dispatch/'stderr.log').open('xb') as stderr:
   launchAttempted=True
   actual=subprocess.run(cmd,cwd=W,stdout=stdout,stderr=stderr)
   returnedCode=actual.returncode
   assert type(returnedCode) is int,'child completion requires an integer returned exit receipt'
   childReturned=True
  receipt.update(status='RETURNED_ACTUAL_DELIVERED_PREFERENCES_REVIEW_REQUIRED',exitCode=returnedCode)
 except BaseException as error:
  receipt.update(status='ROOT_ATTEMPT_INTERRUPTED_OR_FAILED_RETAINED',wrapperError={'type':type(error).__name__,'message':str(error)})
  raise
 finally:
  completion='CHILD_RETURNED_KNOWN_EXIT' if childReturned else 'UNKNOWN_PENDING_ROOT_RECONCILIATION' if launchAttempted else 'VERIFIED_NO_CHILD_LAUNCH_ATTEMPT'
  releasePermitted=childReturned or not launchAttempted
  receipt.update(processChainCompletion=completion,launchAttempted=launchAttempted,childReturned=childReturned,leaseReleasePermitted=releasePermitted)
  if childReturned:receipt['exitCode']=returnedCode
  if not releasePermitted:
   receipt.update(status='ROOT_PROCESS_CHAIN_COMPLETION_UNKNOWN_PENDING_RECONCILIATION',exitCode=None,outputAccounting='PARTIAL_SNAPSHOT_COMPLETION_UNKNOWN')
   pendingRaw=L.read_bytes();pendingLedger=json.loads(pendingRaw);held=pendingLedger['resourceLeases']['heavy-browser']
   assert held['holder']=='root' and held['status']=='ACTIVE' and held['capacity']==1 and held['leaseId']==x.lease_id and Path(held['command']).resolve()==DRIVER.resolve(),'retain unresolved lease drift; no blind pending-state write'
   held.update(currentCase='R0010-delivered-unknown-completion-pending-root-reconciliation',pendingReconciliation={'status':'UNKNOWN_PROCESS_CHAIN_COMPLETION','leaseId':x.lease_id,'command':cmd,'output':str(out),'dispatch':str(dispatch/'dispatch.json'),'automaticRetry':False,'releaseCondition':'Root verifies process-chain termination and retained output identity before a separate guarded release; this wrapper neither retries nor frees unknown completion.'})
   pendingLedger['updatedAtUtc']=now()
   cas_replace(L,pendingRaw,pendingLedger,dispatch/'ACTIVE_LEDGER.pending-CAS.json')
   (dispatch/'ACTIVE_LEDGER.pending.json').write_bytes(L.read_bytes())
  receipt.update(finishedAtUtc=now(),files=[{'path':str(p.relative_to(out)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file()] if out.exists() else [])
  save(dispatch/'dispatch.json',receipt)
  if releasePermitted:
   releaseRaw=L.read_bytes();releaseLedger=json.loads(releaseRaw);held=releaseLedger['resourceLeases']['heavy-browser']
   assert held['holder']=='root' and held['status']=='ACTIVE' and held['capacity']==1 and held['leaseId']==x.lease_id and Path(held['command']).resolve()==DRIVER.resolve(),'retain unresolved lease drift; no blind release'
   held.update(holder=None,status='FREE',currentCase=None,sessionId=None,finishedAtUtc=now(),lastResult=str(dispatch/'dispatch.json'));releaseLedger['updatedAtUtc']=now()
   cas_replace(L,releaseRaw,releaseLedger,dispatch/'ACTIVE_LEDGER.release-CAS.json');(dispatch/'ACTIVE_LEDGER.after.json').write_bytes(L.read_bytes())
  print(json.dumps({'status':receipt['status'],'exitCode':receipt.get('exitCode'),'actualFiles':len(receipt['files']),'dispatchSha256':sha(dispatch/'dispatch.json'),'processChainCompletion':completion,'leaseReleasePermitted':releasePermitted,'nodeCredit':False}),flush=True)
 return receipt.get('exitCode',1)
if __name__=='__main__':raise SystemExit(main())