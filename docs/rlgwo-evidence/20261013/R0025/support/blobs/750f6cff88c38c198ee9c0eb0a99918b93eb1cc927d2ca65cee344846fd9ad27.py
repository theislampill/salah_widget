"""Prepared root-only native runner. It never launches a browser without a digest-bound authorization.

--validate-only performs source/package checks with the standard library only.
The worker does not execute this runner's native path. No builder, provider or terrain is run.
"""
import argparse
import base64
import hashlib
import http.server
import json
from pathlib import Path
import platform
import sys
import threading
import traceback
from urllib.parse import parse_qs,urlencode,urlsplit

BASE=Path(__file__).resolve().parent
# Owned helper modules are loaded by exact file identity. Never add the
# diagnostic worker directory to the SDK/standard-library search path.
import importlib.util
def _fixture_module(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module
_fixture_admission=_fixture_module('_r0025_fixture_admission',BASE/'admission.py')
_fixture_pixels=_fixture_module('_r0025_fixture_pixels',BASE/'pixels.py')
admit_current,asset_response,lease_contract,EXPECTED,CASE=(_fixture_admission.validate,_fixture_admission.asset_response,
    _fixture_admission.lease_contract,_fixture_admission.EXPECTED,_fixture_admission.CASE)
decode_png,measure,composite,difference,png,sha,write_json,WIDTH,HEIGHT=(_fixture_pixels.decode_png,_fixture_pixels.measure,
    _fixture_pixels.composite,_fixture_pixels.difference,_fixture_pixels.png,_fixture_pixels.sha,_fixture_pixels.write_json,
    _fixture_pixels.WIDTH,_fixture_pixels.HEIGHT)

def validate(workspace):
    binding,mutants=admit_current(workspace,BASE)
    seal=json.loads((BASE/'SEAL.json').read_bytes())
    for name,record in seal['files'].items():
        target=(BASE/name).resolve()
        if not target.is_relative_to(BASE) or not target.is_file() or sha(target.read_bytes())!=record['sha256']:
            raise ValueError('sealed current fixture drift: '+name)
    manifest=json.loads((BASE/'SEQUENCE_MANIFEST.json').read_bytes())
    if set(manifest['profiles'])!={'firefox-dpr1'}:
        raise ValueError('only the remaining Firefox DPR1 scope is admitted')
    profile=manifest['profiles']['firefox-dpr1']
    if (profile['engine']!='firefox' or profile['DPR']!=1 or profile['healthyPreview']!=[]
        or profile['healthyWall']!=manifest['originalWall']
        or profile['retainedPreview']['names']!=manifest['originalPreview']
        or profile['healthyDenominator']!=15 or profile['faultDenominator']!=6):
        raise ValueError('retained/new original scope differs')
    # Exact accepted input is required before main() may import the SDK or
    # acquire any browser/server effect; rechecked when used as fault controls.
    retained_preview(profile)
    return binding,mutants,sha((BASE/'SEAL.json').read_bytes())

def authorization(path,binding,seal_hash,workspace,output,engine,dpr):
    value=json.loads(path.read_bytes())
    if value.get('draftOnly'):raise ValueError('draft is not a realized root authorization/lease')
    required={'schema':'r0025-original-sequence-authorization/1','node':'R0025-PIXELS','executor':'root',
        'resourceLease':'EXCLUSIVE_HEAVY_BROWSER','reviewStatus':'APPROVED','fixtureSealSha256':seal_hash,
        'sourceIndexSha256':EXPECTED['generated'],'authoredSha256':EXPECTED['authored'],'runtimeTreeSha256':EXPECTED['runtimeTree'],
        'case':'original-finite-sequence','engine':engine,'DPR':dpr,'noConcurrentBrowserTerrainJobs':True}
    for key,want in required.items():
        if value.get(key)!=want:raise ValueError('root current authorization missing/mismatched '+key)
    if Path(value['workspace']).resolve()!=workspace.resolve() or Path(value['output']).resolve()!=output.resolve():
        raise ValueError('authorized source/output identity mismatch')
    review=Path(value['independentReview']['path']).resolve()
    if sha(review.read_bytes())!=value['independentReview']['sha256']:raise ValueError('new independent review receipt custody mismatch')
    receipt=json.loads(review.read_bytes())
    for key,want in {'status':'APPROVED_R0025_ORIGINAL_SEQUENCE_FINITE_CUSTODY_ONLY','fixtureSealSha256':seal_hash,
                     'driverSha256':sha((BASE/'run-native.py').read_bytes()),'sourceIndexSha256':EXPECTED['generated'],
                     'runtimeTreeSha256':EXPECTED['runtimeTree']}.items():
        if receipt.get(key)!=want:raise ValueError('current review missing/mismatched '+key)
    ledger=json.loads((BASE.parent.parent.parent/'ACTIVE_LEDGER.json').read_bytes())
    lease_contract(ledger,value,output)
    return value

class Server:
    def __init__(self):
        self.ledger=[];parent=self
        allowed=set(json.loads((BASE/'ASSET_RESPONSES.json').read_bytes()))
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                parts=urlsplit(self.path);name=parts.path.lstrip('/')
                if name=='index.html':
                    variant=parse_qs(parts.query).get('variant',['healthy'])[0]
                    permitted={'healthy',*[m['name'] for m in json.loads((BASE/'NATIVE_MUTANTS.json').read_text(encoding='utf-8'))]}
                    if variant not in permitted:self.send_error(404);return
                    text=(BASE/'fixture/index.html').read_text(encoding='utf-8')
                    if variant!='healthy':text=text.replace('src="runtime.js"','src="mutants/'+variant+'.js"',1)
                    text=text.replace('</body>','<script src="operators.js"></script></body>',1)
                    data=text.encode();mime='text/html; charset=utf-8'
                elif name in allowed:
                    data,mime,status=asset_response(name,BASE)
                    if status!=200:self.send_error(status);return
                elif name=='favicon.ico':self.send_response(204);self.end_headers();return
                else:self.send_error(404);return
                parent.ledger.append({'path':self.path,'status':200,'mime':mime,'bytes':len(data),'sha256':sha(data)})
                self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    def __enter__(self):
        self.entryAttempted=True;self.entryReturned=False;self.closed=None
        self.entryCleanupAttempted=False;self.entryCleanupReturned=False
        try:
            threading.Thread(target=self.server.serve_forever,daemon=True).start()
        except BaseException:
            self.entryFailureTraceback=traceback.format_exc();self.entryCleanupAttempted=True
            # __exit__ is not called after failed __enter__. Never shutdown a
            # backend whose serving loop has not returned successful start.
            try:self.server.server_close();self.closed=True;self.entryCleanupReturned=True
            except BaseException:
                self.entryCleanupTraceback=traceback.format_exc();self.closed=None
            raise
        self.origin='http://127.0.0.1:'+str(self.server.server_port);self.entryReturned=True;return self
    def __exit__(self,*args):
        try:self.server.shutdown()
        finally:self.server.server_close();self.closed=True

def artifacts(case,folder,*,source_case,source_record):
    source_path=Path(source_record['path']);source_bytes=source_path.read_bytes()
    if len(source_bytes)!=source_record['bytes'] or sha(source_bytes)!=source_record['sha256']:
        raise ValueError('native capture source association drift')
    source_value=json.loads(source_bytes)
    if 'cases' in source_value:
        choices=[c for c in source_value['cases'] if c.get('name')==case.get('name')]
        if len(choices)!=1:raise ValueError('native case source association missing/duplicate')
        expected_case=choices[0]
    else:expected_case=source_value
    if source_case!=expected_case or case.get('name')!=source_case.get('name') or len(case['captures'])!=len(source_case['captures']):
        raise ValueError('native case/capture source association differs')
    folder.mkdir(parents=True,exist_ok=True);captures=case['captures'];lookup={}
    if len({c['label'] for c in captures})!=len(captures):raise ValueError('duplicate native capture association label')
    for index,capture in enumerate(captures):
        label=capture['label']
        if not isinstance(label,str) or Path(label).name!=label or '/' in label or '\\' in label:
            raise ValueError('unsafe native capture association label')
        if capture!=source_case['captures'][index]:raise ValueError('native raw/PNG/capture source association differs')
        write_json(folder/(label+'.returned-capture.json'),capture)
        rgba=bytes(capture['rgba']);encoded=base64.b64decode(capture['png'].removeprefix('data:image/png;base64,'),validate=True)
        (folder/(label+'.rgba')).write_bytes(rgba);(folder/(label+'.png')).write_bytes(encoded)
        if len(rgba)!=WIDTH*HEIGHT*4:raise ValueError('actual native RGBA size')
        w,h,decoded=decode_png(encoded)
        if (w,h)!=(WIDTH,HEIGHT):raise ValueError('native PNG dimensions differ from source canvas')
        # Both actual APIs are preserved. Cross-API encoding equality is not an
        # original raw-pixel oracle; never normalize/substitute native PNG here.
        capture['nativePngReadbackDifference']=measure(rgba,decoded)
        capture['nativeCaptureAssociation']={'sourceRecord':source_record,'case':case.get('name'),'captureIndex':index,
            'label':label,'nativePngSha256':sha(encoded),'getImageDataSha256':sha(rgba),
            'scope':'Same immutable source-produced synchronous capture; raw native comparisons remain exact within getImageData.'}
        capture.pop('rgba');capture.pop('png')
        (folder/(label+'.composite.png')).write_bytes(png(WIDTH,HEIGHT,composite(rgba,[34,64,96])))
        capture['rawRGBA']={'path':str(folder/(label+'.rgba')),'bytes':len(rgba),'sha256':sha(rgba),'width':WIDTH,'height':HEIGHT,'format':'unpremultiplied-u8-RGBA; visible-color oracle independently premultiplies'}
        capture['crop']={'path':str(folder/(label+'.png')),'sha256':sha(encoded),'scope':'actual native 144x232 cloud canvas, no CSS blur/whole-sky qualification'}
        capture['composite']={'path':str(folder/(label+'.composite.png')),'fixedBackgroundRGB':[34,64,96],'scope':'same recorded diagnostic background for every cloud foreground'}
        lookup[label]=rgba
    comparisons={}
    if len(captures)>=2:
        for a,b in zip(captures,captures[1:]):
            name=a['label']+'--'+b['label'];comparisons[name]=measure(lookup[a['label']],lookup[b['label']])
            diff=folder/(name+'.DIFFERENCE_GAIN4.png');diff.write_bytes(png(WIDTH,HEIGHT,difference(lookup[a['label']],lookup[b['label']])))
            comparisons[name]['amplifiedDifference']={'path':str(diff),'gain':4,'label':'AMPLIFIED ABSOLUTE PREMULTIPLIED RGB DIFFERENCE; NOT A PRODUCT IMAGE'}
    case['independentRGBAComparisons']=comparisons;return lookup

def native_effect_summary(state,attempts):
    returned=any(a.get('sceneAdmissionReturned') or a.get('operatorsReturned') for a in attempts)
    attempted=any(a.get('sceneAdmissionAttempted') or a.get('operatorsAttempted') for a in attempts)
    return {'nativeExecuted':True if returned else None if attempted else False,
        'nativeAttempted':attempted,'effectState':state,'caseAttempts':attempts,
        'nativeOperatorCallsReturned':sum(bool(a.get('operatorsReturned')) for a in attempts)}

def execute_case(browser,server,name,mode,folder,binding,variant='healthy',real_elapsed=False,dpr=1,attempts=None,selection=None,viewport=None,cost_config=None,scene_only=False):
    folder.mkdir(parents=True,exist_ok=True)
    attempt={'case':name,'variant':variant,'mode':mode,'source':binding['expected'],
        'contextAttempted':False,'contextReturned':False,'sceneNavigationAttempted':False,
        'sceneAdmissionAttempted':False,'sceneAdmissionReturned':False,'operatorsAttempted':False,
        'operatorsReturned':False,'contextCloseAttempted':False,'contextCloseReturned':False,
        'nativeExecuted':False,'status':'ATTEMPT_RECORDED'}
    if attempts is not None:attempts.append(attempt)
    def record():write_json(folder/'attempt.json',attempt)
    context=None;page=None;errors=[];blocked=[];requests=[];record()
    try:
        attempt['contextAttempted']=True;record()
        context=browser.new_context(viewport=viewport or {'width':394,'height':614},device_scale_factor=dpr,reduced_motion='no-preference',timezone_id='Asia/Riyadh')
        attempt['contextReturned']=True;record()
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
        def route(route):
            if route.request.url.startswith(server.origin+'/'):route.continue_()
            else:blocked.append(route.request.url);route.abort()
        page.route('**/*',route)
        params={'lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','label':'Madinah','method':4,'units':'c','seed':1,'simWx':2,
            'simMoon':.08,'simWax':1,'simMoonAlt':20,'simMoonH':42,'simTemp':24,'simWind':3,'simHumid':55,'motion':'full'}
        if mode=='preview':params.update({'simTime':'18:10','timeScale':1})
        url=server.origin+'/index.html?variant='+variant+'#'+urlencode(params)
        attempt.update({'url':url,'sceneNavigationAttempted':True});record()
        page.goto(url,wait_until='domcontentloaded');page.wait_for_function('typeof window.__r0025Run==="function"',polling=100,timeout=30000)
        attempt.update({'sceneAdmissionAttempted':True,'nativeExecuted':None});record()
        admission=page.evaluate('async()=>{await document.fonts.ready;return await __r0025.init();}')
        attempt.update({'sceneAdmissionReturned':True,'nativeExecuted':True,'admittedFiniteScene':admission});record()
        page.evaluate('async()=>{await new Promise(r=>__r0025Boundary.nativeRAF(()=>__r0025Boundary.nativeRAF(r)));}')
        card=page.evaluate('()=>{const r=document.querySelector(".c").getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}')
        page.screenshot(path=str(folder/'admitted-card-context.png'),clip=card)
        if scene_only:
            if selection is not None or cost_config is None or name!='cost-scene-only':
                raise ValueError('only the admitted non-measuring G scene may omit original callbacks')
            report=None;rasters={}
            attempt['status']='ADMITTED_NON_MEASURING_G_SCENE';record()
        else:
            attempt['operatorsAttempted']=True;record()
            report=page.evaluate('async options=>await __r0025Run(options)',{'mode':mode,'nativePixels':True,'realElapsed':real_elapsed,'only':selection if selection is not None else CASE,'stopOnFailure':True})
            attempt.update({'operatorsReturned':True,'operatorTerminals':report.get('executed'),'status':'OPERATORS_RETURNED'});record()
            write_json(folder/'returned-operators.json',report)
            source_raw=(folder/'returned-operators.json').read_bytes()
            source_record={'path':str(folder/'returned-operators.json'),'bytes':len(source_raw),'sha256':sha(source_raw)}
            source_cases=json.loads(source_raw)['cases'];rasters={}
            for index,case in enumerate(report['cases']):
                rasters[case['name']]=artifacts(case,folder/case['name'],source_case=source_cases[index],source_record=source_record)
        environment=page.evaluate('()=>({userAgent:navigator.userAgent,DPR:devicePixelRatio,viewport:{width:innerWidth,height:innerHeight},fonts:{status:document.fonts.status,interCheck:document.fonts.check("400 14px Inter"),frauncesCheck:document.fonts.check("600 24px Fraunces")},prohibited:__r0025Boundary.prohibited,syntheticRequests:__r0025Boundary.requests,scheduler:{heldIntervals:__r0025Boundary.intervals.size,queuedRAF:__r0025Boundary.rafs.size}})')
        css=binding['structuralStylesheets']
        deliveries=[x for x in server.ledger if urlsplit(x['path']).path.lstrip('/') in css]
        environment['structuralCSSDeliveries']=deliveries
        environment['cardRect']=card
        if card['width']!=325 or card['height']!=530:raise ValueError('current structural card CSS consumer is not 325x530')
        for rel in css:
            expected=json.loads((BASE/'ASSET_RESPONSES.json').read_bytes())[rel]
            if not any(urlsplit(x['path']).path.lstrip('/')==rel and x['status']==200 and x['mime']=='text/css; charset=utf-8' and x['sha256']==expected['sha256'] for x in deliveries):
                raise ValueError('structural CSS transport missing/503/wrong MIME/bytes: '+rel)
        if errors or environment['prohibited']:raise ValueError('native bootstrap/prohibited execution: '+json.dumps({'errors':errors,'prohibited':environment['prohibited']}))
        if any(x['kind']=='blocked' for x in environment['syntheticRequests']):raise ValueError('unexpected product fetch was attempted')
        value={'name':name,'variant':variant,'mode':mode,'url':url,'source':binding['expected'],'engine':environment,
            'admittedFiniteScene':admission,'actualNativeOperators':report,'pageErrors':errors,'blockedExternalAssets':blocked,
            'allBrowserRequests':requests,'cardContext':{'path':str(folder/'admitted-card-context.png'),'scope':'initial admitted detached source fixture; not per-operator whole-card equality'},
            'nativeAttempted':True,'nativeExecuted':True,
            'limits':'External fonts blocked; readiness/check booleans are recorded, no exact font/UI claim. Main product boot held, unrelated Moon lifecycle disposed and terrain/worker blocked. Native raw cloud consumer only.'}
        # A separate scene collector must not run after an unsatisfied original terminal.
        chosen=selection if isinstance(selection,list) else [selection if selection is not None else CASE]
        healthy_return=(report is not None and report.get('failed')==0 and report.get('declared')==len(chosen)
            and report.get('executed')==len(chosen) and [c.get('name') for c in report['cases']]==chosen
            and all(c.get('status')=='PASS' and c.get('reached') is True and c.get('terminal') is True for c in report['cases']))
        if cost_config is not None and (healthy_return or scene_only):
            page.add_script_tag(content=(BASE/'fixture/cost_boundary.js').read_text(encoding='utf-8'))
            cost=page.evaluate(COST_SCENE_JS,cost_config)
            write_json(folder/'cost-scene-returned.json',cost)
            cost_raw=(folder/'cost-scene-returned.json').read_bytes()
            cost_record={'path':str(folder/'cost-scene-returned.json'),'bytes':len(cost_raw),'sha256':sha(cost_raw)}
            cost_case={'captures':cost['captures']};cost_source=json.loads(cost_raw)
            cost_rasters=artifacts(cost_case,folder/'cost-scene',source_case=cost_source,source_record=cost_record)
            metric=measure(cost_rasters['actual-current-consumer'],cost_rasters['selected-current-painter'])
            cost['captures']=cost_case['captures'];cost['nativeRGBAComparison']=metric
            cost['selectedFixtureParity']=metric['changedVisiblePixels']==0 and metric['maxAlphaDelta']==0
            write_json(folder/'cost-scene.json',cost);value['costScene']=cost;attempt['costSceneReturned']=True
        write_json(folder/'results.json',value);attempt['status']='CASE_RETURNED';return value,rasters
    except BaseException:
        attempt.update({'status':'INCOMPLETE','traceback':traceback.format_exc()})
        diagnostic={'status':'NO_PAGE_RETURNED','data':None}
        if page is not None:
            try:
                data=page.evaluate('()=>window.__r0025?.admissionDiagnostic?.()??null')
                diagnostic={'status':'DIRECT_DIAGNOSTIC_RETURNED' if data is not None else 'DIAGNOSTIC_NOT_INSTALLED','data':data}
            except BaseException:
                diagnostic={'status':'DIAGNOSTIC_READBACK_FAILED','data':None,'traceback':traceback.format_exc()}
        write_json(folder/'admission-diagnostic.json',diagnostic)
        attempt['admissionDiagnostic']={'path':str(folder/'admission-diagnostic.json'),'status':diagnostic['status']}
        raise
    finally:
        try:
            if context is not None:
                attempt['contextCloseAttempted']=True
                try:context.close();attempt['contextCloseReturned']=True
                except BaseException:
                    attempt['cleanupTraceback']=traceback.format_exc()
                    if attempt['status']!='INCOMPLETE':attempt['status']='CLEANUP_FAILED';raise
                finally:record()
            else:record()
        finally:
            write_json(folder/'browser-events.json',{'pageErrors':errors,'blockedExternalAssets':blocked,'allBrowserRequests':requests,
                'scope':'retained through finally, including failed admission and attempted context cleanup; not operator completion'})


def detect_pixel_mutant(m,healthy,mutated):
    name=m['expectedOperator'];a=healthy[name];b=mutated[name]
    if m['name']=='phase-times-epoch':metric=measure(b['before'],b['after']);caught=metric['changedVisiblePixels']>0
    elif m['name']=='ordinary-daily-reseed':metric=measure(b['boundary-after'],b['ordinary-after']);caught=metric['changedVisiblePixels']>0
    elif m['name']=='frozen-visual-interval':metric=measure(b['before'],b['after-30s']);caught=metric['changedVisiblePixels']==0 and measure(a['before'],a['after-30s'])['changedOver5']>0
    elif m['name']=='missing-periodic-wings':
        metric=measure(b['before-wrap'],b['after-wrap']);control=measure(a['before-wrap'],a['after-wrap']);caught=metric['meanAbsolutePremultipliedRGB']>control['meanAbsolutePremultipliedRGB']+1e-12;metric['healthyMatchedEdgeDelta']=control
    elif m['name']=='new-wind-before-elapsed':metric=measure(a['independent-old-velocity-reference'],b['after-admission']);caught=metric['changedVisiblePixels']>0
    else:metric=measure(b['returned-populated'],b['never-empty-reference']);caught=metric['changedVisiblePixels']>0
    return {'caught':caught,'oracle':'independent actual native RGBA compared with same-time/ordinary/healthy matched control','metrics':metric}

COST_SCENE_JS=r"""config=>{
 const f=window.__r0025,b=window.__r0025Boundary;
 const inventory=()=>({requests:JSON.parse(JSON.stringify(b.requests)),queuedRAF:b.rafs.size,heldIntervals:b.intervals.size,
  listenerRegistrations:JSON.parse(JSON.stringify(b.listenerInventory)),scope:'actual whole classic source in disposable held-clock/scheduler consumer; no default live-widget inventory claim'});
 const before=inventory(),actual=f.costScene(config.scene);
 const cv=document.createElement('canvas');cv.width=144;cv.height=232;
 const selected=R0025CostBoundary.setup(cv,config,b.nativeNow);
 const control=selected.control('after'),rgba=Array.from(cv.getContext('2d').getImageData(0,0,144,232).data);
 const after=inventory(),snapshot=f.snapshot();
 return {schema:'r0025-native-cost-scene-parity/1',protocol:config.protocol,collector:config.collector,
  scene:config.scene,actualInput:snapshot.cloudState,selectedState:control.after,selectedStateCheck:control.check,
  selectedRetentionEqual:control.retentionEqual,inventoryBefore:before,inventoryAfter:after,
  clock:snapshot.clock,axes:snapshot.axes,columns:snapshot.columns,measurementExecuted:false,
  captures:[{label:'actual-current-consumer',rgba:actual.rgba,png:actual.png},
   {label:'selected-current-painter',rgba,png:cv.toDataURL('image/png')}],
  limits:'No durations/budget acceptance. Same finite declared G scene on actual whole-source painter and guarded selected painter; producer inventory scope and accepted source/lifecycle evidence must be independently reconciled.'};
}"""

def retained_preview(profile):
    retained=profile.get('retainedPreview')
    if retained is None:return {},[]
    decision=json.loads(captured_input(retained['decision']))
    if (decision.get('schema')!='independent-r0025-original-profile-prefix-case-decisions/1'
        or decision.get('status')!='PASS_EIGHT_RETAINED_ORIGINAL_FIREFOX_DPR1_PREVIEW_CASES_NO_REPLAY'
        or decision.get('reviewer')!='/root/r0024_consumer_admission_20261013'
        or decision.get('profile')!='firefox-dpr1' or decision.get('actualNativeSourceDTO')!=retained['sourceDTO']
        or decision.get('source')!={**EXPECTED,'config':'91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81'}):
        raise ValueError('actual accepted native preview prefix/source association missing')
    names=[c['name'] for c in decision['originalCases']]
    if names!=retained['names'] or len(names)!=8 or not all(c['status']=='PASS_ORIGINAL_NATIVE_PREVIEW_CASE_FROM_RETAINED_ACTUAL' for c in decision['originalCases']):
        raise ValueError('accepted original prefix denominator differs')
    dto=json.loads(captured_input(retained['sourceDTO']))
    if [c['name'] for c in dto['cases']]!=names or dto['failed']!=0 or dto['executed']!=8:
        raise ValueError('retained native prefix source return differs')
    raw={}
    for case in dto['cases']:
        if case['status']!='PASS' or case['reached'] is not True or case['terminal'] is not True:
            raise ValueError('retained native original was not reached')
        raw[case['name']]={c['label']:bytes(c['rgba']) for c in case['captures']}
        if any(len(v)!=WIDTH*HEIGHT*4 for v in raw[case['name']].values()):raise ValueError('retained native RGBA size')
    return raw,names

def captured_input(record):
    p=Path(record['path']);raw=p.read_bytes()
    if len(raw)!=record['bytes'] or sha(raw)!=record['sha256']:raise ValueError('retained input drift')
    return raw

def run_original_sequence(browser,server,binding,mutants,output,engine,dpr,results,detections,attempts):
    manifest=json.loads((BASE/'SEQUENCE_MANIFEST.json').read_bytes());profile=manifest['profiles'][engine+'-dpr'+str(dpr)]
    healthy,healthy_names=retained_preview(profile)
    config=json.loads((BASE/'COST_SCENE_CONFIG.json').read_bytes())
    if profile.get('retainedPreview'):
        value,_=execute_case(browser,server,'cost-scene-only','preview',output/'cost-scene-only',binding,
            dpr=dpr,attempts=attempts,viewport=profile['previewViewport'],cost_config=config,scene_only=True)
        results.append(value)
    for mode,names in [('preview',profile['healthyPreview']),('wall',profile['healthyWall'])]:
        if not names:continue
        value,raw=execute_case(browser,server,'healthy-'+mode,mode,output/('healthy-'+mode),binding,
            real_elapsed=mode=='wall',dpr=dpr,attempts=attempts,selection=names,
            viewport=profile[mode+'Viewport'],cost_config=config if mode=='preview' else None)
        results.append(value);terminal=value['actualNativeOperators'];healthy.update(raw)
        if terminal['failed'] or terminal['declared']!=len(names) or terminal['executed']!=len(names) or [c['name'] for c in terminal['cases']]!=names:
            raise ValueError('original healthy sequence failure; retained partial DTO and no further case/fault execution')
        if not all(c['status']=='PASS' and c['reached'] is True and c['terminal'] is True for c in terminal['cases']):
            raise ValueError('unreached original healthy case')
        healthy_names.extend(names)
    for m in mutants:
        names=[m['expectedOperator']];name='mutant-'+m['name']
        value,raw=execute_case(browser,server,name,m['mode'],output/name,binding,variant=m['name'],
            real_elapsed=m['expectedOperator']=='positive-elapsed-30s',dpr=dpr,attempts=attempts,
            selection=names,viewport=profile[m['mode']+'Viewport'])
        results.append(value);terminal=value['actualNativeOperators']
        if terminal['declared']!=1 or terminal['executed']!=1 or terminal['cases'][0]['name']!=names[0] or terminal['cases'][0]['reached'] is not True:
            raise ValueError('native fault did not reach named original oracle; bootstrap is not mutation detection')
        detection=detect_pixel_mutant(m,healthy,raw);detection.update(name=m['name'],operator=names[0],classicScriptSha256=m['classicScriptSha256'],sourceStateStatus=terminal['cases'][0]['status'])
        detections.append(detection);write_json(output/(name+'-detection.json'),detection)
        if detection['caught'] is not True:raise ValueError('required original native fault was not caught; stop without retry or widened gate')
    return healthy_names,profile

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--engine',choices=['chromium','firefox'],default='chromium')
    parser.add_argument('--output',type=Path);parser.add_argument('--authorization',type=Path);parser.add_argument('--executable',type=Path);parser.add_argument('--dpr',type=float,default=1);parser.add_argument('--validate-only',action='store_true');parser.add_argument('--case',choices=['original-finite-sequence'])
    args=parser.parse_args();binding,mutants,seal_hash=validate(args.workspace)
    if args.validate_only:print(json.dumps({'validated':True,'sourceIndexSha256':binding['expected']['generated'],'fixtureSealSha256':seal_hash,'nativeExecuted':False}));return
    if not args.authorization or not args.output:raise ValueError('root authorization and fresh output directory required')
    if args.case!='original-finite-sequence' or args.dpr not in (1,2):raise ValueError('exact original finite engine/DPR sequence required')
    args.dpr=int(args.dpr)
    output=args.output.resolve()
    auth=authorization(args.authorization,binding,seal_hash,args.workspace,output,args.engine,args.dpr)
    if output.exists():raise ValueError('fresh output directory required; no overwrite or ambiguous native retry')
    output.mkdir(parents=True);write_json(output/'authorization-used.json',auth)
    state={'sdkImportAttempted':False,'sdkImported':False,'serverAttempted':False,'serverEntered':False,
        'serverConstructed':False,'serverClosed':None,'browserLaunchAttempted':False,'browserLaunchReturned':False,'browserLaunched':False,'browserCloseAttempted':False,'browserClosed':None}
    results=[];detections=[];attempts=[];browser=None;server=None
    try:
        state['sdkImportAttempted']=True;write_json(output/'effect-state.json',state)
        from playwright.sync_api import sync_playwright
        state['sdkImported']=True;state['serverAttempted']=True;write_json(output/'effect-state.json',state)
        server=Server();state['serverConstructed']=True;write_json(output/'effect-state.json',state)
        with server:
            state['serverEntered']=True;write_json(output/'effect-state.json',state)
            with sync_playwright() as p:
                options={'headless':True}
                if args.executable:
                    if not args.executable.is_file():raise FileNotFoundError('explicit browser executable missing')
                    options['executable_path']=str(args.executable.resolve())
                if args.engine=='chromium':options['chromium_sandbox']=True
                state['browserLaunchAttempted']=True;state['browserLaunched']=None;write_json(output/'effect-state.json',state)
                try:
                    browser=getattr(p,args.engine).launch(**options);state['browserLaunched']=True;state['browserLaunchReturned']=True
                    identity={'family':args.engine,'version':browser.version,'OS':platform.platform(),'executable':str(args.executable) if args.executable else 'installed Playwright engine; no installation attempted'}
                    healthy_names,profile=run_original_sequence(browser,server,binding,mutants,output,args.engine,args.dpr,results,detections,attempts)

                finally:
                    if browser is not None:
                        state['browserCloseAttempted']=True
                        try:browser.close();state['browserClosed']=True
                        except BaseException:
                            state['browserCleanupTraceback']=traceback.format_exc()
        state['serverClosed']=getattr(server,'closed',None)
        if state.get('browserCleanupTraceback'):raise ValueError('browser cleanup failed; preserve outputs')
        value={'schema':'r0025-native-original-sequence/v1','source':binding['expected'],'fixtureSealSha256':seal_hash,'engine':identity,
            'DPR':args.dpr,'namedOperators':len(healthy_names),'healthyPassed':len(healthy_names),'healthyNames':healthy_names,
            'retainedHealthy':len(profile['retainedPreview']['names']),
            'healthyNewlyExecuted':len(profile['healthyPreview']+profile['healthyWall']),
            'retainedPreview':profile['retainedPreview'],
            'originalDenominatorPerProfile':15,'retainedAcceptedParity':json.loads((BASE/'SEQUENCE_MANIFEST.json').read_bytes())['acceptedCase'] if args.engine=='chromium' and args.dpr==1 else None,
            'nativeMutantsUnrun':0,'reachedNativeMutants':detections,**native_effect_summary(state,attempts),'runs':results,
            'status':'ORIGINAL_FINITE_SEQUENCE_RETURNED_AWAITING_INDEPENDENT_RAW_REVIEW','nodeCompletion':False,
            'limits':'This exact engine/DPR only; cost-scene parity is not COST measurement/acceptance, full physical sky/default motion/public/closure claim.'}
        write_json(output/'results.json',value);print(json.dumps({'status':value['status'],'operators':len(healthy_names),'nativeMutants':len(detections),'results':str(output/'results.json'),'nodeCompletion':False}))

    except BaseException:
        state['serverClosed']=getattr(server,'closed',None) if server is not None else None
        if server is not None:
            state['serverEntryAttempted']=getattr(server,'entryAttempted',None)
            state['serverEntryReturned']=getattr(server,'entryReturned',None)
            state['serverEntryCleanupAttempted']=getattr(server,'entryCleanupAttempted',None)
            state['serverEntryCleanupReturned']=getattr(server,'entryCleanupReturned',None)
            state['serverEntryCleanupTraceback']=getattr(server,'entryCleanupTraceback',None)
        write_json(output/'INCOMPLETE.json',{'status':'INCOMPLETE','traceback':traceback.format_exc(),'nativeRunsReturned':len(results),**native_effect_summary(state,attempts),'nodeCompletion':False})
        raise
    finally:
        if server is not None:write_json(output/'request-ledger.json',server.ledger)
        write_json(output/'effect-state.json',state)

if __name__=='__main__':main()
