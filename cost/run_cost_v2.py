"""Passive real-callback acquisition. Exact review/admission required before launch."""
from pathlib import Path
import argparse,asyncio,datetime,hashlib,http.server,json,math,os,subprocess,sys,threading,time,traceback
from urllib.parse import urlsplit,parse_qs

O=Path(__file__).resolve().parents[1];C=O/'cost'
R=Path(r'<candidate>')
NODE=Path(r'<runtime-install>\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe')
BROWSERS={'chromium':Path(r'<browser-install>\chromium-1223\chrome-win64\chrome.exe'),'firefox':Path(r'<browser-install>\firefox-1522\firefox\firefox.exe')}
ROOTS={'A':O/'builds/baseline-18ff','B':O/'builds/integrated-r3'}
OVERLAY=C/'instrumented-r3';FONTS=C/'fonts-r1'
sys.path.insert(0,str(C))
from analyse_cost_v2 import analyse,match_state,validate_state,no_moon_work,WINDOW_MS,LATENESS_MS

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def safe(v):
 if isinstance(v,float) and not math.isfinite(v):return {'nonfiniteDiagnostic':repr(v)}
 if isinstance(v,Path):return str(v)
 if isinstance(v,dict):return {k:safe(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [safe(x) for x in v]
 return v
def save(p,v):p.write_text(json.dumps(safe(v),indent=2,allow_nan=False)+'\n',encoding='utf-8')
async def bounded(awaitable,seconds=10):return await asyncio.wait_for(awaitable,timeout=seconds)

def input_paths():
 import psutil
 fonts=json.loads((FONTS/'MANIFEST.json').read_text())
 paths=[Path(__file__),C/'probe.js',C/'instrument.cjs',C/'analyse_cost_v2.py',C/'RECIPE-v2.md',OVERLAY/'SOURCE-MAP.json',C/'EXPECTED-RUNTIME-A.json',C/'EXPECTED-RUNTIME-B.json',FONTS/'MANIFEST.json',R/'tests/v1_browser.py',R/'tools/cp9/runtime_identity.py',O/'capture-driver/cli.js',O/'capture-driver/lib/coreBundle.js',NODE,*BROWSERS.values()]
 paths += [FONTS/v['file'] for v in fonts['files'].values()]
 paths += [p for p in OVERLAY.rglob('*') if p.is_file()]
 paths += [p for p in Path(psutil.__file__).parent.glob('*') if p.suffix in ['.py','.pyd']]
 return sorted(set(paths))

def owned_processes():
 import psutil
 rows=[]
 for p in psutil.Process(os.getpid()).children(recursive=True):
  try:rows.append({'pid':p.pid,'created':p.create_time(),'exe':p.exe()})
  except psutil.NoSuchProcess:pass
 return rows

def merge_owned(previous,current):
 return list({(p['pid'],p['created'],p['exe']):p for p in previous+current}.values())

def reap_owned(rows):
 """Only previously observed descendants with matching PID/create-time/exe."""
 import psutil
 killed=[];remaining=[]
 for row in reversed(rows):
  try:
   p=psutil.Process(row['pid'])
   if p.create_time()!=row['created'] or p.exe()!=row['exe']:continue
   p.kill();killed.append(row)
  except psutil.NoSuchProcess:pass
  except Exception as e:remaining.append({**row,'error':str(e)})
 deadline=time.monotonic()+8
 for row in rows:
  try:
   p=psutil.Process(row['pid'])
   if p.create_time()!=row['created'] or p.exe()!=row['exe']:continue
   p.wait(timeout=max(.01,deadline-time.monotonic()))
  except psutil.NoSuchProcess:pass
  except Exception as e:remaining.append({**row,'error':str(e)})
 return {'killed':killed,'remaining':remaining,'verified':not remaining}

class Network:
 def __init__(self,slot):self.slot=slot;self.active={};self.serial=0
 def start(self,q):
  self.serial+=1;row={'id':self.serial,'url':q.url,'type':q.resource_type,'startMonotonic':time.monotonic()};self.active[q]=row;self.slot['network'].append(row)
 def finish(self,q,failed=False):
  row=self.active.pop(q,None)
  if row is None:self.slot['networkViolations'].append('Unmatched request completion '+q.url);return
  row['endMonotonic']=time.monotonic();row['failed']=failed
  if failed:self.slot['networkViolations'].append('Request failed '+q.url+': '+str(q.failure))
 def settled(self):
  assert not self.active,'Outstanding network at boundary'
  assert not self.slot['networkViolations'],'Network violation'
 def quiet_since(self,at):
  self.settled()
  assert not [r for r in self.slot['network'] if r['startMonotonic']>=at or r.get('endMonotonic',float('inf'))>=at],'Network overlaps warmup/observation'

async def run(a,out,record):
 import playwright._impl._transport as transport
 transport.compute_driver_executable=lambda:(str(NODE),str(O/'capture-driver/cli.js'))
 from playwright.async_api import async_playwright
 sys.path.insert(0,str(R/'tests'));from v1_browser import fixture,SETTINGS,ROOT_KEY
 sys.path.insert(0,str(R/'tools/cp9'));from runtime_identity import runtime_identity
 expected={s:json.loads((C/f'EXPECTED-RUNTIME-{s}.json').read_text()) for s in 'AB'}
 source_map=json.loads((OVERLAY/'SOURCE-MAP.json').read_text());fonts=json.loads((FONTS/'MANIFEST.json').read_text())['files']
 record['runtime']={s:runtime_identity(root) for s,root in ROOTS.items()}
 record['runtimeRoots']={s:str(root) for s,root in ROOTS.items()};record['expectedRuntimeFiles']={s:str(C/f'EXPECTED-RUNTIME-{s}.json') for s in 'AB'}
 assert record['runtime']==expected,'Initial complete runtime identity changed'
 record['runtimeExpectedMatched']=True
 for side,root in ROOTS.items():
  for rel,v in source_map['sides'][side]['files'].items():
   assert sha(root/rel)==v['originalSha256'] and sha(OVERLAY/side/rel)==v['instrumentedSha256'],'Overlay binding'
 for url,v in fonts.items():assert sha(FONTS/v['file'])==v['sha256'] and (FONTS/v['file']).stat().st_size==v['bytes'],'Font fixture changed'
 record['expectedScopes']={s:sorted(set(r['role'] for v in source_map['sides'][s]['files'].values() for p in v['parts'] for r in p['roles'])) for s in 'AB'}
 record['expectedOwners']={s:sorted(set(r['owner'] for v in source_map['sides'][s]['files'].values() for p in v['parts'] for r in p['owners'])) for s in 'AB'}
 record['sourceMapSha256']=sha(OVERLAY/'SOURCE-MAP.json');record['fontManifestSha256']=sha(FONTS/'MANIFEST.json')
 requests=[];active={'side':None,'slot':None};payloads={};serve_errors=[]
 def provider(u):
  v=fixture(u,True);parts=urlsplit(u);query=parse_qs(parts.query)
  if parts.hostname=='api.aladhan.com':
   date=parts.path.rstrip('/').split('/')[-1];day,month,year=date.split('-');hd=11+(datetime.datetime(int(year),int(month),int(day))-datetime.datetime(2026,9,24)).days
   assert 1<=hd<=30
   v['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year)
   v['data']['date']['hijri'].update(day=str(hd),month={'number':4,'en':'Rabi al-Thani'},year='1448')
   v['data']['meta']['timezone']='America/New_York'
   v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
  elif parts.hostname=='api.open-meteo.com':
   v.update(latitude=float(query.get('latitude',['28.5383'])[0]),longitude=float(query.get('longitude',['-81.3792'])[0]),elevation=0,timezone='America/New_York',utc_offset_seconds=-14400)
   v['current'].update(time='2026-09-24T22:00',interval=900,weather_code=0,cloud_cover=0,cloud_cover_low=0,cloud_cover_mid=0,cloud_cover_high=0,precipitation=0,rain=0,visibility=20000)
   v['current_units']={'time':'iso8601','interval':'seconds','temperature_2m':'°C','apparent_temperature':'°C','dew_point_2m':'°C','relative_humidity_2m':'%','wind_speed_10m':'m/s','precipitation':'mm','rain':'mm','showers':'mm','snowfall':'cm'}
  elif parts.hostname in ['get.geojs.io','ipinfo.io']:
   v={'latitude':'28.5383','longitude':'-81.3792','loc':'28.5383,-81.3792','city':'Orlando fixture','country':'United States','country_code':'US','timezone':'America/New_York'}
  data=json.dumps(v,separators=(',',':')).encode();digest=hashlib.sha256(data).hexdigest()
  if u in payloads:assert payloads[u]['sha256']==digest,'Fixture payload drift'
  else:payloads[u]={'sha256':digest,'body':v}
  return data
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   p=urlsplit(self.path);side=active['side'];row={'slot':active['slot'],'side':side,'path':self.path,'monotonic':time.monotonic()};requests.append(row)
   try:
    if p.path=='/fixture':data=provider(parse_qs(p.query)['url'][0]);kind='application/json'
    elif p.path=='/favicon.ico':data=b'';kind='image/x-icon'
    else:
     rel=p.path.removeprefix('/salah_widget/');rel='index.html' if rel=='' else rel
     assert rel in expected[side]['files'],'Unplanned runtime resource '+rel
     binding=source_map['sides'][side]['files'].get(rel);target=OVERLAY/side/rel if binding else ROOTS[side]/rel
     data=target.read_bytes();kind=self.guess_type(str(target));digest=hashlib.sha256(data).hexdigest()
     assert digest==(binding['instrumentedSha256'] if binding else expected[side]['files'][rel]['sha256']),'Served bytes drift'
    row['servedSha256']=hashlib.sha256(data).hexdigest()
    self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):row['clientDisconnected']=True
   except Exception as e:row['error']=str(e);serve_errors.append(str(e));self.send_error(500,str(e))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
 settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
 provider_js="""(()=>{const original=window.fetch.bind(window),cache=new Map(),hosts=new Set(['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io']);window.__r21Provider={attempts:0,firstRequests:0,cachedResponses:0,pending:0,blockedExternalRefresh:true};window.fetch=async(input,init)=>{const u=new URL(typeof input==='string'?input:input.url,location.href);if(!hosts.has(u.hostname))return original(input,init);const p=window.__r21Provider;p.attempts++;if(cache.has(u.href)){p.cachedResponses++;return (await cache.get(u.href)).clone();}p.firstRequests++;p.pending++;const promise=original(ORIGIN+'/fixture?url='+encodeURIComponent(u.href),init).then(async r=>{const b=await r.arrayBuffer();return new Response(b,{status:r.status,headers:r.headers});}).finally(()=>p.pending--);cache.set(u.href,promise);return (await promise).clone();};})();""".replace('ORIGIN',json.dumps(origin))
 record.update(fixtureRevision=2,settings=settings,sequence=[{'block':b,'order':i,'side':s} for b in range(4) for i,s in enumerate('ABBA')],requests=requests,payloads=payloads,serveErrors=serve_errors,slots=[])
 browser=None;pw=None;owned=[]
 async def acquire(slot,sd,ctx,page,net):
  side=slot['side'];required=record['expectedOwners'][side]
  async def evaluate(js):return await bounded(page.evaluate(js))
  async def route(r):
   url=r.request.url
   if url in fonts:
    v=fonts[url];data=(FONTS/v['file']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=v['sha256']:slot['networkViolations'].append('Font bytes changed');return await r.abort()
    slot['fontDeliveries'].append({'url':url,'sha256':v['sha256']});return await r.fulfill(body=data,content_type=v['contentType'],headers={'access-control-allow-origin':'*'})
   if url.startswith(origin+'/'):return await r.continue_()
   slot['networkViolations'].append('Unplanned external request '+url);await r.abort()
  await bounded(ctx.route('**/*',route))
  await bounded(ctx.add_init_script("(()=>{const D=Date,t=D.parse('2026-09-25T02:00:00Z'),s=D.now();window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();"))
  await bounded(ctx.add_init_script('if(location.protocol==="http:")localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');'))
  await bounded(ctx.add_init_script(provider_js));await bounded(ctx.add_init_script(path=str(C/'probe.js')))
  page.on('pageerror',lambda e:slot['errors'].append(str(e)))
  ctx.on('request',net.start);ctx.on('requestfinished',net.finish);ctx.on('requestfailed',lambda q:net.finish(q,True))
  page.on('response',lambda r:slot['networkViolations'].append('HTTP '+str(r.status)+' '+r.url) if r.status>=400 else None)
  async def ready():
   await bounded(page.goto(origin+'/salah_widget/#local=1&motion=full',wait_until='domcontentloaded',timeout=60000),65)
   while True:
    value=await evaluate('window.__r21.ready()');slot['readiness'].append(value)
    if slot['errors'] or slot['networkViolations'] or serve_errors:raise RuntimeError('Acquisition native/network error')
    if value['ready'] and not net.active:break
    await asyncio.sleep(1)
  await bounded(ready(),130)
  slot['readyState']=await evaluate('window.__r21.snapshot()');validate_state(slot['readyState'],required)
  if 'referenceState' not in record:record['referenceState']=slot['readyState']
  slot['readyMatch']=match_state(record['referenceState'],slot['readyState'],required);net.settled()
  assert any(x['url'].endswith('.woff2') for x in slot['fontDeliveries']),'No pinned font payload delivered'
  slot['overheadBefore']=await evaluate('window.__r21.overhead()');steps=slot['overheadBefore']['clockPositiveStepsMs']
  assert steps and min(steps)<=.25,'Clock cannot resolve minimum .25ms allowance; no browser preference changed'
  net.settled();quiet=time.monotonic();slot['quietStartMonotonic']=quiet
  slot['warmStart']=await evaluate('window.__r21.mark()');await asyncio.sleep(5);slot['warmEnd']=await evaluate('window.__r21.mark()')
  assert WINDOW_MS<=slot['warmEnd']['at']-slot['warmStart']['at']<=WINDOW_MS+LATENESS_MS,'Warmup boundary lateness'
  slot['startState']=await evaluate('window.__r21.snapshot()');slot['startMatch']=match_state(record['referenceState'],slot['startState'],required);no_moon_work(slot['readyState'],slot['startState']);net.quiet_since(quiet)
  slot['start']=await evaluate('window.__r21.mark()');await asyncio.sleep(5);slot['end']=await evaluate('window.__r21.mark()')
  assert WINDOW_MS<=slot['end']['at']-slot['start']['at']<=WINDOW_MS+LATENESS_MS,'Observation boundary lateness'
  slot['endState']=await evaluate('window.__r21.snapshot()');slot['endMatch']=match_state(record['referenceState'],slot['endState'],required);no_moon_work(slot['startState'],slot['endState']);net.quiet_since(quiet)
  slot['networkSettled']=True;slot['overheadAfter']=await evaluate('window.__r21.overhead()')
  raw=await evaluate('window.__r21.export()');save(sd/'CALLS.json',raw);slot.update(callsSha256=sha(sd/'CALLS.json'),rawFile=str((sd/'CALLS.json').relative_to(out)))
  assert not raw['invalid'] and not raw['errors'] and not slot['errors'],'Observer/native error'
  await evaluate("()=>{window.SalahRealSky?.dispose();window.SalahSkyPreview?.dispose();window.SalahMoonRuntime?.dispose();window.SalahMoonDetail?.dispose();}")
  slot['disposedState']=await evaluate('window.__r21.snapshot()');slot['status']='RAW_SLOT_RETURNED'
 try:
  pw=await bounded(async_playwright().start(),20)
  launch={'headless':True,'executable_path':str(BROWSERS[a.engine])}
  if a.engine=='chromium':launch.update(args=['--disable-dev-shm-usage'],chromium_sandbox=True)
  browser=await bounded(getattr(pw,a.engine).launch(**launch),40)
  record['browser']={'engine':a.engine,'version':browser.version,'options':launch};owned=owned_processes()
  for step in record['sequence']:
   sid=f"{step['block']}-{step['order']}-{step['side']}";active.update(side=step['side'],slot=sid);sd=out/sid;sd.mkdir()
   slot={**step,'id':sid,'startedUtc':utc(),'status':'ACQUIRING','readiness':[],'errors':[],'network':[],'networkViolations':[],'fontDeliveries':[]};record['slots'].append(slot)
   ctx=None;page=None;started=time.monotonic()
   try:
    ctx=await bounded(browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference'),10)
    page=await bounded(ctx.new_page(),10);await bounded(acquire(slot,sd,ctx,page,Network(slot)),180)
   except Exception:
    slot.update(status='INCOMPLETE',error=traceback.format_exc())
    if page:
     try:
      raw=await bounded(page.evaluate('window.__r21.export()'),5);save(sd/'CALLS.json',raw);slot.update(callsSha256=sha(sd/'CALLS.json'),rawFile=str((sd/'CALLS.json').relative_to(out)))
      slot['failureState']=await bounded(page.evaluate('window.__r21.snapshot()'),5)
     except Exception as e:slot['failureReadbackError']=str(e)
   finally:
    owned=merge_owned(owned,owned_processes())
    if ctx:
     try:await bounded(ctx.close(),10);slot['contextClosed']=True
     except Exception as e:slot.update(status='INCOMPLETE',contextClosed=False,closeError=str(e))
    slot['returnedUtc']=utc();save(sd/'SLOT.json',slot);save(out/'RESULTS.json',record)
    print(json.dumps({'slot':sid,'status':slot['status'],'seconds':round(time.monotonic()-started,2)}),flush=True)
   if slot['status']!='RAW_SLOT_RETURNED':break
 finally:
  owned=merge_owned(owned,owned_processes());record['ownedProcesses']=owned
  if browser:
   try:await bounded(browser.close(),15);record['browserClosed']=True
   except Exception as e:record.update(browserClosed=False,browserCloseError=str(e))
  if pw:
   try:await bounded(pw.stop(),10);record['playwrightStopped']=True
   except Exception as e:record.update(playwrightStopped=False,playwrightStopError=str(e))
  record['ownedCleanup']=reap_owned(owned)
  server.shutdown();server.server_close()
  record['runtimeUnchanged']={s:record['runtime'][s]==runtime_identity(root) for s,root in ROOTS.items()}
  record['servedIdentityVerified']=not serve_errors
 clean=record.get('browserClosed') is True and record.get('playwrightStopped') is True and record['ownedCleanup']['verified'] is True and not record['ownedCleanup']['remaining']
 record['status']='RAW_BATCH_RETURNED' if len(record['slots'])==16 and all(s['status']=='RAW_SLOT_RETURNED' for s in record['slots']) and clean else 'INCOMPLETE'

def main():
 p=argparse.ArgumentParser();p.add_argument('engine',choices=BROWSERS);p.add_argument('name');p.add_argument('--admission',type=Path,required=True);a=p.parse_args()
 pins={str(x):sha(x) for x in input_paths()};admission=json.loads(a.admission.read_text())
 assert admission.get('status')=='ADMITTED_EXACT_PASSIVE_COST_ACQUISITION' and admission.get('inputSha256')==pins,'Exact admission missing/stale'
 out=C/'runs'/a.name;assert not out.exists(),'Preserve earlier run';out.mkdir(parents=True)
 for i,(p,h) in enumerate(pins.items()):
  target=out/'harness'/f'{i:03d}-{Path(p).name}';target.parent.mkdir(exist_ok=True);target.write_bytes(Path(p).read_bytes())
 record={'schema':'r0021-passive-cost-acquisition/v2','status':'ACQUIRING','engine':a.engine,'createdAtUtc':utc(),'inputs':pins,'admission':str(a.admission),'admissionSha256':sha(a.admission),'pythonPid':os.getpid()}
 lock=O/'native-resource.lock'
 with lock.open('x') as f:f.write(a.name)
 try:
  record['powerPlan']=subprocess.run(['powercfg','/getactivescheme'],capture_output=True,text=True,timeout=10).stdout.strip()
  asyncio.run(run(a,out,record))
 except BaseException:record.update(status='INCOMPLETE',error=traceback.format_exc())
 finally:
  if 'ownedCleanup' not in record:record['ownedCleanup']=reap_owned(owned_processes())
  record['returnedAtUtc']=utc();record['inputsUnchanged']=all(Path(p).is_file() and sha(Path(p))==h for p,h in pins.items());save(out/'RESULTS.json',record)
  analysis=analyse(out,record)
  if analysis['globalReasons']:record['status']='INCOMPLETE'
  save(out/'ANALYSIS.json',analysis)
  if record.get('ownedCleanup',{}).get('verified') is True:
   assert lock.read_text()==a.name;lock.unlink();record['lockReleased']=True
  else:record['lockReleased']=False
  save(out/'RESULTS.json',record)
 print(json.dumps({'status':record['status'],'output':str(out),'lockReleased':record.get('lockReleased')}));return 0 if record['status']=='RAW_BATCH_RETURNED' else 2
if __name__=='__main__':sys.exit(main())
