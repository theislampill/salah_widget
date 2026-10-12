"""Read-only review of the returned ten-case R0010 batch; own output only."""
from pathlib import Path
from copy import deepcopy
import datetime as dt, hashlib, json, re, struct, traceback

R = Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009')
W = Path(__file__).resolve().parent
A = R/'workers/r0010_delivered_native_closure_r2'
P = A/'actual-return-r1'
O = R/'evidence/R0010/preferences-delivered-main-r2'
D = R/'evidence/R0010/preferences-delivered-dispatch-r2'
Q = W.parent/'delivered-native-source-admission-r2'
HEAD = '88926dd12d22a6a8c1cd369d4823750778fccb48'
RUNTIME = 'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
CASES = ['fresh-2-f','fresh-2-c','fresh-4-f','fresh-4-c','generic-local','saved-native-reload','prefer-local-fresh','prefer-local-saved','mutant-omitMethod','mutant-omitUnits']
KEY = 'salah_widget:config:v1'
read = lambda p: json.loads(Path(p).read_bytes())
digest = lambda b: hashlib.sha256(b).hexdigest()
refs = []

def pin(p):
    p = Path(p); b = p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':digest(b)}

def bound(ref):
    p = Path(ref['path']); actual = pin(p)
    assert actual == {k:ref[k] for k in actual}, 'reference differs: '+str(p)
    refs.append(actual)
    return p

def packet(root, expected):
    assert pin(root/'SEAL.json')['sha256'] == expected, 'seal differs'
    s = read(root/'SEAL.json')
    assert pin(root/'MANIFEST.json')['sha256'] == s['manifestSha256']
    files = read(root/'MANIFEST.json')['files']
    if isinstance(files,dict): files = [{'path':k,**({'sha256':v} if isinstance(v,str) else v)} for k,v in files.items()]
    seen = set()
    for f in files:
        rel = f['path']
        assert rel not in seen and '\\' not in rel and ':' not in rel and all(x not in ('','.','..') for x in rel.split('/'))
        seen.add(rel); p = (root/rel).resolve(); assert p.is_relative_to(root.resolve())
        actual = pin(p)
        assert actual['sha256'] == f['sha256'] and ('bytes' not in f or actual['bytes'] == f['bytes']), rel
    if 'reportSha256' in s: assert pin(root/'REPORT.json')['sha256'] == s['reportSha256']
    return len(files)

def manifest(binding, variant=None):
    b = deepcopy(binding); root = Path(binding['candidateRoot'])
    for name,file in [('widget','index.html'),('builder','builder.html')]:
        raw = (root/file).read_bytes()
        scripts = re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>',raw.decode('utf-8'),re.I)
        b['pages'][name] = {'sha':digest(raw),'attrs':[x[0] for x in scripts],'bodiesSha256':[digest(x[1].encode()) for x in scripts]}
    config = (root/'config.js').read_bytes(); base = digest(config)
    if variant:
        branch = 'method' if variant == 'omitMethod' else 'units'
        old = ('explicit.indexOf("'+branch+'") >= 0').encode()
        assert config.count(old) == 1
        config = config.replace(old,b'false')
    b['configSha256'] = digest(config)
    b['fixtureMutation'] = {'name':variant,'file':'config.js','baseSha256':base,'mutatedSha256':digest(config)} if variant else None
    return b

def config_bytes(s): return next((v for k,v in s['report']['storage'] if k == KEY),None)
def coarse(s): return sum(bool(re.search(r'geojs|ipinfo',x['url'])) for x in s['report']['requests'])
def writes(s): return sum(x[0]=='set' and x[1]==KEY for x in s['report']['storageEvents'])

def js_property_order(value):
    # SourceServer serves JSON.stringify; JS enumerates integer option keys first.
    if isinstance(value,list): return [js_property_order(x) for x in value]
    if not isinstance(value,dict): return value
    integer = lambda k: bool(re.fullmatch(r'0|[1-9][0-9]*',k)) and int(k)<4294967295
    keys=sorted((k for k in value if integer(k)),key=int)+[k for k in value if not integer(k)]
    return {k:js_property_order(value[k]) for k in keys}

def preference(s,method,units,lat,lon,inputs=True):
    assert (s['config']['method'],s['config']['units'],s['config']['lat'],s['config']['lon']) == (method,units,lat,lon)
    if inputs: assert (s['app']['inputs']['set-method'],s['app']['inputs']['set-units']) == (method,units)

def visible(v, method, units, labels):
    for field,want in [('set-method',method),('set-units',units)]:
        x=v[field]; assert x['value']==want and x['label']==labels[field][want] and x['visible'] is True
        rect=x['rect']; assert rect['width']>0 and rect['height']>0 and rect['x']>=0 and rect['y']>=0 and rect['x']+rect['width']<=325 and rect['y']+rect['height']<=530

def exports(row, expected, platforms):
    ex=row.get('builderExports',[]); assert [x['platform'] for x in ex]==platforms
    for x in ex:
        assert x['hash']==expected and x['cmd']['carry'] is True
        assert re.search(r'\bsrc="([^"]+)"',x['code'])[1].split('#',1)[1]==expected
        assert x['preview'].split('#',1)[1]==x['openURL'].split('#',1)[1]==expected
        assert re.search(r"SALAH_WIDGET_HASH='([^']*)'",x['cmd']['cmd'])[1]==expected
        assert len(x['copies'])==2 and x['copies'][0]['payload']==x['code'] and x['copies'][1]['payload']==x['cmd']['cmd'] and all(v['state']=='success' for v in x['copies'])
        assert 'width:325px;height:530px' in x['code']
        assert all(k+'=' not in expected for k in ['lat','lon','label'])

def utc(row):
    witnesses=row['actualUTCContexts']; assert len(witnesses)==3
    assert [x['purpose'] for x in witnesses]==['builder-Windows','builder-Linux','actual-widget-consumer']
    for x in witnesses:
        assert x['api']=='browser.newContext' and x['requestedTimezoneId']=='UTC' and x['syntheticProviderTimezoneIsNotThisWitness'] is True
        for field in ['beforeNavigation','afterProductionInitialization']:
            assert x[field]['timeZone']=='UTC' and x[field]['timezoneOffsetAtFixtureEpoch']==0
            assert x[field]['method']=='actual Intl.DateTimeFormat resolvedOptions and native Date offset'

def verify_case(row,binding,active,expected_env):
    name=row['name']; negative=name.startswith('mutant-'); variant=row.get('mutant')
    b=manifest(binding,variant)
    assert row['group']=='r0010' and row['sourceRef']==HEAD and row['sourceBinding']==b
    assert row['launchLease']['ledgerSha256']==pin(D/'ACTIVE_LEDGER.active.json')['sha256'] and row['launchLease']['lease']==active
    assert row['executionEnvironment']==expected_env
    native=row['native']; assert native['browser']=='chromium' and native['version']=='148.0.7778.96' and native['os']=='win32' and native['viewport']=={'width':1000,'height':900} and native['dpr']==1
    assert native['timezone']==('Asia/Riyadh' if name.startswith('fresh-') or name=='generic-local' else 'UTC')
    pre=row['preflight']; assert pre['selected']==CASES and pre['runtimeSha256']==RUNTIME and pre['runtimeFiles']==135 and pre['scriptCounts']=={'widget':6,'builder':2}
    inventory_sha=digest(json.dumps(js_property_order(b),ensure_ascii=False,separators=(',',':')).encode())
    for s in row['snapshots'].values():
        report=s['report']; assert report['state']=='ready' and report['error'] is None and report['storageMode']=='native'
        assert report['productionScriptBodiesPreserved'] is True and report['scriptCount']==6 and report['target']==HEAD
        assert report['sourceSha256']==binding['pages']['widget']['sha'] and report['configSha256']==b['configSha256'] and report['runtimeInventorySha256']==inventory_sha
        assert report['gpsCalls']==[] and report['nativeCallbacks']==[] and report['clock']=='fixed synthetic UTC epoch'
        assert config_bytes(s)==s['app']['savedBytes']
    reds=[x['name'] for x in row['checks'] if x['passed'] is not True]
    assert reds==(['selected preference'] if negative else [])
    assert row['status']==('CAUGHT' if negative else 'PASS')
    counts={'preference':19 if not negative else 15,'generic':6,'saved':21,'prefer':6}
    assert len(row['checks'])==counts[row['type']]
    labels=binding['visibleOptionLabels']; sv=row['snapshots']
    if row['type']=='preference':
        method,units=row['method'],row['units']; expected=f'local=1&method={method}&units={units}&appearance=glass'
        if variant=='omitMethod': expected=f'local=1&units={units}&appearance=glass'
        if variant=='omitUnits': expected=f'local=1&method={method}&appearance=glass'
        exports(row,expected,['Windows','Linux']); s=sv['fresh widget consumer']
        assert s['report']['bytesBeforeSeed'] is None and s['report']['seedApplied'] is False and config_bytes(s) is None and writes(s)==0 and coarse(s)==1
        if not negative:
            preference(s,method,units,24.47,39.61); visible(row['visiblePreferences']['fresh'],method,units,labels)
        else:
            utc(row); observed=('4','f') if variant=='omitMethod' else ('2','c')
            preference(s,*observed,24.47,39.61); assert observed != (method,units)
            assert row['error']['code']=='CONSUMER_ASSERTION' and row['error']['assertion']=='selected preference'
            f=row['selectedPreferenceFailure']; assert f['code']=='CONSUMER_ASSERTION' and f['assertion']=='selected preference' and f['detail']==s
            e=row['selectedFailureEvidence']; field='set-method' if variant=='omitMethod' else 'set-units'
            assert e['field']==field and e['requested']=={'method':method,'units':units} and e['observed']=={'method':observed[0],'units':observed[1]}
            visible(e['visibleSelected'],*observed,labels)
    elif row['type']=='generic':
        s=sv['generic local']; preference(s,'4','c',24.47,39.61)
        assert row['genericHash']=='local=1' and coarse(s)==1 and config_bytes(s) is None and not s['report']['seedApplied'] and s['report']['bytesBeforeSeed'] is None
        visible(row['visiblePreferences']['generic'],'4','c',labels)
    elif row['type']=='saved':
        exports(row,'local=1&method=2&units=f&appearance=glass',['Windows'])
        first,second=sv['first saved boot'],sv['actual reload']
        preference(first,'3','c',51.5,-.12)
        # The reload snapshot precedes opening the lazy-populated settings form.
        # Its CONFIG is the original reload predicate; visiblePreferences below
        # independently checks the original post-open form and retained crop.
        preference(second,'3','c',51.5,-.12,inputs=False)
        assert first['report']['seedApplied'] is True and first['report']['bytesBeforeSeed'] is None and writes(first)==1
        saved=config_bytes(first); assert saved is not None and saved==first['report']['seedBytes']==config_bytes(second)==second['report']['bytesBeforeSeed']
        assert second['report']['seedApplied'] is False and writes(second)==0 and coarse(first)==coarse(second)==0
        rw=row['reloadWitness']; assert rw['api']=='Playwright page.reload' and rw['seed']=='none' and rw['sameOrigin'] is True and 'seed=none' in rw['wrapperUrl']
        for k in ['saved-first','saved-reload']: visible(row['visiblePreferences'][k],'3','c',labels)
        assert any(x['name']=='native reload replaces actual document' and x['passed'] is True for x in row['checks'])
    elif row['type']=='prefer':
        s=sv['prefer-local']; saved=name.endswith('saved')
        preference(s,*('3','c',51.5,-.12) if saved else ('2','f',24.47,39.61))
        assert coarse(s)==0 and s['report']['bytesBeforeSeed'] is None and s['report']['seedApplied'] is saved
        assert (config_bytes(s) is not None)==saved
        visible(row['visiblePreferences']['prefer-saved' if saved else 'prefer-fresh'],*('3','c') if saved else ('2','f'),labels)
    return {'case':name,'acceptance':row['acceptance'],'independentDisposition':row['status'],'rawReceipt':pin(O/name/'result.json'),'snapshotCount':len(sv),'checks':len(row['checks']),'semanticRed':reds,'inventoryManifestSha256':inventory_sha}

def main():
    sizes={'actualReturn':packet(P,'0282dad5ab8297658785575bb136b6a5de0b683db1fd8ce97374fc845fbd70e5'),'source':packet(A,'7261e6808570fd8dedac479a55d872bada63f3c3605030ab43ee8bc222523f69'),'sourceReview':packet(Q,'c2e711581acf3e7281222080c4290d29af750bee574915617fd21c7ee5d82b5a')}
    report=read(P/'REPORT.json')
    for ref in report.values():
        if isinstance(ref,dict) and all(k in ref for k in ['path','bytes','sha256']): bound(ref)
    admission=read(Q/'ADMISSION.json'); assert admission['sourceAdmission']=='PASS' and admission['scope']==CASES and admission['deliveredHead']==HEAD
    binding=read(A/'native/source-binding.json'); root=Path(binding['candidateRoot'])
    for rel,f in binding['runtimeRows'].items(): assert pin(root/rel)['sha256']==f['sha256'] and pin(root/rel)['bytes']==f['bytes']
    canonical=''.join(f['sha256']+'  '+p+'\n' for p,f in sorted(binding['runtimeRows'].items()))
    assert digest(canonical.encode())==binding['runtimeSha256']==RUNTIME and len(binding['runtimeRows'])==135
    dispatch=read(D/'dispatch.json'); results=read(O/'results.json'); outputs=read(P/'OUTPUT_FILES.json')
    expected_inventory={x['relative']:{'bytes':x['bytes'],'sha256':x['sha256']} for x in outputs['files']}
    actual_inventory={p.relative_to(O).as_posix():{k:v for k,v in pin(p).items() if k!='path'} for p in O.rglob('*') if p.is_file()}
    assert actual_inventory==expected_inventory=={x['path']:{'bytes':x['bytes'],'sha256':x['sha256']} for x in dispatch['files']} and len(actual_inventory)==36
    for f in outputs['files']: bound(f)
    assert dispatch['scope']==results['selected']==CASES and results['notRun']==[] and [x['name'] for x in results['executed']]==CASES
    assert results['sourceRef']==HEAD and results['runtimeAfter']=={'treeSha256':RUNTIME,'unchanged':True}
    assert dispatch['exitCode']==0 and dispatch['processChainCompletion']=='CHILD_RETURNED_KNOWN_EXIT' and dispatch['childReturned'] is True and dispatch['leaseReleasePermitted'] is True and dispatch['automaticRetries']==0 and dispatch['nodeCredit'] is False
    assert dispatch['authorSealSha256']==pin(A/'SEAL.json')['sha256'] and dispatch['independentSourceReviewSealSha256']==pin(Q/'SEAL.json')['sha256'] and dispatch['sourceRuntime']==RUNTIME
    cmd=dispatch['command']; assert [cmd[i+1] for i,x in enumerate(cmd) if x=='--only']==CASES and cmd[cmd.index('--source-ref')+1]==HEAD and cmd[cmd.index('--source-root')+1]==str(root) and cmd[cmd.index('--browser')+1]=='chromium' and cmd[cmd.index('--lease-id')+1]==dispatch['leaseId']
    prepared=read(A/'ROOT_COMMAND.json')
    expected_cmd=[str(O) if x=='ROOT_FRESH_CONSUMER_OUT_REQUIRED' else dispatch['leaseId'] if x=='ROOT_ACTUAL_LEASE_ID_REQUIRED' else x for x in prepared['argvTemplate']]
    assert cmd==expected_cmd
    for f in list(prepared['toolIdentities'].values())+[prepared['driverIdentity'],prepared['actionsIdentity'],prepared['fixtureIdentity'],prepared['bindingIdentity']]: bound(f)
    custody=read(P/'CUSTODY_ASSOCIATION.json')
    before,held,after=[read(bound(custody[k])) for k in ['recordedBefore','active','recordedAfter']]
    assert before['nodes']==held['nodes']==after['nodes'] and before['issues']==held['issues']==after['issues'] and before['effects']==held['effects']==after['effects']
    leases=[x['resourceLeases']['heavy-browser'] for x in [before,held,after]]; free,active,released=leases
    assert free['status']=='FREE' and free['holder'] is None and free['capacity']==1 and free['leaseId']!=dispatch['leaseId']
    assert active['status']=='ACTIVE' and active['holder']=='root' and active['capacity']==1 and active['leaseId']==released['leaseId']==dispatch['leaseId']
    assert active['command']==released['command']==cmd[4] and active['delegatedOperator']=='/root/r0010_isolated_release_path_r1' and active['delegation']==report['ownerAuthority']
    assert released['status']=='FREE' and released['holder'] is None and released['lastResult']==str(D/'dispatch.json') and active['unknownChildCompletion'] is False and released['unknownChildCompletion'] is False
    assert pin(D/'ACTIVE_LEDGER.before.json')['sha256']==dispatch['freeLedgerSha256'] and pin(D/'ACTIVE_LEDGER.active.json')['sha256']==dispatch['activeLedgerSha256']
    assert {k:released[k] for k in custody['operativeResourceFields']}==custody['operativeResourceFields']
    inherited={k:v for k,v in free.items() if active.get(k)==v and k not in ['holder','status','capacity','sessionId','unknownChildCompletion']}
    environment=read(O/CASES[0]/'result.json')['executionEnvironment']
    rows=[]; raw=[]
    association=read(P/'CASE_ASSOCIATION.json'); assert [x['case'] for x in association['rows']]==CASES
    for name,res,assoc in zip(CASES,results['executed'],association['rows']):
        row=read(O/name/'result.json'); raw.append(row)
        proof=verify_case(row,binding,active,environment); rows.append(proof)
        assert res['status']==assoc['observed']==proof['independentDisposition'] and assoc['rawReceipt']==proof['rawReceipt']
        for key in ['native','executionEnvironment','builderExports','visiblePreferences','reloadWitness','actualUTCContexts','selectedFailureEvidence']:
            assert assoc[key]==row.get(key,[] if key in ['builderExports','actualUTCContexts'] else None)
        assert assoc['checksPASS']==sum(x['passed'] is True for x in row['checks'])
        for image in assoc['images']:
            bound({k:image[k] for k in ['path','bytes','sha256']}); content=Path(image['path']).read_bytes()
            assert content[:8]==b'\x89PNG\r\n\x1a\n' and list(struct.unpack('>II',content[16:24]))==image['dimensions']
    # Offline adverse controls demonstrate that changed raw evidence cannot receive this acceptance.
    controls=[]
    def reject(label,fn):
        try: fn()
        except AssertionError: controls.append({'control':label,'expected':'REFUSE','observed':'REFUSED'}); return
        raise AssertionError('false green adverse control: '+label)
    x=deepcopy(raw[0]); x['snapshots']['fresh widget consumer']['config']['method']='4'
    reject('fresh configured preference mismatch',lambda:verify_case(x,binding,active,environment))
    x=deepcopy(raw[0]); x['builderExports'][0]['openURL']+='_drift'
    reject('builder output hash drift',lambda:verify_case(x,binding,active,environment))
    x=deepcopy(raw[5]); x['snapshots']['actual reload']['report']['seedApplied']=True
    reject('saved reload reseeding',lambda:verify_case(x,binding,active,environment))
    x=deepcopy(raw[8]); x['actualUTCContexts'][2]['afterProductionInitialization']['timeZone']='Asia/Riyadh'
    reject('actual omission timezone drift',lambda:verify_case(x,binding,active,environment))
    x=deepcopy(raw[8]); x['error']['code']='TYPE_ERROR'
    reject('nonsemantic mutant failure',lambda:verify_case(x,binding,active,environment))
    x=deepcopy(raw[0]); x['sourceRef']='historical-e718'
    reject('historical source substituted',lambda:verify_case(x,binding,active,environment))
    return {'schema':'r0010-independent-return-verification/1','atUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'PASS','packetMembersVerified':sizes,'referencesVerified':refs,'sourceHead':HEAD,'runtimeSha256':RUNTIME,'runtimeFiles':135,'outputFiles':len(actual_inventory),'pngFiles':sum(p.endswith('.png') for p in actual_inventory),'rows':rows,'adverseControls':controls,'custody':{'nodeIssueEffectValuesUnchanged':True,'knownExit':0,'before':'FREE','during':'ACTIVE','after':'FREE','leaseId':dispatch['leaseId'],'inheritedNonoperativeProjection':inherited},'nativeEffectsByReviewer':False,'nodeComplete':False}

if __name__=='__main__':
    try:
        result=main()
        with (W/'VERIFICATION.json').open('xb') as f: f.write((json.dumps(result,indent=2)+'\n').encode())
        print(json.dumps({'status':result['status'],'cases':len(result['rows']),'files':result['outputFiles'],'png':result['pngFiles'],'adverseControls':len(result['adverseControls'])}))
    except BaseException:
        diagnostic=W/'DIAGNOSTIC.json'
        if diagnostic.exists(): diagnostic=W/('DIAGNOSTIC-'+dt.datetime.now(dt.timezone.utc).strftime('%H%M%S%f')+'.json')
        with diagnostic.open('xb') as f: f.write((json.dumps({'status':'REVIEW_PREPARATION_ERROR','trace':traceback.format_exc(),'nativeEffects':False},indent=2)+'\n').encode())
        raise
