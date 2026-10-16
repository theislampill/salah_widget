"""Bounded transport discriminator only; no product or callback-cost verdict."""
from pathlib import Path
import asyncio,datetime,hashlib,http.server,json,sys,threading,time,traceback
C=Path(__file__).resolve().parent;O=C.parent
sys.path.insert(0,str(C))
from run_cost_v2 import NODE,BROWSERS,ROOTS,sha,save,bounded,owned_processes,merge_owned,reap_owned
R=ROOTS['B']

def pins():
 manifest=json.loads((R/'moon/asset-manifest.json').read_text())
 paths=[Path(__file__),C/'run_cost_v2.py',R/'moon/src/moon-worker.mjs',R/'moon/asset-manifest.json',O/'capture-driver/cli.js',O/'capture-driver/lib/coreBundle.js',NODE,BROWSERS['chromium']]
 paths += [R/'moon'/v['path'] for v in manifest['assets'].values()]
 return {str(p):sha(p) for p in paths}

async def acquire(out,result):
 import playwright._impl._transport as transport
 transport.compute_driver_executable=lambda:(str(NODE),str(O/'capture-driver/cli.js'))
 from playwright.async_api import async_playwright
 manifest=json.loads((R/'moon/asset-manifest.json').read_text())
 specs=[manifest['assets'][key] for key in ['dem','colour']]
 # Copy the exact unchanged native stream consumer; no substitute read loop.
 source=(R/'moon/src/moon-worker.mjs').read_text()
 reader=source[source.index('async function read('):source.index('\nfunction unbase64(')]
 worker=reader+"\nself.onmessage=async e=>{try{const rows=await Promise.all(e.data.map(async s=>{const b=await read(s.url,s.bytes);const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),x=>x.toString(16).padStart(2,'0')).join('');if(h!==s.sha256)throw Error('digest mismatch');return {url:s.url,bytes:b.length,sha256:h};}));self.postMessage({status:'READ_AND_DIGEST_OK',rows});}catch(e){self.postMessage({status:'ERROR',error:String(e.stack||e)});}};"
 result['readerSha256']=hashlib.sha256(reader.encode()).hexdigest()
 assets={'/moon/'+s['path']:(R/'moon'/s['path']).read_bytes() for s in specs}
 for s in specs:assert len(assets['/moon/'+s['path']])==s['bytes'] and hashlib.sha256(assets['/moon/'+s['path']]).hexdigest()==s['sha256']
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   row={'path':self.path,'at':time.monotonic()};result['server'].append(row)
   try:
    if self.path=='/':data=b'<!doctype html><title>Isolated transport control</title>';kind='text/html'
    elif self.path=='/favicon.ico':data=b'';kind='image/x-icon'
    else:data=assets[self.path];kind='application/gzip'
    row['sha256']=hashlib.sha256(data).hexdigest();row['bytes']=len(data)
    self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):row['clientDisconnected']=True
   except Exception as e:row['error']=str(e);self.send_error(500)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}'
 pw=None;browser=None;owned=[]
 try:
  pw=await bounded(async_playwright().start(),20)
  browser=await bounded(pw.chromium.launch(headless=True,executable_path=str(BROWSERS['chromium']),args=['--disable-dev-shm-usage'],chromium_sandbox=True),40)
  result['browser']=browser.version;owned=merge_owned(owned,owned_processes())
  for intercept in [True,False,False,True]:
   row={'index':len(result['slots']),'interceptLocal':intercept,'requests':[]};result['slots'].append(row);ctx=None
   try:
    ctx=await bounded(browser.new_context(viewport={'width':390,'height':600}),10)
    by_request={}
    def started(q):
     item={'url':q.url,'type':q.resource_type,'at':time.monotonic()};row['requests'].append(item);by_request[q]=item
    def finished(q,failed=False):
     by_request[q].update(endedAt=time.monotonic(),failed=failed,failure=q.failure if failed else None)
    ctx.on('request',started);ctx.on('requestfinished',finished);ctx.on('requestfailed',lambda q:finished(q,True))
    async def route(r):
     assert r.request.url.startswith(origin+'/'),'Unexpected external request'
     await r.continue_()
    if intercept:await bounded(ctx.route('**/*',route))
    page=await bounded(ctx.new_page(),10);await bounded(page.goto(origin,wait_until='load',timeout=10000),12)
    row['consumer']=await bounded(page.evaluate("""({worker,specs})=>new Promise((resolve,reject)=>{const url=URL.createObjectURL(new Blob([worker],{type:'text/javascript'})),w=new Worker(url);window.__transportWorker=w;const done=v=>{URL.revokeObjectURL(url);resolve(v);};w.onmessage=e=>done(e.data);w.onerror=e=>done({status:'ERROR',error:e.message});w.postMessage(specs);})""",{'worker':worker,'specs':[{**s,'url':origin+'/moon/'+s['path']} for s in specs]}),20)
    await asyncio.sleep(.25)
    row.update(status='OBSERVED',observationEndedAt=time.monotonic())
   except Exception:row.update(status='FAILED',error=traceback.format_exc())
   finally:
    owned=merge_owned(owned,owned_processes())
    if ctx:
     try:row['contextCloseStartedAt']=time.monotonic();await bounded(ctx.close(),10);row['contextClosed']=True
     except Exception as e:row.update(contextClosed=False,closeError=str(e))
    save(out/'RESULTS.json',result)
   if row['status']!='OBSERVED':break
 finally:
  owned=merge_owned(owned,owned_processes());result['ownedProcesses']=owned
  if browser:
   try:await bounded(browser.close(),15);result['browserClosed']=True
   except Exception as e:result['browserCloseError']=str(e)
  if pw:
   try:await bounded(pw.stop(),10);result['playwrightStopped']=True
   except Exception as e:result['playwrightStopError']=str(e)
  result['ownedCleanup']=reap_owned(owned);server.shutdown();server.server_close()

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--admission',type=Path,required=True);a=p.parse_args()
 actual=pins();admission=json.loads(a.admission.read_text());assert admission['status']=='ADMITTED_BOUNDED_TRANSPORT_CONTROL' and admission['pins']==actual
 out=C/'transport-control-r1';assert not out.exists();out.mkdir()
 result={'schema':'r0021-transport-control/v1','status':'ACQUIRING','createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pins':actual,'admissionSha256':sha(a.admission),'slots':[],'server':[],'scope':'Exact lunar read consumer and pinned compressed bytes only; route-continuation vs direct local transport. No product rendering, cost gate or S1 claim.'}
 lock=O/'native-resource.lock'
 with lock.open('x') as f:f.write('transport-control-r1')
 try:asyncio.run(acquire(out,result))
 except BaseException:result['error']=traceback.format_exc()
 finally:
  result['pinsUnchanged']=actual==pins();result['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  result['status']='OBSERVATIONS_ONLY' if len(result['slots'])==4 and all(s.get('status')=='OBSERVED' and s.get('contextClosed') for s in result['slots']) and result.get('browserClosed') and result.get('playwrightStopped') and result.get('ownedCleanup',{}).get('verified') and result['pinsUnchanged'] else 'INCOMPLETE'
  if result.get('ownedCleanup',{}).get('verified'):
   assert lock.read_text()=='transport-control-r1';lock.unlink();result['lockReleased']=True
  save(out/'RESULTS.json',result)
 print(json.dumps({'status':result['status'],'path':str(out)}))
if __name__=='__main__':main()
