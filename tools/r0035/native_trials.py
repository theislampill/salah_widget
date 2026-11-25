"""Interleave COMPLETE native widgets. No production API or private provider is contacted.
Supply measured-arm trees/flags explicitly. PNG acquisition is an independent, timed lane.
"""
import argparse
import functools
import hashlib
import json
import math
import os
import re
import subprocess
import threading
import time
from contextlib import ExitStack
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from trial_admission import assess, producer_flags


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def check_plan(plan):
    reconstructed = plan.get('kind') == 'independent-reconstruction'
    arms = plan['arms']
    if set(arms) != {'main', 'unmodified', 'mitigated'}:
        raise ValueError('Three named arms required')
    if not reconstructed and len({arm['commit'] for arm in arms.values()}) != 3:
        raise ValueError('Three distinct commits required')
    for label, arm in arms.items():
        root = Path(arm['root']).resolve()
        if reconstructed and label != 'main':
            receipt = json.loads((root/'r0035-lab-identity.json').read_text())
            ref = arms['unmodified']
            if (receipt['sourceHead'] != arm['commit'] or root != Path(ref['root']).resolve()
                    or not re.fullmatch(r'[a-f0-9]{40}', arm['commit'])):
                raise ValueError('Both reconstructed write arms must use the same identified build')
            for name, digest in receipt['sha256'].items():
                if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
                    raise ValueError(f'{label}: lab build digest mismatch for {name}')
        elif git(root, 'rev-parse', 'HEAD') != arm['commit'] or git(root, 'status', '--porcelain'):
            raise ValueError(f'{label}: commit mismatch or non-clean checkout')
        if not (root / 'index.html').is_file():
            raise ValueError(f'{label}: missing generated entry')
        if label != 'main' and not arm.get('producerProbe'):
            raise ValueError(f'{label}: give the actual qaState field path and expected active value')
        producer_flags(label,arm.get('flags',''),reconstructed,plan.get('historicalProducerOptions'))


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def verify_reconstructed_flags(arms):
    flags = [parse_qs(arms[name]['flags'].lstrip('&')) for name in ('unmodified','mitigated')]
    if flags[0].pop('r35arm', None) != ['full'] or flags[1].pop('r35arm', None) != ['changed'] or flags[0] != flags[1]:
        raise ValueError('The two reconstructed arms may differ only in full vs changed writes')


def start_server(root, stack):
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    stack.callback(server.server_close)
    stack.callback(thread.join)
    stack.callback(server.shutdown)
    return f'http://127.0.0.1:{server.server_port}'


def prayer_fixture(path, date):
    day = datetime.strptime(date, '%d-%m-%Y')
    data = json.loads(path.read_text())
    data['meta']['timezone'] = 'UTC'
    data['date']['gregorian'].update(date=date, day=f'{day.day:02d}', month={
        'number': day.month, 'en': day.strftime('%B')}, year=str(day.year))
    return {'code': 200, 'status': 'OK', 'data': data}


INIT = """() => {
  const trace = window.__r0035 = {frames:[],longTasks:[],states:[],longTaskSupported:false,running:false};
  let last=-Infinity;
  function frame(t) {
    if(trace.running&&t>=trace.start){
      trace.frames.push(t);
      if(trace.poll && t-last>=1000){
        last=t;const start=performance.now(),sample=window.__r35Read(trace.probe);
        trace.states.push({...sample,readMs:performance.now()-start});
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  if(PerformanceObserver.supportedEntryTypes.includes('longtask')){
    trace.longTaskSupported=true;
    new PerformanceObserver(list=>{
      for(const e of list.getEntries())if(trace.running) trace.longTasks.push([e.startTime,e.duration]);
    }).observe({entryTypes:['longtask']});
  }
}"""

READ = r"""probe => {
  const host=window.SalahNativeSkyHost.capture(false), sky=window.SalahRealSky?.state;
  const qa=window.qaState(), read=p=>p.split('.').reduce((v,k)=>v?.[k],qa);
  const card=document.querySelector('.c'), rect=card.getBoundingClientRect(),disc=document.querySelector('.moon-mask-disc'),m=disc?.getScreenCTM();
  const box=n=>{const b=n?.getBoundingClientRect();return b?[b.left-rect.left,b.top-rect.top,b.width,b.height]:null;};
  const at=performance.now(),rows=[...card.querySelectorAll('.times .p')],composition=sky?.last?.composition;
  const sc=card.querySelector('.simclock');
  return {t:at,identity:sky?.displayed?.identity??null,expectedUtc:window.__r35Clock.utc+at-window.__r35Clock.at,
    clock:{wall:FOLLOW_WALL_CLOCK,advancing:ADVANCING,preview:_clockPreview,fast:card.classList.contains('fast'),chrome:getComputedStyle(sc).display!=='none'},
    cloudAlpha:composition?.maxCloudAlpha??null,cloudSource:composition?.cloudSource??null,cloudCurrent:composition?.cloudAuthority?.revision===qa.clouds?.publication?.revision,
    cloudPublication:composition?.cloudAuthority?.state??null,fixtureWx:qa.wx,prayerKeys:rows.map(n=>n.dataset.prayerKey),rowBoxes:rows.map(box),
    prayersReady:!qa.cache?.prayerStale&&rows.every(n=>/\d/.test(n.querySelector('.tm')?.textContent??'')),utcMs:host.utcMs,paused:host.paused,reduced:host.reducedMotion,rate:host.timeScale,
    composed:card.classList.contains('real-sky-composed'),sunAlt:sky?.last?.physicalState?.sun?.altDeg??null,
    predicate:probe?(read(probe.path)??null):null,realMoon:sky?.last?.physicalState?.moon??null,
    calendarMoon:qa.moonTruth??null,moonDisc:m?{maskOn:disc.classList.contains('mask-on'),r:disc.getAttribute('r'),
      matrix:[m.a,m.b,m.c,m.d,m.e-rect.left,m.f-rect.top]}:null,header:box(card.querySelector('.h')),
    footer:box(card.querySelector('.d')),buckle:box(card.querySelector('.buckle')),dimensions:[rect.width,rect.height],
    prayerRows:document.querySelectorAll('.times .p').length,composeMs:sky?.last?.composition?.lastComposeMs,
    catalogue:sky?.last?.catalogue?.sha256,glass:[...document.querySelectorAll('.e,.wt,.buckle,.times .p')]
      .map(n=>{const r=n.getBoundingClientRect();return {element:n.className,x:r.left-rect.left,
        y:r.top-rect.top,width:r.width,height:r.height};})};
}"""


def percentile(samples, q):
    return sorted(samples)[max(0, math.ceil(len(samples) * q)-1)] if samples else None


def trial(browser, engine, base, arm, label, out, args):
    out.mkdir()
    probe = arm.get('probesByCell', {}).get(args.scene+'/'+args.motion, arm.get('producerProbe'))
    utc_ms = datetime.fromisoformat(args.utc.replace('Z', '+00:00')).timestamp()*1000
    lower,upper,weather,extra=args.scene_inputs
    context = browser.new_context(viewport={'width': 360, 'height': 570}, device_scale_factor=1,
                                  timezone_id='UTC', reduced_motion='reduce' if args.motion in ('reduced','override') else 'no-preference', service_workers='block')
    from playwright.sync_api import TimeoutError as BrowserTimeout
    try:
        fixture = Path(arm['root']) / 'tests/r0002-ordinary.json'

        def route(req):
            url = urlsplit(req.request.url)
            if url.netloc == urlsplit(base).netloc or url.scheme in ('blob', 'data'):
                req.continue_()
            elif url.hostname == 'api.aladhan.com' and url.path.startswith('/v1/timings/'):
                req.fulfill(json=prayer_fixture(fixture, url.path.rsplit('/', 1)[-1]))
            else:
                req.abort()

        context.route('**/*', route)
        setup=Path(__file__).with_name('trial_clock.js').read_text()
        clock_setup=f'installTrialWallClock({utc_ms});' if args.clock=='ordinary' else ''
        context.add_init_script(setup+'\n'+clock_setup+f'\nwindow.__r35Read=({READ});({INIT})();')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        fragment = '#lat=24.47&lon=39.61&tz=UTC&method=4&seed=1'+weather+extra
        if args.motion=='override':
            fragment += '&motion=full'
        flags = arm.get('flags', '').lstrip('&')
        page.goto(base+'/index.html'+fragment+('&'+flags if flags else ''))
        page.wait_for_function('() => window.SalahClock && window.SalahNativeSkyHost')
        if args.clock=='simulation':
            page.evaluate('t => {window.__r35Clock={utc:t,at:performance.now()};window.SalahClock.set({rate:1,utcMs:t});}',utc_ms)
        page.wait_for_function("""limits => document.querySelector('.c.real-sky-composed')
            && window.SalahRealSky?.state?.last?.physicalState?.sun?.altDeg > limits[0]
            && window.SalahRealSky?.state?.last?.physicalState?.sun?.altDeg < limits[1]
            && document.querySelectorAll('.times .p').length===6""", arg=[lower,upper], timeout=60000)
        page.wait_for_timeout(args.warmup*1000)
        before = page.evaluate(READ, probe)
        card = page.locator('.c')
        observations = []
        page.evaluate('p => {window.R0035Lab?.beginTrial();Object.assign(window.__r0035,{start:performance.now(),running:true,poll:p.poll,probe:p.probe});}',
                      {'poll':args.observe_producer,'probe':probe})
        start = time.monotonic_ns()
        if args.capture:
            # Each PNG is a separate snapshot. Record request and receipt bounds,
            # which do not identify the underlying presentation timestamp exactly.
            while (time.monotonic_ns()-start)/1e9 < args.seconds:
                begin = time.monotonic_ns()
                data = card.screenshot(timeout=10000)
                end = time.monotonic_ns()
                name = f'{len(observations):05}.png'
                (out / name).write_bytes(data)
                observations.append({'file':name,'startMs':(begin-start)/1e6,'endMs':(end-start)/1e6,
                                     'sha256':hashlib.sha256(data).hexdigest()})
        else:
            page.wait_for_timeout(args.seconds*1000)
        elapsed = (time.monotonic_ns()-start)/1e9
        trace = page.evaluate('() => {window.__r0035.end=performance.now();window.__r0035.running=false;window.__r0035.publication=window.R0035Lab?.endTrial()??null;return window.__r0035}')
        after = page.evaluate(READ, probe)
        frames = trace['frames']
        gaps = [b-a for a,b in zip(frames,frames[1:])]
        acquisition = [b['endMs']-a['endMs'] for a,b in zip(observations,observations[1:])]
        active=args.motion!='reduced' and args.scene not in ('day','twilight')
        verdict=assess(before,after,trace,trace['publication'],args.scene,[lower,upper],args.motion,args.clock,probe,label,active)
        if errors:
            verdict['failures'].append('page errors');verdict['verdict']='failed'
        valid=verdict['verdict']=='passed'
        result = {'arm':label,'commit':arm['commit'],'flags':flags,'engine':engine,'version':browser.version,
            'root':os.fspath(Path(arm['root']).resolve()),'utc':args.utc,'elapsedSeconds':elapsed,'capture':args.capture,
            'qualification':verdict,'driverSha256':args.driver_sha256,'clock':args.clock,'weather':'controlled fixture','trace':trace,'scope':args.scope,'scene':args.scene,'motion':args.motion,'p50FrameMs':percentile(gaps,.5),'p95FrameMs':percentile(gaps,.95),
            'p99FrameMs':percentile(gaps,.99),'maxFrameMs':max(gaps,default=None),'framesOver50Ms':sum(g>50 for g in gaps),
            'observedProducerDuringTrial':args.observe_producer,'acquisitions':observations,'acquisitionP95Ms':percentile(acquisition,.95),'acquisitionMaxMs':max(acquisition,default=None),
            'before':before,'after':after,'pageErrors':errors,'admitted':valid}
        (out/'trial.json').write_text(json.dumps(result,indent=2))
        return result
    except BrowserTimeout as error:
        result={'arm':label,'commit':arm['commit'],'clock':args.clock,'scene':args.scene,'motion':args.motion,
                'capture':args.capture,'driverSha256':args.driver_sha256,'observedProducerDuringTrial':args.observe_producer,'engine':engine,'version':browser.version,
                'p95FrameMs':None,'p99FrameMs':None,'maxFrameMs':None,'framesOver50Ms':None,'admitted':False,
                'qualification':{'verdict':'indeterminate','missing':['native setup or acquisition timed out'],'error':str(error)}}
        (out/'trial.json').write_text(json.dumps(result,indent=2))
        return result
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--engine', choices=['webkit','firefox','chromium'], required=True)
    parser.add_argument('--clock',choices=['ordinary','simulation'],default='ordinary')
    parser.add_argument('--rounds', type=int, default=9)
    parser.add_argument('--seconds', type=int, choices=range(15,61),default=60)
    parser.add_argument('--warmup', type=int, default=5)
    parser.add_argument('--scene', choices=['dark','moonlit','near-fajr','twilight','day','broken','crescent','half','gibbous','full'],default='dark')
    parser.add_argument('--motion',choices=['normal','reduced','override'],default='normal')
    parser.add_argument('--utc', help='Override only if the specified solar scene still passes its measured altitude gate')
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--observe-producer',action=argparse.BooleanOptionalAction,default=True,help='Check the scene at 1 Hz; disabling this creates a timing-only lane with indeterminate scene coverage')
    args = parser.parse_args()
    clear='&simWx=0&simCloud=0'
    scenes={'dark':('2026-11-09T00:00:00Z',-91,-20,clear,''),
      'moonlit':('2026-11-24T00:00:00Z',-91,-20,clear,''),
      'near-fajr':('2026-11-09T02:15:00Z',-20,-16,clear,''),
      'twilight':('2026-11-09T03:15:00Z',-7,-3,clear,''),
      'day':('2026-11-09T09:00:00Z',25,90,clear,''),
      'broken':('2026-11-09T00:00:00Z',-91,-20,'&simWx=2&simCloud=50','')}
    for name,fraction in [('crescent',.08),('half',.5),('gibbous',.9),('full',.99)]:
        scenes[name]=('2026-11-24T00:00:00Z',-91,-20,clear,
                      f'&simMoon={fraction}&simWax=1&simMoonAlt=30&simMoonH=42')
    clock,*args.scene_inputs=scenes[args.scene]
    args.utc=args.utc or clock
    if args.rounds < 1 or args.warmup < 0:
        parser.error('Positive rounds and nonnegative warmup required')
    plan = json.loads(args.plan.read_text())
    args.scope=plan.get('kind','original-and-mitigated')
    check_plan(plan)
    args.driver_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                        for name in ('native_trials.py','trial_admission.py','trial_clock.js')}
    if plan.get('kind') == 'independent-reconstruction':
        verify_reconstructed_flags(plan['arms'])
    from playwright.sync_api import sync_playwright
    args.output.mkdir(parents=True, exist_ok=False)
    with ExitStack() as stack:
        servers = {k:start_server(v['root'],stack) for k,v in plan['arms'].items()}
        pw = stack.enter_context(sync_playwright())
        browser = getattr(pw,args.engine).launch()
        stack.callback(browser.close)
        (args.output/'plan.json').write_text(json.dumps(plan,indent=2))
        summary=[]
        for n in range(args.rounds):
            labels=['main','unmodified','mitigated']
            if n//3%2: labels.reverse()
            for label in labels[n%3:]+labels[:n%3]:
                r=trial(browser,args.engine,servers[label],plan['arms'][label],label,
                        args.output/f'{n+1:02}-{label}',args)
                summary.append({k:r[k] for k in ('arm','commit','clock','scene','motion','capture','observedProducerDuringTrial','qualification','p95FrameMs','p99FrameMs','maxFrameMs','framesOver50Ms','admitted')})
                (args.output/'summary.json').write_text(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
