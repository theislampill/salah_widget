"""Bounded real transport faults using the existing native startup harness."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=Path(r'${REPO_ROOT}')
H=O/'recovery-tools-r121-r122';assert not H.exists()
prior=json.loads((O/'native/chromium-arc-samples-r105/EXECUTION.json').read_bytes())['harnessInputSha256']
observer=r'''(()=>{
 const d=window.__terminalFault={kind:FAULT_KIND,timers:[],workers:[],events:[],corrupt:FAULT_KIND==='file-atob',injections:0};
 const event=(kind,extra={})=>d.events.push({kind,at:performance.now(),absolute:performance.timeOrigin+performance.now(),...extra});
 const st=window.setTimeout,ct=window.clearTimeout;
 window.setTimeout=function(fn,ms,...args){
  if((ms!==120000&&ms!==240000)||typeof fn!=='function')return Reflect.apply(st,this,[fn,ms,...args]);
  const rec={delay:ms,before:performance.now(),timeOrigin:performance.timeOrigin,stack:String(new Error().stack)};
  const id=Reflect.apply(st,this,[function(...a){rec.firedAt=performance.now();return Reflect.apply(fn,this,a);},ms,...args]);
  rec.id=id;rec.after=performance.now();d.timers.push(rec);return id;
 };
 window.clearTimeout=function(id){const rec=d.timers.find(t=>t.id===id);if(rec)rec.clearedAt=performance.now();return Reflect.apply(ct,this,[id]);};
 const W=window.Worker;let serial=0;
 window.Worker=class extends W{
  constructor(...args){super(...args);this.__terminalId=++serial;const rec={id:this.__terminalId,createdAt:performance.now(),terminatedAt:null};this.__terminalRecord=rec;d.workers.push(rec);
   this.addEventListener('message',e=>{const m=e.data;if(['boot-error','ready','preview','frame','error'].includes(m?.kind))event('worker-message',{worker:this.__terminalId,messageKind:m.kind,error:m.error??null});});
  }
  postMessage(m,...args){
   if(m?.kind==='boot')event('worker-boot',{worker:this.__terminalId,offline:m.offline===true});
   if(m?.kind==='asset-chunk'&&m.index===0&&String(m.name).includes('dem')){
    const data={worker:this.__terminalId,name:m.name,index:m.index,last:m.last,type:typeof m.data,originalLength:m.data.length,originalPrefix:m.data.slice(0,32),originalSuffix:m.data.slice(-32)};
    if(d.corrupt){d.corrupt=false;d.injections++;event('malformed-base64-injected',data);m={...m,data:'%INVALID-BASE64%'};}
    else event('original-base64-delivered',data);
   }
   return super.postMessage(m,...args);
  }
  terminate(){this.__terminalRecord.terminatedAt=performance.now();event('worker-terminate',{worker:this.__terminalId});return super.terminate();}
 };
})();'''
body_marker="    elif self.path=='/favicon.ico':self.send(b'',status=204)\n"
body=body_marker+'''    elif os.environ.get('SALAH_TERMINAL_FAULT')=='delayed-body' and not server_recovered and urlsplit(self.path).path=='/salah_widget/moon/assets/dem.bin.gz':
     target=a.root/'moon/assets/dem.bin.gz';length=target.stat().st_size
     with target.open('rb') as f:prefix=f.read(4096)
     self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(length));self.end_headers()
     self.wfile.write(prefix);self.wfile.flush()
     request={'kind':'controlled-open-body','url':self.path,'httpStatus':200,'declaredBytes':length,'sentBytes':len(prefix),'prefixSha256':hashlib.sha256(prefix).hexdigest(),'openedAbsolute':time.time()*1000};requests.append(request)
     while not server_recovered:time.sleep(.1)
     request['releasedAbsolute']=time.time()*1000;self.close_connection=True
     try:self.connection.shutdown(1)
     except OSError:pass
'''
old_recovery='''   recovery=None
   if a.recover_at is not None:
    await asyncio.sleep(max(0,a.recover_at-(time.monotonic()-start)));server_recovered=True
    recovery={'atMs':(time.monotonic()-start)*1000,'retry':await frame.evaluate('async()=>({moon:window.SalahMoonRuntime?.retry(),sky:await window.SalahRealSkyAssets?.retry()})')}
'''
new_recovery='''   recovery=None;fault_record={'kind':os.environ['SALAH_TERMINAL_FAULT'],'observations':[],'status':'WAITING_FOR_ACTUAL_FAILURE'}
   probe=initial
   while time.monotonic()-start<a.duration:
    moon=probe.get('moon') or {}
    fault_record['observations'].append({'at':probe.get('at'),'status':moon.get('status'),'source':moon.get('visibleSource'),'current':moon.get('current'),'pending':moon.get('pending'),'workerAlive':moon.get('workerAlive'),'errors':moon.get('errors')})
    if moon.get('status')=='unavailable':break
    await asyncio.sleep(1);probe=await frame.evaluate(FINAL)
   fault_record['failedState']=probe;fault_record['sourceObserverBeforeRecovery']=await frame.evaluate('window.__terminalFault')
   await page.screenshot(path=str(a.out/f'{mode}-failed-before-recovery.png'),timeout=30000)
   moon=probe.get('moon') or {};expected=('Moon asset startup deadline exceeded' if fault_record['kind']=='delayed-body' else None)
   actual_errors=moon.get('errors') or []
   fault_record['expectedFailureObserved']=moon.get('status')=='unavailable' and (expected in actual_errors if expected else any('atob' in e.lower() or 'base64' in e.lower() or 'invalid character' in e.lower() for e in actual_errors))
   fault_record['currentInitialAndCleanup']=moon.get('visibleSource')=='initial-v5' and moon.get('current') is True and moon.get('workerAlive') is False and not moon.get('pending')
   report['fault']=fault_record;save()
   if fault_record['expectedFailureObserved'] and fault_record['currentInitialAndCleanup']:
    if probe.get('settingsButton'):
     await frame.locator('.buckle').click(timeout=10000)
     await page.screenshot(path=str(a.out/f'{mode}-failed-settings.png'),timeout=30000)
     await frame.locator('#setClose').click(timeout=10000)
     fault_record['settingsRoute']='ACTUAL_BUCKLE_OPEN_CLOSE'
    else:fault_record['settingsRoute']='NOT_ENABLED_THIS_ENTRY'
    fault_record['afterSettings']=await frame.evaluate(FINAL)
    fault_record['beforeRestoreElapsedMs']=(time.monotonic()-start)*1000
    server_recovered=True
    await frame.evaluate('()=>{window.__terminalFault.corrupt=false;}')
    recovery={'atMs':(time.monotonic()-start)*1000,'retry':await frame.evaluate('async()=>({moon:window.SalahMoonRuntime?.retry(),sky:await window.SalahRealSkyAssets?.retry()})')}
    fault_record['status']='ONE_EXPLICIT_RETRY_STARTED'
   else:fault_record['status']='INCOMPLETE_UNEXPECTED_FAILURE_OR_OBSERVER_CEILING'
   report['fault']=fault_record;save()
'''
old_loop='''   final=initial
   while time.monotonic()-start<a.duration:
    if (final.get('moon') or {}).get('visibleSource')=='refined-terrain' and (final.get('sky') or {}).get('status')=='ready':break
    await asyncio.sleep(1)
    final=await frame.evaluate(FINAL)
'''
new_loop='''   final=await frame.evaluate(FINAL)
   while recovery and time.monotonic()-start<a.duration:
    moon=final.get('moon') or {}
    if moon.get('status')=='unavailable':fault_record['status']='UNEXPECTED_RETRY_FAILURE';break
    if moon.get('status')=='ready' and moon.get('visibleSource')=='refined-terrain' and moon.get('current') and (final.get('sky') or {}).get('status')=='ready':
     fault_record['status']='CURRENT_FINAL_RETURNED_FOR_REVIEW';break
    await asyncio.sleep(1);final=await frame.evaluate(FINAL)
   if recovery and fault_record['status']=='ONE_EXPLICIT_RETRY_STARTED':fault_record['status']='INCOMPLETE_OBSERVER_CEILING'
   fault_record['sourceObserverAfterRecovery']=await frame.evaluate('window.__terminalFault')
   fault_record['finalState']=final;fault_record['totalElapsedMs']=(time.monotonic()-start)*1000
'''
entries={}
for rel,pin in prior.items():
 data=(R/rel).read_bytes();assert hashlib.sha256(data).hexdigest()==pin
 if rel=='tools/cp9/celestial_startup_check.py':
  s=data.decode()
  for old,new in [(body_marker,body),(old_recovery,new_recovery),(old_loop,new_loop)]:
   assert s.count(old)==1,old[:70];s=s.replace(old,new)
  marker='  if a.trace:await ctx.add_init_script(TRACE)\n';assert s.count(marker)==1
  s=s.replace(marker,'  await ctx.add_init_script('+repr(observer)+'.replace("FAULT_KIND",json.dumps(os.environ["SALAH_TERMINAL_FAULT"])))\n'+marker)
  begin=s.index('   nav=asyncio.create_task(');end=s.index('  if a.capture_trace:await ctx.tracing.stop',begin)
  original=s[begin:end]
  bounded='   try:\n    async with asyncio.timeout(max(0,a.duration-(time.monotonic()-start))):\n'+''.join('  '+line if line.strip() else line for line in original.splitlines(keepends=True))
  bounded+='   except TimeoutError:\n    server_recovered=True;report["observerCeiling"]={"status":"INCOMPLETE_ABSOLUTE_CEILING","elapsedMs":(time.monotonic()-start)*1000,"navigationAbsolute":absolute};save()\n'
  s=s[:begin]+bounded+s[end:]
  data=s.encode();ast.parse(s)
 target=H/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 entries[rel]={'beforeSha256':pin,'afterSha256':hashlib.sha256(data).hexdigest()}
record={'schema':'r0021-native-recovery-fixtures/v1','changes':entries,'runtimeUnmodified':True,
 'delayedBody':'HTTP200 originallength/prefix held until actual deadline failure observed; original primary worker termination before restore. Observe timer installation/fire using a transparent test-only setTimeout wrapper; product120000/240000 timers unchanged. One explicitretry, absolute540s from firstnav.',
 'fileAtob':'ActualWorker.postMessage receives exactly one copied valid asset-chunk envelope with malformeddata after host envelope validation. Original scripts/cache never modified. Observe native worker boot-error/termination, then one restored retry. No mocked decode Promise.',
 'limits':'Onecase/engine/fault. No S1/performance/continuous-display claim. Report source clocks/worker records and failed/settings/final PNGs; no new recorder.'}
(O/'intake/recovery-r121-r122-preparation.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
print(json.dumps({'harness':entries['tools/cp9/celestial_startup_check.py'],'preparationSha256':hashlib.sha256((O/'intake/recovery-r121-r122-preparation.json').read_bytes()).hexdigest()}))
