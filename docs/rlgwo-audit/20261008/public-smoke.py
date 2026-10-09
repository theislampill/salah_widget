"""Serial public rollout smoke; real clock/providers, isolated public-site fixture.
No routes, fake clocks, service workers, user profile, or production mutations.
"""
import argparse, json, time, sys, threading, traceback, hashlib
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

R=Path(__file__).parent
W=Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
sys.path.insert(0,str(W/'tools/cp9'))
from browser_runtime import launch_browser, browser_identity
from moon_continuity_check import STATE as MOON_STATE
PUBLIC='https://theislampill.github.io/salah_widget/'
SETTINGS={'v':1,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'Orlando public fixture','method':'2','school':'0','time':'24','datefmt':'YYYY-MM-DD','units':'c','lp':0,'seed':1,'source':'manual'}
class Parent(BaseHTTPRequestHandler):
 def do_GET(self):
  url=PUBLIC+('v1/' if 'v1' in self.path else '')+'#local=1'
  data=('<!doctype html><meta charset="utf-8"><title>Public deployment iframe check</title><style>body{margin:0;background:#162033}</style><iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="'+url+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden" scrolling="no"></iframe>').encode()
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass

INIT=r'''(()=>{
 window.__release={events:[],frames:[],errors:[]};
 const W=Worker;window.Worker=class extends W{constructor(...args){super(...args);let lunar=false;const post=this.postMessage.bind(this);this.postMessage=(m,t)=>{if(m.kind==='boot')lunar='offline' in m;if(lunar&&['render','cancel'].includes(m.kind))__release.events.push({at:performance.now(),way:'submit',kind:m.kind,id:m.id,identity:m.identity,scene:m.scene});return t?post(m,t):post(m);};this.addEventListener('message',e=>{const m=e.data;if(lunar&&['preview','result','error','ready','boot-error'].includes(m.kind))__release.events.push({at:performance.now(),way:'receive',kind:m.kind,id:m.id,identity:m.identity,quality:m.diagnostics?.quality});});}};
 let last,started=false;function tick(){try{const c=document.querySelector('.c'),me=document.querySelector('.moon'),f=document.querySelector('.mfeatures');if(c&&me&&f&&window.SalahMoonRuntime){const g=getComputedStyle(me),fs=getComputedStyle(f),d=document.querySelector('.moon-detail-canvas'),p=document.querySelector('.mphoto'),ps=p&&getComputedStyle(p),m=SalahMoonRuntime.state;
 const detail=d?.style.visibility==='visible',base=c.classList.contains('real-sky-composed')||c.classList.contains('real-sky-preview-ready'),visible=!!(c.classList.contains('moon-ready')&&g.visibility==='visible'&&+g.opacity*+fs.opacity>.01&&(detail||base||ps?.visibility==='visible')),owner=detail?'device-terrain':base?'base-composite':ps?.visibility==='visible'?'svg':'none',at=performance.now();
 if(!last||last.visible!==visible||last.owner!==owner||last.quality!==m.quality||at-last.at>=1000){last={at,visible,owner,quality:m.quality,status:m.status,current:m.current,source:m.visibleSource,epoch:m.epoch};__release.frames.push(last);}
 }}catch(e){if(!__release.errors.includes(String(e)))__release.errors.push(String(e));}requestAnimationFrame(tick);}requestAnimationFrame(tick);
})();'''

STATE=r'''()=>{const q=typeof qaState==='function'?qaState():null,m=typeof model==='function'?model():null,c=document.querySelector('.c'),r=c?.getBoundingClientRect();return {at:performance.now(),utc:Date.now(),accepted:window.SalahNativeSkyHost?.capture(),scale:typeof TIMESCALE==='undefined'?null:TIMESCALE,config:window.SalahConfig?.loadLocal(),prayer:q?.cache,model:m?{current:m.currentKey,next:m.nextKey,nextEpoch:m.nextEpoch,nextTime:m.nextTime}:null,rows:[...document.querySelectorAll('.times .p')].map(e=>({text:e.innerText,key:e.dataset.key,classes:e.className})),countdown:document.querySelector('.left')?.innerText,date:document.querySelector('.d')?.innerText,weather:q?.wxTruth,weatherHeader:q?.weatherHeader,fx:c?.dataset.fx,precip:c?.dataset.precip,sky:window.realSkyState?.(),moon:window.SalahMoonRuntime?.state,detail:window.SalahMoonDetail?.state,surface:!!window.SalahMoonRuntime?.surface(),card:r?{x:r.x,y:r.y,w:r.width,h:r.height}:null,bodyClass:c?.className,storage:Object.fromEntries(['salah_widget:config:v1','salah_widget:v1:config:v1'].map(k=>[k,localStorage.getItem(k)])),resources:performance.getEntriesByType('resource').filter(x=>x.name.includes('salah_widget')).map(x=>({url:x.name,transferSize:x.transferSize,encodedBodySize:x.encodedBodySize,duration:x.duration}))};}'''
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def sample(page,frame,out,rows,label):
 # Frozen V1's model() assumes admitted prayer data. Do not invoke that test
 # accessor during acquisition; observe its rendered shell and readiness first.
 s=frame.evaluate(STATE.replace("m=typeof model==='function'?model():null", "m=q?.cache?.prayerLoaded&&typeof model==='function'?model():null"));s['label']=label;s['capture']=f'{len(rows):04}-{label}.png'
 frame.locator('.c').screenshot(path=out/s['capture'],animations='allow');s['capturedAt']=frame.evaluate('performance.now()');rows.append(s);dump(out/'frames.json',rows);return s

def check_settings(frame,version):
 frame.evaluate('()=>{if(typeof _enableSettingsAffordance==="function")_enableSettingsAffordance()}')
 frame.locator('.buckle').click(force=True);frame.locator('#set-label').wait_for(state='visible',timeout=5000)
 value=frame.locator('#set-label').input_value();frame.locator('#setClose').click(force=True)
 if version=='root':
  frame.locator('#ceDateButton').click(force=True);frame.locator('#dateDialog').wait_for(state='visible',timeout=5000);frame.locator('#dateClose').click(force=True)
 else:assert frame.locator('#ce').inner_text() and frame.locator('#ah').inner_text()
 return {'settingsLabel':value,'settingsOpenedClosed':True,'dates':'root date dialog opened/closed' if version=='root' else 'frozen V1 CE/AH text read (no new date-dialog control in V1)'}

def run(browser_name,continuation=False):
 out=R/('public-'+browser_name+('-continuation' if continuation else ''));out.mkdir(exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Parent);threading.Thread(target=server.serve_forever,daemon=True).start()
 report={'status':'RUNNING','startedAt':datetime.now(timezone.utc).isoformat(),'AUDIT_SHA':json.loads((R/'release.json').read_text())['mergeCommit'],'scope':'Public Pages; real current UTC and providers; saved manual public Orlando fixture, not owner location; no simulation or transport interception; HTTP cache remains enabled. Screenshots are timestamped samples, ownership monitored on rAF with 1s stored heartbeat.','cases':[],'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};dump(out/'results.json',report)
 try:
  with sync_playwright() as pw:
   browser=launch_browser(pw);report['browser']=browser_identity(browser)
   # One page/worker group at a time. Each mode has a fresh context (cold), then real reload (warm).
   for mode in ['iframe','direct']:
    context=browser.new_context(viewport={'width':390,'height':600},timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference',device_scale_factor=1)
    context.add_init_script('if(location.hostname==="theislampill.github.io"){for(const k of ["salah_widget:config:v1","salah_widget:v1:config:v1"])if(!localStorage.getItem(k))localStorage.setItem(k,JSON.stringify({...'+json.dumps(SETTINGS)+',savedAt:Date.now()}));}')
    context.add_init_script(INIT)
    for version in ['root','v1']:
     if continuation and mode=='iframe' and version=='root':continue
     page=context.new_page();errors=[];failed=[];responses=[]
     page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure}));page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}))
     path=PUBLIC+('v1/' if version=='v1' else '')+'#local=1';url=f'http://127.0.0.1:{server.server_port}/{version}.html' if mode=='iframe' else path
     for warm in [False,True]:
      name=f'{version}-{mode}-'+('warm' if warm else 'cold');caseout=out/name;caseout.mkdir(exist_ok=True);rows=[]
      if warm:page.reload(wait_until='domcontentloaded')
      else:page.goto(url,wait_until='domcontentloaded')
      frame=page.frames[1] if mode=='iframe' else page.main_frame
      frame.locator('.c').wait_for(timeout=60000)
      begin=time.monotonic();first_refined=None;replacement=None;settings=None
      for sec in [0,.25,.5,1,2,5,10]:
       page.wait_for_timeout(max(0,(begin+sec-time.monotonic())*1000));sample(page,frame,caseout,rows,'startup-'+str(sec))
      frame.wait_for_function('typeof qaState==="function" && qaState().cache.prayerLoaded',timeout=60000)
      settings=check_settings(frame,version)
      long=version=='root' and mode=='iframe'
      deadline=begin+(420 if long else 65 if version=='root' else 15)
      next_capture=time.monotonic()
      while time.monotonic()<deadline:
       page.wait_for_timeout(max(0,(next_capture-time.monotonic())*1000));s=sample(page,frame,caseout,rows,'normal-1x')
       if version=='root' and s.get('surface') and (s.get('moon')or{}).get('quality')=='empirical-adaptive':
        if first_refined is None:first_refined={'wall':time.monotonic()-begin,'renders':s['moon'].get('renders',0),'at':s['at']}
        # Exercise a normal-current replacement without changing time, phase, location or weather. This is an explicit request, not a claimed natural bucket boundary.
        if long and replacement is None and time.monotonic()-begin>first_refined['wall']+10:
         before=s;frame.evaluate('SalahMoonRuntime.refresh()');replacement={'requestedAt':frame.evaluate('performance.now()'),'rendersBefore':s['moon'].get('renders',0),'trigger':'explicit refresh at unchanged normal 1x scene','before':before}
        elif replacement and s['moon'].get('renders',0)>replacement['rendersBefore'] and s['at']>replacement['requestedAt']+10000:
         replacement['acceptedAt']=s['at'];replacement['after']=s
         if time.monotonic()-begin>=65:break
       if not long and time.monotonic()-begin>= (15 if version=='v1' else 30):break
       next_capture=time.monotonic()+2
      s=rows[-1];telemetry=frame.evaluate('window.__release');dump(caseout/'telemetry.json',telemetry)
      seen=[x for x in telemetry['frames'] if x['visible']];first=seen[0]['at'] if seen else None;gaps=[x for x in telemetry['frames'] if first is not None and x['at']>first and not x['visible']]
      checks={'cardGeometry':s['card']['w']==325 and s['card']['h']==530,'sixRows':len(s['rows'])==6,'countdown':bool(s['countdown']),'date':bool(s['date']),'prayerReady':bool(s.get('prayer',{}).get('prayerLoaded')),'settingsUsable':bool(settings),'normal1x':s['scale']==1,'noRuntimeErrors':not errors,'noLocalAssetFailures':not [x for x in failed if x['url'].startswith(PUBLIC) and 'ABORT' not in str(x)],'localAssetHTTP':all(x['status']<400 for x in responses if x['url'].startswith(PUBLIC))}
      if version=='root':checks.update({'moonObserverNoError':not telemetry['errors'],'noVisibleMoonWithdrawal':not gaps,'surfaceAcquired':any(x.get('surface') for x in rows)})
      if long:checks.update({'fullTerrain':first_refined is not None,'currentReplacement':bool(replacement and replacement.get('acceptedAt'))})
      rootstorage=frame.evaluate('localStorage.getItem("salah_widget:config:v1")')
      if version=='v1':
       # Mutate only this disposable profile's V1 label through its real settings consumer, then verify root remains unchanged.
       frame.locator('.buckle').click(force=True);frame.locator('#set-label').fill('V1 isolated fixture');frame.locator('#setClose').click(force=True);page.wait_for_timeout(1000)
       checks['v1RootStorageIsolation']=frame.evaluate('localStorage.getItem("salah_widget:config:v1")')==rootstorage
       checks['v1SavedOwnKey']='V1 isolated fixture' in (frame.evaluate('localStorage.getItem("salah_widget:v1:config:v1")')or'')
       checks['v1AssetsScoped']=not any('/salah_widget/config.js' in x['url'] for x in responses)
      case={'name':name,'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'settings':settings,'firstRefined':first_refined,'replacement':replacement,'visibleGaps':gaps,'wallSeconds':time.monotonic()-begin,'captures':len(rows),'initial':rows[0],'final':s,'errors':errors,'failedRequests':failed,'responses':responses};dump(caseout/'results.json',case);report['cases'].append(case);dump(out/'results.json',report);print(name,case['status'],{k:v for k,v in checks.items() if not v},flush=True)
     page.close()
    context.close()
   browser.close()
  report['status']='PASS' if all(x['status']=='PASS' for x in report['cases']) else 'FAIL'
 except Exception:report.update(status='FAIL',exception=traceback.format_exc());print(report['exception'],flush=True)
 finally:server.shutdown()
 report['finishedAt']=datetime.now(timezone.utc).isoformat();dump(out/'results.json',report);print(report['status'],flush=True);return report['status']=='PASS'
if __name__=='__main__':
 import os
 p=argparse.ArgumentParser();p.add_argument('--browser',choices=['chromium','firefox'],required=True);p.add_argument('--continuation',action='store_true');a=p.parse_args();os.environ['SALAH_BROWSER']=a.browser;raise SystemExit(0 if run(a.browser,a.continuation) else 1)
