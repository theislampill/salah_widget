"""Actual HTTP timetable text/background pairs; isolated fixture, no timing claims."""
from pathlib import Path
import argparse, datetime, functools, hashlib, http.server, json, math, os, re, subprocess, sys, threading
from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/cp9'))
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity

def sha(b): return hashlib.sha256(b).hexdigest()
def write(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def lum(rgb):
    c=[v/255 for v in rgb[:3]]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    return sum(x*y for x,y in zip(c,[.2126,.7152,.0722]))
def ratio(a,b):
    a,b=lum(a),lum(b);return (max(a,b)+.05)/(min(a,b)+.05)

INSPECT=r'''async () => {
const base=window.__appearanceFixture.snapshot(),rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}},chain=e=>{const a=[];for(;e;e=e.parentElement)a.push({tag:e.tagName,id:e.id,className:typeof e.className==='string'?e.className:'SVG',opacity:+getComputedStyle(e).opacity});return a};
const boxStyle=s=>({padding:s.padding,gap:s.gap,borderWidth:s.borderWidth,borderRadius:s.borderRadius,fontFamily:s.fontFamily,fontSize:s.fontSize,lineHeight:s.lineHeight,fontWeight:s.fontWeight});
base.rows=Array.from(document.querySelectorAll('.p')).map(e=>{const s=getComputedStyle(e);return{text:e.textContent,className:e.className,rect:rect(e),boxStyle:boxStyle(s),color:s.color,opacity:s.opacity,background:s.background,filter:s.filter,blend:s.mixBlendMode,backdropFilter:s.backdropFilter,chain:chain(e),texts:Array.from(e.querySelectorAll('b,.tm')).map(t=>{const s=getComputedStyle(t);return{text:t.textContent,rect:rect(t),color:s.color,font:s.font,fontFamily:s.fontFamily,fontWeight:s.fontWeight,opacity:+s.opacity,chain:chain(t)}})}});
base.geometry={};for(const s of ['.c','.h','.e','.buckle','.wt','.panel','.arc','.foc','.cn','.nt','.bar','.left','.times','.d','#ceDateButton','#ahDateButton','#ce','#ah']){const e=document.querySelector(s);if(e){const cs=getComputedStyle(e);base.geometry[s]={rect:rect(e),fontFamily:cs.fontFamily,fontSize:cs.fontSize,lineHeight:cs.lineHeight,fontWeight:cs.fontWeight,padding:cs.padding,gap:cs.gap,borderWidth:cs.borderWidth,borderRadius:cs.borderRadius}}};
base.moon=JSON.parse(JSON.stringify(window.SalahMoonRuntime?.state??null));base.sky=window.realSkyState?.()??null;base.cardClasses=document.querySelector('.c').className;
base.clock=Date.now();base.hash=location.hash;base.cardStyle=document.querySelector('.c').getAttribute('style');
base.canvases=[];
for(const e of document.querySelectorAll('.c canvas')){
 const cs=getComputedStyle(e),ancestors=chain(e),visible=ancestors.every(a=>a.opacity>0)&&cs.display!=='none'&&cs.visibility!=='hidden'&&e.getBoundingClientRect().width>0;
 // Read native pixels; never replace a canvas, scheduler, renderer or draw call.
 const bytes=new TextEncoder().encode(e.toDataURL('image/png'));
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
 base.canvases.push({id:e.id,className:e.className,width:e.width,height:e.height,rect:rect(e),visible,opacity:cs.opacity,transform:cs.transform,filter:cs.filter,blend:cs.mixBlendMode,sha256:digest});
}
base.scene={clock:base.clock,hash:base.hash,cardStyle:base.cardStyle,sky:{status:base.sky?.status,physical:base.sky?.physical,displayed:base.sky?.displayed,native:base.sky?.last?.native,utcMs:base.sky?.last?.utcMs},moon:{current:base.moon?.current,epoch:base.moon?.epoch,generation:base.moon?.generation,acceptedIdentity:base.moon?.accepted?.identity},canvases:base.canvases.filter(c=>c.visible)};
return base;
}'''

def renderer_valid(state):
    sky,moon=state.get('sky') or {},state.get('moon') or {}
    return (sky.get('status')=='ready' and sky.get('physical') is True and not sky.get('errors')
            and moon.get('current') is True and moon.get('legacyFallback') is False and not moon.get('errors'))

def difference(a,b):
    d=ImageChops.difference(a,b)
    return {'bbox':d.getbbox(),'channelExtrema':d.getextrema()}

def run(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=args.workspace.resolve();identity=runtime_identity(source)
    # Preserve every executed collector/import, not only an unresolvable digest.
    collector={}
    for rel in ['tests/r0018-default-readability.py','tests/r0018-appearance-browser-fixture.cjs','tests/r0018-timetable-contrast.cjs','tests/r0018-appearance-fixture.cjs','tests/r0001-browser-fixture.cjs','tools/cp9/browser_runtime.py','tools/cp9/runtime_identity.py']:
        data=(ROOT/rel).read_bytes();target=out/'collector'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);collector[rel]=sha(data)
    write(out/'collector.json',collector)
    assets=['/'+p for p in identity['files']]
    request={'fixture':str(ROOT/'tests/r0018-appearance-browser-fixture.cjs'),'source':str(source/'index.html'),'scene':args.scene,'appearance':args.appearance,'options':{'assetPaths':assets,'stress':args.stress,'mutant':args.mutant,'dateCase':args.date_case}}
    request_path=out/'fixture-input.json';write(request_path,request)
    script="const fs=require('node:fs'),r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')),f=require(r.fixture),s=f.spec(r.scene,r.appearance);let hash=f.routeHash(s)+'&school=0';if(r.options.dateCase!=='compact'){for(const p of [s.today,s.tomorrow])p.date.hijri.month.en='Rabīʿ al-awwal';hash+='&datefmt=DD%20MMMM%20YYYY';}process.stdout.write(JSON.stringify({spec:s,hash,html:f.buildPage(fs.readFileSync(r.source,'utf8'),s,r.options)}));"
    generated=json.loads(subprocess.check_output([args.node,'-e',script,str(request_path)],cwd=ROOT).decode('utf-8'))
    html=generated.pop('html').encode('utf-8');(out/'fixture.html').write_bytes(html)
    served=[]
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if path=='/index.html':
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(html);served.append(path);return
            if path not in assets:
                self.send_error(404,'Outside pinned runtime allowlist');return
            served.append(path);super().do_GET()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(source)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    errors=[];network=[];font_receipts=[];result={'schema':'r0018-native-readability/1','atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':args.stage,'sourceRuntime':identity,'fixtureSha256':sha(html),'driverSha256':sha(Path(__file__).read_bytes()),'helperSha256':sha((ROOT/'tests/r0018-appearance-browser-fixture.cjs').read_bytes()),'syntheticPrayerWeather':True,'fixture':generated,'stress':args.stress,'scope':'Actual local HTTP entry with native assets, production source bodies, pre-script fixed Date/private Map and controlled prayer transport. Frozen SIM stills, no motion/timing or actual extension-parent claim.'}
    try:
        with sync_playwright() as p:
            browser=launch_browser(p);result['browser']=browser_identity(browser)
            result['browser']['executableSha256']=sha(Path(os.environ['SALAH_BROWSER_EXECUTABLE']).read_bytes())
            context=browser.new_context(viewport={'width':args.width,'height':args.height},device_scale_factor=args.dpr,reduced_motion='reduce',timezone_id='Asia/Riyadh',locale='en-US')
            if args.font_fixture:
                font_dir=args.font_fixture.resolve();font_manifest=json.loads((font_dir/'manifest.json').read_text(encoding='utf-8'))
                fonts={r['url']:r for r in font_manifest['files']}
                def pinned_font(route):
                    record=fonts.get(route.request.url)
                    if record is None:raise AssertionError('Unpinned font resource: '+route.request.url)
                    data=(font_dir/record['sha256']).read_bytes()
                    assert sha(data)==record['sha256'] and len(data)==record['bytes'],'Pinned font bytes changed'
                    route.fulfill(status=record['status'],body=data,content_type=record['contentType'])
                context.route(re.compile(r'https://fonts\.(googleapis|gstatic)\.com/.*'),pinned_font)
                result['fontFixture']=font_manifest
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:network.append({'url':r.url,'failure':r.failure}))
            def font_finished(request):
                if not re.match(r'https://fonts\.(googleapis|gstatic)\.com/',request.url):return
                try:
                    response=request.response();body=response.body();digest=sha(body)
                    (out/('font-'+digest)).write_bytes(body)
                    font_receipts.append({'url':request.url,'status':response.status,'sha256':digest,'bytes':len(body),'contentType':response.header_value('content-type')})
                except Exception as error:font_receipts.append({'url':request.url,'error':str(error)})
            context.on('requestfinished',font_finished)
            try:
                page.goto(f'http://127.0.0.1:{server.server_port}/index.html?case={args.stage}-{args.scene}'+generated['hash'],wait_until='domcontentloaded')
                page.wait_for_function('window.__appearanceFixture?.snapshot().ready && document.fonts.status === "loaded"',timeout=45000)
                page.wait_for_function('Array.from(document.fonts).some(f=>f.family.includes("Inter")&&f.status==="loaded") && Array.from(document.fonts).some(f=>f.family.includes("Fraunces")&&f.status==="loaded")',timeout=45000)
                page.wait_for_function('window.SalahMoonRuntime?.state.current && window.realSkyState?.().status === "ready"',timeout=120000)
                # Wait for actual finite CSS transitions, not an elapsed-time
                # assumption. Frozen simulation leaves native timers/rAF intact.
                animations='() => document.getAnimations().map(a=>({state:a.playState,type:a.constructor.name,property:a.transitionProperty||null,timing:a.effect.getComputedTiming().endTime}))'
                result['animationsBeforeSettle']=page.evaluate(animations)
                page.wait_for_function('document.getAnimations().every(a=>a.playState!=="running" || !Number.isFinite(a.effect.getComputedTiming().endTime))',timeout=10000)
                result['animationsAfterSettle']=page.evaluate(animations)
                result['before']=page.evaluate(INSPECT)
                page.screenshot(path=str(out/'full.png'))
                page.evaluate('window.__appearanceFixture.setTextHidden(true)')
                page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                result['hidden']=page.evaluate(INSPECT);page.screenshot(path=str(out/'text-hidden.png'))
                page.evaluate('window.__appearanceFixture.setTextHidden(false)')
                page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                result['restored']=page.evaluate(INSPECT);page.screenshot(path=str(out/'restored.png'))
                page.evaluate('window.__appearanceFixture.setTextHidden(true)')
                page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                result['hidden2']=page.evaluate(INSPECT);page.screenshot(path=str(out/'text-hidden-2.png'))
                page.evaluate('window.__appearanceFixture.setTextHidden(false)')
                page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                result['final']=page.evaluate(INSPECT)
                full=Image.open(out/'full.png').convert('RGB');hidden=Image.open(out/'text-hidden.png').convert('RGB');restored=Image.open(out/'restored.png').convert('RGB');hidden2=Image.open(out/'text-hidden-2.png').convert('RGB')
                tests=[];text_results=[]
                for i,row in enumerate(result['before']['rows']):
                    for k,t in enumerate(row['texts']):
                        r=t['rect'];box=(math.floor(r['x']*args.dpr),math.floor(r['y']*args.dpr),math.ceil((r['x']+r['width'])*args.dpr),math.ceil((r['y']+r['height'])*args.dpr))
                        fg=tuple(map(float,re.findall(r'[\d.]+',t['color'])[:3]));a=full.crop(box);b=hidden.crop(box);a2=restored.crop(box);b2=hidden2.crop(box)
                        for name,im in [('text',a),('background',b),('text-2',a2),('background-2',b2)]:im.save(out/f'{name}-{i}-{k}.png')
                        pixels=lambda im:list(im.get_flattened_data()) if hasattr(im,'get_flattened_data') else list(im.getdata())
                        px=pixels(b);minimum=min(ratio(fg,c) for c in px);minimum2=min(ratio(fg,c) for c in pixels(b2))
                        opacity=math.prod(v['opacity'] for v in t['chain'])
                        changed=[ratio(x,y) for x,y in zip(pixels(a),px) if max(abs(x[c]-y[c]) for c in range(3))>=8]
                        changed2=[ratio(x,y) for x,y in zip(pixels(a2),pixels(b2)) if max(abs(x[c]-y[c]) for c in range(3))>=8]
                        entry={'row':i,'textIndex':k,'text':t['text'],'className':row['className'],'rect':r,'box':box,'foreground':fg,'ancestorOpacity':opacity,'minimumIntendedContrast':min(minimum,minimum2),'pairIntendedContrasts':[minimum,minimum2],'changedPixelCount':len(changed),'secondChangedPixelCount':len(changed2),'maxChangedPixelContrastDiagnostic':max(changed) if changed else None,'secondMaxChangedPixelContrastDiagnostic':max(changed2) if changed2 else None,'visiblePairDifferenceDiagnostic':difference(a,a2),'hiddenPairDifferenceDiagnostic':difference(b,b2)}
                        text_results.append(entry)
                        tests.extend([{'name':f'text-{i}-{k}-opacity1','pass':opacity==1},{'name':f'text-{i}-{k}-intended-contrast','pass':minimum>=4.5 and minimum2>=4.5},{'name':f'text-{i}-{k}-visible-pixels','pass':bool(changed) and bool(changed2)}])
                card=result['before']['card'];box=(round(card['x']*args.dpr),round(card['y']*args.dpr),round((card['x']+card['width'])*args.dpr),round((card['y']+card['height'])*args.dpr))
                full.crop(box).save(out/'card.png');hidden.crop(box).save(out/'card-text-hidden.png');restored.crop(box).save(out/'card-2.png');hidden2.crop(box).save(out/'card-text-hidden-2.png')
                pair_difference=ImageChops.difference(full,hidden);mask=ImageDraw.Draw(pair_difference)
                for t in text_results:
                    x0,y0,x1,y1=t['box'];mask.rectangle((x0,y0,x1-1,y1-1),fill=(0,0,0))
                # Shadows may extend outside glyph rectangles; they are deliberately
                # diagnostics, not intended-colour contrast or a geometry tolerance.
                result['textHiddenOutsideRectDifferenceDiagnostic']=pair_difference.crop(box).getbbox()
                result['wholeRestoredDifferenceDiagnostic']=difference(full,restored)
                result['wholeHiddenDifferenceDiagnostic']=difference(hidden,hidden2)
                states=[result[k] for k in ['before','hidden','restored','hidden2','final']]
                equal=lambda key:all(s[key]==states[0][key] for s in states)
                tests.extend([{'name':'card325x530','pass':card['width']==325 and card['height']==530},{'name':'actual-viewport-dpr','pass':result['before']['viewport']=={'width':args.width,'height':args.height,'dpr':args.dpr}},{'name':'twelve-text-rects','pass':len(text_results)==12},{'name':'same-native-geometry','pass':equal('geometry')},{'name':'same-text-style-font-rectangles','pass':equal('rows') and equal('fonts') and equal('cardClasses')},{'name':'same-clock-native-scene-and-visible-canvas-pixels','pass':equal('scene')},{'name':'native-renderer-valid-through-pairs','pass':all(renderer_valid(s) for s in states)},{'name':'no-blocked-runtime-fetch','pass':all(not s['unexpectedFetch'] for s in states)},{'name':'text-restored','pass':result['final']['textHidden'] is False},{'name':'no-page-errors','pass':not errors}])
                result.update(texts=text_results,checks=tests,status='PASS_SCOPED' if all(t['pass'] for t in tests) else 'FAIL',failures=[t['name'] for t in tests if not t['pass']])
            except Exception as e:
                result.update(status='HARNESS_OR_READINESS_FAILURE',error=str(e))
                try:result['failureState']=page.evaluate(INSPECT);page.screenshot(path=str(out/'failure.png'))
                except Exception as inner:result['failureReadError']=str(inner)
            finally:context.close();browser.close()
    finally:
        server.shutdown();server.server_close();result.update(pageErrors=errors,networkFailures=network,fontReceipts=font_receipts,servedPaths=served,runtimeUnchanged=runtime_identity(source)==identity)
        if 'checks' in result:
            result['checks'].append({'name':'runtime-unchanged','pass':result['runtimeUnchanged']})
            result['failures']=[t['name'] for t in result['checks'] if not t['pass']]
            result['status']='FAIL' if result['failures'] else 'PASS_SCOPED'
        write(out/'results.json',result)
    print(json.dumps({'output':str(out),**{k:result.get(k) for k in ['status','failures','error','pageErrors','networkFailures','runtimeUnchanged']}}),flush=True)
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--workspace',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--stage',choices=['red','green','mutant'],required=True);a.add_argument('--scene',default='noon');a.add_argument('--appearance',default='default',choices=['default','glass','contrast']);a.add_argument('--stress',action='store_true');a.add_argument('--mutant',default='',choices=['','default-past','default-base','default-on']);a.add_argument('--dpr',type=float,default=1);a.add_argument('--width',type=int,default=1100);a.add_argument('--height',type=int,default=900);a.add_argument('--date-case',default='compact',choices=['compact','long','stale']);a.add_argument('--font-fixture',type=Path);a.add_argument('--node',default='node');args=a.parse_args();result=run(args);raise SystemExit(0 if result['status']=='PASS_SCOPED' else 1)
