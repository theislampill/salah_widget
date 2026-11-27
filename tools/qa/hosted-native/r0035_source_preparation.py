"""Exact hosted SOURCE-ONLY preparation; no acquisition, observation or native CLI.

Target source is validated before import. The only original native-facing call
is readmission with --native, which must refuse before any execution is possible.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import traceback

HERE=Path(__file__).absolute().parent
ROOT=HERE.parents[2]
CONTRACT=HERE/'r0035-source-preparation.json'
CONTRACT_CANONICAL_SHA256='26bea9fae7d6cc286203c3170c38609f0a0e9936c323518a96d62e8812256136'
PROTOCOL='r0035-hosted-source-preparation-result/1'
REPOSITORY='theislampill/salah_widget'
BRANCH='chatgpt/r0035-source-preparation-20261127'
WORKFLOW='.github/workflows/r0035-source-preparation.yml'
ROLES=('harness','target','research','baseline','historical')
SOURCE_DIRS=('src','real-sky','tools','moon','vendor','v1','tests')
HISTORICAL=['tools/qa/precip_eval_lib.cjs','tools/qa/precip_models_geom.js','tools/qa/precip_declared_gain.json',
            'tools/qa/precip_models.js','tools/qa/precip_models_capture.cjs','tools/qa/precip_models_post.py']
NATIVE_REFUSAL='ValueError: native common preparation was not isolated by hosted execution'


def need(value,message):
    if not value:raise ValueError(message)


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
def sha(value):return hashlib.sha256(value).hexdigest()


def load(path):
    def pairs(rows):
        result={}
        for key,value in rows:need(key not in result,'duplicate JSON field');result[key]=value
        return result
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def save(path,value):
    with Path(path).open('xb') as stream:stream.write(canonical(value))


def validate_contract(value):
    need(type(value) is dict and sha(canonical(value))==CONTRACT_CANONICAL_SHA256,'complete pinned source-only contract differs')
    return value


def validate_workflow(root,contract):
    need(sha(literal(Path(root)/contract['workflowPath']).read_bytes())==contract['workflowSha256'],
         'complete reviewed source-only workflow bytes differ')


def clean_environment():
    rejected={'NODE_OPTIONS','NODE_PATH','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONINSPECT','PYTHONPYCACHEPREFIX',
              'LD_PRELOAD','LD_LIBRARY_PATH','BASH_ENV','ENV','CDPATH','VIRTUAL_ENV','PLAYWRIGHT_BROWSERS_PATH'}
    env={k:v for k,v in os.environ.items() if k not in rejected and not k.startswith(('GIT_','PIP_','npm_config_','NPM_CONFIG_'))}
    env.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL='/dev/null',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONUTF8='1',
               PIP_CONFIG_FILE='/dev/null',PIP_NO_INPUT='1',PIP_DISABLE_PIP_VERSION_CHECK='1',
               NPM_CONFIG_USERCONFIG='/dev/null',PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1')
    return env


def safe_relative(name):
    need(type(name) is str and bool(name) and '\\' not in name and not any(ord(x)<32 or ord(x)==127 for x in name),'source path required')
    p=PurePosixPath(name);need(not p.is_absolute() and str(p)==name and '..' not in p.parts,'source path escapes root');return name


def literal(path):
    path=Path(path).absolute();need('..' not in path.parts and path.resolve()==path and not any(p.is_symlink() for p in (path,*path.parents)),'literal source path required');return path


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],env=clean_environment(),stderr=subprocess.PIPE,timeout=20).decode().strip()


def source_identity(root,names):
    root=literal(root);need(type(names) is list and names and len(names)==len(set(names)),'unique declared source paths required')
    for name in names:safe_relative(name)
    need(not git(root,'status','--porcelain','--untracked-files=all'),'source checkout is not clean')
    need(not any(root.rglob('*.pyc')) and not any(root.rglob('*.pyo')),'source bytecode cache is outside declared executable closure')
    raw=subprocess.check_output(['git','-C',str(root),'ls-tree','-rz','HEAD','--',*names],env=clean_environment(),stderr=subprocess.PIPE,timeout=20)
    files={}
    for item in raw.split(b'\0'):
        if not item:continue
        metadata,name=item.split(b'\t',1);mode,kind,blob=metadata.decode().split();name=name.decode();safe_relative(name)
        need(kind=='blob' and mode in ('100644','100755'),'nonregular source Git entry')
        path=literal(root/name);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            info=os.fstat(fd);need(stat.S_ISREG(info.st_mode),'nonregular source file');size=0
            actual=hashlib.sha1(b'blob '+str(info.st_size).encode()+b'\0');digest=hashlib.sha256()
            while True:
                block=os.read(fd,1<<20)
                if not block:break
                size+=len(block);need(size<=info.st_size,'source changed while reading');actual.update(block);digest.update(block)
            after=os.fstat(fd)
            need(size==info.st_size and (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)==
                 (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'source changed while reading')
            need(actual.hexdigest()==blob,'source bytes differ from immutable Git blob')
            need(bool(info.st_mode&0o111)==(mode=='100755'),'source executable mode differs')
            files[name]={'bytes':size,'sha256':digest.hexdigest(),'gitBlob':blob,'mode':mode}
        finally:os.close(fd)
    need(files and all(any(n==p or n.startswith(p+'/') for n in files) for p in names),'required declared source absent')
    return {'protocol':'source-only-declared-git-inputs/1','root':str(root),'commit':git(root,'rev-parse','HEAD'),
            'tree':git(root,'rev-parse','HEAD^{tree}'),'clean':True,'files':dict(sorted(files.items()))}


def validate_host(env,os_release,node_version,python_version):
    expected_ref='refs/heads/'+BRANCH;expected_workflow=REPOSITORY+'/'+WORKFLOW+'@'+expected_ref
    need(env.get('GITHUB_ACTIONS')=='true' and env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')==expected_ref
         and env.get('GITHUB_WORKFLOW_REF')==expected_workflow,'separate source-only workflow identity differs')
    need(type(env.get('GITHUB_SHA')) is str and re.fullmatch('[0-9a-f]{40}',env['GITHUB_SHA']),'actual workflow source SHA required')
    need(env.get('GITHUB_WORKFLOW_SHA',env['GITHUB_SHA'])==env['GITHUB_SHA'],'workflow source and executed ref differ')
    need(os_release.get('ID')=='ubuntu' and os_release.get('VERSION_ID')=='22.04' and node_version=='v24.14.0'
         and tuple(python_version)==(3,11),'original hosted OS/Node/Python pins differ')
    numbers={}
    for name,key in (('runId','GITHUB_RUN_ID'),('runAttempt','GITHUB_RUN_ATTEMPT')):
        raw=env.get(key,'');need(type(raw) is str and re.fullmatch('[1-9][0-9]*',raw),'positive actual workflow run required');numbers[name]=int(raw)
    return {'repository':REPOSITORY,'workflowPath':WORKFLOW,'workflowRef':expected_workflow,'workflowCommit':env['GITHUB_SHA'],**numbers}


def command_for_phase(phase,task,roots,runtime):
    here=roots['target']/'tools/qa/hosted-native';task=Path(task).absolute()
    if phase=='common':
        # Literal original common argv deliberately has no extra -B operand.
        argv=[runtime['python'],str(here/'prepare.py'),'--research',str(roots['research']),'--baseline',str(roots['baseline']),
              '--historical',str(roots['historical']),'--out',str(task/'work/prepared')];seconds=900
    elif phase=='derived':argv=[runtime['python'],'-B',str(here/'r0035_publish.py'),'prepare','--task',str(task)];seconds=240
    elif phase in ('readmit','refusal'):
        argv=[runtime['python'],'-B',str(here/'r0035_publish.py'),'readmit','--task',str(task),*(['--native'] if phase=='refusal' else [])];seconds=120
    else:raise ValueError('unavailable source-only phase')
    return {'argv':argv,'cwd':str(here),'timeoutSeconds':seconds}


def native_refusal(process):
    need(type(process.get('returncode')) is int and process['returncode']==1 and process.get('timedOut') is False
         and process.get('error') is None and process.get('retentionError') is None and process.get('stdout')==''
         and type(process.get('stderr')) is str and process['stderr'].strip().splitlines()[-1:]==[NATIVE_REFUSAL],
         'original specific source-only native refusal was not observed')
    return True


def roots_for(workspace):
    workspace=literal(workspace)
    return {'harness':workspace/'source-preparation','target':workspace/'target',
            **{name:workspace/name for name in ('research','baseline','historical')}}


def validate_inputs(contract,roots,host):
    result={};result['harness']=source_identity(roots['harness'],contract['harnessFiles'])
    need(result['harness']['commit']==host['workflowCommit'] and roots['harness']==ROOT,'actual harness checkout differs from workflow source')
    validate_workflow(roots['harness'],contract)
    target=contract['target'];manifest_path=roots['target']/target['sourceManifestPath']
    need(sha(literal(manifest_path).read_bytes())==target['sourceManifestSha256'],'target source closure manifest differs')
    manifest=load(manifest_path);need(len(manifest['sourceFiles'])==target['sourceFiles'],'complete target closure count differs')
    result['target']=source_identity(roots['target'],manifest['sourceFiles'])
    need(result['target']['commit']==target['commit'] and result['target']['tree']==target['tree'],'immutable receiving target differs')
    need(result['target']['files'][target['campaignPath']]['sha256']==target['campaignSha256'],'actual selected campaign differs')
    for role in ('harness','target'):
        need(result[role]['files']['.github/workflows/research-native-pilot.yml']['sha256']==target['nativeWorkflowSha256'],'original native workflow changed')
    for role in ('research','baseline','historical'):
        names=list(SOURCE_DIRS)
        if role=='research':names+=['docs/state-contracts/evidence/R0040/phase1-options.patch.gz']
        elif role=='baseline':names+=['index.html','offline.html','config.js','builder.html','GENERATED.json','.gitignore']
        else:names=HISTORICAL
        value=source_identity(roots[role],names);expected=contract['sources'][role]
        need(value['commit']==expected['commit'] and value['tree']==expected['tree'],'immutable original source differs: '+role);result[role]=value
    here=roots['target']/'tools/qa/hosted-native'
    for name,key in (('node/package.json','packageJsonSha256'),('node/package-lock.json','packageLockSha256'),('requirements.txt','requirementsSha256')):
        need(sha((here/name).read_bytes())==contract['runtime'][key],'actual locked driver input differs')
    return result


def import_target(roots,identities):
    here=roots['target']/'tools/qa/hosted-native';need(str(here) not in sys.path,'target import already initialized')
    for name in ('r0035_publish','r0035_psf','prepare','r002f_bfcache_central','r003f_matrix_campaign'):
        need(name not in sys.modules,'foreign target module already loaded')
    sys.path.insert(0,str(here));import r0035_publish as publish
    actual=publish.source_identity();need(actual['commit']==identities['target']['commit'] and actual['tree']==identities['target']['tree']
        and actual['files']==identities['target']['files'],'original current source identity differs from preimport admission')
    return publish


class Deadline(Exception):pass


def arm_deadline(deadline):
    remaining=deadline-time.monotonic();need(remaining>0,'source-only phase ceiling exhausted');signal.setitimer(signal.ITIMER_REAL,remaining)


def dependency_inventory(root):
    from r0035_source_payload import file_record
    rows={}
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in list(dirs):
            if (Path(current)/name).is_symlink():files.append(name);dirs.remove(name)
        for name in files:
            path=Path(current)/name;relative=path.relative_to(root).as_posix()
            if path.is_symlink():
                target=os.readlink(path)
                interpreter=(relative in ('python/bin/python','python/bin/python3','python/bin/python3.11')
                             and path.resolve()==Path(sys.executable).resolve())
                need(path.resolve().is_relative_to(root) or interpreter,'installed package link escapes declared runtime')
                rows[relative]={'kind':'symlink','target':target}
            else:rows[relative]={'kind':'file',**file_record(path,1<<30)}
    return dict(sorted(rows.items()))


def install_source_runtime(task,roots,node,supervisor,environment,record):
    # Materialize exact locked SDK dependencies. No managed browser installer is
    # called; package scripts are disabled and a fresh empty browser path is set.
    directory=task/'source-runtime';directory.mkdir(mode=0o700);(directory/'node').mkdir(mode=0o700)
    here=roots['target']/'tools/qa/hosted-native'
    for name in ('package.json','package-lock.json'):shutil.copyfile(here/'node'/name,directory/'node'/name)
    environment.update(PLAYWRIGHT_BROWSERS_PATH=str(directory/'unused-browsers'))
    commands=[('python-environment',[sys.executable,'-B','-m','venv',str(directory/'python')],60),
              ('node-packages',[str(Path(node).with_name('npm')),'ci','--prefix',str(directory/'node'),'--ignore-scripts','--no-audit','--no-fund','--omit=optional','--registry=https://registry.npmjs.org'],300),
              ('python-packages',[str(directory/'python/bin/python'),'-B','-m','pip','install','--require-hashes','--only-binary=:all:',
                                  '--no-cache-dir','--index-url','https://pypi.org/simple','-r',str(here/'requirements.txt')],300)]
    from r0035_source_supervisor import successful
    for label,argv,seconds in commands:
        process=supervisor.run(argv,str(task),environment,record/(label+'.stdout'),record/(label+'.stderr'),seconds)
        save(record/(label+'-process.json'),process);successful(process)
    runtime={'python':str(directory/'python/bin/python'),'node':node,'modules':str(directory/'node/node_modules')}
    runtime.update(playwright=str(Path(runtime['modules'])/'playwright'),pngjs=str(Path(runtime['modules'])/'pngjs'))
    node_versions={name:load(Path(runtime['modules'])/name/'package.json')['version'] for name in ('playwright','playwright-core','pngjs')}
    need(node_versions=={'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'},'actual source SDK versions differ')
    code="import importlib.metadata,json,sys,sysconfig; print(json.dumps({'python':sys.version,'version':list(sys.version_info[:2]),'site':sysconfig.get_paths()['purelib'],'packages':{n:importlib.metadata.version(n) for n in ('playwright','pyee','greenlet','typing_extensions')}}))"
    process=supervisor.run([runtime['python'],'-B','-c',code],str(task),environment,record/'package-identity.stdout',record/'package-identity.stderr',30)
    save(record/'package-identity-process.json',process);successful(process);python=json.loads(process['stdout'])
    need(python['version']==[3,11] and python['packages']=={'playwright':'1.57.0','pyee':'13.0.0','greenlet':'3.2.4','typing_extensions':'4.15.0'},'actual Python source SDK versions differ')
    need(not (directory/'unused-browsers').exists(),'source-only route installed a managed browser')
    from r0035_source_payload import file_record
    identity={'protocol':'source-only-installed-driver-dependencies/1','nativeIsolationClaim':False,'nativeExecution':'NOT_RUN',
        'runtime':runtime,'nodePackages':node_versions,'python':python,'binaries':{name:{'path':runtime[name],
            'resolved':str(Path(runtime[name]).resolve()),**file_record(Path(runtime[name]).resolve(),1<<30)} for name in ('python','node')},
        'installedFiles':dependency_inventory(directory),'managedBrowserPopulation':[]}
    save(record/'dependency-identity.json',identity);save(task/'runtime.json',runtime);return runtime,identity


def verify_quiescence(value):
    need(value.get('quiescent') is True and value.get('unexpectedDescendants') is False,'source process left detached descendants')


def run(task,workspace):
    os.umask(0o077);sys.dont_write_bytecode=True;task=literal(task);roots=roots_for(workspace);record=task/'records'
    need(task.is_dir() and record.is_dir() and not (record/'result.json').exists(),'fresh owned source-only task required')
    need(task==literal(os.environ['RUNNER_TEMP'])/('salah-source-preparation-'+os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']),'actual source-only task path differs')
    contract=validate_contract(load(CONTRACT));result={'protocol':PROTOCOL,'scope':'SOURCE_ONLY','status':'INCOMPLETE',
        'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','speed':'NOT_ESTABLISHED','stage':'input-validation',
        'task':str(task),'roots':{k:str(v) for k,v in roots.items()},'actualProcesses':[],'failures':[]}
    sources={name:{'status':'NOT_ADMITTED','root':str(root)} for name,root in roots.items()};supervisor=None
    started=time.monotonic();overall=started+contract['limits']['sourceCoordinatorSeconds'];environment=clean_environment()
    os.environ.clear();os.environ.update(environment)
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(Deadline('actual source-only phase ceiling reached')));arm_deadline(overall)
    try:
        node=str(Path(shutil.which('node')).resolve());node_version=subprocess.check_output([node,'--version'],env=environment,text=True,timeout=10).strip()
        release={k:v.strip('"') for k,v in (line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)}
        host=validate_host(environment,release,node_version,sys.version_info[:2]);sources=validate_inputs(contract,roots,host)
        save(record/'sources-before.json',sources)
        binding={**host,'workflowTree':sources['harness']['tree'],'targetCommit':sources['target']['commit'],'targetTree':sources['target']['tree'],
                 'campaignSha256':contract['target']['campaignSha256'],'contractSha256':sha(CONTRACT.read_bytes())}
        save(record/'binding.json',binding);result.update(binding=binding,host={'osRelease':release,'nodeVersion':node_version,'pythonVersion':sys.version})
        from r0035_source_supervisor import Supervisor,successful
        supervisor=Supervisor();save(record/'coordinator-identity.json',{'pid':supervisor.pid,'startTicks':supervisor.started})
        result['stage']='locked-source-runtime';arm_deadline(min(overall,time.monotonic()+720))
        runtime,dependency_before=install_source_runtime(task,roots,node,supervisor,environment,record)
        environment.update(NODE_PATH=runtime['modules'],PATH=str(Path(node).parent)+os.pathsep+environment['PATH'])
        os.environ.update(environment);publish=import_target(roots,sources)
        preparation_started=time.monotonic();arm_deadline(min(overall,preparation_started+1350));result['stage']='original-common-preparation'
        common=command_for_phase('common',task,roots,runtime)
        save(task/'capture/preparation-context.json',{'protocol':'source-only-common-preparation-execution/1',**common,
            'sourceSha256':sha((roots['target']/'tools/qa/hosted-native/prepare.py').read_bytes()),'nativeIsolationClaim':False})
        process=supervisor.run(common['argv'],common['cwd'],environment,task/'capture/preparation.stdout',task/'capture/preparation.stderr',common['timeoutSeconds'])
        save(task/'capture/preparation-process.json',process);result['actualProcesses'].append('task/capture/preparation-process.json');successful(process);publish.success(process,'actual original common preparation',900)
        result['stage']='derived-source-preparation';derived=command_for_phase('derived',task,roots,runtime)
        process=supervisor.run(derived['argv'],derived['cwd'],environment,task/'capture/r0035-publish-preparation.stdout',task/'capture/r0035-publish-preparation.stderr',240)
        save(record/'derived-process.json',process);result['actualProcesses'].append('records/derived-process.json')
        entry=publish.preparation_entry(task,runtime,process);successful(process);publish.success(entry,'actual derived source preparation',240)
        result['stage']='source-currentness';readmit=command_for_phase('readmit',task,roots,runtime)
        process=supervisor.run(readmit['argv'],readmit['cwd'],environment,record/'readmission.stdout',record/'readmission.stderr',120)
        save(record/'readmission-process.json',process);result['actualProcesses'].append('records/readmission-process.json');successful(process)
        admission=publish.admitted_process(process,task,runtime,False);need(admission['nativePreparation'] is False,'source currentness acquired native authority')
        result['preparationElapsedSeconds']=time.monotonic()-preparation_started;need(result['preparationElapsedSeconds']<=1350,'original combined preparation ceiling exceeded')
        post_started=time.monotonic();arm_deadline(min(overall,post_started+240));result['stage']='canonical-source-plan'
        plan=publish.make_plan(publish.load(publish.paths(task)['prepared']),task/'capture/lanes',runtime,admission)
        save(record/'source-only-plan.json',plan)
        try:rows=publish.admit_plan(plan,task,runtime,False,retain=record/'canonical-readmission-process.json')
        finally:
            quiescence=supervisor.quiesce();save(record/'canonical-readmission-quiescence.json',quiescence);verify_quiescence(quiescence)
        need(rows==plan['lanes'] and len(rows)==1,'actual source-only canonical plan differs');result['actualProcesses'].append('records/canonical-readmission-process.json')
        result['stage']='original-native-refusal';refusal=command_for_phase('refusal',task,roots,runtime)
        process=supervisor.run(refusal['argv'],refusal['cwd'],environment,record/'native-refusal.stdout',record/'native-refusal.stderr',120)
        save(record/'native-refusal-process.json',process);result['actualProcesses'].append('records/native-refusal-process.json');native_refusal(process);verify_quiescence(process['quiescence'])
        result['postSourceElapsedSeconds']=time.monotonic()-post_started;need(result['postSourceElapsedSeconds']<=240,'post-source checks exceeded their bound')
        arm_deadline(overall);result['stage']='final-source-currentness'
        current=validate_inputs(contract,roots,host);save(record/'sources-after.json',current);need(current==sources,'actual source population changed')
        dependency_after=dependency_inventory(task/'source-runtime');save(record/'dependency-files-after.json',dependency_after)
        need(dependency_after==dependency_before['installedFiles'],'actual installed source driver dependency changed')
        from r0035_source_payload import file_record
        binaries_after={name:{'path':runtime[name],'resolved':str(Path(runtime[name]).resolve()),
                        **file_record(Path(runtime[name]).resolve(),1<<30)} for name in ('python','node')}
        need(binaries_after==dependency_before['binaries'],'actual source interpreter changed')
        need(not (task/'source-runtime/unused-browsers').exists(),'unexpected managed browser population')
        save(record/'dependency-currentness.json',{'protocol':'source-only-runtime-currentness/1','beforeSha256':sha(canonical(dependency_before['installedFiles'])),
            'afterSha256':sha(canonical(dependency_after)),'files':len(dependency_after),'binaries':binaries_after,'managedBrowserPopulation':[]})
        result.update(status='PREPARED_SOURCE_ONLY',stage='complete',sourceUnchanged=True,originalNativeRefusal=NATIVE_REFUSAL,
            referencePopulation=admission['referencePopulation'],derivedPopulation=admission['derivedPopulation'],actualLaneCount=1,
            originalDriverExecuted=False,originalCountersOrWaitsChanged=False)
    except BaseException as error:
        result['failures'].append({'stage':result['stage'],'type':type(error).__name__,'message':str(error)});traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if not (record/'sources-before.json').exists():save(record/'sources-before.json',sources)
        if supervisor is not None:
            try:
                quiescence=supervisor.quiesce();save(record/'final-quiescence.json',quiescence);verify_quiescence(quiescence)
            except BaseException as error:result['status']='INCOMPLETE';result['failures'].append({'stage':'final-quiescence','type':type(error).__name__,'message':str(error)})
        else:save(record/'final-quiescence.json',{'protocol':'source-only-descendant-quiescence/1','quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[],'scope':'no source producer was started'})
        result['elapsedSeconds']=time.monotonic()-started
        if result['elapsedSeconds']>2640:result['status']='INCOMPLETE';result['failures'].append({'stage':'coordinator-ceiling','type':'Deadline','message':'actual coordinator exceeded original outer ceiling'})
        save(record/'result.json',result)
    return 0 if result['status']=='PREPARED_SOURCE_ONLY' else 1


def seal(task,workspace):
    os.umask(0o077);sys.dont_write_bytecode=True;task=literal(task);roots=roots_for(workspace);record=task/'records'
    contract=validate_contract(load(CONTRACT));environment=clean_environment();os.environ.clear();os.environ.update(environment)
    need(task==literal(os.environ['RUNNER_TEMP'])/('salah-source-preparation-'+os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']),'source-only sealing task differs')
    own=source_identity(roots['harness'],contract['harnessFiles']);need(roots['harness']==ROOT and own['commit']==os.environ['GITHUB_SHA'],'actual sealing source differs')
    node=str(Path(shutil.which('node')).resolve());version=subprocess.check_output([node,'--version'],env=environment,text=True,timeout=10).strip()
    release={k:v.strip('"') for k,v in (line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)}
    host=validate_host(environment,release,version,sys.version_info[:2])
    binding={**host,'workflowTree':own['tree'],'targetCommit':contract['target']['commit'],'targetTree':contract['target']['tree'],
             'campaignSha256':contract['target']['campaignSha256'],'contractSha256':sha(CONTRACT.read_bytes())}
    if (record/'binding.json').exists():need(load(record/'binding.json')==binding,'source result and current sealing workflow differ')
    else:save(record/'binding.json',binding)
    result=load(record/'result.json');need(result.get('protocol')==PROTOCOL and result.get('scope')=='SOURCE_ONLY'
        and result.get('nativeIsolationClaim') is False and result.get('nativeExecution')=='NOT_RUN','source-only terminal record missing')
    need(result['status'] in ('PREPARED_SOURCE_ONLY','INCOMPLETE'),'source-only terminal status differs')
    verify_quiescence(load(record/'final-quiescence.json'))
    from r0035_source_supervisor import process_table,Supervisor
    if (record/'coordinator-identity.json').exists():
        producer=load(record/'coordinator-identity.json');actual=process_table().get(producer['pid'])
        need(actual is None or actual['startTicks']!=producer['startTicks'],'source coordinator still alive during sealing')
    supervisor=Supervisor();need(not supervisor.descendants(),'unexpected sealing descendant')
    before=load(record/'sources-before.json');errors=[];current=None
    try:
        current=validate_inputs(contract,roots,host)
        need(current==before,'source changed between preparation and sealing')
    except Exception as error:errors.append({'type':type(error).__name__,'message':str(error)})
    save(record/'seal-admission.json',{'protocol':'source-only-sealing-admission/1','binding':binding,
         'harness':own,'originalStatus':result['status'],'sourceCurrent':not errors,'errors':errors,
         'sourceOnlyAuthority':True,'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN'})
    collections=[{'prefix':'records','root':record,'names':None}]
    for name in ('capture','work/prepared','work/r0035-publish'):
        if (task/name).exists():collections.append({'prefix':'task/'+name,'root':task/name,'names':None})
    if (task/'runtime.json').exists():collections.append({'prefix':'task','root':task,'names':['runtime.json']})
    for role in ROLES:
        value=before[role]
        if value.get('clean') is True:
            collections.append({'prefix':'sources/'+role,'root':roots[role],'names':sorted(value['files'])})
    from r0035_source_payload import seal_collections,inventory_collections,canonical as payload_bytes
    logical,objects,_=inventory_collections(collections);unique=sum(row['bytes'] for row in objects)
    free=shutil.disk_usage(task).free;required=2*unique+4*(96<<20)+4*(18<<20)+(256<<20)
    save(record/'seal-space-preflight.json',{'protocol':'source-only-sealing-space/1','freeBytes':free,'requiredBytes':required,
        'existingLogicalBytes':sum(r['bytes'] for r in logical),'existingUniqueBytes':unique,
        'formula':'2*unique + 4*96MiB shard workspace + 4*18MiB index workspace + 256MiB margin'})
    need(free>=required,'insufficient actual space for source-only envelope set')
    packing=task/'packing';packing.mkdir(mode=0o700)
    logical_roots={**{k:str(v) for k,v in roots.items()},'task':str(task),'records':str(record)}
    identities={k:sha(payload_bytes(before[k])) for k in ROLES}
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(Deadline('source-only sealing ceiling reached')));signal.setitimer(signal.ITIMER_REAL,1200)
    try:
        index=seal_collections(collections,binding,identities,logical_roots,task/'sealed',packing,HERE/'recipient.crt')
        verify_quiescence(supervisor.quiesce())
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    # This non-content stdout is outside the encrypted logical population.
    print('SOURCE_ONLY_ENVELOPE_SET_SEALED');return 0


def retained_process(value,expected,quiescence=True):
    need(type(value.get('returncode')) is int and value['returncode']==0 and value.get('timedOut') is False
         and value.get('error') is None and value.get('retentionError') is None,'retained actual source process failed')
    need(value.get('argv')==expected['argv'] and value.get('cwd')==expected['cwd'] and type(value.get('timeoutSeconds')) is int
         and value['timeoutSeconds']==expected['timeoutSeconds'],'retained original argv/cwd/deadline differs')
    elapsed=value.get('elapsedSeconds');need(type(elapsed) in (int,float) and 0<=elapsed<=expected['timeoutSeconds'],'retained elapsed outside original ceiling')
    if quiescence:verify_quiescence(value.get('quiescence',{}))


def original_child_commands(task,roots,runtime):
    out=task/'work/prepared';main=out/'trees/main';rain=out/'trees/r0040';lab=out/'trees/r0035';baseline=roots['baseline']
    patterns=['/'+p+'/' for p in SOURCE_DIRS]+['/'+p for p in ('index.html','offline.html','config.js','builder.html','GENERATED.json','.gitignore')]
    commands=[('baseline-worktree',['git','-c','core.hooksPath=/dev/null','-C',str(baseline),'worktree','add','--detach','--no-checkout',str(main),'df644ef60156b67b5c487395176369bcec7a0d7b'],out),
              ('baseline-sparse',['git','-C',str(main),'sparse-checkout','set','--no-cone',*patterns],out),
              ('baseline-checkout',['git','-c','core.hooksPath=/dev/null','-C',str(main),'checkout','--detach','df644ef60156b67b5c487395176369bcec7a0d7b'],out)]
    for label,root in [('baseline',main),('r0040',rain)]:
        for suffix in ('build-1','build-2'):commands.append((label+'-'+suffix,[runtime['python'],'-B','tools/build_native.py'],root))
        commands.append((label+'-v1',[runtime['python'],'-B','tools/verify_v1.py','--negative-control'],root))
    commands.extend([('r0035-materialize-and-build-1',[runtime['python'],'-B',str(roots['research']/'tools/r0035/materialize_lab.py'),str(lab)],roots['research']),
                     ('r0035-build-2',[runtime['python'],'-B','tools/build_native.py'],lab),
                     ('r0035-v1',[runtime['python'],'-B','tools/verify_v1.py','--negative-control'],lab)])
    return [{'label':label,'argv':argv,'cwd':str(cwd),'timeoutSeconds':600} for label,argv,cwd in commands]


def verify_prepared_populations(logical,body,before,prepared):
    """Read original inventories against every retained raw member; execute none."""
    def population(prefix):return {name[len(prefix)+1:]:{k:row[k] for k in ('bytes','sha256')} for name,row in logical.items() if name.startswith(prefix+'/')}
    input_rows={role:body('task/work/prepared/receipts/'+role+'-files.json') for role in ('baseline','research')}
    for role,rows in input_rows.items():
        need(all(before[role]['files'].get(name)==row for name,row in rows.items()),'original input receipt differs from immutable actual source')
    counts={}
    for label,source in [('main','baseline'),('r0040','baseline'),('r0035','research')]:
        prefix='task/work/prepared/trees/'+label;actual=population(prefix);generated=body(prefix+'/GENERATED.json')
        need(generated['fileCount']==len(generated['files']) and generated['byteCount']==sum(r['bytes'] for r in generated['files'].values()),'original generated totals differ')
        need(all(actual.get(name)==row for name,row in generated['files'].items()),'complete generated raw file inventory differs')
        base={name:row for name,row in input_rows[source].items() if name.split('/')[0] in SOURCE_DIRS}
        expected_names=set(base)|set(generated['files'])|{'GENERATED.json'}
        if label=='main':expected_names|={'.git','.gitignore'}
        if label=='r0035':expected_names.add('r0035-lab-identity.json')
        need(set(actual)==expected_names,'complete generated/source tree membership differs: '+label)
        changed={name for name,row in base.items() if name not in generated['files'] and actual[name]!={k:row[k] for k in ('bytes','sha256')}}
        if label=='main':need(not changed,'unmodified baseline input changed')
        elif label=='r0040':
            need(changed=={'src/native/index.html'},'original rain patch changed unknown input')
            patch=body('task/work/prepared/receipts/r0040-patch.json');need(actual['src/native/index.html']['sha256']==patch['postimage'],'original rain patch body differs')
        else:
            lab=body(prefix+'/r0035-lab-identity.json');need(changed<=set(lab['sha256']),'original lab changed unknown input')
            need(all(actual[name]['sha256']==digest for name,digest in lab['sha256'].items()),'original lab patch/generated body differs')
        need(prepared['trees'][label]['fileCount']==generated['fileCount'] and prepared['trees'][label]['byteCount']==generated['byteCount'],'original prepared/generated totals differ')
        for name,digest in prepared['trees'][label]['sha256'].items():need(actual[name]['sha256']==digest,'original prepared generated pin differs')
        counts[label]=len(actual)
    runtime_rows=body('task/work/prepared/receipts/r003f-runtime-files.json')
    runtime_actual=population('task/work/prepared/trees/r003f')
    need(runtime_actual=={name:{k:row[k] for k in ('bytes','sha256')} for name,row in runtime_rows.items()},'complete original R003F runtime population differs')
    counts['r003f']=len(runtime_actual);return counts


def inspect_source_task(index_path,object_root,binding_path):
    from r0035_source_payload import load_index,inspect,read_logical,load_json,canonical as payload_bytes
    expected=load(binding_path);index=load_index(index_path,expected);custody=inspect(index,object_root)
    logical={row['path']:row for row in index['logicalFiles']}
    raw=lambda path,maximum=16<<20:read_logical(index,object_root,path,maximum)
    body=lambda path:load_json(raw(path))
    roots=index['logicalRoots'];task=Path(roots['task']);source_roots={k:Path(roots[k]) for k in ROLES}
    before=body('records/sources-before.json');result=body('records/result.json');seal_admission=body('records/seal-admission.json')
    need(body('records/binding.json')==expected and seal_admission['binding']==expected,'retained workflow/run/target binding differs')
    need(set(before)==set(ROLES) and all(sha(payload_bytes(before[k]))==index['sourceIdentities'][k] for k in ROLES),'retained full source identity binding differs')
    need(result.get('protocol')==PROTOCOL and result.get('scope')=='SOURCE_ONLY' and result.get('nativeIsolationClaim') is False
         and result.get('nativeExecution')=='NOT_RUN' and result.get('status') in ('PREPARED_SOURCE_ONLY','INCOMPLETE'),'retained source authority differs')
    verify_quiescence(body('records/final-quiescence.json'))
    def recorded(path):
        matches=[]
        for role,prefix in [('records','records'),('task','task'),*[(r,'sources/'+r) for r in ROLES]]:
            root=PurePosixPath(roots[role]);value=PurePosixPath(path)
            if value.is_relative_to(root):
                candidate=prefix+'/'+str(value.relative_to(root))
                if candidate in logical:matches.append(candidate)
        need(len(set(matches))==1,'retained path has no unique logical lookup');return matches[0]
    def record_check(value):
        row=logical[recorded(value['path'])];need(row['sha256']==value['sha256'] and ('bytes' not in value or row['bytes']==value['bytes']),'retained receipt points to different raw bytes')
    for role in ROLES:
        value=before[role]
        if value.get('clean') is not True:continue
        expected_names={'sources/'+role+'/'+name for name in value['files']}
        need({name for name in logical if name.startswith('sources/'+role+'/')}==expected_names,'retained complete declared source population differs')
        for name,row in value['files'].items():
            actual=logical['sources/'+role+'/'+name];need(actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'],'retained source bytes differ from Git admission')
            digest=hashlib.sha1(b'blob '+str(row['bytes']).encode()+b'\0')
            with (Path(object_root)/row['sha256']).open('rb') as stream:
                for chunk in iter(lambda:stream.read(1<<20),b''):digest.update(chunk)
            need(digest.hexdigest()==row['gitBlob'],'retained source Git blob differs')
    report={'protocol':'r0035-hosted-source-preparation-retained-review/1','status':'INCOMPLETE','binding':expected,
            'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','custody':custody,'originalStatus':result['status'],
            'failures':result['failures'],'sourceCurrentAtSealing':seal_admission['sourceCurrent']}
    if result['status']=='INCOMPLETE' or seal_admission['sourceCurrent'] is not True:
        print(json.dumps(report,sort_keys=True));return 1
    need(result['failures']==[] and result.get('sourceUnchanged') is True and result.get('originalDriverExecuted') is False
         and result.get('originalCountersOrWaitsChanged') is False,'successful source terminal conditions differ')
    need(before==body('records/sources-after.json'),'retained source before/after populations differ')
    contract=validate_contract(body('sources/harness/tools/qa/hosted-native/r0035-source-preparation.json'))
    need(sha(raw('sources/harness/tools/qa/hosted-native/r0035-source-preparation.json'))==expected['contractSha256'],'retained exact contract differs')
    need(before['harness']['commit']==expected['workflowCommit'] and before['harness']['tree']==expected['workflowTree']
         and before['target']['commit']==expected['targetCommit'] and before['target']['tree']==expected['targetTree'],'retained full Git identities differ')
    for role in ('research','baseline','historical'):
        need(all(before[role][key]==contract['sources'][role][key] for key in ('commit','tree')),'retained original Git identity differs')
    target_manifest=body('sources/target/tools/qa/hosted-native/r0035-publish-pins.json')
    need(sorted(before['target']['files'])==target_manifest['sourceFiles'] and len(target_manifest['sourceFiles'])==107,'retained target closure differs')
    runtime=body('task/runtime.json');dependency=body('records/dependency-identity.json');need(dependency['runtime']==runtime and dependency['managedBrowserPopulation']==[],'retained source runtime differs')
    need(dependency['nodePackages']==contract['runtime']['nodePackages'] and dependency['python']['version']==[3,11],'retained driver versions differ')
    need(dependency['python']['packages']=={'playwright':'1.57.0','pyee':'13.0.0','greenlet':'3.2.4','typing_extensions':'4.15.0'},'retained locked Python SDK differs')
    dependencies_after=body('records/dependency-files-after.json');dependency_current=body('records/dependency-currentness.json')
    need(dependency['installedFiles']==dependencies_after and dependency_current=={'protocol':'source-only-runtime-currentness/1',
        'beforeSha256':sha(canonical(dependency['installedFiles'])),'afterSha256':sha(canonical(dependencies_after)),
        'files':len(dependencies_after),'binaries':dependency['binaries'],'managedBrowserPopulation':[]},'retained actual runtime currentness differs')
    for phase,path in [('common','task/capture/preparation-process.json'),('derived','records/derived-process.json'),('readmit','records/readmission-process.json')]:
        retained_process(body(path),command_for_phase(phase,task,source_roots,runtime))
    context=body('task/capture/preparation-context.json');common=command_for_phase('common',task,source_roots,runtime)
    need(context=={'protocol':'source-only-common-preparation-execution/1',**common,'sourceSha256':logical['sources/target/tools/qa/hosted-native/prepare.py']['sha256'],
                   'nativeIsolationClaim':False},'original source-only common context differs')
    need(raw('task/capture/preparation.stdout').strip()==b'PREPARATION READY'
         and raw('task/capture/r0035-publish-preparation.stdout').strip()==b'PUBLISH SOURCE PREPARED; native NOT_RUN','original preparation terminal output differs')
    admission_process=body('records/readmission-process.json');admission=json.loads(admission_process['stdout'])
    canonical_process=body('records/canonical-readmission-process.json');retained_process(canonical_process,command_for_phase('readmit',task,source_roots,runtime),False)
    verify_quiescence(body('records/canonical-readmission-quiescence.json'))
    need(json.loads(canonical_process['stdout'])==admission and admission['status']=='PASS' and admission['nativePreparation'] is False,'complete actual source readmissions differ')
    need(admission['protocol']=='r0035-publish-current-admission/1' and admission['nativeQualification']=='NOT_RUN'
         and admission['speed']=='NOT_ESTABLISHED' and admission['task']==str(task) and admission['runtime']==runtime,'original source admission authority differs')
    refusal=body('records/native-refusal-process.json');native_refusal(refusal);verify_quiescence(refusal['quiescence'])
    refusal_command=command_for_phase('refusal',task,source_roots,runtime)
    need(all(refusal[k]==v for k,v in refusal_command.items()) and 0<=refusal['elapsedSeconds']<=120,'actual original native-refusal command differs')
    need(result['originalNativeRefusal']==NATIVE_REFUSAL and 0<=result['preparationElapsedSeconds']<=1350
         and 0<=result['postSourceElapsedSeconds']<=240 and 0<=result['elapsedSeconds']<=2640,'original source-only ceilings/refusal differ')
    identity=body('task/capture/r0035-publish-preparation/identity.json');prepared=body('task/work/prepared/receipts/prepared.json')
    need(prepared['status']=='PREPARED' and identity['status']=='PREPARED' and identity['nativeStatus']=='NOT_RUN','original preparation was incomplete')
    def population(prefix):return {name[len(prefix)+1:]:{k:row[k] for k in ('bytes','sha256')} for name,row in logical.items() if name.startswith(prefix+'/')}
    reference=population('task/work/prepared/trees/r0035');derived=population('task/work/r0035-publish')
    need(reference==identity['referenceFiles'] and derived==identity['derivedFiles'] and set(reference)==set(derived)
         and [name for name in reference if reference[name]!=derived[name]]==['tools/r0035/live_lab.mjs'],'complete original/derived populations differ')
    need(reference['tools/r0035/live_lab.mjs']=={'bytes':10601,'sha256':'11717de894a630f99b5d661ff35c4200b355f4486c533e0e31dbc39e67a6a02a'}
         and derived['tools/r0035/live_lab.mjs']=={'bytes':11281,'sha256':'a6ab675b9436d080836c82c1aa6d1d4bbcd28d4e4fac03b84712fed61e8a6672'},'exact independently reviewed original/derived source bodies differ')
    entry=body('task/capture/r0035-publish-preparation-entry.json')
    for sources in (identity['sources'],admission['sources'],entry['sources']):
        need(all(sources[key]==before['target'][key] for key in ('root','commit','tree','clean','files')),'retained original complete target source closure differs')
    need(identity['runtime']==runtime and identity['common']==admission['common'] and identity['originalSources']==admission['originalSources'],'retained original source/runtime custody differs')
    need({k:v for k,v in entry.items() if k not in ('protocol','sources')}==body('records/derived-process.json'),'original preparation entry and actual process differ')
    for process_path,stdout_path,stderr_path in [
        ('task/capture/preparation-process.json','task/capture/preparation.stdout','task/capture/preparation.stderr'),
        ('records/derived-process.json','task/capture/r0035-publish-preparation.stdout','task/capture/r0035-publish-preparation.stderr'),
        ('records/readmission-process.json','records/readmission.stdout','records/readmission.stderr'),
        ('records/native-refusal-process.json','records/native-refusal.stdout','records/native-refusal.stderr')]:
        process=body(process_path);need(process['stdout']==raw(stdout_path).decode('utf-8',errors='replace')
             and process['stderr']==raw(stderr_path).decode('utf-8',errors='replace'),'actual process and raw terminal stream differ')
    for rows,key in ((reference,'referencePopulation'),(derived,'derivedPopulation')):
        digest=sha(json.dumps(rows,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
        need(admission[key]=={'files':len(rows),'sha256':digest} and result[key]==admission[key],'retained source population identity differs')
    for key in ('runtimeReceipt','transformProcess','referencePlanRecord','originalLabIdentity'):record_check(identity[key])
    for key in ('runtimeReceipt','identity','transformProcess','referencePlan','derivedPlan'):record_check(admission[key])
    for key in ('prepared','process','context'):record_check(admission['common'][key])
    for value in admission['common']['streams'].values():record_check(value)
    record_check(admission['entry']['entry'])
    for value in admission['entry']['streams'].values():record_check(value)
    transform=body('task/capture/r0035-publish-preparation/transform-process.json')
    retained_process(transform,{'argv':[runtime['node'],str(source_roots['target']/'tools/qa/hosted-native/r0035_publish_io.mjs'),'derive',
                                      identity['baseRoot'],identity['root']], 'cwd':str(source_roots['target']/'tools/qa/hosted-native'),'timeoutSeconds':30},False)
    need(json.loads(transform['stdout'])==identity['transform'],'retained actual transformation result differs')
    prepared_counts=verify_prepared_populations(logical,body,before,prepared)
    expected_children=original_child_commands(task,source_roots,runtime)
    labels=[child['label'] for child in expected_children]
    paths=sorted(name for name in logical if re.fullmatch(r'task/work/prepared/receipts/[0-9]{2}-.+\.json',name))
    need(paths==['task/work/prepared/receipts/'+f'{i+1:02d}-'+label+'.json' for i,label in enumerate(labels)],'original complete child receipt population differs')
    for path,expected_child in zip(paths,expected_children):
        process=body(path);need(process['status']=='PASS' and type(process['returncode']) is int and process['returncode']==0
             and type(process['timeoutSeconds']) is int and process['timeoutSeconds']==expected_child['timeoutSeconds']
             and 0<=process['elapsedSeconds']<=process['timeoutSeconds'],'actual original nested child failed')
        need(process['argv']==expected_child['argv'] and process['cwd']==expected_child['cwd'],'original complete child command differs')
        for stream in ('stdout','stderr'):need(recorded(process[stream])==path[:-5]+'.'+stream,'original child raw stream custody differs')
        if 'build-' in expected_child['label'] and 'materialize' not in expected_child['label']:
            terminal=body(recorded(process['stdout']));need(terminal.get('stage')=='complete-native-and-moon','original builder terminal missing')
            if expected_child['label'].endswith('-2'):need(terminal.get('written')==0 and terminal.get('removed')==0 and terminal.get('unchanged')==117,'original second-build unchanged population differs')
    plan=body('records/source-only-plan.json');need(plan['lanes'][0]['preparation']==admission and len(plan['lanes'])==1
         and plan['r0035Publish'] is True and plan['r0035Psf'] is False,'retained canonical source-only plan differs')
    original_args=[runtime['python'],str(source_roots['research']/'tools/r0035/native_trials.py'),
        str(task/'capture/r0035-publish-preparation/derived-plan.json'),str(task/'capture/lanes/r0035-chromium-publish'),
        '--engine','chromium','--rounds','1','--seconds','15','--clock','ordinary','--scene','dark','--motion','normal']
    need(plan['lanes'][0]['evidenceRetention']['originalArgv']==original_args,'original recorded native arguments differ')
    report.update(status='VERIFIED_HOSTED_SOURCE_PREPARATION_NATIVE_REFUSED',referencePopulation=admission['referencePopulation'],derivedPopulation=admission['derivedPopulation'],
                  originalNestedChildren=len(paths),preparedTreeFiles=prepared_counts,originalDriverExecuted=False,relocatedPathsUsedOnlyForReadback=True)
    print(json.dumps(report,sort_keys=True));return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('run','seal','inspect'))
    parser.add_argument('--task',type=Path);parser.add_argument('--workspace',type=Path);parser.add_argument('--index',type=Path);parser.add_argument('--objects',type=Path);parser.add_argument('--binding',type=Path)
    args=parser.parse_args()
    if args.operation=='run':return run(args.task,args.workspace)
    if args.operation=='seal':return seal(args.task,args.workspace)
    return inspect_source_task(args.index,args.objects,args.binding)


if __name__=='__main__':raise SystemExit(main())
