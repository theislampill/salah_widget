"""Four isolated native functional cases for r109. Controlled faults, not S1 timing or continuous-display evidence."""
from pathlib import Path
import asyncio,datetime,hashlib,http.server,json,os,sys,threading
from urllib.parse import parse_qs,urlsplit
from playwright.async_api import async_playwright
O=Path(__file__).resolve().parent;R=Path(r'${REPO_ROOT}')
sys.path.insert(0,str(R/'tests'));from v1_browser import fixture
sys.path.insert(0,str(R/'tools/cp9'));from browser_runtime import browser_options,browser_identity
from runtime_identity import runtime_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=O/'native/retention-r109';assert not out.exists();out.mkdir()
record={'schema':'r0021-retention-native/v1','scope':__doc__,'scriptSha256':sha(Path(__file__)),'cases':[],'errors':[]}
INIT=r"""(()=>{
 const D=Date,anchor=D.parse('2026-09-26T03:00:00Z'),start=performance.now();window.Date=class extends D{constructor(...a){super(...(a.length?a:[anchor+performance.now()-start]));}static now(){return anchor+performance.now()-start;}};
 const fetch0=fetch.bind(window);window.fetch=(u,...a)=>{const url=new URL(String(u),location.href);return fetch0(['api.aladhan.com','api.open-meteo.com','api.rainviewer.com'].includes(url.hostname)?'/fixture?url='+encodeURIComponent(url.href):u,...a);};
 const read=CanvasRenderingContext2D.prototype.getImageData;window.__holdPrep=false;window.__prepThrows=0;
 CanvasRenderingContext2D.prototype.getImageData=function(...a){if(window.__holdPrep&&this.canvas.width===325){window.__prepThrows++;throw Error('r109 controlled foreground readback failure');}return read.apply(this,a);};
 let preview;Object.defineProperty(window,'SalahStartSkyPreview',{configurable:true,get(){return preview;},set(fn){preview=function(...a){window.__holdPrep=true;window.__initialBefore={at:performance.now(),head:!!window.SalahFirstPaint?.value,style:!!document.querySelector('#native-first-paint')};try{return fn.apply(this,a);}finally{window.__initialAfter={at:performance.now(),head:!!window.SalahFirstPaint?.value,style:!!document.querySelector('#native-first-paint'),state:window.SalahSkyPreview?.state};}};}});
 const post=Worker.prototype.postMessage;window.__badRequest=null;
 Worker.prototype.postMessage=function(m,...a){if(window.__failNextSky&&m?.kind==='render'&&m.job?.options?.view){window.__failNextSky=false;const bad=structuredClone(m);bad.job.options.view.width=0;window.__badRequest={at:performance.now(),id:m.id,originalView:m.job.options.view,changedView:bad.job.options.view};return post.call(this,bad,...a);}return post.call(this,m,...a);};
})();"""
STATE=r"""()=>({at:performance.now(),head:!!window.SalahFirstPaint?.value,headStyle:!!document.querySelector('#native-first-paint'),classes:document.querySelector('.c').className,preview:window.SalahSkyPreview?.state,sky:window.SalahRealSky?.state,detail:window.SalahMoonDetail?.state,moon:window.SalahMoonRuntime?.state,prepThrows:window.__prepThrows,badRequest:window.__badRequest,geometry:document.querySelector('.c').getBoundingClientRect().toJSON(),rows:document.querySelectorAll('.times .p').length})"""
DETAIL_FAULT=r"""async()=>{
 const c=document.querySelector('.real-sky-preview'),owner=window.SalahMoonDetail,fn=owner.compose;
 const before={state:window.SalahSkyPreview.state,png:c.toDataURL(),detail:owner.state};
 const clouds=document.querySelector('.cloudcanvas'),cx=clouds.getContext('2d');cx.fillStyle='rgba(100,120,150,.5)';cx.fillRect(0,40,clouds.width,80);
 let thrown=0;owner.compose=function(){thrown++;throw Error('r109 controlled detail readback failure');};
 window.SalahSkyPreview.update();
 const end=performance.now()+2000;while(!thrown&&performance.now()<end)await new Promise(r=>setTimeout(r,10));
 const after={state:window.SalahSkyPreview.state,png:c.toDataURL(),detail:owner.state};owner.compose=fn;
 return {thrown,beforeUtc:before.state.utcMs,afterUtc:after.state.utcMs,beforeDraws:before.state.draws,afterDraws:after.state.draws,sameBackground:before.png===after.png,beforeDetail:before.detail,afterDetail:after.detail,afterState:after.state,controlledCloudPixels:true};
}"""
def provider(url):
 p=urlsplit(url)
 if p.hostname!='api.aladhan.com':return None
 v=fixture(url,False);day,month,year=p.path.rstrip('/').split('/')[-1].split('-')
 v['data']['date']['gregorian'].update(date=f'{day}-{month}-{year}',day=day,month={'number':int(month)},year=year)
 v['data']['date']['hijri'].update(day='14'if day=='26'else'13',month={'number':4,'en':'Rabi al-Thani'},year='1448')
 v['data']['meta']['timezone']='America/New_York'
 v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
 return v
async def run():
 async with async_playwright()as pw:
  for family,exe in [('chromium',r'${ISOLATED_CHROMIUM}'),('firefox',r'${ISOLATED_FIREFOX}')]:
   for version,folder in [('before','integrated-r27'),('after','integrated-r28-retention')]:
    root=O/'builds'/folder;identity=runtime_identity(root);name=family+'-'+version;browser=None;server=None;ctx=None
    item={'name':name,'runtime':identity,'states':[],'errors':[]};record['cases'].append(item)
    release=asyncio.Event()
    try:
     class Handler(http.server.SimpleHTTPRequestHandler):
      def log_message(self,*a):pass
      def translate_path(self,p):return str(root/urlsplit(p).path.lstrip('/'))
      def do_GET(self):
       if self.path.startswith('/fixture?'):
        value=provider(parse_qs(urlsplit(self.path).query)['url'][0]);body=json.dumps(value).encode()
        self.send_response(200 if value is not None else 503);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers()
        try:self.wfile.write(body)
        except(BrokenPipeError,ConnectionResetError):pass
       else:super().do_GET()
     server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
     os.environ['SALAH_BROWSER']=family;os.environ['SALAH_BROWSER_EXECUTABLE']=exe
     _,options=browser_options();browser=await getattr(pw,family).launch(**options);item['browser']=browser_identity(browser)
     ctx=await browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='America/New_York',locale='en-US')
     async def hold(route):
      await release.wait();await route.continue_()
     await ctx.route('**/real-sky/native-data.js*',hold);await ctx.add_init_script(INIT)
     page=await ctx.new_page();page.on('pageerror',lambda e:item['errors'].append(str(e)))
     await page.goto(f'http://127.0.0.1:{server.server_port}/#preferLocal=1&lat=28.5383&lon=-81.3792&tz=America%2FNew_York&label=Orlando&method=2&motion=full',wait_until='domcontentloaded',timeout=20000)
     await page.wait_for_function('()=>window.__initialAfter',timeout=10000)
     item['initial']=await page.evaluate('()=>({before:__initialBefore,after:__initialAfter})')
     async def capture(stage):
      s=await page.evaluate(STATE);s['stage']=stage;s['file']=name+'-'+stage+'.png';await page.screenshot(path=str(out/s['file']));s['sha256']=sha(out/s['file']);item['states'].append(s);return s
     initial=await capture('preparation-failure');assert item['initial']['before']['head'],'No initial head reached controlled boundary'
     if version=='after':assert initial['headStyle']and initial['preview']['retained']
     else:assert not initial['headStyle'],'Baseline did not reproduce initial withdrawal'
     await page.evaluate('()=>window.__holdPrep=false')
     await page.wait_for_function('()=>window.SalahSkyPreview?.state.status==="ready"&&window.SalahMoonDetail?.state.visible',timeout=12000)
     await capture('preview-recovered')
     item['detailFailure']=await page.evaluate(DETAIL_FAULT);assert item['detailFailure']['thrown']>0,'Detail exception not reached'
     if version=='after':assert item['detailFailure']['sameBackground'],'Failed detail replaced background'
     else:assert not item['detailFailure']['sameBackground'],'Baseline did not reproduce partial publication'
     await capture('detail-failure');release.set()
     await page.wait_for_function('()=>window.SalahRealSky?.state.displayed&&!window.SalahRealSky.state.displayed.retained',timeout=35000)
     good=await capture('refined-before-error');item['workerBefore']=good['sky']['displayed'];oldErrors=len(good['sky']['errors'])
     await page.evaluate('()=>{window.__failNextSky=true;window.SalahRealSky.request(true)}')
     await page.wait_for_function('(n)=>window.SalahRealSky?.state.errors.length>n',arg=oldErrors,timeout=10000)
     failed=await capture('worker-error');assert failed['badRequest'],'Worker corruption did not reach real request'
     assert failed['sky']['status']=='unavailable'
     item['workerRetained']=failed['sky'].get('displayed')
     if version=='after':assert item['workerRetained']['retained']and item['workerRetained']['utcMs']==item['workerBefore']['utcMs']
     else:assert item['workerRetained']is None,'Baseline did not withdraw refined scene'
     await page.evaluate('()=>window.SalahRealSky.request(true)')
     await page.wait_for_function('()=>window.SalahRealSky?.state.status==="ready"&&window.SalahRealSky.state.displayed&&!window.SalahRealSky.state.displayed.retained',timeout=35000)
     await capture('worker-recovered');assert not item['errors'];item['status']='EXPECTED_FUNCTIONAL_RESULT'
    except BaseException as e:item['status']='INCOMPLETE';item['exception']=repr(e);raise
    finally:
     release.set()
     if ctx:await ctx.close()
     if browser:await browser.close()
     if server:server.shutdown();server.server_close()
     item['runtimeUnchanged']=identity==runtime_identity(root)
     (out/'partial.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
    print(json.dumps({'name':name,'status':item['status'],'runtimeUnchanged':item['runtimeUnchanged']}),flush=True)
lock=O/'native-resource.lock'
with lock.open('x')as f:f.write('retention-r109')
record['startedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:asyncio.run(run());record['status']='RETURNED_FUNCTIONAL_COMPARISON'
except BaseException as e:record['status']='INCOMPLETE';record['errors'].append(repr(e));raise
finally:
 record['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (out/'RESULT.json').write_bytes((json.dumps(record,indent=2)+'\n').encode());assert lock.read_text()=='retention-r109';lock.unlink()
