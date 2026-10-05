#!/usr/bin/env python3
"""Serve exact candidate/baseline bytes; controlled external prayer responses and wall time only."""
import argparse,json,threading,http.server,functools,time,hashlib,traceback,sys
from pathlib import Path
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
INIT=r'''(() => {
 const NativeDate=Date,base=NativeDate.parse('2026-09-07T20:30:00Z');
 window.Date=class extends NativeDate{constructor(...a){super(...(a.length?a:[base]));}static now(){return base;}};
 const storage=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>storage.get(String(k))??null,setItem:(k,v)=>storage.set(String(k),String(v)),removeItem:k=>storage.delete(String(k)),clear:()=>storage.clear()}});
 window.__testRequests=[];
 const originalFetch=window.fetch;
 window.fetch=async(input,opts)=>{
  const u=new URL(typeof input==='string'?input:input.url,location.href);window.__testRequests.push(u.href);
  if(u.origin===location.origin)return originalFetch(input,opts);
  if(u.hostname==='api.aladhan.com'&&u.pathname.includes('/timings/')){
   const date=u.pathname.split('/').at(-1);const [d,m,y]=date.split('-');const p=u.searchParams;
   const tz=window.__testTimezone||new URLSearchParams(location.hash.slice(1)).get('tz')||'Asia/Riyadh';
   const timings={Fajr:'04:46',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Sunset:'18:33',Maghrib:'18:33',Isha:'20:03'};
   return new Response(JSON.stringify({code:200,status:'OK',data:{timings,date:{gregorian:{date,day:d,month:{number:+m,en:'September'},year:y},hijri:{date:'25-03-1448',day:'25',month:{number:3,en:'Rabi al-awwal'},year:'1448',method:'HJCoSA'}},meta:{latitude:+p.get('latitude'),longitude:+p.get('longitude'),timezone:tz,method:{id:+p.get('method')},school:p.get('school')==='1'?'HANAFI':'STANDARD'}}}),{status:200,headers:{'Content-Type':'application/json'}});
  }
  throw new Error('Controlled fixture blocks unrelated external fetch '+u.href);
 };
})();'''
def run(root,output,baseline=False,scenes=None):
 output.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 results=[]
 try:
  with sync_playwright() as p:
   browser=launch_browser(p)
   for scene in scenes or [{'name':'madinah-night','lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','time':'23:30','cloud':0,'wx':0}]:
    context=browser.new_context(viewport={'width':700,'height':720},device_scale_factor=scene.get('dpr',1),reduced_motion='reduce')
    context.add_init_script(INIT)
    page=context.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url))
    page.route('https://fonts.googleapis.com/**',lambda route:route.abort())
    page.route('https://fonts.gstatic.com/**',lambda route:route.abort())
    folder='src/native' if baseline else '.'
    h=f"lat={scene['lat']}&lon={scene['lon']}&tz={scene['tz']}&label={scene['name']}&method=4&simTime={scene['time']}&simWx={scene['wx']}&simCloud={scene['cloud']}&simPrecip=0&simTemp=20&simHumid={scene.get('humidity',45)}&units=c&motion=reduced&qa=1"
    h+=scene.get('extra','')
    url=f'http://127.0.0.1:{server.server_port}/{folder}/index.html?case={scene["name"]}#{h}'
    started=time.monotonic()
    page.evaluate('(h)=>{location.hash=h}',h)
    page.evaluate(INIT.replace('2026-09-07T20:30:00Z',scene.get('utcBase','2026-09-07T20:30:00Z')))
    source=(root/folder/('index.html' if baseline else 'offline.html')).read_text(encoding='utf-8')
    if baseline:source=source.replace('<script src="config.js"></script>','<script>'+(root/folder/'config.js').read_text(encoding='utf-8').replace('</script','<\\/script')+'</script>')
    page.set_content(source,wait_until='load',timeout=30000)
    error=None
    try:
     page.wait_for_function("document.querySelectorAll('.p').length===6 && !!document.querySelector('.mphoto').getAttribute('href')",timeout=20000)
     if not baseline:page.wait_for_function("typeof realSkyState==='function' && realSkyState().status==='ready'",timeout=90000)
    except Exception as e:error=str(e)
    # Terminal state rather than a claim about a single captured screenshot.
    page.screenshot(path=str(output/(scene['name']+'.png')))
    state=page.evaluate("""()=>({qa:window.qaState?.(),sky:window.realSkyState?.(),native:window.SalahNativeSkyHost?.capture(),pbr:{hrefBytes:document.querySelector('.mphoto').getAttribute('href').length,ready:document.querySelector('.c').classList.contains('moon-ready')},prayerRows:document.querySelectorAll('.p').length,classes:document.querySelector('.c').className,syntheticPoints:document.querySelectorAll('.stars circle,.milkyway circle,.starglints line').length,fetches:window.__testRequests})""")
    result={'scene':scene,'seconds':time.monotonic()-started,'error':error,'pageErrors':errors,'state':state,'requests':requests,'sourceSha256':hashlib.sha256((root/folder/'index.html').read_bytes()).hexdigest(),'harness':'actual native app expanded inline on about:blank; inline fixture route; not actual HTTP/file-entry qualification; controlled prayer/weather fixtures' }
    results.append(result);(output/'results.json').write_text(json.dumps(results,indent=2))
    print(scene['name'],result['seconds'],'rows',state['prayerRows'],'sky',(state.get('sky') or {}).get('status'),'errors',errors,flush=True)
    if error:print(error,flush=True)
    context.close()
   browser.close()
 finally:server.shutdown()
 return results
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(ROOT));a.add_argument('--output',required=True);a.add_argument('--baseline',action='store_true');a.add_argument('--scenes');args=a.parse_args()
 r=run(Path(args.root),Path(args.output),args.baseline,json.loads(Path(args.scenes).read_text(encoding='utf-8')) if args.scenes else None)
 sys.exit(1 if any(x['error'] or x['pageErrors'] for x in r) else 0)
