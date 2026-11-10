"""Root-only bounded R0024 actual consumer runner. Preparation does not launch this entry.

All bound candidate runtime files are served unchanged. Provider/clock/storage inputs
and the separate forecast dependency are disclosed. One serial admitted run per engine.
The output never claims pixel, native-node, delivery, provider, or R0018 qualification.
"""
import argparse,ast,hashlib,importlib.util,json,math,os,platform,re,struct,sys,time,traceback,zlib
from pathlib import Path
from urllib.parse import unquote,urlsplit

PROPOSED=Path(__file__).resolve().parents[2]
ASSETS=PROPOSED/'tests/weather-native'
BINDING=None
def sha(b):return hashlib.sha256(b).hexdigest()
def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write_json(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def require(ok,msg):
    if not ok:raise ValueError(msg)
def cases():return read_json(ASSETS/'cases.json')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def input_manifest(root):
    root=Path(root).resolve()
    runtime=load('r24_runtime_identity',root/'tools/cp9/runtime_identity.py').runtime_identity(root)
    paths=[root/'src/native/index.html',root/'tools/build_native.py',root/'tools/build_moon.py',root/'tools/cp9/browser_runtime.py',root/'tools/cp9/runtime_identity.py',root/'tests/weather-forecast-fixture.js']
    paths+=sorted(p for p in ASSETS.rglob('*')if p.is_file())
    paths+=sorted((PROPOSED/'tools/qa').glob('*.py'))
    fixtures={p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in paths}
    return {'schema':'r0024-current-native-input/v1','candidate':str(root),'runtime':runtime,'fixtures':fixtures,'entrySha256':sha((root/'index.html').read_bytes())}

def source_preflight(root):
    actual=input_manifest(root);expected=read_json(BINDING)
    require(actual==expected,'Current runtime or fixture identity changed')
    return {'status':'SOURCE_PREFLIGHT_ONLY','runtimeSha256':actual['runtime']['treeSha256'],'runtimeFiles':len(actual['runtime']['files']),'fixtureFiles':len(actual['fixtures']),'candidate':str(root),'bindingSha256':sha(BINDING.read_bytes()),'native':'NOT_RUN'}

def lease_preflight(args):
    require(sha(BINDING.read_bytes())==args.admission_sha,'Input manifest digest changed')
    pref=source_preflight(args.root)
    require(platform.system()=='Windows'and platform.machine()in ['AMD64','x86_64'],'Windows x64 required')
    require(args.executable.is_file(),'Explicit installed executable required')
    import importlib.metadata
    cap={'os':platform.system(),'machine':platform.machine(),'engine':args.browser,'playwrightVersion':importlib.metadata.version('playwright'),'executable':str(args.executable.resolve()),'executableSha256':sha(args.executable.read_bytes()),'headless':True,'chromiumSandbox':args.browser=='chromium','installedByThisTask':False}
    if args.driver_cli or args.driver_node:
        require(args.driver_cli and args.driver_node and args.driver_cli.is_file() and args.driver_node.is_file(),'Both existing driver CLI and Node executable required')
        package=read_json(args.driver_cli.parent/'package.json');registry=read_json(args.driver_cli.parent/'browsers.json')
        require(package['name']=='playwright-core','Existing Playwright core required')
        entry=next(x for x in registry['browsers']if x['name']==args.browser)
        require(args.executable.parents[1].name==args.browser+'-'+entry['revision'],'Driver/browser revision mismatch')
        # Select the already installed matching driver only in this disposable
        # Python process. No installed SDK file, browser or recorder is modified.
        import playwright._impl._transport as transport
        transport.compute_driver_executable=lambda:(str(args.driver_node),str(args.driver_cli))
        cap['driver']={'version':package['version'],'apiClientVersion':cap['playwrightVersion'],'node':str(args.driver_node),'nodeSha256':sha(args.driver_node.read_bytes()),'cli':str(args.driver_cli),'browserRegistryEntry':entry,
            'files':{p.relative_to(args.driver_cli.parent).as_posix():sha(p.read_bytes())for p in sorted(args.driver_cli.parent.rglob('*'))if p.is_file() and p.suffix in ['.js','.json','.mjs']},'scope':'Existing matching Node driver selected with unchanged Python API client; actual exercised protocol only'}
    lease={'holder':'R0024 owner executor','scope':'one serial native run','expiresEpoch':time.time()+7200,'fixtureManifestSha256':args.admission_sha,'lock':str(args.out.parent.parent/'native-resource.lock')}
    return lease,cap,pref

def select_cases(engine,matrix,ordered=None):
    table=cases();require(len(table)==98 and len({x['id']for x in table})==98,'Complete 98-row registry changed')
    require(engine in ['chromium','firefox'],'Exact engine required for selection')
    complete=[x for x in table if engine in x.get('engines',['chromium','firefox'])];require(len(complete)==(98 if engine=='chromium'else 97),'Complete engine denominator changed')
    if matrix=='all':require(not ordered,'--case requires --matrix subset');return complete,complete
    require(matrix=='subset' and isinstance(ordered,list)and 1<=len(ordered)<=len(complete),'Bounded nonempty ordered subset required')
    require(len(ordered)==len(set(ordered)),'Duplicate case IDs refused')
    lookup={x['id']:x for x in table}
    require(all(x in lookup for x in ordered),'Unknown case ID refused')
    require(all(engine in lookup[x].get('engines',['chromium','firefox'])for x in ordered),'Wrong-engine case ID refused')
    return complete,[lookup[x]for x in ordered]

def prior_attempts(engine_root):
    result={}
    if not engine_root.exists():return result
    for phase in sorted(engine_root.iterdir()):
        if not phase.is_dir():continue
        for case_dir in sorted(phase.iterdir()):
            if case_dir.is_dir():result.setdefault(case_dir.name,[]).append(str(case_dir))
    return result

def tile_png(kind):
    def chunk(k,b):return struct.pack('!I',len(b))+k+b+struct.pack('!I',zlib.crc32(k+b)&0xffffffff)
    colors={'zero-dbz':[130,123,105,73],'saturated':[255,68,0,255],'transparent':[0,0,0,0]}
    if kind in colors:rows=[bytearray(bytes(colors[kind])*256) for _ in range(256)]
    elif kind=='three-neighbours':
        rows=[bytearray(256*4) for _ in range(256)];fx=(39.61+180)/360*64;lr=24.47*math.pi/180;fy=(1-math.log(math.tan(lr)+1/math.cos(lr))/math.pi)/2*64
        px=int((fx-math.floor(fx))*256);py=int((fy-math.floor(fy))*256)
        for dx,dy in [(-1,0),(1,0),(0,1)]:rows[py+dy][(px+dx)*4:(px+dx)*4+4]=bytes(colors['saturated'])
    else:raise ValueError('Closed tile kind required')
    raw=b''.join(b'\0'+r for r in rows)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',256,256,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def helper_module():
    module=load('r24_legacy_helpers',PROPOSED/'tools/qa/legacy_weather_helpers.py')
    # Exact legacy transport implementation plus one closed separately labelled file route.
    original=module.FixtureServer
    class Server(original):
        def __init__(self,root):
            super().__init__(root);handler=self.server.RequestHandlerClass;parent=self
            class Handler(handler):
                def do_GET(self):
                    if unquote(urlsplit(self.path).path)=='/native-controls.js':
                        data=(ASSETS/'native-controls.js').read_bytes();parent.ledger.append({'path':'/native-controls.js','bytes':len(data),'sha256':sha(data)})
                        self.send_response(200);self.send_header('Content-Type','text/javascript');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
                    else:super().do_GET()
            self.server.RequestHandlerClass=Handler
    module.FixtureServer=Server
    return module

def approved_seed():
    return (ASSETS/'description-seed.js').read_text(encoding='utf-8')

def ax_read(page,base):
    result={'rawAriaSnapshot':base.accessibility(page)}
    if page.context.browser.browser_type.name!='chromium':return result
    session=page.context.new_cdp_session(page)
    try:
        root=session.send('DOM.getDocument')['root']['nodeId']
        for selector in ['#wi','.buckle']:
            node=session.send('DOM.querySelector',{'nodeId':root,'selector':selector})['nodeId'];require(bool(node),'AX element absent')
            backend=session.send('DOM.describeNode',{'nodeId':node})['node']['backendNodeId'];raw=session.send('Accessibility.getPartialAXTree',{'backendNodeId':backend,'fetchRelatives':False})
            nodes=[n for n in raw.get('nodes',[])if n.get('backendDOMNodeId')==backend];require(len(nodes)==1,'Ambiguous AX subject');n=nodes[0]
            result[selector]={'name':n.get('name',{}).get('value'),'description':n.get('description',{}).get('value'),'role':n.get('role',{}).get('value'),'ignored':n.get('ignored'),'raw':raw}
    finally:session.detach()
    return result

def publication(page,base,expected):
    base.wait(page,"()=>{const s=__weatherCases.read(__weatherCases.identity()),h=s.information.header,d=s.information.decision;return h&&h.generation===d.target.generation&&h.rawCode===(d.record?.code??null)&&h.temperature===(d.record?.temp??null)&&s.information.description===h.information.summary;}",timeout=10000)
    if 'wet'in expected:base.wait(page,"wet=>{const s=__weatherCases.read(__weatherCases.identity());return wet?s.precip==='on'&&s.visibleParticles>0:s.precip==='off'&&s.visibleParticles===0;}",expected['wet'],10000)

def observation(page):return page.evaluate('()=>__r24NativeControl.read(__r24NativeControl.identity())')

def cloud_surface(page):
    # The native input cloud canvas is intentionally hidden after CP9. Capture
    # the source-owned visible compositor; its pixels include the physical sky.
    return page.evaluate("""()=>{
      const card=document.querySelector('.c');if(!card)throw Error('Cloud capture card absent');
      const composed=card.classList.contains('real-sky-composed'),preview=card.classList.contains('real-sky-preview-ready');
      const selector=composed?'.real-sky-canvas':preview?'.real-sky-preview':null;
      if(!selector)throw Error('No accepted visible cloud compositor');
      const canvas=card.querySelector(selector);if(!canvas)throw Error('Cloud compositor absent');
      const style=getComputedStyle(canvas),box=canvas.getBoundingClientRect();
      if(style.visibility!=='visible'||style.display==='none'||!(+style.opacity>0)||![box.x,box.y,box.width,box.height].every(Number.isFinite)||!(box.width>0&&box.height>0))throw Error('Cloud compositor is not visibly drawable');
      return {selector,owner:composed?'accepted-composed':'accepted-preview',box:{x:box.x,y:box.y,width:box.width,height:box.height},visibility:style.visibility,display:style.display,opacity:+style.opacity,legacyInputVisible:false};
    }""")

def capture_cloud(page,path):
    before=cloud_surface(page);page.locator(before['selector']).screenshot(path=str(path));after=cloud_surface(page)
    require(before==after,'Visible cloud compositor changed during capture')
    return {'surface':before,'scope':'Actual visible compositor pixels include cloud, atmosphere and celestial contributions; cloud-only attribution remains a pixel-review gate.'}

def publish_case(output,row):
    try:write_json(output/'receipt.json',row)
    except (ValueError,TypeError):
        # Keep the unpublishable diagnostic literal. It cannot earn a case PASS.
        failure=traceback.format_exc();raw=output/'receipt-publication-failure.txt'
        raw.write_text(repr(row)+'\n'+failure,encoding='utf-8',newline='\n')
        data=raw.read_bytes()
        row={'id':row['id'],'attempt':row['attempt'],'status':'FAILED_DIAGNOSTIC_PUBLICATION','nativeClaim':False,
             'exception':failure,'rawDiagnostic':{'path':str(raw),'bytes':len(data),'sha256':sha(data)},
             'originalReportedStatus':row.get('status'),'qualification':'Unpublishable raw diagnostics retained; no case or numeric acceptance.'}
        write_json(output/'receipt.json',row)
    return row

def native_settings(page,base,oracle,native,spec,out):
    require(spec['id']=='INFO-local-settings' and spec.get('local')is True and page.context.browser.browser_type.name in ['chromium','firefox'],'Exact settings workflow required')
    receipt={'activation':[],'persistence':[]};checks={}
    def stored():return page.evaluate('()=>__weatherInfoStorage.read(__weatherCases.identity())')
    def arm(fault):page.evaluate('f=>__weatherInfoStorage.arm(__weatherCases.identity(),f)',fault)
    def opened(method):
        if method=='click':page.locator('.buckle').click()
        else:page.locator('.buckle').focus();page.keyboard.press(method)
        base.wait(page,"()=>document.querySelector('.c').classList.contains('settings-open')&&document.activeElement.id==='set-label'",timeout=3000)
    def closed():
        page.locator('#setClose').click();base.wait(page,"()=>!document.querySelector('.c').classList.contains('settings-open')&&document.activeElement===document.querySelector('.buckle')",timeout=3000)
    def information():
        publication(page,base,{})
        state=page.evaluate('()=>__weatherCases.read(__weatherCases.identity())');ax=ax_read(page,base);c=native.info_applicability(oracle.info_checks(state,ax,spec),spec,page.context.browser.browser_type.name)
        return {'state':state,'accessibility':ax,'INFOOracle':c},all(c['applicable'].values())
    for method in ['click','Enter','Space']:
        name=page.locator('.buckle').get_attribute('aria-label');opened(method);closed()
        event={'method':method,'focusRestored':page.evaluate("()=>document.activeElement===document.querySelector('.buckle')"),'nameUnchanged':page.locator('.buckle').get_attribute('aria-label')==name,'tabindex':page.locator('.buckle').get_attribute('tabindex')}
        checks['settings-'+method]=event['focusRestored']and event['nameUnchanged']and event['tabindex']=='0';receipt['activation'].append(event)
    for fault,label in [('none','Weather fixture saved'),('set','Weather fixture session only')]:
        arm(fault);before=stored();opened('click');page.locator('#set-label').fill(label);closed()
        if fault=='none':base.wait(page,'label=>JSON.parse(__weatherInfoStorage.read(__weatherCases.identity()).configRaw).label===label',label,5000)
        else:base.wait(page,"()=>document.querySelector('.buckle').getAttribute('aria-label').includes('changes not saved')",timeout=5000)
        after=stored();info,info_ok=information()
        valid=json.loads(after['configRaw'])['label']==label if fault=='none'else after['configRaw']==before['configRaw']and any(e[0]=='set-rejected'for e in after['events'][len(before['events']):])and 'changes not saved'in info['state']['information']['buckle']['name']
        checks['actual-save-'+fault]=valid;checks['post-save-info-'+fault]=info_ok;receipt['persistence'].append({'action':'actual-label-edit-close','fault':fault,'before':before,'after':after,**info});page.locator('.c').screenshot(path=str(out/('settings-save-'+fault+'.png')))
    arm('remove');before=stored();opened('Enter');page.locator('#set-reset').click();base.wait(page,"()=>document.querySelector('.buckle').getAttribute('aria-label').includes('saved settings could not be cleared')",timeout=5000)
    middle=stored();page.locator('.c').screenshot(path=str(out/'settings-reset-failure-open.png'));closed();info,info_ok=information()
    checks['actual-reset-failure']=middle['configRaw']==before['configRaw']and any(e[0]=='remove-rejected'for e in middle['events'][len(before['events']):])and 'saved settings could not be cleared'in info['state']['information']['buckle']['name'];checks['post-reset-info']=info_ok
    receipt['persistence'].append({'action':'actual-reset-click','fault':'remove','before':before,'after':middle,**info});arm('none');page.locator('.c').screenshot(path=str(out/'settings-reset-failure-closed.png'))
    return {'receipt':receipt,'checks':checks,'scope':'Actual settings click/keyboard/persistence/focus workflow in this recorded engine'}

def stale_sequence(page,base):
    before=observation(page);receipts=[]
    page.evaluate("()=>__r24NativeControl.stale(__r24NativeControl.identity(),'A')")
    base.wait(page,'()=>__r24NativeControl.read(__r24NativeControl.identity()).held.length===1',timeout=3000)
    a=observation(page);page.evaluate("()=>__r24NativeControl.stale(__r24NativeControl.identity(),'B')")
    base.wait(page,'()=>__r24NativeControl.read(__r24NativeControl.identity()).held.length===2',timeout=3000)
    b=observation(page);receipts.append(page.evaluate("()=>__r24NativeControl.stale(__r24NativeControl.identity(),'release')"))
    page.wait_for_timeout(100);after_a=observation(page)
    require(a['held'][0]['target']=={'lat':24.47,'lon':39.61} and b['held'][1]['target']=={'lat':30,'lon':0},'Held A/B physical target identities wrong')
    require(receipts[0]['aborted']is True,'Original A signal not aborted on generation')
    require(after_a['slots']['weather']==b['slots']['weather'] and after_a['state']['wxBusy']is True,'Obsolete A cleared active B')
    require(after_a['state']['raw']==before['state']['raw'] and after_a['state']['cached']==b['state']['cached'] and after_a['cacheByTarget']==b['cacheByTarget'] and after_a['cacheByTarget']['A']==before['cacheByTarget']['A'],'Obsolete A renewed/installed/cache-wrote either original A or active B key')
    require(b['capturedOperation']['lat']==30 and b['capturedOperation']['lon']==0 and after_a['capturedOperation']==b['capturedOperation'],'Captured B owner changed after obsolete A')
    receipts.append(page.evaluate("()=>__r24NativeControl.stale(__r24NativeControl.identity(),'release')"))
    base.wait(page,'()=>{const r=__r24NativeControl.read(__r24NativeControl.identity());return !r.state.wxBusy&&r.state.raw?.target?.lat===30&&r.state.raw?.target?.lon===0&&r.state.qa.cache.prayerLoaded;}',timeout=10000)
    after_b=observation(page);require(after_b['state']['cached']['w']['target']==after_b['state']['raw']['target'],'B current cache target mismatch')
    require(after_b['cacheByTarget']['A']==before['cacheByTarget']['A'],'B/late A overwrote retained original A cache')
    receipts.append(page.evaluate("()=>__r24NativeControl.stale(__r24NativeControl.identity(),'tick')"))
    return {'before':before,'A':a,'B':b,'releaseA':after_a,'afterB':after_b,'releases':receipts,'checks':{'obsoleteANeverInstallsOrRenews':True,'obsoleteADoesNotClearB':True,'BLat30Lon0Admitted':True}}

def suspension(page,context,base,spec,engine,out):
    before=observation(page);require(before['state']['precip']=='on','Suspension must begin with actual wet presentation')
    before_particles=page.evaluate("()=>[...document.querySelectorAll('.drop,.flake')].map(e=>({class:e.className,left:e.style.left,delay:e.style.animationDelay}))")
    page.locator('.c').screenshot(path=str(out/'before-suspension.png'))
    kind=spec['suspend']['kind']
    session=None;other_session=None;other=None;physical={'requested':kind,'kind':kind,'reason':'Declared native operation; Chromium focus emulation disabled using its installed protocol so actual tab visibility can propagate','startedMonotonic':time.monotonic(),'seconds':spec['suspend']['seconds']}
    try:
        require(kind in ['freeze','tab'],'Closed suspension kind')
        if engine=='chromium':
            session=context.new_cdp_session(page);session.send('Emulation.setFocusEmulationEnabled',{'enabled':False})
            physical['subjectFocusEmulationDisabled']=True
        other=context.new_page();other.goto('about:blank')
        if engine=='chromium':
            other_session=context.new_cdp_session(other);other_session.send('Emulation.setFocusEmulationEnabled',{'enabled':False})
            physical['helperFocusEmulationDisabled']=True
        other.bring_to_front()
        base.wait(page,"()=>document.visibilityState==='hidden'&&document.querySelector('.c').classList.contains('paused')",timeout=3000)
        physical['hidden']=observation(page)
        if kind=='freeze':
            require(engine=='chromium','Freeze only admitted Chromium CDP');session.send('Page.setWebLifecycleState',{'state':'frozen'})
            # No evaluation, synthetic event or fake callback while frozen.
            time.sleep(spec['suspend']['seconds']);session.send('Page.setWebLifecycleState',{'state':'active'})
        else:time.sleep(spec['suspend']['seconds'])
        page.bring_to_front()
        base.wait(page,"()=>document.visibilityState==='visible'&&!document.querySelector('.c').classList.contains('paused')",timeout=3000)
    finally:
        if other_session:other_session.detach()
        if session:session.detach()
        if other:other.close()
    publication(page,base,{'wet':False});after=observation(page);page.locator('.c').screenshot(path=str(out/'expired-after-resume.png'))
    actual_particles=page.evaluate("()=>[...document.querySelectorAll('.drop,.flake')].map(e=>({class:e.className,left:e.style.left,delay:e.style.animationDelay}))")
    events=after['nativeEvents'];types=['freeze','resume']if kind=='freeze' else ['visibilitychange']
    checks={'actualTrustedLifecycleObserved':all(any(e['type']==t and e['trusted']is True for e in events)for t in types),
        'actualTrustedHiddenAndVisible':all(any(e['type']=='visibilitychange' and e['trusted']is True and e['visibility']==visibility for e in events)for visibility in ['hidden','visible']),
        'expiredWetWithdrawn':after['state']['precip']=='off' and after['state']['visibleParticles']==0 and after['state']['lightning']=='off',
        'cloudPopulationRetained':before['cloud']['motion']['key']==after['cloud']['motion']['key'] and before['cloud']['motion']['population']==after['cloud']['motion']['population'] and before['cloud']['fieldSeed']==after['cloud']['fieldSeed'],
        'particleHistoryRetained':before_particles==actual_particles}
    result={'before':before,'after':after,'physicalOperation':physical,'checks':checks,'pixelContinuity':'PENDING independent full-scene/crop/clip review'}
    if spec['suspend'].get('recover'):
        result['recoveryKick']=page.evaluate('()=>__r24NativeControl.recovery(__r24NativeControl.identity())')
        base.wait(page,'()=>{const r=__r24NativeControl.read(__r24NativeControl.identity());return !r.state.wxBusy&&r.eligibility.eligible;}',timeout=12000);publication(page,base,{'wet':True})
        fresh=observation(page);result['recovered']=fresh;checks['freshAcquisitionRestoresModelOnly']=fresh['state']['raw']['retrievedAt']>before['state']['raw']['retrievedAt'] and fresh['state']['qa']['wxTruth']['observedPresent']is False and fresh['state']['lightning']=='off';page.locator('.c').screenshot(path=str(out/'fresh-model-restored.png'))
    return result

def run(args):
    lease,cap,pref=lease_preflight(args) # All guards occur before imports, output mkdir, socket or browser launch.
    def alive():require(time.time()<lease['expiresEpoch'],'Execution lease expired; stop and retain partial output')
    import importlib.metadata
    from playwright.sync_api import sync_playwright
    base=helper_module();oracle=load('r24_info',PROPOSED/'tools/qa/info_contract.py');native=load('r24_native_contract',PROPOSED/'tools/qa/native_contract.py')
    complete,specs=select_cases(args.browser,args.matrix,args.case)
    prior=prior_attempts(args.out.parent)
    args.out.mkdir(parents=True,exist_ok=False)
    report={'schema':'r0024-native-executed-proposal/v1','node':'R0024-NATIVE','status':'STARTED','preflight':pref,'lease':lease,'admissionSha256':args.admission_sha,'capability':cap,'cases':[],
        'settingsWorkflowReused':False,'nativeNodeCredit':False,'publicDeliveryCredit':False,'pixelReview':'PENDING','independentDisposition':'PENDING','providerScope':'Controlled native Response/real Image fixtures; no provider availability/precision claim',
        'phase':args.phase,'matrix':args.matrix,'selectedCaseIds':[x['id']for x in specs],'attemptedCaseIds':[],'completeEngineCaseIds':[x['id']for x in complete],'fullEngineDenominator':len(complete),'fullUniqueRows':98,
        'obligationRegistry':[{'id':x['id'],'status':'PRIOR_ATTEMPT_RETAINED_PENDING_ROOT_RECONCILIATION'if x['id']in prior else'NOT_RUN','retainedPhasePaths':prior.get(x['id'],[])}for x in complete],
        'otherEngineDenominator':97 if args.browser=='chromium'else 98,'otherEngineDisposition':'Not executed by this phase; root reconciles any retained other-engine receipts',
        'unexecutedCaseIds':[x['id']for x in complete if x['id']not in {s['id']for s in specs}and x['id']not in prior]}
    write_json(args.out/'results.json',report)
    try:
        with base.FixtureServer(args.root)as server,sync_playwright()as pw:
            report['fixtureOrigin']=server.origin;write_json(args.out/'results.json',report) # actual owned transport endpoint, before browser launch
            options={'headless':cap['headless'],'executable_path':cap['executable']}
            if args.browser=='chromium':options.update(chromium_sandbox=True,args=['--disable-dev-shm-usage'])
            browser=getattr(pw,args.browser).launch(**options)
            try:
                cap['version']=browser.version
                for attempt,spec in enumerate(specs,1):
                    require(time.time()<lease['expiresEpoch'],'Execution lease expired; stop, retain prior outputs')
                    output=args.out/spec['id'];output.mkdir();report['attemptedCaseIds'].append(spec['id']);context=None;row={'id':spec['id'],'attempt':attempt,'input':spec,'status':'NOT_RUN','actualRequestFailed':[],
                        'priorRetainedAttemptPaths':prior.get(spec['id'],[]),'lifetimeAttemptIndex':len(prior.get(spec['id'],[]))+1}
                    write_json(output/'ATTEMPT_RESERVATION.json',{'schema':'r0024-native-case-attempt-reservation/v1','id':spec['id'],'engine':args.browser,'phase':args.phase,'admissionSha256':args.admission_sha,'fixtureManifestSha256':lease['fixtureManifestSha256'],'status':'PRE_CONTEXT_RESERVED','oneAttemptOnly':True})
                    try:
                        server.tile=tile_png(spec.get('tile','zero-dbz'))
                        context,page,errors,network,url=base.open_case(browser,server,spec,read_json(BINDING)['entrySha256'],args.run,attempt,output,failed=row['actualRequestFailed'])
                        alive();row['seedDescriptions']=page.evaluate(approved_seed());row['url']=url;row['fixtureIdentity']=page.evaluate('()=>__weatherCases.identity()');row['actionReceipts']=[]
                        for index,value in enumerate(spec.get('actions',[])):
                            alive()
                            receipt=page.evaluate('i=>__weatherCases.step(__weatherCases.identity(),i)',index);publication(page,base,value.get('checkpoint',{}))
                            state=page.evaluate('()=>__weatherCases.read(__weatherCases.identity())');receipt['publishedState']=state
                            if value.get('checkpoint'):receipt['checks']=page.evaluate('e=>__weatherCases.checks(__weatherCases.read(__weatherCases.identity()),e)',value['checkpoint'])
                            row['actionReceipts'].append(receipt)
                        row['nativeReceipts']=[]
                        for step in spec.get('nativeSteps',[]):
                            alive()
                            if step['kind']=='stale-response':r=stale_sequence(page,base)
                            else:r=page.evaluate('k=>__r24NativeControl.run(__r24NativeControl.identity(),k)',step['kind'])
                            row['nativeReceipts'].append(r)
                        if spec.get('suspend'):
                            require(time.time()+20<lease['expiresEpoch'],'Insufficient suspension/recovery lease remainder');row['suspension']=suspension(page,context,base,spec,args.browser,output)
                        if spec.get('settingsWorkflow'):row['settingsWorkflow']=native_settings(page,base,oracle,native,spec,output)
                        expected={**spec.get('expect',{}),'group':'R0024'}
                        # Recovery has its own before/off/after requirements; final state is healthy again.
                        if spec.get('suspend',{}).get('recover'):expected.update(wet=True,modelEstimate=True)
                        publication(page,base,expected)
                        state=page.evaluate('()=>__weatherCases.read(__weatherCases.identity())');native_state=observation(page)
                        checks=page.evaluate('e=>__weatherCases.checks(__weatherCases.read(__weatherCases.identity()),e)',expected)
                        checks['allActionCheckpoints']=all(all(r.get('checks',{}).values())for r in row['actionReceipts'])
                        checks['allTypedNativeControls']=all(all(r['checks'].values())if isinstance(r.get('checks'),dict)else all(x['passed']for x in r.get('checks',[]))for r in row['nativeReceipts'])
                        checks['allFinalNativeControls']=all(x['passed']for x in native_state['checks'])
                        if spec.get('suspend'):checks.update(row['suspension']['checks'])
                        if spec.get('settingsWorkflow'):checks.update(row['settingsWorkflow']['checks'])
                        if 'imageRequests'in expected:checks['actualTileRequestCount']=len([u for u in network if '/tile/'in u])==expected['imageRequests']
                        checks.update(noUnexpectedCoarseDetection=not any('geojs' in u or 'ipinfo'in u for u in network),noPageErrors=not errors)
                        ax=ax_read(page,base);info=native.info_applicability(oracle.info_checks(state,ax,spec),spec,args.browser);checks.update({'INFO:'+k:v for k,v in info['applicable'].items()})
                        samples=[];end=time.monotonic()+(spec.get('strikeObservationSeconds',0)if spec.get('watchStrike')else .3);peak=False
                        while time.monotonic()<end:
                            alive()
                            frame=page.evaluate('()=>__weatherCases.strikeRead(__weatherCases.identity())');samples.append(frame)
                            if not peak and any(x['opacity']>.5 for x in frame):page.locator('.c').screenshot(path=str(output/'actual-strike-peak.png'));peak=True
                            page.wait_for_timeout(50)
                        if spec.get('watchStrike'):checks.update(native.strike_checks(samples,spec))
                        checks.update(native.effect_checks(state,samples,{**spec,'expect':expected},native_state['origins']))
                        checks.update(native.provenance_checks(state,spec))
                        if 'alpha'in spec['nativeChecks']:checks.update(native.alpha_checks(state,spec))
                        if 'quantity-null'in spec['nativeChecks']:checks['nonfiniteStringOrOverflowUnavailable']=state['raw']['precip']is None and 'amount unavailable'in state['information']['description']
                        page.locator('#wi').hover();row['hover']=page.evaluate("()=>{const wi=document.querySelector('#wi');return {title:wi.title,hovered:wi.matches(':hover'),description:document.querySelector('#weather-information').textContent};}")
                        checks['actualPointerTitleSameSnapshot']=row['hover']['hovered']is True and row['hover']['description']==state['information']['description'] and state['information']['description']in row['hover']['title']
                        for selector,name in [('.c','card'),('.h','header'),('.d','footer')]:page.locator(selector).screenshot(path=str(output/(name+'.png')))
                        row['cloudCapture']=capture_cloud(page,output/'cloud.png')
                        box=page.locator('.c').bounding_box();page.screenshot(path=str(output/'sky-upper.png'),clip={'x':box['x'],'y':box['y'],'width':box['width'],'height':260})
                        if spec.get('watchMotionSeconds'):
                            require(time.time()+spec['watchMotionSeconds']+5<lease['expiresEpoch'],'Insufficient motion lease remainder')
                            row['motionSurfaceBefore']=capture_cloud(page,output/'cloud-before.png');page.wait_for_timeout(spec['watchMotionSeconds']*1000);row['motionSurfaceAfter']=capture_cloud(page,output/'cloud-after.png')
                            row['motionPixels']=base.pixel_delta(output/'cloud-before.png',output/'cloud-after.png');row['motionReview']='PENDING actual visible compositor clip/crops; delta includes atmosphere/celestial contributions and supplies no cloud-only or hash proof'
                            row['afterMotion']=observation(page)
                            page.locator('.c').screenshot(path=str(output/'card-after-motion.png'))
                            page.screenshot(path=str(output/'sky-after-motion.png'),clip={'x':box['x'],'y':box['y'],'width':box['width'],'height':260})
                        row.update(state=state,nativeObservation=native_state,checks=checks,accessibility=ax,INFOOracle=info,strikeSamples=samples,network=network,pageErrors=errors,providerLedger=page.evaluate('()=>__widgetFixture.ledger'))
                        row['requestFailureDisposition']='Raw actual Context/Page callbacks retained for root reconciliation; no R0018 or transport-clearance claim. Any resulting broken scene remains a pixel gate.'
                        row['status']='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW'if all(checks.values())else 'FAIL'
                    except Exception:
                        row.update(status='FAILED_CONSUMER_OR_HARNESS',exception=traceback.format_exc(),nativeClaim=False)
                        if context:
                            try:
                                row['failureObservation']=observation(page);page.locator('.c').screenshot(path=str(output/'failure-card.png'))
                            except Exception:row['failureCaptureException']=traceback.format_exc()
                    finally:
                        if context:context.close()
                    row=publish_case(output,row)
                    print(json.dumps({'case':row['id'],'status':row['status']}),flush=True)
                    next(x for x in report['obligationRegistry']if x['id']==spec['id'])['status']=row['status']
                    report['cases'].append(row);write_json(args.out/'results.json',report)
                    if row['status']!='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW':break # preserve failure and stop this admitted batch
            finally:browser.close()
            report['httpLedger']=server.ledger
    except Exception:
        report['executionFailure']={'type':'CONSUMER_OR_HARNESS_EXCEPTION','traceback':traceback.format_exc(),'nativeClaim':False}
    report['sourcePostflight']=source_preflight(args.root)
    complete_return=not report.get('executionFailure')and [r['id']for r in report['cases']]==report['selectedCaseIds']==report['attemptedCaseIds']and all(r['status']=='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW'for r in report['cases'])
    report['status']=('EXECUTED_SUBSET_PENDING_PIXEL_AND_INDEPENDENT_REVIEW'if args.matrix=='subset'else'EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW')if complete_return else 'FAIL'
    write_json(args.out/'results.json',report);print(json.dumps({'status':report['status'],'executed':len(report['cases']),'out':str(args.out)}));return 0 if report['status'].startswith('EXECUTED_')else 1

def main():
    global BINDING
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=PROPOSED);p.add_argument('--out',type=Path);p.add_argument('--browser',choices=['chromium','firefox']);p.add_argument('--executable',type=Path);p.add_argument('--driver-cli',type=Path);p.add_argument('--driver-node',type=Path);p.add_argument('--matrix',choices=['all','subset'],default='all');p.add_argument('--case',action='append');p.add_argument('--phase');p.add_argument('--run');p.add_argument('--input',type=Path);p.add_argument('--input-sha',dest='admission_sha');p.add_argument('--prepare',action='store_true');p.add_argument('--preflight',action='store_true');p.add_argument('--list',action='store_true');a=p.parse_args()
    if a.list:
        complete,selected=select_cases(a.browser,a.matrix,a.case);print(json.dumps({'orderedCaseIds':[x['id']for x in selected],'completeEngineDenominator':len(complete),'completeUniqueRows':len(cases()),'native':'NOT_RUN'},indent=2));return 0
    if a.prepare:
        if not a.input or a.input.exists():p.error('New --input path required; previous evidence is immutable')
        write_json(a.input,input_manifest(a.root));print(sha(a.input.read_bytes()));return 0
    BINDING=a.input
    if a.preflight:print(json.dumps(source_preflight(a.root)));return 0
    if not all([a.out,a.browser,a.executable,a.phase,a.run,a.input,a.admission_sha]):p.error('Exact input/hash/output/engine/executable/phase/run required')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    lock=a.out.parent.parent/'native-resource.lock'
    with lock.open('x',encoding='utf-8')as f:json.dump({'pid':os.getpid(),'run':a.run,'out':str(a.out),'started':time.time()},f)
    try:return run(a)
    finally:lock.unlink()
if __name__=='__main__':raise SystemExit(main())
