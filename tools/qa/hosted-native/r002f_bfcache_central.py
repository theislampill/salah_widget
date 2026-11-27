"""Additive R002F bfcache source, acquisition, canonical dispatch and terminal custody.

This module never imports or launches a browser. Native qualification belongs to
the exact original witness plus the separately disclosed adapter, not a green job.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import r002f_bfcache_tools as tools

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MODE='bfcache-witness'
KIND='r002f-bfcache-witness'
LANE='r002f-bfcache-chromium-dpr1'
ADMISSION='r002f-bfcache-source-admission/1'
RESULT='r002f-bfcache-pair/1'
STATUS='OBSERVED_BFCACHE_DIAGNOSTIC'
QUALIFICATION='R002F_BFCACHE_MOON_WITNESS_ONLY'
TIMING='instrumented-existing-witness-retention'
PHASES={'admission':30,'display':15,'listeners':15,'launch':210,'owner':15,'before':180,'experiment':600,
        'contextClose':90,'after':180,'browserClose':60,'serverDrain':15,'decoder':120,'judgment':60,'failureCleanup':60,'reserve':30}
need=tools.need
load=tools.load
record=tools.file_record
save=tools.save


def same(left,right):
    return json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False)


def campaign_selected(value):
    if not tools.selected(value):return False
    need(value.get('schemaVersion',1)==1 and type(value.get('r003fDpr',1)) is int and value.get('r003fDpr',1)==1,
         'bfcache route leaves the unselected Moon DPR at its original default')
    return True


def budget():
    return {'protocol':'r002f-bfcache-budget/1','calibration':'UNCALIBRATED_OUTER_CEILINGS','phases':dict(PHASES),
            'childSeconds':1680,'armSeconds':2040,'pairSeconds':4200,'preparationSeconds':2160,
            'currentSeconds':120,'armCurrentSeconds':60,'postSeconds':120,'replaySeconds':210,'namespaceSeconds':4560,
            'coordinatorSeconds':6960,'workflowObservationMinutes':117,'workflowAcquisitionMinutes':15,
            'toolAcquisitionSeconds':180,'originalLaunchDefaultSeconds':180,'originalFiniteObservationAllowanceSeconds':401.1,
            'finiteAllowanceIsNotWallClockBound':True,'scientificWaitsChanged':False}


def source_files():
    names=['r002f_bfcache.cjs','r002f_bfcache_preload.cjs','r002f_bfcache_source.cjs','r002f_bfcache_replay.cjs',
           'r002f_bfcache_tools.py','r002f_bfcache_central.py','r002f-bfcache-pins.json','R002F_BFCACHE.md',
           'r002f_bfcache_controls.cjs','r002f_bfcache_replay_controls.cjs','r002f_bfcache_tools_controls.py','r002f_bfcache_central_controls.py',
           'fixtures/r002f-bfcache-decode-control.webm','fixtures/r002f-bfcache-decode-control.json',
           'acquire.sh','lanes.py','observe.py','capture_pipeline.py','campaign.json','identities.py',
           'prepare.py','r002f_prepare.py','r002f_probe.cjs','r002f-tabhide-pins.json','r002f_tabhide_source.cjs',
           'r002f_tabhide_runtime.cjs','r002f_tabhide.cjs','r002f_focus_owner.cjs','r003f_matrix_campaign.py',
           'r003f_diagnostics.py','r0035_psf.py','r0035_stage_materialize.py','r0035_cost_materialize.py',
           'observe_r0035_stages.py','observe_r0035_costs.py','r0040_capture_prepare.py','r0040_passive_central.py','r0040_mechanism_central.py',
           'capture_transport.py','envelope.py','recipient.crt',
           'browser-control.cjs','namespace.sh','node/package.json','node/package-lock.json','requirements.txt',
           # Recomputed composed caller/leaf closure, including local imports of the registered controls.
           'R0040_AUTOATTACH.md','r0040_autoattach.cjs','r0040_autoattach_network.cjs','r0040_autoattach_central.py',
           'r0040_autoattach_controls.cjs','r0040_autoattach_network_controls.cjs','r0040_autoattach_operational_controls.cjs',
           'r0040_autoattach_central_controls.py','r0040_autoattach_currentness_controls.py','r0040_autoattach_route_controls.py','r0040_autoattach_fixture.cjs',
           'r0040_mechanism.cjs','r0040_mechanism_bracket.cjs','r0040_mechanism_network.cjs','r0040_mechanism_fixture.cjs',
           'r0040_passive.cjs','r0040_passive_sampler.cjs','r0040_passive_runtime.cjs','r0040_dateonly.cjs',
           'retain_r0040_capture.cjs','retain_r0040.cjs','retention-pins.json','retain_r0035.py',
           'r0035_cost_controls.py','r0035_stage_controls.py','r0040_capture_preparation_controls.py',
           'r0040_passive_central_controls.py','retention_controls.py','test_lanes.py','test_observe.py',
           # The additive publish route is imported by the composed callers.
           'r0035_publish.py','observe_r0035_publish.py','r0035_publish_io.mjs','r0035-publish-pins.json','R0035_PUBLISH.md',
           'r0035_publish_controls.py','r0035_publish_io_controls.cjs','observe_r0035_psf.py',
           'r0035-stage-pins.json','r0035-psf-native-pins.json','r0035_psf_transform.mjs',
           'test_capture_pipeline.py','test_envelope.py','r0035_psf_controls.py']
    return sorted(['tools/qa/hosted-native/'+name for name in names]+['tools/qa/r0041/'+name for name in
        ('real-witness.cjs','iso.cjs','png.cjs')]+['.github/workflows/research-native-pilot.yml',
        'docs/state-contracts/R0040-native-capture-preflight.md','docs/state-contracts/evidence/R0040/native-capture-preflight.json',
        'tools/r0035/publish_diagnostic.mjs','tools/r0035/publish_diagnostic_controls.cjs',
        'tools/r0035/live_lab.mjs','tools/r0035/frame_guard.mjs','tools/r0035/sample_history.mjs',
        'tools/r0035/changed_rectangles.mjs','tools/r0035/psf_within_call.mjs','real-sky/native-contract.mjs',
        'tools/r0035/native_trials.py','tools/r0035/trial_admission.py','tools/r0035/trial_clock.js'])


def producer_source_files():
    return [os.path.relpath(ROOT/name,HERE) for name in source_files()]


def source_identity():
    def git(*args):
        result=subprocess.run(['git','-C',str(ROOT),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True)
        return result.stdout.decode().strip()
    need(not git('status','--porcelain'),'complete orchestration source is not clean')
    files={name:record(ROOT/name) for name in source_files()}
    manifest=load(HERE/'r002f-bfcache-pins.json')
    need(manifest.get('protocol')=='r002f-bfcache-source/1' and manifest.get('originalScientificBodiesChanged') is False,
         'bfcache original source manifest missing')
    for name,digest in manifest['original'].items():need(files[name]['sha256']==digest,'original bfcache source pin changed: '+name)
    need(manifest['sourceFiles']==source_files() and same(manifest['budget'],budget()),'declared source closure/budget differs')
    return {'protocol':'r002f-bfcache-current-source/1','root':str(ROOT),'commit':git('rev-parse','HEAD'),
            'tree':git('rev-parse','HEAD^{tree}'),'clean':True,'files':files}


def paths(task):
    task=Path(task).absolute()
    need(task!=Path('/') and task.resolve()==task and '..' not in task.parts
         and not any(p.is_symlink() for p in (task,*task.parents)),'literal current task root required')
    capture=task/'capture';out=capture/'lanes'/LANE
    return {'task':task,'capture':capture,'tools':capture/'r002f-bfcache-tools/receipt.json',
            'common':task/'work/prepared/receipts/prepared.json','commonProcess':capture/'preparation-process.json',
            'commonContext':capture/'preparation-context.json','r002f':task/'work/r002f-prepared/build-result.json',
            'r002fProcess':capture/'r002f-preparation-process.json','output':out,'result':out/'result.json',
            'entryProcess':capture/'lanes'/(LANE+'-process.json'),'isolation':capture/'isolation'/LANE/'receipt.json'}


def process_success(value,argv,seconds):
    need(type(value) is dict and value.get('argv')==argv and value.get('cwd')==str(HERE)
         and type(value.get('timeoutSeconds')) is int and value['timeoutSeconds']==seconds
         and type(value.get('returncode')) is int and value['returncode']==0 and value.get('timedOut') is False
         and not value.get('error') and not value.get('retentionError') and not value.get('overflow'),
         'actual source process argv/cwd/completion differs')
    elapsed=value.get('elapsedSeconds')
    need(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=seconds,'actual process bound/elapsed differs')


def tools_current(task,runtime):
    p=paths(task);tools.runtime_schema(runtime)
    need(same(load(p['task']/'runtime.json'),runtime),'current acquired runtime differs')
    need(p['tools'].is_file(),'selected route tool receipt is missing')
    value=load(p['tools']);need(value.get('protocol')==tools.PROTOCOL and value.get('status')=='COMPLETE'
        and value.get('task')==str(p['task']) and value.get('scope')=='SELECTED_ROUTE_HOSTED_TOOL_ACQUISITION'
        and value.get('nativeObservation') is False and same(value['acquired']['runtime'],runtime),'actual selected tool receipt differs')
    need(value['capability'].get('protocol')=='r002f-bfcache-source-capability/1' and value['capability'].get('status')=='COMPLETE'
         and value['capability'].get('scope')=='SOURCE_CONTROL_ONLY' and value['capability'].get('nativeObservation') is False,
         'original decoder synthetic capability is absent')
    need(all(value['capability'][key].get('complete') is True and value['capability'][key].get('mappingsComplete') is True
             for key in ('probe','decode')),'actual source capability dependency mappings missing')
    need(value['capability']['decoded']['bytes']==1036680 and value['capability']['decoded']['sha256']==tools.FIXTURE_RGB_SHA256,
         'decoded source-control population differs')
    tools.admit_metadata(value['capability']['metadata']);tools.current_records(value)
    need(same(source_identity(),value['sources']),'current merged caller/source identity differs from tool acquisition')
    for name,files in value['acquired']['packages'].items():
        need(tools.file_tree(Path(runtime['modules'])/name)==files,'complete acquired package population changed')
    return {'receipt':record(p['tools']),'sources':value['sources'],'runtime':runtime}


def current_admission(task,runtime,*,native=False):
    import prepare
    import lanes
    import r003f_matrix_campaign as common
    p=paths(task);tool=tools_current(task,runtime)
    prepared,common_receipts=common.common_custody(p['common'],p['commonProcess'],p['commonContext'],native=native)
    context=load(p['commonContext']);process=load(p['commonProcess'])
    argv=[runtime['python'],str(HERE/'prepare.py'),'--research',prepared['sources']['research']['root'],
          '--baseline',prepared['sources']['baseline']['root'],'--historical',prepared['sources']['historical']['root'],
          '--out',str(p['common'].parent.parent)]
    need(context['argv']==argv and context['cwd']==str(HERE),'common literal source/task/runtime differs')
    process_success({**process,'argv':context['argv'],'cwd':context['cwd'],'timeoutSeconds':context['timeoutSeconds']},argv,900)
    need((p['capture']/'preparation.stdout').read_text().strip()=='PREPARATION READY','actual common terminal output differs')
    common_receipts['streams']={key:record(p['capture']/('preparation.'+key)) for key in ('stdout','stderr')}
    source_inputs={}
    for label,names in (('research',(*prepare.SOURCE_DIRS,prepare.RAIN_PATCH)),
                        ('baseline',(*prepare.SOURCE_DIRS,'index.html','offline.html','config.js','builder.html','GENERATED.json'))):
        actual=prepare.checked_files(Path(prepared['sources'][label]['root']),names)
        expected=load(p['common'].parent/(label+'-files.json'));need(same(actual,expected),'complete original source input population changed: '+label)
        source_inputs[label]={'count':len(actual),'sha256':common.population_digest(actual) if hasattr(common,'population_digest') else hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    for name in ('real-witness.cjs','iso.cjs','png.cjs'):
        wanted=record(ROOT/'tools/qa/r0041'/name)['sha256'];need(record(Path(prepared['sources']['research']['root'])/'tools/qa/r0041'/name)['sha256']==wanted,
            'immutable research/orchestration original witness differs')
    def run_generated(argv,**kwargs):
        need(kwargs=={'cwd':HERE,'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'timeout':30,'check':False},
             'original generated source command contract differs')
        parent=p['capture']/'r002f-bfcache-source-checks';parent.mkdir(mode=0o700,exist_ok=True)
        folder=Path(tempfile.mkdtemp(prefix='generated-',dir=parent))
        check=tools.run_bounded(argv,folder,'generated',30,cwd=HERE,env=dict(os.environ))
        save(folder/'process.json',{**check,
            'scope':'ACTUAL_GENERATED_SOURCE_READMISSION_NOT_NATIVE_OBSERVATION'})
        stdout=Path(check['streams']['stdout']['path']).read_bytes();stderr=Path(check['streams']['stderr']['path']).read_bytes()
        if check['timedOut']:raise subprocess.TimeoutExpired(argv,30,output=stdout,stderr=stderr)
        need(check['complete'] or type(check['returncode']) is int and check['returncode']!=0,
             'generated source process has incomplete streams or group cleanup')
        return subprocess.CompletedProcess(argv,check['returncode'],stdout,stderr)
    original=lanes.admit_r002f_tabhide(p['r002f'],p['r002fProcess'],prepared,p['common'],Path(runtime['node']),run_currentness=run_generated)
    need(original.get('status')=='PASS','original full R002F source/preparation admission failed: '+str(original.get('reason')))
    need(all(original['trees'][arm]['root']==str(p['task']/'work/r002f-prepared'/arm) for arm in ('baseline','candidate')),
         'R002F preparation was relocated')
    return {'protocol':ADMISSION,'status':'PASS','native':native,'task':str(p['task']),'runtime':runtime,
            'sources':tool['sources'],'tools':tool['receipt'],'common':common_receipts,'sourceInputs':source_inputs,
            'r002f':original,'generated':original['generated']}


def child_argv(runtime,root,out,label):
    need(label in ('baseline','candidate'),'original label required')
    return [runtime['node'],'--require',str(HERE/'r002f_bfcache_preload.cjs'),str(ROOT/'tools/qa/r0041/real-witness.cjs'),
            str(root),str(out),'chromium','bfcache','2026-11-18T16:30:00Z','3','--label='+label]


def make_lane(task,runtime,admission):
    p=paths(task);admission=admission or {'status':'INCOMPLETE','reason':'bfcache source preparation is missing'}
    valid=(admission.get('status')=='PASS' and admission.get('protocol')==ADMISSION and admission.get('native') is True
           and admission.get('task')==str(p['task']))
    if not valid and admission.get('status')=='PASS':admission={'status':'INCOMPLETE','reason':'native current preparation is absent or rebound'}
    return {'id':LANE,'workOrder':'R002F','engine':'chromium','dpr':1,'cwd':str(HERE),'env':{'NODE_PATH':runtime.get('modules')},
            'output':str(p['output']),'stdout':str(p['capture']/'lanes'/(LANE+'.stdout')),'stderr':str(p['capture']/'lanes'/(LANE+'.stderr')),
            'argv':[runtime['node'],str(HERE/'r002f_bfcache.cjs'),'--task',str(p['task']),'--out',str(p['output'])] if valid else [],
            'timeoutSeconds':4200,'postObservationCheckSeconds':120,'result':{'kind':KIND,'path':str(p['result']),'expectedArms':['baseline','candidate'],
                'expectedEventsPerArm':3,'nativeQualification':QUALIFICATION},'exitStatuses':{'0':STATUS,'2':'INCOMPLETE','86':'ISOLATION_FAIL'},
            'dependsOn':[],'stopScopeOnAndon':'R002F','stopAllOnExit':[86],'preparation':admission,
            'bfcacheObservation':{'protocol':'r002f-bfcache-diagnostic/1','budget':budget(),'captureCallsAdded':0},
            'evidenceRetention':{'instrumented':True,'output':str(p['output']),'timingClass':TIMING,'timingComparableToOriginal':False,
              'overhead':'Existing return retention, source/owner checks, IPC and hashing add uncalibrated time; no added screenshots or page evaluations.'}}


def lane_selected(lane):
    return type(lane) is dict and lane.get('result',{}).get('kind')==KIND


def make_plan(prepared,out,runtime,admission):
    from lanes import original_star_plan
    task=Path(out).parent.parent;need(Path(out)==task/'capture/lanes','canonical task-owned plan directory required')
    star=original_star_plan(prepared)
    return {'schemaVersion':1,'protocol':'salah-hosted-native-lanes/1','sequential':True,'workOrders':['R002F'],
            'scope':'One paired R002F Moon bfcache witness diagnostic; no product/owner-policy acceptance.',
            'evidenceRetention':False,'r0035Controls':{'guard':'default','scope':'all','mode':'both'},'r0035Stages':False,
            'r003fHarness':'published','r0040Mode':'options','r002fRoute':MODE,
            'r0035PlanPath':str(Path(out)/'r0035-plan.json'),'r0035Plan':star,'lanes':[make_lane(task,runtime,admission)],
            'failurePolicy':{'isolation':'stop all observations','incompleteArm':'stop pair; retain actual evidence',
                             'timeout':'kill owned child; incomplete; namespace teardown remains separate'}}


def namespace_admitted(lane,inner):
    if inner.get('status')!=STATUS:
        return not lane_selected(lane) or inner.get('status') in ('INCOMPLETE','ISOLATION_FAIL')
    return (lane_selected(lane) and type(inner.get('returncode')) is int and inner['returncode']==0
            and inner.get('timedOut') is False and inner.get('nativeQualification')==QUALIFICATION
            and inner.get('humanAcceptance')=='OUTSTANDING' and inner.get('timingClass')==TIMING
            and inner.get('bfcacheIntake',{}).get('result',{}).get('status')=='COMPLETE')


def admit_runtime(lane,runtime):
    tools.runtime_schema(runtime);task=Path(lane['output']).parents[2]
    canonical=make_lane(task,runtime,lane.get('preparation'))
    need(same(lane,canonical),'bfcache literal command/runtime/source/budget differs')


def runtime_authority(task,runtime):
    """Before child execution, bind its interpreter to this actual acquired process and receipt."""
    p=paths(task);tools.runtime_schema(runtime)
    need(runtime['python']==sys.executable and same(load(p['task']/'runtime.json'),runtime),
         'actual acquired Python/runtime authority differs')
    acquired=load(p['tools'])['acquired'];need(same(acquired['runtime'],runtime),'actual tool runtime authority differs')
    tools.require_record(acquired['python']);need(same(record(sys.executable,system=True),acquired['python']),
         'actual acquired Python bytes differ')


def readmit(task,runtime,native=True,seconds=120):
    import r003f_diagnostics as bounded
    need(type(seconds) is int and seconds in (60,120),'declared currentness process bound required')
    runtime_authority(task,runtime)
    return bounded.bounded([runtime['python'],'-B',str(HERE/'r002f_bfcache_central.py'),'readmit'],
                           {'task':str(task),'runtime':runtime,'native':native},seconds,raw=True)


def admit_currentness_reference(task,lane,runtime,check,reference,phase,*,refused=False):
    """Admit retained T1 bytes, not a reason string or reconstructed process output."""
    p=paths(task);file=Path(reference['path']);identity=record(file)
    need(phase in ('outer','inner') and file.name=='process.json' and file.parent.parent==p['capture']/'currentness'
         and file.parent.name.startswith(phase+'-'+LANE+'-') and identity['sha256']==reference['sha256'],
         'currentness receipt location/hash differs')
    body=load(file)
    need(body.get('protocol')=='salah-returned-currentness/1' and body.get('phase')==phase
         and body.get('lane')==LANE and body.get('workOrder')=='R002F' and same(body.get('process'),check)
         and body.get('knownReturnedRefusal') is refused,'actual returned currentness receipt differs')
    argv=[runtime['python'],'-B',str(HERE/'r002f_bfcache_central.py'),'readmit']
    need(type(check.get('returncode')) is int and type(check.get('timedOut')) is bool
         and check.get('argv')==argv and check.get('cwd')==str(HERE) and type(check.get('timeoutSeconds')) is int
         and check['timeoutSeconds']==120 and not any(check.get(k) for k in ('error','retentionError','interrupted','forced','overflow')),
         'actual returned currentness invocation/completion differs')
    need(set(body.get('streams',{}))=={'stdout','stderr'},'actual currentness streams missing')
    for key,row in body['streams'].items():
        actual=record(file.parent/key)
        need(row=={k:actual[k] for k in ('path','bytes','sha256')}
             and Path(actual['path']).read_bytes().decode('utf8',errors='replace')==check[key],
             'original currentness byte stream differs')
    if refused:
        need(check['timedOut'] or 0<check['returncode']<126,'unknown/interrupted currentness is not a returned refusal')
    else:
        process_success(check,argv,120)
        need(same(json.loads(check['stdout']),lane['preparation']),'current source readmission differs')
    return True


def admit_intake_process(check,argv,folder):
    need(check.get('argv')==argv and check.get('cwd')==str(folder) and type(check.get('timeoutSeconds')) is int
         and check['timeoutSeconds']==60 and type(check.get('returncode')) is int and check['returncode']==0
         and check.get('timedOut') is False and check.get('complete') is True and check.get('overflow') is False
         and check.get('groupStopped') is True and not check.get('error'),'actual complete-pair process differs')
    need(type(check.get('elapsedSeconds')) in (int,float) and math.isfinite(check['elapsedSeconds'])
         and 0<=check['elapsedSeconds']<=60,'actual complete-pair process elapsed differs')
    need(check.get('streams')=={key:record(Path(folder)/('complete-pair.'+key)) for key in ('stdout','stderr')},
         'actual complete-pair process streams differ')
    return True


def record_entry(lane,process):
    p=paths(Path(lane['output']).parents[2]);save(p['entryProcess'],{**process,'protocol':'r002f-bfcache-entry-process/1',
        'argv':lane['argv'],'cwd':lane['cwd'],'timeoutSeconds':4200,'streams':{key:record(lane[key]) for key in ('stdout','stderr')}})


def summary_shape(value):
    try:
        return (type(value) is dict and value.get('protocol')==RESULT and value.get('status')==STATUS
          and value.get('nativeQualification')==QUALIFICATION and value.get('humanAcceptance')=='OUTSTANDING'
          and value.get('timingClass')==TIMING and value.get('timingComparableToOriginal') is False
          and type(value.get('captureCallsAdded')) is int and value['captureCallsAdded']==0 and value.get('errors')==[]
          and type(value.get('arms')) is list and [x.get('label') for x in value['arms']]==['baseline','candidate']
          and all(x.get('status')=='COMPLETE' and x.get('originalValid') is True and type(x.get('originalVerdict')) is str
                  and x['originalVerdict']!='VOID' for x in value['arms']))
    except (TypeError,AttributeError,KeyError):return False


def classify(lane,body,returncode,timed_out):
    result={'status':'INCOMPLETE','stopAll':False,'nativeQualification':'NOT_EVALUATED','humanAcceptance':'OUTSTANDING',
            'returncode':returncode,'timedOut':timed_out,'timingClass':TIMING}
    if returncode==86 or type(body) is dict and body.get('status')=='ISOLATION_FAIL':return {**result,'status':'ISOLATION_FAIL','stopAll':True}
    if type(returncode) is not int or returncode!=0 or timed_out is not False or not summary_shape(body):return result
    try:
        started=time.monotonic()
        task=Path(lane['output']).parents[2];runtime=load(task/'runtime.json');p=paths(task);entry=load(p['entryProcess']);process_success(entry,lane['argv'],4200)
        folder=p['capture']/'r002f-bfcache-intake';need(not folder.exists(),'bfcache intake already exists');folder.mkdir(mode=0o700)
        current=readmit(task,runtime,native=True,seconds=60);streams={}
        for key in ('stdout','stderr'):
            raw=current.pop(key+'Bytes',None);need(type(raw) is bytes,'actual post-currentness bytes missing')
            file=folder/('source-current.'+key)
            with file.open('xb') as output:output.write(raw);output.flush();os.fsync(output.fileno())
            file.chmod(0o600);streams[key]=record(file)
        source_check=save(folder/'source-current-process.json',{**current,'streams':streams})
        process_success(current,[runtime['python'],'-B',str(HERE/'r002f_bfcache_central.py'),'readmit'],60)
        need(same(json.loads(current['stdout']),lane['preparation']),'current preparation differs after pair')
        argv=[runtime['node'],str(HERE/'r002f_bfcache.cjs'),'--admit','--task',str(task),'--out',str(p['output'])]
        check=tools.run_bounded(argv,folder,'complete-pair',60,env=dict(os.environ))
        save(folder/'process.json',check);admit_intake_process(check,argv,folder)
        intake=load(check['streams']['stdout']['path']);need(intake.get('status')=='COMPLETE' and intake.get('pair')==record(p['result']),
            'actual paired intake result differs')
        elapsed=time.monotonic()-started;need(elapsed<=120,'aggregate returned intake/currentness ceiling exceeded')
        result.update(status=STATUS,nativeQualification=QUALIFICATION,bfcacheIntake={'process':record(folder/'process.json'),
            'result':intake,'pair':record(p['result']),'entry':record(p['entryProcess']),'sourceCheck':source_check,'elapsedSeconds':elapsed})
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:result['reason']=str(error)
    return result


def pipeline_admitted(campaign,plan,body,lane,row,task):
    selected=campaign.get('r002fRoute')==MODE;new_status=row.get('status')==STATUS
    if not selected:return not new_status and not lane_selected(lane)
    try:
        campaign_selected(campaign);p=paths(task)
        need(plan.get('r002fRoute')==MODE and body.get('r002fRoute')==MODE and len(plan['lanes'])==1 and lane_selected(lane)
             and row['id']==LANE and lane['id']==LANE,'bfcache selected complete lane population differs')
        runtime=load(p['task']/'runtime.json');admit_runtime(lane,runtime)
        status=row.get('status')
        if status=='NOT_RUN':
            need('namespaceProcess' not in row and not p['entryProcess'].exists() and not p['result'].exists(),
                 'native dispatch bytes exist for a no-dispatch result')
            if lane['preparation']['status']=='INCOMPLETE':
                return lane['argv']==[] and row.get('preparationStatus')=='INCOMPLETE' and row.get('reason')==lane['preparation'].get('reason')
            refused=row.get('reason')!='bounded observation budget exhausted'
            return admit_currentness_reference(task,lane,runtime,row['outerCurrentness'],
                row['currentnessReceipt'] if refused else row['outerCurrentnessReceipt'],'outer',refused=refused)
        need(status in (STATUS,'INCOMPLETE','ISOLATION_FAIL','ISOLATION_UNCONFIRMED'),'foreign bfcache lane status')
        inner_file=p['capture']/'lane-status'/(LANE+'.json')
        inner=load(inner_file) if inner_file.exists() else None
        need(same(row.get('innerStatus'),inner),'actual inner status file differs')
        import observe
        actual=observe.namespace_status(lane,row['namespaceProcess'],inner)
        need(all(same(row.get(k),v) for k,v in actual.items()),'actual namespace disposition differs')
        if not new_status:
            if type(inner) is dict and inner.get('nativeStatus')=='NOT_RUN':
                need(status=='INCOMPLETE' and not p['entryProcess'].exists() and not p['result'].exists(),'source refusal was followed by native dispatch')
                admit_currentness_reference(task,lane,runtime,inner['preExecutionCurrentness'],inner['currentnessReceipt'],'inner',refused=True)
            return True
        need(row.get('nativeQualification')==QUALIFICATION and row.get('humanAcceptance')=='OUTSTANDING'
             and row.get('returncode')==0 and type(row.get('returncode')) is int and row.get('timedOut') is False,
             'bfcache reported qualification or actual process differs')
        tools_current(task,runtime)
        for name in ('id','status','returncode','timedOut','bfcacheIntake','nativeQualification','humanAcceptance','timingClass','preExecutionCurrentness','preExecutionCurrentnessReceipt'):
            need(same(row.get(name),inner.get(name)),'bfcache inner/outer returned row differs')
        for name,phase in (('outerCurrentness','outer'),('preExecutionCurrentness','inner')):
            admit_currentness_reference(task,lane,runtime,row[name],row[name+'Receipt'],phase)
        proof=row['bfcacheIntake'];need(proof['pair']==record(p['result']) and summary_shape(load(p['result'])),'paired report differs')
        tools.current_records(proof);entry=load(p['entryProcess']);process_success(entry,lane['argv'],4200)
        need(proof['entry']==record(p['entryProcess']) and entry['streams']=={key:record(lane[key]) for key in ('stdout','stderr')},'actual entry streams differ')
        folder=p['capture']/'r002f-bfcache-intake'
        need(proof['process']==record(folder/'process.json') and proof['sourceCheck']==record(folder/'source-current-process.json'),
             'literal post-intake process path differs')
        check=load(proof['process']['path']);argv=[runtime['node'],str(HERE/'r002f_bfcache.cjs'),'--admit','--task',str(task),'--out',str(p['output'])]
        admit_intake_process(check,argv,folder)
        need(same(proof['result'],load(check['streams']['stdout']['path'])) and proof['result']['pair']==proof['pair']
             and proof['result']['nativeQualification']==QUALIFICATION and proof['result']['humanAcceptance']=='OUTSTANDING',
             'actual intake stdout or qualification differs')
        current=load(proof['sourceCheck']['path']);process_success(current,[runtime['python'],'-B',str(HERE/'r002f_bfcache_central.py'),'readmit'],60)
        need(same(json.loads(current['stdout']),lane['preparation']) and current['streams']=={key:record(folder/('source-current.'+key)) for key in ('stdout','stderr')}
             and all(Path(current['streams'][key]['path']).read_bytes().decode('utf8',errors='replace')==current[key] for key in ('stdout','stderr')),
             'actual post-currentness process or original bytes differ')
        need(type(proof['elapsedSeconds']) in (int,float) and math.isfinite(proof['elapsedSeconds']) and 0<=proof['elapsedSeconds']<=120,
             'aggregate final intake bound differs')
        return True
    except (OSError,ValueError,KeyError,TypeError,AttributeError,subprocess.SubprocessError):return False


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('readmit','admit'))
    parser.add_argument('--task');parser.add_argument('--native',action='store_true');parser.add_argument('--output')
    args=parser.parse_args()
    if args.command=='readmit':
        request=json.load(sys.stdin);value=current_admission(request['task'],request['runtime'],native=request['native'])
    else:
        value=current_admission(args.task,load(Path(args.task)/'runtime.json'),native=args.native)
    if args.output:save(args.output,value)
    print(json.dumps(value,sort_keys=True,allow_nan=False))


if __name__=='__main__':main()
