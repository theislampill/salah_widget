"""R0017: drive the unchanged delivered smoke page in one disposable native context.

This is an evidence driver, not a replacement instrument. Product and smoke bytes
are served directly from the bound snapshot. No result/ready state is assigned.
"""
import argparse, hashlib, http.server, json, os, re, sys, threading, time, traceback, subprocess
from pathlib import Path
from urllib.parse import urlsplit, unquote

BASE=Path(__file__).resolve().parent
ROOT=Path(r'C:/Users/theis/.codex/worktrees/r0017-moon-readiness/salah_widget')
PACKAGES=Path('C:/Users/theis/Documents/Codex/r0007-close-20261014/venv/Lib/site-packages')
sys.path.insert(0,str(PACKAGES))
sys.path.insert(0,str(ROOT/'tools/cp9'))
from playwright.sync_api import sync_playwright
from browser_runtime import browser_options, browser_identity
from runtime_identity import runtime_identity

def sha(data):return hashlib.sha256(data).hexdigest()
def dump(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def identity():
    rt=runtime_identity(ROOT)
    return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'baseCommit':'763a460e98dc23c7f0e95bf346274f1685b3c654','runtime':rt,
            'files':{p:sha((ROOT/p).read_bytes()) for p in ['README.md','tests/smoke.html','tests/widget-fixture.html','tests/r0017-contract.cjs','tests/r0017-transport.cjs','src/native/config.js','src/native/index.html']}}

class Server:
    def __init__(self,overrides=None):
        self.requests=[];self.overrides=overrides if overrides is not None else {}
        owner=self
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
            def log_message(self,*a):pass
            def do_GET(self):
                p=(ROOT/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
                if not p.is_relative_to(ROOT):self.send_error(403);return
                owner.requests.append({'url':self.path,'monotonic':time.monotonic()})
                relative=p.relative_to(ROOT).as_posix()
                if relative in owner.overrides:
                    data=owner.overrides[relative]
                    self.send_response(200);self.send_header('Content-Type',self.guess_type(str(p)))
                    self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
                try:super().do_GET()
                except (ConnectionResetError,BrokenPipeError,ConnectionAbortedError) as e:
                    owner.requests.append({'url':self.path,'event':'client-disconnected','error':str(e),'monotonic':time.monotonic()})
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.origin=f'http://127.0.0.1:{self.server.server_port}'
    def close(self):self.server.shutdown();self.server.server_close()

OUTER=r'''(seed)=>{
  if(window!==window.top)return;
  const storage=window.localStorage;
  for(const [key,value] of Object.entries(seed)){if(value!==null)storage.setItem(key,value);}
  const keys=Object.keys(seed),snapshot=()=>Object.fromEntries(keys.map(k=>[k,storage.getItem(k)]));
  const proof=window.__r0017Outer={before:snapshot(),getterAccesses:0,snapshot};
  Object.defineProperty(window,'localStorage',{configurable:true,get(){proof.getterAccesses++;return storage;}});
}'''

def seeds(kind):
    cfg={'valid':'{"v":1,"lat":12,"lon":34,"label":"fixture-user-setting","method":"4","savedAt":42}',
         'malformed':'  { not-json: "preserve\\u0000 literal"\n','absent':None}[kind]
    return {'salah_widget:config:v1':cfg,'__sw_probe__':'R0017 untouched probe \u03a9\nraw',
            'unrelated-origin-key':'retained exactly \u2603\n{"spaces":  2}'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',choices=['chromium','firefox'],required=True)
    p.add_argument('--mode',choices=['healthy','reject','hang','bootstrap-error'],default='healthy')
    p.add_argument('--preference',choices=['reduce','no-preference'],default='no-preference')
    p.add_argument('--storage',choices=['valid','malformed','absent'],default='valid')
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--public',action='store_true')
    a=p.parse_args();assert a.public and a.mode=='healthy';out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    declared=json.loads(re.search(r'const CASES=(\[[\s\S]*?\n\]);',(ROOT/'tests/smoke.html').read_text(encoding='utf-8')).group(1))
    assert len(declared)==30 and sum(x[1] for x in declared)==141
    row={'schema':'r0017-native-proof/v1','status':'ATTEMPT_STARTED','mode':a.mode,'preference':a.preference,'storage':a.storage,
         'source':identity(),'denominator':declared,'driverSha256':sha(Path(__file__).read_bytes()),'startedUtc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         'console':[],'pageErrors':[],'requests':[],'responses':[],'requestFailures':[],'resourceTimings':[],'workerLifecycle':[],'checks':{},'delivery':json.loads((BASE/'merge.json').read_text()),'scope':'Actual deployed Pages runtime; unchanged original instrument; disposable context; fixture controlled provider/private storage; no local runtime substitution'}
    dump(out/'result.json',row);(out/'driver.py').write_bytes(Path(__file__).read_bytes())
    srv=Server();os.environ['SALAH_BROWSER']=a.engine
    origin='https://theislampill.github.io/salah_widget' if a.public else srv.origin
    try:
        with sync_playwright() as pw:
            family,options=browser_options();options['executable_path']=getattr(pw,family).executable_path
            browser=getattr(pw,family).launch(**options)
            exe=options.get('executable_path') or getattr(pw,family).executable_path
            row['browser']={**browser_identity(browser),'executable':exe,'executableSha256':sha(Path(exe).read_bytes()),'headless':options['headless']}
            context=browser.new_context(viewport={'width':1100,'height':900},device_scale_factor=1,timezone_id='Asia/Riyadh',reduced_motion=a.preference,service_workers='block')
            context.add_init_script('('+OUTER+')('+json.dumps(seeds(a.storage))+');')
            page=context.new_page()
            page.on('console',lambda m:row['console'].append({'type':m.type,'text':m.text}))
            page.on('pageerror',lambda e:row['pageErrors'].append(str(e)))
            page.on('request',lambda r:row['requests'].append({'url':r.url,'method':r.method,'type':r.resource_type}))
            page.on('response',lambda r:row['responses'].append({'url':r.url,'status':r.status}))
            page.on('requestfailed',lambda r:row['requestFailures'].append({'url':r.url,'failure':r.failure}))
            page.on('requestfinished',lambda r:row['resourceTimings'].append({'url':r.url,'timing':r.timing}))
            def observe_worker(worker):
                row['workerLifecycle'].append({'event':'created','url':worker.url,'monotonic':time.monotonic()})
                worker.on('close',lambda closed:row['workerLifecycle'].append({'event':'closed','url':worker.url,'monotonic':time.monotonic()}))
            page.on('worker',observe_worker)
            row['url']=origin+'/tests/smoke.html?fixture='+a.mode
            started=time.monotonic();page.goto(row['url'],wait_until='domcontentloaded',timeout=30000)
            page.wait_for_function('()=>!!window.__smoke',timeout=120000)
            row['elapsedSeconds']=time.monotonic()-started
            row['smoke']=page.evaluate('()=>window.__smoke')
            row['summary']=page.locator('#sum').inner_text()
            row['assertionLog']=page.locator('#out').inner_text()
            row['outerStorage']=page.evaluate('()=>({before:__r0017Outer.before,after:__r0017Outer.snapshot(),getterAccesses:__r0017Outer.getterAccesses})')
            row['nativeReduced']=page.evaluate('()=>matchMedia("(prefers-reduced-motion: reduce)").matches')
            page.screenshot(path=str(out/'summary.png'),full_page=True)
            s=row['smoke'];c=row['checks'];req=s['required']
            c['exactNamesAndMinima']=[[x['name'],x['expected']] for x in req['cases']]==declared
            c['outerBytesPreserved']=row['outerStorage']['before']==row['outerStorage']['after']==seeds(a.storage)
            c['zeroOuterStorageAccess']=row['outerStorage']['getterAccesses']==0
            c['nativePreference']=row['nativeReduced']==(a.preference=='reduce')
            if a.mode=='healthy':
                c['fullHealthy']=s['status']=='PASS' and req['executed']==30 and s['pass']==141 and s['fail']==s['skip']==0 and not req['missing'] and all(x['state']=='executed' and x['assertions']==x['expected'] for x in req['cases'])
                c['sourceIdentity']=all(t.get('fixture',{}).get('sourceSha256')==row['source']['runtime']['files']['index.html']['sha256'] for t in s['fixture']['attempts'])
            else:c['expectedNonPass']=s['status']=='FAIL' if a.mode=='bootstrap-error' else s['status']=='INCOMPLETE'
            row['status']='PASS' if all(c.values()) else 'FAIL'
            context.close();browser.close()
    except Exception as e:
        row['status']='ATTEMPT_ERROR';row['exception']=traceback.format_exc()
        try:
            row['partial']=page.evaluate('()=>({summary:document.querySelector("#sum")?.textContent,smoke:window.__smoke,fixture:document.querySelector("#w")?.contentWindow?.__widgetFixture})')
            page.screenshot(path=str(out/'error.png'),full_page=True)
        except Exception:pass
    finally:
        row['serverRequests']=srv.requests;srv.close();row['finishedUtc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());dump(out/'result.json',row)
    print(json.dumps({'out':str(out),'status':row['status'],'summary':row.get('summary'),'checks':row['checks'],'error':row.get('exception')},ensure_ascii=False),flush=True)
    return 0 if row['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
