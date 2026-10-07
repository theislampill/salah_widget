"""Bounded Windows browser test of the prospective root + frozen V1 iframe.

Uses installed browsers and preserved provider/font fixtures. The browser clock
runs at 1x from a controlled instant; no simTime/timeScale hash is supplied.
Requires the prospective merge containing PR41's tests/v1_browser.py.
"""
import argparse, functools, hashlib, http.server, json, shutil, sys, threading, time, traceback
from urllib.parse import urlsplit
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser, browser_identity
from moon_receiving_check import OBSERVER, MONITOR, STATE, wait, small_scene
from runtime_identity import runtime_identity


def run(root, out, font_source):
    sys.path.insert(0,str(root/'tests'))
    from v1_browser import fonts, fixture, SETTINGS, ROOT_KEY, V1_KEY, FONT_CSS
    out.mkdir(parents=True,exist_ok=True)
    shutil.copytree(font_source,out/'fonts',dirs_exist_ok=True);font_files=fonts(out)
    pages={}
    for name,src in [('root','/salah_widget/#local=1'),('v1','/salah_widget/v1/#local=1')]:
        pages['/'+name+'.html']='<!doctype html><meta charset="utf-8"><iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="'+src+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden" scrolling="no"></iframe>'
        (out/(name+'-iframe.html')).write_text(pages['/'+name+'.html'],encoding='utf-8')
    class Server(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_GET(self):
            if self.path in pages:
                b=pages[self.path].encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
            else:super().do_GET()
        def translate_path(self,path):
            assert path.startswith('/salah_widget/'),path
            return str(root/path.split('?',1)[0][len('/salah_widget/'):])
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Server);threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_port}'
    report={'status':'RUNNING','runtime':runtime_identity(root),'checks':{},'errors':[],'assetFailures':[],
            'scope':'Pages-shaped actual iframe; controlled providers/fonts/location and 1x clock from 2026-10-07T20:30Z. Not live providers or physical GPS.',
            'v1Hashes':{n:hashlib.sha256((root/'v1'/n).read_bytes()).hexdigest() for n in ['index.html','config.js','VERSION.json','MANIFEST.sha256']}}
    def save():(out/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    try:
        with sync_playwright() as pw:
            b=launch_browser(pw);report['browser']=browser_identity(b)
            c=b.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='Asia/Riyadh',locale='en-US',reduced_motion='reduce')
            requests=[]
            def route(r):
                u=r.request.url;requests.append(u)
                if u.startswith(origin+'/'):r.continue_()
                elif u in font_files:r.fulfill(body=font_files[u].read_bytes(),content_type='text/css' if u==FONT_CSS else 'font/woff2',headers={'Access-Control-Allow-Origin':'*'})
                else:
                    value=fixture(u,True)
                    if urlsplit(u).hostname=='api.aladhan.com':
                        date=urlsplit(u).path.rstrip('/').split('/')[-1];day,month,year=date.split('-')
                        value['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year)
                    r.fulfill(json=value,headers={'Access-Control-Allow-Origin':'*'})
            c.route('**/*',route)
            c.add_init_script(OBSERVER)
            c.add_init_script('if(location.protocol==="http:"&&!localStorage.getItem('+json.dumps(ROOT_KEY)+'))localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(SETTINGS))+');')
            q=c.new_page();q.on('pageerror',lambda e:report['errors'].append(str(e)))
            q.on('response',lambda r:report['assetFailures'].append({'url':r.url,'status':r.status}) if r.url.startswith(origin) and r.status>=400 else None)
            # Anchor Date only; leave real rAF/timer/worker clocks untouched.
            c.add_init_script("(()=>{const D=Date,start=performance.now(),base=D.parse('2026-10-07T20:30:00Z');window.Date=class extends D{constructor(...a){super(...(a.length?a:[base+performance.now()-start]));}static now(){return base+performance.now()-start;}};})();")
            report['requests']=requests
            start=time.monotonic();q.goto(origin+'/root.html',wait_until='domcontentloaded');f=q.frames[1]
            try:f.wait_for_function("typeof qaState==='function'&&qaState().cache.prayerLoaded&&!!window.SalahMoonRuntime",timeout=45000,polling=100)
            except Exception:
                report['failureDiagnostic']=f.evaluate("({url:location.href,qa:window.qaState?.(),moon:window.SalahMoonRuntime?.state,sky:window.realSkyState?.(),rows:document.querySelectorAll('.p').length})")
                q.screenshot(path=out/'failure.png');save();raise
            report['prayerSeconds']=time.monotonic()-start
            print('prayers ready',report['prayerSeconds'],flush=True)
            f.evaluate('()=>_enableSettingsAffordance()');f.evaluate(MONITOR)
            wait(f,"SalahMoonRuntime.state.status==='refining'",200);report['previewSeconds']=time.monotonic()-start
            print('preview',report['previewSeconds'],flush=True)
            f.evaluate('()=>__mqInteract()')
            try:wait(f,"SalahMoonRuntime.state.status==='ready'&&!SalahMoonRuntime.state.pending&&SalahMoonDetail.state.visible&&realSkyState().status==='ready'",300)
            except Exception:
                report['failureDiagnostic']=f.evaluate(STATE);report['workerEvents']=f.evaluate('__mq.events')
                report['interaction']=f.evaluate('()=>{clearInterval(__mqTimer);return __mqPerf;}')
                q.locator('iframe').screenshot(path=out/'FAIL-preview-not-acceptance.png');save();raise
            report['refinedSeconds']=time.monotonic()-start
            perf=f.evaluate('()=>{clearInterval(__mqTimer);return __mqPerf;}');report['interaction']=perf
            assert len(perf['actions'])==16 and all(a['opened'] for a in perf['actions'])
            assert all(any(a['type']==k and a['status']=='refining' for a in perf['actions']) for k in ['date','settings'])
            report['checks']['settingsDuringRefinement']=True
            before=f.evaluate(STATE);report['root']=before
            report['workerEvents']=f.evaluate('__mq.events')
            assert before['rows']==6 and before['host']['timeScale']==1 and not before['moon']['legacyFallback'] and before['moon']['quality']=='empirical-adaptive'
            precision=before['moon']['phasePrecision']
            assert precision['targetPositionErrorBound']<=precision['maximumPositionErrorDevicePixels']+1e-9
            assert before['sky']['composition']['moonPixels']==0 and before['geometry']['footerBottom']<=534
            q.locator('iframe').screenshot(path=out/'root-iframe.png');f.locator('.moon-detail-canvas').screenshot(path=out/'root-moon.png')
            clock=f.evaluate('({now:simNow(),left:model().leftMin,sky:realSkyState().last.utcMs})')
            q.wait_for_timeout(15000)
            later=f.evaluate('({now:simNow(),left:model().leftMin,sky:realSkyState().last.utcMs,scale:TIMESCALE})')
            assert 14000<later['now']-clock['now']<18000 and later['left']<clock['left'] and later['sky']>clock['sky'] and later['scale']==1
            report['checks']['normalClock']={'before':clock,'after':later}
            report['checks']['phaseDisplayBound']=precision
            # Bounded protocol failure/recovery uses a small actual solver after
            # the full native refinement capture, not as its substitute.
            f.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',small_scene());wait(f,"SalahMoonRuntime.state.status==='ready'",60)
            f.evaluate("__mq.workers.findLast(w=>w.isMoon).onerror({message:'controlled worker failure'})")
            wait(f,"SalahMoonRuntime.state.status==='unavailable'",20)
            assert f.evaluate('SalahMoonRuntime.state.legacyFallback&&SalahMoonRuntime.surface()===null')
            q.wait_for_timeout(200);report['failureState']=f.evaluate(STATE)
            q.locator('iframe').screenshot(path=out/'root-fallback-control.png')
            assert f.evaluate('SalahMoonRuntime.retry()');wait(f,"SalahMoonRuntime.state.status==='ready'&&!SalahMoonRuntime.state.legacyFallback",60)
            report['checks']['retry']=True
            original=f.evaluate('localStorage.getItem('+json.dumps(ROOT_KEY)+')')
            request_start=len(requests);q.goto(origin+'/v1.html',wait_until='load');f=q.frames[1]
            f.wait_for_function("typeof qaState==='function'&&qaState().cache.prayerLoaded",timeout=30000);f.evaluate('document.fonts.ready')
            q.wait_for_timeout(1500);q.locator('iframe').screenshot(path=out/'v1-iframe.png')
            report['v1']={'qa':f.evaluate('qaState()'),'geometry':f.locator('.c').bounding_box(),'footer':f.locator('.d').bounding_box(),'localRequests':[u.replace(origin,'') for u in requests[request_start:] if u.startswith(origin)]}
            assert report['v1']['geometry']['width']==325 and report['v1']['geometry']['height']==530
            assert '/salah_widget/v1/config.js' in report['v1']['localRequests'] and '/salah_widget/config.js' not in report['v1']['localRequests']
            f.locator('.buckle').click(force=True);f.locator('#set-label').fill('V1 separate');f.locator('#set-time').select_option('12');f.locator('#setClose').click(force=True)
            q.wait_for_timeout(1000);assert f.evaluate('localStorage.getItem('+json.dumps(ROOT_KEY)+')')==original
            assert f.evaluate('SalahConfig.loadLocal().label')=='V1 separate'
            q.reload(wait_until='load');f=q.frames[1];f.wait_for_function("typeof qaState==='function'&&qaState().cache.prayerLoaded",timeout=30000)
            assert f.evaluate('SalahConfig.loadLocal().time')=='12' and f.evaluate('localStorage.getItem('+json.dumps(ROOT_KEY)+')')==original
            report['checks']['v1DependencyStorageReload']=True
            assert not report['errors'] and not report['assetFailures']
            assert report['runtime']==runtime_identity(root)
            c.close();b.close();report['status']='PASS_SCOPED'
    except Exception:
        report['status']='FAIL';report['exception']=traceback.format_exc()
        try:
            report['failureDiagnostic']=f.evaluate("({url:location.href,qa:window.qaState?.(),moon:window.SalahMoonRuntime?.state,sky:window.realSkyState?.()})")
            q.screenshot(path=out/'failure.png')
        except Exception:pass
    finally:server.shutdown();save()
    print(json.dumps({k:report.get(k) for k in ['status','browser','prayerSeconds','previewSeconds','refinedSeconds','exception']},indent=2),flush=True)
    return report['status']=='PASS_SCOPED'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--fonts',required=True,type=Path);a=p.parse_args()
    raise SystemExit(0 if run(a.root.resolve(),a.output,a.fonts) else 1)
