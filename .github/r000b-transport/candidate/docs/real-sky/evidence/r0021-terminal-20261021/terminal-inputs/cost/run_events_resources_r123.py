"""One finite Chromium actual-event group and one resource sequence per engine.
Uses the retained v5 native marker method; no Firefox profiler or steady ABBA.
"""
from pathlib import Path
import asyncio,datetime,hashlib,http.server,json,os,subprocess,sys,threading,time,traceback
from urllib.parse import urlsplit,parse_qs
C=Path(__file__).resolve().parent;O=C.parent
R=Path(r'${REPO_ROOT}')
sys.path.insert(0,str(C));sys.path.insert(0,str(R/'tests'));sys.path.insert(0,str(R/'tools/cp9'))
from run_cost_v5_r76 import NativeProfiler,owned_processes,merge_owned,reap_owned,safe,clock_info
from runtime_identity import runtime_identity
from v1_browser import fixture,SETTINGS,ROOT_KEY
ROOTS={'A':O/'builds/baseline-18ff','B':O/'builds/integrated-r30-owner-callbacks'}
OVERLAY=C/'instrumented-r123-reviewed';FONTS=C/'fonts-r1';DEST=C/'runs/events-resources-r123'
NODE=Path(r'${TOOL_CACHE}\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe')
EXES={'chromium':r'${BROWSER_CACHE}\chromium-1223\chrome-win64\chrome.exe','firefox':r'${BROWSER_CACHE}\firefox-1522\firefox\firefox.exe'}
SCENES={'night':'2026-09-25T02:00:00Z','twilight':'2026-09-24T10:30:00Z','day':'2026-09-24T14:00:00Z'}
OWNED=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_bytes((json.dumps(safe(v),indent=2,allow_nan=False)+'\n').encode())
def inputs():
 paths=[Path(__file__),C/'instrument-r123.cjs',C/'probe-r123.js',C/'resource-controls-r123.js',C/'native_profile_v5.py',C/'native_profiler_v5.py',C/'native-mark-recorder-r55.js',C/'run_cost_v5_r76.py',OVERLAY/'SOURCE-MAP.json',FONTS/'MANIFEST.json',R/'tests/v1_browser.py',R/'tools/cp9/runtime_identity.py',O/'capture-driver/cli.js',O/'capture-driver/lib/coreBundle.js']
 paths += [p for p in OVERLAY.rglob('*') if p.is_file()]
 paths += [NODE,*map(Path,EXES.values()),O/'parent/firefox_actual_widget_r9.py']
 paths += [C/(name+'.py') for name in ['host_clock_v76','analyse_cost_v3','cost_state_v5','window_wait_v5','analyse_cost_v76','analyse_cost_v5','network_evidence_v4']]
 paths += [FONTS/v['file'] for v in json.loads((FONTS/'MANIFEST.json').read_bytes())['files'].values()]
 return {str(p):sha(p) for p in sorted(set(paths))}

async def run():
 global OWNED
 assert not DEST.exists(),'No repeat or overwrite'
 DEST.mkdir(parents=True)
 record={'schema':'r0021-bounded-events-resources/v1','status':'ACQUIRING','inputs':inputs(),'runtime':{k:runtime_identity(v) for k,v in ROOTS.items()},'slots':[],'hostObservationClock':clock_info(),'resourceSettlementLimitMs':10000,'perOwnerCycles':3,'noNewPerformanceTolerance':True}
 record['powerPlan']=subprocess.run(['powercfg','/getactivescheme'],capture_output=True,text=True,timeout=10).stdout.strip()
 assert record['runtime']['B']['treeSha256']=='3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821'
 source_map=json.loads((OVERLAY/'SOURCE-MAP.json').read_bytes());fonts=json.loads((FONTS/'MANIFEST.json').read_bytes())['files']
 for side in 'AB':
  for rel,v in source_map['sides'][side]['files'].items():assert sha(ROOTS[side]/rel)==v['originalSha256'] and sha(OVERLAY/side/rel)==v['instrumentedSha256']
 active={};requests=[];payloads=[]
 def provider(u):
  v=fixture(u,True);parts=urlsplit(u);q=parse_qs(parts.query);local=active['instant'].astimezone(datetime.timezone(datetime.timedelta(hours=-4)))
  if parts.hostname=='api.aladhan.com':
   date=parts.path.rstrip('/').split('/')[-1];day,month,year=date.split('-');hd=11+(datetime.datetime(int(year),int(month),int(day))-datetime.datetime(2026,9,24)).days;assert 1<=hd<=30
   v['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year);v['data']['date']['hijri'].update(day=str(hd),month={'number':4,'en':'Rabi al-Thani'},year='1448');v['data']['meta']['timezone']='America/New_York'
   v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
  elif parts.hostname=='api.open-meteo.com':
   v.update(latitude=float(q.get('latitude',['28.5383'])[0]),longitude=float(q.get('longitude',['-81.3792'])[0]),elevation=0,timezone='America/New_York',utc_offset_seconds=-14400)
   v['current'].update(time=local.strftime('%Y-%m-%dT%H:%M'),interval=900,weather_code=2 if active['scene']=='day' else 0,cloud_cover=35 if active['scene']=='day' else 0,cloud_cover_low=35 if active['scene']=='day' else 0,cloud_cover_mid=0,cloud_cover_high=0,precipitation=0,rain=0,visibility=20000)
   v['current_units']={'time':'iso8601','interval':'seconds','temperature_2m':'°C','apparent_temperature':'°C','dew_point_2m':'°C','relative_humidity_2m':'%','wind_speed_10m':'m/s','precipitation':'mm','rain':'mm','showers':'mm','snowfall':'cm'}
  elif parts.hostname in ['get.geojs.io','ipinfo.io']:v={'latitude':'28.5383','longitude':'-81.3792','loc':'28.5383,-81.3792','city':'Orlando fixture','country':'United States','country_code':'US','timezone':'America/New_York'}
  data=json.dumps(v,separators=(',',':')).encode();payloads.append({'slot':active['id'],'url':u,'sha256':hashlib.sha256(data).hexdigest(),'body':v});return data
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   path=urlsplit(self.path);side=active['side'];row={'slot':active['id'],'path':self.path,'atPerfCounter':time.perf_counter()};requests.append(row)
   try:
    if path.path=='/fixture':
     u=parse_qs(path.query)['url'][0]
     if urlsplit(u).hostname=='api.open-meteo.com':time.sleep(.75)
     data=provider(u);kind='application/json'
    elif path.path=='/favicon.ico':data=b'';kind='image/x-icon'
    else:
     rel=path.path.removeprefix('/salah_widget/') or 'index.html';assert rel in record['runtime'][side]['files'],rel
     info=source_map['sides'][side]['files'].get(rel);p=OVERLAY/side/rel if info else ROOTS[side]/rel;data=p.read_bytes();kind=self.guess_type(str(p));assert hashlib.sha256(data).hexdigest()==(info['instrumentedSha256'] if info else record['runtime'][side]['files'][rel]['sha256'])
    row.update(status=200,bytes=len(data),sha256=hashlib.sha256(data).hexdigest());self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):row['clientDisconnected']=True
   except Exception:row['error']=traceback.format_exc();self.send_error(500)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
 import playwright._impl._transport as transport
 transport.compute_driver_executable=lambda:(str(NODE),str(O/'capture-driver/cli.js'))
 from playwright.async_api import async_playwright
 complete=False;fatal_acquisition=False
 try:
  pw=await asyncio.wait_for(async_playwright().start(),30)
  try:
   for engine in ['chromium','firefox']:
    browser=await asyncio.wait_for(getattr(pw,engine).launch(headless=True,executable_path=EXES[engine]),30);OWNED=merge_owned(OWNED,owned_processes())
    sequence=[(scene,side,False) for scene in SCENES for side in 'AB']+[('day','B',True)] if engine=='chromium' else [('day','B',True)]
    try:
     for scene,side,resource in sequence:
      sid=f'{engine}-{scene}-{side}'+('-resources' if resource else '');sd=DEST/sid;sd.mkdir();active.update(id=sid,scene=scene,side=side,instant=datetime.datetime.fromisoformat(SCENES[scene].replace('Z','+00:00')))
      slot={'id':sid,'engine':engine,'browserVersion':browser.version,'scene':scene,'side':side,'errors':[],'boundaries':[],'resources':{},'status':'ACQUIRING'};record['slots'].append(slot);save(DEST/'RESULTS.json',record)
      slot['resourceOnly']=resource
      ctx=await asyncio.wait_for(browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference'),15);page=await asyncio.wait_for(ctx.new_page(),15);profiler=NativeProfiler(engine) if engine=='chromium' else None
      release=asyncio.Event();start=time.perf_counter()
      async def route(r):
       u=r.request.url
       if u in fonts:
        v=fonts[u];p=FONTS/v['file'];assert sha(p)==v['sha256'];return await r.fulfill(body=p.read_bytes(),content_type=v['contentType'],headers={'access-control-allow-origin':'*'})
       if u.startswith(origin+'/'):
        if resource and urlsplit(u).path.endswith('/real-sky/native-sky.js'):await release.wait()
        return await r.continue_()
       slot['errors'].append('Unexpected external '+u);await r.abort()
      async def mark(label):
       value=await page.evaluate('(label)=>window.__r21.mark(label)',label);slot['boundaries'].append(value);return value
      async def snapshot(label):
       await mark('observer.'+label+'.before');value=await page.evaluate('window.__r21.snapshot()');await mark('observer.'+label+'.after');return value
      async def wait_for(js,seconds=30):return await page.wait_for_function(js,timeout=seconds*1000,polling=100)
      async def admitted_final():
       end=time.perf_counter()+360
       while time.perf_counter()<end:
        state=await page.evaluate('()=>{window.__r21.mark("observer.ready-poll.before");try{return {ready:window.__r21.ready(),recorder:window.__r21.status(),moon:window.SalahMoonRuntime?.state,sky:window.SalahRealSky?.state};}finally{window.__r21.mark("observer.ready-poll.after");}}')
        if state['recorder']['invalid']:raise RuntimeError('INCOMPLETE native marker recorder invalid/capacity')
        if state['ready']['ready']:
         if side=='B':
          q=state['moon']['last']['quality'];assert q['status']=='empirical-adaptive' and q['projectedGate']==.5 and q['projectedMaximumCode']<=.5 and q['unsettled']==0,'Current final quality gate'
         return
        if state.get('moon',{}).get('status')=='unavailable' or state.get('sky',{}).get('status')=='unavailable':raise RuntimeError('Unexpected product failure before final: '+json.dumps({'moon':state.get('moon',{}).get('errors'),'sky':state.get('sky',{}).get('errors')}))
        await asyncio.sleep(.25)
       raise TimeoutError('INCOMPLETE final observation; source deadlines unchanged')
      try:
       async with asyncio.timeout(540):
        await ctx.route('**/*',route)
        settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
        await ctx.add_init_script('localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
        await ctx.add_init_script("(()=>{const D=Date,t=D.parse("+json.dumps(SCENES[scene])+"),s=D.now();window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();")
        await ctx.add_init_script("(()=>{const f=window.fetch.bind(window),hosts=new Set(['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io']);window.fetch=(input,init)=>{const u=new URL(typeof input==='string'?input:input.url,location.href);return f(hosts.has(u.hostname)?"+json.dumps(origin)+"+'/fixture?url='+encodeURIComponent(u.href):input,init);};})();")
        probe=(C/'probe-r123.js').read_text(encoding='utf-8')
        if engine=='firefox':probe+="\nwindow.__r21.enter=()=>-1;window.__r21.leave=()=>{};window.__r21.caught=()=>{};"
        resource_probe=(C/'resource-controls-r123.js').read_text(encoding='utf-8') if resource else '''(()=>{const noop=()=>{};window.__r21Resources={register:noop,reaction:noop,reactionComplete:noop,export:()=>({resourceControlInstalled:false})};const decode=HTMLImageElement.prototype.decode;HTMLImageElement.prototype.decode=function(){const token=window.__r21.enter('image.decodeInitiation');try{return decode.call(this);}finally{window.__r21.leave(token);}};})();'''
        await ctx.add_init_script(probe+'\n'+resource_probe+'\nwindow.__r21Document=window.__r21.mark('+json.dumps('document/'+sid)+');')
        page.on('pageerror',lambda e:slot['errors'].append(str(e)))
        if profiler:slot['profileStart']=await profiler.start(ctx,page)
        await page.goto(origin+'/salah_widget/#local=1&motion=full',wait_until='commit')
        await wait_for("()=>window.SalahNativeSkyHost?.capture(false)?.weather?.cloud==="+('35' if scene=='day' else '0'))
        slot['weatherAdmitted']=await snapshot('weather');await mark('weather.admitted');await asyncio.sleep(1);await mark('weather.unchanged-control');slot['unchangedWeather']=await page.evaluate('window.SalahNativeSkyHost.capture(false).weather')
        if resource:
         await wait_for("()=>window.SalahSkyPreview?.state.status==='ready'&&window.__r21.readOwner('preview')?.solarPublication?.displayed?.image")
         slot['resources']['previewBefore']=await page.evaluate("window.__r21Resources.snapshot('preview.before')")
         slot['resources']['previewCycles']=[]
         for i in range(3):slot['resources']['previewCycles'].append(await page.evaluate('(i)=>window.__r21Resources.run("preview",i)',i));save(sd/'PARTIAL.json',slot)
         slot['resources']['previewDispose']=await page.evaluate('window.__r21Resources.run("preview",3,true)');slot['resources']['previewAfter']=await page.evaluate("window.__r21Resources.snapshot('preview.after')")
         release.set()
        await admitted_final()
        slot['ready']=await snapshot('ready');await mark('final.admitted');await page.screenshot(path=str(sd/'final-before-controls.png'))
        if resource:
         slot['resources']['skyBefore']=await page.evaluate("window.__r21Resources.snapshot('sky.before')");slot['resources']['skyCycles']=[]
         for i in range(3):slot['resources']['skyCycles'].append(await page.evaluate('(i)=>window.__r21Resources.run("sky",i)',i));save(sd/'PARTIAL.json',slot)
         slot['resources']['skyDispose']=await page.evaluate('window.__r21Resources.run("sky",3,true)');slot['resources']['skyAfter']=await page.evaluate("window.__r21Resources.snapshot('sky.after')")
         slot['resources']['events']=await page.evaluate('window.__r21Resources.export()')
        else:
         # Existing explicit clock API produces a real changed minute/geometry job.
         await mark('minute-geometry.before');slot['clockControl']=await page.evaluate('window.SalahClock.set({rate:1,utcMs:window.SalahNativeSkyHost.capture(false).utcMs+60000})');await admitted_final();await mark('minute-geometry.after');slot['afterMinute']=await snapshot('afterMinute')
        if profiler:slot['overhead']=await page.evaluate('window.__r21.overhead()')
        slot['documentReadback']=await page.evaluate('({url:location.href,mark:window.__r21Document,timeOrigin:performance.timeOrigin})')
        raw=await page.evaluate("()=>{const cut=window.__r21.mark('export.cut');return {...window.__r21.export(),cut};}");save(sd/'CALLS.json',raw)
        if raw['invalid'] or raw['depth']:slot['errors'].append('Native marker recorder invalid or open stack')
        if profiler:slot['profileStop']=await profiler.stop(sd/'PROFILE.json')
        slot['status']='RETURNED_FOR_REVIEW' if not slot['errors'] else 'INCOMPLETE_BROWSER_ERROR'
      except Exception as e:
       slot.update(status='INCOMPLETE_STOP',failure=traceback.format_exc())
       if not str(e).startswith('Unexpected product failure'):fatal_acquisition=True
      finally:
       release.set()
       try:slot['lastState']=await asyncio.wait_for(page.evaluate('window.__r21.snapshot()'),10)
       except Exception as e:slot['lastStateError']=str(e)
       if not (sd/'CALLS.json').exists():
        try:
         raw=await asyncio.wait_for(page.evaluate("()=>{const cut=window.__r21.mark('export.cut');return {...window.__r21.export(),cut};}"),10);save(sd/'FAILURE-CALLS.json',raw)
         if raw['invalid'] or raw['depth']:fatal_acquisition=True;slot['errors'].append('Failure-export marker recorder invalid or open stack')
         slot['documentReadback']=await asyncio.wait_for(page.evaluate('({url:location.href,mark:window.__r21Document,timeOrigin:performance.timeOrigin})'),10)
         slot['partialResources']=await asyncio.wait_for(page.evaluate('window.__r21Resources.export()'),10)
        except Exception as e:slot['partialEvidenceError']=str(e)
       if profiler and profiler.active:
        try:slot['cleanupProfile']=await asyncio.wait_for(profiler.stop(sd/'CLEANUP-PROFILE.json'),20)
        except Exception as e:slot['cleanupProfileError']=str(e)
       OWNED=merge_owned(OWNED,owned_processes())
       try:await asyncio.wait_for(ctx.close(),15);slot['contextClosed']=True
       except Exception as e:slot.update(contextClosed=False,contextCloseError=str(e),status='INCOMPLETE_CLEANUP')
       slot['elapsedMs']=(time.perf_counter()-start)*1000;save(sd/'SLOT.json',slot);save(DEST/'RESULTS.json',record);print(json.dumps({'slot':sid,'status':slot['status']}),flush=True)
      if slot['status']!='RETURNED_FOR_REVIEW':
       record.setdefault('stoppedPaths',[]).append({'engine':engine,'after':sid,'reason':slot['status']})
       if slot['errors'] or not slot.get('contextClosed') or slot.get('cleanupProfileError') or slot.get('partialEvidenceError'):fatal_acquisition=True
       if side=='A' and not resource and not fatal_acquisition:continue
       break
    finally:
     try:await asyncio.wait_for(browser.close(),15)
     except Exception as e:record.setdefault('browserCloseErrors',[]).append(str(e));fatal_acquisition=True
    if fatal_acquisition:record['acquisitionStopped']=True;break
  finally:
   try:await asyncio.wait_for(pw.stop(),10);record['playwrightStopped']=True
   except Exception as e:record.update(playwrightStopped=False,playwrightStopError=str(e))
  complete=True
 finally:
  server.shutdown();server.server_close();record['requests']=requests;record['payloads']=payloads;OWNED=merge_owned(OWNED,owned_processes());record['ownedProcesses']=OWNED;record['ownedCleanup']=reap_owned(OWNED);record['runtimeUnchanged']={s:record['runtime'][s]==runtime_identity(p) for s,p in ROOTS.items()};record['inputsUnchanged']=record['inputs']==inputs()
  valid=complete and len(record['slots'])==8 and all(s['status']=='RETURNED_FOR_REVIEW' and s.get('contextClosed') for s in record['slots']) and all(record['runtimeUnchanged'].values()) and record['inputsUnchanged'] and record.get('playwrightStopped') and record['ownedCleanup']['verified'] and not record.get('browserCloseErrors') and not any(r.get('error') for r in requests)
  record['status']='RETURNED_FOR_REVIEW' if valid else 'INCOMPLETE';save(DEST/'RESULTS.json',record)

if __name__=='__main__':
 if '--prepare' in sys.argv:save(C/'r123-INPUTS.json',{'inputs':inputs(),'scenes':SCENES,'sequence':'Six ordinary Chromium night/twilight/day A/B events; separate one day B resource case per engine. One observation per slot; no steady ABBA. Resource interventions and observer-marked snapshot intervals are excluded from matched event comparisons. Minute/solar-geometry control is not a coordinate-target or DPR change.','limits':{'caseSeconds':540,'decodeSettlementSeconds':10,'cyclesPerActiveOwner':3,'extra':'one terminal clear/dispose pending boundary perowner, without recovery; cleanup calls bounded10/15/20s'},'status':'PREPARED_NOT_ADMITTED'});print('prepared')
 else:
  admission=json.loads((C/'r123-ADMISSION.json').read_bytes());assert admission['inputs']==inputs() and admission['status']=='SUPPORTED_EXACT_FINITE_GROUP';assert not DEST.exists(),'No repeat'
  lock=O/'native-resource.lock'
  with lock.open('x') as f:f.write('events-resources-r123')
  interrupted=False
  try:asyncio.run(run())
  except BaseException:
   interrupted=True;DEST.mkdir(parents=True,exist_ok=True);save(DEST/'OUTER-FAILURE.json',{'status':'INCOMPLETE','error':traceback.format_exc()})
  finally:
   DEST.mkdir(parents=True,exist_ok=True);OWNED=merge_owned(OWNED,owned_processes());cleanup=reap_owned(OWNED)
   result=json.loads((DEST/'RESULTS.json').read_bytes()) if (DEST/'RESULTS.json').exists() else {}
   cleanup.update(knownOwnedProcesses=OWNED,interrupted=interrupted,innerCleanupVerified=result.get('ownedCleanup',{}).get('verified') is True)
   release=not interrupted and cleanup['verified'] and cleanup['innerCleanupVerified'];cleanup['lockReleased']=release
   if release and lock.read_text()=='events-resources-r123':lock.unlink()
   save(DEST/'FINAL-CLEANUP.json',cleanup)
   print(json.dumps({'status':result.get('status','INCOMPLETE'),'slots':len(result.get('slots',[])),'lockReleased':release}),flush=True)
