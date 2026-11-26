"""Two explicitly foreign R003F diagnostics, with current source/process custody.

This helper never starts a browser. The unchanged leaf entries own their native
work. A source-only preparation cannot authorize either hosted diagnostic.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import r003f_matrix_campaign as common_support

HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[2]
ADMISSION = 'R003F/diagnostic-source-admission/1'
PREPARATION = 'R003F/diagnostic-preparation/1'
PREPARATION_ENTRY = 'R003F/diagnostic-preparation-entry/1'
ENTRY_PROCESS = 'R003F/diagnostic-entry-process/1'
FINAL = 'R003F/diagnostic-final-intake/1'
FIREFOX_PINS = '4221060e1613f913b157f0c326cfeefc0f0661ff156d2ce5eac51f9c44b992ef'
WEBKIT_MATERIALIZATION = 'c8c26bfdff9f20b38a5ece423db2759fc96339ca9d68cf2c68f7893d36930290'
SOURCE_SECONDS = 45
ROUTES = {
    'firefox-policy': {'engine':'firefox','id':'r003f-firefox-policy','kind':'r003f-firefox-policy',
        'status':'OBSERVED_FIREFOX_POLICY','qualification':'MANAGED_POLICY_DIAGNOSTIC_ONLY',
        'timing':'instrumented-managed-policy-dwell'},
    'preconnect-input': {'engine':'webkit','id':'r003f-webkit-preconnect-input','kind':'r003f-preconnect-input',
        'status':'OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC','qualification':'ALTERED_INPUT_DIAGNOSTIC_ONLY',
        'timing':'instrumented-altered-document-input'},
}
PINS = {
    'firefox_policy_source.cjs':'02d7dbc5d409d79cae9d855a77c7a2958d26fb386471f8575bc94a976a5e9845',
    'firefox_policy_probe.cjs':'c9f453ed69f2b1b8c2c84ed18ff3bde1268556c2218fd4d6d6fb17373480bfc6',
    'r003f_preconnect_materialize.cjs':'dc3ddd8b3e1ee7aa9d27b58c42659b57e1dcc18c709e8102935a2cb2e48dde21',
    'r003f_preconnect_input.cjs':'25ad6457e98f1090bb7f234d6f4cdeed451a6b72b5c9a5a9c2d820e57ada50ca',
    'r003f_materialize.cjs':'2fc95820151e08ff416ce10890a801045a960cd49c65eff499a1cf0ee4473fbc',
    'r003f_ui.cjs':'ccce93bcbe1bcd4834789e03ead8a2a104710e4955e05d57cc846ab4a341c82a',
    'prepare.py':'9f1a104ea49e263bee83dc6a82491830a4a105a751eb821ea8c4cefa0c68c114',
    'r003f_matrix_campaign.py':'9a165407a47ac25c147fda0a4344955b25d713b6c0ebcf04410da4786284ca14',
    'identities.py':'dcc5a11457221bbe97d1459b6ee3f50ad73b154ffd690912e6d3ee630a042049',
    'browser-control.cjs':'8ee6d30af1a97ee7ef702614c8150b42573f7f0d681336b683a99c2ed1519671',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def same(a, b):
    return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)


def regular(value):
    p=Path(value)
    need(p.is_absolute() and '..' not in p.parts, 'absolute nonescaping diagnostic path required')
    need(not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file(), 'regular diagnostic source or artifact required')
    return p


def sha(value):
    with regular(value).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def record(value):
    p=regular(value)
    return {'path':str(p),'sha256':sha(p)}


def artifact(value):
    p=regular(value)
    return {**record(p),'bytes':p.stat().st_size}


def load(value):
    p=regular(value)
    need(p.stat().st_size<=8*1024*1024,'diagnostic JSON bound exceeded')
    return json.loads(p.read_bytes())


def save(path, body):
    common_support.save(path,body)


def controls(mode, selected, engine, dpr, retained=False):
    if mode not in ROUTES:
        return None
    need(selected==['R003F'] and engine==ROUTES[mode]['engine'] and type(dpr) is int and dpr==1
         and retained is False, 'diagnostic requires its sole R003F engine, DPR1 and no generic retention')
    return {'mode':mode,**ROUTES[mode],'budget':budget(mode)}


def budget(mode):
    need(mode in ROUTES,'unknown R003F diagnostic budget')
    ff=mode=='firefox-policy';entry=330 if ff else 960;final=90 if ff else 120
    namespace=entry+120+final+75;coordinator=2640 if ff else 2880
    return {'protocol':'R003F/diagnostic-budget/1','calibration':'UNCALIBRATED_CEILINGS',
        'preparationSeconds':1350,'optionalPreparationSeconds':180,'preparationChildSeconds':60,
        'sourceSeconds':SOURCE_SECONDS,'outerCurrentSeconds':120,'currentSeconds':120,'entrySeconds':entry,
        **({'originalChildSeconds':270} if ff else {'originalCaptureSeconds':900,'documentReserveSeconds':60}),
        'finalSeconds':final,'finalNodeSeconds':30 if ff else 60,'namespaceAllowanceSeconds':75,
        'namespaceSeconds':namespace,'accountedSeconds':1350+120+namespace,'coordinatorSeconds':coordinator,
        'workflowObservationMinutes':coordinator//60+1}


def scope_fields(mode):
    route=ROUTES[mode]
    return {'diagnosticMode':mode,'nativeQualification':route['qualification'],
            'nativeProductAcceptance':'NOT_EVALUATED','humanAcceptance':'OUTSTANDING',
            'timingClass':route['timing'],'originalFailedObservation':'UNCHANGED','boundaryEngine':'chromium'}


def paths(task, mode):
    task=Path(task)
    need(task.is_absolute() and '..' not in task.parts and mode in ROUTES,'current absolute diagnostic task required')
    lane=ROUTES[mode]['id'];capture=task/'capture';preparation=capture/'r003f-diagnostic-preparation'
    output=capture/'firefox-policy' if mode=='firefox-policy' else capture/'lanes'/lane
    return {'task':task,'common':task/'work/prepared/receipts/prepared.json',
        'commonProcess':capture/'preparation-process.json','commonContext':capture/'preparation-context.json',
        'preparation':preparation,'preparationEntry':capture/'r003f-diagnostic-preparation-entry.json',
        'preparationProcess':preparation/'process.json','source':task/'work/r003f-preconnect',
        'output':output,'entryProcess':capture/'lanes'/(lane+'-process.json'),
        'isolation':capture/'isolation'/lane/'receipt.json',
        'result':output/('entry-result.json' if mode=='firefox-policy' else 'summary.json')}


def verify_sources():
    need(sha(HERE/'firefox-policy-pins.json')==FIREFOX_PINS,'reviewed Firefox manifest differs')
    manifest=load(HERE/'firefox-policy-pins.json')
    names={'tools/qa/hosted-native/'+x for x in ('firefox_policy_source.cjs','firefox_policy_probe.cjs',
        'firefox_policy_controls.cjs','FIREFOX_POLICY.md','node/package.json','node/package-lock.json')}
    names.update(('tools/qa/r0033_isolation.cjs','tools/qa/v1_net_guard.cjs'))
    need(manifest.get('protocol')=='firefox-policy-source/1' and manifest.get('nativeExecution')=='NOT_RUN'
         and set(manifest.get('files',{}))==names,'Firefox complete source population differs')
    for name,wanted in manifest['files'].items():
        actual=artifact(ROOT/name)
        need(same(wanted,{k:actual[k] for k in ('bytes','sha256')}),'Firefox pinned source drift: '+name)
    for name,wanted in PINS.items():
        need(sha(HERE/name)==wanted,'diagnostic pinned source drift: '+name)
    return {'firefoxManifest':record(HERE/'firefox-policy-pins.json'),'files':dict(PINS),
            'webkitMaterialization':WEBKIT_MATERIALIZATION,'centralReplay':record(HERE/'r003f_diagnostic_replay.cjs')}


def producer_source_files():
    """Explicit complete new diagnostic closure for the known producer identity."""
    verify_sources()
    return sorted({'lanes.py','r003f_diagnostics.py','r003f_diagnostic_replay.cjs',
        'firefox-policy-pins.json',*PINS,
        *(os.path.relpath(ROOT/name,HERE) for name in load(HERE/'firefox-policy-pins.json')['files'])})


def actual_success(value, label):
    need(type(value) is dict and type(value.get('returncode')) is int and value['returncode']==0
         and value.get('timedOut') is False and not value.get('error') and not value.get('retentionError'),
         label+' actual integer zero and no timeout required')
    if 'elapsedSeconds' in value:
        need(type(value['elapsedSeconds']) in (int,float) and math.isfinite(value['elapsedSeconds'])
             and value['elapsedSeconds']>=0,label+' actual elapsed time required')


def runtime_binding(task, runtime, mode):
    need(type(runtime) is dict and set(runtime)=={'node','python','modules','playwright','pngjs','engine'},
         'complete independently acquired diagnostic runtime required')
    for key in ('node','python','modules','playwright','pngjs'):
        need(type(runtime[key]) is str and Path(runtime[key]).is_absolute() and '..' not in Path(runtime[key]).parts,
             'absolute acquired diagnostic runtime required')
    need(runtime['engine']==ROUTES[mode]['engine'],'diagnostic acquired engine differs')
    modules=Path(task)/'node/node_modules'
    need(runtime['modules']==str(modules) and runtime['playwright']==str(modules/'playwright')
         and runtime['pngjs']==str(modules/'pngjs'),'diagnostic acquired module location differs')
    need(same(load(Path(task)/'runtime.json'),runtime),'current task runtime differs from acquired runtime')
    acquisition=load(Path(task)/'capture/acquisition-identity.json')
    need(acquisition.get('protocol')=='salah-hosted-native-acquisition/1'
         and same(acquisition.get('runtime'),runtime),'actual diagnostic acquisition differs')
    return {'runtime':record(Path(task)/'runtime.json'),'acquisition':record(Path(task)/'capture/acquisition-identity.json')}


def bounded(argv, payload, seconds, *, raw=False):
    """One real process bound. Text is a view; raw=True also returns exact stream bytes."""
    process=None;started=time.monotonic()
    try:
        process=subprocess.Popen(argv,cwd=HERE,env=dict(os.environ),stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:
            stdout,stderr=process.communicate(json.dumps(payload,allow_nan=False).encode(),timeout=seconds)
            timed=False
        except subprocess.TimeoutExpired:
            timed=True
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            stdout,stderr=process.communicate()
        return {'argv':argv,'cwd':str(HERE),'timeoutSeconds':seconds,'returncode':process.returncode,
                'timedOut':timed,'elapsedSeconds':time.monotonic()-started,
                'stdout':stdout.decode('utf8',errors='replace'),
                'stderr':stderr.decode('utf8',errors='replace'),
                **({'stdoutBytes':stdout,'stderrBytes':stderr} if raw else {})}
    except OSError as error:
        return {'argv':argv,'cwd':str(HERE),'timeoutSeconds':seconds,'returncode':None,'timedOut':False,
                'elapsedSeconds':time.monotonic()-started,'stdout':'','stderr':str(error),
                **({'stdoutBytes':b'','stderrBytes':b''} if raw else {}),'error':str(error)}
    except BaseException:
        if process is not None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()
        raise


NODE_SOURCE = r"""
const fs=require('fs'),path=require('path'),{isDeepStrictEqual:same}=require('util');
const x=JSON.parse(fs.readFileSync(0,'utf8')),S=require(path.join(x.here,'firefox_policy_source.cjs'));
const need=S.need;need(process.execPath===x.runtime.node,'actual Node differs from acquired runtime');
const source=S.packet(x.firefoxPins);let acquired;
if(x.mode==='firefox-policy')acquired=S.admitAcquisition(x.task,process.execPath);
else {
 const runtime=S.read(path.join(x.task,'runtime.json')),a=S.read(path.join(x.task,'capture/acquisition-identity.json'));
 need(same(runtime,x.runtime)&&same(a.runtime,runtime)&&runtime.engine==='webkit','current WebKit acquisition runtime differs');
 const versions={'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'},packages={};
 need(same(a.nodePackages,versions),'acquired WebKit package versions differ');
 function tree(root){S.safe(root,'directory');const rows={};function walk(dir,depth){need(depth<=64,'package depth exceeded');
  for(const name of fs.readdirSync(dir).sort()){const p=path.join(dir,name),s=fs.lstatSync(p);need(!s.isSymbolicLink(),'package symlink');
   if(s.isDirectory())walk(p,depth+1);else{need(Object.keys(rows).length<4096&&s.isFile(),'package population or type differs');
    const r=S.record(p);rows[path.relative(root,p)]={bytes:r.bytes,sha256:r.sha256};}}}walk(root,0);return rows;}
 for(const [name,version] of Object.entries(versions)){const root=path.join(runtime.modules,name),p=path.join(root,'package.json');
  need(S.read(p).version===version,'current acquired package differs');packages[name]={packageJson:S.record(p),currentFiles:tree(root)};}
 for(const name of ['node/package.json','node/package-lock.json'])need(a.locks[name]===S.record(path.join(x.here,name)).sha256&&
  a.locks[name]===S.record(path.join(x.task,name)).sha256,'installed or acquisition lock differs');
 const descriptor=path.join(runtime.modules,'playwright-core/browsers.json');
 need(a.browserDescriptors.node.sha256===S.record(descriptor).sha256&&same(a.browserDescriptors.node.body,S.read(descriptor)),'browser descriptor differs');
 const executables={};
 for(const [name,wanted] of Object.entries(a.browserExecutables||{}))if(name.startsWith('node-browsers/')){
  need(!path.isAbsolute(name)&&!name.split('/').some(p=>!p||p==='.'||p==='..'),'acquired executable path escapes');
  need(Object.keys(executables).length<4096,'acquired executable bound exceeded');const r=S.record(path.join(x.task,name));
  need(same(wanted,{size:r.bytes,sha256:r.sha256}),'current acquired executable differs');executables[r.path]=r;
 }
 // Reading the already verified package's path resolver starts no browser.
 const previous=process.env.PLAYWRIGHT_BROWSERS_PATH;process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(x.task,'node-browsers');
 const executable=require(runtime.playwright).webkit.executablePath();
 if(previous===undefined)delete process.env.PLAYWRIGHT_BROWSERS_PATH;else process.env.PLAYWRIGHT_BROWSERS_PATH=previous;
 need(executable.startsWith(path.join(x.task,'node-browsers')+path.sep)&&executables[executable],'WebKit path is outside actual acquired executables');
 acquired={task:x.task,runtime,runtimeRecord:S.record(path.join(x.task,'runtime.json')),
  acquisition:S.record(path.join(x.task,'capture/acquisition-identity.json')),packages,descriptor:S.record(descriptor),executable,executables};
}
let materialization=null,harness=null;
if(x.mode==='preconnect-input'){
 const I=require(path.join(x.here,'r003f_preconnect_input.cjs'));
 materialization=I.admitClosure(x.sourceRoot,x.materialization);
 const input=I.deriveIndex(fs.readFileSync(path.join(x.runtimeRoot,'index.html')));
 need(same(materialization.documentInput,input.identity),'current original/served document identity differs');
 const outputs=Object.fromEntries(materialization.outputFiles.map(r=>[r.path,r.sha256]));
 harness={protocol:'R003F/preconnect-input-harness/1',kind:'two exact preconnect spans omitted from served index before parsing',
  materializationSha256:x.materialization,driverSha256:outputs['tools/qa/r003f_owner_baseline.cjs'],
  captureHelperSha256:outputs['tools/qa/r003f_capture.cjs'],uiHelperSha256:outputs['tools/qa/hosted-native/r003f_ui.cjs'],
  inputHelperSha256:outputs['tools/qa/hosted-native/r003f_preconnect_input.cjs']};
}
process.stdout.write(JSON.stringify({source,acquired,materialization,harness}));
"""


def source_payload(mode, task, runtime, prepared):
    return {'mode':mode,'task':str(task),'runtime':runtime,'here':str(HERE),'firefoxPins':FIREFOX_PINS,
            'sourceRoot':str(paths(task,mode)['source']),'materialization':WEBKIT_MATERIALIZATION,
            'runtimeRoot':prepared['trees']['r003f']['root']}


def node_source(mode, task, runtime, prepared):
    check=bounded([runtime['node'],'-e',NODE_SOURCE],source_payload(mode,task,runtime,prepared),SOURCE_SECONDS)
    actual_success(check,'actual diagnostic source verifier')
    return json.loads(check['stdout'])


def preparation_argv(mode, task, runtime):
    return [runtime['python'],'-B',str(HERE/'r003f_diagnostics.py'),'prepare','--mode',mode,
            '--task',str(task),'--node',runtime['node']]


def preparation_child(mode, task, runtime, prepared):
    if mode=='firefox-policy':
        return [runtime['node'],'-e',NODE_SOURCE]
    return [runtime['node'],str(HERE/'r003f_preconnect_materialize.cjs'),'--source',
            prepared['sources']['research']['root'],'--runtime',prepared['trees']['r003f']['root'],
            '--out',str(paths(task,mode)['source'])]


def custody_prefix(mode, task, runtime):
    """No copied executable or path reaches an optional verifier before this check."""
    p=paths(task,mode);binding=runtime_binding(task,runtime,mode);sources=verify_sources()
    prepared=load(p['common']);context=load(p['commonContext']);common=load(p['commonProcess'])
    expected=[runtime['python'],str(HERE/'prepare.py')]
    for key in ('research','baseline','historical'):
        expected+=['--'+key,prepared['sources'][key]['root']]
    expected+=['--out',str(Path(task)/'work/prepared')]
    need(same(context.get('argv'),expected) and context.get('cwd')==str(HERE)
         and context.get('sourceSha256')==PINS['prepare.py'] and type(context.get('timeoutSeconds')) is int
         and context['timeoutSeconds']==900,'common actual acquired Python, source, path or bound differs')
    actual_success(common,'common preparation')
    entry=load(p['preparationEntry']);child=load(p['preparationProcess'])
    actual_success(entry,'diagnostic preparation entry');actual_success(child,'diagnostic preparation child')
    need(entry.get('protocol')==PREPARATION_ENTRY and same(entry.get('argv'),preparation_argv(mode,task,runtime))
         and entry.get('cwd')==str(HERE) and type(entry.get('timeoutSeconds')) is int and entry['timeoutSeconds']==180
         and entry.get('sourceSha256')==sha(HERE/'r003f_diagnostics.py')
         and entry.get('process')==str(p['preparationProcess']),'actual diagnostic preparation entry differs')
    need(child.get('protocol')==PREPARATION and child.get('status')=='PREPARED'
         and child.get('nativeExecution')=='NOT_RUN' and child.get('mode')==mode and child.get('task')==str(task)
         and same(child.get('runtime'),runtime) and same(child.get('argv'),preparation_child(mode,task,runtime,prepared))
         and child.get('cwd')==str(HERE) and type(child.get('timeoutSeconds')) is int and child['timeoutSeconds']==60,
         'actual diagnostic preparation child command, runtime or bound differs')
    streams={name:artifact(p['preparation']/('child.'+name)) for name in ('stdout','stderr')}
    need(same(child.get('streams'),streams),'actual diagnostic preparation child stream bytes differ')
    outer={name:artifact(Path(task)/'capture'/('r003f-diagnostic-preparation.'+name)) for name in ('stdout','stderr')}
    common_streams={name:artifact(Path(task)/'capture'/('preparation.'+name)) for name in ('stdout','stderr')}
    return {'paths':p,'prepared':prepared,'entry':entry,'child':child,'binding':binding,'sources':sources,
            'streams':streams,'outerStreams':outer,'commonStreams':common_streams}


def common_custody(p, native):
    return common_support.common_custody(p['common'],p['commonProcess'],p['commonContext'],native=native)


def admit(mode, task, runtime, *, native=True):
    prefix=custody_prefix(mode,task,runtime);p=prefix['paths']
    prepared,common=common_custody(p,native)
    need(same(prefix['prepared'],prepared) and same(prefix['child'].get('common'),common),
         'current complete common preparation differs from actual diagnostic child')
    source=node_source(mode,task,runtime,prepared)
    need(same(prefix['child'].get('source'),source) and same(prefix['child'].get('sources'),prefix['sources'])
         and same(prefix['child'].get('binding'),prefix['binding']), 'current diagnostic source/acquisition differs from preparation')
    if mode=='preconnect-input':
        need((p['preparation']/'child.stdout').read_bytes()==regular(p['source']/'materialization.json').read_bytes(),
             'actual materializer stdout differs from retained deterministic source receipt')
    return {'status':'PASS','protocol':ADMISSION,'mode':mode,'task':str(task),'runtime':runtime,
        'research':prepared['sources']['research']['root'],'runtimeRoot':prepared['trees']['r003f']['root'],
        'sourceRoots':{k:prepared['sources'][k]['root'] for k in ('research','baseline','historical')},
        'common':common,'entry':record(p['preparationEntry']),'child':record(p['preparationProcess']),
        'binding':prefix['binding'],'sources':prefix['sources'],'source':source,
        'streams':prefix['streams'],'outerStreams':prefix['outerStreams'],'commonStreams':prefix['commonStreams']}


def prepare(mode, task, runtime):
    p=paths(task,mode);p['preparation'].mkdir(mode=0o700)
    row={'protocol':PREPARATION,'status':'INCOMPLETE','mode':mode,'task':str(task),'runtime':runtime,
         'nativeExecution':'NOT_RUN','returncode':None,'timedOut':False}
    try:
        row['binding']=runtime_binding(task,runtime,mode);row['sources']=verify_sources()
        context=load(p['commonContext'])
        need(context.get('argv',[None])[0]==runtime['python'],'common preparation Python differs from acquired runtime')
        prepared,row['common']=common_custody(p,False)
        argv=preparation_child(mode,task,runtime,prepared)
        payload=source_payload(mode,task,runtime,prepared) if mode=='firefox-policy' else {}
        check=bounded(argv,payload,60,raw=True)
        for name in ('stdout','stderr'):
            with (p['preparation']/('child.'+name)).open('xb') as stream:
                os.chmod(stream.name,0o600);stream.write(check[name+'Bytes']);stream.flush();os.fsync(stream.fileno())
        row.update({k:check[k] for k in ('argv','cwd','timeoutSeconds','returncode','timedOut','elapsedSeconds')})
        row['streams']={name:artifact(p['preparation']/('child.'+name)) for name in ('stdout','stderr')}
        actual_success(check,'diagnostic source preparation')
        row['source']=json.loads(check['stdout']) if mode=='firefox-policy' else node_source(mode,task,runtime,prepared)
        row['status']='PREPARED'
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        row['error']=str(error)
    finally:
        save(p['preparationProcess'],row)
    return row


def make_lane(mode, admission, task, runtime):
    route=ROUTES[mode];b=budget(mode);p=paths(task,mode);out=Path(task)/'capture/lanes'
    admission=admission or {'status':'INCOMPLETE','reason':'diagnostic source preparation is missing'}
    row={'id':route['id'],'workOrder':'R003F','engine':route['engine'],'dpr':1,'cwd':str(HERE),
        'env':{'NODE_PATH':runtime['modules']},'output':str(p['output']),
        'stdout':str(out/(route['id']+'.stdout')),'stderr':str(out/(route['id']+'.stderr')),
        'timeoutSeconds':b['entrySeconds'],'preExecutionCheckSeconds':120,'postCaptureCheckSeconds':b['finalSeconds'],
        'diagnosticRuntime':runtime,'diagnosticObservation':{'protocol':'R003F/diagnostic-observation/1',
            'mode':mode,'instrumented':True,'budget':b,**scope_fields(mode)},
        'result':{'kind':route['kind'],'path':str(p['result']),'entryProcessPath':str(p['entryProcess']),
                  'isolationReceiptPath':str(p['isolation'])},
        'exitStatuses':{'0':route['status'],'1':'INCOMPLETE','2':'INCOMPLETE','86':'ISOLATION_FAIL'},
        'dependsOn':[],'stopScopeOnAndon':'R003F','stopAllOnExit':[86],
        'preparation':admission,'argv':[]}
    if mode=='preconnect-input':
        row['exitStatuses'].update({'3':'ISOLATION_FAIL','4':'ANDON'});row['stopAllOnExit']=[3,86]
        row['result'].update(expectedCaptures=['offset','b0','b0-repeat','reference'],
                             expectedHarness=admission.get('source',{}).get('harness'),
                             materialization=WEBKIT_MATERIALIZATION)
    if admission.get('status')=='PASS':
        if mode=='firefox-policy':
            row['argv']=[runtime['node'],str(HERE/'firefox_policy_probe.cjs'),'--task',str(task),'--out',str(p['output']),
                         '--isolation',str(p['isolation']),'--pins-sha256',FIREFOX_PINS]
        else:
            row['argv']=[runtime['node'],str(p['source']/'tools/qa/r003f_owner_baseline.cjs'),
                '--root',admission['runtimeRoot'],'--out',str(p['output']),'--engine','webkit','--dpr','1',
                '--playwright',runtime['playwright'],'--pngjs',runtime['pngjs'],
                '--materialization-sha256',WEBKIT_MATERIALIZATION]
    return row


def mode_for_lane(lane):
    kind=lane.get('result',{}).get('kind') if type(lane) is dict else None
    return next((mode for mode,r in ROUTES.items() if r['kind']==kind),None)


def admit_runtime(lane, runtime):
    mode=mode_for_lane(lane)
    need(mode is not None and same(lane.get('diagnosticRuntime'),runtime),
         'diagnostic runtime differs from independently acquired runtime')
    need(lane.get('env')=={'NODE_PATH':runtime['modules']},'diagnostic acquired module environment differs')
    if lane.get('preparation',{}).get('status')=='INCOMPLETE':
        need(lane.get('argv')==[],'incomplete diagnostic cannot execute a substitute');return
    need(lane.get('argv',[None])[0]==runtime['node'],'diagnostic executable differs from acquired runtime')
    task=Path(lane['preparation']['task'])
    canonical=make_lane(mode,lane['preparation'],task,runtime)
    need(same(lane,canonical),'diagnostic canonical command or scope differs from acquired runtime')


def readmit(mode, task, runtime):
    return bounded([runtime['python'],'-B',str(HERE/'r003f_diagnostics.py'),'readmit'],
                   {'mode':mode,'task':str(task),'runtime':runtime},120,raw=True)


def namespace_admitted(lane, inner):
    mode=mode_for_lane(lane);statuses={r['status'] for r in ROUTES.values()}
    if mode is None:return inner.get('status') not in statuses
    status=inner.get('status')
    if status in statuses:
        return (status==ROUTES[mode]['status'] and type(inner.get('returncode')) is int and inner['returncode']==0
            and inner.get('timedOut') is False and inner.get('stopAll') is False
            and all(same(inner.get(k),v) for k,v in scope_fields(mode).items()))
    return status in ('FAIL','INCOMPLETE','INCONCLUSIVE','ANDON','ISOLATION_FAIL')


def pipeline_admitted(campaign, plan, observation, lane, row, task):
    """A producer's terminal diagnostic label is not an original-B0 success alias."""
    mode=mode_for_lane(lane);selected=campaign.get('r003fHarness')
    statuses={r['status'] for r in ROUTES.values()}
    if mode is None and selected not in ROUTES:
        return row.get('status') not in statuses
    if mode!=selected:return False
    try:controls(mode,campaign.get('workOrders'),campaign.get('engine'),campaign.get('r003fDpr'),campaign.get('evidenceRetention',False))
    except (ValueError,KeyError,TypeError):return False
    if (plan.get('r003fHarness')!=mode or observation.get('r003fHarness')!=mode
            or lane.get('id')!=ROUTES[mode]['id'] or lane.get('engine')!=ROUTES[mode]['engine']
            or lane.get('workOrder')!='R003F' or type(lane.get('dpr')) is not int or lane['dpr']!=1):return False
    try:
        runtime=load(Path(task)/'runtime.json')
        runtime_binding(task,runtime,mode)
        if not same(lane,make_lane(mode,lane.get('preparation'),task,runtime)):return False
    except (OSError,ValueError,KeyError,TypeError):return False
    status=row.get('status')
    if status=='NOT_RUN':return True
    if status in statuses:
        inner=row.get('innerStatus');process=row.get('namespaceProcess')
        return (type(inner) is dict and type(process) is dict and inner.get('id')==lane['id']
            and inner.get('status')==status and namespace_admitted(lane,inner)
            and namespace_admitted(lane,row) and type(process.get('returncode')) is int
            and process['returncode']==0 and process.get('timedOut') is False)
    return status in ('FAIL','INCOMPLETE','INCONCLUSIVE','ANDON','ISOLATION_FAIL','ISOLATION_UNCONFIRMED')


def record_entry(lane, actual):
    mode=mode_for_lane(lane);need(mode is not None,'diagnostic entry kind required')
    need(type(actual.get('returncode')) is int and type(actual.get('timedOut')) is bool,
         'actual diagnostic process completion required')
    body={'protocol':ENTRY_PROCESS,**actual,'argv':lane['argv'],'cwd':lane['cwd'],
          'timeoutSeconds':lane['timeoutSeconds'],'mode':mode,
          'streams':{k:artifact(lane[k]) for k in ('stdout','stderr')}}
    save(lane['result']['entryProcessPath'],body)
    return body


def final_check(lane, returncode, timed_out):
    mode=mode_for_lane(lane);runtime=lane['diagnosticRuntime']
    need(type(returncode) is int and returncode==0 and timed_out is False,'actual diagnostic entry did not succeed')
    return bounded([runtime['python'],'-B',str(HERE/'r003f_diagnostics.py'),'final'],
        {'lane':lane,'returncode':returncode,'timedOut':timed_out},budget(mode)['finalSeconds'])


NODE_FINAL_PATH = HERE/'r003f_diagnostic_replay.cjs'


def final_intake(payload):
    lane=payload['lane'];mode=mode_for_lane(lane);need(mode is not None,'exact final diagnostic kind required')
    runtime=lane['diagnosticRuntime'];need(runtime['python']==sys.executable,'actual final Python differs from acquisition')
    task=Path(lane['preparation']['task']);p=paths(task,mode)
    current=admit(mode,task,runtime,native=True)
    need(same(current,lane['preparation']),'final actual preparation/current source differs from lane')
    canonical=make_lane(mode,current,task,runtime)
    need(same({k:v for k,v in lane.items() if k!='preExecutionCurrentness'},canonical),'final canonical diagnostic lane differs')
    actual=load(p['entryProcess']);actual_success(actual,'actual diagnostic entry')
    need(type(payload.get('returncode')) is int and payload['returncode']==0 and payload.get('timedOut') is False
         and actual.get('protocol')==ENTRY_PROCESS and actual.get('mode')==mode and same(actual.get('argv'),lane['argv'])
         and actual.get('cwd')==str(HERE) and type(actual.get('timeoutSeconds')) is int
         and actual['timeoutSeconds']==budget(mode)['entrySeconds']
         and same(actual.get('streams'),{k:artifact(lane[k]) for k in ('stdout','stderr')}),
         'actual diagnostic entry receipt, command, bound or streams differ')
    check=bounded([runtime['node'],str(NODE_FINAL_PATH)],
        {'mode':mode,'task':str(task),'here':str(HERE),'runtime':runtime,'source':current['source'],
         'firefoxPins':FIREFOX_PINS,'sourceRoot':str(p['source']),'materialization':WEBKIT_MATERIALIZATION,
         'runtimeRoot':current['runtimeRoot'],'output':str(p['output']),'file':str(p['result']),
         'entryProcess':str(p['entryProcess']),'isolation':str(p['isolation']),'argv':lane['argv'],
         'protocol':FINAL,'status':ROUTES[mode]['status'],'scope':scope_fields(mode),
         'sourceAdmission':{'entry':current['entry'],'child':current['child'],'common':current['common']}},
        budget(mode)['finalNodeSeconds'])
    if check['returncode'] in (4,86):
        return {'status':'ISOLATION_FAIL' if check['returncode']==86 else 'ANDON','verification':check,**scope_fields(mode)},check['returncode']
    actual_success(check,'actual retained diagnostic replay')
    value=json.loads(check['stdout']);value['replayProcess']=check
    return value,0


def classify(lane, body, returncode, timed_out):
    mode=mode_for_lane(lane);result={'status':'INCOMPLETE','stopAll':False,**scope_fields(mode)}
    if returncode==86 or mode=='preconnect-input' and returncode==3:
        return {**result,'status':'ISOLATION_FAIL','stopAll':True}
    if isinstance(body,dict) and (body.get('status') in ('ISOLATION_FAIL','ISOLATION FAIL')
        or any(isinstance(body.get(key),dict) and body[key].get('ok') is False for key in ('isolation','network'))):
        return {**result,'status':'ISOLATION_FAIL','stopAll':True}
    if mode=='preconnect-input' and (returncode==4 or isinstance(body,dict) and body.get('status')=='FAIL (Andon)'):
        return {**result,'status':'ANDON'}
    if type(returncode) is not int or returncode!=0 or timed_out is not False or not isinstance(body,dict):return result
    try:
        check=final_check(lane,returncode,timed_out);result['diagnosticVerification']=check
        if check.get('returncode')==86:return {**result,'status':'ISOLATION_FAIL','stopAll':True}
        if mode=='preconnect-input' and check.get('returncode')==4:return {**result,'status':'ANDON'}
        actual_success(check,'diagnostic actual final intake')
        value=json.loads(check['stdout'])
        need(value.get('protocol')==FINAL and value.get('status')==ROUTES[mode]['status']
             and all(same(value.get(k),v) for k,v in scope_fields(mode).items()),'diagnostic final scope or status differs')
        result.update(status=value['status'],diagnosticIntake=value)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:result['reason']=str(error)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','readmit','final'))
    parser.add_argument('--mode',choices=tuple(ROUTES));parser.add_argument('--task',type=Path);parser.add_argument('--node')
    args=parser.parse_args();os.umask(0o077)
    try:
        if args.action=='prepare':
            need(args.mode and args.task and args.node,'complete diagnostic preparation arguments required')
            runtime=load(args.task/'runtime.json')
            need(runtime['python']==sys.executable and runtime['node']==args.node,'actual preparation interpreter differs from acquisition')
            value=prepare(args.mode,args.task,runtime);code=0 if value['status']=='PREPARED' else 2
        else:
            payload=json.load(sys.stdin)
            if args.action=='readmit':
                runtime=payload['runtime'];need(runtime['python']==sys.executable,'actual readmission Python differs from acquisition')
                value=admit(payload['mode'],Path(payload['task']),runtime,native=True);code=0
            else:
                value,code=final_intake(payload)
        print(json.dumps(value,allow_nan=False));return code
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'INCOMPLETE','error':str(error)}));return 2


if __name__=='__main__':raise SystemExit(main())
