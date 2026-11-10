"""Actual HTTP/index and file/offline observations; fixtures never count as live providers.

Runs one explicitly selected engine. Keep raw failures and partial BFCache/CSP
observations; platform_acceptance joins the three engines without inventing PASS.
"""
import argparse, functools, hashlib, http.server, json, platform, threading, time, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser, browser_identity, browser_options
from native_browser_check import ROOT, Quiet
from native_lifecycle_check import CLOCK
from native_pixel_probes import MATERIAL_PROBE, COMPOSITION_PROBE, install_composition_probe
from platform_acceptance import REQUIRED_CHECKS
from runtime_identity import runtime_identity

CSP = "default-src 'self'; script-src 'self' 'unsafe-inline' blob:; worker-src 'self' blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self' https://api.aladhan.com https://api.open-meteo.com https://geocoding-api.open-meteo.com https://nominatim.openstreetmap.org https://api.rainviewer.com https://tilecache.rainviewer.com"
class Server(Quiet):
    def end_headers(self):
        self.send_header('Content-Security-Policy', CSP)
        super().end_headers()
    def do_GET(self):
        if self.path == '/away':
            self.send_response(200); self.send_header('Content-Type','text/html'); self.end_headers(); self.wfile.write(b'<title>Navigation control</title>Navigation control')
        else: super().do_GET()

WATCH = r'''(() => {
 window.__csp=[];document.addEventListener('securitypolicyviolation',e=>__csp.push({directive:e.effectiveDirective,blocked:e.blockedURI}));
 window.__navigation=[];
 for(const name of ['pagehide','pageshow'])addEventListener(name,e=>{
  const row={name,persisted:e.persisted};__navigation.push(row);
  try{const a=JSON.parse(sessionStorage.getItem('cp9-navigation')||'[]');a.push(row);sessionStorage.setItem('cp9-navigation',JSON.stringify(a));}catch{}
 });
})();'''
SNAP = '''()=>({sky:window.realSkyState?.(),host:window.SalahNativeSkyHost?.capture(),qa:window.qaState?.(),rows:document.querySelectorAll('.p').length,visible:document.querySelector('.real-sky-canvas')?.style.visibility,canvasCount:document.querySelectorAll('.real-sky-canvas').length,synthetic:document.querySelectorAll('.stars circle,.milkyway circle,.starglints line').length,csp:window.__csp,navigation:window.__navigation})'''

def wait(page, expression, timeout=30000):
    # Protocol evaluation avoids Playwright's in-page string eval, which the CSP
    # correctly rejects. Do not loosen script-src to accommodate the harness.
    deadline=time.monotonic()+timeout/1000
    while time.monotonic()<deadline:
        if page.evaluate('() => ('+expression+')'): return
        page.wait_for_timeout(50)
    raise TimeoutError(expression)

def ready(page):
    wait(page,"document.querySelectorAll('.p').length===6&&window.realSkyState?.().status==='ready'", timeout=60000)
def current(state):
    sky, host = state.get('sky') or {}, state.get('host') or {}
    last=sky.get('last') or {}
    return sky.get('status')=='ready' and abs(last.get('utcMs',0)-host.get('utcMs',1e99))<=30000 and last.get('native',{}).get('generation')==host.get('generation') and last.get('observer',{}).get('latDeg')==host.get('lat')

def run(root, out):
    root=root.resolve();out.mkdir(parents=True,exist_ok=True);identity=runtime_identity(root)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Server,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start();records=[]
    fragment='#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&simTime=23:30&simWx=0&simCloud=0&simPrecip=0&qa=1&preferLocal=1'
    try:
        with sync_playwright() as p:
            family,options=browser_options()
            # Playwright's default Chromium launcher disables BFCache. Restore
            # the browser default for this actual-navigation observation only.
            if family=='chromium':options['ignore_default_args']=['--disable-back-forward-cache']
            browser=getattr(p,family).launch(**options);env={**browser_identity(browser),'platform':platform.platform(),'launchOptions':options}
            if family=='chromium':
                session=browser.new_browser_cdp_session();args=session.send('Browser.getBrowserCommandLine')['arguments'];session.detach()
                env['securityFlags']=[arg for arg in args if any(word in arg for word in ('sandbox','web-security','file-access','back-forward-cache'))]
            for form, base in [('http',f'http://127.0.0.1:{server.server_port}/index.html'),('file',(root/'offline.html').as_uri())]:
                name=env['family']+'-'+form;record={'schemaVersion':1,'recordId':name,'runtimeTreeSha256':identity['treeSha256'],'environment':env,'entry':{'form':form,'url':base},'checks':{}}
                raw={'runtimeTreeSha256':identity['treeSha256'],'environment':env,'url':base,'providerMode':'controlled fixture except separate live probe','checks':{},'requests':[],'pageErrors':[]}
                context=browser.new_context(viewport={'width':430,'height':640},reduced_motion='reduce');context.add_init_script(CLOCK);context.add_init_script(WATCH)
                page=context.new_page();page.on('pageerror',lambda e:raw['pageErrors'].append(str(e)));page.on('request',lambda q:raw['requests'].append(q.url))
                def check(key, body, mode='actual-entry'):
                    try:
                        data, passed=body();status='PASS' if passed else 'PARTIAL'
                        raw['checks'][key]={'status':status,'observation':data}
                    except Exception:
                        status='NOT_VERIFIED';raw['checks'][key]={'status':status,'error':traceback.format_exc()}
                    record['checks'][key]={'status':status,'mode':mode}
                    print(name,key,status,flush=True)
                def entry():
                    response=page.goto(base+fragment,wait_until='domcontentloaded',timeout=30000);ready(page)
                    s=page.evaluate(SNAP);page.locator('.c').screenshot(path=str(out/(name+'-clear.png')))
                    raw['responseCSP']=response.headers.get('content-security-policy') if response else None
                    return s,current(s) and s['rows']==6 and s['synthetic']==0 and not raw['pageErrors']
                check('entry',entry)
                check('material',lambda: ((r:=page.evaluate(MATERIAL_PROBE)),r['opaquePixels']>5000 and r['maxCodeDifference']<=1))
                def composition():
                    page.goto(base+fragment.replace('simWx=0&simCloud=0','simWx=2&simCloud=60'),wait_until='domcontentloaded');page.reload(wait_until='domcontentloaded');ready(page)
                    install_composition_probe(page,root);r=page.evaluate(COMPOSITION_PROBE);page.locator('.c').screenshot(path=str(out/(name+'-cloud.png')))
                    return r,r['maxCodeDifference']==0 and r['cloudOutsideDeclaredSupport']==0 and all(n>100 for n in r['mutations'].values())
                check('composition',composition)
                def seek():
                    a=page.evaluate(SNAP);page.evaluate('()=>{_simBase-=86400000;render();SalahRealSky.request(true);}');ready(page);b=page.evaluate(SNAP)
                    return {'before':a,'after':b},current(b) and b['sky']['last']['utcMs']==b['host']['utcMs'] and b['host']['utcMs']!=a['host']['utcMs']
                check('currentness',seek)
                def failure():
                    page.evaluate("()=>{window.__normalWorker=Worker;window.Worker=class{constructor(){throw new Error('Controlled worker creation failure');}};SalahRealSkyAssets.retry();}")
                    wait(page,"realSkyState()?.status==='unavailable'",timeout=30000);failed=page.evaluate(SNAP)
                    page.locator('#ceDateButton').click();wait(page,"document.querySelector('#dateDialog').open");page.locator('#dateClose').click()
                    page.evaluate('()=>{window.Worker=__normalWorker;SalahRealSkyAssets.retry();}');ready(page);recovered=page.evaluate(SNAP)
                    return {'failed':failed,'recovered':recovered},failed['rows']==6 and failed['sky']['last'] is None and failed['visible']!='visible' and current(recovered) and recovered['canvasCount']==1
                check('sourceFailure',failure)
                def calendar_settings():
                    page.locator('.buckle').click();wait(page,"document.querySelector('.c').classList.contains('settings-open')")
                    page.locator('#set-units').select_option('f');page.locator('#set-method').select_option('2');page.locator('#set-appearance').select_option('contrast');page.locator('#setClose').click();ready(page)
                    settings=page.evaluate('()=>({units:CONFIG.units,method:CONFIG.method,appearance:CONFIG.appearance,generation:_runtimeGeneration})')
                    states=[]
                    for utc in ['2026-09-07T15:32:59Z','2026-09-07T15:33:00Z','2026-09-07T20:59:59Z','2026-09-07T21:00:01Z']:
                        page.evaluate("utc=>{_simBase=Date.parse(utc);render();SalahRealSky.request(true);}",utc);ready(page)
                        wait(page,"qaState().dateTruth.loadedGregorianDay===qaState().dateTruth.requestedGregorianDay")
                        states.append(page.evaluate(SNAP))
                    a,b,c,d=[s['qa']['dateTruth'] for s in states]
                    page.locator('#ceDateButton').click();wait(page,"document.querySelector('#dateDialog').open");page.locator('#dateClose').click()
                    passed=settings['units']=='f' and settings['method']=='2' and a['selectedSource']=='today' and b['selectedSource']=='tomorrow' and b['hijriText']!=a['hijriText'] and d['gregorianText']=='2026-09-08' and d['hijriText']==b['hijriText'] and all(current(s) and s['rows']==6 for s in states)
                    return {'settings':settings,'states':states},passed
                check('prayerCalendarSettings',calendar_settings)
                def navigation():
                    before=page.evaluate(SNAP);page.goto(f'http://127.0.0.1:{server.server_port}/away',wait_until='load')
                    # A restored document does not fire DOMContentLoaded again.
                    # Drive the real history traversal and observe its destination
                    # and current native state, not a new-document load event.
                    page.evaluate('()=>history.back()')
                    deadline=time.monotonic()+30
                    while not page.url.startswith(base) and time.monotonic()<deadline:page.wait_for_timeout(50)
                    if not page.url.startswith(base):raise TimeoutError('Actual history traversal did not return to the widget')
                    ready(page)
                    after=page.evaluate(SNAP);events=page.evaluate("()=>{try{return JSON.parse(sessionStorage.getItem('cp9-navigation')||'[]')}catch{return __navigation}}")
                    reasons=page.evaluate("()=>performance.getEntriesByType('navigation')[0]?.notRestoredReasons?.toJSON?.()??null")
                    return {'before':before,'after':after,'events':events,'notRestoredReasons':reasons,'actualTraversal':True,'bfcacheObserved':any(e.get('name')=='pageshow' and e.get('persisted') for e in events)},current(after) and after['canvasCount']==1 and any(e.get('name')=='pageshow' and e.get('persisted') for e in events)
                check('navigation',navigation,'actual-navigation')
                nav=raw['checks']['navigation'];record['checks']['lifecycle']={'status':nav['status'],'mode':'actual-entry'};raw['checks']['lifecycle']={'status':nav['status'],'basis':'Actual pagehide/return and current worker recovery; complete BFCache restoration requires persisted pageshow.'}
                check('csp',lambda: ({'header':raw.get('responseCSP'),'violations':page.evaluate('window.__csp'),'scope':'HTTP response CSP; local file has no HTTP policy'},form=='http' and raw.get('responseCSP')==CSP and not page.evaluate('window.__csp')))
                context.close()
                # Fresh browser context with no Date, storage, provider or source overrides.
                def live():
                    c=browser.new_context(viewport={'width':430,'height':640},reduced_motion='reduce');q=c.new_page();requests=[];responses=[];failures=[];errors=[]
                    q.on('request',lambda r:requests.append(r.url));q.on('response',lambda r:responses.append({'url':r.url,'status':r.status}));q.on('requestfailed',lambda r:failures.append({'url':r.url,'failure':r.failure}));q.on('pageerror',lambda e:errors.append(str(e)))
                    try:
                        q.goto(base+'#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&qa=1',wait_until='domcontentloaded',timeout=30000)
                        q.wait_for_timeout(20000);s=q.evaluate(SNAP);q.locator('.c').screenshot(path=str(out/(name+'-live.png')))
                        # Preserve source metadata for review. Merely surviving network failure is insufficient for admission PASS.
                        data={'state':s,'requests':requests,'responses':responses,'failures':failures,'pageErrors':errors,'wallUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'observationMode':'unmodified live provider requests','admissionDisposition':'REQUIRES_REVIEW'}
                        host=s.get('host') or {};qa=s.get('qa') or {};date=qa.get('dateTruth') or {};wx=qa.get('wxTruth') or {};owner=host.get('elevationOwner') or {}
                        prayer=host.get('prayerReady') and date.get('staleDateState')=='current' and date.get('loadedGregorianDay')==date.get('requestedGregorianDay') and any('api.aladhan.com' in r['url'] and r['status']==200 for r in responses)
                        weather=wx.get('requests',{}).get('weather',{}).get('state')=='received' and owner.get('generation')==host.get('generation') and owner.get('lat')==host.get('lat') and owner.get('lon')==host.get('lon')
                        truthful=wx.get('permissions',{}).get('rain') is False and wx.get('permissions',{}).get('lightning') is False if not wx.get('present',{}).get('available') else True
                        data['admissionDisposition']='LIVE_PRAYER_AND_MODEL_WEATHER_ADMITTED' if prayer and weather else 'LIVE_UNAVAILABLE_OR_INCOMPLETE'
                        data['admissionAssertions']={'prayer':bool(prayer),'weatherAndElevationOwner':bool(weather),'unqualifiedPresentCannotEnableParticles':truthful}
                        return data,prayer and weather and truthful and s['rows']==6 and not errors
                    finally:c.close()
                check('providers',live,'live')
                record['sourceRequests']=raw['requests']
                rawpath=out/(name+'.json');rawpath.write_text(json.dumps(raw,indent=2),encoding='utf-8');digest=hashlib.sha256(rawpath.read_bytes()).hexdigest()
                for item in record['checks'].values():item.update(evidence=rawpath.name,sha256=digest)
                records.append(record);(out/'records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
            browser.close()
    finally:server.shutdown()
    return records

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);args=a.parse_args();run(args.root,args.output)
