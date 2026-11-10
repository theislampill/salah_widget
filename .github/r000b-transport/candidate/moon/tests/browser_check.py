#!/usr/bin/env python3
"""Exercise exact entries with controlled provider/date data; no silent transport fallback.
--transport navigation uses actual HTTP/file navigation (receiving Codex).
--transport fixture uses explicit set_content/resource delivery under restricted hosts.
Neither is a live provider observation. Browser process sandbox policy is explicit.
"""
from pathlib import Path
import argparse, ast, functools, hashlib, http.server, json, mimetypes, os, sys, threading, time, traceback
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cp9'))
from browser_runtime import browser_options, browser_identity
# Fixture data is installed before product execution, never inside product files.
INIT=r'''(()=>{
const NativeDate=Date,base=NativeDate.parse('2026-09-07T20:30:00Z');window.Date=class extends NativeDate{constructor(...a){super(...(a.length?a:[base]));}static now(){return base;}};
const storage=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>storage.get(String(k))??null,setItem:(k,v)=>storage.set(String(k),String(v)),removeItem:k=>storage.delete(String(k)),clear:()=>storage.clear()}});
const f=window.fetch;window.fetch=async(input,opts)=>{const u=new URL(typeof input==='string'?input:input.url,document.baseURI);if(u.hostname==='api.aladhan.com'&&u.pathname.includes('/timings/')){const date=u.pathname.split('/').at(-1),[d,m,y]=date.split('-'),p=u.searchParams,tz=new URLSearchParams(location.hash.slice(1)).get('tz')||'Asia/Riyadh';return new Response(JSON.stringify({code:200,status:'OK',data:{timings:{Fajr:'04:46',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Sunset:'18:33',Maghrib:'18:33',Isha:'20:03'},date:{gregorian:{date,day:d,month:{number:+m,en:'September'},year:y},hijri:{date:'25-03-1448',day:'25',month:{number:3,en:'Rabi al-awwal'},year:'1448',method:'HJCoSA'}},meta:{latitude:+p.get('latitude'),longitude:+p.get('longitude'),timezone:tz,method:{id:+p.get('method')},school:p.get('school')==='1'?'HANAFI':'STANDARD'}}}),{status:200,headers:{'Content-Type':'application/json'}});}return f(input,opts);};
// Test-only appended failure listener, preserving every product worker function.
const makeURL=URL.createObjectURL.bind(URL);URL.createObjectURL=b=>makeURL(b.type==='text/javascript'?new Blob([b,'\nself.addEventListener("message", e=>{if(e.data.kind==="__moon_test_crash")setTimeout(()=>{throw new Error("CONTROLLED_MOON_WORKER_EXCEPTION")},0);});'],{type:b.type}):b);
window.__moonTestWorkers=[];const W=window.Worker;window.Worker=class extends W{constructor(u,o){super(u,o);window.__moonTestWorkers.push(this);const post=this.postMessage.bind(this);this.postMessage=(m,t)=>{if(m.kind==='boot'&&'offline' in m)this.__moon=true;return t?post(m,t):post(m);}}};
window.__heartbeats=[];let last=performance.now();setInterval(()=>{const n=performance.now();window.__heartbeats.push(n-last);last=n;},25);
})();'''
STATE="""()=>({moon:window.SalahMoonRuntime?.state,sky:(()=>{const s=window.realSkyState?.();return s?{status:s.status,renders:s.renders,errors:s.errors}:null})(),rows:document.querySelectorAll('.p').length,detail:window.SalahMoonDetail?.state,bytes:document.querySelector('.mphoto')?.getAttribute('href')?.length,embedded:document.querySelectorAll('[id^="moon-embedded-"]').length,classes:document.querySelector('.c')?.className,heartbeats:window.__heartbeats.splice(0)})"""
def wait(page,expr,timeout=240):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if page.evaluate('()=>('+expr+')'):return
  page.wait_for_timeout(100)
 s=page.evaluate(STATE);s.pop('heartbeats',None);raise TimeoutError(expr+' '+json.dumps(s))
def refscene(f=.5):
 import math
 a=math.acos(2*f-1)
 return {'size':40,'outSize':80,'diameter':76.8,'basis':[0,1,0,0,0,1,1,0,0],'sun':[math.cos(a),-math.sin(a),0],'earth':[384400,0,0],'distance':384400,'extent':1.08,'mode':'physical-reference','fraction':f,'waxing':False,'tilt':0}
def run(root,out,entry,transport,dpr,quick,sandbox,executable,initial_fault=None,local_scripts=False):
 root=root.resolve();out.mkdir(parents=True,exist_ok=True);records=[];requests=[];errors=[]
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}'
 hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/entry,root/'moon/moon-host.js',root/'moon/moon-worker.js',root/'moon/moon_kernel.wasm']}
 record={'entry':entry,'transport':transport,'dpr':dpr,'quickPhysicalReference':quick,'localScriptAssetPath':local_scripts,'scope':'Controlled provider/date actual product. Test-only failure listener appended to worker source; numerical function bodies unchanged. No live acquisition or native deployment inference from fixture transport','source':hashes,'processSandbox':sandbox,'webSecurity':'unmodified','harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':records,'errors':errors}
 started=time.monotonic()
 try:
  with sync_playwright() as p:
   family,options=browser_options()
   if executable:options['executable_path']=executable
   if family=='chromium':options['chromium_sandbox']=sandbox
   b=getattr(p,family).launch(**options)
   record['browser']=browser_identity(b)
   c=b.new_context(viewport={'width':700,'height':720},device_scale_factor=dpr,reduced_motion='reduce')
   page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   fault={'mode':initial_fault}
   def route(r):
    from urllib.parse import urlparse,unquote
    u=urlparse(r.request.url);requests.append(r.request.url)
    if u.scheme in ['blob','data']:r.continue_();return
    if u.hostname not in ['127.0.0.1','moon.cp9.test']:r.abort();return
    f=root/unquote(u.path.lstrip('/'))
    if not f.is_file() or root not in f.resolve().parents:r.abort();return
    if f.name=='dem.bin.gz' and fault['mode']:
     mode=fault['mode']; data=f.read_bytes()
     if mode=='missing':r.fulfill(status=404,body='not found');return
     if mode=='truncated':data=data[:-1]
     elif mode=='corrupt':data=bytes([data[0]^1])+data[1:]
     r.fulfill(body=data,content_type='application/octet-stream');return
    r.fulfill(path=str(f),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   c.route('**/*',route)
   h='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Moon-test&method=4&simTime=23:30&simWx=0&simCloud=0&simTemp=20&units=c&motion=reduced&simMoon=.5&simWax=0&simMoonAlt=20&simMoonH=42&qa=1'
   if transport=='navigation':
    c.add_init_script(INIT);url=(root/entry).as_uri() if entry=='offline.html' else origin+'/'+entry
    page.goto(url+'#'+h,wait_until='domcontentloaded',timeout=30000)
   else:
    page.evaluate('(h)=>location.hash=h',h);page.evaluate(INIT)
    if local_scripts:page.evaluate('window.__SALAH_MOON_OFFLINE__=true')
    source=(root/entry).read_text(encoding='utf-8')
    if entry!='offline.html':source=source.replace('<head>','<head><base href="'+origin+'/">',1)
    page.set_content(source,wait_until='domcontentloaded',timeout=60000)
   wait(page,'!!window.SalahMoonRuntime',30)
   if quick:page.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',refscene())
   if initial_fault:
    wait(page,'SalahMoonRuntime.state.status==="unavailable"',60)
    fail=page.evaluate(STATE)
    assert fail['rows']==6 and not fail['moon']['legacyFallback'] and fail['moon']['visibleSource']=='awaiting-terrain'
    assert page.evaluate('SalahMoonRuntime.surface()===null')
    records.append({'name':'asset-'+initial_fault+'-refused-without-old-Moon-substitution','status':'PASS','state':fail})
    fault['mode']=None;assert page.evaluate('SalahMoonRuntime.retry()')
   wait(page,'SalahMoonRuntime.state.status==="ready"',280)
   wait(page,'document.querySelectorAll(".p").length===6',20)
   s=page.evaluate(STATE);assert not s['moon']['legacyFallback'];records.append({'name':'initial-full-terrain','status':'PASS','seconds':time.monotonic()-started,'state':s})
   page.evaluate('window.__heartbeats=[]')
   lags=[]
   for _ in range(4):
    tick=time.monotonic();page.locator('#ceDateButton').click();assert page.locator('#dateDialog').evaluate('(x)=>x.open');page.locator('#dateClose').click();lags.append((time.monotonic()-tick)*1000)
   page.wait_for_timeout(1500)
   ui=page.evaluate(STATE);gaps=ui['heartbeats'];records.append({'name':'loaded-prayer-date-interaction','status':'PASS','dialogs':4,'maxAutomationRoundTripMs':max(lags),'maxHeartbeatMs':max(gaps or [0]),'state':ui})
   # Captures are separate from heartbeat samples (protocol capture itself can stall).
   page.screenshot(path=str(out/'ready.png'),timeout=30000)
   page.evaluate('window.__heartbeats=[]')
   if not quick:page.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',refscene()) ; wait(page,'SalahMoonRuntime.state.status==="ready"',90)
   # A failed replacement retains the original independently validated current
   # surface; a target change below must still revoke it immediately.
   retained=page.evaluate('SalahMoonRuntime.state.accepted.identity')
   page.evaluate('''()=>{const w=__moonTestWorkers.filter(w=>w.__moon).at(-1);w.postMessage({kind:'__moon_test_crash'});}''')
   wait(page,'SalahMoonRuntime.state.status==="unavailable"',10)
   s=page.evaluate(STATE)
   assert s['rows']==6 and not s['moon']['legacyFallback'] and s['moon']['accepted']['identity']==retained
   assert page.evaluate('!!SalahMoonRuntime.surface() && SalahMoonRuntime.state.quality==="empirical-adaptive"')
   records.append({'name':'actual-worker-exception-retains-only-original-current-terrain','status':'PASS','state':s})
   page.evaluate("SalahMoonRuntime.setProfile('reference')");assert page.evaluate('SalahMoonRuntime.surface()===null')
   assert page.evaluate('SalahMoonRuntime.retry()')
   wait(page,'SalahMoonRuntime.state.status==="ready"',90)
   s=page.evaluate(STATE);assert not s['moon']['legacyFallback'];records.append({'name':'real-worker-retry','status':'PASS','state':s})
   if entry=='offline.html':assert s['embedded']==68
   page.evaluate("SalahMoonRuntime.setProfile('reference')");wait(page,'SalahMoonRuntime.state.status==="ready"',90)
   s=page.evaluate(STATE);assert s['moon']['accepted']['scene']['profile']['mode']=='reference';records.append({'name':'profile-currentness','status':'PASS','state':s})
   page.evaluate("SalahMoonRuntime.setProfile('calendar')");page.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',refscene(.12));page.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',refscene(.75))
   wait(page,'SalahMoonRuntime.state.status==="ready"',90)
   s=page.evaluate(STATE);assert abs(s['moon']['accepted']['scene']['fraction']-.75)<1e-9;records.append({'name':'superseded-phase-final-winner','status':'PASS','state':s})
   page.screenshot(path=str(out/'gibbous.png'),timeout=30000)
   page.evaluate("SalahMoonRuntime.dispose()");s=page.evaluate(STATE);assert not s['moon']['workerAlive'];records.append({'name':'dispose','status':'PASS','state':s})
   record['expectedInjectedExceptions']=[e for e in errors if 'CONTROLLED_MOON_WORKER_EXCEPTION' in e]
   unexpected=[e for e in errors if 'CONTROLLED_MOON_WORKER_EXCEPTION' not in e];assert not unexpected,unexpected
   c.close();b.close();record['status']='PASS_SCOPED'
 except Exception as e:record['status']='FAIL_OR_BLOCKED';record['exception']=str(e);record['traceback']=traceback.format_exc()
 finally:
  server.shutdown();record['seconds']=time.monotonic()-started;record['requests']=requests
  (out/'receipt.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
 return record
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);a.add_argument('--entry',choices=['index.html','offline.html'],default='offline.html');a.add_argument('--transport',choices=['fixture','navigation'],default='navigation');a.add_argument('--dpr',type=float,default=1);a.add_argument('--quick',action='store_true');a.add_argument('--asset-fault',choices=['missing','truncated','corrupt']);a.add_argument('--local-script-assets',action='store_true');a.add_argument('--container-no-process-sandbox',action='store_true');a.add_argument('--executable',default=os.environ.get('SALAH_BROWSER_EXECUTABLE'));args=a.parse_args()
 r=run(args.root,args.output,args.entry,args.transport,args.dpr,args.quick,not args.container_no_process_sandbox,args.executable,args.asset_fault,args.local_script_assets);print(json.dumps({k:r[k] for k in ['status','seconds','entry','transport']},indent=2));raise SystemExit(0 if r['status']=='PASS_SCOPED' else 1)
