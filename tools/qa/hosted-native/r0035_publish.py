"""One explicit R0035 publish-decision observation, preserving original science.

No browser is imported here. Common preparation and original assessment replay
are reused as pinned source. A complete merged source identity accompanies every
preparation, canonical plan, producer, entry and terminal intake.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import r0035_psf as original_support

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
KIND='derived-r0035-publish-decision/1'
IDENTITY='r0035-publish-native-source/1'
ADMISSION='r0035-publish-current-admission/1'
OBSERVED='OBSERVED_PUBLISH_DIAGNOSTIC'
TIMING='original-publish-decision-observation'
LANE='r0035-chromium-publish'
ARMS=('main','unmodified','mitigated')
LIVE='tools/r0035/live_lab.mjs'
CONTROLS={'guard':'off','scope':'all','mode':'timing'}
DRIVER_ARGS=['--engine','chromium','--rounds','1','--seconds','15','--clock','ordinary','--scene','dark','--motion','normal']
CHILD_SECONDS=540
READMISSION_SECONDS=120
INTAKE_SECONDS=30
POST_SECONDS=150
LANE_SECONDS=885
PREPARATION_SECONDS=1350
ADAPTER={'protocol':'r0035-publish-explicit-driver-adapter/1',
         'interceptions':['private-module-check_plan','private-module-trial-route-and-custody'],
         'scientificPredicates':'original-source-functions-unmodified',
         'originalOperationalDriverUnchanged':False,'newNativeCalls':0,
         'observerOverhead':'UNCALIBRATED','cpuTiming':'NOT_MEASURED'}
need=original_support.need
same=original_support.same
record=original_support.record
load=original_support.load
save=original_support.save
inventory=original_support.inventory
population_digest=original_support.population_digest
success=original_support.success
run_process=original_support.run_process
runtime_authority=original_support.runtime_authority
original_plan=original_support.original_plan


def mode(enabled,selected,stars,engine,*,psf=False,stages=False,costs=False,retained=False,r002f=False,
         moon='published',rain='options',matrix=None,r002f_route='offscreen'):
    need(type(enabled) is bool,'publish selector must be boolean')
    if enabled:
        need(selected==['R0035'] and engine=='chromium' and same(stars,CONTROLS)
             and psf is False and stages is False and costs is False and retained is False and r002f is False
             and moon=='published' and rain=='options' and matrix is None and r002f_route=='offscreen',
             'publish requires only fixed Chromium full-population guard-off original timing')
    return enabled


def budget():
    # 1350 preparation +120 outer readmission +885 namespace =2355.
    # Original 2640/2700 envelope stays intact, with no added original wait.
    return {'coordinatorSeconds':2640,'workflowObservationMinutes':45}


def source_files():
    # The composed shared caller closure already includes both imported BF and
    # autoattach modules. Their own selectors remain inactive for this route.
    import r002f_bfcache_central as composed
    names=['r0035_publish.py','observe_r0035_publish.py','r0035_publish_io.mjs',
           'r0035_publish_controls.py','r0035_publish_io_controls.cjs','r0035-publish-pins.json','R0035_PUBLISH.md',
           'observe_r0035_psf.py','r0035-stage-pins.json','r0035-psf-native-pins.json','r0035_psf_transform.mjs',
           'test_capture_pipeline.py','test_envelope.py','r0035_psf_controls.py']
    extra=['tools/r0035/publish_diagnostic.mjs','tools/r0035/publish_diagnostic_controls.cjs',
           'tools/r0035/live_lab.mjs','tools/r0035/frame_guard.mjs','tools/r0035/sample_history.mjs',
           'tools/r0035/changed_rectangles.mjs','tools/r0035/psf_within_call.mjs','real-sky/native-contract.mjs']
    return sorted(set(composed.source_files()+['tools/qa/hosted-native/'+name for name in names]+extra))


def producer_source_files():
    return [os.path.relpath(ROOT/name,HERE) for name in source_files()]


def source_identity():
    import prepare
    def git(*args):
        return subprocess.run(['git','-C',str(ROOT),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              timeout=10,env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='')).stdout.decode().strip()
    need(not git('status','--porcelain'),'complete publish orchestration source is not clean')
    names=source_files();manifest=load(HERE/'r0035-publish-pins.json')
    need(manifest.get('protocol')=='r0035-publish-source-closure/1' and manifest.get('sourceFiles')==names
         and manifest.get('scientificBodiesChanged') is False and same(manifest.get('budget'),budget()),
         'declared complete publish source closure differs')
    # Check actual bytes against Git blobs, including sparse/skip-worktree files.
    files=prepare.checked_files(ROOT,names)
    need(set(files)==set(names),'publish source closure has unknown or missing members')
    for name,digest in manifest['original'].items():
        need(name in files and files[name]['sha256']==digest,'pinned original/helper source changed: '+name)
    return {'protocol':'r0035-publish-current-source/1','root':str(ROOT),'commit':git('rev-parse','HEAD'),
            'tree':git('rev-parse','HEAD^{tree}'),'clean':True,'files':files}


def paths(task):
    task=Path(task).absolute()
    need(task!=Path('/') and '..' not in task.parts and task.resolve()==task
         and not any(p.is_symlink() for p in (task,*task.parents)),'literal nonaliased publish task required')
    folder=task/'capture/r0035-publish-preparation'
    return {'task':task,'folder':folder,'prepared':task/'work/prepared/receipts/prepared.json',
            'commonProcess':task/'capture/preparation-process.json','commonContext':task/'capture/preparation-context.json',
            'entry':task/'capture/r0035-publish-preparation-entry.json','identity':folder/'identity.json',
            'referencePlan':folder/'reference-plan.json','derivedPlan':folder/'derived-plan.json',
            'candidate':task/'work/r0035-publish','transformProcess':folder/'transform-process.json'}


def check_delta(before,after):
    need(set(after)==set(before) and {name for name in before if not same(before[name],after[name])}=={LIVE},
         'publish derived population must change exactly the original live lab and no member count')


def owned_population(root,protected):
    before=inventory(protected);after=inventory(root)
    original_inodes=set()
    for name in before:
        stat=(Path(protected)/name).stat();original_inodes.add((stat.st_dev,stat.st_ino))
    for name in after:
        stat=(Path(root)/name).stat()
        need(stat.st_nlink==1 and (stat.st_dev,stat.st_ino) not in original_inodes,
             'publish candidate member aliases original or another hardlink')
    return after


def derived_plan(reference,root,identity):
    value=copy.deepcopy(reference);value['kind']=KIND
    for name in ('unmodified','mitigated'):value['arms'][name]['root']=str(root)
    value['publishDiagnostic']={'protocol':IDENTITY,'identity':identity};return value


def transform_argv(runtime,mode_name,base,candidate):
    return [runtime['node'],str(HERE/'r0035_publish_io.mjs'),mode_name,str(base),str(candidate)]


def prepare_argv(task,runtime):
    return [runtime['python'],'-B',str(HERE/'r0035_publish.py'),'prepare','--task',str(Path(task).absolute())]


def prepare_source(task,runtime):
    sources=source_identity();p=paths(task)
    for key in ('folder','candidate','entry'):
        target=p[key];need(not target.exists() and not target.is_symlink()
                          and not any(q.is_symlink() for q in target.parents),'fresh regular publish preparation required')
    prepared,current=original_support.common_current(task,runtime)
    base=Path(prepared['trees']['r0035']['root']);reference=original_plan(prepared)
    import r0035_stage_materialize as original
    driver=original.support().load_driver(Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py')
    original.original_plan(driver,reference)
    need(all(p['candidate']!=Path(r['root']) and Path(r['root']) not in p['candidate'].parents
             and p['candidate'] not in Path(r['root']).parents for group in ('sources','trees') for r in prepared[group].values()),
         'publish candidate must be separate from every original source and generated tree')
    p['folder'].mkdir(mode=0o700)
    partial={'protocol':IDENTITY,'status':'INCOMPLETE','nativeStatus':'NOT_RUN','baseRoot':str(base),'root':str(p['candidate'])}
    try:
        save(p['referencePlan'],reference);shutil.copytree(base,p['candidate'],copy_function=shutil.copy2)
        need(same(owned_population(p['candidate'],base),current['referenceFiles']),'publish copy differs before transformation')
        child=run_process(transform_argv(runtime,'derive',base,p['candidate']),30)
        save(p['transformProcess'],child);success(child,'publish exact transform',30)
        transform=json.loads(child['stdout']);need(transform.get('protocol')=='r0035-publish-file-transform/1','publish transform terminal differs')
        after=owned_population(p['candidate'],base);check_delta(current['referenceFiles'],after)
        need(same(inventory(base),current['referenceFiles']) and same(source_identity(),sources),
             'original or merged source changed during publish derivation')
        identity={**partial,'status':'PREPARED','sources':sources,'runtime':current['runtime'],
                  'runtimeReceipt':current['runtimeReceipt'],'common':current['common'],'originalSources':current['sources'],
                  'referenceFiles':current['referenceFiles'],'derivedFiles':after,'transform':transform,
                  'transformProcess':record(p['transformProcess']),'referencePlan':reference,
                  'referencePlanRecord':record(p['referencePlan']),'originalLabIdentity':record(base/'r0035-lab-identity.json'),
                  'adapter':ADAPTER,'speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}
        save(p['identity'],identity);save(p['derivedPlan'],derived_plan(reference,p['candidate'],record(p['identity'])))
        return identity
    except BaseException as error:
        save(p['folder']/'failure.json',{**partial,'error':{'type':type(error).__name__,'message':str(error)}});raise


def preparation_entry(task,runtime,process):
    value={**process,'protocol':'r0035-publish-preparation-entry/1','argv':prepare_argv(task,runtime),
           'cwd':str(HERE),'timeoutSeconds':240,'sources':source_identity()}
    save(paths(task)['entry'],value);return value


def entry_custody(task,runtime):
    p=paths(task);runtime_authority(task,runtime);entry=load(p['entry'])
    need(entry.get('protocol')=='r0035-publish-preparation-entry/1' and entry.get('argv')==prepare_argv(task,runtime)
         and entry.get('cwd')==str(HERE) and type(entry.get('timeoutSeconds')) is int and entry['timeoutSeconds']==240
         and same(entry.get('sources'),source_identity()),'publish actual preparation entry differs')
    success(entry,'publish preparation entry',240)
    transform=load(p['transformProcess']);base=Path(load(p['prepared'])['trees']['r0035']['root'])
    need(transform.get('argv')==transform_argv(runtime,'derive',base,p['candidate']) and transform.get('cwd')==str(HERE)
         and type(transform.get('timeoutSeconds')) is int and transform['timeoutSeconds']==30,
         'publish actual preparation Node, roots or bound differs')
    success(transform,'publish preparation Node',30)
    need((p['task']/'capture/r0035-publish-preparation.stdout').read_text().strip()=='PUBLISH SOURCE PREPARED; native NOT_RUN',
         'publish actual preparation terminal output differs')
    return {'entry':record(p['entry']),'streams':{name:record(p['task']/'capture'/('r0035-publish-preparation.'+name)) for name in ('stdout','stderr')}}


def candidate_files(task,runtime,identity=None):
    p=paths(task);identity=load(p['identity']) if identity is None else identity
    need(identity.get('protocol')==IDENTITY and identity.get('status')=='PREPARED' and identity.get('nativeStatus')=='NOT_RUN'
         and same(identity.get('adapter'),ADAPTER),'exact prepared publish identity required')
    base=Path(identity['baseRoot'])
    need(identity['root']==str(p['candidate']) and same(inventory(base),identity['referenceFiles'])
         and same(owned_population(p['candidate'],base),identity['derivedFiles']),'complete original/derived publish population changed')
    check_delta(identity['referenceFiles'],identity['derivedFiles'])
    need(same(record(base/'r0035-lab-identity.json'),identity['originalLabIdentity']),'original lab receipt changed')
    child=run_process(transform_argv(runtime,'check',base,p['candidate']),30);success(child,'publish actual inverse/source check',30)
    need(same(json.loads(child['stdout']),identity['transform']),'publish actual inverse/source output differs')
    return identity,child


def current_admission(task,runtime,native=False):
    sources=source_identity();p=paths(task);entry=entry_custody(task,runtime)
    prepared,current=original_support.common_current(task,runtime,native=native)
    identity,check=candidate_files(task,runtime)
    need(identity['baseRoot']==prepared['trees']['r0035']['root'] and same(identity['referencePlan'],original_plan(prepared))
         and same(identity['referenceFiles'],current['referenceFiles']) and same(identity['sources'],sources)
         and same(identity['runtime'],current['runtime']) and same(identity['runtimeReceipt'],current['runtimeReceipt'])
         and same(identity['common'],current['common']) and same(identity['originalSources'],current['sources']),
         'publish complete current source/preparation/runtime binding differs')
    need(same(record(p['referencePlan']),identity['referencePlanRecord']) and same(load(p['referencePlan']),identity['referencePlan'])
         and same(load(p['derivedPlan']),derived_plan(identity['referencePlan'],p['candidate'],record(p['identity']))),
         'publish canonical original/derived plans differ')
    transform=load(p['transformProcess']);success(transform,'publish actual transform process',30)
    need(same(json.loads(transform['stdout']),identity['transform']) and same(record(p['transformProcess']),identity['transformProcess']),
         'publish actual transform bytes or terminal output differs')
    import r0035_stage_materialize as original
    driver_path=Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py'
    original.original_plan(original.support().load_driver(driver_path),identity['referencePlan'])
    return {'protocol':ADMISSION,'status':'PASS','task':str(p['task']),'sources':sources,
            'runtime':current['runtime'],'runtimeReceipt':current['runtimeReceipt'],'identity':record(p['identity']),
            'entry':entry,'transformProcess':record(p['transformProcess']),'referencePlan':record(p['referencePlan']),
            'derivedPlan':record(p['derivedPlan']),'baseRoot':identity['baseRoot'],'root':identity['root'],'driver':str(driver_path),
            'referencePopulation':{'files':len(identity['referenceFiles']),'sha256':population_digest(identity['referenceFiles'])},
            'derivedPopulation':{'files':len(identity['derivedFiles']),'sha256':population_digest(identity['derivedFiles'])},
            'experiment':identity['transform']['identity'],'common':current['common'],'originalSources':current['sources'],
            'adapter':ADAPTER,'nativePreparation':load(p['commonContext'])['nativeIsolationClaim'],
            'nativeQualification':'NOT_RUN','speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}


def readmit_argv(task,runtime,native=False):
    return [runtime['python'],'-B',str(HERE/'r0035_publish.py'),'readmit','--task',str(Path(task).absolute()),*(['--native'] if native else [])]


def readmit(task,runtime,native=False):
    return run_process(readmit_argv(task,runtime,native),READMISSION_SECONDS)


def admitted_process(process,task,runtime,native=False):
    success(process,'publish current source readmission',READMISSION_SECONDS)
    need(process.get('argv')==readmit_argv(task,runtime,native) and process.get('cwd')==str(HERE)
         and type(process.get('timeoutSeconds')) is int and process['timeoutSeconds']==READMISSION_SECONDS,
         'publish actual readmission executable, task, cwd or bound differs')
    value=json.loads(process['stdout'])
    need(value.get('protocol')==ADMISSION and value.get('status')=='PASS' and value.get('task')==str(Path(task).absolute())
         and same(value.get('runtime'),runtime_authority(task,runtime)) and (not native or value.get('nativePreparation') is True),
         'publish actual current source terminal record differs')
    return value


def make_plan(prepared,out,runtime,admission):
    out=Path(out).absolute();task=out.parent.parent;p=paths(task)
    need(out==task/'capture/lanes','canonical publish plan output required')
    target=out/LANE;evidence=out/(LANE+'-custody');reference=original_plan(prepared)
    original=[runtime['python'],str(Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py'),
              str(p['derivedPlan']),str(target),*DRIVER_ARGS]
    ready=admission.get('status')=='PASS'
    lane={'id':LANE,'workOrder':'R0035','engine':'chromium','dpr':1,'cwd':prepared['sources']['research']['root'],
          'env':{'NODE_PATH':runtime['modules']},'output':str(target),'stdout':str(out/(LANE+'.stdout')),'stderr':str(out/(LANE+'.stderr')),
          'argv':[runtime['python'],str(HERE/'observe_r0035_publish.py'),'--task',str(task),
                  '--preadmission',str(task/'capture/r0035-publish-preadmission.json'),'--evidence',str(evidence),'--',*original[2:]] if ready else [],
          'timeoutSeconds':CHILD_SECONDS,'preObservationCheckSeconds':READMISSION_SECONDS,'postObservationCheckSeconds':POST_SECONDS,
          'namespaceSeconds':LANE_SECONDS,'preparation':admission,'dependsOn':[],'stopScopeOnAndon':'R0035','stopAllOnExit':[86],
          'result':{'kind':'r0035-trials','path':str(target/'summary.json'),'expectedRows':3,'expectedArms':list(ARMS),
                    'capture':False,'requiresEveryRowAdmitted':True,'publishDriverPath':str(evidence/'driver.json')},
          'publishObservation':{'protocol':'r0035-publish-diagnostic/1','timingClass':TIMING},
          'exitStatuses':{'0':OBSERVED,'1':'INCOMPLETE','86':'EXTERNAL_CONTINUATION_VETOED'},
          'evidenceRetention':{'instrumented':True,'output':str(evidence),'originalArgv':original,'adapter':ADAPTER,
                               'timingComparableToOriginal':False,'overhead':'Uncalibrated original-condition bookkeeping and explicit route/trial custody; no new native calls.'}}
    return {'protocol':'salah-hosted-native-lanes/1','sequential':True,'workOrders':['R0035'],'evidenceRetention':False,
            'r0035Controls':dict(CONTROLS),'r0035Stages':False,'r0035Costs':False,'r0035Psf':False,'r0035Publish':True,
            'r003fHarness':'published','r0040Mode':'options','r0035PlanPath':str(out/'r0035-plan.json'),'r0035Plan':reference,
            'preparedReceipt':{'path':str(p['prepared']),'sha256':record(p['prepared'])['sha256']},
            'publishSources':admission.get('sources'),'lanes':[lane]}


def admit_plan(plan,task,runtime,native=False,retain=None):
    authority=runtime_authority(task,runtime)
    need(type(plan) is dict and type(plan.get('lanes')) is list and len(plan['lanes'])==1,'one complete publish dispatch required')
    row=plan['lanes'][0];need(type(row) is dict and type(row.get('preparation')) is dict,'publish lane preparation required')
    if row['preparation'].get('status')=='PASS':
        need(type(row.get('argv')) is list and row['argv'] and row['argv'][0]==runtime['python']
             and row.get('evidenceRetention',{}).get('originalArgv',[None])[0]==runtime['python'],'publish executable differs from acquired runtime')
        need(same(row.get('env'),{'NODE_PATH':runtime['modules']}) and same(row['preparation'].get('runtime'),authority),
             'publish copied runtime or package environment differs from acquired authority')
    else:need(row['preparation'].get('status')=='INCOMPLETE' and row.get('argv')==[],'unprepared publish route cannot execute substitute code')
    process=readmit(task,runtime,native)
    if retain is not None:save(retain,process)
    admission=admitted_process(process,task,runtime,native)
    expected=make_plan(load(paths(task)['prepared']),Path(task)/'capture/lanes',runtime,admission)
    need(same(plan,expected),'complete canonical publish plan, source closure or argv differs');return expected['lanes']


def lane_selected(lane):
    return type(lane) is dict and type(lane.get('publishObservation')) is dict and lane['publishObservation'].get('protocol')=='r0035-publish-diagnostic/1'


def intake(task,runtime):
    sources=source_identity();runtime_authority(task,runtime);p=paths(task)
    target=p['task']/'capture/lanes'/LANE;evidence=target.with_name(LANE+'-custody');final=load(evidence/'driver.json')
    need(final.get('protocol')=='r0035-publish-adapted-driver/1' and final.get('status')=='DRIVER_RETURNED'
         and type(final.get('adapterCalls')) is int and final['adapterCalls']==1
         and type(final.get('trialCalls')) is int and final['trialCalls']==3 and same(final.get('adapter'),ADAPTER)
         and final.get('errors')==[] and final.get('originalException') is None and final.get('continuationVeto') is None
         and final.get('actualPython')==runtime['python'] and same(final.get('sources'),sources)
         and final.get('nativeQualification')=='UNCHANGED_ORIGINAL_REPORT_ONLY'
         and final.get('speed')=='NOT_ESTABLISHED' and final.get('humanAcceptance')=='OUTSTANDING',
         'complete explicit publish adapter terminal receipt required')
    pre=p['task']/'capture/r0035-publish-preadmission.json';post=p['task']/'capture/r0035-publish-postadmission.json'
    need(same(final['preadmission'],record(pre)),'publish actual preadmission receipt differs')
    before=admitted_process(load(pre),task,runtime,True);after=admitted_process(load(post),task,runtime,True)
    need(same(before,after) and same(final.get('sourceAdmission'),before) and same(before.get('sources'),sources),
         'publish actual complete pre/post source admission differs')
    plan=load(p['derivedPlan']);expected=[runtime['python'],before['driver'],str(p['derivedPlan']),str(target),*DRIVER_ARGS]
    need(final.get('actualOriginalArgv')==expected and same(load(target/'plan.json'),plan),
         'publish original operational arguments or retained plan differs')
    import r0035_stage_materialize as original
    import r003f_matrix_campaign as boundary
    loader=original.support();driver=loader.load_driver(Path(before['driver']))
    need(same(final.get('originalSources'),loader.verify_inputs(Path(before['driver']))),
         'publish original driver/admission/clock closure differs')
    namespace=p['task']/'capture/isolation'/LANE/'receipt.json'
    need(same(final.get('isolation'),record(namespace)),'publish actual namespace custody differs')
    loader.verify_isolation(namespace);boundary.original_isolation(namespace)
    need(set(inventory(target))=={'plan.json','summary.json',*[f'01-{arm}/trial.json' for arm in ARMS]},
         'publish original report population has missing or extra members')
    receipts=final.get('trials');need(type(receipts) is list and len(receipts)==3,'publish ordered original trial population differs')
    rows=[];reports=[];bodies=[];versions=[]
    original_hashes={name:original.pins()['files']['tools/r0035/'+name]['sha256']
                     for name in ('native_trials.py','trial_admission.py','trial_clock.js')}
    for ordinal,label in enumerate(ARMS,1):
        trial_path=target/f'01-{label}/trial.json';receipt_path=evidence/f'trial-{ordinal:03}-{label}.json'
        need(same(receipts[ordinal-1],{'ordinal':ordinal,'arm':label,'receipt':record(receipt_path)}),
             'publish exact ordered arm custody differs')
        custody=load(receipt_path);body=load(trial_path)
        need(custody.get('protocol')=='r0035-publish-adapted-trial/1' and type(custody.get('ordinal')) is int
             and custody['ordinal']==ordinal and custody.get('arm')==label and custody.get('engine')=='chromium'
             and custody.get('browserVersion')==body.get('version') and same(custody.get('sourceArm'),plan['arms'][label])
             and custody.get('originalOutput')==str(trial_path.parent) and type(custody.get('pages')) is int
             and custody['pages']==1 and custody.get('catchAllRoute') is True and custody.get('contextClosed') is True
             and not any(custody.get(k) for k in ('originalException','unwinding','closeError','continuationVeto','abortError'))
             and same(custody.get('originalReport'),record(trial_path)),'publish actual trial, source or cleanup custody differs')
        options={'viewport':{'width':360,'height':570},'device_scale_factor':1,'timezone_id':'UTC',
                 'reduced_motion':'no-preference','service_workers':'block'}
        need(same(custody.get('contextOptions'),options),'publish original native viewport/DPR or context differs')
        required={'plan':str(p['derivedPlan']),'output':str(target),'engine':'chromium','clock':'ordinary','rounds':1,
                  'seconds':15,'warmup':5,'scene':'dark','motion':'normal','utc':'2026-11-09T00:00:00Z',
                  'capture':False,'observe_producer':True,'scope':KIND,'driver_sha256':original_hashes,
                  'scene_inputs':[-91,-20,'&simWx=0&simCloud=0','']}
        need(same(custody.get('originalArguments'),required) and same(body.get('driverSha256'),original_hashes),
             'publish original measured arguments or helper hashes differ')
        rows.append(original_support.replay_trial(driver,body,plan['arms'][label],label,KIND));bodies.append(body)
        reports.append({'arm':label,'report':record(trial_path),'receipt':record(receipt_path)});versions.append(body['version'])
    need(set(inventory(evidence))=={'driver.json',*[f'trial-{i:03}-{arm}.json' for i,arm in enumerate(ARMS,1)]},
         'publish custody population has missing or extra members')
    need(len(set(versions))==1 and same(load(target/'summary.json'),rows)
         and same(final['originalSummary'],record(target/'summary.json')),
         'publish browser identity or complete original assessment replay differs')
    checked=run_process([runtime['node'],str(HERE/'r0035_publish_io.mjs'),'inspect'],10,bodies)
    history_process=p['task']/'capture/r0035-publish-history-process.json'
    save(history_process,{**checked,'inputReports':[row['report'] for row in reports]})
    success(checked,'publish complete owner-history inspection',10);history=json.loads(checked['stdout'])
    need(history.get('protocol')=='r0035-publish-history-intake/1' and history.get('status')=='COMPLETE'
         and history.get('nativeQualification')=='UNCHANGED_ORIGINAL_REPORT_ONLY'
         and history.get('cpuTiming')=='NOT_MEASURED' and history.get('speed')=='NOT_ESTABLISHED'
         and history.get('humanAcceptance')=='OUTSTANDING','publish supplemental history terminal record differs')
    status='FAIL' if any(x['qualification']['verdict']=='failed' for x in rows) else 'PASS' if all(x['admitted'] is True for x in rows) else 'INCOMPLETE'
    return {'protocol':'r0035-publish-original-intake/1','status':'COMPLETE','originalStatus':status,
            'sourceAdmission':before,'driver':record(evidence/'driver.json'),'summary':record(target/'summary.json'),
            'trials':reports,'browserVersion':versions[0],'runtime':before['runtime'],'history':history,
            'historyProcess':record(history_process),'timingClass':TIMING,'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY',
            'speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}


def post_observation(lane,returncode,timed_out):
    result={'status':'INCOMPLETE'};task=Path(lane['output']).parents[2]
    try:
        runtime=load(task/'runtime.json')
        need(type(returncode) is int and returncode==0 and timed_out is False,'publish actual adapted child did not finish normally')
        current=readmit(task,runtime,True);save(task/'capture/r0035-publish-postadmission.json',current)
        result['currentSourceProcess']=current
        result['currentSourceRecord']=record(task/'capture/r0035-publish-postadmission.json')
        admission=admitted_process(current,task,runtime,True)
        need(same(admission,lane['preparation']),'publish complete source changed after planned native observation')
        checked=run_process([runtime['python'],'-B',str(HERE/'r0035_publish.py'),'intake','--task',str(task),'--native'],INTAKE_SECONDS)
        save(task/'capture/r0035-publish-intake.json',checked);result['intakeProcess']=checked
        result['intakeRecord']=record(task/'capture/r0035-publish-intake.json')
        success(checked,'publish original report and owner-history intake',INTAKE_SECONDS);body=json.loads(checked['stdout'])
        need(body.get('protocol')=='r0035-publish-original-intake/1' and body.get('status')=='COMPLETE'
             and same(body.get('sourceAdmission'),admission),'publish actual intake source/terminal record differs')
        result.update(status='COMPLETE',intake=body)
    except (OSError,ValueError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:result['reason']=str(error)
    return result


def complete_supplement(lane,value,original_status):
    if type(value) is not dict:return False
    body=value.get('intake',{})
    if type(body) is not dict:return False
    history=body.get('history',{})
    if type(history) is not dict:return False
    return (value.get('status')=='COMPLETE' and body.get('protocol')=='r0035-publish-original-intake/1'
            and body.get('status')=='COMPLETE' and body.get('originalStatus')==original_status
            and same(body.get('sourceAdmission'),lane.get('preparation'))
            and history.get('protocol')=='r0035-publish-history-intake/1' and history.get('status')=='COMPLETE'
            and body.get('speed')=='NOT_ESTABLISHED' and body.get('humanAcceptance')=='OUTSTANDING')


def retained_supplement(task,runtime,lane,value):
    """Read literal retained files; a copied supplemental body is insufficient."""
    p=paths(task);capture=p['task']/'capture';body=value['intake']
    need(complete_supplement(lane,value,body.get('originalStatus')),'complete publish supplemental shape differs')
    for phase in ('outer','pre','post'):
        path=capture/('r0035-publish-'+('outer-admission' if phase=='outer' else phase+'admission')+'.json')
        process=load(path);admission=admitted_process(process,task,runtime,True)
        need(same(admission,lane['preparation']),'actual retained publish source admission differs')
        if phase=='post':
            need(same(record(path),value.get('currentSourceRecord'))
                 and same(process,value.get('currentSourceProcess')),'actual retained post-currentness process differs')
    checked_path=capture/'r0035-publish-intake.json';checked=load(checked_path)
    need(same(record(checked_path),value.get('intakeRecord')) and same(checked,value.get('intakeProcess')),
         'actual retained publish intake process differs')
    success(checked,'retained publish intake',INTAKE_SECONDS)
    need(checked.get('argv')==[runtime['python'],'-B',str(HERE/'r0035_publish.py'),'intake','--task',str(p['task']),'--native']
         and checked.get('cwd')==str(HERE) and type(checked.get('timeoutSeconds')) is int
         and checked['timeoutSeconds']==INTAKE_SECONDS and same(json.loads(checked['stdout']),body),
         'actual retained intake executable, bound or terminal bytes differ')
    target=capture/'lanes'/LANE;evidence=target.with_name(LANE+'-custody')
    need(same(body.get('driver'),record(evidence/'driver.json')) and same(body.get('summary'),record(target/'summary.json')),
         'actual retained original driver or summary bytes differ')
    expected=[{'arm':arm,'report':record(target/f'01-{arm}/trial.json'),
               'receipt':record(evidence/f'trial-{i:03}-{arm}.json')} for i,arm in enumerate(ARMS,1)]
    need(same(body.get('trials'),expected),'actual retained ordered original trials or custody differ')
    history_path=capture/'r0035-publish-history-process.json';history=load(history_path)
    need(same(body.get('historyProcess'),record(history_path)),'actual retained owner-history process bytes differ')
    success(history,'retained owner-history inspection',10)
    need(history.get('argv')==[runtime['node'],str(HERE/'r0035_publish_io.mjs'),'inspect']
         and history.get('cwd')==str(HERE) and type(history.get('timeoutSeconds')) is int and history['timeoutSeconds']==10
         and same(history.get('inputReports'),[row['report'] for row in expected])
         and same(json.loads(history['stdout']),body.get('history')),
         'actual retained history executable, source reports or terminal bytes differ')
    final=load(evidence/'driver.json')
    need(same(final.get('preadmission'),record(capture/'r0035-publish-preadmission.json'))
         and same(final.get('sourceAdmission'),lane['preparation']),
         'actual retained driver preadmission differs')


def classify(lane,original,supplement,returncode,timed_out):
    status=original['status']
    if status=='PASS':
        status=OBSERVED if type(returncode) is int and returncode==0 and timed_out is False and complete_supplement(lane,supplement,'PASS') else 'INCOMPLETE'
    return {**original,'status':status,'originalStatus':original['status'],'publishObservation':supplement,
            'timingClass':TIMING,'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY',
            'speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}


def namespace_admitted(lane,inner):
    if inner.get('status')==OBSERVED:
        return (lane_selected(lane) and type(inner.get('returncode')) is int and inner['returncode']==0
                and inner.get('timedOut') is False and inner.get('originalStatus')=='PASS'
                and complete_supplement(lane,inner.get('publishObservation'),'PASS') and inner.get('timingClass')==TIMING
                and inner.get('nativeQualification')=='UNCHANGED_ORIGINAL_REPORT_ONLY'
                and inner.get('speed')=='NOT_ESTABLISHED' and inner.get('humanAcceptance')=='OUTSTANDING')
    return not (lane_selected(lane) and inner.get('status')=='PASS')


def producer_gate(campaign,plan,body,task):
    selected=campaign.get('r0035Publish',False);need(type(selected) is bool,'publish producer selector must be boolean')
    rows=body['lanes']
    if not selected:
        need(not any(row.get('status')==OBSERVED or 'publishObservation' in row for row in rows)
             and plan.get('r0035Publish',False) is False and body.get('r0035Publish',False) is False,
             'publish producer claim requires its explicit campaign')
        return None
    mode(selected,campaign.get('workOrders'),campaign.get('r0035'),campaign.get('engine'),
         psf=campaign.get('r0035Psf',False),stages=campaign.get('r0035Stages',False),costs=campaign.get('r0035Costs',False),
         retained=campaign.get('evidenceRetention',False),r002f=campaign.get('r002f',{}).get('enabled',False),
         moon=campaign.get('r003fHarness','published'),rain=campaign.get('r0040Mode','options'),
         matrix=campaign.get('r003fMatrix'),r002f_route=campaign.get('r002fRoute','offscreen'))
    need(body.get('r0035Publish') is True and type(rows) is list and len(rows)==1
         and type(plan.get('lanes')) is list and len(plan['lanes'])==1,'one complete publish producer population required')
    lane=plan['lanes'][0];runtime=load(Path(task)/'runtime.json');runtime_authority(task,runtime)
    canonical=make_plan(load(paths(task)['prepared']),Path(task)/'capture/lanes',runtime,lane['preparation'])
    need(same(plan,canonical),'publish complete producer plan differs from canonical actual runtime/task')
    if lane['preparation'].get('status')=='PASS':
        need(same(source_identity(),lane['preparation'].get('sources')),'publish complete source closure changed before producer gate')
    row=rows[0];need(row.get('id')==LANE,'publish producer lane identity differs')
    if row.get('status')=='NOT_RUN':
        need(not (Path(task)/'capture/lanes'/(LANE+'-custody')/'driver.json').exists(),
             'publish no-dispatch result has actual driver custody')
        return False
    need(namespace_admitted(lane,row),'publish producer namespace/supplement binding differs')
    inner_path=Path(task)/'capture/lane-status'/(LANE+'.json')
    inner=load(inner_path) if inner_path.exists() else None
    need(same(row.get('innerStatus'),inner),'actual retained publish inner status file differs')
    import observe
    actual=observe.namespace_status(lane,row.get('namespaceProcess'),inner)
    need(all(same(row.get(key),value) for key,value in actual.items()),'actual publish namespace disposition differs')
    if inner is None:return False
    fields=('id','status','returncode','timedOut','originalStatus','publishObservation','timingClass','nativeQualification','speed','humanAcceptance')
    need(all(same(inner.get(key),row.get(key)) for key in fields),'publish full inner/outer terminal equality differs')
    supplement=row.get('publishObservation',{})
    if supplement.get('status')=='COMPLETE':
        need(complete_supplement(lane,supplement,row.get('originalStatus')),'publish complete supplemental source or original status differs')
        retained_supplement(task,runtime,lane,supplement)
    if row.get('status')!=OBSERVED:return False
    outer=row.get('namespaceProcess',{})
    need(type(outer.get('returncode')) is int and outer['returncode']==0 and outer.get('timedOut') is False
         and row.get('stopAll') is False,'publish actual namespace process did not complete normally')
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('prepare','readmit','intake'))
    parser.add_argument('--task',type=Path,required=True);parser.add_argument('--native',action='store_true');args=parser.parse_args()
    os.umask(0o077);runtime=load(args.task/'runtime.json');need(runtime.get('python')==sys.executable,'actual publish Python differs from acquired runtime')
    if args.command=='prepare':prepare_source(args.task,runtime);print('PUBLISH SOURCE PREPARED; native NOT_RUN')
    elif args.command=='readmit':print(json.dumps(current_admission(args.task,runtime,args.native),allow_nan=False))
    else:print(json.dumps(intake(args.task,runtime),allow_nan=False))


if __name__=='__main__':main()
