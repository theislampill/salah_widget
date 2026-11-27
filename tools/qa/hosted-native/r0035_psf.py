"""Explicit paired PSF source, preparation, dispatch and report admission.

This module imports no browser. The original scientific admission functions
are loaded from pinned source; changed source is admitted by a distinct plan.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
KIND = 'derived-r0035-within-call-psf/1'
IDENTITY = 'r0035-psf-native-source-pair/1'
OBSERVED = 'OBSERVED_PSF_DIAGNOSTIC'
TIMING = 'paired-native-psf-adapter-diagnostic'
ROLES = ('reference','derived')
ARMS = ('main','unmodified','mitigated')
RENDERER = 'real-sky/core/src/renderer.mjs'
STELLAR = 'tools/r0035/stellar_replay.mjs'
CANDIDATE = 'tools/r0035/psf_within_call_renderer.mjs'
LAB_IDENTITY_SHA256 = 'cd516864258a819376773a177a6d50730b1f30fa3f37e6d43499009d89e6adf1'
CHILD_SECONDS = 540
READMISSION_SECONDS = 120
INTAKE_SECONDS = 30
POST_SECONDS = READMISSION_SECONDS + INTAKE_SECONDS
LANE_SECONDS = CHILD_SECONDS + READMISSION_SECONDS + POST_SECONDS + 75
PREPARATION_SECONDS = 1350
CONTROLS = {'guard':'off','scope':'all','mode':'timing'}
DRIVER_ARGS = ['--engine','chromium','--rounds','1','--seconds','15','--clock','ordinary',
               '--scene','dark','--motion','normal']
ADAPTER = {'protocol':'r0035-psf-explicit-driver-adapter/1',
           'interceptions':['private-module-check_plan','private-module-trial-route-and-custody'],
           'scientificPredicates':'original-source-functions-unmodified',
           'originalOperationalDriverUnchanged':False}


def need(condition, message):
    if not condition:raise ValueError(message)


def same(left, right):
    return json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path):
    p=Path(path).absolute()
    need(p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)), 'regular PSF source or custody file required')
    return p


def record(path):
    p=regular(path);raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}


def load(path):
    return json.loads(regular(path).read_bytes())


def save(path,value):
    p=Path(path)
    with p.open('x') as stream:
        os.chmod(p,0o600);json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def inventory(root):
    root=Path(root).absolute()
    need(root.is_dir() and not any(x.is_symlink() for x in (root,*root.parents)), 'regular PSF root required')
    result={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:
            need(not (Path(directory)/name).is_symlink(),'symlink directory in PSF population')
        for name in files:
            p=regular(Path(directory)/name);r=record(p)
            result[p.relative_to(root).as_posix()]={k:r[k] for k in ('bytes','sha256')}
    return dict(sorted(result.items()))


def population_digest(value):
    return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())


def success(value,label,seconds=None):
    need(isinstance(value,dict) and type(value.get('returncode')) is int and value['returncode']==0
         and value.get('timedOut') is False and value.get('error') is None and value.get('retentionError') is None,
         label+' actual process did not complete successfully')
    elapsed=value.get('elapsedSeconds')
    need(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0
         and (seconds is None or elapsed<=seconds),label+' actual elapsed time is missing or outside its bound')


def run_process(argv,seconds,payload=None):
    """Bound the actual process group; retain both terminal streams on failure."""
    env=dict(os.environ);env.pop('NODE_OPTIONS',None);env['PYTHONDONTWRITEBYTECODE']='1'
    started=time.monotonic();child=None
    result={'argv':list(map(str,argv)),'cwd':str(HERE),'timeoutSeconds':seconds,
            'returncode':None,'timedOut':False,'stdout':'','stderr':''}
    try:
        child=subprocess.Popen(result['argv'],cwd=HERE,env=env,stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:
            stdout,stderr=child.communicate(None if payload is None else json.dumps(payload,allow_nan=False).encode(),timeout=seconds)
        except subprocess.TimeoutExpired:
            result['timedOut']=True
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            stdout,stderr=child.communicate()
        result.update(returncode=child.returncode,stdout=stdout.decode('utf-8',errors='replace'),stderr=stderr.decode('utf-8',errors='replace'))
    except OSError as error:result['error']=str(error)
    except BaseException:
        if child is not None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait()
        raise
    finally:result['elapsedSeconds']=time.monotonic()-started
    return result


def source_pins():
    # This constant belongs to the separately reviewed orchestration caller.
    from lanes import R0035_PSF_PINS
    path=HERE/'r0035-psf-native-pins.json'
    need(record(path)['sha256']==R0035_PSF_PINS,'PSF caller manifest identity differs')
    value=load(path)
    need(value.get('protocol')=='r0035-psf-native-caller-source/1','PSF source manifest protocol differs')
    for name,digest in value['files'].items():
        need(record(HERE/name)['sha256']==digest,'PSF reviewed source drift: '+name)
    return record(path)


def caller_sources():
    """Bind mergeable central seams to this genuine preparation and intake."""
    files=[HERE/name for name in ('lanes.py','observe.py','capture_pipeline.py')]
    files.append(HERE.parents[2]/'.github/workflows/research-native-pilot.yml')
    return [record(path) for path in files]


def mode(enabled,selected,stars,engine,*,stages=False,costs=False,retained=False,r002f=False,
         moon='published',rain='options',matrix=None):
    need(type(enabled) is bool,'PSF selector must be boolean')
    if enabled:
        need(selected==['R0035'] and engine=='chromium' and same(stars,CONTROLS)
             and stages is False and costs is False and retained is False and r002f is False
             and moon=='published' and rain=='options' and matrix is None,
             'PSF requires only the fixed Chromium full-population guard-off timing pair')
    return enabled


def runtime_authority(task,runtime):
    task=paths(task)['task']
    need(isinstance(runtime,dict) and same(load(task/'runtime.json'),runtime),'PSF acquired runtime differs from current task')
    for name in ('python','node','modules','playwright','pngjs'):
        need(isinstance(runtime.get(name),str) and Path(runtime[name]).is_absolute(),'absolute acquired PSF runtime required')
    need(runtime['playwright']==str(Path(runtime['modules'])/'playwright'),'PSF Playwright differs from acquired modules')
    return {name:runtime[name] for name in ('python','node','modules','playwright','pngjs')}


def paths(task):
    task=Path(task).absolute()
    need('..' not in task.parts and task.resolve()==task and not any(q.is_symlink() for q in (task,*task.parents)),
         'canonical literal PSF task without path aliases required')
    folder=task/'capture/r0035-psf-preparation'
    return {'task':task,'folder':folder,'prepared':task/'work/prepared/receipts/prepared.json',
            'commonProcess':task/'capture/preparation-process.json','commonContext':task/'capture/preparation-context.json',
            'entry':task/'capture/r0035-psf-preparation-entry.json','identity':folder/'identity.json',
            'referencePlan':folder/'reference-plan.json','derivedPlan':folder/'derived-plan.json',
            'candidate':task/'work/r0035-psf','transformProcess':folder/'transform-process.json'}


def original_plan(prepared):
    from lanes import original_star_plan
    return original_star_plan(prepared,'off','all')


def derived_plan(reference,root,identity):
    value=copy.deepcopy(reference);value['kind']=KIND
    for name in ('unmodified','mitigated'):value['arms'][name]['root']=str(root)
    value['psfDiagnostic']={'protocol':IDENTITY,'identity':identity}
    return value


def common_current(task,runtime,native=False):
    import prepare
    import r003f_matrix_campaign as common
    p=paths(task);authority=runtime_authority(task,runtime)
    prepared,custody=common.common_custody(p['prepared'],p['commonProcess'],p['commonContext'],native=native)
    context=load(p['commonContext']);process=load(p['commonProcess'])
    expected=[authority['python'],str(HERE/'prepare.py'),'--research',prepared['sources']['research']['root'],
              '--baseline',prepared['sources']['baseline']['root'],'--historical',prepared['sources']['historical']['root'],
              '--out',str(p['prepared'].parent.parent)]
    need(context['argv']==expected and context['cwd']==str(HERE),'PSF actual common executable, caller or literal task differs')
    success(process,'common preparation',900)
    need(regular(p['task']/'capture/preparation.stdout').read_text().strip()=='PREPARATION READY',
         'PSF original common preparation terminal output differs')
    custody['streams']={name:record(p['task']/'capture'/('preparation.'+name)) for name in ('stdout','stderr')}
    source_rows={}
    for label,names in (('research',(*prepare.SOURCE_DIRS,prepare.RAIN_PATCH)),
                        ('baseline',(*prepare.SOURCE_DIRS,'index.html','offline.html','config.js','builder.html','GENERATED.json'))):
        root=Path(prepared['sources'][label]['root']);actual=prepare.checked_files(root,names)
        recorded=load(p['prepared'].parent/(label+'-files.json'))
        need(same(actual,recorded),'PSF complete original source input population changed: '+label)
        source_rows[label]={'count':len(actual),'sha256':population_digest(actual)}
    # The complete served experimental population is 1004 original inputs plus
    # the five generated top-level members and original lab receipt. Generated
    # and original patched members are admitted by their original inventories.
    base=Path(prepared['trees']['r0035']['root']);base_files=inventory(base)
    research_files=load(p['prepared'].parent/'research-files.json')
    source={name:row for name,row in research_files.items() if name.split('/')[0] in prepare.SOURCE_DIRS}
    generated=load(base/'GENERATED.json')['files'];lab=load(base/'r0035-lab-identity.json')
    need(record(base/'r0035-lab-identity.json')['sha256']==LAB_IDENTITY_SHA256
         and same(load(p['prepared'].parent/'r0035-lab-identity.json'),lab),'original canonical lab receipt differs')
    expected=set(source)|set(generated)|{'GENERATED.json','r0035-lab-identity.json'}
    need(set(base_files)==expected,'PSF reference has missing or extra source/generated members')
    for name,row in source.items():
        if name not in lab['sha256'] and name not in generated:
            need(same(base_files[name],{k:row[k] for k in ('bytes','sha256')}),'PSF unmodified reference input differs: '+name)
    for name,digest in lab['sha256'].items():need(base_files[name]['sha256']==digest,'PSF original patched lab member differs: '+name)
    runtime_files=load(Path(prepared['trees']['r003f']['manifest']))
    need(same(inventory(prepared['trees']['r003f']['root']),{name:{k:row[k] for k in ('bytes','sha256')} for name,row in runtime_files.items()}),
         'PSF common original runtime population differs')
    return prepared,{'runtime':authority,'runtimeReceipt':record(p['task']/'runtime.json'),'common':custody,
                     'sources':source_rows,'referenceFiles':base_files}


def check_delta(before,after):
    need(CANDIDATE not in before and set(after)==set(before)|{CANDIDATE},'PSF derived population must add exactly one renderer')
    need({name for name in before if not same(before[name],after[name])}=={STELLAR},
         'only candidate stellar renderer import may change')


def transform_argv(runtime,mode_name,base,candidate):
    return [runtime['node'],str(HERE/'r0035_psf_transform.mjs'),mode_name,str(base),str(candidate)]


def prepare_argv(task,runtime):
    return [runtime['python'],'-B',str(HERE/'r0035_psf.py'),'prepare','--task',str(Path(task).absolute())]


def prepare_pair(task,runtime):
    source=source_pins();p=paths(task)
    for name in ('folder','candidate','entry'):
        target=p[name];need(not target.exists() and not target.is_symlink(),'fresh PSF preparation required')
        need(not any(q.is_symlink() for q in target.parents),'regular PSF preparation ancestry required')
    prepared,current=common_current(task,runtime)
    base=Path(prepared['trees']['r0035']['root']);reference=original_plan(prepared)
    import r0035_stage_materialize as original
    driver=original.support().load_driver(Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py')
    original.original_plan(driver,reference)
    need(all(p['candidate']!=Path(r['root']) and Path(r['root']) not in p['candidate'].parents
             and p['candidate'] not in Path(r['root']).parents for group in ('sources','trees') for r in prepared[group].values()),
         'separate PSF candidate and original roots required')
    p['folder'].mkdir(mode=0o700)
    partial={'protocol':IDENTITY,'status':'INCOMPLETE','nativeStatus':'NOT_RUN','baseRoot':str(base),'root':str(p['candidate'])}
    try:
        save(p['referencePlan'],reference)
        shutil.copytree(base,p['candidate'],copy_function=shutil.copy2)
        child=run_process(transform_argv(runtime,'derive',base,p['candidate']),30)
        save(p['transformProcess'],child);success(child,'PSF exact transform',30)
        transform=json.loads(child['stdout']);need(transform.get('protocol')=='r0035-psf-file-transform/1','PSF transform terminal output differs')
        after=inventory(p['candidate']);check_delta(current['referenceFiles'],after)
        need(same(inventory(base),current['referenceFiles']),'PSF original reference changed during derivation')
        identity={**partial,'status':'PREPARED','sourcePins':source,'runtime':current['runtime'],
                  'callerSources':caller_sources(),
                  'common':current['common'],'runtimeReceipt':current['runtimeReceipt'],'originalSources':current['sources'],
                  'referenceFiles':current['referenceFiles'],'derivedFiles':after,'transform':transform,
                  'transformProcess':record(p['transformProcess']),'referencePlan':reference,
                  'referencePlanRecord':record(p['referencePlan']),'originalLabIdentity':record(base/'r0035-lab-identity.json'),
                  'adapter':ADAPTER,'humanAcceptance':'OUTSTANDING'}
        save(p['identity'],identity);save(p['derivedPlan'],derived_plan(reference,p['candidate'],record(p['identity'])))
        return identity
    except BaseException as error:
        save(p['folder']/'failure.json',{**partial,'error':{'type':type(error).__name__,'message':str(error)}})
        raise


def preparation_entry(task,runtime,process):
    p=paths(task)
    value={**process,'protocol':'r0035-psf-preparation-entry/1','argv':prepare_argv(task,runtime),
           'cwd':str(HERE),'timeoutSeconds':240,'sourcePins':source_pins()}
    save(p['entry'],value);return value


def entry_custody(task,runtime):
    p=paths(task);entry=load(p['entry'])
    # Authority is checked before any receipt-driven child can be launched.
    runtime_authority(task,runtime)
    need(entry.get('protocol')=='r0035-psf-preparation-entry/1' and entry.get('argv')==prepare_argv(task,runtime)
         and entry.get('cwd')==str(HERE) and type(entry.get('timeoutSeconds')) is int and entry['timeoutSeconds']==240
         and same(entry.get('sourcePins'),source_pins()),'PSF actual preparation entry differs')
    success(entry,'PSF preparation entry',240)
    transform=load(p['transformProcess']);base=Path(load(p['prepared'])['trees']['r0035']['root'])
    need(transform.get('argv')==transform_argv(runtime,'derive',base,p['candidate'])
         and transform.get('cwd')==str(HERE) and type(transform.get('timeoutSeconds')) is int
         and transform['timeoutSeconds']==30,'PSF actual preparation Node or literal roots differ')
    success(transform,'PSF preparation Node',30)
    stdout=regular(p['task']/'capture/r0035-psf-preparation.stdout')
    need(stdout.read_text().strip()=='PSF SOURCE PAIR PREPARED; native NOT_RUN','PSF preparation terminal output differs')
    return {'entry':record(p['entry']),'streams':{name:record(p['task']/'capture'/('r0035-psf-preparation.'+name)) for name in ('stdout','stderr')}}


def pair_files(task,runtime,identity=None):
    p=paths(task);identity=load(p['identity']) if identity is None else identity
    need(identity.get('protocol')==IDENTITY and identity.get('status')=='PREPARED' and identity.get('nativeStatus')=='NOT_RUN'
         and same(identity.get('adapter'),ADAPTER),'explicit prepared PSF pair identity required')
    base=Path(identity['baseRoot'])
    need(identity['root']==str(p['candidate']) and same(inventory(base),identity['referenceFiles'])
         and same(inventory(p['candidate']),identity['derivedFiles']),'PSF complete original/derived current population differs')
    check_delta(identity['referenceFiles'],identity['derivedFiles'])
    need(same(record(base/'r0035-lab-identity.json'),identity['originalLabIdentity']),'PSF original lab identity drift')
    child=run_process(transform_argv(runtime,'check',base,p['candidate']),30)
    success(child,'PSF actual inverse check',30)
    need(same(json.loads(child['stdout']),identity['transform']),'PSF actual inverse/source-pair check differs')
    return identity,child


def current_admission(task,runtime,native=False):
    source=source_pins();p=paths(task);entry=entry_custody(task,runtime)
    prepared,current=common_current(task,runtime,native=native)
    identity,check=pair_files(task,runtime)
    need(identity['baseRoot']==prepared['trees']['r0035']['root'] and same(identity['referencePlan'],original_plan(prepared))
         and same(identity['referenceFiles'],current['referenceFiles']) and same(identity['sourcePins'],source)
         and same(identity['runtime'],current['runtime']) and same(identity['runtimeReceipt'],current['runtimeReceipt'])
         and same(identity['common'],current['common']) and same(identity['originalSources'],current['sources']),
         'PSF current preparation/source/runtime binding differs')
    need(same(identity.get('callerSources'),caller_sources()),'PSF actual central caller changed after preparation')
    need(same(record(p['referencePlan']),identity['referencePlanRecord']) and same(load(p['referencePlan']),identity['referencePlan'])
         and same(load(p['derivedPlan']),derived_plan(identity['referencePlan'],p['candidate'],record(p['identity']))),
         'PSF canonical complete pair plan differs')
    transform=load(p['transformProcess']);success(transform,'PSF actual materializer Node',30)
    need(transform['argv']==transform_argv(runtime,'derive',Path(identity['baseRoot']),p['candidate'])
         and transform['cwd']==str(HERE) and type(transform.get('timeoutSeconds')) is int and transform['timeoutSeconds']==30
         and same(json.loads(transform['stdout']),identity['transform'])
         and same(record(p['transformProcess']),identity['transformProcess']),'PSF actual transform process or terminal bytes differ')
    import r0035_stage_materialize as original
    driver_path=Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py'
    original.original_plan(original.support().load_driver(driver_path),identity['referencePlan'])
    admission={'protocol':'r0035-psf-current-admission/1','status':'PASS','task':str(p['task']),
               'sourcePins':source,'runtime':current['runtime'],'runtimeReceipt':current['runtimeReceipt'],
               'callerSources':caller_sources(),
               'identity':record(p['identity']),'entry':entry,'transformProcess':record(p['transformProcess']),
               'referencePlan':record(p['referencePlan']),'derivedPlan':record(p['derivedPlan']),
               'baseRoot':identity['baseRoot'],'root':identity['root'],'driver':str(driver_path),
               'referencePopulation':{'files':len(identity['referenceFiles']),'sha256':population_digest(identity['referenceFiles'])},
               'derivedPopulation':{'files':len(identity['derivedFiles']),'sha256':population_digest(identity['derivedFiles'])},
               'experiment':identity['transform']['identity'],'common':current['common'],'originalSources':current['sources'],
               'adapter':ADAPTER,'nativePreparation':load(p['commonContext'])['nativeIsolationClaim'],
               'nativeQualification':'NOT_RUN','humanAcceptance':'OUTSTANDING'}
    return admission


def readmit(task,runtime,native=False):
    return run_process([runtime['python'],'-B',str(HERE/'r0035_psf.py'),'readmit','--task',str(Path(task).absolute()),
                        *(['--native'] if native else [])],READMISSION_SECONDS)


def admitted_process(process,task,runtime,native=False):
    success(process,'PSF current source readmission',READMISSION_SECONDS)
    expected=[runtime['python'],'-B',str(HERE/'r0035_psf.py'),'readmit','--task',str(Path(task).absolute()),*(['--native'] if native else [])]
    need(process.get('argv')==expected and process.get('cwd')==str(HERE)
         and type(process.get('timeoutSeconds')) is int and process['timeoutSeconds']==READMISSION_SECONDS,
         'PSF actual source readmission command differs')
    value=json.loads(process['stdout'])
    need(value.get('protocol')=='r0035-psf-current-admission/1' and value.get('status')=='PASS'
         and value.get('task')==str(Path(task).absolute()) and same(value.get('runtime'),runtime_authority(task,runtime))
         and (not native or value.get('nativePreparation') is True),'PSF actual source readmission output differs')
    return value


def make_plan(prepared,out,runtime,admission):
    out=Path(out).absolute();task=out.parent.parent;p=paths(task)
    reference=original_plan(prepared);rows=[]
    for role in ROLES:
        identifier='r0035-chromium-psf-'+role;target=out/identifier;evidence=out/(identifier+'-custody')
        plan_path=p['referencePlan' if role=='reference' else 'derivedPlan']
        original=[runtime['python'],str(Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py'),
                  str(plan_path),str(target),*DRIVER_ARGS]
        ready=admission.get('status')=='PASS'
        row={'id':identifier,'workOrder':'R0035','engine':'chromium','dpr':1,
             'cwd':prepared['sources']['research']['root'],'env':{'NODE_PATH':runtime['modules']},
             'output':str(target),'stdout':str(out/(identifier+'.stdout')),'stderr':str(out/(identifier+'.stderr')),
             'timeoutSeconds':CHILD_SECONDS,'preObservationCheckSeconds':READMISSION_SECONDS,
             'postObservationCheckSeconds':POST_SECONDS,'namespaceSeconds':LANE_SECONDS,
             'result':{'kind':'r0035-trials','path':str(target/'summary.json'),'expectedRows':3,'expectedArms':list(ARMS),
                       'capture':False,'requiresEveryRowAdmitted':True,'psfDriverPath':str(evidence/'driver.json')},
             'psfObservation':{'protocol':'r0035-psf-paired-diagnostic/1','role':role,'timingClass':TIMING},
             'preparation':admission,'dependsOn':[] if role=='reference' else ['r0035-chromium-psf-reference'],
             'dependencyPolicy':'finished; preserve original failure, admit each member independently; complete pair required',
             'stopScopeOnAndon':'R0035','stopAllOnExit':[86],
             'exitStatuses':{'0':OBSERVED,'1':'INCOMPLETE','86':'EXTERNAL_CONTINUATION_VETOED'},
             'evidenceRetention':{'instrumented':True,'output':str(evidence),'originalArgv':original,
                                  'timingComparableToOriginal':False,'adapter':ADAPTER,
                                  'overhead':'Explicit plan and route/trial custody adapter; no new per-frame host writes or collector.'}}
        row['argv']=[runtime['python'],str(HERE/'observe_r0035_psf.py'),'--task',str(task),'--role',role,
                     '--preadmission',str(task/'capture'/('r0035-psf-preadmission-'+role+'.json')),
                     '--evidence',str(evidence),'--',*original[2:]] if ready else []
        rows.append(row)
    return {'protocol':'salah-hosted-native-lanes/1','sequential':True,'workOrders':['R0035'],'evidenceRetention':False,
            'r0035Controls':dict(CONTROLS),'r0035Stages':False,'r0035Costs':False,'r0035Psf':True,
            'r003fHarness':'published','r0040Mode':'options','r0035PlanPath':str(out/'r0035-plan.json'),
            'r0035Plan':reference,'preparedReceipt':{'path':str(p['prepared']),'sha256':record(p['prepared'])['sha256']},
            'lanes':rows,'psfPair':{'roles':list(ROLES),'fixedOrder':True,'timingClass':TIMING,
                                  'humanAcceptance':'OUTSTANDING','speedClaim':'NOT_ESTABLISHED'}}


def admit_plan(plan,task,runtime,native=False,retain=None):
    """Caller runtime authority precedes any optional receipt-driven process."""
    runtime_authority(task,runtime)
    need(isinstance(plan,dict) and isinstance(plan.get('lanes'),list) and len(plan['lanes'])==2,
         'complete two-member PSF dispatch required')
    for row in plan['lanes']:
        need(isinstance(row,dict) and isinstance(row.get('preparation'),dict),'PSF lane preparation required')
        if row['preparation'].get('status')=='PASS':
            need(isinstance(row.get('argv'),list) and row['argv'] and row['argv'][0]==runtime['python']
                 and row.get('evidenceRetention',{}).get('originalArgv',[None])[0]==runtime['python'],
                 'PSF actual executable differs from acquired runtime')
            need(same(row.get('env'),{'NODE_PATH':runtime['modules']})
                 and same(row['preparation'].get('runtime'),runtime_authority(task,runtime)),
                 'PSF copied runtime or package environment differs from acquired authority')
        else:
            need(row['preparation'].get('status')=='INCOMPLETE' and row.get('argv')==[],
                 'unprepared PSF member cannot execute substitute code')
    process=readmit(task,runtime,native=native)
    if retain is not None:save(retain,process)
    admission=admitted_process(process,task,runtime,native=native)
    prepared=load(paths(task)['prepared']);expected=make_plan(prepared,Path(task)/'capture/lanes',runtime,admission)
    need(same(plan,expected),'PSF canonical complete current plan/argv population differs')
    return expected['lanes']


def replay_trial(driver,body,arm,label,scope):
    """Replay exactly the original assessment; no new scientific predicate."""
    need(isinstance(body,dict) and body.get('arm')==label and body.get('commit')==arm['commit']
         and body.get('root')==arm['root'] and body.get('flags')==arm.get('flags','').lstrip('&')
         and body.get('engine')=='chromium' and isinstance(body.get('version'),str) and bool(body['version'])
         and body.get('utc')=='2026-11-09T00:00:00Z' and body.get('clock')=='ordinary'
         and body.get('scene')=='dark' and body.get('motion')=='normal' and body.get('capture') is False
         and body.get('observedProducerDuringTrial') is True and body.get('scope')==scope
         and body.get('weather')=='controlled fixture' and body.get('acquisitions')==[],
         'PSF raw original trial source, role, controls or native population differs')
    probe=arm.get('producerProbe')
    trace=body['trace']
    verdict=driver.assess(body['before'],body['after'],trace,trace['publication'],'dark',[-91,-20],
                          'normal','ordinary',probe,label,True)
    errors=body.get('pageErrors')
    need(isinstance(errors,list) and all(isinstance(x,str) for x in errors),'original page-error population required')
    if errors:verdict['failures'].append('page errors');verdict['verdict']='failed'
    need(same(body.get('qualification'),verdict) and body.get('admitted') is (verdict['verdict']=='passed'),
         'PSF raw trial qualification differs from original assessment replay')
    gaps=[b-a for a,b in zip(trace['frames'],trace['frames'][1:])]
    metrics={'p50FrameMs':driver.percentile(gaps,.5),'p95FrameMs':driver.percentile(gaps,.95),
             'p99FrameMs':driver.percentile(gaps,.99),'maxFrameMs':max(gaps,default=None),
             'framesOver50Ms':sum(g>50 for g in gaps),'acquisitionP95Ms':None,'acquisitionMaxMs':None}
    need(all(same(body.get(k),v) for k,v in metrics.items()),'PSF original frame metrics differ from raw original frames')
    return {k:body[k] for k in ('arm','commit','clock','scene','motion','capture','observedProducerDuringTrial',
                               'qualification','p95FrameMs','p99FrameMs','maxFrameMs','framesOver50Ms','admitted')}


def intake(task,runtime,role):
    need(role in ROLES,'PSF intake role required');source_pins();runtime_authority(task,runtime)
    p=paths(task);identifier='r0035-chromium-psf-'+role;target=p['task']/'capture/lanes'/identifier
    evidence=target.with_name(identifier+'-custody');final=load(evidence/'driver.json')
    need(final.get('protocol')=='r0035-psf-adapted-driver/1' and final.get('status')=='DRIVER_RETURNED'
         and final.get('role')==role and type(final.get('adapterCalls')) is int and final['adapterCalls']==1
         and type(final.get('trialCalls')) is int and final['trialCalls']==3
         and same(final.get('adapter'),ADAPTER) and final.get('errors')==[] and final.get('originalException') is None
         and final.get('continuationVeto') is None and final.get('actualPython')==runtime['python']
         and final.get('nativeQualification')=='UNCHANGED_ORIGINAL_REPORT_ONLY' and final.get('humanAcceptance')=='OUTSTANDING',
         'complete explicit PSF adapter terminal receipt required')
    prepath=p['task']/'capture'/('r0035-psf-preadmission-'+role+'.json')
    need(same(final['preadmission'],record(prepath)),'PSF actual preadmission process receipt differs')
    before=admitted_process(load(prepath),task,runtime,native=True)
    afterpath=p['task']/'capture'/('r0035-psf-postadmission-'+role+'.json')
    after=admitted_process(load(afterpath),task,runtime,native=True)
    need(same(before,after) and same(final.get('sourceAdmission'),before)
         and same(final.get('sourcePins'),source_pins()),'PSF actual pre/post source admission differs')
    plan_path=p['referencePlan' if role=='reference' else 'derivedPlan'];plan=load(plan_path)
    expected_argv=[runtime['python'],before['driver'],str(plan_path),str(target),*DRIVER_ARGS]
    need(final.get('actualOriginalArgv')==expected_argv and same(load(target/'plan.json'),plan),
         'PSF original operational arguments or retained plan differs')
    import r0035_stage_materialize as original
    import r003f_matrix_campaign as boundary
    loader=original.support();driver=loader.load_driver(Path(before['driver']))
    need(same(final.get('sources'),loader.verify_inputs(Path(before['driver']))),'PSF original driver/admission/clock closure differs')
    namespace=p['task']/'capture/isolation'/identifier/'receipt.json'
    need(same(final.get('isolation'),record(namespace)),'PSF actual namespace custody differs')
    loader.verify_isolation(namespace);boundary.original_isolation(namespace)
    expected_files={'plan.json','summary.json',*[f'01-{arm}/trial.json' for arm in ARMS]}
    need(set(inventory(target))==expected_files,'PSF original raw report population has missing or extra members')
    receipts=final.get('trials')
    need(isinstance(receipts,list) and len(receipts)==3,'PSF original trial custody population differs')
    rows=[];reports=[];versions=[]
    sources={name:original.pins()['files']['tools/r0035/'+name]['sha256']
             for name in ('native_trials.py','trial_admission.py','trial_clock.js')}
    for ordinal,label in enumerate(ARMS,1):
        trial_path=target/f'01-{label}/trial.json';receipt_path=evidence/f'trial-{ordinal:03}-{label}.json'
        need(same(receipts[ordinal-1],{'ordinal':ordinal,'arm':label,'receipt':record(receipt_path)}),
             'PSF ordered role/arm receipt population differs')
        custody=load(receipt_path);body=load(trial_path)
        need(custody.get('protocol')=='r0035-psf-adapted-trial/1' and type(custody.get('ordinal')) is int
             and custody['ordinal']==ordinal and custody.get('role')==role and custody.get('arm')==label
             and custody.get('engine')=='chromium' and custody.get('browserVersion')==body.get('version')
             and same(custody.get('sourceArm'),plan['arms'][label]) and custody.get('originalOutput')==str(trial_path.parent)
             and type(custody.get('pages')) is int and custody['pages']==1 and custody.get('catchAllRoute') is True
             and custody.get('contextClosed') is True and not any(custody.get(k) for k in ('originalException','unwinding','closeError','continuationVeto','abortError'))
             and same(custody.get('originalReport'),record(trial_path)), 'PSF actual trial or cleanup custody differs')
        options={'viewport':{'width':360,'height':570},'device_scale_factor':1,'timezone_id':'UTC',
                 'reduced_motion':'no-preference','service_workers':'block'}
        need(same(custody.get('contextOptions'),options),'PSF actual native viewport/DPR or context differs')
        args=custody.get('originalArguments',{})
        required={'plan':str(plan_path),'output':str(target),'engine':'chromium','clock':'ordinary','rounds':1,
                  'seconds':15,'warmup':5,'scene':'dark','motion':'normal','utc':'2026-11-09T00:00:00Z',
                  'capture':False,'observe_producer':True,'scope':plan['kind'],'driver_sha256':sources,
                  'scene_inputs':[-91,-20,'&simWx=0&simCloud=0','']}
        need(same(args,required) and same(body.get('driverSha256'),sources),'PSF original measured arguments or helper hashes differ')
        rows.append(replay_trial(driver,body,plan['arms'][label],label,plan['kind']))
        reports.append({'arm':label,'report':record(trial_path),'receipt':record(receipt_path)})
        versions.append(body['version'])
    need(set(inventory(evidence))=={'driver.json',*[f'trial-{i:03}-{arm}.json' for i,arm in enumerate(ARMS,1)]},
         'PSF custody population has missing or extra members')
    need(len(set(versions))==1,'PSF original browser version changed within a member')
    need(same(load(target/'summary.json'),rows) and same(final['originalSummary'],record(target/'summary.json')),
         'PSF original summary differs from complete raw original assessment replay')
    status='FAIL' if any(x['qualification']['verdict']=='failed' for x in rows) else 'PASS' if all(x['admitted'] is True for x in rows) else 'INCOMPLETE'
    return {'protocol':'r0035-psf-original-intake/1','status':'COMPLETE','role':role,'originalStatus':status,
            'sourceAdmission':before,'driver':record(evidence/'driver.json'),'summary':record(target/'summary.json'),
            'trials':reports,'browserVersion':versions[0],'runtime':before['runtime'],
            'timingClass':TIMING,'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','humanAcceptance':'OUTSTANDING'}


def post_observation(lane,returncode,timed_out):
    """Actual source and original-report checks are independent retained children."""
    result={'status':'INCOMPLETE'}
    role=lane['psfObservation']['role'];task=Path(lane['output']).parents[2]
    try:
        runtime=load(task/'runtime.json')
        need(type(returncode) is int and returncode==0 and timed_out is False,'PSF actual adapted child did not finish normally')
        current=readmit(task,runtime,native=True);save(task/'capture'/('r0035-psf-postadmission-'+role+'.json'),current)
        result['currentSourceProcess']=current
        admission=admitted_process(current,task,runtime,native=True)
        need(same(admission,lane['preparation']),'PSF source changed after planned native member')
        command=[runtime['python'],'-B',str(HERE/'r0035_psf.py'),'intake','--task',str(task),'--role',role,'--native']
        checked=run_process(command,INTAKE_SECONDS);save(task/'capture'/('r0035-psf-intake-'+role+'.json'),checked)
        result['intakeProcess']=checked;success(checked,'PSF original report intake',INTAKE_SECONDS)
        body=json.loads(checked['stdout'])
        need(body.get('protocol')=='r0035-psf-original-intake/1' and body.get('status')=='COMPLETE'
             and body.get('role')==role and same(body.get('sourceAdmission'),admission),'PSF actual intake terminal record differs')
        result.update(status='COMPLETE',intake=body)
    except (OSError,ValueError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:result['reason']=str(error)
    return result


def pair_status(plan,rows):
    result={'protocol':'r0035-psf-pair-intake/1','status':'INCOMPLETE','roles':list(ROLES),
            'fixedOrder':True,'speedClaim':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}
    try:
        need(len(rows)==2 and [x.get('id') for x in rows]==[x['id'] for x in plan['lanes']]
             and all(x.get('status')==OBSERVED for x in rows),'both complete original-admitted PSF members required')
        intakes=[x['psfObservation']['intake'] for x in rows]
        need([x.get('role') for x in intakes]==list(ROLES) and all(x.get('originalStatus')=='PASS' for x in intakes)
             and all(x.get('status')=='COMPLETE' for x in intakes),'PSF pair cannot promote original failures or partial members')
        reference,derived=intakes
        for key in ('sourceAdmission','runtime','browserVersion','timingClass'):
            need(same(reference[key],derived[key]),'PSF pair actual '+key+' differs')
        need(reference['timingClass']==TIMING,'PSF pair timing identity differs')
        result.update(status='OBSERVED',identity=reference['sourceAdmission']['identity'],
                      browserVersion=reference['browserVersion'],runtime=reference['runtime'],
                      members=[{'role':x['role'],'summary':x['summary'],'driver':x['driver']} for x in intakes])
    except (ValueError,KeyError,TypeError) as error:result['reason']=str(error)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('prepare','readmit','intake'))
    parser.add_argument('--task',type=Path,required=True);parser.add_argument('--native',action='store_true')
    parser.add_argument('--role',choices=ROLES)
    args=parser.parse_args();os.umask(0o077);runtime=load(args.task/'runtime.json')
    need(runtime.get('python')==sys.executable,'PSF actual entry Python differs from acquired runtime')
    if args.command=='prepare':
        prepare_pair(args.task,runtime);print('PSF SOURCE PAIR PREPARED; native NOT_RUN')
    elif args.command=='readmit':print(json.dumps(current_admission(args.task,runtime,args.native),allow_nan=False))
    else:print(json.dumps(intake(args.task,runtime,args.role),allow_nan=False))


if __name__=='__main__':main()
