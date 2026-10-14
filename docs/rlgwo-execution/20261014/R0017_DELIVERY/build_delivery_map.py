"""Join retained R0017 local qualification with fresh actual-public delivery evidence."""
import hashlib,json,pathlib,datetime
B=pathlib.Path(__file__).resolve().parent
def read(name):return json.loads((B/name).read_text(encoding='utf-8-sig'))
def ref(name):
 data=(B/name).read_bytes()
 return {'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
a=read('acceptance.json'); runs=[]
for name in ['chromium-default-01','chromium-reduce-01','firefox-default-01','firefox-reduce-01']:
 p='public/'+name+'/result.json';r=read(p);s=r['smoke'];required=s['required']
 assert r['status']=='PASS' and all(r['checks'].values())
 assert required['executed']==required['total']==30 and s['pass']==141 and s['fail']==s['skip']==0 and not required['missing']
 assert [[c['name'],c['expected']] for c in required['cases']]==r['denominator']
 assert all(c['state']=='executed' and c['assertions']==c['expected'] for c in required['cases'])
 attempts=s['fixture']['attempts'];moon=[]
 assert len(attempts)==25 and len({x['documentId'] for x in attempts})==25
 for attempt in attempts:
  f=attempt['fixture']
  assert attempt['result']=='ready' and f['state']=='ready' and not f['error']
  assert f['sourceSha256']==r['source']['runtime']['files']['index.html']['sha256']
  assert f['attempt']==attempt['attempt'] and f['documentId']==attempt['documentId'] and f['run']==s['fixture']['run']
  assert any('/timings/07-09-2026?' in x['url'] and x['attempt']==attempt['attempt'] and x['jsonReads']>0 and x['result']=='json-consumed' for x in f['ledger'])
  if 'calendarView' in attempt:
   view=attempt['calendarView'];o=view['readyObservation']
   assert view['budgetMs']==8000 and o['elapsedMs']<8000 and o['sameOwner'] and o['current'] and o['composed'] and o['surfaceAvailable']
   assert o['acceptedIdentity']==o['surfaceIdentity'] and o['contentPublished'] and o['nonopaqueVisiblePixels']==0
   moon.append({'attempt':attempt['attempt'],'elapsedMs':o['elapsedMs'],'acceptedIdentity':o['acceptedIdentity']})
 assert len(moon)==3 and not r['pageErrors']
 assert not any(x['url'].startswith('http://127.0.0.1') for x in r['requests'])
 runs.append({'name':name,'result':ref(p),'pixels':ref('public/'+name+'/summary.png'),'engine':r['browser']['family'],
  'version':r['browser']['version'],'preference':r['preference'],'storageSeed':r['storage'],'status':'PASS',
  'requiredExecuted':30,'assertions':141,'failed':0,'missing':0,'skipped':0,'freshOwnedDocuments':25,'currentDayJsonConsumedAttempts':25,
  'moon':moon,'outerBytesPreserved':True,'outerGetterAccesses':0,'nativePreferenceVerified':True,
  'requestFailureCount':len(r['requestFailures']),'requestFailureCodes':sorted({x['failure'] for x in r['requestFailures']}),
  'requestFailureDisposition':'Raw aborted requests retained; precise cancellation causes not individually attributed. No page error or failed/missing/skipped required callback. No all-network-success claim.'})
normal=read('normal-root-01/result.json');assert normal['status']=='PASS'
assert len(normal['results'])==2 and all(r['status']=='PASS' and all(r['checks'].values()) for r in normal['results'])
payload=read('deployed-pages-payload.json');public=read('public-source-readback.json');deployment=read('deployment.json');merge=read('merge.json')
assert payload['status']==public['status']==deployment['status']==merge['status']=='PASS'
assert public['runtimeFiles']==135 and payload['regularFilePayloadBytes']==897967831
summary={'schema':'r0017-fresh-public-delivery/v1','status':'PUBLIC_CONSUMERS_QUALIFIED_PENDING_INDEPENDENT_FINAL_ACCEPTANCE',
 'merge':merge['merge'],'head':merge['head'],'base':merge['reviewedBase'],'tree':merge['tree'],'runtimeSha256':public['runtimeSha256'],
 'deployment':ref('deployment.json'),'payload':ref('deployed-pages-payload.json'),'publicIdentities':ref('public-source-readback.json'),
 'regularFileBytes':payload['regularFilePayloadBytes'],'protectedFiles':286,'publicRuntimeFiles':135,'publicRoutes':len(public['files']),
 'runs':runs,'maximumPublicMoonReadyMs':max(m['elapsedMs'] for r in runs for m in r['moon']),
 'ordinaryPublicRoot':{'result':ref('normal-root-01/result.json'),'engines':['chromium','firefox'],'status':'PASS','viewport':[375,800],'dpr':2,
  'consumer':'Actual root index with unchanged controlled ingress spans; no smoke weather observer. Current-day/tomorrow JSON consumed once each; Dhuhr, next Asr15:30, leftMin180; stable325x530card/footer and exact outer bytes.',
  'pixels':[ref('normal-root-01/'+name+'.png') for name in ['chromium','firefox']],
  'pixelAssessment':'Primary viewed both original captures: Dhuhr/15:30/3h0m-left readable, all six prayer rows and footer visible. Controlled fixed clock/providers and font-suppression limitations remain; no whole-sky/appearance/M0 claim.'},
 'reusedLocalQualification':'Four accepted local30/141 runs, six hostile outcomes,35contract+21transport,60Moon components, native storage/motion/identity mutants, V1/build preservation; exact135runtime and unchanged semantic owners justify reuse. No replay for membership change.',
 'retainedFailures':'Original326-member ZIP and all original/intermediate failures including same-runtime29/30 remain unchanged. These four fresh public executions are separate first attempts, not relabelled failures.',
 'limits':['WASM linear-memory sum653262848 vs326631424 bytes; excludes other browser memory; low-memory devices unqualified.',
  'Same-runtime historical29/30 readiness failure remains unexplained and owner-accepted; later passes do not retrospectively cure it.',
  'Windows headless Chromium148.0.7778.96/Firefox150.0.2 on recorded16-logical-CPU host, isolated contexts; not universal reliability.',
  'Original4s/8s/3s gates unchanged. R0017 smoke is not R0021/issue33 first-complete presentation or normal-liveM0.',
  'Network abort entries retained with bounded disposition; no missing/failed/skipped callback in any fresh public run.']}
(B/'public-delivery.json').write_text(json.dumps(summary,indent=2)+'\n')
a['disposition']='PUBLIC_DELIVERY_QUALIFIED_PENDING_INDEPENDENT_CERTIFICATE_ACCEPTANCE'
a['currentDelivery'].update(status=a['disposition'],summary=ref('public-delivery.json'))
a['delivery']=summary
findings={
 '17-01':'Exact admitted head/base/normal merge/tree and successful actual deployment bound. All135 public runtime identities equal qualified5ff; all286 protected actual-output files preserved.',
 '17-03':'Fresh actual deployed Chromium/Firefox in each native preference: all original30 callbacks and141assertions executed, zero failed/missing/skipped. All12 required Moon readiness observations within original8s; maximum7358ms.',
 '17-07':'Each of100 fresh owned fixture documents JSON-consumes matching current-day response; actual ordinary public root in both engines independently shows Dhuhr, Asr15:30,180minutes with matching today/tomorrow JSON and exact source.',
 '17-09':'Fresh both-browser/both-native-preference smoke runs retain explicit reduced/full controls, override and original matchMedia restoration. Accepted thrown/timeout and semantic mutation controls reused on unchanged owner bytes.',
 '17-10':'Existing accurate root README unchanged and publicly byte-matched. Actual smoke/fixture/config/docs and supported delivery routes verified; exclusion resolver preserves immutable historical evidence access.',
 '17-11':'Same independent Astra Max reviewer admitted exact packaging successor before normal merge and independently verified merge/deployment boundary. Completed public raw evidence is ready; final independent delivery/certificate acceptance and intentional issue closure remain pending.'}
for row in a['matrix']:
 row['priorLocalFinding']=row['finding']
 if row['id'] in findings:row['finding']=findings[row['id']]
 row['currentDisposition']='QUALIFIED_REUSED_WITH_CURRENT_IDENTITY' if row['id'] in ['17-02','17-04','17-05','17-06','17-08'] else 'QUALIFIED_PUBLIC' if row['id']!='17-11' else 'DELIVERY_QUALIFIED_CERTIFICATE_SEQUENCE_PENDING'
for row in a['residualMatrix']:
 row['finalDeliveryDisposition']='QUALIFIED_PUBLIC_AND_REUSED_CURRENT_CONTROLS' if row.get('id')!='R0017-A06' else 'INDEPENDENT_FINAL_CERTIFICATE_PENDING'
a['nextAction']='Independent complete delivery acceptance; publish CLOSE-R0017 and read back it and evidence; intentionally close issue23 ascompleted and independently verify final state.'
(B/'acceptance.json').write_text(json.dumps(a,indent=2)+'\n')
print(json.dumps({'status':summary['status'],'publicRuns':4,'each':'30/141','maximumMoonMs':summary['maximumPublicMoonReadyMs'],'ordinaryRoot':'PASS both engines'}))
