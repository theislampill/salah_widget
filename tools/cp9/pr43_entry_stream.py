"""Actual generated-entry stream controls, isolated settings and controlled providers.

The held-tail case is a causal diagnostic, not a measurement of ordinary latency.
It serves unchanged entry bytes and observes real settings/provider consumers.
"""
import argparse, asyncio, gzip, hashlib, http.server, json, os, sys, threading, time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,urlencode
from playwright.async_api import async_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
from v1_browser import fixture,SETTINGS,ROOT_KEY

SNAPSHOT="""() => {
 const box=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
 return {at:performance.now(),readyState:document.readyState,mainDeclared:typeof boot==='function',
  card:box(document.querySelector('.c')),settings:!!document.querySelector('.buckle.interactive'),
  settingsOpen:!!document.querySelector('.c.settings-open'),
  prayerRows:[...document.querySelectorAll('.times .p')].map(x=>x.textContent),
  requests:window.__entryFixture.requests,firstPaint:window.SalahFirstPaint?.preparedAt??null,
  headScene:window.SalahFirstPaint?{error:window.SalahFirstPaint.error??null,utcMs:window.SalahFirstPaint.snapshot?.utcMs,
   moon:window.SalahFirstPaint.moon?{visible:window.SalahFirstPaint.moon.visible,geometry:window.SalahFirstPaint.moon.geometry,
    native:window.SalahFirstPaint.moon.moon,presentation:window.SalahFirstPaint.moon.presentation,quality:window.SalahFirstPaint.moon.quality}:null,
   hasBackground:getComputedStyle(document.querySelector('.c')).backgroundImage!=='none'}:null,
  moon:window.SalahMoonRuntime?.state??null,sky:window.SalahSkyPreview?.state??null,
  moonDetail:window.SalahMoonDetail?.state??null,
  fonts:[...document.fonts].map(f=>({family:f.family,status:f.status})),
  navigation:performance.getEntriesByType('navigation').map(x=>x.toJSON())};
}"""
def write(p,data):p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()

async def run(a):
 a.out.mkdir(parents=True,exist_ok=False)
 identity=runtime_identity(a.root);entry=(a.root/'index.html').read_bytes()
 allowed={'/'+name for name in identity['files']}
 marker=b'<script id="moon-refinement-code">'
 boundary='complete-entry'
 if a.mode=='held-tail':
  if entry.count(marker)==1:
   cut=entry.index(marker)+len(marker)+128;boundary='independent-refinement-source-after-native-core'
  else:
   marker=b'const text=atob('
   assert entry.count(marker)==1,'Exact reviewed initial payload boundary required'
   cut=entry.index(marker)+len(marker)+128;boundary='reviewed-inline-payload-before-native-boot'
 elif a.mode=='held-core':
  marker=b'\nboot();\n</script>'
  assert entry.count(marker)==1,'Exact generated native core terminator required'
  cut=entry.index(marker);boundary='core-script-incomplete-after-card-markup'
 else:cut=len(entry)
 compressed=gzip.compress(entry,mtime=0)
 release=threading.Event();sent=threading.Event();requests=[];errors=[]
 stamp='2026-09-25T02:00:00Z' if a.scene=='night' else '2026-09-25T17:00:00Z'
 def provider(url):
  value=fixture(url,a.scene=='night');host=urlsplit(url).hostname
  if host=='api.aladhan.com':
   date=urlsplit(url).path.rstrip('/').split('/')[-1];day,month,year=date.split('-')
   value['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year)
   hd=11+(datetime(int(year),int(month),int(day))-datetime(2026,9,24)).days
   assert 1<=hd<=30
   value['data']['date']['hijri'].update(day=str(hd),month={'number':4,'en':'Rabi al-Thani'},year='1448')
   value['data']['meta']['timezone']='America/New_York'
   value['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
  elif host=='api.open-meteo.com':
   local=datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(timezone(timedelta(hours=-4)))
   value.update(latitude=28.5383,longitude=-81.3792,elevation=0,timezone='America/New_York',utc_offset_seconds=-14400)
   value['current'].update(time=local.strftime('%Y-%m-%dT%H:%M'),interval=900,weather_code=0,cloud_cover=0,cloud_cover_low=0,cloud_cover_mid=0,cloud_cover_high=0,precipitation=0,rain=0,visibility=20000)
   value['current_units']={'time':'iso8601','interval':'seconds','temperature_2m':'°C','apparent_temperature':'°C','dew_point_2m':'°C','wind_speed_10m':'m/s','precipitation':'mm','rain':'mm','showers':'mm','snowfall':'cm'}
  elif host in ['get.geojs.io','ipinfo.io']:
   value={'latitude':'28.5383','longitude':'-81.3792','loc':'28.5383,-81.3792','city':'Orlando fixture','country':'United States','country_code':'US','timezone':'America/New_York'}
  return value
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,p):return str(a.root/urlsplit(p).path.lstrip('/'))
  def send(self,data,kind='application/json'):
   self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  def do_GET(self):
   path=urlsplit(self.path).path;requests.append({'path':self.path,'wall':time.time()})
   try:
    if path=='/fixture':self.send(json.dumps(provider(parse_qs(urlsplit(self.path).query)['url'][0])).encode());return
    if path=='/index.html':
     payload=compressed if a.mode=='compressed' else entry
     self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
     self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','public, max-age=3600')
     if a.mode=='compressed':self.send_header('Content-Encoding','gzip')
     self.end_headers()
     if a.mode in ['held-tail','held-core']:
      self.wfile.write(payload[:cut]);self.wfile.flush();sent.set()
      if not release.wait(45):return
      self.wfile.write(payload[cut:]);self.wfile.flush()
     elif a.kib_per_second:
      size=8192
      for at in range(0,len(payload),size):
       part=payload[at:at+size];self.wfile.write(part);self.wfile.flush();time.sleep(len(part)/(a.kib_per_second*1024))
     else:self.wfile.write(payload)
     return
    if path not in allowed:self.send_error(404);return
    super().do_GET()
   except (BrokenPipeError,ConnectionResetError):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 origin='http://127.0.0.1:'+str(server.server_port)
 report={'schema':'pr43-actual-entry-stream/1','mode':a.mode,'scene':a.scene,'runtime':identity,'entrySha256':sha(entry),'harnessSha256':sha(Path(__file__).read_bytes()),'decodedEntryBytes':len(entry),'gzipEntityBytes':len(compressed),'heldDecodedBoundary':cut,'boundaryKind':boundary,'controlledKiBPerSecond':a.kib_per_second,'scope':'Actual unchanged entry; synthetic provider/clock and private Map. Held boundary is a causal regression, not ordinary performance or physical presentation qualification.'}
 settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
 init="""(() => {
 const D=Date,origin=D.now(),stamp=D.parse(STAMP),values=new Map([[KEY,SETTINGS]]);
 Object.defineProperty(window,'localStorage',{value:{getItem:k=>values.get(String(k))??null,setItem:(k,v)=>values.set(String(k),String(v)),removeItem:k=>values.delete(String(k))}});
 window.Date=class extends D{constructor(...a){super(...(a.length?a:[stamp+D.now()-origin]));}static now(){return stamp+D.now()-origin;}};
 window.__entryFixture={requests:[]};const fetch0=window.fetch.bind(window);
 window.fetch=(input,options)=>{const u=new URL(typeof input==='string'?input:input instanceof URL?input.href:input.url,location.href);window.__entryFixture.requests.push({url:u.href,at:performance.now()});
 return fetch0(u.origin!==location.origin&&['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io'].includes(u.hostname)?ORIGIN+'/fixture?url='+encodeURIComponent(u.href):input,options);};
 })();""".replace('STAMP',json.dumps(stamp)).replace('KEY',json.dumps(ROOT_KEY)).replace('SETTINGS',json.dumps(json.dumps(settings))).replace('ORIGIN',json.dumps(origin))
 os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 try:
  async with async_playwright() as p:
   browser=await launch_browser(p);report['browser']=browser_identity(browser)
   options=dict(viewport={'width':390,'height':600},device_scale_factor=a.dpr,timezone_id='America/New_York',reduced_motion='no-preference')
   # This retained Firefox protocol lacks Browser.setVideoRecordingOptions.
   # Preserve its native screenshots; do not replace the selected engine.
   if os.environ.get('SALAH_BROWSER')!='firefox':options['record_video_dir']=str(a.out/'video')
   report['videoCapture']='chromium-native' if 'record_video_dir' in options else 'unsupported-firefox-protocol; screenshots retained'
   context=await browser.new_context(**options)
   await context.add_init_script(init);page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   try:
    params={'local':'1','motion':'full'}
    if a.moon is not None:params.update(simMoon=str(a.moon),simWax='0' if a.waning else '1',simMoonAlt=str(a.moon_alt),simMoonH='42')
    report['parameters']=params;report['scenario']=a.scenario
    url=origin+'/index.html#'+urlencode(params)
    if a.scenario!='cold':
     assert a.mode not in ['held-tail','held-core'],'held transfer is a cold causal boundary'
     await page.goto(url,wait_until='load',timeout=90000)
     await page.wait_for_function("window.SalahMoonRuntime?.state && document.querySelector('.times .tm')?.textContent.includes(':')",timeout=45000)
     report['prime']=await page.evaluate(SNAPSHOT)
     if a.scenario=='new-document':
      await page.close();page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
      await page.goto(url,wait_until='commit',timeout=90000)
     else:await page.reload(wait_until='commit',timeout=90000)
    else:await page.goto(url,wait_until='commit',timeout=90000)
    if a.mode in ['held-tail','held-core']:
     assert await asyncio.to_thread(sent.wait,10),'Server did not deliver held prefix'
     await page.wait_for_selector('.c',state='attached',timeout=15000)
     await page.wait_for_timeout(1500)
     report['whileHeld']=await page.evaluate(SNAPSHOT);await page.screenshot(path=str(a.out/'while-held.png'))
     if report['whileHeld']['settings']:
      await page.locator('.buckle.interactive').click();report['heldSettingsInteraction']=await page.evaluate("({open:!!document.querySelector('.c.settings-open'),role:document.querySelector('#settings')?.getAttribute('role'),expanded:document.querySelector('.buckle')?.getAttribute('aria-expanded')})")
      # Opening focuses the first field asynchronously. Use the actual close
      # control, then verify restoration before retaining scene captures.
      await page.locator('#setClose').click()
      await page.wait_for_function("!document.querySelector('.c.settings-open')")
      report['heldSettingsClosed']=True
     release.set()
    await page.wait_for_function("window.SalahMoonRuntime?.state && window.__entryFixture.requests.some(x=>x.url.includes('api.aladhan.com')) && /[0-9]{1,2}:[0-9]{2}/.test(document.querySelector('.times .tm')?.textContent??'')",timeout=45000)
    await page.wait_for_function("document.readyState!=='loading' && window.SalahMoonRuntime.state.status!=='waiting-refinement-source'",timeout=45000)
    report['afterRelease']=await page.evaluate(SNAPSHOT);await page.screenshot(path=str(a.out/'after-release.png'))
    if a.wait_final:
     await page.wait_for_function("window.SalahMoonRuntime?.state.visibleSource==='refined-terrain'",timeout=240000)
     report['finalRefinement']=await page.evaluate(SNAPSHOT);await page.screenshot(path=str(a.out/'final-refinement.png'))
    report['status']='OBSERVATIONS_REQUIRING_REVIEW'
    if a.mode=='held-tail':
     held=report['whileHeld'];checks={'nativeMainBeforeTail':held['mainDeclared'],'settingsBeforeTail':held['settings'],
      'prayerBeforeTail':len(held['prayerRows'])==6 and any('api.aladhan.com' in x['url'] for x in held['requests']) and any('06:21' in x or '6:21' in x for x in held['prayerRows']),
      'settingsInteractionBeforeTail':report.get('heldSettingsInteraction',{}).get('open') is True,'noPageErrors':not errors}
     report['controls']=checks;report['causalPass']=all(checks.values())
    elif a.mode=='held-core':
     head=report['whileHeld']['headScene'];report['controls']={'coreStillHeld':not report['whileHeld']['mainDeclared'],
      'actualHeadBackground':bool(head and head['hasBackground']),'coherentNativeMoon':bool(head and head['moon'] and (a.scene=='day' or head['moon']['visible'])),'noPageErrors':not errors}
     report['causalPass']=all(report['controls'].values())
   finally:await context.close();await browser.close()
 except Exception as e:report.update(status='HARNESS_OR_READINESS_FAILURE',error=str(e))
 finally:
  release.set();server.shutdown();report.update(pageErrors=errors,requests=requests,runtimeUnchanged=runtime_identity(a.root)==identity);write(a.out/'results.json',report)
 print(json.dumps({k:report.get(k) for k in ['status','error','pageErrors','decodedEntryBytes','gzipEntityBytes','runtimeUnchanged']}),flush=True)
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
 parser.add_argument('--mode',choices=['held-tail','held-core','compressed','ordinary'],default='held-tail');parser.add_argument('--scene',choices=['night','day'],default='night');parser.add_argument('--kib-per-second',type=float,default=0);parser.add_argument('--dpr',type=float,default=1)
 parser.add_argument('--moon',type=float);parser.add_argument('--waning',action='store_true');parser.add_argument('--moon-alt',type=float,default=20);parser.add_argument('--wait-final',action='store_true')
 parser.add_argument('--scenario',choices=['cold','reload','new-document'],default='cold')
 args=parser.parse_args();report=asyncio.run(run(args))
 # A retained capture or zero browser exception count cannot turn a failed
 # consumer control into success. Visual and S1 review still remain separate.
 passed=report.get('status')=='OBSERVATIONS_REQUIRING_REVIEW' and report.get('runtimeUnchanged') is True and not report.get('pageErrors')
 if args.mode.startswith('held-'):passed=passed and report.get('causalPass') is True
 if args.wait_final:
  final=report.get('finalRefinement',{});moon=final.get('moon',{})
  passed=passed and moon.get('current') is True and moon.get('visibleSource')=='refined-terrain' and final.get('settingsOpen') is False
 raise SystemExit(0 if passed else 1)
