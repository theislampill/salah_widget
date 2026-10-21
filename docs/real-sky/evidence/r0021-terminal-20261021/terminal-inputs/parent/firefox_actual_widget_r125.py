"""Bounded native Marionette actual-parent integration control; disposable owned profile only.

Protocol and command shapes are from Mozilla's reference client, not Juggler.
No packages, drivers, personal profiles, desktop capture or browser preferences
outside this profile are installed or changed. This tests actual-parent attachment and geometry; it does not certify cold S1 timing or continuous pixels.
"""
from pathlib import Path
import base64, datetime, hashlib, json, os, socket, subprocess, time, sys
import psutil
import http.server,threading,functools
from PIL import Image

O=Path(__file__).resolve().parent
OUT=O/'firefox-actual-widget-r125'
BUILD=O.parent/'builds/integrated-r30-owner-callbacks'
EXE=Path(r'${BROWSER_CACHE}\firefox-1522\firefox\firefox.exe')
XPI=O/'tabliss-firefox.xpi'
sys.path.insert(0,str(O))
from parent_fixture_r125 import handler_class,runtime_identity

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Client:
 def __init__(self,sock):self.sock=sock;self.serial=0;self.hello=self.read()
 def read(self):
  prefix=b''
  while True:
   c=self.sock.recv(1)
   if not c:raise EOFError('Marionette closed')
   if c==b':':break
   prefix+=c
   if len(prefix)>10:raise ValueError('Invalid prefix')
  n=int(prefix);assert 0<n<20000000
  out=b''
  while len(out)<n:
   v=self.sock.recv(min(n-len(out),65536))
   if not v:raise EOFError('Truncated response')
   out+=v
  return json.loads(out)
 def call(self,name,params=None):
  self.serial+=1;payload=json.dumps([0,self.serial,name,params or {}]).encode()
  start=time.monotonic();self.sock.sendall(str(len(payload)).encode()+b':'+payload)
  reply=self.read();assert reply[:2]==[1,self.serial],reply[:2]
  log.append({'command':name,'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsedMs':(time.monotonic()-start)*1000,'error':reply[2]})
  if reply[2]:raise RuntimeError(json.dumps(reply[2]))
  return reply[3]
 def script(self,js):return self.call('WebDriver:ExecuteScript',{'script':js,'args':[],'newSandbox':True,'sandbox':'default','line':1,'filename':'r0021-parent-capability'})['value']

def main():
 assert sha(XPI)=='2f16feb3a32e6b07b70d224fa21d975ad280394499fd3ca4d16fbb72d0741622'
 OUT.mkdir();profile=OUT/'isolated-profile';profile.mkdir()
 lock=O.parent/'native-resource.lock'
 with lock.open('x') as f:f.write(OUT.name)
 report={'schema':'r0021-native-marionette-capability/1','purpose':__doc__,'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executable':str(EXE),'executableSha256':sha(EXE),'extensionSha256':sha(XPI),'driverSha256':sha(Path(__file__)),'references':['https://firefox-source-docs.mozilla.org/remote/marionette/Protocol.html','https://raw.githubusercontent.com/mozilla-firefox/firefox/main/testing/marionette/client/marionette_driver/marionette.py','https://raw.githubusercontent.com/mozilla-firefox/firefox/main/testing/marionette/client/marionette_driver/addons.py'],'commands':log}
 proc=client=server=None;owned={}
 def remember():
  if proc is None:return
  try:processes=[psutil.Process(proc.pid),*psutil.Process(proc.pid).children(recursive=True)]
  except psutil.Error:return
  for p in processes:
   try:owned[p.pid]={'pid':p.pid,'created':p.create_time(),'exe':p.exe()}
   except psutil.Error:pass
 try:
  report['runtime']=runtime_identity(BUILD)
  assert report['runtime']['treeSha256']=='3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821'
  report['fixtureHelperSha256']=sha(O/'parent_fixture_r125.py')
  report['fixtureNotice']='Accepted fixed civil calendar, provider transport and real1x clock fixture; actual installed parent and native settings. Not live weather or owner location.'
  handler=functools.partial(handler_class(http.server.SimpleHTTPRequestHandler,BUILD,report),directory=str(BUILD.parent))
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
  threading.Thread(target=server.serve_forever,daemon=True).start()
  origin='http://127.0.0.1:'+str(server.server_port)
  report['buildIndexSha256']=sha(BUILD/'index.html')
  with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
  prefs={'marionette.port':port,'browser.newtabpage.enabled':True,'browser.shell.checkDefaultBrowser':False,'browser.startup.page':0,'browser.startup.homepage':'about:blank'}
  (profile/'user.js').write_text(''.join('user_pref('+json.dumps(k)+','+json.dumps(v)+');\n' for k,v in prefs.items()))
  report['profilePreferences']=prefs
  command=[str(EXE),'-headless','-no-remote','-marionette','--remote-allow-system-access','-profile',str(profile),'about:blank']
  report['command']=command
  with (OUT/'browser.log').open('wb') as output:
   proc=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   deadline=time.monotonic()+20
   while True:
    remember()
    try:sock=socket.create_connection(('127.0.0.1',port),timeout=1);sock.settimeout(20);break
    except (ConnectionRefusedError,socket.timeout):
     if proc.poll() is not None or time.monotonic()>deadline:raise TimeoutError('Native Marionette did not listen within20s')
     time.sleep(.1)
   client=Client(sock);report['hello']=client.hello
   report['session']=client.call('WebDriver:NewSession',{'capabilities':{'alwaysMatch':{'acceptInsecureCerts':False,'pageLoadStrategy':'normal','timeouts':{'pageLoad':15000,'script':10000,'implicit':0}}}})
   report['addon']=client.call('Addon:Install',{'path':str(XPI),'temporary':False})
   remember()
   old_handles=client.call('WebDriver:GetWindowHandles')
   client.call('Marionette:SetContext',{'value':'chrome'})
   report['chromeBefore']=client.script("return {newTabURL:BROWSER_NEW_TAB_URL,pref:Services.prefs.getBoolPref('browser.newtabpage.enabled'),tabs:gBrowser.tabs.length};")
   client.script("Services.prefs.setBoolPref('browser.newtabpage.enabled',true);BrowserCommands.openTab();return true;")
   report['chromeAfter']=client.script("return {newTabURL:BROWSER_NEW_TAB_URL,pref:Services.prefs.getBoolPref('browser.newtabpage.enabled'),tabs:gBrowser.tabs.length,selected:gBrowser.selectedBrowser.currentURI.spec};")
   client.call('Marionette:SetContext',{'value':'content'})
   new_handles=client.call('WebDriver:GetWindowHandles')
   report['handles']={'before':old_handles,'after':new_handles}
   created=[x for x in new_handles if x not in old_handles];assert len(created)==1
   client.call('WebDriver:SwitchToWindow',{'handle':created[0],'focus':True})
   deadline=time.monotonic()+12
   while True:
    state=client.script("return {url:location.href,ready:document.readyState,text:document.body?.innerText.slice(0,200),customise:!!document.querySelector('[title=\"Customise Tabliss (S)\"]')};")
    if state['customise']:break
    if time.monotonic()>deadline:report['readinessTimeout']=state;break
    time.sleep(.2)
   client.call('WebDriver:SetWindowRect',{'width':1100,'height':1000,'x':0,'y':0})
   def element(css):
    value=client.call('WebDriver:FindElement',{'using':'css selector','value':css})['value']
    return value['element-6066-11e4-a52e-4f735466cecf']
   def click(css):client.call('WebDriver:ElementClick',{'id':element(css)})
   def shot(name):
    assert not (OUT/(name+'.png')).exists(),'Refuse screenshot overwrite'
    value=client.call('WebDriver:TakeScreenshot',{'id':None,'highlights':[],'full':False,'scroll':False})
    (OUT/(name+'.png')).write_bytes(base64.b64decode(value['value']))
   preset_path=BUILD/'presets/salah-widget.tablissng.json'
   preset=json.loads(preset_path.read_text(encoding='utf-8'))
   public='https://theislampill.github.io/salah_widget/#local=1'
   url=origin+'/'+BUILD.name+'/#local=1&lat=28.5383&lon=-81.3792&tz=America/New_York&method=2&units=f&label=CENTRAL%20FL&motion=full'
   html=preset['data/orpul7IDXSSP']['input'];assert html.count(public)==1
   preset['data/orpul7IDXSSP']['input']=html.replace(public,url)
   imported=OUT/'parent-import.json';imported.write_text(json.dumps(preset,indent=2)+'\n',encoding='utf-8')
   report['parentImport']={'sourceSha256':sha(preset_path),'importSha256':sha(imported),'changedField':'Widget URL only; exact parent wrapper preserved. Actual local-mode resolver consumes disclosed Orlando provider fixture; no direct target assignment. Warm parent integration, no S1 claim.'}
   click('[title="Customise Tabliss (S)"]')
   link=client.call('WebDriver:FindElement',{'using':'link text','value':'Import'})['value']['element-6066-11e4-a52e-4f735466cecf']
   client.call('WebDriver:ElementClick',{'id':link})
   report['fileInputs']=client.script("return [...document.querySelectorAll('input[type=file]')].map(e=>({id:e.id,outer:e.outerHTML}));")
   file_id=element('input[type=file]')
   client.call('WebDriver:ElementSendKeys',{'id':file_id,'text':str(imported)})
   deadline=time.monotonic()+15
   while True:
    frames=client.script("return [...document.querySelectorAll('iframe')].map(f=>({src:f.src,width:f.getBoundingClientRect().width,height:f.getBoundingClientRect().height}));")
    if any(f['src']==url for f in frames):break
    if time.monotonic()>deadline:raise TimeoutError('Imported native parent did not attach widget')
    time.sleep(.1)
   report['framesAfterImport']=frames;shot('imported-widget')
   # Acquired TablissNG main.js batches native storage writes for1000ms.
   time.sleep(2)

   old_handles=client.call('WebDriver:GetWindowHandles')
   client.call('Marionette:SetContext',{'value':'chrome'});client.script('BrowserCommands.openTab();return true;');client.call('Marionette:SetContext',{'value':'content'})
   new_handles=client.call('WebDriver:GetWindowHandles');created=[x for x in new_handles if x not in old_handles];assert len(created)==1
   client.call('WebDriver:SwitchToWindow',{'handle':created[0],'focus':True})
   time.sleep(1);shot('new-tab-first-second');time.sleep(15);shot('new-tab-settled')
   report['parentUrl']=client.call('WebDriver:GetCurrentURL')
   report['framesNewTab']=client.script("return [...document.querySelectorAll('iframe')].map(f=>({src:f.src,width:f.getBoundingClientRect().width,height:f.getBoundingClientRect().height}));")
   def enter_widget():
    target=element('iframe[title="Prayer Times"]');client.call('WebDriver:SwitchToFrame',{'id':{'element-6066-11e4-a52e-4f735466cecf':target}})
   def widget_state():
    return client.script("""const w=window.wrappedJSObject,c=document.querySelector('.c'),r=c.getBoundingClientRect(),style=getComputedStyle(c);return JSON.parse(JSON.stringify({url:location.href,ready:document.readyState,card:{width:r.width,height:r.height},weatherHeader:{icon:document.querySelector('#wi')?.textContent,temperature:document.querySelector('#wt')?.textContent},mode:c.dataset.appearance,classes:c.className,background:style.background,opacity:style.opacity,backdropFilter:style.backdropFilter,storage:localStorage.getItem('salah_widget:config:v1'),mainWorldAvailable:!!w?.SalahMoonRuntime,native:w?.SalahNativeSkyHost?.capture(false),moon:w?.SalahMoonRuntime?.state,sky:w?.SalahRealSky?.state,qa:w?.qaState?.(),rows:[...document.querySelectorAll('.times .p')].map(e=>({text:e.innerText,opacity:getComputedStyle(e).opacity,background:getComputedStyle(e).background,rect:e.getBoundingClientRect().toJSON()})),text:c.innerText}));""")
   def parent_shot(name):
    client.call('WebDriver:SwitchToFrame',{'id':None});shot(name);enter_widget()
   def compositor_shot(name):
    # Installed Capture.sys.mjs exposes the existing framebuffer readback path.
    # This reads only the selected browser in this owned headless process.
    client.call('WebDriver:SwitchToFrame',{'id':None});client.call('Marionette:SetContext',{'value':'chrome'})
    try:
     expected=report['parentUrl']['value']
     script="const done=arguments[arguments.length-1];const b=gBrowser.selectedBrowser,w=b.ownerGlobal,r=b.getBoundingClientRect(),expected="+json.dumps(expected)+";if(!expected.startsWith('moz-extension://')||b.currentURI.spec!==expected){done({error:'Owned selected parent mismatch'});return;}const before={url:b.currentURI.spec,rect:{x:r.x,y:r.y,width:r.width,height:r.height},dpr:w.devicePixelRatio};const {capture}=ChromeUtils.importESModule('chrome://remote/content/shared/Capture.sys.mjs');capture.canvas(w,b.browsingContext,r.x,r.y,r.width,r.height,{readback:true}).then(c=>{const s=b.getBoundingClientRect();done({before,after:{url:b.currentURI.spec,rect:{x:s.x,y:s.y,width:s.width,height:s.height},dpr:w.devicePixelRatio},data:c.toDataURL('image/png')});},e=>done({error:String(e)}));"
     result=client.call('WebDriver:ExecuteAsyncScript',{'script':script,'args':[],'newSandbox':True,'sandbox':'default','scriptTimeout':10000,'line':1,'filename':'r0021-owned-compositor-readback'})['value']
     data=result.pop('data',None)
     if data:
      path=OUT/(name+'.png');assert not path.exists(),'Refuse compositor overwrite';path.write_bytes(base64.b64decode(data.split(',',1)[1]));result['sha256']=sha(path);result['size']=list(Image.open(path).size)
      result['geometryValid']=result['before']==result['after'] and result['size']==[round(result['before']['rect'][k]*result['before']['dpr'])for k in ['width','height']]
     report.setdefault('compositorReadbacks',[]).append({'name':name,**result})
    finally:
     client.call('Marionette:SetContext',{'value':'content'});enter_widget()
   enter_widget()
   def ready_state():
    return client.script("const w=window.wrappedJSObject,m=w.SalahMoonRuntime?.state,s=w.SalahRealSky?.state;return {moon:m?{current:m.current,pending:m.pending,visibleSource:m.visibleSource,status:m.status}:null,sky:s?{status:s.status,pending:s.lifecycle?.pending}:null,at:performance.now()};")
   def settle(label):
    deadline=time.monotonic()+360;observations=[]
    while True:
     value=ready_state();observations.append(value)
     if (value.get('moon') or {}).get('status')=='unavailable' or (value.get('sky') or {}).get('status')=='unavailable':raise RuntimeError('Actual parent product failure: '+json.dumps(value))
     if (value.get('moon') or {}).get('current')and value['moon'].get('visibleSource')=='refined-terrain'and not value['moon'].get('pending')and (value.get('sky') or {}).get('status')=='ready'and not value['sky'].get('pending'):break
     if time.monotonic()>deadline:report.setdefault('readiness',{})[label]=observations;raise TimeoutError('Current refined parent not ready within360s')
     time.sleep(1)
    report.setdefault('readiness',{})[label]=observations
   def endpoint(label,mode):
    state=widget_state();report.setdefault('endpoints',{})[label]=state
    client.call('WebDriver:SwitchToFrame',{'id':None})
    wrappers=client.script("return [...document.querySelectorAll('iframe')].map(f=>({src:f.src,title:f.title,width:f.getBoundingClientRect().width,height:f.getBoundingClientRect().height,style:f.getAttribute('style')}));")
    enter_widget();matches=[f for f in wrappers if f['src']==url and f['title']=='Prayer Times'];state['parentWrappers']=wrappers
    assert len(matches)==1 and matches[0]['width']==325 and matches[0]['height']==530,'Actual preset iframe geometry/source changed'
    assert state['weatherHeader']['temperature'] and state['weatherHeader']['icon'] not in ['', '—'],'Weather must be admitted before mode observations'
    assert state['native']['weather']['cloud']==35,'Expected actual accepted cloud fixture'
    assert state['mode']==mode and len(state['rows'])==6 and state['card']=={'width':325,'height':530}
    assert state['moon']['current']and state['moon']['visibleSource']=='refined-terrain'and not state['moon']['pending']and state['sky']['status']=='ready'
    q=state['moon']['last']['quality'];assert q['status']=='empirical-adaptive' and q['projectedGate']==.5 and q['projectedMaximumCode']<=.5 and q['unsettled']==0
    compositor_shot(label)
    assert report['compositorReadbacks'][-1].get('geometryValid')
   def change_mode(mode):
    click('.buckle');click('#set-appearance option[value="'+mode+'"]');click('#setClose')
   settle('initial-parent');endpoint('refined-glass-default','glass')
   original=report['endpoints']['refined-glass-default']['native']
   for mode in ['contrast','glass']:
    change_mode(mode);time.sleep(.3);endpoint('refined-'+mode+'-return',mode)
    current=report['endpoints']['refined-'+mode+'-return']['native']
    assert all(current[k]==original[k]for k in ['lat','lon','tz','generation','weather']),'Appearance changed native target/weather/generation'
   client.call('WebDriver:SwitchToFrame',{'id':None});client.call('WebDriver:Refresh')
   deadline=time.monotonic()+15
   while True:
    frames=client.script("return [...document.querySelectorAll('iframe')].map(f=>({src:f.src,title:f.title}));")
    if any(f['src']==url and f['title']=='Prayer Times' for f in frames):
     enter_widget()
     if client.script("return !!document.querySelector('.c');"):break
     client.call('WebDriver:SwitchToFrame',{'id':None})
    if time.monotonic()>deadline:raise TimeoutError('Exact parent reload iframe/card did not attach within15s')
    time.sleep(.1)
   settle('reload');endpoint('refined-glass-reload','glass')
   report['scope']='Actual installed TablissNG parent; valid calendar/provider fixture; admitted weather before actual glass/contrast/reload controls. Current refined endpoints and whole-parent compositor captures; no continuous motion or S1 claim.'
   client.call('WebDriver:SwitchToFrame',{'id':None});report['url']=client.call('WebDriver:GetCurrentURL')
   report['screenshots']=[{'file':p.name,'sha256':sha(p)}for p in sorted(OUT.glob('*.png'))]
   report['buildIndexUnchanged']=sha(BUILD/'index.html')==report['buildIndexSha256']
   report['runtimeUnchanged']=runtime_identity(BUILD)==report['runtime']
   assert report['runtimeUnchanged']
   report['status']='RETURNED'
 except Exception as e:report.update(status='FAILED',error=repr(e))
 finally:
  if server:server.shutdown();server.server_close()
  remember()
  if client:
   try:client.call('WebDriver:DeleteSession')
   except Exception as e:report['deleteSessionError']=repr(e)
   client.sock.close()
  if proc and proc.poll() is None:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
  for row in owned.values():
   try:
    p=psutil.Process(row['pid'])
    if p.create_time()==row['created'] and p.exe()==row['exe']:p.terminate()
   except psutil.Error:pass
  remaining=[]
  for row in owned.values():
   try:
    p=psutil.Process(row['pid'])
    if p.create_time()==row['created']:p.wait(timeout=5)
   except psutil.NoSuchProcess:pass
   except psutil.TimeoutExpired:remaining.append(row)
  report.update(ownedProcesses=list(owned.values()),remainingOwnedProcesses=remaining,closedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  (OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
  if not remaining:
   assert lock.read_text()==OUT.name;lock.unlink()
 print(json.dumps({k:v for k,v in report.items() if k in ['status','error','url','addon','remainingOwnedProcesses']}))
log=[]
if __name__=='__main__':main()
