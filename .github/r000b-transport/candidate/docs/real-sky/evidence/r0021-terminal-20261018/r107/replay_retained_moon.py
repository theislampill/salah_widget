"""One retained-scene production-worker replay; no source or quality substitution."""
from pathlib import Path
import argparse, functools, hashlib, http.server, json, threading, time
from playwright.sync_api import sync_playwright

p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--scene-record',type=Path,required=True)
p.add_argument('--firefox',required=True)
a=p.parse_args()
assert not a.out.exists()
a.out.mkdir(parents=True)
o=Path(__file__).resolve().parent
lock=o/'native-resource.lock'
with lock.open('x') as f:f.write(a.out.name)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/probe':
   body=b'<!doctype html><title>Retained numerical Moon scene</title>'
   self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  else:super().do_GET()
record={'scope':'Exact retained accepted-preview numerical scene; original rejected job identity not recorded, so not an exact original-job replay. No widget/native timing or visual qualification.',
        'errors':[],
        'deadlineMs':240000,'qualityGate':'unchanged production worker; empirical-adaptive required; no retry'}
server=None
def verify_runtime():
 inv=json.loads((a.root/'RUNTIME.json').read_bytes())
 for rel,x in inv['files'].items():
  b=(a.root/rel).read_bytes()
  assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],rel
 assert hashlib.sha256(''.join(f"{x['sha256']}  {rel}\n" for rel,x in sorted(inv['files'].items())).encode()).hexdigest()==inv['treeSha256']
 return inv['treeSha256']
try:
 scene=json.loads(a.scene_record.read_bytes())['observed']['acceptedPreviewScene']
 record.update(scene=scene,sceneRecordSha256=hashlib.sha256(a.scene_record.read_bytes()).hexdigest(),runtime=verify_runtime(),harnessSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(a.root)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}'
 with sync_playwright() as pw:
  browser=pw.firefox.launch(headless=True,executable_path=a.firefox,timeout=30000)
  record['browser']={'family':'firefox','version':browser.version}
  context=browser.new_context(viewport={'width':390,'height':640},device_scale_factor=2)
  page=context.new_page();page.on('pageerror',lambda e:record['errors'].append(str(e)))
  page.goto(origin+'/probe')
  page.evaluate('''scene=>{window.__replayResult=null;(async()=>{
   const source=await(await fetch('/moon/moon-worker.js',{signal:AbortSignal.timeout(10000)})).text(),base=new URL('/moon/',location.href).href;
   const worker=new Worker('/moon/moon-worker.js'),rows=[],started=performance.now();
   window.__replayResult=await new Promise(resolve=>{
    let done=false;
    const finish=(status,message)=>{if(done)return;done=true;clearTimeout(timer);worker.terminate();resolve({status,message,rows,elapsedMs:performance.now()-started});};
    const timer=setTimeout(()=>finish('deadline',null),240000);
    worker.onerror=e=>finish('worker-error',String(e.message));
    worker.onmessage=e=>{
     const m=e.data;
     if(m.kind==='progress') {if(m.stage==='refinement')rows.push({...m,at:performance.now()-started});return;}
     if(m.kind==='ready'){rows.push({kind:'ready',at:performance.now()-started});worker.postMessage({kind:'render',id:1,identity:{id:1,key:'retained-r3-preview-scene',epoch:1},scene});return;}
     const {rgba,surfaceLinear,surfaceCoverage,calendarLinear,calendarRgba,...metadata}=m;
     rows.push({...metadata,at:performance.now()-started});
     if(m.kind==='result'||m.kind==='error'||m.kind==='boot-error')finish(m.kind,metadata);
    };
    worker.postMessage({kind:'boot',base,offline:false,workerSource:source});
   });
  })().catch(e=>window.__replayResult={status:'setup-error',error:String(e)});
  }''',scene)
  page.wait_for_function('window.__replayResult!==null',timeout=255000)
  record['result']=page.evaluate('window.__replayResult')
  message=record['result'].get('message') or {}
  record['qualityAdmissible']=message.get('diagnostics',{}).get('quality',{}).get('status')=='empirical-adaptive'
  record['requestReplyIdentityMatches']=message.get('identity')=={'id':1,'key':'retained-r3-preview-scene','epoch':1} and message.get('scene')==scene
  record['nativeHostAdmission']='NOT_OBSERVED; numerical worker replay only'
  context.close();browser.close()
except Exception as e:
 record['errors'].append(repr(e));raise
finally:
 if server is not None:server.shutdown();server.server_close()
 try:record['runtimeAfter']=verify_runtime()
 except Exception as e:record['errors'].append('post-runtime: '+repr(e))
 record['finishedAtUnix']=time.time()
 (a.out/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
 assert lock.read_text()==a.out.name;lock.unlink()
print(json.dumps({'status':record.get('result',{}).get('status'),'quality':(record.get('result',{}).get('message') or {}).get('diagnostics',{}).get('quality'),'identity':record.get('requestReplyIdentityMatches'),'qualityAdmissible':record.get('qualityAdmissible'),'errors':record['errors']}))
