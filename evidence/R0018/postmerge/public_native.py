"""Real public documents in disposable headless contexts. No desktop APIs."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, subprocess, sys, textwrap, urllib.parse
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from delivery_control import CORE,PROD,PUBLIC,HEAD,BASE,read,sha,now,runtime_identity
sys.path.insert(0,str(PROD/'tools/cp9'))
from browser_runtime import launch_browser,browser_identity
from playwright.sync_api import sync_playwright

NODE='C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe'
ENGINES={'chromium':'C:/Users/theis/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe',
         'firefox':'C:/Users/theis/AppData/Local/ms-playwright/firefox-1522/firefox/firefox.exe'}

def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')

def main(args):
    out=HERE/'native'/args.name;out.mkdir(parents=True,exist_ok=False)
    runtime=runtime_identity(PROD); candidate=read('candidate-identity.json')
    assert runtime['treeSha256']==candidate['runtimeSha256']
    delivery=json.loads((HERE/'merged-pages-readback.json').read_bytes());assert delivery['passed']
    driver=PROD/'tests/r0018-default-readability.py';data=driver.read_bytes()
    assert sha(data)=='503bc293263c304def159b4b6521dc3d8f039dea677d177a8ff39c66d4e99668'
    # Reuse the exact existing native capture/oracle block, without the local
    # fixture server or its modified document delivery. Preserve the extraction.
    text=data.decode('utf-8');begin="                result['before']=page.evaluate(INSPECT)";end='                if args.geometry_baseline:'
    assert text.count(begin)==1 and text.count(end)==1
    block=text[text.index(begin):text.index(end)]
    capture='def capture(page,args,out,result,errors):\n'+textwrap.indent(textwrap.dedent(block),'    ')
    spec=importlib.util.spec_from_file_location('r0018_accepted_native',driver);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    scope=dict(vars(native));exec(compile(capture,'accepted-capture.py','exec'),scope)
    (out/'accepted-capture.py').write_text(capture,encoding='utf-8',newline='\n')
    request={'assetPaths':['/salah_widget/'+p for p in runtime['files']]};write(out/'fixture-input.json',request)
    fixture=json.loads(subprocess.check_output([NODE,str(HERE/'prepare_public.cjs'),str(out/'fixture-input.json')]))
    assert fixture['sourceSha256']==candidate['rootSha256'] and fixture['reconstructedProductExact']
    write(out/'fixture.json',fixture)
    os.environ['SALAH_BROWSER']=args.engine;os.environ['SALAH_BROWSER_EXECUTABLE']=ENGINES[args.engine]
    errors=[];network=[];responses=[];font_receipts=[];cleanup={'contextClosed':False,'browserClosed':False}
    result={'schema':'r0018-public-native-readability/v1','startedUtc':now(),'case':args.name,'sourceHead':HEAD,
            'mergeCommit':delivery['merge']['mergeCommit'],'runtimeSha256':runtime['treeSha256'],
            'driverSha256':sha(Path(__file__).read_bytes()),'prepareSha256':sha((HERE/'prepare_public.cjs').read_bytes()),
            'acceptedCollectorSha256':sha(data),'acceptedCaptureSha256':sha(capture.encode()),
            'fixtureSha256':sha((out/'fixture.json').read_bytes()),'fixture':{'spec':fixture['spec'],'hash':fixture['hash']},
            'stress':args.stress,'sourceDelivery':'Real public document and public static assets; no document interception, local server, rebuilt HTML, render replacement or canvas substitution.',
            'fixtureScope':'Original preboot fixed Date/private empty Map/prayer-layout transport; exact previously pinned declared font bodies. Optional contrast is not selected. Local white backing is confined to .times in the disposable stress context. Frozen stills; no motion claim.'}
    try:
        with sync_playwright() as p:
            browser=launch_browser(p);result['browser']=browser_identity(browser);result['browser']['executableSha256']=sha(Path(ENGINES[args.engine]).read_bytes())
            context=browser.new_context(viewport={'width':args.width,'height':args.height},device_scale_factor=args.dpr,reduced_motion='reduce',timezone_id='Asia/Riyadh',locale='en-US',service_workers='block')
            try:
                font_manifest=read('fonts/manifest.json');fonts={f['url']:f for f in font_manifest['files']}
                def font(route):
                    item=fonts[route.request.url];body=(CORE/'fonts'/item['sha256']).read_bytes()
                    assert sha(body)==item['sha256'] and len(body)==item['bytes']
                    font_receipts.append(item);route.fulfill(status=item['status'],content_type=item['contentType'],body=body)
                context.route(re.compile(r'https://fonts\.(googleapis|gstatic)\.com/.*'),font)
                context.add_init_script(script=fixture['pre'])
                page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('requestfailed',lambda r:network.append({'url':r.url,'failure':r.failure}))
                page.on('response',lambda r:responses.append({'url':r.url,'status':r.status,'resourceType':r.request.resource_type}))
                response=page.goto(PUBLIC+'index.html'+fixture['hash'],wait_until='domcontentloaded',timeout=60000)
                document=response.body();result['document']={'url':response.url,'status':response.status,'bytes':len(document),'sha256':sha(document)}
                assert response.status==200 and sha(document)==candidate['rootSha256'],'Actual served document differs'
                page.add_script_tag(content=fixture['inspect'])
                page.wait_for_function('window.__appearanceFixture.snapshot().ready && document.fonts.status === "loaded"',timeout=45000)
                page.wait_for_function('Array.from(document.fonts).some(f=>f.family.includes("Inter")&&f.status==="loaded") && Array.from(document.fonts).some(f=>f.family.includes("Fraunces")&&f.status==="loaded")',timeout=45000)
                page.wait_for_function('window.SalahMoonRuntime?.state.current && window.realSkyState?.().status === "ready"',timeout=120000)
                if args.stress:page.add_style_tag(content='.times{background:#fff}')
                page.wait_for_function('document.getAnimations().every(a=>a.playState!=="running" || !Number.isFinite(a.effect.getComputedTiming().endTime))',timeout=10000)
                scope['capture'](page,args,out,result,errors)
                public_responses=[r for r in responses if r['url'].startswith(PUBLIC)]
                allowed={'/salah_widget/'+p for p in runtime['files']}
                result['checks'].extend([
                    {'name':'actual-public-document-identity','pass':result['document']['sha256']==candidate['rootSha256']},
                    {'name':'default-appearance-not-forced-contrast','pass':result['before']['configAppearance']!='contrast' and result['before']['cardAppearance']!='contrast' and 'appearance=' not in fixture['hash']},
                    {'name':'public-runtime-http-status','pass':all(r['status']==200 and urllib.parse.urlparse(r['url']).path in allowed for r in public_responses)},
                    {'name':'no-network-failures','pass':not network}])
                prior=CORE/'matrix'/('green-'+args.engine+'-noon-'+('constrained-dpr2-compact-default-white' if args.stress else 'desktop-dpr1-compact-default'))/'results.json'
                old=json.loads(prior.read_bytes());differences=[]
                for selector,value in result['before']['geometry'].items():
                    if value!=old['before']['geometry'].get(selector):differences.append({'selector':selector,'qualified':old['before']['geometry'].get(selector),'delivered':value})
                row_diffs=[]
                for i,(actual,qualified) in enumerate(zip(result['before']['rows'],old['before']['rows'])):
                    for field in ('text','className','rect','boxStyle','texts'):
                        if actual.get(field)!=qualified.get(field):row_diffs.append({'row':i,'field':field,'qualified':qualified.get(field),'delivered':actual.get(field)})
                result['comparisonToQualified']={'receiptSha256':sha(prior.read_bytes()),'geometryDifferences':differences,'rowDifferences':row_diffs,
                    'disposition':'EXACT' if not differences and not row_diffs else 'INDEPENDENT_RECONCILIATION_REQUIRED; no tolerance or field exclusion'}
                result['checks'].append({'name':'qualified-timetable-rows-fonts-strings-exact','pass':not row_diffs})
            except Exception as exc:
                result.update(status='HARNESS_OR_READINESS_FAILURE',error=repr(exc))
                try:result['failureState']=page.evaluate(native.INSPECT);page.screenshot(path=str(out/'failure.png'))
                except Exception as inner:result['failureCaptureError']=repr(inner)
            finally:
                context.close();cleanup['contextClosed']=True
                browser.close();cleanup['browserClosed']=True
    finally:
        result.update(finishedUtc=now(),pageErrors=errors,networkFailures=network,responses=responses,fontReceipts=font_receipts,
                      runtimeUnchanged=runtime_identity(PROD)==runtime,cleanup=cleanup)
        if 'checks' in result and result.get('status')!='HARNESS_OR_READINESS_FAILURE':
            result['checks'].append({'name':'source-runtime-unchanged','pass':result['runtimeUnchanged']})
            result['failures']=[c['name'] for c in result['checks'] if not c['pass']];result['status']='FAIL' if result['failures'] else 'PASS_SCOPED'
        write(out/'results.json',result)
    print(json.dumps({'case':args.name,'status':result.get('status'),'failures':result.get('failures'),'error':result.get('error'),'networkFailures':network,'geometry':result.get('comparisonToQualified',{}).get('disposition')}),flush=True)
    return 0 if result.get('status')=='PASS_SCOPED' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=list(ENGINES),required=True);parser.add_argument('--name',required=True)
    parser.add_argument('--stress',action='store_true');parser.add_argument('--width',type=int,default=1100);parser.add_argument('--height',type=int,default=900);parser.add_argument('--dpr',type=float,default=1)
    raise SystemExit(main(parser.parse_args()))
