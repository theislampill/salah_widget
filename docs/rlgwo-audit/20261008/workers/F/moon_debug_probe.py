"""Primary-only native opt-in instrument probe; actual public normal 1x Moon."""
import argparse, hashlib, importlib.util, json, pathlib, sys, time, traceback
from playwright.sync_api import sync_playwright
HERE=pathlib.Path(__file__).resolve().parent;AUDIT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('public_smoke',AUDIT/'public-smoke.py');public=importlib.util.module_from_spec(spec);spec.loader.exec_module(public)
INIT=r'''(()=>{window.__instrumentProbe={first:null,errors:[]};function f(){if(typeof moonDebugSamples==='function'){try{__instrumentProbe.first={at:performance.now(),sample:moonDebugSamples(),runtime:window.SalahMoonRuntime?.state??null};}catch(e){__instrumentProbe.errors.push(String(e));}}else requestAnimationFrame(f);}requestAnimationFrame(f);})();'''
STATE=r'''()=>{const s=moonDebugSamples(),q=qaState().moonTruth,cv=SalahMoonRuntime.surface(),raw=cv?.getContext('2d')?.getImageData(0,0,cv.width,cv.height)?.data;return {at:performance.now(),utc:Date.now(),scale:TIMESCALE,debug:DEBUGMOON,sample:s,truth:q,runtime:SalahMoonRuntime.state,accepted:SalahNativeSkyHost.capture(false),overlay:document.querySelector('.dbgmoon')?.textContent,overlayVisible:getComputedStyle(document.querySelector('.dbgmoon')).display,independent:s.samples.map(p=>{const i=4*(p.y*cv.width+p.x);return {x:p.x,y:p.y,lum:Math.round((raw[i]+raw[i+1]+raw[i+2])/3),alpha:raw[i+3]};})};}'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--timeout',type=int,default=180);a=p.parse_args()
 out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
 r={'target':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','runtimeSha256':'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260','harnessSha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'scope':'Actual public source; private profile with same saved manual public Orlando fixture as rollout, real UTC/providers, normal1x, opt-in debugMoon; actual current V5 surface retained, no Moon omission/no phase campaign/no solver replay. Initial unavailable and current raw samples plus synchronous reversible error controls; sampled image is raw backing, not composited sky.'}
 try:
  with sync_playwright() as pw:
   b=public.launch_browser(pw);r['browser']=public.browser_identity(b)
   try:
    c=b.new_context(viewport={'width':390,'height':600},timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference',device_scale_factor=1)
    try:
     c.add_init_script('if(location.hostname==="theislampill.github.io"&&!localStorage.getItem("salah_widget:config:v1"))localStorage.setItem("salah_widget:config:v1",JSON.stringify({...'+json.dumps(public.SETTINGS)+',savedAt:Date.now()}));')
     c.add_init_script(INIT);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     response=page.goto(public.PUBLIC+'#local=1&debugMoon=1',wait_until='domcontentloaded');r['url']=page.url;r['servedIndexSha256']=hashlib.sha256(response.body()).hexdigest();assert r['servedIndexSha256']=='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
     page.wait_for_function('window.__instrumentProbe.first!==null',timeout=10000);r['initial']=page.evaluate('__instrumentProbe')
     assert not r['initial']['errors'];assert r['initial']['first']['sample']['status']=='unavailable','initial actual absence must be unavailable'
     page.wait_for_function('typeof qaState==="function"&&qaState().cache.prayerLoaded&&window.SalahMoonRuntime?.surface()',timeout=a.timeout*1000)
     page.evaluate('renderMoon();render();');page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');r['current']=page.evaluate(STATE)
     current=r['current'];s=current['sample'];assert current['debug'] and current['scale']==1;assert s['status']=='ok' and s['width']==300 and s['height']==300 and s['radius']==144
     assert [(x['label'],x['x'],x['y']) for x in s['samples']]==[('inner',222,150),('limb',293,150),('edge',294,150),('disc exterior',295,150),('canvas exterior',299,150)]
     assert all(x['status']=='ok' and x['lum']==z['lum'] and x['alpha']==z['alpha'] for x,z in zip(s['samples'],current['independent']))
     assert current['truth']['moonSkyFresh'] is True and current['truth']['lastConsumed']['status']=='completed'
     assert current['truth']['surface']['status']=='v5-terrain' and current['runtime']['visibleSource'] in ['terrain-preview','refined-terrain']
     assert current['truth']['surface']['visibleSource']==current['runtime']['visibleSource'];assert current['overlayVisible']=='block';assert 'canvas 300×300 R144' in current['overlay']
     r['errorControls']=page.evaluate(r'''()=>{const cv=SalahMoonRuntime.surface(),ctx=cv.getContext('2d'),data=ctx.getImageData(0,0,cv.width,cv.height).data,hadContext=Object.hasOwn(cv,'getContext'),oldContext=cv.getContext,hadRead=Object.hasOwn(ctx,'getImageData'),oldRead=ctx.getImageData,out={};try{cv.getContext=()=>null;out.missingContext=moonDebugSamples();}finally{if(hadContext)cv.getContext=oldContext;else delete cv.getContext;}try{ctx.getImageData=()=>{throw Error('controlled audit read failure')};out.throwingRead=moonDebugSamples();}finally{if(hadRead)ctx.getImageData=oldRead;else delete ctx.getImageData;}out.bounds=[[300,150],[-1,150],[150,-1],[150,300],[1.5,150]].map(([x,y])=>sampleMoonPixel(data,300,300,x,y));out.restored=cv.getContext===oldContext&&ctx.getImageData===oldRead;out.restoredSample=moonDebugSamples();return out;}''')
     e=r['errorControls'];assert e['missingContext']['status']=='unavailable' and e['throwingRead']['status']=='unavailable';assert all(x['status']=='OOB' for x in e['bounds']);assert e['restored'] and e['restoredSample']['status']=='ok'
     page.locator('.c').screenshot(path=str(out/'debug-card.png'),animations='allow');page.locator('.dbgmoon').screenshot(path=str(out/'debug-readout.png'),animations='allow')
     r['pageErrors']=errors;assert not errors;r['status']='PASS'
    finally:c.close()
   finally:b.close()
 except Exception as e:r.update(status='FAIL',error=str(e),traceback=traceback.format_exc());raise
 finally:(out/'results.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':r.get('status','INCOMPLETE'),'output':str(out),'source':r.get('servedIndexSha256'),'browser':r.get('browser')}),flush=True)
if __name__=='__main__':main()
