"""Bounded actual Pages readback; original qualification is not repeated here."""
from pathlib import Path
import ast, asyncio, datetime, hashlib, json, math, os, sys, time, types
from urllib.parse import urlsplit, parse_qs

D = Path(__file__).resolve().parent
O = D.parent
R = Path('C:/Users/theis/.codex/worktrees/r0022-execution/salah_widget')
M = 'f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de'
URL = 'https://theislampill.github.io/salah_widget/'
CONTRACT = 'R0022-L1-H1-K003-H020-v1'
CAMERA = {'azDeg': 180, 'altDeg': 45, 'fovYDeg': 90, 'rollDeg': 0}

def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p, value): p.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def finite(x): return isinstance(x, (int, float)) and math.isfinite(x)
def checked_pins(pins):
    rows = []
    for p, want in pins['files'].items():
        try: got = sha(Path(p))
        except Exception as e: got = repr(e)
        rows.append({'path': p, 'sha256': got, 'match': got == want})
    return {'atUtc': now(), 'rows': rows, 'allMatch': all(x['match'] for x in rows)}

READOUT = r'''()=>{
 const box=e=>{if(!e)return null;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,width:r.width,height:r.height,visibility:s.visibility,opacity:s.opacity};};
 const stats=a=>{if(!a)return null;let positive=0,sum=0,max=0,nonfinite=0;for(const v of a){if(!Number.isFinite(v))nonfinite++;if(v>0)positive++;sum+=v;max=Math.max(max,v);}return {length:a.length,positive,sum,max,nonfinite};};
 const per=r=>r?{physical:r.physicalState,exposure:r.effectiveExposure,lunar:r.lunarDisplayPresentation??null,raw:stats(r.lunarBackgroundLinear),mapped:stats(r.lunarNightDisplayLinear),rawSky:stats(r.physicalSkyBackgroundLinear),solar:stats(r.solarBackgroundLinear),stellar:stats(r.stellarLinear),diffuse:stats(r.diffuseLinear),drawn:r.drawn}:null;
 const captureDateBefore=Date.now(),native=window.SalahNativeSkyHost?.capture(false),captureDateAfter=Date.now();
 // Exact field sequence from the pinned nativeIdentity source; no render mutation.
 const s=native,identity=s?JSON.stringify([s.sceneIdentity,s.generation,s.lat,s.lon,s.heightM,s.camera,s.weather,s.lp,s.reducedMotion,s.allowEstimates!==false,s.units,s.tz??null,s.timeScale??1,s.elevationSource??null,s.elevationOwner??null]):null;
 return {url:location.href,at:performance.now(),captureDateBefore,captureDateAfter,native,identity,sky:window.realSkyState?.(),moon:window.SalahMoonRuntime?.state,qa:window.qaState?.(),display:{refined:per(window.realSkyFrame?.()?.raster),preview:per(window.SalahSkyPreview?.frame?.raster)},card:box(document.querySelector('.c')),detail:box(document.querySelector('.moon-detail-canvas')),prayerRows:[...document.querySelectorAll('.times .p')].map(e=>e.textContent),weatherInformation:document.querySelector('#weather-information')?.textContent,classes:document.querySelector('.c')?.className,dpr:devicePixelRatio,viewport:[innerWidth,innerHeight]};
}'''

def predicates(row):
    f = row.get('final') or {}; n = f.get('native') or {}; sky = f.get('sky') or {}
    display = sky.get('displayed') or {}; ref = (f.get('display') or {}).get('refined') or {}
    composition = (sky.get('last') or {}).get('composition') or {}; qa = f.get('qa') or {}
    moon = f.get('moon') or {}; card = f.get('card') or {}; truth = qa.get('wxTruth') or {}
    weather = n.get('weather') or {}; lunar = ref.get('lunar') or {}; physical = ref.get('physical') or {}
    settings = row.get('settings') or {}; scene = row['scene']; rain = scene == 'rain'
    stored = settings.get('storedAfter') or {}; intended = row['settingsIntended']
    utc = n.get('utcMs'); displayed = display.get('utcMs'); bounds = row.get('readoutClockBounds') or [None, None]
    def array_ok(key):
        x = ref.get(key) or {}
        return x.get('length') == 325*530*3 and x.get('nonfinite') == 0 and finite(x.get('sum')) and finite(x.get('max'))
    relevant_failures = [x for x in row['requestFailures'] if urlsplit(x['url']).hostname == 'theislampill.github.io' and urlsplit(x['url']).path.startswith('/salah_widget/')]
    checks = {
        'acquisitionComplete': not row['errors'],
        'actualPublicDocument': f.get('url', '').startswith(URL),
        'card325x530': card.get('width') == 325 and card.get('height') == 530,
        'viewportAndDpr': f.get('viewport') == [375, 800] and f.get('dpr') == row['dpr'],
        'nativeTarget': n.get('lat') == 28.5383 and n.get('lon') == -81.3792 and n.get('generation') == 0 and n.get('sceneIdentity') == '28.5383|-81.3792|America/New_York|wall',
        'clock1xAndTimezone': n.get('timeScale') == 1 and n.get('tz') == 'America/New_York',
        'utcFromNativeClock': finite(utc) and f['captureDateBefore'] <= utc <= f['captureDateAfter'],
        'utcMatchesAnchor': finite(utc) and all(finite(x) for x in bounds) and bounds[0] <= utc <= bounds[1],
        'camera': n.get('camera') == CAMERA,
        'currentDisplayedSky': sky.get('status') == 'ready' and (sky.get('availability') or {}).get('reason') == 'current-frame' and display.get('identity') == f.get('identity') and finite(displayed) and finite(utc) and abs(utc-displayed) <= 30000,
        'physicalUtcMatchesDisplayed': finite(displayed) and physical.get('utcMs') == displayed,
        'prayerReady': n.get('prayerReady') is True and len(f.get('prayerRows', [])) >= 5 and all(f.get('prayerRows', [])),
        'declaredWeather': weather.get('src') == 'current' and weather.get('code') == (63 if rain else 0) and weather.get('cloud') == (65 if rain else 0),
        'declaredModelPrecipitation': truth.get('rawCode') == (63 if rain else 0) and truth.get('modelPrecipMm') == (2 if rain else 0),
        'weatherInformation': bool(f.get('weatherInformation')),
        'settingsRoute': settings.get('closeVisible') is True and settings.get('visibleInputs', 0) > 0 and settings.get('closedAfter') is True and all(stored.get(k) == intended[k] for k in ['lat','lon','tz','label','method','units']),
        'actualDocumentAndBundleBytes': {'index.html','real-sky/native-sky.js','moon/moon-host.js'}.issubset({x['path'] for x in row['productResponses'] if x['match']}),
        'allObservedProductBytes': bool(row['productResponses']) and all(x['match'] for x in row['productResponses']),
        'noProductRequestFailure': not relevant_failures,
        'noObservationError': not row['observationErrors'],
        'noPageError': not row['pageErrors'],
        'singleCloudApplication': composition.get('cloudApplications') == 1,
        'finitePhysicalFields': all(array_ok(k) for k in ['raw','rawSky','stellar','diffuse']),
        'originalExposure': finite(ref.get('exposure')) and ref['exposure'] > 0 and display.get('exposure') == ref['exposure'],
        'ownedBrowserClosed': row['cleanup'].get('browserClosed') is True and row['cleanup'].get('contextClosed') is True,
        'pinsBeforeAfter': row.get('pinsBefore', {}).get('allMatch') is True and row.get('pinsAfter', {}).get('allMatch') is True,
    }
    if scene != 'day':
        checks.update(currentV5=moon.get('current') is True and not moon.get('legacyFallback') and (qa.get('moonTruth') or {}).get('surface', {}).get('status') == 'v5-terrain', rawLunarPositive=(ref.get('raw') or {}).get('positive', 0) > 0, mappedLunarPositive=(ref.get('mapped') or {}).get('positive', 0) > 0, exactNightWeight=lunar.get('nightWeight') == 1, cataloguePresent=(ref.get('stellar') or {}).get('positive',0)>0)
        checks['exactH1MetadataAndExposure'] = lunar.get('contract') == CONTRACT and lunar.get('owner') == 'native lunar atmosphere display' and lunar.get('kneeEnergy') == .003 and lunar.get('headroomEnergy') == .020 and lunar.get('physicalExposure') == ref.get('exposure') and array_ok('mapped')
    else:
        # The approved source returns no H1 mapping in the daytime domain.
        checks['dayDisplayGate'] = ref.get('lunar') is None and ref.get('mapped') is None and (physical.get('sun') or {}).get('altDeg', -90) > 0 and array_ok('solar') and (ref.get('solar') or {}).get('positive',0) > 0
    if rain: checks['cloudsActuallyComposed'] = composition.get('meanCloudAlpha', 0) > 0
    return checks

async def main():
    # All imported helpers, full runtime files and all retained driver implementation
    # members are verified before use, and again after each owned browser closes.
    pins = read(D/'CONSUMED-SOURCE-PINS.json')
    review = read(D/'CONSUMER-METHOD-REVIEW.json')
    assert review['status'] == 'ACCEPTED_BOUNDED_DELIVERY_METHOD' and review['scriptSha256'] == sha(Path(__file__)) and review['pinsSha256'] == sha(D/'CONSUMED-SOURCE-PINS.json')
    out = D/'native'; assert not out.exists(); out.mkdir()
    result = {'schema':'r0022-delivered-native-consumers/v2','startedAtUtc':now(),'merge':M,'scriptSha256':sha(Path(__file__)),'pinsSha256':sha(D/'CONSUMED-SOURCE-PINS.json'),'scope':'Actual public HTTPS product bytes; external-provider fixtures and anchored ordinary 1x only. Routes disable cache: no performance/startup timing credit. Original full-viewport PNGs and native final observations; no recording repair, every-paint or M0 claim. Fresh isolated managed test browsers; no personal browser interaction.','cells':[],'cleanup':False}
    before = checked_pins(pins); write(out/'pins-before.json', before); result['pinsBefore'] = before['allMatch']; write(out/'summary.json',result)
    assert before['allMatch'], 'Consumed-source drift before acquisition; retained'
    sys.path.insert(0,str(R/'tools/cp9')); sys.path.insert(0,str(R/'tests'))
    from browser_runtime import launch_browser, browser_identity
    from v1_browser import fixture, SETTINGS, ROOT_KEY
    from playwright.async_api import async_playwright
    import playwright._impl._transport as transport
    expected=read(O/'selected-r7/RUNTIME.json'); served=read(D/'served-runtime.json')
    assert served['allMatch'] and served['merge']==M
    result['runtime']=expected['treeSha256']
    adapter=O/'qualification/capture_qualified_r2.py'
    provider_node=next(n for n in ast.walk(ast.parse(adapter.read_text(encoding='utf-8'))) if isinstance(n,ast.FunctionDef) and n.name=='provider')
    assert read(O/'browser-lease.json')['status']=='FREE' and not(O/'native-resource.lock').exists()
    assert read(Path('C:/Users/theis/Documents/Codex/salah-rlgwo-execution-20261009/ACTIVE_LEDGER.json'))['resourceLeases']['heavy-browser']['status']=='FREE'
    assert read(Path('C:/Users/theis/.codex/work-products/r0024-execution-20261015/execution.json'))['heavyLease']['kind']=='FREE'
    lock=O/'native-resource.lock'; lock.write_text('r0022-delivered-consumers',encoding='utf-8')
    write(O/'browser-lease.json',{'status':'ACTIVE','owner':'R0022 root','leaseId':'r0022-delivered-consumers','scope':result['scope'],'startedAtUtc':now()})
    all_owned_closed=True
    try:
        for engine,dpr,scene,duration in [('chromium',1,'clear',30),('firefox',2,'rain',60),('chromium',1,'day',15)]:
            cell=out/(engine+'-'+scene); cell.mkdir()
            cap=read(Path(pins['capabilities'][engine]))['capability']; driver=cap['driver']
            transport.compute_driver_executable=lambda:(driver['node'],driver['cli'])
            os.environ['SALAH_BROWSER']=engine; os.environ['SALAH_BROWSER_EXECUTABLE']=cap['executable']; os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
            stamp='2026-09-25T17:00:00Z' if scene=='day' else '2026-09-25T02:00:00Z'
            wx,cloud=(63,65) if scene=='rain' else (0,0)
            settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
            ns={'fixture':fixture,'urlsplit':urlsplit,'parse_qs':parse_qs,'datetime':datetime.datetime,'timedelta':datetime.timedelta,'timezone':datetime.timezone,'time':time,'a':types.SimpleNamespace(scene=scene,prayer_delay=0,acquiring=False),'stamp':stamp,'wx':wx,'cloud':cloud}
            exec(compile(ast.Module(body=[provider_node],type_ignores=[]),str(adapter),'exec'),ns); provider=ns['provider']
            row={'engine':engine,'dpr':dpr,'scene':scene,'anchor':stamp,'declaredSeconds':duration,'capability':cap,'settingsIntended':settings,'frames':[],'providerFixtures':[],'productResponses':[],'requestFailures':[],'pageErrors':[],'observationErrors':[],'errors':[],'cleanup':{},'status':'ACQUIRING','pinsBefore':checked_pins(pins)}
            tasks=[]; browser=None; ctx=None; launch_attempted=False
            def save(): write(cell/'result.json',row)
            save()
            async def drain():
                # Stable bounded task batches; every failure is retained.
                batch=list(tasks)
                if batch:
                    done,pending=await asyncio.wait(batch,timeout=30)
                    if pending:
                        row['observationErrors'].append({'stage':'response-drain','pending':len(pending)})
                        for t in pending: t.cancel()
                    values=await asyncio.gather(*batch,return_exceptions=True)
                    for v in values:
                        if isinstance(v,BaseException): row['observationErrors'].append({'stage':'response-task','error':repr(v)})
            async with async_playwright() as pw:
                try:
                    assert row['pinsBefore']['allMatch'], 'Consumed-source drift'
                    launch_attempted=True; all_owned_closed=False
                    browser=await launch_browser(pw); row['browser']=browser_identity(browser)
                    ctx=await browser.new_context(viewport={'width':375,'height':800},device_scale_factor=dpr,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference')
                    async def external(route):
                        u=route.request.url; value=provider(u); row['providerFixtures'].append({'url':u,'value':value})
                        await route.fulfill(status=200,content_type='application/json',body=json.dumps(value))
                    for host in ['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io']: await ctx.route('https://'+host+'/**',external)
                    await ctx.add_init_script('if(location.origin==="https://theislampill.github.io")localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
                    clock=time.time()*1000; anchor=datetime.datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp()*1000
                    await ctx.add_init_script('(()=>{const D=Date,s='+str(clock)+',t=D.parse('+json.dumps(stamp)+');window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();')
                    async def observe(response):
                        u=urlsplit(response.url)
                        if u.hostname!='theislampill.github.io' or not u.path.startswith('/salah_widget/'): return
                        path=u.path[len('/salah_widget/'):] or 'index.html'
                        if path not in expected['files']: return
                        try:
                            body=await response.body(); want=expected['files'][path]; got=hashlib.sha256(body).hexdigest()
                            row['productResponses'].append({'url':response.url,'path':path,'status':response.status,'bytes':len(body),'sha256':got,'match':response.status==200 and len(body)==want['bytes'] and got==want['sha256']})
                        except Exception as e: row['observationErrors'].append({'path':path,'error':repr(e)})
                    ctx.on('response',lambda r:tasks.append(asyncio.create_task(observe(r))))
                    ctx.on('requestfailed',lambda r:row['requestFailures'].append({'url':r.url,'failure':r.failure}))
                    page=await ctx.new_page(); page.on('pageerror',lambda e:row['pageErrors'].append(str(e))); start=time.monotonic()
                    await page.goto(URL+'?r0022_delivery='+M+'#local=1&motion=full',wait_until='domcontentloaded',timeout=60000)
                    for index,target in enumerate([1,5,duration]):
                        await asyncio.sleep(max(0,target-(time.monotonic()-start)))
                        p=cell/f'original-{index:02}.png'; frame={'path':p.name,'requestedSeconds':target,'startSeconds':time.monotonic()-start,'status':'ATTEMPTED'}
                        row['frames'].append(frame); save()
                        try:
                            await page.screenshot(path=str(p),type='png',timeout=30000); frame.update(status='CAPTURED',sha256=sha(p))
                        finally:
                            frame['endSeconds']=time.monotonic()-start
                            if p.exists(): frame['retainedSha256']=sha(p)
                            save()
                    lower=anchor+time.time()*1000-clock
                    row['final']=await page.evaluate(READOUT)
                    row['readoutClockBounds']=[lower,anchor+time.time()*1000-clock]
                    save()
                    # Actual settings events; closing invokes native auto-save in this isolated profile.
                    await page.locator('.buckle').click()
                    await page.screenshot(path=str(cell/'settings.png'),type='png',timeout=30000)
                    row['settings']={'pngSha256':sha(cell/'settings.png'),'visibleInputs':await page.locator('input:visible,select:visible').count(),'closeVisible':await page.locator('#setClose').is_visible()}; save()
                    await page.locator('#setClose').click()
                    row['settings']['closedAfter']=await page.locator('#setClose').is_hidden()
                    row['settings']['storedAfter']=await page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))',ROOT_KEY)
                except Exception as e:
                    row['errors'].append({'atUtc':now(),'error':repr(e)})
                finally:
                    try: await drain()
                    except Exception as e: row['observationErrors'].append({'stage':'pre-close-drain','error':repr(e)})
                    if ctx is not None:
                        try: await ctx.close(); row['cleanup']['contextClosed']=True
                        except Exception as e: row['cleanup']['contextError']=repr(e)
                    if browser is not None:
                        try: await browser.close(); row['cleanup']['browserClosed']=True; all_owned_closed=True
                        except Exception as e: row['cleanup']['browserError']=repr(e)
                    elif not launch_attempted: all_owned_closed=True
                    try: await drain()
                    except Exception as e: row['observationErrors'].append({'stage':'post-close-drain','error':repr(e)})
                    row['pinsAfter']=checked_pins(pins)
                    # Preserve all completed PNGs even if a later observation failed.
                    row['retainedImages']=[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(cell.glob('*.png'))]
                    try: row['checks']=predicates(row)
                    except Exception as e: row['errors'].append({'stage':'predicates','error':repr(e)}); row['checks']={'predicateEvaluation':False}
                    row['status']='OBSERVATIONS_FOR_INDEPENDENT_REVIEW' if all(row['checks'].values()) else 'FAILED_RETAINED'
                    row['completedAtUtc']=now(); save()
            result['cells'].append({'path':str(cell.relative_to(D)),'resultSha256':sha(cell/'result.json'),'status':row['status'],'checks':row['checks']})
            write(out/'summary.json',result); print(json.dumps({'cell':cell.name,'status':row['status'],'failed':[k for k,v in row['checks'].items() if not v]}),flush=True)
            assert row['status']=='OBSERVATIONS_FOR_INDEPENDENT_REVIEW', 'Retained failure; stop for exact affected-predicate review'
        result['cleanup']=all_owned_closed; result['completedAtUtc']=now()
    except Exception as e:
        result['error']=repr(e); raise
    finally:
        result['cleanup']=all_owned_closed; write(out/'summary.json',result)
        write(O/'browser-lease.json',{'status':'FREE' if all_owned_closed else 'RECOVERY_REQUIRED','owner':None if all_owned_closed else 'R0022 root','leaseId':'r0022-delivered-consumers','finishedAtUtc':now(),'scope':'Owned browser close operations completed' if all_owned_closed else 'Owned launch/close unresolved; retain lease'})
        if all_owned_closed:
            assert lock.read_text(encoding='utf-8')=='r0022-delivered-consumers'; lock.unlink()

if __name__=='__main__': asyncio.run(main())
