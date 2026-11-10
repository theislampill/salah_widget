"""Actual-entry limb regression; reuses only an identical refined worker scene.

The source cache is test evidence, never a product fallback. DPR/placement changes
still pass through the real request identity, host admission and final compositor.
"""
from pathlib import Path
import argparse, base64, functools, hashlib, http.server, json, math, threading, time
from playwright.sync_api import sync_playwright
from PIL import Image
from browser_runtime import launch_browser, browser_identity
from native_browser_check import INIT, Quiet, ROOT
from moon_receiving_check import OBSERVER, wait
from runtime_identity import runtime_identity

REPLAY = r'''(()=>{
const entry=ENTRY,types={Float32Array,Uint8ClampedArray};
for(const [k,s] of Object.entries(entry.arrays)){const b=Uint8Array.from(atob(s.data),c=>c.charCodeAt(0));entry.metadata[k]=new types[s.type](b.buffer);}
window.__rimCache=new Map([[JSON.stringify(entry.metadata.scene),entry.metadata]]);window.__rimReplays=0;
const NW=Worker;window.Worker=class extends NW{constructor(u,o){super(u,o);const send=this.postMessage.bind(this);
this.addEventListener('message',e=>{if(this.isMoon&&e.data.kind==='result')__rimCache.set(JSON.stringify(e.data.scene),e.data);});
this.postMessage=(m,t)=>{const cached=this.isMoon&&m.kind==='render'&&__rimCache.get(JSON.stringify(m.scene));
if(cached){__rimReplays++;setTimeout(()=>this.dispatchEvent(new MessageEvent('message',{data:{...cached,id:m.id,identity:m.identity}})),0);return;}
return t?send(m,t):send(m);};}};})();'''

MEASURE = r'''()=>{
const cv=document.querySelector('.moon-detail-canvas'),p=document.querySelector('.mphoto'),t=p.getScreenCTM(),r=cv.getBoundingClientRect(),dpr=devicePixelRatio;
const x=t.a*+p.getAttribute('x')+t.e,y=t.d*+p.getAttribute('y')+t.f,w=t.a*+p.getAttribute('width'),h=t.d*+p.getAttribute('height');
const left=Math.floor(x*dpr)-1,top=Math.floor(y*dpr)-1,width=Math.ceil((x+w)*dpr)-left+1,height=Math.ceil((y+h)*dpr)-top+1;
const s=SalahMoonRuntime.state,m=__mq.lastResult,composition=realSkyState().last.composition;
return {dpr,photo:{x,y,width:w,height:h},canvas:r.toJSON(),backing:{width:cv.width,height:cv.height},expectedDevice:{left,top,width,height},
alignmentErrorDevice:{x:r.x*dpr-left,y:r.y*dpr-top,width:r.width*dpr-width,height:r.height*dpr-height},
baseMoonPixels:composition.moonPixels,cloudApplications:composition.cloudApplications,
state:s,detail:SalahMoonDetail.state,acceptedMatchesWorker:s.accepted.identity===m.physicalIdentity&&s.accepted.profile===m.profileIdentity,
legacyHidden:getComputedStyle(p).visibility==='hidden'&&getComputedStyle(document.querySelector('.moccluder')).visibility==='hidden',
sky:realSkyState().status,replays:__rimReplays};}'''


def run(root, output, surface_file, sweep=True):
    root=root.resolve();output.mkdir(parents=True,exist_ok=True)
    record=json.loads(surface_file.read_text(encoding='utf-8'))
    assert record['metadata']['kind']=='result'
    assert record['metadata']['diagnostics']['quality']['status']=='empirical-adaptive'
    assert record['metadata']['diagnostics']['quality']['unsettled']==0
    # Presentation sweeps hold the explicitly admitted physical geometry fixed.
    # Native DPR-aware phase buckets intentionally differ; they cannot share a
    # cached solve. Only the view-convention label changes here. The worker's
    # physical fingerprint excludes that label and includes every field below.
    physical_fields=['basis','sun','earth','distance','size','extent','outSize','diameter','profile']
    physical_before={k:record['metadata']['scene'][k] for k in physical_fields}
    record['metadata']['scene']['mode']='physical-reference'
    assert physical_before=={k:record['metadata']['scene'][k] for k in physical_fields}
    report={'status':'RUNNING','runtime':runtime_identity(root),'cacheSha256':hashlib.sha256(surface_file.read_bytes()).hexdigest(),
            'scope':'Explicit physical-reference replay of an actual refined surface for presentation only; all numerical geometry/profile fields and physical fingerprint unchanged. Native phase solves are qualified separately. Real host/currentness and compositor. Reported crop is left-lit half; its original URL/UTC was not supplied.', 'physicalFields':physical_before,'cases':[], 'pageErrors':[]}
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=launch_browser(pw);report['browser']=browser_identity(browser)
            scene=record['metadata']['scene'];fraction=scene['requestedNativeFraction'];wax=int(scene['waxing'])
            url=f'http://127.0.0.1:{server.server_port}/index.html#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Moon%20rim&method=4&simTime=23:30&simWx=0&simCloud=0&simTemp=20&units=c&motion=reduced&simMoon={fraction}&simWax={wax}&simMoonAlt=20&simMoonH=42&qa=1'
            for dpr in ([1,1.25,2,3] if sweep else [1]):
                # A context owns DPR. Playwright screenshots can restore a CDP
                # override to context defaults, invalidating a supposed sweep.
                context=browser.new_context(viewport={'width':430,'height':640},device_scale_factor=dpr,reduced_motion='reduce')
                context.add_init_script(INIT+'\n'+OBSERVER+'\n'+REPLAY.replace('ENTRY',json.dumps(record)))
                context.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(status=200,body='',content_type='text/css'))
                page=context.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
                page.goto(url,wait_until='domcontentloaded');page.add_style_tag(content='*{animation-play-state:paused!important;transition:none!important}')
                wait(page,'!!window.SalahMoonRuntime',30)
                page.evaluate('(s)=>SalahMoonRuntime.setReferenceScene(s)',scene)
                wait(page,"SalahMoonRuntime.state.status==='ready'&&!SalahMoonRuntime.state.pending&&SalahMoonDetail.state.visible&&realSkyState().status==='ready'",300)
                assert page.evaluate('__rimReplays')>0, 'Exact physical scene cache did not match'
                for shift in ([0,.125,.25,.375,.5,.625,.75,.875,1] if sweep else [0]):
                    page.evaluate('v=>{document.querySelector(".c").style.transform=`translate(${v}px,${v*.7}px)`;SalahRealSky.compose();}',shift)
                    page.wait_for_timeout(75)
                    data=page.evaluate(MEASURE)
                    assert data['dpr']==dpr, 'Capture DPR changed'
                    data.update(shiftCss=[shift,shift*.7])
                    data['checks']={'alignedDeviceFootprint':max(map(abs,data['alignmentErrorDevice'].values()))<=1/16,
                                    'singleMoonOwner':data['baseMoonPixels']==0,
                                    'refinedVisible':data['state']['quality']=='empirical-adaptive' and not data['state']['legacyFallback'] and data['detail']['visible'] and data['acceptedMatchesWorker'] and data['legacyHidden'],
                                    'oneCloudApplication':data['cloudApplications']==1}
                    report['cases'].append(data)
                    if shift in [0,.375,1]:
                        name=f'dpr{dpr}-shift{shift}'
                        r=data['canvas'];clip={'x':max(0,r['x']-3),'y':max(0,r['y']-3),'width':r['width']+6,'height':r['height']+6}
                        page.screenshot(path=output/(name+'-crop.png'),clip=clip)
                        # Diagnostic nearest-neighbor enlargement; preserve original capture too.
                        with Image.open(output/(name+'-crop.png')) as im:im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(output/(name+'-nearest4x.png'))
                        page.locator('.c').screenshot(path=output/(name+'-widget.png'))
                    if shift in [0,.375]:
                        # Direct source-cell overlap integration, independent of
                        # the product's prefix sums. Compare the final displayed
                        # OUTER limb, not a whole-frame average.
                        from moon_rim_spatial import verify_spatial
                        data['spatial']=verify_spatial(page,output,f'dpr{dpr}-s{shift}',data)
                        data['checks']['spatialOuterLimb']=data['spatial']['passed']
                context.close()
            browser.close()
        report['status']='PASS' if all(all(x['checks'].values()) for x in report['cases']) and not report['pageErrors'] else 'FAIL'
    finally:
        server.shutdown();(output/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'cases':len(report['cases']),'failed':[{'dpr':x['dpr'],'shift':x['shiftCss'],'checks':x['checks'],'alignment':x['alignmentErrorDevice'],'baseMoonPixels':x['baseMoonPixels']} for x in report['cases'] if not all(x['checks'].values())]},indent=2))
    return report['status']=='PASS'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);p.add_argument('--surface-file',type=Path,required=True);p.add_argument('--single',action='store_true');a=p.parse_args()
    raise SystemExit(0 if run(a.root,a.output,a.surface_file,not a.single) else 1)
