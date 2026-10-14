"""Serial native date probes and exact-runtime font probes. Preparation is not qualification.

The worker never executes --execute without the root's capacity-one lease.
No source writes, builds, persistent profile, clipboard or system clock changes.
"""
import argparse,hashlib,html as html_module,importlib.util,json,mimetypes,os,platform,re,shutil,subprocess,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin,urlparse

HERE=Path(__file__).resolve().parent
FIXTURE=HERE/'rlgwo-clock-date-fixture.cjs'
VARIANTS={
 'wall':{'prayer':['default'],'promotion':['default'],'held':['default'],'back-late':['default'],
   'retry':['wall-plus','wall-minus'],'visibility':['default'],'modes':['ordinary','scale1','scale60','frozen','sim1','sim60']},
 'timezone':{'scenes':['default','gap','fold-invalid','fold-valid'],'recovery':['gap','provider-zone'],
   'capture':['default','obsolete','ignored-zone-mutant'],'track':['default','gap','fold-invalid','duplicate','decreasing','invalid-current'],
   'modes':['ordinary','default','scale1','scale60'],'profiles':['instrumented','uninstrumented']},
 'access':{'keyboard':['default'],'touch':['default'],'presets':['long','saved-long','preset-us','preset-eu','before'],
   'long':['very-long','long-month','literal','month-literal','unescaped-control'],
   'font':['missing','delayed-css-forenoon','delayed-bytes-forenoon','split-face-forenoon','loaded-forenoon','permanent-bytes-forenoon','warm-cache-forenoon','loaded-sunrise','loaded-maghrib'],
   'transitions':['default'],'effects':['default'],'builder':['default']}}
VARIANTS['wall']['back-late']=['current8-back7','prefetch8-back7','prefetch9-back7']
RUNNER_CASES={suite:set(cases) for suite,cases in VARIANTS.items()}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def check(condition,label):
 if not condition:raise AssertionError(label)
 return {'label':label,'result':'PASS'}

def css_font_families(css,url):
 """Observe declared face URLs from actual returned CSS, without loading substitutes."""
 found={}
 for block in re.findall(r'@font-face\s*\{([^{}]*)\}',css,re.S):
  family=re.search(r'font-family\s*:\s*([^;]+)',block)
  if not family:continue
  family=family.group(1).strip().strip('"\'')
  if family not in {'Fraunces','Inter'}:continue
  for declared in re.findall(r'url\(\s*([^)]*?)\s*\)',block):found[urljoin(url,declared.strip().strip('"\''))]=family
 return found

class Server:
 def __init__(self,root,page,entry_hash,runtime_identity=None):
  self.root=Path(root).resolve();self.page=Path(page).read_bytes();self.receipts=[];self.entry_hash=entry_hash;self.runtime_identity=runtime_identity
  allowed={('/'+name):(self.root/name,identity) for name,identity in (runtime_identity or {}).get('files',{}).items()}
  for name,(target,identity) in allowed.items():
   check(target.resolve().is_relative_to(self.root) and name=='/'+target.relative_to(self.root).as_posix(),'Exact inventory path remains under selected source root')
  owned=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    name=urlparse(self.path).path
    if name in ['/','/index.html']:data,ctype,status=owned.page,'text/html; charset=utf-8',200
    elif name=='/config.js':data,ctype,status=(owned.root/'config.js').read_bytes(),'text/javascript; charset=utf-8',200
    elif name=='/builder.html':data,ctype,status=(owned.root/'builder.html').read_bytes(),'text/html; charset=utf-8',200
    elif name=='/offscreen-host.html':
     href=html_module.escape('/index.html'+owned.entry_hash,quote=True)
     data=(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0}}iframe{{display:block;border:0;width:325px;height:530px}}.spacer{{height:2500px}}</style><iframe id="widget" src="{href}"></iframe><div class="spacer"></div>').encode()
     ctype,status='text/html; charset=utf-8',200
    elif name in allowed:
     target,identity=allowed[name];data=target.read_bytes()
     ctype={'.mjs':'text/javascript; charset=utf-8','.js':'text/javascript; charset=utf-8','.wasm':'application/wasm','.css':'text/css; charset=utf-8','.json':'application/json'}.get(target.suffix,mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
     status=200 if len(data)==identity['bytes'] and hashlib.sha256(data).hexdigest()==identity['sha256'] else 409
     if status!=200:data=b'Runtime inventory file changed after binding'
    else:data,ctype,status=b'Explicit date-only optional transport unavailable','text/plain',503
    if owned.runtime_identity and name in allowed and name not in ['/','/index.html'] and status==200:
     identity=allowed[name][1]
     if len(data)!=identity['bytes'] or hashlib.sha256(data).hexdigest()!=identity['sha256']:data,status=b'Runtime inventory file changed after binding',409
    owned.receipts.append({'path':name,'status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'runtimeInventory':name in allowed})
    self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
  self.httpd=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  self.thread=threading.Thread(target=self.httpd.serve_forever,daemon=True);self.thread.start()
  self.origin='http://127.0.0.1:'+str(self.httpd.server_port)
 def close(self):self.httpd.shutdown();self.httpd.server_close();self.thread.join()

class NativeHostUnsupported(RuntimeError):pass

READ="""() => {const f=window.__rlgwo,s=f.read(),d=document.querySelector('#dateDialog');
 const geometry=selector=>{const e=document.querySelector(selector);if(!e)return null;const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,font:c.fontFamily,fontSize:c.fontSize,whiteSpace:c.whiteSpace,overflowWrap:c.overflowWrap,visibility:c.visibility,direction:c.direction};};
 const ink=selector=>{const e=document.querySelector(selector);if(!e)return null;const r=document.createRange();r.selectNodeContents(e);const b=r.getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,width:b.width,height:b.height};};
 const cn=geometry('.cn'),nt=ink('.nt'),hz=geometry('.arc .horizon'),bar=geometry('.bar'),rail=document.querySelector('.arc .rail');
 let railObservation=null;if(rail){const matrix=rail.getScreenCTM(),length=rail.getTotalLength(),points=[];if(matrix)for(let i=0;i<=200;i++){const p=rail.getPointAtLength(length*i/200),q=new DOMPoint(p.x,p.y).matrixTransform(matrix);points.push({x:q.x,y:q.y});}railObservation={length,points,scope:'Readonly screen-coordinate path samples; no inferred glyph clearance or pixel verdict.'};}
 return {...s,requests:f.requestReadback(),effects:f.effectsReadback(),frames:f.frames,timers:f.timers,inputEvents:f.inputEvents,fitMeasurements:f.fitMeasurements,trace:f.trace,
 capabilities:{dialogElement:typeof HTMLDialogElement==='function',showModal:typeof d?.showModal==='function',close:typeof d?.close==='function',maxTouchPoints:navigator.maxTouchPoints,intersectionObserver:typeof IntersectionObserver==='function',fontFaceSet:!!document.fonts},
 fonts:{status:document.fonts?.status||'unsupported',faces:Array.from(document.fonts||[],f=>({family:f.family,status:f.status})),fraunces:document.fonts?.check('600 24px "Fraunces"'),inter:document.fonts?.check('400 14px "Inter"')},
 typography:{cnFit:s.cnFit,currentInk:ink('.cn'),heroInk:nt,horizon:hz,bar,rail:railObservation,heroCenterError:nt&&hz&&bar?(nt.top+nt.bottom)/2-(hz.y+bar.y)/2:null},
 dom:{current:document.querySelector('.cn')?.textContent,next:document.querySelector('.nt')?.textContent,countdown:document.querySelector('.left')?.textContent,sim:document.querySelector('.simclock')?.textContent,rows:document.querySelectorAll('.p').length,ce:document.querySelector('#ce')?.textContent,ah:document.querySelector('#ah')?.textContent,gregorian:document.querySelector('#dateGregorian')?.textContent,hijri:document.querySelector('#dateHijri')?.textContent,preview:document.querySelector('#datePreview')?.textContent,reason:document.querySelector('#dateReason')?.textContent,ceLabel:document.querySelector('#ceDateButton')?.getAttribute('aria-label'),ahLabel:document.querySelector('#ahDateButton')?.getAttribute('aria-label'),active:document.activeElement?.id,hasFocus:document.hasFocus(),open:d?.open,modal:d?.matches(':modal'),canary:window.__sw_sec_probe,svg:!!d?.querySelector('svg'),viewport:[innerWidth,innerHeight,devicePixelRatio]},
 geometry:Object.fromEntries(['.c','.e','.times','.d','.cn','.nt','.arc .rail','.arc .horizon','.bar','#dateDialog','#dateGregorian','#dateHijri','#dateClose'].map(x=>[x,geometry(x)]))};}"""

def wait_ready(page,invalid=False):
 if invalid:page.wait_for_function("window.__rlgwo?.read().valid===false")
 else:page.wait_for_function("window.__rlgwo?.read().loopStarted===true && document.querySelectorAll('.p').length===6")
 page.evaluate('window.__rlgwo.waitFrames(2)')

def capture(page,out,name,states):
 state=page.evaluate(READ);states.append({'name':name,'state':state})
 surface=page if hasattr(page,'screenshot') else page.page
 surface.screenshot(path=str(out/(name+'.png')))
 return state

def step(page,wall=None,mono=None):
 previous=page.evaluate("window.__rlgwo.trace.filter(x=>x.event==='actual-render').length")
 if wall is not None:page.evaluate('(v)=>window.__rlgwo.setWall(v)',wall)
 if mono is not None:page.evaluate('(v)=>window.__rlgwo.setMono(v)',mono)
 page.wait_for_function("(count)=>window.__rlgwo.trace.filter(x=>x.event==='actual-render').length>count",arg=previous)
 page.evaluate('window.__rlgwo.waitFrames(2)')

def pending(page,kind,day=None):
 return page.evaluate("([kind,day])=>window.__rlgwo.requestReadback().filter(x=>x.kind===kind&&!x.settled&&(!day||x.day===day))",[kind,day])
def wait_pending(page,kind,day=None):
 page.wait_for_function("([kind,day])=>window.__rlgwo?.requestReadback().some(x=>x.kind===kind&&!x.settled&&(!day||x.day===day))",arg=[kind,day])
 return pending(page,kind,day)[0]
def release(page,row,value=None):page.evaluate('([id,value])=>window.__rlgwo.release(id,value)',[row['id'],value])
def policy(page,key,value):page.evaluate('([key,value])=>window.__rlgwo.policy(key,value)',[key,value])

def loop_frames(state):return [row for row in state['frames'] if row['event']=='fired' and row['name']=='loop']
def settle_prayers(page):page.wait_for_function("__rlgwo.read().slots.current===null && __rlgwo.read().slots.prefetch===null")

def retry_case(page,variant,out):
 states=[];checks=[]
 # Native retry timers really run; the driver advances only the independent fixture clock before their callbacks.
 for delay,mono in [(900,900),(1800,2700)]:
  page.wait_for_function("(ms)=>__rlgwo?.timers.some(x=>x.event==='requested'&&x.ms===ms) && !__rlgwo.timers.some(x=>x.event==='fired'&&x.ms===ms)",arg=delay)
  page.evaluate('(n)=>__rlgwo.setMono(n)',mono)
  page.wait_for_function("(ms)=>__rlgwo.timers.some(x=>x.event==='fired'&&x.ms===ms)",arg=delay)
 page.wait_for_function("__rlgwo.read().loopStarted && __rlgwo.requestReadback().filter(x=>x.kind==='prayer').length===3 && __rlgwo.read().slots.current===null")
 failed=capture(page,out,'three-native-attempts-failed',states)
 requests=[r for r in failed['requests'] if r['kind']=='prayer']
 checks.append(check([r['mono'] for r in requests]==[0,900,2700],'Actual attempts at monotonic 0/900/2700'))
 checks.append(check(failed['cooldown']['current']['nextTry']==60000,'Owning operation eligibility remains 60000'))
 policy(page,'prayer:07-09-2026','hold')
 sign=-1 if variant=='wall-minus' else 1
 base=failed['clock']['wall'];page.evaluate('(v)=>__rlgwo.setWall(v)',base+sign*3600000)
 for mono in [59000,59999]:
  page.evaluate('(n)=>__rlgwo.setMono(n)',mono);page.evaluate('__rlgwo.waitFrames(3)')
  state=capture(page,out,'before-eligibility-'+str(mono),states)
  checks.append(check(len([r for r in state['requests'] if r['kind']=='prayer'])==3,'No fourth attempt before '+str(mono)))
  checks.append(check(any(f['mono']==mono for f in loop_frames(state)),'Actual scheduled loop observes '+str(mono)))
 page.evaluate('__rlgwo.setMono(60000)');held=wait_pending(page,'prayer','07-09-2026')
 eligible=capture(page,out,'one-owning-retry-at-60000',states)
 checks.append(check(held['mono']==60000 and held['owner']['operationId']!=requests[-1]['owner']['operationId'],'One new eligible owning operation'))
 page.evaluate('__rlgwo.waitFrames(20)');busy=capture(page,out,'busy-owner-repeated-native-frames',states)
 checks.append(check(len([r for r in busy['requests'] if r['kind']=='prayer'])==4,'Held owner prevents overlap over repeated frames'))
 release(page,held);wait_ready(page);capture(page,out,'recovered-six-rows',states)
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Injected wall/elapsed clocks; native scheduler/timers; no OS clock or sleep claim.']

def back_late_case(page,variant,out):
 states=[];checks=[]
 if variant=='current8-back7':
  current8=wait_pending(page,'prayer','08-09-2026');capture(page,out,'cold-current8-held',states)
  policy(page,'prayer:07-09-2026','hold');page.evaluate('__rlgwo.setWall("2026-09-07T23:59:59Z")');release(page,current8)
  current7=wait_pending(page,'prayer','07-09-2026');before=capture(page,out,'reverse-before-corrected7',states)
  checks.append(check(before['day']!='08-09-2026' and before['today'] is None,'Cold late8 never adopted as current7'))
  release(page,current7);wait_ready(page);after=capture(page,out,'corrected7-starts-real-loop',states)
  checks.append(check(after['day']=='07-09-2026','Actual loader admits corrected day7'))
  next8=wait_pending(page,'prayer','08-09-2026');release(page,next8);settle_prayers(page)
  final=capture(page,out,'day8-nextDay-only',states)
  checks.append(check(final['day']=='07-09-2026' and final['tomorrow']['date']['gregorian']['date']=='08-09-2026','Day8 eligible nextDay remains distinct from current7'))
 elif variant=='prefetch8-back7':
  wait_ready(page);next8=wait_pending(page,'prayer','08-09-2026');capture(page,out,'warm7-next8-held',states)
  step(page,'2026-09-08T00:00:01Z');current8=wait_pending(page,'prayer','08-09-2026')
  # Two different real operations now own the same requested day; choose by observed slot/operation identity.
  rows=pending(page,'prayer','08-09-2026');current8=next(r for r in rows if r['owner']['kind']=='current')
  step(page,'2026-09-07T23:59:59Z');release(page,next8)
  page.wait_for_function("__rlgwo.read().tomorrow?.date.gregorian.date==='08-09-2026'")
  returned=capture(page,out,'prefetch8-classified-after-reverse',states)
  checks.append(check(returned['day']=='07-09-2026' and returned['tomorrow']['date']['gregorian']['date']=='08-09-2026','Pending next8 classifies as nextDay7 on reverse settlement'))
  policy(page,'prayer:07-09-2026','hold');release(page,current8);current7=wait_pending(page,'prayer','07-09-2026');release(page,current7);settle_prayers(page)
  capture(page,out,'late-current8-corrected7',states)
 else:
  wait_ready(page);next9=wait_pending(page,'prayer','09-09-2026');capture(page,out,'warm8-next9-held',states)
  policy(page,'prayer:07-09-2026','hold');step(page,'2026-09-07T23:59:59Z');current7=wait_pending(page,'prayer','07-09-2026')
  release(page,next9);page.evaluate('__rlgwo.waitFrames(2)');rejected=capture(page,out,'unrelated9-rejected-after-reverse',states)
  checks.append(check(rejected['tomorrow'] is None,'Unrelated day9 never retained as day7 nextDay'))
  checks.append(check(any(x['event']=='adoptPrayerBundle' and x['payloadDay']=='09-09-2026' and x['value'] is False for x in rejected['trace']),'Actual settlement classifier rejects unrelated day9'))
  release(page,current7);wait_ready(page);settle_prayers(page);capture(page,out,'matching7-recovered',states)
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Cold loader is not credited as a scheduled callback before its actual boot completes.']

def visibility_case(page,out):
 states=[];checks=[];wait_ready(page);settle_prayers(page);before=capture(page,out,'visible-before-injection',states)
 page.evaluate('__rlgwo.injectVisibility("hidden")');page.evaluate('__rlgwo.waitFrames(2)')
 hidden=capture(page,out,'injected-hidden-loop-cancelled',states)
 checks.append(check(not any(name=='loop' for _,name in hidden['activeFrames']),'Injected hidden state cancels actual clock-loop owner'))
 page.evaluate('__rlgwo.setWall("2026-09-08T00:00:01Z")');page.evaluate('__rlgwo.waitFrames(4)')
 quiet=capture(page,out,'hidden-wall-correction-no-catchup',states)
 checks.append(check(len(loop_frames(quiet))==len(loop_frames(hidden)),'No scheduled source clock callback during controlled hidden interval'))
 checks.append(check(len(quiet['requests'])==len(hidden['requests']),'Settled hidden control creates no missed-day request storm'))
 page.evaluate('__rlgwo.injectVisibility("visible")');page.wait_for_function("__rlgwo.read().day==='08-09-2026'");page.evaluate('__rlgwo.waitFrames(3)')
 resumed=capture(page,out,'first-resume-current-day8',states)
 checks.append(check(sum(name=='loop' for _,name in resumed['activeFrames'])==1,'Resume retains one active native clock loop'))
 checks.append(check(resumed['now']==resumed['clock']['wall'],'Resume consumes present device-wall fixture instant'))
 # A fresh real parent scrolls the unchanged widget iframe out of view: native IntersectionObserver, not a visibility-property stub.
 host=page.context.new_page();host.goto(page.url.split('/index.html')[0]+'/offscreen-host.html',wait_until='domcontentloaded')
 frame=host.frame_locator('#widget');host.wait_for_function("document.querySelector('#widget').contentWindow.__rlgwo?.read().loopStarted")
 widget=host.frames[1];settle_prayers(widget);native_before=capture(widget,out,'native-offscreen-before',states)
 host.mouse.wheel(0,900);host.wait_for_function("!document.querySelector('#widget').contentWindow.__rlgwo.activeFrames().some(x=>x[1]==='loop')")
 widget.evaluate('__rlgwo.setWall("2026-09-08T00:00:01Z")');widget.evaluate('__rlgwo.waitFrames(3)')
 native_hidden=capture(widget,out,'native-offscreen-correction',states)
 checks.append(check(not any(name=='loop' for _,name in native_hidden['activeFrames']),'Actual parent scrolling stops native IntersectionObserver clock loop'))
 host.mouse.wheel(0,-1200);host.wait_for_function("document.querySelector('#widget').contentWindow.__rlgwo.read().day==='08-09-2026'")
 native_resume=capture(widget,out,'native-offscreen-resume',states)
 checks.append(check(sum(name=='loop' for _,name in native_resume['activeFrames'])==1,'Native offscreen resume owns one callback'))
 host.close()
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Injected document hidden is not native sleep. Separate parent scroll is actual IntersectionObserver evidence; no OS suspend claim.']

TAIL="""selector=>{const e=document.querySelector(selector),d=document.querySelector('#dateDialog');const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let n,last;while(n=w.nextNode())if(n.textContent)last=n;if(!last)return null;const r=document.createRange();r.setStart(last,Math.max(0,last.length-4));r.setEnd(last,last.length);const b=r.getBoundingClientRect(),db=d.getBoundingClientRect();return {tail:last.textContent.slice(-4),x:b.left+b.width/2,y:b.top+b.height/2,width:b.width,height:b.height,visible:b.top>=db.top&&b.bottom<=db.bottom&&b.top>=0&&b.bottom<=innerHeight,dialog:{x:db.x,y:db.y,width:db.width,height:db.height},scrollTop:d.scrollTop,scrollHeight:d.scrollHeight,clientHeight:d.clientHeight};}"""

def touch_case(page,out):
 states=[];checks=[];wait_ready(page);settle_prayers(page)
 for trigger in ['ceDateButton','ahDateButton']:
  page.locator('#'+trigger).tap();opened=capture(page,out,trigger+'-native-tap',states)
  checks.append(check(opened['dom']['modal'],'Native touch tap opens '+trigger))
  tail=None
  for _ in range(100):
   tail=page.evaluate(TAIL,'#dateHijri')
   if tail['visible']:break
   d=tail['dialog'];page.mouse.move(d['x']+d['width']/2,d['y']+d['height']/2);page.mouse.wheel(0,180 if tail['y']>d['y']+d['height'] else -90);page.evaluate('__rlgwo.waitFrames(2)')
  checks.append(check(tail['visible'] and tail['tail']=='1448','Literal final year reached through native scroll input'))
  page.mouse.dblclick(tail['x'],tail['y']);selected=page.evaluate('window.getSelection().toString()')
  checks.append(check('1448' in selected,'Actual native pointer text selection obtains final year; no clipboard'))
  capture(page,out,trigger+'-selected-tail',states)
  # Native pointer-wheel return route, then actual touch Close.
  for _ in range(100):
   close=page.locator('#dateClose').bounding_box();dialog=page.locator('#dateDialog').bounding_box()
   if close and close['y']>=dialog['y'] and close['y']+close['height']<=dialog['y']+dialog['height']:break
   page.mouse.move(dialog['x']+dialog['width']/2,dialog['y']+dialog['height']/2);page.mouse.wheel(0,-250);page.evaluate('__rlgwo.waitFrames(2)')
  checks.append(check(close and close['y']>=dialog['y'] and close['y']+close['height']<=dialog['y']+dialog['height'],'Explicit native scroll route reaches Close before any automatic actionability scroll'))
  page.locator('#dateClose').tap();checks.append(check(page.evaluate('document.activeElement.id')==trigger,'Native Close returns connected initiator'))
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Taps use actual Playwright touch input. Scroll/selection use actual native pointer input in touch-enabled context; touch-drag acquisition is not claimed on either engine.']

def transitions_case(page,out):
 states=[];checks=[];wait_ready(page);next8=wait_pending(page,'prayer','08-09-2026');page.locator('#ceDateButton').click()
 page.evaluate("window.__transitionNodes=Object.fromEntries(['dateDialog','dateClose','dateGregorian','dateHijri','dateReason'].map(id=>[id,document.getElementById(id)]));window.__transitionMutations=[];window.__transitionObserver=new MutationObserver(rows=>__transitionMutations.push(...rows.map(r=>({type:r.type,target:r.target.id||r.target.parentElement?.id,attribute:r.attributeName}))));__transitionObserver.observe(document.getElementById('dateDialog'),{subtree:true,childList:true,characterData:true,attributes:true})")
 initial=capture(page,out,'open-before-maghrib',states);focus=initial['dom']['active']
 page.evaluate('__rlgwo.waitFrames(4)');checks.append(check(page.evaluate('__transitionMutations.length')==0,'Unchanged real frames do not rewrite full values'))
 step(page,'2026-09-07T18:00:00Z');missing=capture(page,out,'open-at-maghrib-missing-next',states)
 checks.append(check(missing['date']['unavailableReason']=='Sunset date update unavailable','Missing tomorrow gives exact sunset cue'))
 step(page,'2026-09-07T18:01:00Z');release(page,next8)
 page.wait_for_function("__rlgwo.read().date?.selectedSource==='tomorrow'")
 late=capture(page,out,'open-late-source-clears-cue',states);checks.append(check(late['date']['unavailableReason'] is None,'Real deferred next-day admission clears sunset cue'))
 step(page,'2026-09-07T17:59:59Z');reverse=capture(page,out,'open-reverse-before-boundary',states)
 checks.append(check(reverse['date']['selectedSource']=='today' and reverse['date']['previewDay']=='20','Reverse selection uses truthful present record and preview'))
 policy(page,'prayer:09-09-2026','hold');step(page,'2026-09-08T00:00:01Z');day8=capture(page,out,'open-midnight-prefetch8-promotion',states)
 next9=wait_pending(page,'prayer','09-09-2026');checks.append(check(day8['day']=='08-09-2026','Actual midnight promotion while same dialog stays open'))
 # Admitted optional AH absence: real loader consumes a declared complete Gregorian/timing record with AH=null.
 page.evaluate("__rlgwo.fixture.records['08-09-2026'].date.hijri=null")
 cfg=dict(day8['config']);cfg['label']='Madinah calendar unavailable'
 page.evaluate('(cfg)=>{window.__calendarUnavailable=__rlgwo.apply(cfg)}',cfg)
 page.wait_for_function("__rlgwo.read().today?.date.hijri===null && __rlgwo.read().date?.hijriText===''")
 unavailable=capture(page,out,'open-admitted-AH-unavailable',states)
 checks.append(check(unavailable['dom']['hijri']=='Hijri date unavailable','Unavailable full value clears prior year through actual loader'))
 # Next-day acquisition is held across another real midnight to obtain actual prayer-stale state.
 policy(page,'prayer:09-09-2026','hold');step(page,'2026-09-09T00:00:01Z');stale=capture(page,out,'open-real-stale-day-context',states)
 checks.append(check(stale['date']['staleDateState']=='prayer-stale','Prayer staleness is observed separately from missing AH'))
 checks.append(check(page.evaluate("Object.entries(__transitionNodes).every(([id,node])=>document.getElementById(id)===node)"),'Actual nodes stay connected across every transition'))
 checks.append(check(stale['dom']['open'] and stale['dom']['active']==focus,'Continuously open dialog retains observed focus'))
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Mutations/actual deferred loader boundaries observed; assistive-technology speech is unclaimed. Separate hostile native mutation control remains required.']

def profiles_case(page,variant,out):
 states=[];checks=[];wait_ready(page);settle_prayers(page);first=capture(page,out,'first-day-native-callers',states)
 actual=[x for x in first['trace'] if x['event']=='zoneDay']
 checks.append(check(any(x['args'][3]=='America/New_York' for x in actual),'Actual model/hourly callers reach native NY day profile'))
 if variant=='instrumented':checks.append(check(any(not x['hit'] and x['supported'] and x['projections']==4321 for x in actual),'Full inclusive 4321-minute native profile scan'))
 checks.append(check(any(x['hit'] for x in actual),'Actual same-day caller reuse'))
 for day in ['09','10','11','12']:
  step(page,'2026-03-'+day+'T12:00:00Z');page.wait_for_function('(day)=>__rlgwo.read().day===day',arg=day+'-03-2026');settle_prayers(page)
  current=capture(page,out,'distinct-day-'+day,states);checks.append(check(len(current['profileKeys'])<=4,'Four-profile bound on native day '+day))
 fifth=current
 checks.append(check('["America/New_York",2026,3,8]' not in fifth['profileKeys'],'Fifth distinct day evicts first'))
 step(page,'2026-03-08T12:00:00Z');page.wait_for_function("__rlgwo.read().day==='08-03-2026'");settle_prayers(page);revisit=capture(page,out,'evicted-day-native-revisit',states)
 builds=[x for x in revisit['trace'] if x['event']=='zoneDay' and not x['hit'] and x['supported']]
 checks.append(check(len([x for x in builds if x['args'][:3]==[2026,3,8]])>=2,'Evicted first day actually rebuilt on caller revisit'))
 if variant=='instrumented':checks.append(check(all(x['projections']==4321 for x in builds),'Every supported native build keeps exhaustive coverage'))
 # Actual key input and native callback heartbeat, without inventing a millisecond acceptance deadline.
 page.keyboard.press('Tab');page.evaluate('__rlgwo.waitFrames(12)');responsive=capture(page,out,'native-input-heartbeat',states)
 checks.append(check(any(x['event']=='keydown' and x['trusted'] for x in responsive['inputEvents']),'Actual trusted input reaches native document'))
 checks.append(check(len(loop_frames(responsive))>len(loop_frames(revisit)),'Native callback heartbeat remains observable'))
 timing={'coldMs':[x['durationMs'] for x in builds],'reuseMs':[x['durationMs'] for x in responsive['trace'] if x['event']=='zoneDay' and x['hit']],
   'scope':'Native Intl/resolver is uncounted in uninstrumented variant; readonly wrapper and input/callback trace overhead retained. No invented latency deadline.'}
 write(out/'profile-timing.json',timing)
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Independent responsiveness disposition and matched uninstrumented timing review remain required; unsupported synthetic profiles retain source-only scope.']

def builder_case(page,server,out):
 states=[];checks=[];page.set_viewport_size({'width':1000,'height':900});page.goto(server.origin+'/builder.html',wait_until='domcontentloaded')
 # Actual form inputs and source-generated URL/snippet; never click Copy/Install or touch a clipboard.
 for selector,value in [('#lat','24.47'),('#lon','39.61')]:page.locator(selector).fill(value)
 page.locator('#method').select_option('4');page.locator('#datefmt').select_option('DD MMMM YYYY')
 page.locator('#reload').click();page.wait_for_function("document.querySelector('#pv').contentWindow.__rlgwo?.read().loopStarted")
 widget=page.frames[1];wait_ready(widget);state=capture(widget,out,'builder-preview-inner-card',states)
 dimensions=page.locator('#pv').bounding_box();snippet=page.locator('#code').input_value()
 write(out/'builder-source-consumer.json',{'outer':dimensions,'inner':state['geometry']['.c'],'snippet':snippet,'viewport':state['dom']['viewport'],'builderSourceSha256':sha(server.root/'builder.html')})
 checks.append(check(state['geometry']['.c']['width']==325 and state['geometry']['.c']['height']==530,'Actual inner card remains 325×530'))
 # Retain the owner-amended gate even when pinned source presently emits 325×530.
 checks.append(check(dimensions['width']==330 and dimensions['height']==534,'Owner-approved production outer iframe is 330×534'))
 checks.append(check('width:330px;height:534px' in snippet,'Actual copy text has approved outer 330×534'))
 widget.locator('#ceDateButton').click();capture(widget,out,'builder-dialog-open',states);widget.locator('#dateClose').click()
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Builder hint discoverability and same-clock stack comparison still need independent pixel review. No Copy/Install action.']

def natural_fit_tick(page):
 before=page.evaluate("__rlgwo.trace.filter(x=>x.event==='fitCn').length")
 page.evaluate('__rlgwo.setWall(Date.now()+1000)')
 page.wait_for_function("(before)=>__rlgwo.trace.filter(x=>x.event==='fitCn').length>before",arg=before)
 page.evaluate('__rlgwo.waitFrames(2)')

def wait_real_fonts(page):
 page.wait_for_function("Array.from(document.fonts).some(f=>f.family.includes('Fraunces')&&f.status==='loaded') && Array.from(document.fonts).some(f=>f.family.includes('Inter')&&f.status==='loaded') && document.fonts.status==='loaded'")
 page.evaluate('document.fonts.ready')

def split_face_case(page,controller,out):
 states=[];checks=[];wait_ready(page);settle_prayers(page)
 first=capture(page,out,'split-first-natural-fallback-fit',states)
 checks.append(check(first['dom']['current']=='Forenoon','Actual model reaches Forenoon for split-face control'))
 page.wait_for_function("Array.from(document.fonts).some(f=>f.family.includes('Fraunces')&&f.status==='loading') && Array.from(document.fonts).some(f=>f.family.includes('Inter')&&f.status==='loading') && document.fonts.status==='loading'")
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  held=controller['pending']();families={row['family'] for row in held}
  if {'Fraunces','Inter'}<=families:break
  page.evaluate('__rlgwo.waitFrames(2)')
 else:raise NativeHostUnsupported('Actual returned CSS did not bind held Fraunces and Inter binary URLs; family-targeted split-face qualification unavailable. URLs are retained in receipts.')
 both=capture(page,out,'split-both-real-families-registered-bytes-held',states)
 controller['release']('binary','Fraunces')
 page.wait_for_function("Array.from(document.fonts).some(f=>f.family.includes('Fraunces')&&f.status==='loaded') && !Array.from(document.fonts).some(f=>f.family.includes('Fraunces')&&f.status==='loading') && Array.from(document.fonts).some(f=>f.family.includes('Inter')&&f.status==='loading') && document.fonts.status==='loading'")
 arrived=capture(page,out,'split-Fraunces-loaded-Inter-still-held',states)
 pending_after=controller['pending']()
 checks.append(check(any(row['family']=='Inter' for row in pending_after) and not any(row['family']=='Fraunces' for row in pending_after),'Only real Inter bytes remain held after all Fraunces releases'))
 baseline=len(arrived['fitMeasurements'])
 for _ in range(3):natural_fit_tick(page)
 natural=capture(page,out,'split-three-natural-fits-before-Inter-completion',states)
 records=[x for x in natural['trace'] if x['event']=='fitCn']
 def note(condition,label):checks.append({'label':label,'result':'PASS' if condition else 'FAIL'})
 note(natural['fonts']['status']=='loading' and any('Inter' in face['family'] and face['status']=='loading' for face in natural['fonts']['faces']),'Set-wide FontFaceSet remains loading throughout Fraunces-only natural-fit evidence')
 note(any(x['measurements']>0 and any('Fraunces' in f['family'] and f['status']=='loaded' for f in x['faces']) and any('Inter' in f['family'] and f['status']=='loading' for f in x['faces']) for x in records),'Natural fit measures arrived Fraunces while Inter remains pending')
 note(len(natural['fitMeasurements'])-baseline<=1,'Stable Fraunces arrival does not cause repeated fitting while Inter remains pending')
 note(not any(x['event']=='explicit-fit-invalidation-control' for x in natural['trace']),'Split-face natural path never forces a cache clear')
 # Preserve the causal interval before allowing the unrelated family to finish.
 write(out/'font-split-face-before-Inter.json',{'first':first,'bothHeld':both,'FrauncesOnly':arrived,'naturalBeforeInter':natural,'checksBeforeInter':checks,'heldBeforeRelease':held,'heldAfterFraunces':pending_after,'actualCssFamilyMap':controller['familyMap'],'fontResources':controller['events'],
   'scope':'Actual stylesheet-declared Fraunces bytes released; actual Inter bytes held. Raw _cnFit/faces and natural calls retained. No manual fit/render or cache invalidation; set-wide completion has not occurred.'})
 controller['release']('binary','Inter');wait_real_fonts(page)
 for _ in range(2):natural_fit_tick(page)
 terminal=capture(page,out,'split-Inter-later-completion-causal-control',states)
 note(terminal['fonts']['status']=='loaded','Later real Inter completion supplies a separate set-wide causal control')
 note(not any(x['event']=='explicit-fit-invalidation-control' for x in terminal['trace']),'Entire split-face case remains free of forced cache clears')
 return states,checks,'FAIL' if any(x['result']=='FAIL' for x in checks) else 'PARTIAL_NATIVE_SCOPE',[
  'Individual-family arrival is distinguished from later set-wide completion. The primary measurements/crops precede Inter release.',
  'Exact URLs/families are read from actual CSS response bytes; no local or forged font/FontFaceSet substitute.',
  'Independent rail/hero pixel review remains required; no invented alignment threshold or whole-renderer/first-scene qualification.']

def font_case(page,variant,controller,out):
 if variant.startswith('split-face'):return split_face_case(page,controller,out)
 states=[];checks=[];wait_ready(page);settle_prayers(page)
 initial=capture(page,out,'font-first-natural-fit',states)
 label='Sunrise' if 'sunrise' in variant else 'Maghrib' if 'maghrib' in variant else 'Forenoon'
 checks.append(check(initial['dom']['current']==label,'Actual model reaches canonical long label '+label))
 def note(condition,label):checks.append({'label':label,'result':'PASS' if condition else 'FAIL'})
 if variant.startswith('delayed-css'):
  note(not any('Fraunces' in f['family'] for f in initial['fonts']['faces']),'Delayed CSS first fit has genuinely unregistered Fraunces')
  # check() can be true here. It is recorded, never substituted for face presence.
  controller['release']('css');wait_real_fonts(page)
 elif variant.startswith('delayed-bytes'):
  page.wait_for_function("Array.from(document.fonts).some(f=>f.family.includes('Fraunces')&&f.status==='loading')")
  capture(page,out,'font-registered-bytes-pending',states);controller['release']('binary');wait_real_fonts(page)
 elif variant.startswith('permanent-bytes'):
  page.wait_for_function("document.fonts.status==='loaded' && Array.from(document.fonts).some(f=>f.family.includes('Fraunces')&&f.status==='error')")
  capture(page,out,'font-permanent-error',states)
 elif variant=='missing':
  page.wait_for_function("document.fonts.status==='loaded'")
 else:wait_real_fonts(page)
 arrival=capture(page,out,'font-terminal-state-before-next-native-fit',states)
 baseline_measurements=len(arrival['fitMeasurements'])
 for _ in range(3):natural_fit_tick(page)
 settled=capture(page,out,'font-after-three-natural-fit-calls',states)
 fits=[x for x in settled['trace'] if x['event']=='fitCn']
 if variant!='missing' and not variant.startswith('permanent-bytes'):
  note(any(x['measurements']>0 and any('Fraunces' in f['family'] and f['status']=='loaded' for f in x['faces']) for x in fits),'At least one natural actual fit measures the real loaded Fraunces generation')
  note(len(settled['fitMeasurements'])-baseline_measurements<=1,'Stable loaded generation avoids continuous expensive fitting')
 else:note(len(settled['fitMeasurements'])-baseline_measurements<=1,'Terminal permanent failure retains bounded stable fallback fitting')
 note(settled['geometry']['.c']['width']==325 and settled['geometry']['.c']['height']==530,'Typography keeps fixed inner card')
 # Named diagnostic control only, after all natural-fit evidence has been retained.
 # Do not invoke fitCn or render manually: the next real native callback consumes this explicit invalidation.
 page.evaluate('__rlgwo.invalidateFitControl()');natural_fit_tick(page)
 control=capture(page,out,'explicit-cache-invalidation-control',states)
 note(len(control['fitMeasurements'])>len(settled['fitMeasurements']),'Explicit invalidation control actually remeasures through natural callback')
 write(out/'font-natural-versus-control.json',{'variant':variant,'label':label,'first':initial['typography'],'arrival':arrival['typography'],
   'natural':settled['typography'],'control':control['typography'],'naturalFitRecords':fits,
   'fontResources':controller['events'],'cacheAttribution':controller.get('cacheEvents',[]),
   'scope':'Actual authored widget/Fraunces/native FontFaceSet. Natural path never clears _cnFit; explicit-control stage is excluded from production-fix claims. Pixel alignment needs independent review; no invented clearance threshold.'})
 if variant.startswith('warm-cache'):
  # Routing is disabled for this context: the reload can genuinely consume native HTTP/font caches.
  page.reload(wait_until='domcontentloaded');wait_ready(page);wait_real_fonts(page);natural_fit_tick(page)
  warm=capture(page,out,'same-context-warm-cache-reload',states)
  note(any(x['measurements']>0 and any('Fraunces' in f['family'] and f['status']=='loaded' for f in x['faces']) for x in warm['trace'] if x['event']=='fitCn'),'Warm entry naturally measures real Fraunces')
 return states,checks,'FAIL' if any(x['result']=='FAIL' for x in checks) else 'PARTIAL_NATIVE_SCOPE',[
  'Actual font lifecycle and raw geometry only; rail/hero alignment needs independent pixel disposition.',
  'Same-context warm reload is distinct from proven HTTP cache hits. Chromium passive CDP cache events are retained where available; Firefox cache attribution remains bounded.',
  'No substituted local font, forged FontFaceSet, pre-font first-layout equivalence or automatic whole-renderer closure.']

def native_case(page,suite,name,variant,metadata,out,environment):
 states=[];checks=[];p=metadata['plan']
 if suite=='access' and not page.evaluate("typeof document.getElementById('dateDialog')?.showModal==='function' && typeof document.getElementById('dateDialog')?.close==='function'"):
  raise NativeHostUnsupported('Actual declared engine lacks required native dialog capability; owner support/fallback gate stays open.')
 if suite=='wall' and name=='retry':return retry_case(page,variant,out)
 if suite=='wall' and name=='back-late':return back_late_case(page,variant,out)
 if suite=='wall' and name=='visibility':return visibility_case(page,out)
 if suite=='timezone' and name=='profiles':return profiles_case(page,variant,out)
 if suite=='access' and name=='touch':return touch_case(page,out)
 if suite=='access' and name=='transitions':return transitions_case(page,out)
 if suite=='access' and name=='builder':return builder_case(page,environment['server'],out)
 if suite=='access' and name=='font':return font_case(page,variant,environment['fonts'],out)
 invalid=suite=='timezone' and name in {'scenes','recovery'} and variant in {'gap','fold-invalid'}
 if suite=='timezone' and name=='recovery' and variant=='provider-zone':
  prayer=wait_pending(page,'prayer','08-03-2026');before=capture(page,out,'valid-UTC-held-provider',states)
  changed=json.loads(json.dumps(p['records']['08-03-2026']));changed['meta']['timezone']='America/New_York'
  release(page,prayer,changed);wait_ready(page,True);withdrawn=capture(page,out,'provider-zone-gap-withdrawal',states)
  checks.append(check(withdrawn['zone']=='America/New_York' and not withdrawn['valid'] and not withdrawn['anchorFinite'],'Actual provider-zone admission invalidates UTC 02:30 into NY gap with no numeric anchor'))
  cfg=dict(withdrawn['config']);cfg['tz']='UTC';cfg['label']='Recovered UTC after provider zone'
  page.evaluate("Object.values(__rlgwo.fixture.records).forEach(r=>r.meta.timezone='UTC')")
  page.evaluate('(cfg)=>{window.__providerRecovery=__rlgwo.apply(cfg)}',cfg);wait_ready(page);settle_prayers(page)
  recovered=capture(page,out,'provider-zone-actual-UTC-recovery',states)
  checks.append(check(recovered['valid'] and recovered['dom']['rows']==6,'Actual valid configuration recovers six rows after provider-zone invalidation'))
  checks.append(check(recovered['sceneBuilds']==before['sceneBuilds'],'Existing successful scene builders do not rerun on recovery'))
  return states,checks,'PARTIAL_NATIVE_SCOPE',['Provider metadata is a declared same-day admitted fixture; native rendered withdrawal/recovery still needs independent crop review.']
 if suite=='timezone' and name=='capture':
  wx=wait_pending(page,'weather');prayer=wait_pending(page,'prayer','08-03-2026')
  before=capture(page,out,'owning-before-zone-adoption',states)
  if variant=='obsolete':
   release(page,prayer);wait_ready(page);settle_prayers(page)
   cfg=dict(before['config']);cfg['tz']='Asia/Riyadh';cfg['label']='Riyadh successor operation'
   page.evaluate("Object.values(__rlgwo.fixture.records).forEach(r=>r.meta.timezone='Asia/Riyadh');const next=structuredClone(__rlgwo.fixture.weather);next.timezone='Asia/Riyadh';next.current.time='2026-03-08T10:30';next.hourly.time=['2026-03-08T10:30','2026-03-08T11:30'];__rlgwo.fixture.weather=next")
   page.evaluate('(cfg)=>{window.__obsoleteApply=__rlgwo.apply(cfg)}',cfg);wait_ready(page);settle_prayers(page)
   page.wait_for_function('(old)=>__rlgwo.requestReadback().some(r=>r.kind==="weather"&&!r.settled&&r.id!==old)',arg=wx['id'])
   successor=next(r for r in pending(page,'weather') if r['id']!=wx['id']);owning=capture(page,out,'successor-before-obsolete-body',states)
   release(page,wx);page.evaluate('__rlgwo.waitFrames(6)');after_old=capture(page,out,'obsolete-body-no-effect',states)
   checks.append(check(after_old['generation']==owning['generation'] and after_old['slots']['weather']['operationId']==owning['slots']['weather']['operationId'],'Obsolete weather settlement cannot clear its actual successor slot'))
   checks.append(check(after_old['weather']==owning['weather'] and after_old['track']==owning['track'] and after_old['effects']['storage']==owning['effects']['storage'],'Obsolete body neither adopts nor writes cache'))
   release(page,successor);page.wait_for_function("__rlgwo.read().weather!==null && __rlgwo.read().slots.weather===null")
   complete=capture(page,out,'Riyadh-successor-complete',states)
   checks.append(check(complete['weather']['currentValidAt']==1772955000000 and complete['weatherEligibility']['sourceAgeMs']==300000,'Actual new Riyadh 10:30 body commits the literal fresh instant'))
   return states,checks,'PARTIAL_NATIVE_SCOPE',['Obsolete rejection may precede parsing; this run is separate from same-generation captured-zone conversion.']
  changed=json.loads(json.dumps(p['records']['08-03-2026']));changed['meta']['timezone']='Asia/Riyadh'
  release(page,prayer,changed);page.wait_for_function("__rlgwo.read().zone==='Asia/Riyadh'")
  mid=capture(page,out,'zone-adopted-weather-still-owned',states)
  checks.append(check(mid['generation']==before['generation'],'Eligible prayer adoption preserves generation'))
  checks.append(check(mid['slots']['weather']['operationId']==before['slots']['weather']['operationId'],'Captured weather owner unchanged'))
  release(page,wx);page.wait_for_function("__rlgwo.read().weather!==null && __rlgwo.read().slots.weather===null")
  after=capture(page,out,'captured-zone-completion',states)
  literal=1772955000000 # 2026-03-08T07:30:00.000Z
  if variant=='ignored-zone-mutant':
   calls=[x for x in after['trace'] if x['event']=='epochForTzTime' and len(x['args'])==6 and x['args'][3:5]==[3,30] and x['args'][5]=='America/New_York' and x['globalZone']=='Asia/Riyadh']
   checks.append(check(calls and after['weather']['currentValidAt']==1772929800000 and after['weather']['currentValidAt']!=literal,'Reached ignored-zone native mutant yields Riyadh 00:30 rather than captured NY 07:30'))
   return states,checks,'MUTANT_DETECTED',['This disposable mutated-source result needs its separate healthy captured-zone control; it is not a product PASS.']
  checks.append(check(after['weather']['currentValidAt']==literal,'Reached captured NY current epoch is literal 07:30Z'))
  checks.append(check(after['track']['ep'][0]==literal,'Reached captured NY hourly epoch is literal 07:30Z'))
  checks.append(check(after['weatherEligibility']['sourceAgeMs']==300000,'Source age 300000ms'))
  calls=[x for x in after['trace'] if x['event']=='epochForTzTime' and len(x['args'])==6 and x['args'][3:5]==[3,30]]
  checks.append(check(any(x['args'][5]=='America/New_York' and x['globalZone']=='Asia/Riyadh' for x in calls),'Sixth captured zone reaches actual resolver after global change'))
  return states,checks,'PARTIAL_NATIVE_SCOPE', ['Separate obsolete-generation and reached ignored-zone-mutant results remain required before combined qualification.']
 if suite=='wall' and name=='held':
  wait_ready(page);warm=capture(page,out,'warm-boot-cache7-loop',states)
  checks.append(check(any(x[0].startswith('salah:') for x in warm['effects']['storage']),'Warm boot persists admitted cache7'))
  # A fulfilled day8 from warm boot is cleared by actual applyConfig/reset; new-generation body policies hold both requests.
  policy(page,'prayer:07-09-2026','hold');policy(page,'prayer:08-09-2026','hold');policy(page,'prayer:09-09-2026','hold')
  cfg=dict(warm['config']);cfg['label']='Madinah refreshed'
  page.evaluate('(cfg)=>{window.__heldApply=__rlgwo.apply(cfg)}',cfg)
  current=wait_pending(page,'prayer','07-09-2026');next8=wait_pending(page,'prayer','08-09-2026')
  refreshed=capture(page,out,'new-generation-current7-prefetch8',states)
  checks.append(check(refreshed['loopStarted'] and refreshed['generation']==warm['generation']+1,'Label-only actual apply retains running loop'))
  step(page,'2026-09-08T00:00:01Z');release(page,next8)
  page.wait_for_function("__rlgwo.read().day==='08-09-2026'")
  next9=wait_pending(page,'prayer','09-09-2026');successor=capture(page,out,'prefetch9-owning-before-current7-finally',states)
  release(page,current);corrected=wait_pending(page,'prayer','08-09-2026');release(page,corrected)
  page.wait_for_function("__rlgwo.read().slots.current===null")
  after=capture(page,out,'current-finally-preserves-prefetch9',states)
  checks.append(check(after['day']=='08-09-2026','Late current7 never relabeled8'))
  checks.append(check(after['slots']['prefetch']['operationId']==successor['slots']['prefetch']['operationId'],'Current finally does not clear successor prefetch9'))
  checks.append(check(len([x for x in after['requests'] if x['kind']=='prayer' and x['day']=='08-09-2026' and x['id']>current['id']])<=2,'One corrected current8 plus separate prefetch8 within distinct owners'))
  release(page,next9);page.wait_for_function("__rlgwo.read().slots.prefetch===null");capture(page,out,'settled-day8-next9',states)
  return states,checks,'PARTIAL_NATIVE_SCOPE',['Shared attempt-budget trace and independent review required.']
 wait_ready(page,invalid)
 if suite=='access':settle_prayers(page)
 initial=capture(page,out,'initial',states)
 if invalid:
  checks += [check(initial['dom']['countdown']=='Simulation time unavailable','Invalid scene has exact unavailable text'),check(initial['dom']['next']=='—','Invalid next time em dash'),check(initial['dom']['sim']=='SIM unavailable','SIM unavailable')]
  if name=='recovery':
   cfg=dict(initial['config']);cfg['tz']='UTC'
   # Change only declared provider inputs before the actual config loader begins.
   page.evaluate("Object.values(__rlgwo.fixture.records).forEach(r=>r.meta.timezone='UTC')")
   page.evaluate('(cfg)=>{window.__recovery=__rlgwo.apply(cfg)}',cfg);wait_ready(page)
   valid=capture(page,out,'recovered-UTC-six-rows',states)
   checks.append(check(valid['dom']['rows']==6 and valid['valid'],'Actual UTC recovery renders six rows'))
   bad=dict(cfg);bad['tz']='America/New_York';page.evaluate('(cfg)=>{window.__recovery=__rlgwo.apply(cfg)}',bad)
   wait_ready(page,True);capture(page,out,'invalid-again-NY',states)
   page.evaluate('(cfg)=>{window.__recovery=__rlgwo.apply(cfg)}',cfg);wait_ready(page)
   recovered=capture(page,out,'second-UTC-recovery',states)
   checks.append(check(recovered['dom']['rows']==6 and recovered['valid'],'Actual second recovery works'))
   checks.append(check(recovered['sceneBuilds']==valid['sceneBuilds'] and recovered['sceneBuilds']=={'stars':1,'weather':1},'Successful scene builders initialize once across valid/invalid/valid recovery'))
   return states,checks,'PARTIAL_NATIVE_SCOPE',['Separate provider-zone reinitialization and actual crop/visibility review remain required.']
 elif suite=='wall' and name=='prayer':
  checks.append(check(initial['dom']['current']=='Dhuhr','Before Asr current Dhuhr'))
  step(page,'2026-09-07T15:30:01Z');forward=capture(page,out,'forward',states)
  checks.append(check(forward['dom']['current']=='Asr','Scheduled forward current Asr'))
  step(page,'2026-09-07T15:29:59Z');back=capture(page,out,'backward',states)
  checks.append(check(back['dom']['current']=='Dhuhr','Scheduled backward current Dhuhr'))
  checks.append(check(back['clock']['mono']==initial['clock']['mono'],'Independent monotonic unchanged'))
 elif suite=='wall' and name=='promotion':
  page.wait_for_function("__rlgwo.read().tomorrow?.date.gregorian.date==='08-09-2026'")
  step(page,'2026-09-08T00:00:01Z');forward=capture(page,out,'promoted8',states)
  checks.append(check(forward['day']=='08-09-2026' and forward['today']['date']['gregorian']['date']=='08-09-2026','Actual completed prefetch promotes matching day8'))
  step(page,'2026-09-07T23:59:59Z');page.wait_for_function("__rlgwo.read().day==='07-09-2026'");back=capture(page,out,'reverse7',states)
  checks.append(check(back['date']['requestedGregorianDay']=='07-09-2026','Reverse selector has no future hold'))
 elif name=='modes':
  anchor=initial['now'];page.evaluate('window.__rlgwo.setMono(1000)')
  rate=0 if variant in {'frozen','default'} else 60 if variant in {'scale60','sim60'} else 1
  for offset in [3600000,-3600000,7200000,-7200000]:
   page.evaluate('(wall)=>__rlgwo.setWall(wall)',initial['clock']['wall']+offset);page.evaluate('__rlgwo.waitFrames(4)')
   after=capture(page,out,'independent-wall-step-'+str(offset),states)
   want=after['clock']['wall'] if variant=='ordinary' else anchor+1000*rate
   checks.append(check(after['now']==want,'Literal authority/rate after mono+1000 and wall step '+str(offset)))
   checks.append(check(after['clockMode']['followWall']==(variant=='ordinary') and after['clockMode']['advancing']==(variant!='ordinary' and rate>0),'Actual default/ADVANCING intention remains bound to explicit mode'))
 elif suite=='timezone' and name=='scenes':
  want=1793521800000 if variant=='fold-valid' else 1772955000000
  checks.append(check(initial['now']==want,'Literal valid inverse instant'))
  checks.append(check(initial['dom']['rows']==6,'Healthy six rows'))
 elif suite=='timezone' and name=='track':
  page.wait_for_function("__rlgwo.read().slots.weather===null && __rlgwo.read().weather!==null")
  after=capture(page,out,'current-track-settled',states)
  checks.append(check((after['track'] is None)==(variant!='default'),'Whole invalid/non-increasing track rejected without sorting'))
  if variant=='invalid-current':checks.append(check(after['weatherEligibility']['sourceAgeMs'] is None and not after['weatherEligibility']['eligible'],'Invalid current epoch never supplies finite age'))
  else:checks.append(check(after['weatherEligibility']['eligible'],'Valid current independently remains eligible'))
 elif suite=='access':
  before=initial['effects'];dialog=page.locator('#dateDialog')
  if name=='long' and variant=='unescaped-control':
   page.locator('#ceDateButton').click();page.wait_for_function("window.__sw_sec_probe===1 && !!document.querySelector('#dateDialog svg')")
   reached=capture(page,out,'native-unescaped-positive-control',states)
   checks.append(check(reached['dom']['svg'] and reached['dom']['canary']==1,'Reached disposable unescaped full-value sink creates SVG and fires literal canary'))
   page.locator('#dateClose').click()
   return states,checks,'MUTANT_DETECTED',['Disposable altered sink is a positive security control only; healthy literal variants must separately remain SVG-free/canary0.']
  if name=='effects':
   page.evaluate('__rlgwo.waitFrames(6)');control=capture(page,out,'equal-clock-non-opening-control',states)
   checks.append(check(control['effects']==before,'Equal-clock settled native control has stable requests/storage'))
   for trigger in ['ceDateButton','ahDateButton']:
    page.locator('#'+trigger).click();page.evaluate('__rlgwo.waitFrames(6)');opened=capture(page,out,trigger+'-read-only-open',states);page.locator('#dateClose').click()
    after=capture(page,out,trigger+'-read-only-closed',states)
    checks.append(check(opened['effects']==before and after['effects']==before,'Native disclosure has no request/storage effects from '+trigger))
    checks.append(check(after['config']==initial['config'] and after['today']==initial['today'] and after['tomorrow']==initial['tomorrow'] and after['date']==initial['date'],'Native read retains config/admission/calendar projection from '+trigger))
   return states,checks,'PARTIAL_NATIVE_SCOPE',['Comparison excludes qaState storage probes; both interaction and equal-clock non-opening control use settled actual provider ownership.']
  if name=='keyboard':
   for trigger in ['ceDateButton','ahDateButton']:
    # Start from real document tab order. Programmatic focus is never used for reachability.
    found=False
    for _ in range(20):
     page.keyboard.press('Tab')
     if page.evaluate('document.activeElement.id')==trigger:found=True;break
    checks.append(check(found,'Actual Tab reaches '+trigger))
    for key in ['Enter','Space']:
     page.keyboard.press(key);checks.append(check(dialog.evaluate("e=>e.open&&e.matches(':modal')"),key+' opens native modal'))
     containment=page.evaluate("()=>{const outcomes=[];for(const element of document.querySelectorAll('button')){if(element.closest('#dateDialog')||element.disabled)continue;element.focus();outcomes.push({attempt:element.id,active:document.activeElement.id,hasFocus:document.hasFocus(),inside:!!document.activeElement.closest('#dateDialog')})}return outcomes}")
     checks.append(check(all(r['inside'] or not r['hasFocus'] for r in containment),'Native modal rejects attempted background date/settings-button focus'))
     page.evaluate("window.__dateClose=document.querySelector('#dateClose')")
     page.keyboard.press('Tab');page.evaluate('window.__rlgwo.waitFrames(2)')
     checks.append(check(page.evaluate("window.__dateClose===document.querySelector('#dateClose')"),'Tick preserves Close identity'))
     step(page,'2026-09-07T18:00:00Z' if key=='Enter' else '2026-09-07T17:59:59Z')
     checks.append(check(page.evaluate("window.__dateClose===document.querySelector('#dateClose') && (!document.hasFocus() || document.activeElement.closest('#dateDialog')!==null)"),'Changed projection preserves native modal focus/Close node; browser UI transfer allowed'))
     page.keyboard.press('Escape');checks.append(check(page.evaluate('document.activeElement.id')==trigger,'Escape returns initiating trigger'))
  else:
   page.locator('#ceDateButton').click();opened=capture(page,out,'open',states)
   for selector in ['#dateGregorian','#dateHijri']:
    g=opened['geometry'][selector];checks.append(check(g['fontSize']=='14px' and g['whiteSpace']=='normal' and g['overflowWrap']=='anywhere','Existing complete-value 14px/wrap '+selector))
    checks.append(check(g['scrollWidth']<=g['clientWidth']+0.5,'No horizontal clipping '+selector))
   dialog.evaluate('e=>e.scrollTop=e.scrollHeight');capture(page,out,'scrolled-tail',states)
   checks.append(check(opened['dom']['gregorian']==opened['date']['gregorianText'] and opened['dom']['hijri']==opened['date']['hijriText'],'One last-painted full-value projection'))
   checks.append(check(not opened['dom']['svg'] and opened['dom']['canary']==0,'Hostile content remains literal'))
   dialog.evaluate('e=>e.scrollTop=0');page.locator('#dateClose').click()
  after=capture(page,out,'closed',states)
  if name=='effects':checks.append(check(after['effects']==before,'Equal-clock read causes no storage/request effects; qaState excluded'))
  if name=='font':return states,checks,'PARTIAL_NATIVE_SCOPE',['Capture font readiness/loaded faces and original CSS settlement independently; no first-layout equivalence.']
 return states,checks,'PARTIAL_NATIVE_SCOPE',['Named local probes only; full per-obligation review/mutants/release/closure remain required.']

def main(suite):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,required=True);parser.add_argument('--engine',choices=['chromium','firefox'],required=True)
 parser.add_argument('--cases',required=True);parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--variants',help='Optional exact variant subset for a bounded first control')
 parser.add_argument('--node',default=shutil.which('node'));parser.add_argument('--execute',action='store_true');parser.add_argument('--lease-id')
 parser.add_argument('--expected-source-sha256',default='51c09cfdd0bb535018ba76c02878c7bb8574b82a957de0c62392ed379f4834ef')
 args=parser.parse_args();root=args.root.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 names=args.cases.split(',');unknown=set(names)-set(VARIANTS[suite])
 if sha(root/'index.html')!=args.expected_source_sha256:parser.error('Generated source hash differs from explicitly selected target')
 if unknown:parser.error('Unknown cases '+','.join(sorted(unknown)))
 if args.execute and not args.lease_id:parser.error('--execute requires the root-issued capacity-one lease id')
 if args.execute and set(names)-RUNNER_CASES[suite]:parser.error('These case bodies are prepared, but native driver actions are not yet implemented: '+','.join(sorted(set(names)-RUNNER_CASES[suite])))
 inventory=None;inventory_path=None
 if suite=='access' and 'font' in names:
  identity_tool=root/'tools/cp9/runtime_identity.py'
  if not identity_tool.is_file():parser.error('Actual font probes require the full selected runtime and tools/cp9/runtime_identity.py; a material-only snapshot is insufficient')
  identity_spec=importlib.util.spec_from_file_location('rlgwo_runtime_identity',identity_tool);identity_module=importlib.util.module_from_spec(identity_spec);identity_spec.loader.exec_module(identity_module)
  inventory=identity_module.runtime_identity(root)
  check(inventory['files']['index.html']['sha256']==args.expected_source_sha256,'Full runtime identity matches selected generated entry')
  inventory_path=out/'font-runtime-identity.json';write(inventory_path,inventory)
 inputs=[]
 for name in names:
  selected=VARIANTS[suite][name] if not args.variants else args.variants.split(',')
  if set(selected)-set(VARIANTS[suite][name]):parser.error('Unknown variants for '+name+': '+','.join(sorted(set(selected)-set(VARIANTS[suite][name]))))
  for variant in selected:
   target=out/(name+'--'+variant);target.mkdir(exist_ok=True)
   prefix=target/'input'
   command=[args.node,str(FIXTURE),str(root),suite,name,variant,str(prefix)]
   if name=='font':command.append(str(inventory_path))
   result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8');(target/'prepare.log').write_text(result.stdout+result.stderr,encoding='utf-8')
   if result.returncode:raise RuntimeError('Fixture preparation failed '+str(target/'prepare.log'))
   metadata=json.loads(prefix.with_suffix('.json').read_text(encoding='utf-8'));inputs.append((name,variant,target,prefix.with_suffix('.html'),metadata))
 manifest={'schema':'rlgwo-native-driver-run/1','suite':suite,'root':str(root),'engineRequested':args.engine,
  'driverSha256':sha(__file__),'adapterSha256':sha(FIXTURE),'execution':'NOT_EXECUTED' if not args.execute else 'ATTEMPTED',
  'leaseId':args.lease_id,'inputs':[{'case':n,'variant':v,'metadata':str(t/'input.json'),'identity':m['identity']} for n,v,t,_,m in inputs],
  'runtimeIdentity':{'path':str(inventory_path),'treeSha256':inventory['treeSha256'],'toolSha256':sha(root/'tools/cp9/runtime_identity.py')} if inventory else None,
  'scope':'Font cases serve exact runtime_identity assets and use native same-origin asset fetch; controlled providers and unrelated HTTP503. Other cases retain date-only HTTP503. Instrumented clocks/storage/callback observers; no whole-sky, terrain, motion, presentation timing or first-layout equivalence.',
  'screenshotFontReadinessWait':'disabled by PW_TEST_SCREENSHOT_NO_FONTS_READY=1 for font probes' if inventory else 'Playwright default'}
 write(out/'manifest.json',manifest)
 if not args.execute:print(json.dumps({'status':'PREPARED_NOT_EXECUTED','manifest':str(out/'manifest.json')}));return
 # Deferred import: --help and preparation do not import Playwright or launch anything.
 if inventory:os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 from playwright.sync_api import sync_playwright
 spec=importlib.util.spec_from_file_location('rlgwo_browser_runtime',root/'tools/cp9/browser_runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
 os.environ['SALAH_BROWSER']=args.engine
 rows=[]
 with sync_playwright() as playwright:
  browser=runtime.launch_browser(playwright);manifest['browser']=runtime.browser_identity(browser)
  try:
   for name,variant,target,html,metadata in inputs:
    server=Server(root,html,metadata['plan']['hash'],inventory if name=='font' else None);context=browser.new_context(viewport={'width':325,'height':530},device_scale_factor=1,has_touch=True)
    delayed=[];font_events=[];cache_events=[];font_family_map={}
    def font_family(url):return font_family_map.get(url)
    font_policy=('missing' if variant=='missing' else 'delayed-css' if variant.startswith('delayed-css') else 'delayed-binary' if variant.startswith('delayed-bytes') else 'split-face' if variant.startswith('split-face') else 'permanent-binary' if variant.startswith('permanent-bytes') else 'warm-cache' if variant.startswith('warm-cache') else 'loaded') if name=='font' else 'missing'
    def font_route(route):
     kind='css' if 'fonts.googleapis.com' in route.request.url else 'binary'
     font_events.append({'event':'request','url':route.request.url,'kind':kind,'policy':font_policy,'family':font_family(route.request.url)})
     if font_policy=='missing':route.fulfill(status=503,body='Declared missing-font control')
     elif font_policy=='delayed-css' and kind=='css':delayed.append((kind,route))
     elif font_policy=='delayed-binary' and kind=='binary':delayed.append((kind,route))
     elif font_policy=='split-face' and kind=='binary':delayed.append((kind,route))
     elif font_policy=='permanent-binary' and kind=='binary':route.fulfill(status=503,body='Declared permanent-font-binary failure')
     else:route.continue_()
    # Routing disables HTTP cache. Warm and ordinary loaded cases deliberately have no font route.
    if font_policy not in {'loaded','warm-cache'}:
     context.route('https://fonts.googleapis.com/**',font_route);context.route('https://fonts.gstatic.com/**',font_route)
    def release_fonts(kind,family=None):
     chosen=[entry for entry in delayed if entry[0]==kind and (family is None or font_family(entry[1].request.url)==family)]
     for entry in chosen:
      delayed.remove(entry);entry[1].continue_();font_events.append({'event':'released','kind':kind,'url':entry[1].request.url,'family':font_family(entry[1].request.url)})
    def pending_fonts():return [{'kind':kind,'url':route.request.url,'family':font_family(route.request.url)} for kind,route in delayed]
    def font_finished(request):
     if not any(host in request.url for host in ['fonts.googleapis.com','fonts.gstatic.com']):return
     try:
      response=request.response();body=response.body()
      if 'fonts.googleapis.com' in request.url and response.status==200:
       observed=css_font_families(body.decode('utf-8'),response.url);font_family_map.update(observed)
       font_events.append({'event':'actual-css-family-map','url':request.url,'entries':observed})
      font_events.append({'event':'finished','url':request.url,'status':response.status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'headers':response.all_headers()})
     except Exception as error:font_events.append({'event':'readback-error','url':request.url,'error':str(error)})
    context.on('requestfinished',font_finished)
    context.on('requestfailed',lambda request:font_events.append({'event':'failed','url':request.url,'failure':request.failure}) if any(host in request.url for host in ['fonts.googleapis.com','fonts.gstatic.com']) else None)
    page=context.new_page();page.set_default_timeout(15000);page_errors=[];page.on('pageerror',lambda error:page_errors.append(str(error)))
    if args.engine=='chromium' and font_policy=='warm-cache':
     try:
      cdp=context.new_cdp_session(page);cdp.send('Network.enable')
      cdp.on('Network.requestServedFromCache',lambda data:cache_events.append({'event':'requestServedFromCache',**data}))
      cdp.on('Network.responseReceived',lambda data:cache_events.append({'event':'responseReceived','requestId':data.get('requestId'),'url':data.get('response',{}).get('url'),'fromDiskCache':data.get('response',{}).get('fromDiskCache'),'fromServiceWorker':data.get('response',{}).get('fromServiceWorker')}) if any(host in data.get('response',{}).get('url','') for host in ['fonts.googleapis.com','fonts.gstatic.com']) else None)
     except Exception as error:cache_events.append({'event':'cache-attribution-unavailable','error':str(error)})
    fonts={'policy':font_policy,'events':font_events,'cacheEvents':cache_events,'release':release_fonts,'pending':pending_fonts,'familyMap':font_family_map}
    row={'case':name,'variant':variant,'status':'ATTEMPTED','source':metadata['identity'],'url':server.origin+'/index.html'+metadata['plan']['hash']}
    try:
     page.goto(row['url'],wait_until='domcontentloaded')
     states,checks,status,limits=native_case(page,suite,name,variant,metadata,target,{'server':server,'fonts':fonts})
     row.update(status=status,checks=checks,states=states,limits=limits)
    except Exception as error:
     row.update(status='PLATFORM_GATE_BLOCKED' if isinstance(error,NativeHostUnsupported) else 'FAIL',error=str(error))
     try:row['failedState']=page.evaluate(READ);page.screenshot(path=str(target/'failure.png'))
     except Exception as capture_error:row['captureError']=str(capture_error)
    finally:
     for kind,route in delayed:
      try:route.fulfill(status=503,body='Declared delayed font settled at fixture cleanup')
      except Exception:pass
     row['pageErrors']=page_errors;row['fontPolicy']=font_policy;row['fontTransports']=font_events;row['fontRoutingDisablesCache']=font_policy not in {'loaded','warm-cache'};row['fontFamilyMap']=font_family_map;row['cacheAttribution']=cache_events;row['serverReceipts']=server.receipts
     write(target/'result.json',row);rows.append(row);context.close();server.close()
  finally:browser.close()
 manifest['results']=[{'case':r['case'],'variant':r['variant'],'status':r['status']} for r in rows];manifest['execution']='EXECUTED_WITH_LIMITS';write(out/'manifest.json',manifest)
 print(json.dumps({'manifest':str(out/'manifest.json'),'results':manifest['results']}))
 if any(r['status'] in {'FAIL','PLATFORM_GATE_BLOCKED'} for r in rows):raise SystemExit(1)

if __name__=='__main__':raise SystemExit('Use the three explicit suite entry points.')
