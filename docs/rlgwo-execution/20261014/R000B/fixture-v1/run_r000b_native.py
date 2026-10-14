"""R000B native 1x expiry, 503 and ordinary retry; reuse the R000C wrapper/runner.

No acquisition/render/model-install helper is called. Native video runs from
navigation through the predeclared restored watch; first-state pixels remain in
the original recording. Full diagnostic reads occur only at checkpoints.
"""
import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
from urllib.parse import urlencode, unquote, urlsplit
from run_r000c_native import dump, sha, tile_png, wait

READ = '() => __smokeWeather.read(__smokeWeather.identity())'
PASSIVE = """() => {
  const f=window.__widgetFixture;
  if(f?.state==='error')throw Error(f.error);
  return f?.state==='ready'?f.passive?.at(-1):null;
}"""


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--browser',choices=['chromium','firefox'],required=True)
    p.add_argument('--python-packages',type=Path,required=True)
    p.add_argument('--mode',choices=['default','reduced','full'],required=True)
    p.add_argument('--radar-recovery',action='store_true',help='Wait for the ordinary ten-minute radar retry')
    args=p.parse_args();root=args.root.resolve();out=args.out.resolve()
    if out.is_relative_to(root):raise ValueError('Keep original acquisition outside checkout')
    out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root/'tools/cp9'));sys.path.insert(0,str(args.python_packages.resolve()))
    from browser_runtime import browser_options,browser_identity
    from runtime_identity import runtime_identity
    from playwright.sync_api import sync_playwright
    before=runtime_identity(root);wrapper=root/'tests/rlgwo/r000b-weather-fixture.html'
    document=wrapper.read_bytes();tile=tile_png();requests=[]
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_GET(self):
            path=unquote(urlsplit(self.path).path);requests.append({'path':path,'hostMonotonic':time.monotonic()})
            if path=='/fixture.html':data,mime=document,'text/html; charset=utf-8'
            elif path.startswith('/tile/'):data,mime=tile,'image/png'
            elif path.startswith('/product/'):
                target=(root/path[len('/product/'):]).resolve()
                if not target.is_relative_to(root) or not target.is_file():self.send_error(404);return
                data,mime=target.read_bytes(),self.guess_type(str(target))
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    os.environ['SALAH_BROWSER']=args.browser
    case={'id':'B16-'+args.browser+'-'+args.mode,'mode':args.mode,'clock':'native-elapsed-1x',
          'startUtc':'2026-09-07T18:44:50Z','initialSourceTime':'2026-09-07T21:30','intervalSeconds':900,
          'temperature':24,'WMO':63,'precipitationMm':2,'cloudPercent':70,'zone':'Asia/Riyadh',
          'site':{'lat':24.47,'lon':39.61,'label':'Madinah','intent':'fixed-site'},
          'motionPreference':'no-preference' if args.mode=='default' else 'reduce','fullOverride':args.mode=='full',
          'watchSeconds':30,'ordinaryRadarRecovery':args.radar_recovery}
    dump(out/'case-input.json',case)
    row={'schema':'r000b-native/v1','id':case['id'],'status':'FAIL','runtime':before,
         'sourceSha256':before['files']['index.html']['sha256'],'wrapperSha256':sha(document),
         'driverSha256':sha(Path(__file__).read_bytes()),'tileSha256':sha(tile),
         'observations':[],'checks':{},'watches':[],'limitations':__doc__}
    browser=context=page=None;errors=[]
    def capture(stage):
        state=page.evaluate(READ);observation={'stage':stage,'hostMonotonic':time.monotonic(),'state':state}
        row['observations'].append(observation);dump(out/(stage+'.json'),observation)
        row['checks'][stage+'/geometry']=state['card']=={'width':325,'height':530}
        row['checks'][stage+'/footer']=0<=state['footer']['top']<state['footer']['bottom']<=530.1
        row['checks'][stage+'/sixRows']=len(state['rows'])==6
        row['checks'][stage+'/noLightning']=state['lightning']=='off' and not state['qa']['wxTruth']['visualPermissions']['lightning']
        row['checks'][stage+'/liveClock']=state['clock']=={'TIMESCALE':1,'FOLLOW_WALL_CLOCK':True,'ADVANCING':False}
        return state
    try:
        with sync_playwright() as pw:
            family,options=browser_options();browser=getattr(pw,family).launch(**options)
            executable=options.get('executable_path') or getattr(pw,family).executable_path
            row['browser']={**browser_identity(browser),'executable':executable,'executableSha256':sha(Path(executable).read_bytes()),'headless':options['headless']}
            context=browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,
                timezone_id='Asia/Riyadh',reduced_motion=case['motionPreference'],
                record_video_dir=str(out/'video'),record_video_size={'width':390,'height':600})
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            cfg={'lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','label':'Madinah','method':4,'school':0,'units':'c','seed':1,
                 'qa':1,'simMoon':.5,'simMoonAlt':20,'simMoonH':42}
            if args.mode=='full':cfg['motion']='full'
            query={'case':'B16-night-expiry-recovery','mode':'healthy','night':1,'attempt':1,'run':case['id']}
            url=f'http://127.0.0.1:{server.server_port}/fixture.html?'+urlencode(query)+'#'+urlencode(cfg)
            row['url']=url;row['navigationHostMonotonic']=time.monotonic()
            page.goto(url,wait_until='commit',timeout=60000)
            wait(page,"() => {const f=window.__widgetFixture;if(f?.state==='error')throw Error(f.error);return f?.state==='ready'&&f.passive?.some(s=>s.modelEligible&&s.temperature==='24°'&&s.precip==='on');}",15000)
            current=capture('current')
            row['checks']['initialCurrent']=current['modelEligible'] and current['temperature']=='24°' and current['visibleParticles']>0
            row['checks']['sourceDistinct']=current['raw']['currentValidAt']==1788805800000 and current['raw']['currentIntervalSec']==900 and current['raw']['retrievedAt']>current['raw']['currentValidAt']
            row['checks']['initialRadar']=current['radarEligibility']['available'] and current['radar']['frameGeneratedAt']==1788805500000 and current['radar']['indexGeneratedAt']==1788806670000
            wait(page,"() => window.__widgetFixture?.passive?.some(s=>!s.modelEligible&&s.temperature===''&&s.precip==='off'&&s.elapsedMs>10000)",20000)
            expired=capture('expired')
            row['checks']['expiryWithdraws']=not expired['modelEligible'] and expired['temperature']=='' and expired['icon']=='—' and expired['visibleParticles']==0 and expired['rainOpacity']==0
            row['checks']['radarExpires']=not expired['radarEligibility']['available'] and expired['radar']['precipMm']==0
            wait(page,"() => window.__widgetFixture?.ledger?.some(r=>r.weatherOrdinal===2&&r.status===503)",110000)
            failed=capture('503')
            row['checks']['503NoAuthority']=not failed['modelEligible'] and failed['temperature']=='' and failed['visibleParticles']==0
            wait(page,"() => window.__widgetFixture?.passive?.some(s=>s.elapsedMs>60000&&s.modelEligible&&s.temperature==='24°'&&s.precip==='on')",100000)
            restored=capture('restored')
            row['checks']['ordinaryRecovery']=restored['modelEligible'] and restored['temperature']=='24°' and restored['visibleParticles']>0
            watch={'stage':'restored','startHostMonotonic':time.monotonic(),'startFixtureElapsedMs':restored['elapsedMs'],'requiredSeconds':30}
            # Native video only while watching: no screenshot/crop or full diagnostic polling.
            page.wait_for_timeout(30000)
            watch['endHostMonotonic']=time.monotonic();row['watches'].append(watch)
            final=capture('restored-30s')
            if args.radar_recovery:
                wait(page,"() => window.__widgetFixture?.ledger?.some(r=>r.radarOrdinal===2&&r.jsonSettled)",530000)
                wait(page,"() => window.__widgetFixture?.passive?.some(s=>s.elapsedMs>=600000&&s.radarEligible)",15000)
                radar=capture('radar-restored')
                row['checks']['ordinaryRadarRecovery']=radar['radarEligibility']['available'] and radar['radar']['frameGeneratedAt']>current['radar']['frameGeneratedAt'] and radar['radar']['precipMm']==0
            fixture=page.evaluate('() => __widgetFixture');row['fixture']=fixture
            weather=[r for r in fixture['ledger'] if 'weatherOrdinal' in r];radar=[r for r in fixture['ledger'] if 'radarOrdinal' in r]
            row['checks']['retryOwnership']=len(weather)>=3 and weather[1]['status']==503 and weather[1]['jsonReads']==0 and all(b['elapsedMs']-a['elapsedMs']>=60000 for a,b in zip(weather,weather[1:]))
            row['checks']['radarOwnership']=len(radar)>=1 and all(b['elapsedMs']-a['elapsedMs']>=600000 for a,b in zip(radar,radar[1:]))
            row['checks']['sourceBinding']=fixture['sourceSha256']==row['sourceSha256']
            row['checks']['isolation']=fixture['storageIsolated'] and fixture['clockIsolated'] and fixture['fetchIntercepted'] and fixture['initialStorageEntries']==0
            row['checks']['noHelper']=all(e['action']=='consumer-read' for e in fixture['weatherEvents'])
            row['checks']['native1x']=abs((final['wallUtcMs']-current['wallUtcMs'])-(final['elapsedMs']-current['elapsedMs']))<10
            row['checks']['populationRetained']=all(o['state']['cloudPopulation']==current['cloudPopulation'] for o in row['observations'])
            row['checks']['halfMoon']=final['qa']['moonTruth']['phaseFraction']==.5 and final['qa']['moonTruth']['calendarMoonVisible']
            row['checks']['motionPreference']=final['motion']=={'reduced':args.mode!='default','full':args.mode=='full'}
            row['checks']['noErrors']=not errors and not fixture['consoleErrors']
            row['status']='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' if all(row['checks'].values()) else 'FAIL'
    except Exception:row['exception']=traceback.format_exc()
    finally:
        row['pageErrors']=errors
        if page:
            try:row.setdefault('fixture',page.evaluate('() => window.__widgetFixture'))
            except Exception:pass
        if context:context.close()
        if page and page.video:
            video=Path(page.video.path());row['video']={'file':video.relative_to(out).as_posix(),'sha256':sha(video.read_bytes())}
        if browser:browser.close()
        server.shutdown();row['httpRequests']=requests;row['runtimeUnchanged']=runtime_identity(root)==before
        dump(out/'receipt.json',row)
        print(json.dumps({'case':row['id'],'status':row['status'],'failedChecks':[k for k,v in row['checks'].items() if not v],'exception':row.get('exception')}),flush=True)
    return 0 if row['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
