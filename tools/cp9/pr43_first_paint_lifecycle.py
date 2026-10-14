"""Actual unchanged generated-entry controls for the pre-core CSS scene owner.

The age case waits 35 real seconds with an ordinary-rate fixture wall clock.
Visibility events are explicit consumer-boundary controls, not OS tab/BFCache
qualification. These diagnostic waits are never ordinary startup measurements.
The separate compact-head case observes delivery dependency and release recovery;
it requires no literal zero-byte readiness and supplies no ordinary S1 timing.
"""
import argparse, asyncio, hashlib, http.server, json, os, sys, threading, time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.async_api import async_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_runtime import launch_browser, browser_identity
from runtime_identity import runtime_identity
from pr43_entry_stream import SNAPSHOT, fixture, SETTINGS, ROOT_KEY
from first_paint_control import entry_boundaries,validate_binding,original_case_checks,recovery_checks,lifecycle_audit,compact_head_checks

def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

EXTRA="""() => {
 const c=document.querySelector('.c'),first=window.SalahFirstPaint,style=document.getElementById('native-first-paint');
 return {at:performance.now(),timeOrigin:performance.timeOrigin,wallUtc:Date.now(),readyState:document.readyState,
  mainDeclared:typeof boot==='function',hostPresent:!!window.SalahMoonHost,previewPresent:!!window.SalahSkyPreview,
  headAgeMs:first?.snapshot?Date.now()-first.snapshot.utcMs:null,headStyle:!!style,styleText:style?.textContent??null,
  background:c?getComputedStyle(c).backgroundImage:null,cardVisible:c?getComputedStyle(c).visibility:null,
  styleState:first?.state??null,firstScene:first?.snapshot??null,headError:first?.error??null,
  headLifecycle:window.SalahFirstPaintLifecycle?.state??null,headValuePresent:first?.value!=null,headMoonPresent:first?.moon!=null,
  startupTiming:window.SalahStartupTiming?.snapshot?.()??null,
  cardPresent:!!c,settingsPresent:!!document.querySelector('.buckle.interactive'),prayerRowCount:document.querySelectorAll('.times .p').length,
  firstPaintProducerPresent:typeof window.SalahPrepareFirstPaint==='function',initialReceiverPresent:!!window.SalahMoonInitial,moonRuntimePresent:!!window.SalahMoonRuntime,
  moon:window.SalahMoonRuntime?.state??null,hidden:document.hidden,visibilityState:document.visibilityState,
  requests:window.__entryFixture.requests};
}"""

# A held head has no guaranteed animation frame or producer readiness. Observe
# the parser's received script text; never complete or execute it in this driver.
COMPACT_PREFIX_WAIT="""expected => {const script=document.getElementById('moon-initial-code');return document.readyState==='loading'&&!!script&&script.textContent===expected;}"""
COMPACT_PREFIX_READ="""() => {const script=document.getElementById('moon-initial-code');return {present:!!script,text:script?.textContent??null};}"""

async def run(a):
 a.out.mkdir(parents=True,exist_ok=False)
 identity=runtime_identity(a.root);entry=(a.root/'index.html').read_bytes()
 admission={'schema':'f1-actual-candidate-admission/1','stage':'pre-browser-candidate-admission','expectedRuntimeSha256':a.expected_runtime_sha256,'expectedEntrySha256':a.expected_entry_sha256,'actualRuntimeSha256':identity.get('treeSha256'),'actualEntrySha256':sha(entry),'nativeExecutedBeforeAdmission':False}
 try:
  validate_binding(identity,entry,a.expected_runtime_sha256,a.expected_entry_sha256)
  boundaries=entry_boundaries(entry)
 except Exception as error:
  admission.update(status='FAILED_PRECONDITION_NO_BROWSER',error=str(error));write(a.out/'admission.json',admission);return admission
 admission.update(status='ADMITTED_EXACT_CANDIDATE',boundaries=boundaries);write(a.out/'admission.json',admission)
 boundary=boundaries['compactHead' if a.case=='compact-head' else 'nativeCore'];cut=boundary['cutByte']
 release=threading.Event();sent=threading.Event();requests=[];errors=[]
 allowed={'/'+name for name in identity['files']}
 def provider(url):
  value=fixture(url,True)
  if urlsplit(url).hostname=='api.aladhan.com':
   date=urlsplit(url).path.rstrip('/').split('/')[-1];day,month,year=date.split('-')
   value['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year)
   value['data']['date']['hijri'].update(day='12',month={'number':4,'en':'Rabi al-Thani'},year='1448')
   value['data']['meta']['timezone']='America/New_York'
   value['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
  return value
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,p):return str(a.root/urlsplit(p).path.lstrip('/'))
  def do_GET(self):
   path=urlsplit(self.path).path;row={'path':self.path,'atMonotonicNs':time.monotonic_ns()};requests.append(row)
   try:
    if path=='/fixture':
     data=json.dumps(provider(parse_qs(urlsplit(self.path).query)['url'][0])).encode()
     self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
    if path=='/index.html':
     self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(entry)));self.send_header('Cache-Control','no-store');self.end_headers()
     self.wfile.write(entry[:cut]);self.wfile.flush();row.update(prefixFlushedAtNs=time.monotonic_ns(),prefixBytes=cut,prefixSha256=sha(entry[:cut]));sent.set()
     if not release.wait(80):row['holdExpired']=True;return
     row['releasedAtNs']=time.monotonic_ns();self.wfile.write(entry[cut:]);self.wfile.flush();return
    if path not in allowed:self.send_error(404);return
    super().do_GET()
   except (BrokenPipeError,ConnectionResetError) as e:row['connectionClosed']=type(e).__name__
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 origin='http://127.0.0.1:'+str(server.server_port)
 settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
 init="""(() => {
 const D=Date,origin=D.now(),stamp=D.parse('2026-09-25T02:00:00Z'),values=new Map([[KEY,SETTINGS]]);
 Object.defineProperty(window,'localStorage',{value:{getItem:k=>values.get(String(k))??null,setItem:(k,v)=>values.set(String(k),String(v)),removeItem:k=>values.delete(String(k))}});
 window.Date=class extends D{constructor(...a){super(...(a.length?a:[stamp+D.now()-origin]));}static now(){return stamp+D.now()-origin;}};
 window.__entryFixture={requests:[]};const fetch0=window.fetch.bind(window);
 window.fetch=(input,options)=>{const u=new URL(typeof input==='string'?input:input instanceof URL?input.href:input.url,location.href);window.__entryFixture.requests.push({url:u.href,at:performance.now()});
 return fetch0(u.origin!==location.origin&&['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io'].includes(u.hostname)?ORIGIN+'/fixture?url='+encodeURIComponent(u.href):input,options);};
 })();""".replace('KEY',json.dumps(ROOT_KEY)).replace('SETTINGS',json.dumps(json.dumps(settings))).replace('ORIGIN',json.dumps(origin))
 report={'schema':'pr43-actual-first-paint-lifecycle/1','case':a.case,'runtime':identity,'entrySha256':sha(entry),'harnessSha256':sha(Path(__file__).read_bytes()),
  'heldDecodedBoundary':cut,'boundaryKind':boundary['boundaryKind'],'transferBoundary':boundary,'allSourceBoundaries':boundaries,
  'expectedRuntimeSha256':a.expected_runtime_sha256,'expectedEntrySha256':a.expected_entry_sha256,
  'ageControl':'35 real seconds; fixture astronomical UTC advances at ordinary rate, no synthetic age jump',
  'visibilityControl':'Explicit document.hidden/visibilityState event boundary in full actual consumer; not physical OS tab, BFCache or extension-parent qualification',
  'providerClockScope':'Isolated private storage and deterministic provider/ordinary-rate night epoch. Astronomical UTC is used for currentness only, never navigation latency.',
  'snapshots':{},'checks':{},'ordinaryStartupQualification':False}
 os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 async def capture(page,name):
  value=await page.evaluate(EXTRA)
  if a.case=='compact-head' and name.startswith('compact-held-'):
   received=await page.evaluate(COMPACT_PREFIX_READ);text=received['text']
   value.update(compactScriptPresent=received['present'],compactScriptPrefixBytes=len(text.encode('utf-8')) if text is not None else None,compactScriptPrefixSha256=sha(text.encode('utf-8')) if text is not None else None)
  style=value.pop('styleText');background=value.pop('background')
  value['styleSha256']=sha(style.encode()) if style is not None else None
  value['backgroundSha256']=sha(background.encode()) if background is not None else None
  value['hasBackground']=background not in (None,'none')
  report['snapshots'][name]=value
  await page.screenshot(path=str(a.out/(name+'.png')))
  if a.case=='compact-head' and name.startswith('compact-held-'):
   ordinal=1 if name=='compact-held-start' else 2
   receiptPath=a.out/'native-capture-receipts'/(str(ordinal).zfill(4)+'.json')
   receipt=json.loads(receiptPath.read_text(encoding='utf-8'))
   image=(a.out/(name+'.png')).read_bytes()
   if receipt['pngSha256']!=sha(image) or receipt['pngBytes']!=len(image):raise ValueError('Native PNG receipt association failed')
   if (receipt['width'],receipt['height'],receipt['dpr'])!=(390,600,1):raise ValueError('Native viewport receipt drift')
   if receipt['ordinal']!=ordinal:raise ValueError('Native capture ordinal drift')
   for item in [receipt['before'],receipt['after']]:
    if item['prefixBytes']!=boundary['scriptPrefixBytes'] or item['prefixSha256']!=boundary['scriptPrefixSha256']:raise ValueError('Native capture prefix association failed')
    if item['bodyPresent'] or item['cardPresent'] or item['readyState']!='loading' or item['receiverPresent'] or item['runtimePresent']:raise ValueError('Native captured target not actual unfinished head')
   value['nativePixelReceipt']={'path':str(receiptPath),'sha256':sha(receiptPath.read_bytes()),'pngSha256':receipt['pngSha256'],'method':receipt['method'],'ordinal':ordinal}
   report.setdefault('nativeCaptureReceipts',{})[name]=receipt
  return value
 try:
  if a.case=='compact-head':
   if a.dpr!=1:raise ValueError('Compact capture proposal is scoped to DPR1')
   if os.environ.get('NODE_OPTIONS') or os.environ.get('SALAH_F1_CAPTURE_SPEC'):raise ValueError('Existing Node preload/spec requires separate source review')
   captureHook=Path(__file__).with_name('compact_viewport_capture.cjs')
   if sha(captureHook.read_bytes())!='f66fc18c39e4edae115059ee5c2b93215f37b4180fa72bce3feeb63633a19e9d':raise ValueError('Reviewed compact capture hook drift')
   import playwright as installedPlaywright
   package=Path(installedPlaywright.__file__).resolve().parent/'driver'/'package'
   spec={'schema':'f1-compact-native-capture-spec/1','playwrightPackage':str(package),'hookSha256':sha(captureHook.read_bytes()),
    'viewport':{'width':390,'height':600,'dpr':1},'prefixBytes':boundary['scriptPrefixBytes'],'prefixSha256':boundary['scriptPrefixSha256'],
    'receiptsDir':str(a.out/'native-capture-receipts')}
   specPath=a.out/'native-capture-spec.json';write(specPath,spec)
   os.environ['SALAH_F1_CAPTURE_SPEC']=str(specPath)
   os.environ['NODE_OPTIONS']='--require="'+captureHook.resolve().as_posix()+'"'
  async with async_playwright() as p:
   browser=await launch_browser(p);report['browser']=browser_identity(browser)
   context=await browser.new_context(viewport={'width':390,'height':600},device_scale_factor=a.dpr,timezone_id='America/New_York',reduced_motion='no-preference')
   await context.add_init_script(init);page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   try:
    await page.goto(origin+'/index.html#local=1&motion=full',wait_until='commit',timeout=30000)
    assert await asyncio.to_thread(sent.wait,10),'Actual held prefix missing'
    if a.case=='compact-head':
     # Prove actual parser receipt, independently of product availability.
     expectedPrefix=entry[boundary['scriptContentStartByte']:cut].decode('utf-8')
     await page.wait_for_function(COMPACT_PREFIX_WAIT,arg=expectedPrefix,polling=100,timeout=15000)
     before=await capture(page,'compact-held-start')
     await page.wait_for_timeout(1000);after=await capture(page,'compact-held-still')
     entryRequests=[row for row in requests if urlsplit(row['path']).path=='/index.html'];held=entryRequests[0] if len(entryRequests)==1 else {}
     transport={'singleActualEntryRequest':len(entryRequests)==1,'prefixFlushed':'prefixFlushedAtNs' in held,'prefixBytes':held.get('prefixBytes'),'prefixSha256':held.get('prefixSha256'),'suffixReleased':release.is_set() or 'releasedAtNs' in held,'holdExpired':held.get('holdExpired',False)}
     report['compactPrefixTransport']=transport
     report['checks'].update(compact_head_checks(boundary,before,after,transport))
     report['compactHeadObservation']={'zeroByteReadinessRequired':False,'forcedHoldPerformanceMeasurement':False,
      'beforeRelease':{k:after[k] for k in ['cardPresent','settingsPresent','prayerRowCount','headStyle','mainDeclared','hostPresent','previewPresent','firstPaintProducerPresent','initialReceiverPresent','moonRuntimePresent','firstScene','startupTiming']},
      'scope':'Availability is an observation, never a requirement for consumers to run with zero initial receiver bytes. Force-held time is separate from ordinary startup and first scene admission.'}
    else:
     await page.wait_for_selector('.c',state='attached',timeout=15000)
     before=await capture(page,'held-valid');hidden=None
     if a.case=='age':
      await page.wait_for_function('Date.now()-window.SalahFirstPaint.snapshot.utcMs>=35000',timeout=45000,polling=100)
      after=await capture(page,'held-after-35s')
     elif a.case=='invalidate':
      await page.evaluate('window.SalahMoonRuntime.invalidate("actual-entry review scene revocation")')
      await page.wait_for_timeout(100)
      after=await capture(page,'held-after-invalidate')
     elif a.case=='scene-change':
      await page.evaluate('location.hash="#local=1&motion=full&lat=24.47&lon=39.61&label=Madinah&method=4"')
      await page.wait_for_timeout(150)
      after=await capture(page,'held-after-scene-change')
     elif a.case=='hidden-resume':
      await page.evaluate("""() => {window.__visibilityOverride=true;Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.__visibilityOverride});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>window.__visibilityOverride?'hidden':'visible'});document.dispatchEvent(new Event('visibilitychange'));}""")
      hidden=await capture(page,'held-hidden')
      await page.evaluate('window.__visibilityOverride=false;document.dispatchEvent(new Event("visibilitychange"))')
      await page.wait_for_timeout(100)
      after=await capture(page,'held-resumed')
     else:
      await page.wait_for_timeout(1000);after=await capture(page,'held-still-valid')
     report['checks'].update(original_case_checks(a.case,before,after,hidden))
     report['lifecycleAudit']=lifecycle_audit(a.case,before,after)
     if a.case!='continuity' and after['headStyle']:
      await page.evaluate('document.getElementById("native-first-paint").remove()')
      removed=await capture(page,'explicit-style-removal-control')
      report['attributionControl']={'onlyStyleRemoved':True,'backgroundChanged':removed['backgroundSha256']!=after['backgroundSha256'],'headStyleAbsent':not removed['headStyle']}
    release.set()
    await page.wait_for_function("typeof boot==='function' && window.SalahSkyPreview?.state.status==='ready' && window.SalahMoonRuntime?.state.current && /[0-9]{1,2}:[0-9]{2}/.test(document.querySelector('.times .tm')?.textContent??'')",polling=100,timeout=45000)
    report['afterRelease']=await page.evaluate(SNAPSHOT)
    final=await capture(page,'after-compact-recovery' if a.case=='compact-head' else 'after-core-recovery')
    report['checks'].update(recovery_checks(report['afterRelease'],final,errors))
    if a.case=='compact-head':report['status']='PASS_SCOPED_COMPACT_HEAD_OBSERVATION' if all(report['checks'].values()) else 'FAIL_COMPACT_HEAD_OBSERVATION'
    else:
     report['originalOracleStatus']='PASS_SCOPED_ACTUAL_ENTRY_CONTROL' if all(report['checks'].values()) else 'FAIL_ACTUAL_ENTRY_CONTROL'
     report['status']=report['originalOracleStatus'] if report['lifecycleAudit']['status']=='PASS_DIAGNOSTIC_CUSTODY' else 'FAIL_OR_UNKNOWN_OWNER_DIAGNOSTICS'
   finally:
    release.set();await context.close();await browser.close()
 except Exception as e:report.update(status='HARNESS_OR_READINESS_FAILURE',error=str(e))
 finally:
  release.set();server.shutdown();report.update(pageErrors=errors,requests=requests,runtimeUnchanged=runtime_identity(a.root)==identity);write(a.out/'results.json',report)
 print(json.dumps({k:report.get(k) for k in ['case','status','error','checks','pageErrors','runtimeUnchanged']}),flush=True)
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--case',choices=['age','invalidate','scene-change','hidden-resume','continuity','compact-head'],required=True);p.add_argument('--dpr',type=float,default=1)
 p.add_argument('--expected-runtime-sha256',required=True);p.add_argument('--expected-entry-sha256',required=True)
 args=p.parse_args();result=asyncio.run(run(args))
 raise SystemExit(0 if result.get('status') in ['PASS_SCOPED_ACTUAL_ENTRY_CONTROL','PASS_SCOPED_COMPACT_HEAD_OBSERVATION'] and result.get('runtimeUnchanged') else 1)
