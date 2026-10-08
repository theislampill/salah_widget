"""Receiving Moon qualification on actual HTTP/file navigation, with fixture prayers.

No terrain/profile changes, web-security bypass, live-provider claim or V5 campaign.
The worker observer retains actual messages only for explicit stale/malformed controls.
"""
from pathlib import Path
import argparse, functools, hashlib, http.server, json, threading, time, traceback
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser, browser_identity
from native_browser_check import INIT, ROOT
from runtime_identity import runtime_identity

OBSERVER=r'''(()=>{
 const NativeWorker=Worker;window.__mq={workers:[],events:[],lastResult:null,firstPreview:null,firstResult:null,start:performance.now()};
 window.Worker=class extends NativeWorker{
  constructor(u,o){super(u,o);__mq.workers.push(this);const post=this.postMessage.bind(this);
   this.postMessage=(m,t)=>{if(m.kind==='boot')this.isMoon='offline' in m;return t?post(m,t):post(m);};
   this.addEventListener('message',e=>{if(!this.isMoon)return;const m=e.data;
    if(m.kind==='preview'||m.kind==='result'){
     __mq.events.push({kind:m.kind,id:m.id,identity:m.identity,phase:m.scene?.fraction,at:performance.now(),quality:m.diagnostics?.quality});
     if(m.kind==='preview'&&__mq.firstPreview===null)__mq.firstPreview=performance.now();
     if(m.kind==='result'){__mq.lastResult=m;if(__mq.firstResult===null)__mq.firstResult=performance.now();}
    }
   });
  }
 };
})();'''

MONITOR=r'''()=>{
 window.__mqPerf={start:performance.now(),gaps:[],actions:[],statuses:[]};let last=performance.now();
 window.__mqTimer=setInterval(()=>{const now=performance.now(),s=SalahMoonRuntime.state.status;
  __mqPerf.gaps.push({at:now,ms:now-last,status:s,adoption:SalahMoonRuntime.state.lastAdoption});last=now;
  if(__mqPerf.statuses.at(-1)?.status!==s)__mqPerf.statuses.push({status:s,at:now});
 },25);
 window.__mqInteract=()=>{for(let i=1;i<=8;i++){const due=performance.now()+i*300;setTimeout(()=>{
  const start=performance.now(),date=i%2===1;
  if(date){document.querySelector('#ceDateButton').click();const opened=document.querySelector('#dateDialog').open;document.querySelector('#dateClose').click();__mqPerf.actions.push({type:'date',opened,delayMs:start-due,durationMs:performance.now()-start,status:SalahMoonRuntime.state.status});}
  else{document.querySelector('.buckle').click();const opened=document.querySelector('.c').classList.contains('settings-open');document.querySelector('#setClose').click();__mqPerf.actions.push({type:'settings',opened,delayMs:start-due,durationMs:performance.now()-start,status:SalahMoonRuntime.state.status});}
 },i*300);}};__mqInteract();
}'''

STATE=r'''()=>({moon:SalahMoonRuntime.state,detail:SalahMoonDetail.state,
 sky:{status:realSkyState().status,errors:realSkyState().errors,composition:realSkyState().last?.composition},host:SalahMoonHost.capture(),
 rows:document.querySelectorAll('.p').length,qa:qaState().moonTruth,
 geometry:{card:(()=>{const r=document.querySelector('.c').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};})(),footerBottom:document.querySelector('.d').getBoundingClientRect().bottom}})'''

def wait(page, expression, timeout=290):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if page.evaluate('()=>('+expression+')'): return
        page.wait_for_timeout(100)
    raise TimeoutError(expression+' '+json.dumps(page.evaluate(STATE)))

def small_scene(fraction=.5):
    import math
    a=math.acos(2*fraction-1)
    return dict(size=40,outSize=80,diameter=76.8,basis=[0,1,0,0,0,1,1,0,0],sun=[math.cos(a),-math.sin(a),0],earth=[384400,0,0],distance=384400,extent=1.08,mode='physical-reference',fraction=fraction,waxing=False,tilt=0)

def run(root, out, entry='http', phases=True):
    root=root.resolve();out.mkdir(parents=True,exist_ok=True);checks=[];errors=[];served=[]
    class Server(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            served.append(self.path);super().do_GET()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Server,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    report={'scope':'Actual navigation and product worker; controlled native date/prayers/weather. No live-provider, full V5 science or independent-review claim. Refinement and fault workloads identified separately.',
            'entry':entry,'checks':checks,'errors':errors,'runtimeTreeSha256':runtime_identity(root)['treeSha256'],
            'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    def save(): (out/'results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def check(name, passed, **data):
        checks.append(dict(name=name,passed=bool(passed),**data));save()
        if not passed: raise AssertionError(name)
    try:
        with sync_playwright() as p:
            browser=launch_browser(p);report['browser']=browser_identity(browser)
            context=browser.new_context(viewport={'width':430,'height':640},reduced_motion='reduce')
            context.add_init_script(INIT);context.add_init_script(OBSERVER)
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            # Leave the local server and file transport entirely to the browser.
            context.route('https://fonts.googleapis.com/**',lambda route:route.abort())
            context.route('https://fonts.gstatic.com/**',lambda route:route.abort())
            if entry=='http': url=f'http://127.0.0.1:{server.server_port}/index.html'
            elif entry=='file-index': url=(root/'index.html').as_uri()
            else: url=(root/'offline.html').as_uri()
            report['url']=url
            fragment='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Moon%20receiving&method=4&simTime=23:30&simWx=0&simCloud=0&simTemp=20&units=c&motion=reduced&simMoon=.5&simWax=0&simMoonAlt=20&simMoonH=42&qa=1'
            start=time.monotonic();page.goto(url+'#'+fragment,wait_until='domcontentloaded',timeout=45000)
            wait(page,"document.querySelectorAll('.p').length===6&&!!window.SalahMoonRuntime",30)
            report['prayerReadySeconds']=time.monotonic()-start
            page.evaluate('()=>_enableSettingsAffordance()');page.evaluate(MONITOR)
            wait(page,"SalahMoonRuntime.state.status==='refining'",200)
            report['previewSeconds']=time.monotonic()-start
            page.evaluate('()=>__mqInteract()')
            wait(page,"SalahMoonRuntime.state.status==='ready'",290)
            report['refinedSeconds']=time.monotonic()-start
            perf=page.evaluate('()=>{clearInterval(__mqTimer);return __mqPerf;}')
            check('prayer-and-settings-during-refinement', len(perf['actions'])==16 and all(a['opened'] for a in perf['actions']) and all(any(a['type']==kind and a['status']=='refining' for a in perf['actions']) for kind in ['date','settings']) and max(g['ms'] for g in perf['gaps'])<=250 and max(a['delayMs'] for a in perf['actions'])<=250,
                  longGaps=[g for g in perf['gaps'] if g['ms']>100],actions=perf['actions'],maxHeartbeatMs=max(g['ms'] for g in perf['gaps']),maxScheduledActionDelayMs=max(a['delayMs'] for a in perf['actions']),statuses=perf['statuses'],budgetMs=250,
                  budgetMet=max(g['ms'] for g in perf['gaps'])<=250 and max(a['delayMs'] for a in perf['actions'])<=250)
            wait(page,"realSkyState().status==='ready'&&SalahMoonDetail.state.visible",60)
            def capture(name):
                wait(page,"SalahMoonRuntime.state.status==='ready'&&!!SalahMoonRuntime.surface()&&SalahMoonDetail.state.visible",290)
                page.locator('.c').screenshot(path=str(out/(name+'.png')))
                page.locator('.moon-detail-canvas').screenshot(path=str(out/(name+'-moon.png')))
                s=page.evaluate(STATE);g=s['geometry'];check(name,s['rows']==6 and s['detail']['visible'] and not s['moon']['legacyFallback'] and g['footerBottom']<=g['card']['y']+g['card']['height'],state=s)
            capture('half')
            if phases:
                for name,f,wax in [('crescent',.08,1),('gibbous',.92,1),('full',1,1),('new',0,1)]:
                    phase_start=time.monotonic();page.evaluate('x=>{SIM.moon=String(x.f);SIM.wax=String(x.wax);renderMoon();render();SalahMoonRuntime.request();}',dict(f=f,wax=wax))
                    wait(page,"SalahMoonRuntime.state.status==='ready'",290)
                    wait(page,'SalahMoonDetail.state.visible',60);capture(name)
                    checks[-1]['refinementSeconds']=time.monotonic()-phase_start;save()
                page.evaluate("()=>{SIM.moonAlt='-20';renderMoon();render();SalahMoonRuntime.request();SalahRealSky.compose();}")
                capture('below-horizon-calendar')
                check('below-horizon-has-no-moonlight',page.evaluate('qaState().moonTruth.moonlightOpacity===0&&SalahMoonRuntime.state.calendarProxyWeight===1'))
                page.evaluate("()=>{SIM.moonAlt='20';renderMoon();render();SalahMoonRuntime.request();SalahRealSky.compose();}")
                # Horizon presentation can change the rounded display diameter
                # and therefore the admitted phase bucket. A ready label or old
                # canvas backing bytes cannot substitute for a CURRENT surface.
                capture('restored-above-horizon-current')
            # Distinct cloud and direct-field controls on the actual adopted surface.
            encoding='\n'.join(line for line in (root/'real-sky/native-encoding.mjs').read_text(encoding='utf-8').splitlines() if not line.startswith('import ')).replace('export ','')
            for name,path in [('finite','astronomy.mjs'),('linearToSrgb','photometry.mjs')]:
                body=next(line for line in (root/'real-sky/core/src'/path).read_text(encoding='utf-8').splitlines() if line.startswith('export function '+name+'('))
                encoding=body.replace('export ','')+'\n'+encoding
            page.evaluate('(()=>{'+encoding+';window.__moonEncode=encodeNativeFrame;})()')
            proof=page.evaluate(r'''()=>{
 const detail=document.querySelector('.moon-detail-canvas'),cloud=document.querySelector('.cloudcanvas'),c=cloud.getContext('2d'),saved=c.getImageData(0,0,cloud.width,cloud.height),frame=realSkyFrame();
 if(!SalahMoonRuntime.surface()||!SalahMoonDetail.state.visible)throw new Error('Composition control requires a current visible terrain surface');
 c.clearRect(0,0,cloud.width,cloud.height);const fresh=()=>({...frame,raster:{...frame.raster}});
 SalahMoonDetail.compose(fresh(),__moonEncode);const before=detail.getContext('2d').getImageData(0,0,detail.width,detail.height).data;
 const bright=fresh();bright.raster.stellarLinear=new Float64Array(frame.raster.stellarLinear.length).fill(50);bright.raster.diffusePhysicalLinear=new Float64Array(frame.raster.stellarLinear.length).fill(50);
 SalahMoonDetail.compose(bright,__moonEncode);const after=detail.getContext('2d').getImageData(0,0,detail.width,detail.height).data;
 let inner=0,maxInner=0,changed=0;const W=detail.width,H=detail.height;
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const i=4*(y*W+x),inside=Math.hypot(x+.5-W/2,y+.5-H/2)<Math.min(W,H)*.30;
  if(inside&&before[i+3]===255){inner++;for(let k=0;k<3;k++)maxInner=Math.max(maxInner,Math.abs(before[i+k]-after[i+k]));}
  for(let k=0;k<3;k++)if(before[i+k]!==after[i+k])changed++;
 }
 SalahMoonDetail.compose(fresh(),__moonEncode);c.fillStyle='rgba(80,120,160,0.5)';c.fillRect(0,0,cloud.width,cloud.height);
 const cloudCode=c.getImageData(Math.floor(cloud.width/2),Math.floor(cloud.height/2),1,1).data;
 SalahMoonDetail.compose(fresh(),__moonEncode);const joined=detail.getContext('2d').getImageData(0,0,W,H).data,E=frame.raster.effectiveExposure;
 const inv=q=>{const c=q/255,l=c<=.04045?c/12.92:((c+.055)/1.055)**2.4;return -Math.log1p(-Math.min(1-1/131072,l))/E;};
 const code=v=>{const l=-Math.expm1(-E*Math.max(0,v));return Math.round(255*(l<=.0031308?12.92*l:1.055*l**(1/2.4)-.055));};
 const a=cloudCode[3]/255;let maxCloud=0,samples=0,wrongDoubleTransmission=0;
 for(let y=Math.floor(H*.35);y<H*.65;y++)for(let x=Math.floor(W*.35);x<W*.65;x++){
  const i=4*(y*W+x);if(before[i+3]!==255)continue;samples++;
  for(let k=0;k<3;k++){const b=-Math.expm1(-E*inv(before[i+k])),f=-Math.expm1(-E*inv(cloudCode[k])),scene=d=>-Math.log1p(-Math.min(1-1/131072,d))/E,expected=code(scene(b*(1-a)+f*a));maxCloud=Math.max(maxCloud,Math.abs(expected-joined[i+k]));if(code(scene(b*(1-a)*(1-a)+f*a))!==expected)wrongDoubleTransmission++;}
 }
 c.putImageData(saved,0,0);SalahRealSky.compose();
 return {innerOpaquePixels:inner,maximumInteriorStarDifference:maxInner,changedBoundaryChannels:changed,cloudSamples:samples,maximumCloudCodeDifference:maxCloud,wrongDoubleTransmission,cloudCode:[...cloudCode],cloudToleranceCodes:1,scope:'Synthetic direct-light and constant-cloud controls; exact interior star rejection, independent bounded display-linear foreground equation with one code of 8-bit reference quantization'};
}''')
            check('opaque-to-stars-and-cloud-once',proof['innerOpaquePixels']>100 and proof['maximumInteriorStarDifference']==0 and proof['changedBoundaryChannels']>0 and proof['cloudSamples']>100 and proof['maximumCloudCodeDifference']<=1 and proof['wrongDoubleTransmission']>0,proof=proof)
            page.locator('.c').screenshot(path=str(out/'opacity-control-restored.png'))
            # startWeather owns simulated-weather admission; fetchWeather alone
            # intentionally returns for SIM.wx and cannot establish this control.
            page.evaluate("()=>{SIM.wx='2';SIM.cloud='65';startWeather();render();paintClouds(simNow()/1000);SalahRealSky.request(true);}")
            wait(page,"realSkyState().status==='ready'&&SalahMoonDetail.state.visible",60)
            clouds=page.evaluate(r'''()=>{const c=document.querySelector('.cloudcanvas'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
 let nonzero=0,visible=0,maxAlpha=0;for(let i=3;i<d.length;i+=4){if(d[i])nonzero++;if(d[i]>16)visible++;maxAlpha=Math.max(maxAlpha,d[i]);}
 return {nonzeroPixels:nonzero,visiblePixels:visible,maxAlpha,weatherSource:weather?.src,cloud:weather?.cloud,weatherCode:weather?.code};}''')
            check('native-cloud-field-present',clouds['weatherSource']=='sim' and clouds['cloud']==65 and clouds['weatherCode']==2 and clouds['visiblePixels']>1000,field=clouds)
            capture('native-clouds')
            # Small actual solver for protocol controls; not a substitute for the phase pixels.
            page.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',small_scene());wait(page,"SalahMoonRuntime.state.status==='ready'",60)
            aba=page.evaluate(r'''async()=>{
 const stale=__mq.lastResult,w=__mq.workers.findLast(w=>w.isMoon),before=SalahMoonRuntime.state.rejected;
 await applyConfig({...CONFIG,label:'Moon B'},{save:false});await applyConfig({...CONFIG,label:'Moon receiving'},{save:false});
 w.onmessage({data:stale});return {rejected:SalahMoonRuntime.state.rejected-before,epoch:SalahMoonRuntime.state.epoch,staleEpoch:stale.identity.epoch,pending:SalahMoonRuntime.state.pending,withheld:SalahMoonRuntime.surface()===null};
}''')
            check('native-A-B-A-rejects-original-result',aba['rejected']>=1 and aba['epoch']>aba['staleEpoch'] and aba['withheld'],observation=aba)
            wait(page,"SalahMoonRuntime.state.status==='ready'",60)
            retained=page.evaluate('SalahMoonRuntime.state.accepted.identity')
            malformed=page.evaluate(r'''()=>{
 const stale=structuredClone(__mq.lastResult);SalahMoonRuntime.refresh();const w=__mq.workers.findLast(w=>w.isMoon);
 // A matching result from the actual prior request is first fenced, then the
 // next matching real result is corrupted only at the receiving event boundary.
 const handler=w.onmessage;w.onmessage=e=>{if(e.data.kind==='result'){w.onmessage=handler;const m=structuredClone(e.data);m.surfaceLinear[0]=NaN;handler({data:m});}else handler(e);};return {armed:true};
}''')
            wait(page,"SalahMoonRuntime.state.status==='unavailable'",60)
            check('matching-malformed-result-rejected-original-current-surface-retained',page.evaluate("id=>SalahMoonRuntime.state.accepted.identity===id&&!!SalahMoonRuntime.surface()&&document.querySelectorAll('.p').length===6",retained),state=page.evaluate(STATE))
            page.evaluate("SalahMoonRuntime.setProfile('reference')");check('failure-retention-revoked-on-new-profile',page.evaluate('SalahMoonRuntime.surface()===null'))
            check('retry-starts',page.evaluate('SalahMoonRuntime.retry()'));wait(page,"SalahMoonRuntime.state.status==='ready'",60)
            check('retry-recovers-refined-surface',page.evaluate('!!SalahMoonRuntime.surface()&&!SalahMoonRuntime.state.legacyFallback'))
            report['workerEvents']=page.evaluate('__mq.events');report['serverRequests']=served
            check('ordinary-local-transport',entry!='http' or all(any(s.split('?')[0].endswith(n) for s in served) for n in ['/index.html','/moon/moon-host.js','/moon/assets/dem.bin.gz','/moon/assets/colour.bin.gz']),requests=served)
            check('no-unexpected-page-errors',not errors)
            context.close();browser.close();report['status']='PASS_SCOPED'
    except Exception:
        report['status']='FAIL';report['exception']=traceback.format_exc()
    finally:
        server.shutdown();save()
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);a.add_argument('--entry',choices=['http','file-index','file-offline'],default='http');a.add_argument('--no-phase-series',action='store_true');x=a.parse_args()
    r=run(x.root,x.output,x.entry,not x.no_phase_series);print(json.dumps({k:r.get(k) for k in ['status','entry','prayerReadySeconds','previewSeconds','refinedSeconds','exception']},indent=2));raise SystemExit(0 if r['status']=='PASS_SCOPED' else 1)
