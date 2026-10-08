"""Presented lunar continuity, not a settled-ready-only assertion.

Uses isolated profiles and the existing current-provider fixture lane. A public
entry is fetched from Pages, with an explicitly labelled Orlando/time fixture;
it is not a reconstruction of the owner's unrecorded weather or location.
"""
import argparse, hashlib, json, shutil, sys, time, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
import hotfix_stress_check as h
from browser_runtime import launch_browser, browser_identity
from runtime_identity import runtime_identity

OBSERVE=r'''(()=>{
 const W=Worker;window.__lunarContinuity={events:[],surfaces:{},frames:[]};
 window.Worker=class extends W{constructor(...args){super(...args);let lunar=false;const post=this.postMessage.bind(this);
 this.postMessage=(m,t)=>{if(m.kind==='boot')lunar='offline' in m;if(lunar&&['render','cancel'].includes(m.kind))__lunarContinuity.events.push({at:performance.now(),direction:'submit',kind:m.kind,id:m.id,identity:m.identity,scene:m.scene,native:window.SalahMoonHost?.capture()});return t?post(m,t):post(m);};
 this.addEventListener('message',e=>{if(!lunar)return;const m=e.data;if(['preview','result','error','boot-error','ready'].includes(m.kind)){__lunarContinuity.events.push({at:performance.now(),direction:'receive',kind:m.kind,id:m.id,identity:m.identity,quality:m.diagnostics?.quality,native:window.SalahMoonHost?.capture()});if(m.surfaceLinear)__lunarContinuity.surfaces[m.kind]=m;}});
 }};
})();'''

STATE=r'''()=>{
 const st=q=>{const e=document.querySelector(q);if(!e)return null;const c=getComputedStyle(e),r=e.getBoundingClientRect();return {display:c.display,visibility:c.visibility,opacity:+c.opacity,x:r.x,y:r.y,w:r.width,h:r.height};};
 const m=window.SalahMoonRuntime,host=window.SalahMoonHost?.capture(),card=document.querySelector('.c');
 const surface=!!m?.surface(),detail=window.SalahMoonDetail?.state;
 return {at:performance.now(),utc:host?.utcMs,host,moon:m?.state,detail,surface,moonGeometry:typeof moonSky==='undefined'?null:moonSky,
  presentationUp:m?.presentationUp,readyClass:card?.classList.contains('moon-ready'),skyClass:card?.className,
  layers:Object.fromEntries(['.moon','.mfeatures','.mphoto','.moccluder','.moon-mask-disc','.moon-detail-canvas','.mcorona'].map(q=>[q,st(q)])),
  acceptedSky:window.realSkyState?.().displayed,physicalMoon:window.realSkyState?.().last?.physicalState?.moon,weather:window.qaState?.().wxTruth,
  fx:card?.dataset.fx,precip:card?.dataset.precip,rainVisible:[...document.querySelectorAll('.drop')].filter(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility==='visible'&&+s.opacity>.03;}).length,
  timetable:typeof model==='function'?(()=>{const a=model();return a?{current:a.currentKey,next:a.nextKey,nextEpoch:Number.isFinite(a.nextEpoch)?a.nextEpoch:null,ready:Number.isFinite(a.nextEpoch)}:null;})():null};
}'''

def run(a):
 a.out.mkdir(parents=True,exist_ok=True)
 sys.path.insert(0,str(h.ROOT/'tests'));from v1_browser import fonts,ROOT_KEY,SETTINGS
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out)
 h.MONITOR+=OBSERVE
 shutil.copy2(Path(__file__),a.out/'harness.py')
 report={'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'status':'RUNNING','runtime':runtime_identity(a.root),'publicEntry':a.public,'scope':'Ordinary 1x accepted clock; sanitized Orlando 28.5383,-81.3792/time/current-weather fixture. Moon overrides explicitly recorded. Earliest capture is observed, never fabricated 0ms.'}
 h.dump(a.out/'results.json',report)
 try:
  with sync_playwright() as pw:
   b=launch_browser(pw);report['browser']=browser_identity(b)
   e=h.Entry(b,a.root,a.out,ff,direct=a.direct,start=a.start,family=a.family,overrides=a.overrides,dpr=a.dpr)
   try:
    if a.public:
     # Keep the same normal parent and exact iframe attributes; only src changes.
     settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'Central Florida fixture','method':'2','units':'c'}
     e.context.add_init_script('if(location.hostname==="theislampill.github.io")localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
     e.context.route('https://theislampill.github.io/salah_widget/**',lambda r:r.continue_())
     url='https://theislampill.github.io/salah_widget/'+e.suffix
     if a.direct:e.page.goto(url,wait_until='domcontentloaded');e.frame=e.page.main_frame;e.element=e.frame.locator('.c')
     else:
      e.page.locator('iframe').evaluate('(el,url)=>el.src=url',url);e.frame=e.page.frames[1]
      e.frame.wait_for_url('https://theislampill.github.io/salah_widget/**',timeout=45000)
     e.frame.wait_for_function('!!window.SalahMoonRuntime',timeout=45000)
    e.frame.evaluate('window.__lunarSample='+STATE)
    e.frame.evaluate('''()=>{let last=null;function tick(){try{
     // Per-frame observation must not run qaState's full cloud-buffer readback
     // or serialize the whole model. Full receipts are sampled with screenshots.
     const c=document.querySelector('.c'),g=getComputedStyle(document.querySelector('.moon')),f=getComputedStyle(document.querySelector('.mfeatures')),d=document.querySelector('.moon-detail-canvas'),p=getComputedStyle(document.querySelector('.mphoto'));
     const detail=d?.style.visibility==='visible',base=c.classList.contains('real-sky-composed')||c.classList.contains('real-sky-preview-ready');
     const visible=!!(c.classList.contains('moon-ready')&&g.visibility==='visible'&&+g.opacity*+f.opacity>.01&&(detail||base||p.visibility==='visible'));
     const at=performance.now(),owner=detail?'device-terrain':base?'base-composite':p.visibility==='visible'?'svg':'none';
     if(!last||visible!==last.visible||owner!==last.owner||at-last.at>=1000){
      const m=SalahMoonRuntime.state,h=SalahMoonHost.capture();const row={at,utc:h.utcMs,visible,owner,current:m.current,quality:m.quality,source:m.visibleSource,status:m.status,epoch:m.epoch,phase:h.fraction,up:h.up};
      __lunarContinuity.frames.push(row);last=row;
     }
     }catch(error){__lunarContinuity.error=String(error);}requestAnimationFrame(tick);}tick();}''')
    begin=time.monotonic();rows=[];next_at=begin;first_ready=None;actions=[];weather_history=[];other_actions=0
    with (a.out/'frames.jsonl').open('w',encoding='utf-8') as log:
     while time.monotonic()-begin<a.duration:
      now=time.monotonic()
      if now<next_at:e.page.wait_for_timeout(min(100,(next_at-now)*1000));continue
      if a.transitions and first_ready is not None:
       age=now-begin-first_ready
       # Provider retry has its own real60s throttle. Hold each family until
       # an ACTUAL current record and its visible effect have been consumed;
       # a requested fixture is not evidence that rain reached the widget.
       if age>=10 and len(weather_history)<3 and (not weather_history or weather_history[-1].get('acceptedAt') is not None and now-begin-weather_history[-1]['acceptedAt']>=5):
        family=['partial','rain','clear'][len(weather_history)];e.family=family;e.frame.evaluate('()=>startWeather()')
        weather_history.append({'family':family,'requestedAt':now-begin,'responseStart':len(e.responses)});actions.append({'action':family,'wallSeconds':now-begin})
       schedule=[(70,'below'),(90,'above'),(110,'failure'),(125,'retry')]
       if other_actions<len(schedule) and age>=schedule[other_actions][0]:
        _,action=schedule[other_actions];before=e.frame.evaluate(STATE)
        if action in ['above','below']:
         e.frame.evaluate('alt=>{SIM.moonAlt=String(alt);renderMoon();render();SalahMoonRuntime.request();}',25 if action=='above' else -20)
        elif action=='failure':
         e.frame.evaluate('()=>{SalahMoonRuntime.refresh();__h8MoonWorker.onerror({message:"controlled replacement failure"});}')
        else:assert e.frame.evaluate('SalahMoonRuntime.retry()')
        actions.append({'action':action,'wallSeconds':now-begin,'before':before,'after':e.frame.evaluate(STATE)});other_actions+=1
      s=e.frame.evaluate(STATE);s['wallSeconds']=now-begin;s['capture']=f'frame-{len(rows):04}.png'
      if weather_history and weather_history[-1].get('acceptedAt') is None:
       stage=weather_history[-1];code=h.FAMILIES[stage['family']][0];wet=stage['family']=='rain'
       expected_fx={'partial':'cloud','rain':'rain','clear':'clear'}[stage['family']]
       if s['weather']['rawCode']==code and s['weather']['lane']=='live' and s['fx']==expected_fx and (s['precip']=='on' and s['rainVisible']>0 if wet else s['precip']=='off' and s['rainVisible']==0):
        stage.update(acceptedAt=now-begin,code=code,fx=s['fx'],precip=s['precip'],rainVisible=s['rainVisible'],observedPresent=s['weather']['observedPresent'],source=s['weather']['model'])
      e.element.screenshot(path=a.out/s['capture']);s['capturedAt']=e.frame.evaluate('performance.now()')
      rows.append(s);log.write(json.dumps(s)+'\n');log.flush()
      if s['moon']['quality']=='empirical-adaptive' and s['surface'] and first_ready is None:first_ready=s['wallSeconds']
      if first_ready is not None and now-begin>=max(65,first_ready+10) and not a.full_duration and (not a.transitions or len(actions)==7 and len(weather_history)==3 and weather_history[-1].get('acceptedAt') is not None and now-begin-weather_history[-1]['acceptedAt']>=5 and s['moon']['renders']>=2 and s['moon']['status']=='ready'):break
      next_at=now+(1 if now-begin<65 else 2)
    telemetry=e.frame.evaluate('({events:__lunarContinuity.events,frames:__lunarContinuity.frames,error:__lunarContinuity.error})')
    h.dump(a.out/'telemetry.json',telemetry)
    first_surface=next((x['wallSeconds'] for x in rows if x['surface']),None)
    blanks=[{'at':x['wallSeconds'],'moon':x['moon'],'host':x['host']} for x in rows if first_surface is not None and x['wallSeconds']>first_surface and not x['surface']]
    first_visible=next((x['at'] for x in telemetry['frames'] if x['visible']),None)
    layer_gaps=[x for x in telemetry['frames'] if first_visible is not None and x['at']>first_visible and not x['visible']]
    checks={'refinedObserved':first_ready is not None,'noWithdrawalAfterCurrentSurface':not blanks,'originalGeometryBound':all(not x['surface'] or x['moon']['phasePrecision']['targetPositionErrorBound']<=.041600001 for x in rows),'noPageErrors':not e.errors,'noLocalAssetFailures':not e.failures,'currentProviderConsumed':bool(e.responses)}
    checks['visibleLayerContinuity']=first_visible is not None and not layer_gaps
    if a.transitions:checks['weatherHorizonFailureRecovery']=len(actions)==7 and rows[-1]['moon']['renders']>=2 and not blanks
    if a.transitions:checks['currentWeatherSequenceConsumed']=len(weather_history)==3 and all(x.get('acceptedAt') is not None and not x['observedPresent'] for x in weather_history)
    report.update(actions=actions,weatherHistory=weather_history,status='PASS_SCOPED' if all(checks.values()) else 'FAIL',checks=checks,firstSurfaceSeconds=first_surface,unexpectedWithdrawals=blanks,visibleLayerGaps=layer_gaps,firstRefinedSeconds=first_ready,wallSeconds=time.monotonic()-begin,captures=len(rows),errors=e.errors,requests=e.requests,responses=e.responses,initial=rows[0],final=rows[-1])
    # Save true worker surfaces as crops for independent pixel comparison. No
    # material, exposure, geometry or lighting is changed for this diagnostic.
    import base64
    for kind in ['preview','result']:
     data=e.frame.evaluate('''kind=>{const m=__lunarContinuity.surfaces[kind];if(!m)return null;const c=document.createElement('canvas');c.width=m.width;c.height=m.height;c.getContext('2d').putImageData(new ImageData(m.rgba,m.width,m.height),0,0);return {png:c.toDataURL().split(',')[1],scene:m.scene,identity:m.physicalIdentity,quality:m.diagnostics.quality};}''',kind)
     if data:(a.out/(kind+'-surface.png')).write_bytes(base64.b64decode(data.pop('png')));h.dump(a.out/(kind+'-surface.json'),data)
   finally:e.close();b.close()
 except Exception:report.update(status='FAIL',exception=traceback.format_exc())
 report['runtimeUnchanged']=report['runtime']==runtime_identity(a.root)
 h.dump(a.out/'results.json',report)
 print(json.dumps({k:report.get(k) for k in ['status','wallSeconds','firstRefinedSeconds','captures','exception']},indent=2),flush=True)
 return report['status']!='FAIL'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=h.ROOT);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--dpr',type=float,default=1);p.add_argument('--public',action='store_true');p.add_argument('--direct',action='store_true');p.add_argument('--duration',type=float,default=300);p.add_argument('--full-duration',action='store_true');p.add_argument('--transitions',action='store_true');p.add_argument('--start',default='2026-10-08T02:00:00Z');p.add_argument('--family',default='clear');p.add_argument('--overrides',default='simMoon=.5&simWax=0&simMoonAlt=25&simMoonH=42');raise SystemExit(0 if run(p.parse_args()) else 1)
