"""Refined actual-widget pixels, layer exclusion controls, and retained V5 references.

Does not rerun the V5 research campaign or modify the runtime. Reference PNGs
must come with the selected, hash-verified custody record from the V5 gallery.
"""
from pathlib import Path
import argparse,base64,functools,hashlib,http.server,json,threading,time,traceback
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser,browser_identity
from native_browser_check import INIT,Quiet,ROOT
from moon_receiving_check import OBSERVER,STATE,wait
from runtime_identity import runtime_identity

SOURCE_PROOF=r'''async()=>{
 const m=__mq.lastResult,s=SalahMoonRuntime.state,c=SalahMoonRuntime.surface();
 const hash=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer.slice(a.byteOffset,a.byteOffset+a.byteLength))),x=>x.toString(16).padStart(2,'0')).join('');
 const bytes=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
 const legacy=_moonCv.getContext('2d').getImageData(0,0,_moonCv.width,_moonCv.height).data;
 const nodes={};for(const k of ['.mphoto','.moccluder','.moon-detail-canvas']){const e=document.querySelector(k),g=getComputedStyle(e);nodes[k]={visibility:g.visibility,display:g.display,opacity:g.opacity,zIndex:g.zIndex,rect:e.getBoundingClientRect().toJSON()};}
 const binary=a=>{const u=new Uint8Array(a.buffer,a.byteOffset,a.byteLength);let t='';for(let i=0;i<u.length;i+=32768)t+=String.fromCharCode(...u.subarray(i,i+32768));return btoa(t);};
 return {workerKind:m.kind,workerKernel:m.diagnostics.kernel,workerPhysicalIdentity:m.physicalIdentity,workerProfileIdentity:m.profileIdentity,
  acceptedMatchesWorker:s.accepted.identity===m.physicalIdentity&&s.accepted.profile===m.profileIdentity&&JSON.stringify(s.accepted.scene)===JSON.stringify(m.scene),
  publishedCanvasSha256:await hash(bytes),workerRgbaSha256:await hash(m.rgba),legacyCanvasSha256:await hash(legacy),linearSurfaceSha256:await hash(m.surfaceLinear),
  photoUsesPublishedTerrain:document.querySelector('.mphoto').getAttribute('href')===c.toDataURL(),detailEnabled:SalahMoonRuntime.detailEnabled,nodes,
  nativeForegroundMoonPixels:realSkyState().last.composition.moonPixels,size:m.surfaceSize,extent:m.surfaceExtent,linearBase64:binary(m.surfaceLinear),
  surfacePng:c.toDataURL(),legacyPng:_moonCv.toDataURL(),quality:m.diagnostics.quality,state:s};
}'''

def project_black(linear,extent,side,diameter=208):
    """Independent area integral of actual worker linear premultiplied samples."""
    n=linear.shape[0];scale=n/(diameter*extent)
    integral=np.pad(linear.astype(np.float64).cumsum(0).cumsum(1),((1,0),(1,0),(0,0)))
    coords=np.clip(n/2+(np.arange(side+1)-side/2)*scale,0,n)
    ix=np.minimum(n-1,np.floor(coords).astype(int));f=coords-ix
    value=(integral[ix[:,None],ix[None,:]]*(1-f[:,None,None])*(1-f[None,:,None])+
           integral[ix[:,None]+1,ix[None,:]]*f[:,None,None]*(1-f[None,:,None])+
           integral[ix[:,None],ix[None,:]+1]*(1-f[:,None,None])*f[None,:,None]+
           integral[ix[:,None]+1,ix[None,:]+1]*f[:,None,None]*f[None,:,None])
    v=np.maximum(0,(value[1:,1:]-value[:-1,1:]-value[1:,:-1]+value[:-1,:-1])/(scale*scale))
    code=np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)
    return np.floor(np.clip(code,0,1)*255+.5).astype(np.uint8)

def difference(a,b):
    x=np.asarray(Image.open(a).convert('RGB'),dtype=np.int16);y=np.asarray(Image.open(b).convert('RGB'),dtype=np.int16)
    if x.shape!=y.shape:raise ValueError('Comparison dimensions differ')
    d=x-y
    return dict(changedPixels=int(np.count_nonzero(np.any(d,axis=2))),maximumCode=int(np.abs(d).max()),rmsCode=float(np.sqrt(np.mean(d.astype(float)**2))),meanAbsoluteCode=float(np.abs(d).mean()))

def run(root,out,refs):
    root=root.resolve();out.mkdir(parents=True,exist_ok=True);before=runtime_identity(root);rows=[]
    custody=json.loads((refs/'reference-custody.json').read_text());reference={s['name']:s for s in custody['selected']}
    report=dict(status='RUNNING',runtimeTreeSha256=before['treeSha256'],harnessSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),referenceCustodySha256=hashlib.sha256((refs/'reference-custody.json').read_bytes()).hexdigest(),phases=rows,
                scope='Actual local HTTP widget, final empirical-adaptive terrain, observed real worker output and reversible layer controls. Refined means donor final angular criterion, not universal physical convergence. Reference comparison uses retained V5 q4096 outputs; no research rerun.')
    def save(): (out/'results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            b=launch_browser(p);report['browser']=browser_identity(b);c=b.new_context(viewport={'width':430,'height':640},device_scale_factor=2,reduced_motion='reduce')
            c.add_init_script(INIT);c.add_init_script(OBSERVER);q=c.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)));report['pageErrors']=errors
            c.route('https://fonts.googleapis.com/**',lambda r:r.abort());c.route('https://fonts.gstatic.com/**',lambda r:r.abort())
            url=f'http://127.0.0.1:{server.server_port}/index.html#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=V5%20terrain&method=4&simTime=23:30&simWx=0&simCloud=0&simTemp=20&units=c&motion=reduced&simMoon=.12&simWax=1&simMoonAlt=20&simMoonH=42&qa=1'
            start=time.monotonic();q.goto(url,wait_until='domcontentloaded');report['url']=url
            wait(q,"!!window.SalahMoonRuntime&&document.querySelectorAll('.p').length===6",30)
            for name,fraction in [('wax_012',.12),('wax_050',.5),('wax_075',.75),('wax_099',.99)]:
                if rows:
                    start=time.monotonic();q.evaluate("f=>{SIM.moon=String(f);renderMoon();render();SalahMoonRuntime.request();}",fraction)
                wait(q,"SalahMoonRuntime.state.status==='ready'&&!SalahMoonRuntime.state.pending",290)
                state=q.evaluate(STATE);quality=state['moon']['last']['quality']
                assert state['moon']['quality']=='empirical-adaptive' and quality['unsettled']==0 and len(quality['history'])>=2,(name,quality)
                wait(q,"SalahMoonDetail.state.visible&&SalahMoonRuntime.detailEnabled&&realSkyState().status==='ready'",60)
                proof=q.evaluate(SOURCE_PROOF);linear_bytes=base64.b64decode(proof.pop('linearBase64'))
                assert hashlib.sha256(linear_bytes).hexdigest()==proof['linearSurfaceSha256']
                for kind in ['surface','legacy']:
                    png=base64.b64decode(proof.pop(kind+'Png').split(',',1)[1]);(out/(name+'-'+kind+'.png')).write_bytes(png)
                assert proof['workerKind']=='result' and proof['workerKernel']=='metric-radial-terrain-wasm-mb1'
                assert proof['acceptedMatchesWorker'] and proof['photoUsesPublishedTerrain'] and proof['detailEnabled']
                assert proof['publishedCanvasSha256']==proof['workerRgbaSha256']!=proof['legacyCanvasSha256']
                assert proof['workerProfileIdentity']==custody['profileIdentity']
                assert proof['nodes']['.mphoto']['visibility']=='hidden' and proof['nodes']['.moccluder']['visibility']=='hidden'
                assert proof['nodes']['.moon-detail-canvas']['visibility']=='visible' and proof['nativeForegroundMoonPixels']==0
                q.locator('.c').screenshot(path=str(out/(name+'-widget.png')));q.locator('.moon-detail-canvas').screenshot(path=str(out/(name+'-crop.png')))
                # A hostile replacement of the hidden SVG surface cannot affect the visible Moon.
                old=q.evaluate("()=>{const e=document.querySelector('.mphoto'),s=e.getAttribute('href'),v=document.createElement('canvas');v.width=v.height=300;v.getContext('2d').fillStyle='#ff00ff';v.getContext('2d').fillRect(0,0,300,300);e.setAttribute('href',v.toDataURL());SalahRealSky.compose();return s;}")
                q.locator('.moon-detail-canvas').screenshot(path=str(out/(name+'-diagnostic-legacy-poison.png')))
                q.evaluate("s=>document.querySelector('.mphoto').setAttribute('href',s)",old)
                hidden=q.add_style_tag(content='.moon-detail-canvas{visibility:hidden!important}')
                rect=proof['nodes']['.moon-detail-canvas']['rect'];q.screenshot(path=str(out/(name+'-diagnostic-detail-hidden.png')),clip={k:rect[k] for k in ['x','y','width','height']})
                hidden.evaluate('(e)=>e.remove()')
                q.locator('.moon-detail-canvas').screenshot(path=str(out/(name+'-restored.png')))
                poisoned=difference(out/(name+'-crop.png'),out/(name+'-diagnostic-legacy-poison.png'));removed=difference(out/(name+'-crop.png'),out/(name+'-diagnostic-detail-hidden.png'));restored=difference(out/(name+'-crop.png'),out/(name+'-restored.png'))
                assert poisoned['changedPixels']==0 and restored['changedPixels']==0 and removed['changedPixels']>1000
                assert q.evaluate("SalahMoonRuntime.state.status==='ready'&&!SalahMoonRuntime.state.legacyFallback&&!SalahMoonRuntime.state.pending")
                ref=refs/(name+'-reference.png');assert hashlib.sha256(ref.read_bytes()).hexdigest()==reference[name]['sha256']
                im=Image.open(ref);assert im.width==im.height
                linear=np.frombuffer(linear_bytes,dtype='<f4').reshape(proof['size'],proof['size'],3)
                Image.fromarray(project_black(linear,proof['extent'],im.width)).save(out/(name+'-worker-D208.png'))
                delta=difference(out/(name+'-worker-D208.png'),ref)
                row=dict(name=name,requestedFraction=fraction,refinedSeconds=time.monotonic()-start,state=state,sourceProof=proof,legacyPoisonControl=poisoned,detailHiddenControl=removed,restoreControl=restored,reference=reference[name]['originalPath'],referenceComparison=delta,
                         referenceScope='Independent linear area integration of actual WASM surface at reference D208 footprint on black. Phase-angle buckets/adaptive angular rules differ; errors recorded, not a new dense-reference certificate.',captures={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob(name+'*.png')},passed=True)
                rows.append(row);save();print(name,'refined; layer controls pass; reference',delta,flush=True)
            assert not errors and runtime_identity(root)==before
            c.close();b.close();report['status']='PASS_SCOPED'
    except Exception:
        report['status']='FAIL';report['exception']=traceback.format_exc()
    finally:server.shutdown();save()
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);p.add_argument('--references',type=Path,required=True);a=p.parse_args();r=run(a.root,a.output,a.references);print(r['status'],r.get('exception',''));raise SystemExit(0 if r['status']=='PASS_SCOPED' else 1)
