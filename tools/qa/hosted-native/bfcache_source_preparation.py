"""Fixed BF hosted SOURCE-ONLY preparation; no acquisition or observation.

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
CONTRACT=HERE/'bfcache-source-preparation.json'
CONTRACT_CANONICAL_SHA256='8cc1e9c16de96eb5a77b25128d70a3bb2151696bd7091748120ff0bccc30ffc8'
PROTOCOL='bfcache-hosted-source-preparation-result/1'
REPOSITORY='theislampill/salah_widget'
BRANCH='chatgpt/bfcache-source-preparation-20261127'
WORKFLOW='.github/workflows/bfcache-source-preparation.yml'
ROLES=('harness','target','research','baseline','historical')
SOURCE_DIRS=('src','real-sky','tools','moon','vendor','v1','tests')
HISTORICAL=['tools/qa/precip_eval_lib.cjs','tools/qa/precip_models_geom.js','tools/qa/precip_declared_gain.json',
            'tools/qa/precip_models.js','tools/qa/precip_models_capture.cjs','tools/qa/precip_models_post.py']
NATIVE_REFUSAL='ValueError: native common preparation was not isolated by hosted execution'




def need(value,message):
    if not value:raise ValueError(message)


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def sha(value):return hashlib.sha256(value).hexdigest()


def same(left,right):return canonical(left)==canonical(right)


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
    env.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_NOSYSTEM='1',
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
    elif phase=='r002f':
        argv=[runtime['python'],str(here/'r002f_prepare.py'),'--research',str(roots['research']),
              '--baseline',str(roots['baseline']),'--out',str(task/'work/r002f-prepared'),'--node',runtime['node']];seconds=900
    elif phase in ('check-source','refuse-native-common'):
        argv=[runtime['python'],'-B',str(roots['harness']/'tools/qa/hosted-native/bfcache_source_preparation.py'),phase,
              '--task',str(task),'--workspace',str(roots['harness'].parent)];seconds=120
    elif phase=='central-no-runtime':
        argv=[runtime['python'],'-B',str(here/'r002f_bfcache_central.py'),'admit','--task',str(task),'--native'];seconds=120
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
        names=source_paths(role)
        value=source_identity(roots[role],names);expected=contract['sources'][role]
        need(value['commit']==expected['commit'] and value['tree']==expected['tree'],'immutable original source differs: '+role);result[role]=value
    here=roots['target']/'tools/qa/hosted-native'
    for name,key in (('node/package.json','packageJsonSha256'),('node/package-lock.json','packageLockSha256'),('requirements.txt','requirementsSha256')):
        need(sha((here/name).read_bytes())==contract['runtime'][key],'actual locked driver input differs')
    return result


class Deadline(Exception):pass


def arm_deadline(deadline):
    remaining=deadline-time.monotonic();need(remaining>0,'source-only phase ceiling exhausted');signal.setitimer(signal.ITIMER_REAL,remaining)


def dependency_inventory(root):
    from bfcache_source_payload import file_record
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


PYTHON_METADATA_CODE="import importlib.metadata,json,sys,sysconfig; print(json.dumps({'python':sys.version,'version':list(sys.version_info[:2]),'site':sysconfig.get_paths()['purelib'],'packages':{n:importlib.metadata.version(n) for n in ('playwright','pyee','greenlet','typing_extensions')}}))"


def source_runtime_commands(task,roots,node,host_python):
    directory=Path(task)/'source-runtime';here=roots['target']/'tools/qa/hosted-native'
    return [('python-environment',[host_python,'-B','-m','venv',str(directory/'python')],60),
            ('node-packages',[str(Path(node).with_name('npm')),'ci','--prefix',str(directory/'node'),'--ignore-scripts','--no-audit','--no-fund','--omit=optional','--registry=https://registry.npmjs.org'],300),
            ('python-packages',[str(directory/'python/bin/python'),'-B','-m','pip','install','--require-hashes','--only-binary=:all:',
                '--no-cache-dir','--index-url','https://pypi.org/simple','-r',str(here/'requirements.txt')],300),
            ('package-identity',[str(directory/'python/bin/python'),'-B','-c',PYTHON_METADATA_CODE],30)]


def install_source_runtime(task,roots,node,supervisor,environment,record):
    # Materialize exact locked SDK dependencies. No managed browser installer is
    # called; package scripts are disabled and a fresh empty browser path is set.
    directory=task/'source-runtime';directory.mkdir(mode=0o700);(directory/'node').mkdir(mode=0o700)
    here=roots['target']/'tools/qa/hosted-native'
    for name in ('package.json','package-lock.json'):shutil.copyfile(here/'node'/name,directory/'node'/name)
    environment.update(PLAYWRIGHT_BROWSERS_PATH=str(directory/'unused-browsers'))
    commands=source_runtime_commands(task,roots,node,sys.executable)
    from r0035_source_supervisor import successful
    for label,argv,seconds in commands[:3]:
        process=supervisor.run(argv,str(task),environment,record/(label+'.stdout'),record/(label+'.stderr'),seconds)
        save(record/(label+'-process.json'),process);successful(process)
    runtime={'python':str(directory/'python/bin/python'),'node':node,'modules':str(directory/'node/node_modules')}
    runtime.update(playwright=str(Path(runtime['modules'])/'playwright'),pngjs=str(Path(runtime['modules'])/'pngjs'))
    node_versions={name:load(Path(runtime['modules'])/name/'package.json')['version'] for name in ('playwright','playwright-core','pngjs')}
    need(node_versions=={'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'},'actual source SDK versions differ')
    process=supervisor.run(commands[3][1],str(task),environment,record/'package-identity.stdout',record/'package-identity.stderr',30)
    save(record/'package-identity-process.json',process);successful(process);python=json.loads(process['stdout'])
    need(python['version']==[3,11] and python['packages']=={'playwright':'1.57.0','pyee':'13.0.0','greenlet':'3.2.4','typing_extensions':'4.15.0'},'actual Python source SDK versions differ')
    need(not (directory/'unused-browsers').exists(),'source-only route installed a managed browser')
    from bfcache_source_payload import file_record
    identity={'protocol':'source-only-installed-driver-dependencies/1','nativeIsolationClaim':False,'nativeExecution':'NOT_RUN',
        'runtime':runtime,'nodePackages':node_versions,'python':python,'binaries':{name:{'path':runtime[name],
            'resolved':str(Path(runtime[name]).resolve()),**file_record(Path(runtime[name]).resolve(),1<<30)} for name in ('python','node')},
        'installedFiles':dependency_inventory(directory),'managedBrowserPopulation':[]}
    source_sdk_schema(runtime,task);source_only_absence(task)
    save(record/'dependency-identity.json',identity);save(record/'source-runtime.json',runtime);return runtime,identity


def verify_quiescence(value):
    need(type(value) is dict and value.get('quiescent') is True and value.get('unexpectedDescendants') is False
         and value.get('before')==[] and value.get('remaining')==[],'source process left detached descendants')


def retained_process(value,expected,quiescence=True):
    need(type(value.get('returncode')) is int and value['returncode']==0 and value.get('timedOut') is False
         and value.get('error') is None and value.get('retentionError') is None,'retained actual source process failed')
    need(same(value.get('argv'),expected['argv']) and value.get('cwd')==expected['cwd'] and type(value.get('timeoutSeconds')) is int
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


COMMON_PINS={
    'main':{'index.html':'88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1',
            'offline.html':'4a992602ac0c80ef3d2df59e1a0f346c8342502b5503d05783f94d5c2b13f2c6',
            'GENERATED.json':'cbce31ba3a018b99e4259c192902442db421b2d8b8b65e48e143acf19bcaf4f2'},
    'r0040':{'index.html':'4b31c1177826c20e184ad3636642cef046d147fbd16f4ef946bb33e36b7318df',
             'offline.html':'e4e7fa4ad49a07cffd39b554491aea11fa69e4fccf68d079d7d1d987d1d3108f',
             'GENERATED.json':'1e1c8b3a4712bec13257e2805df71d9d0a24dabeaa10b9ac1596cd998460ccd5'},
    'r0035':{'index.html':'74a2d263cc92600a1582f84d4c78f45f7cdecf0c14998ed6edfbd00f6c543851',
             'GENERATED.json':'8bbd701871b710f31af7f2dae8287daca4a40075d582f4e14583459715df4d86'}}
RAIN_IDENTITY={'preimage':'7f9eb1514f8d96097273d1ce9be6607b82ccb0c6df41a5094508dab787401249',
               'patch':'69e5bd1d19e084cb6c5e1dd6f4157a53dff17834d5ba8ada8c190dba383e4b2a',
               'postimage':'f83c4a729d0f0798bd234fb7b531c0a5bf2b767194b50de7a0b6bc71a6e07084'}


def size_digest(row):return {key:row[key] for key in ('bytes','sha256')}


def logical_population(logical,prefix):
    return {name[len(prefix)+1:]:size_digest(row) for name,row in logical.items() if name.startswith(prefix+'/')}


def selected_source(files,paths):
    return {name:row for name,row in files.items() if any(name==p or name.startswith(p+'/') for p in paths)}


def generated_inventory(logical,body,prefix,pins):
    actual=logical_population(logical,prefix);generated=body(prefix+'/GENERATED.json')
    need(type(generated) is dict and set(generated)=={'schema','generator','fileCount','byteCount','files'}
         and generated['schema']=='salah-generated-inventory/1' and generated['generator']=='tools/build_native.py'
         and type(generated['files']) is dict and type(generated['fileCount']) is int and generated['fileCount']==116
         and len(generated['files'])==116 and type(generated['byteCount']) is int,
         'original complete generated inventory schema or count differs')
    for name,row in generated['files'].items():
        safe_relative(name)
        need(type(row) is dict and set(row)=={'bytes','sha256'} and type(row['bytes']) is int and row['bytes']>=0
             and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256'])
             and same(actual.get(name),row),'complete generated raw file inventory differs')
    need(generated['byteCount']==sum(row['bytes'] for row in generated['files'].values()),'original generated byte total differs')
    need(all(actual.get(name,{}).get('sha256')==digest for name,digest in pins.items()),'original fixed generated pin differs')
    return actual,generated


def verify_prepared_populations(logical,body,before,prepared):
    """Check original metadata relations only; the caller separately admits every raw object."""
    need(type(prepared) is dict and set(prepared)=={'schemaVersion','protocol','status','sources','trees','cleanup'}
         and type(prepared['schemaVersion']) is int and prepared['schemaVersion']==1
         and prepared['protocol']=='salah-hosted-native-preparation/1' and prepared['status']=='PREPARED'
         and set(prepared['trees'])=={'main','r0040','r0035','r003f'},'original complete common receipt differs')
    contract=validate_contract(load(CONTRACT));sources={}
    for role in ('research','baseline'):
        need(all(before[role][key]==contract['sources'][role][key] for key in ('commit','tree')),
             'common original immutable source differs')
        sources[role]={key:before[role][key] for key in ('root','commit','tree')}
    sources['historical']={'root':before['historical']['root'],'commit':contract['sources']['historical']['commit'],
        'identityScope':'pinned helper bytes; archive need not contain Git metadata',
        'sha256':{'tools/qa/precip_eval_lib.cjs':'a02358979e9aa2f968c5ca9dde4ec7a8e63db869b871f1c24ce65a68e71497e7'}}
    need(same(prepared['sources'],sources),'original common source root/commit/tree differs')
    task=Path(prepared['trees']['main']['root']).parents[3]
    original_paths={'research':(*SOURCE_DIRS,'docs/state-contracts/evidence/R0040/phase1-options.patch.gz'),
                    'baseline':(*SOURCE_DIRS,'index.html','offline.html','config.js','builder.html','GENERATED.json')}
    inputs={role:body('task/work/prepared/receipts/'+role+'-files.json') for role in original_paths}
    for role,rows in inputs.items():
        need(same(rows,selected_source(before[role]['files'],original_paths[role])),
             'complete original input receipt differs from immutable source population')
    counts={}
    for label,source in [('main','baseline'),('r0040','baseline'),('r0035','research')]:
        prefix='task/work/prepared/trees/'+label
        actual,generated=generated_inventory(logical,body,prefix,COMMON_PINS[label])
        base=selected_source(inputs[source],SOURCE_DIRS);names=set(base)|set(generated['files'])|{'GENERATED.json'}
        if label=='main':names|={'.git','.gitignore'}
        if label=='r0035':names.add('r0035-lab-identity.json')
        need(set(actual)==names,'complete generated/source tree membership differs: '+label)
        changed={name for name,row in base.items() if name not in generated['files'] and not same(actual[name],size_digest(row))}
        if label=='main':
            need(not changed and same(actual['.gitignore'],size_digest(before['baseline']['files']['.gitignore'])),
                 'original baseline source changed')
        elif label=='r0040':
            need(changed=={'src/native/index.html'} and same(body('task/work/prepared/receipts/r0040-patch.json'),RAIN_IDENTITY)
                 and inputs['baseline']['src/native/index.html']['sha256']==RAIN_IDENTITY['preimage']
                 and inputs['research']['docs/state-contracts/evidence/R0040/phase1-options.patch.gz']['sha256']==RAIN_IDENTITY['patch']
                 and actual['src/native/index.html']['sha256']==RAIN_IDENTITY['postimage'],'original rain patch differs')
        else:
            need(changed=={'src/native/index.html','real-sky/native-host.mjs','real-sky/native-preview-host.mjs','real-sky/native-star-preview.mjs'},
                 'original lab changed a different source population')
            lab=body(prefix+'/r0035-lab-identity.json')
            tracked={'index.html','offline.html','GENERATED.json','src/native/index.html','real-sky/native-host.mjs',
                     'real-sky/native-preview-host.mjs','real-sky/native-star-preview.mjs','real-sky/native-sky.js','real-sky/native-worker.js'}
            tracked|={n for n in before['research']['files'] if n.startswith('tools/r0035/') and n.count('/')==2 and n.endswith('.mjs')}
            expected={'sourceHead':before['research']['commit'],
                'purpose':'Independent reconstruction. HTTP lab only. Candidate config requires five explicit options.',
                'sha256':{n:actual[n]['sha256'] for n in tracked}}
            need(same(lab,expected) and same(lab,body('task/work/prepared/receipts/r0035-lab-identity.json')),
                 'complete original lab identity differs')
        expected={'root':str(task/'work/prepared/trees'/label),'fileCount':generated['fileCount'],
                  'byteCount':generated['byteCount'],'sha256':COMMON_PINS[label]}
        need(same(prepared['trees'][label],expected),'original complete prepared/generated identity differs')
        counts[label]=len(actual)
    runtime_path='task/work/prepared/receipts/r003f-runtime-files.json'
    runtime=body(runtime_path);expected=selected_source(before['baseline']['files'],('index.html','config.js','moon','real-sky','tests/r0002-ordinary.json'))
    need(same(runtime,expected),'original complete runtime receipt differs from baseline source')
    actual=logical_population(logical,'task/work/prepared/trees/r003f')
    need(same(actual,{n:size_digest(row) for n,row in expected.items()}),'complete original R003F raw runtime population differs')
    expected={'root':str(task/'work/prepared/trees/r003f'),'sha256':{'index.html':COMMON_PINS['main']['index.html']},
        'materialization':'git-blob-verified-runtime-subset','sourceCommit':before['baseline']['commit'],'sourceTree':before['baseline']['tree'],
        'manifest':str(task/'work/prepared/receipts/r003f-runtime-files.json'),'manifestSha256':logical[runtime_path]['sha256']}
    need(same(prepared['trees']['r003f'],expected),'original runtime preparation identity differs')
    counts['r003f']=len(actual);return counts


R002F_TOOL_PINS={
    'tools/build_native.py':'a48e43cfb6d3d4af0553e89cf808096825bc039d4fb9375e5cca1a9435e63832',
    'tools/build_moon.py':'1561c5d2fbfd6cad5d0196106631404bdfa997c5458d411a8ddfcacb9e13b9f0',
    'tools/generated_outputs.py':'2c3a1f1ece39ab6eca74e247681ce9accc3bdcf949dc6ff2dd07fdf8ddcc850d',
    'tools/verify_v1.py':'48eff560af5cfcbef37e275f7f9cc7d13b101e87c56d68b84ec9d84da8594950',
    'tools/qa/r002f-transaction/materialize.cjs':'b1d80a1a83933097f78fa6f30738794dd5d1677a0e4d9f02b54d87e384f2fa74',
    'tools/qa/r002f-transaction/preview-stage.js':'ab19d1ec14bf162b38519d5bddd58ca3fa88778607ce5942a5ae062d5a39f000',
    'tools/qa/r002f-transaction/detail-stage.js':'be7c571d2afa6c26ff75ad7c48f51aa4e38614a16bab1fa4dc9443268877e20f',
    'tools/qa/r002f_a2_architecture.cjs':'386cd4c7573fb91e4070d4306560a33bba8a7dfc2d4a0e6be22943ef4f81caeb',
    'tools/qa/r002f_a2_quarantine.cjs':'7efce81d525ceed636d4dcb8fd9b83c872f8dd6ed6b5633f505fb15c6898250c'}
R002F_PATCH='a310e13f6c92439cdc30224a5ec6b6a2170804e2a58a9640965ccb7bad7879d7'
R002F_PATCH_FILES=('real-sky/native-preview-host.mjs','real-sky/native-composition.mjs','moon/src/moon-native.mjs',
                   'real-sky/native-host-hooks.js','src/native/index.html')
R002F_COMBINED_PINS={'index.html':'55a8bdbc7b7ab5cb53ede3b58c0ef1e4101c7c89bc6936860bd4bc5f3acb8fe2',
                     'GENERATED.json':'69f819a9cce8b4fb82fc8977d64c71bdf0f071eec40972d0cf99df830250c481'}
R002F_SOURCE_MANIFEST='b9d4556ba1e23bf56e9156f293dd8e3e76c7a678bd38b38e84235019a29c1fad'


def verify_r002f_populations(logical,body,before,build,generated_admission,task):
    """Bind the original R002F aggregates and complete logical populations, without executing them."""
    prefix='task/work/r002f-prepared';task=Path(task)
    need(type(build) is dict and set(build)=={'protocol','status','baseProvenance','researchProvenance','identityScope',
         'wrapperSha256','python','inputs','researchTools','arms','patch'} and build['protocol']=='r002f-hosted-build/1'
         and build['status']=='PASS' and build['baseProvenance']==before['baseline']['commit']
         and build['researchProvenance']==before['research']['commit']
         and build['identityScope']=='content-verified build inputs; commit custody belongs to acquisition'
         and build['wrapperSha256']==before['target']['files']['tools/qa/hosted-native/r002f_prepare.py']['sha256'],
         'original R002F build status/source/authority differs')
    selected=selected_source(before['baseline']['files'],('index.html','offline.html','config.js','builder.html','GENERATED.json','_config.yml',
        'src/native','real-sky','moon','vendor/real-sky','v1','docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json','tests/r0002-ordinary.json'))
    selected.update({n:r for n,r in before['baseline']['files'].items() if n.startswith('tools/') and n.count('/')==1 and n.endswith('.py')})
    rows=[{'path':n,**size_digest(selected[n])} for n in sorted(selected)]
    need(len(rows)==387 and same(build['inputs'],rows),'original complete ordered R002F input population differs')
    need(all(same(size_digest(before['research']['files'][n]),size_digest(r)) for n,r in selected.items()),
         'original R002F research/baseline inputs differ')
    tools=[]
    for n,digest in sorted(R002F_TOOL_PINS.items()):
        row=before['research']['files'][n]
        need(row['sha256']==digest and ('/qa/' in n or before['baseline']['files'][n]['sha256']==digest),
             'original R002F tool pin differs')
        tools.append({'path':n,**size_digest(row)})
    need(same(build['researchTools'],tools),'original complete R002F research tool population differs')
    patch=body(prefix+'/patch/manifest.json')
    need(type(patch) is dict and set(patch)=={'files','patch','unchangedDetail'}
         and patch['patch']==R002F_PATCH and patch['unchangedDetail']=='c5f336a5f42e3774866d66215e2944b2cde7afad05db801868980121fa70a8b8'
         and same(patch,build['patch']) and type(patch['files']) is list
         and [r['file'] for r in patch['files']]==list(R002F_PATCH_FILES),'original complete R002F patch manifest differs')
    patch_actual=logical_population(logical,prefix+'/patch')
    need(set(patch_actual)==set(R002F_PATCH_FILES)|{'transaction.patch','manifest.json'}
         and patch_actual['transaction.patch']['sha256']==R002F_PATCH
         and patch_actual['manifest.json']=={'bytes':1340,'sha256':'26bc7eafa4115b583100844593e9f5443e0b9d725bd6104f68e3efdf7b656fe8'},
         'original complete R002F patch raw population differs')
    post={}
    for row in patch['files']:
        n=row['file']
        need(set(row)=={'file','original','candidate'} and row['original']==selected[n]['sha256']
             and row['candidate']==patch_actual[n]['sha256'],'original patch preimage/postimage differs')
        post[n]=patch_actual[n]
    need(type(build['arms']) is dict and set(build['arms'])=={'baseline','candidate'},'original R002F arm population differs')
    counts={};generated_counts={};expected_generated={}
    for arm in ('baseline','candidate'):
        pins=({'index.html':COMMON_PINS['main']['index.html'],'GENERATED.json':COMMON_PINS['main']['GENERATED.json']}
              if arm=='baseline' else R002F_COMBINED_PINS)
        actual,generated=generated_inventory(logical,body,prefix+'/'+arm,pins)
        need(set(actual)==set(selected)|set(generated['files'])|{'GENERATED.json'},'complete original R002F arm membership differs')
        for n,row in selected.items():
            if n in generated['files'] or n=='GENERATED.json':continue
            expected=post[n] if arm=='candidate' and n in post else size_digest(row)
            need(same(actual[n],expected),'R002F source input changed outside the original patch: '+arm+'/'+n)
        record=build['arms'][arm]
        need(type(record) is dict and set(record)=={'path','indexSha256','inventorySha256','builds','v1'}
             and record['path']==arm and record['indexSha256']==pins['index.html']
             and record['inventorySha256']==pins['GENERATED.json']
             and record['v1']=='PASS with disposable tamper negative control and Pages inclusion preflight'
             and type(record['builds']) is list and len(record['builds'])==2,'original R002F arm build receipt differs')
        for i,terminal in enumerate(record['builds'],1):
            need(same(terminal,body(prefix+'/'+arm+'-build-'+str(i)+'.stdout'))
                 and terminal.get('phase')=='published' and terminal.get('stage')=='complete-native-and-moon'
                 and terminal.get('indexSha256')==pins['index.html'] and terminal.get('inventorySha256')==pins['GENERATED.json'],
                 'original R002F raw build terminal differs')
            if i==2:
                need(same({k:terminal.get(k) for k in ('written','removed','unchanged')},{'written':0,'removed':0,'unchanged':117}),
                     'original R002F second build population differs')
        expected_generated[arm]={'root':str(task/'work/r002f-prepared'/arm),'indexSha256':pins['index.html'],
            'generatedInventorySha256':pins['GENERATED.json'],'files':[{'path':n,**r} for n,r in generated['files'].items()],
            'assets':{n:actual[n] for n in ('moon/assets/dem.bin.gz','moon/assets/colour.bin.gz','moon/asset-manifest.json')}}
        counts[arm]=len(actual);generated_counts[arm]=generated['fileCount']
    expected_module_names={'browser-control.cjs','r002f_focus_owner.cjs','r002f_probe.cjs','r002f_tabhide.cjs',
                           'r002f_tabhide_runtime.cjs','r002f_tabhide_source.cjs'}
    manifest={'protocol':'r002f-tabhide-source/1','reconstructedFromPublicCommit':'890c7b6005228715b58b3d1d90847f39cf4698be',
        'modules':{n:size_digest(before['target']['files']['tools/qa/hosted-native/'+n]) for n in expected_module_names}}
    expected_generated.update(sourceManifest=manifest,sourceManifestSha256=R002F_SOURCE_MANIFEST)
    need(before['target']['files']['tools/qa/hosted-native/r002f-tabhide-pins.json']['sha256']==R002F_SOURCE_MANIFEST
         and same(generated_admission,expected_generated),'complete original generated/source admission differs')
    # The original wrapper has nine bounded child calls and eighteen raw streams,
    # but no per-child structured process records. Do not invent that authority.
    labels=['materialize','patch-check','patch-apply']+[arm+'-'+phase for arm in ('baseline','candidate') for phase in ('build-1','build-2','v1')]
    other={n for n in logical_population(logical,prefix) if not n.startswith(('baseline/','candidate/','patch/'))}
    need(other=={'build-result.json'}|{label+'.'+stream for label in labels for stream in ('stdout','stderr')},
         'original R002F raw stream population differs or gained fabricated child receipts')
    return {'inputs':len(rows),'researchTools':len(tools),'trees':counts,'generatedFiles':generated_counts,
            'rawChildStreamPairs':len(labels),'individualStructuredR002FChildReceipts':'NOT_PRODUCED_BY_ORIGINAL_WRAPPER'}


def source_paths(role):
    pages='docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json'
    if role=='research':return list(SOURCE_DIRS)+['docs/state-contracts/evidence/R0040/phase1-options.patch.gz',
        'index.html','offline.html','config.js','builder.html','GENERATED.json','_config.yml',pages]
    if role=='baseline':return list(SOURCE_DIRS)+['index.html','offline.html','config.js','builder.html','GENERATED.json','.gitignore','_config.yml',pages]
    if role=='historical':return list(HISTORICAL)
    raise ValueError('fixed original source role required')


PHYSICAL_FIELDS={'path','resolvedPath','bytes','sha256','device','inode','links','mode','uid',
                 'mtimeNs','ctimeNs','system','symlinks'}


def physical_file_record(value):
    """Independent descriptor custody before importing original target code."""
    path=literal(value);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and 0<=before.st_size<=1<<30 and before.st_nlink==1,
             'bounded single-link regular source required')
        digest=hashlib.sha256();count=0
        while True:
            block=os.read(fd,1<<20)
            if not block:break
            count+=len(block);need(count<=before.st_size,'physical source grew during read');digest.update(block)
        fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_size','st_mtime_ns','st_ctime_ns')
        after=os.fstat(fd);named=os.stat(path,follow_symlinks=False)
        need(count==before.st_size and all(getattr(before,k)==getattr(after,k)==getattr(named,k) for k in fields),
             'physical source changed during descriptor/path read')
        return {'path':str(path),'resolvedPath':str(path),'bytes':count,'sha256':digest.hexdigest(),
                'device':str(before.st_dev),'inode':str(before.st_ino),'links':before.st_nlink,
                'mode':stat.S_IMODE(before.st_mode),'uid':before.st_uid,'mtimeNs':str(before.st_mtime_ns),
                'ctimeNs':str(before.st_ctime_ns),'system':False,'symlinks':[]}
    finally:os.close(fd)


def target_physical_map(compact):
    return {name:physical_file_record(Path(compact['root'])/name) for name in sorted(compact['files'])}


def join_target_identity(compact,independent,original):
    """Join admitted Git facts and complete original physical records, without normalizing either."""
    need(type(compact) is dict and compact.get('protocol')=='source-only-declared-git-inputs/1'
         and compact.get('clean') is True,'independent compact source admission required')
    need(type(original) is dict and set(original)=={'protocol','root','commit','tree','clean','files'}
         and original['protocol']=='r002f-bfcache-current-source/1' and original['clean'] is True,
         'original full physical source identity required')
    for key in ('root','commit','tree','clean'):
        need(same(original[key],compact[key]),'original source root/commit/tree/clean differs')
    need(type(compact['files']) is dict and type(independent) is dict and type(original['files']) is dict
         and len(compact['files'])==111 and set(compact['files'])==set(independent)==set(original['files']),
         'complete 111-file compact/physical populations differ')
    root=PurePosixPath(compact['root'])
    need(root.is_absolute() and str(root)==compact['root'] and '..' not in root.parts,'literal source root required')
    for name,row in compact['files'].items():
        safe_relative(name);physical=independent[name]
        need(type(row) is dict and set(row)=={'bytes','sha256','gitBlob','mode'}
             and type(row['bytes']) is int and 0<=row['bytes']<=1<<30
             and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256'])
             and type(row['gitBlob']) is str and re.fullmatch('[0-9a-f]{40}',row['gitBlob'])
             and row['mode'] in ('100644','100755'),'compact Git source row differs')
        need(type(physical) is dict and set(physical)==PHYSICAL_FIELDS,'complete physical fields required')
        expected_path=str(root/name)
        need(physical['path']==expected_path and physical['resolvedPath']==expected_path
             and physical['system'] is False and physical['symlinks']==[]
             and type(physical['links']) is int and physical['links']==1
             and type(physical['mode']) is int and physical['mode']==(0o755 if row['mode']=='100755' else 0o644)
             and type(physical['uid']) is int and physical['uid']>=0
             and type(physical['bytes']) is int and physical['bytes']==row['bytes']
             and physical['sha256']==row['sha256'],'physical path/mode/body/ownership differs from Git admission')
        need(all(type(physical[k]) is str and re.fullmatch('[0-9]+',physical[k]) for k in ('device','inode','mtimeNs','ctimeNs')),
             'physical descriptor identity types differ')
        need(same(physical,original['files'][name]),'original source physical custody differs from preimport observation')
    return original


def import_target(roots,identities,independent):
    here=literal(roots['target']/'tools/qa/hosted-native')
    need(str(here) not in sys.path,'target import already initialized')
    names={Path(name).stem for name in identities['target']['files'] if name.startswith('tools/qa/hosted-native/') and name.endswith('.py')}
    need(not names.intersection(sys.modules),'foreign target module already initialized')
    sys.path.insert(0,str(here))
    import r002f_bfcache_central as central
    joined=join_target_identity(identities['target'],independent,central.source_identity())
    return central,joined


def source_sdk_schema(runtime,task):
    task=Path(task).absolute()
    need(type(runtime) is dict and set(runtime)=={'python','node','modules','playwright','pngjs'},
         'exact five-key source SDK required')
    for value in runtime.values():
        need(type(value) is str and PurePosixPath(value).is_absolute() and str(PurePosixPath(value))==value
             and '..' not in PurePosixPath(value).parts,'literal source SDK path required')
    modules=task/'source-runtime/node/node_modules'
    expected={'python':str(task/'source-runtime/python/bin/python'),'node':runtime['node'],'modules':str(modules),
              'playwright':str(modules/'playwright'),'pngjs':str(modules/'pngjs')}
    need(same(runtime,expected),'fixed source SDK paths differ')
    return runtime


def source_only_absence(task):
    task=Path(task)
    for name in ('runtime.json','source-runtime/unused-browsers','capture/isolation','capture/r002f-bfcache-tools'):
        need(not (task/name).exists() and not (task/name).is_symlink(),'source-only route acquired forbidden native/runtime population: '+name)


def central_refusal(process,task):
    expected="FileNotFoundError: [Errno 2] No such file or directory: "+repr(str(Path(task)/'runtime.json'))
    need(type(process.get('returncode')) is int and process['returncode']==1 and process.get('timedOut') is False
         and process.get('error') is None and process.get('retentionError') is None and process.get('stdout')==''
         and type(process.get('stderr')) is str and process['stderr'].strip().splitlines()[-1:]==[expected],
         'original central absent-runtime refusal was not observed')
    return True


def source_current(contract,roots,host,before,physical_before,central,path):
    current=validate_inputs(contract,roots,host)
    independent=target_physical_map(current['target'])
    physical=join_target_identity(current['target'],independent,central.source_identity())
    observed={'protocol':'bfcache-source-only-currentness/1','sources':current,'targetPhysical':physical}
    save(path,observed)
    need(same(current,before) and same(physical,physical_before),'actual full source or physical custody changed')
    return observed


def load_supervisor():
    path=literal(HERE/'r0035_source_supervisor.py');raw=path.read_bytes()
    need(sha(raw)=='5c33dc70746846349cc1b6c8b3977f48d7a146da5c0223bbbf45e131dbb4f116',
         'original source supervisor changed')
    import r0035_source_supervisor as module
    need(Path(module.__file__).absolute()==path,'source supervisor resolved outside admitted harness')
    return module


def runtime_current(task,dependency,record=None):
    from bfcache_source_payload import file_record
    runtime=source_sdk_schema(load(Path(task)/'records/source-runtime.json'),task)
    need(dependency.get('protocol')=='source-only-installed-driver-dependencies/1'
         and dependency.get('nativeIsolationClaim') is False and dependency.get('nativeExecution')=='NOT_RUN'
         and same(runtime,dependency.get('runtime')) and dependency.get('managedBrowserPopulation')==[],
         'actual source SDK descriptor differs')
    installed=dependency_inventory(Path(task)/'source-runtime')
    binaries={name:{'path':runtime[name],'resolved':str(Path(runtime[name]).resolve()),
                    **file_record(Path(runtime[name]).resolve(),1<<30)} for name in ('python','node')}
    source_only_absence(task)
    need(same(installed,dependency['installedFiles']) and same(binaries,dependency['binaries']),
         'actual source SDK files or interpreter changed')
    result={'protocol':'source-only-runtime-currentness/1','beforeSha256':sha(canonical(dependency['installedFiles'])),
            'afterSha256':sha(canonical(installed)),'files':len(installed),'binaries':binaries,'managedBrowserPopulation':[]}
    if record is not None:
        save(record/'dependency-files-after.json',installed);save(record/'dependency-currentness.json',result)
    return runtime,result


def fixed_task(task,environment):
    task=literal(task)
    expected=literal(environment['RUNNER_TEMP'])/('salah-bfcache-source-preparation-'+environment['GITHUB_RUN_ID']+'-'+environment['GITHUB_RUN_ATTEMPT'])
    need(task==expected and task.is_dir(),'actual separate source-only task path differs')
    for path in (task,task/'records',task/'capture',task/'work'):
        info=path.stat()
        need(path.is_dir() and path.resolve()==path and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700,
             'private owned task directories required')
    source_only_absence(task);return task


def read_host(environment,record,supervisor,label):
    node=str(Path(shutil.which('node')).resolve())
    process=supervisor.run([node,'--version'],str(record.parent),environment,record/(label+'.stdout'),record/(label+'.stderr'),10)
    save(record/(label+'-process.json'),process);load_supervisor().successful(process)
    need(process['stderr']=='','unexpected Node version stderr')
    release={k:v.strip('"') for k,v in (line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)}
    host=validate_host(environment,release,process['stdout'].strip(),sys.version_info[:2])
    from bfcache_source_payload import file_record
    return node,host,{'osRelease':release,'nodeVersion':process['stdout'].strip(),'pythonVersion':sys.version,
        'pythonExecutable':{'path':sys.executable,'resolved':str(Path(sys.executable).resolve()),
                            **file_record(Path(sys.executable).resolve(),1<<30)}}


def source_child_context(operation,task,workspace):
    need(operation in ('check-source','refuse-native-common'),'unavailable fixed child operation')
    os.umask(0o077);sys.dont_write_bytecode=True
    environment=clean_environment();os.environ.clear();os.environ.update(environment)
    task=fixed_task(task,environment);roots=roots_for(workspace);record=task/'records'
    contract=validate_contract(load(CONTRACT));supervisor=load_supervisor().Supervisor()
    save(record/(operation+'-start.json'),{'protocol':'fixed-bf-source-child-start/1','operation':operation,
        'pid':supervisor.pid,'startTicks':supervisor.started,'argv':list(sys.argv),'python':sys.executable,
        'task':str(task),'nativeExecution':'NOT_RUN'})
    node,host,_=read_host(environment,record,supervisor,operation+'-node-version')
    sources=validate_inputs(contract,roots,host);before=load(record/'sources-before.json')
    need(same(sources,before),'child source inputs differ from parent admission')
    independent=target_physical_map(sources['target']);central,physical=import_target(roots,sources,independent)
    need(same(physical,load(record/'target-physical-before.json')),'child physical source differs from parent admission')
    save(record/(operation+'-source-before.json'),{'sources':sources,'targetPhysical':physical})
    dependency=load(record/'dependency-identity.json');runtime,_=runtime_current(task,dependency)
    need(runtime['node']==node and sys.executable==runtime['python']
         and str(Path(sys.executable).resolve())==dependency['binaries']['python']['resolved'],
         'fixed source child is not the admitted preparation interpreter')
    environment.update(NODE_PATH=runtime['modules'],PLAYWRIGHT_BROWSERS_PATH=str(task/'source-runtime/unused-browsers'))
    os.environ.update(environment)
    return task,roots,record,contract,host,sources,physical,central,runtime,environment,supervisor


def generated_command(task,roots,runtime):
    return {'argv':[runtime['node'],str(roots['target']/'tools/qa/hosted-native/r002f_tabhide.cjs'),
                    '--admit-generated',str(Path(task)/'work/r002f-prepared/baseline'),str(Path(task)/'work/r002f-prepared/candidate')],
            'cwd':str(roots['target']/'tools/qa/hosted-native'),'timeoutSeconds':30}


def generated_runner(task,roots,runtime,environment,supervisor):
    expected=generated_command(task,roots,runtime);record=Path(task)/'records'
    def run(argv,**kwargs):
        need(same(argv,expected['argv']) and set(kwargs)=={'cwd','stdout','stderr','timeout','check'}
             and kwargs['cwd']==Path(expected['cwd']) and kwargs['stdout']==subprocess.PIPE and kwargs['stderr']==subprocess.PIPE
             and type(kwargs['timeout']) is int and kwargs['timeout']==30 and kwargs['check'] is False,
             'original generated source command contract differs')
        save(record/'generated-admission-request.json',expected)
        process=supervisor.run(argv,expected['cwd'],environment,record/'generated-admission.stdout',record/'generated-admission.stderr',30)
        save(record/'generated-admission-process.json',process)
        stdout=(record/'generated-admission.stdout').read_bytes();stderr=(record/'generated-admission.stderr').read_bytes()
        if process['timedOut']:raise subprocess.TimeoutExpired(argv,30,output=stdout,stderr=stderr)
        load_supervisor().successful(process)
        need(process['stdout']==stdout.decode('utf-8',errors='replace') and process['stderr']==stderr.decode('utf-8',errors='replace'),
             'generated process/raw streams differ')
        return subprocess.CompletedProcess(argv,process['returncode'],stdout,stderr)
    return run


def check_source(task,workspace):
    context=source_child_context('check-source',task,workspace)
    task,roots,record,contract,host,sources,physical,central,runtime,environment,supervisor=context
    try:
        import r003f_matrix_campaign as common
        import lanes
        prepared,custody=common.common_custody(task/'work/prepared/receipts/prepared.json',
            task/'capture/preparation-process.json',task/'capture/preparation-context.json',native=False)
        save(record/'original-common-custody.json',custody)
        admission=lanes.admit_r002f_tabhide(task/'work/r002f-prepared/build-result.json',task/'capture/r002f-preparation-process.json',
            prepared,task/'work/prepared/receipts/prepared.json',Path(runtime['node']),
            run_currentness=generated_runner(task,roots,runtime,environment,supervisor))
        save(record/'original-r002f-admission.json',admission)
        need(admission.get('status')=='PASS','original narrower R002F admission failed: '+str(admission.get('reason')))
        plan=central.make_plan(prepared,task/'capture/lanes',runtime,admission)
        save(record/'source-only-plan.json',plan)
        validate_blocked_plan(plan,prepared,task,roots,runtime,load(roots['target']/'tools/qa/hosted-native/r002f-bfcache-pins.json')['budget'])
        source_current(contract,roots,host,sources,physical,central,record/'check-source-source-after.json')
        runtime_current(task,load(record/'dependency-identity.json'))
        result={'protocol':'bfcache-hosted-source-only-admission/1','status':'PREPARED_SOURCE_ONLY',
            'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','fullCentralAdmission':'NOT_CLAIMED',
            'task':str(task),'runtime':runtime,'common':custody,'r002f':admission,'actualLaneCount':1,
            'originalNativeLaneRunnable':False,'originalDriverExecuted':False,'originalCountersOrWaitsChanged':False}
        save(record/'source-check-result.json',result);print(json.dumps(result,sort_keys=True));return 0
    except BaseException as error:
        save(record/'check-source-failure.json',{'type':type(error).__name__,'message':str(error),'status':'INCOMPLETE'})
        raise
    finally:
        quiet=supervisor.quiesce();save(record/'check-source-final-quiescence.json',quiet);verify_quiescence(quiet)


def refuse_native_common(task,workspace):
    context=source_child_context('refuse-native-common',task,workspace)
    task,roots,record,contract,host,sources,physical,central,runtime,environment,supervisor=context
    try:
        import r003f_matrix_campaign as common
        common.common_custody(task/'work/prepared/receipts/prepared.json',task/'capture/preparation-process.json',
                              task/'capture/preparation-context.json',native=True)
        raise ValueError('original native common unexpectedly admitted a source-only task')
    finally:
        quiet=supervisor.quiesce();save(record/'refuse-native-common-final-quiescence.json',quiet);verify_quiescence(quiet)


def expected_blocked_plan(prepared,task,roots,runtime,budget):
    """Independent literal rendering of the pinned original source-only blocked plan."""
    task=Path(task);out=task/'capture/lanes';lane='r002f-bfcache-chromium-dpr1';output=out/lane
    arms={'main':{'root':prepared['trees']['main']['root'],'commit':'df644ef60156b67b5c487395176369bcec7a0d7b','flags':''}}
    for label,writes in (('unmodified','full'),('mitigated','changed')):
        arms[label]={'root':prepared['trees']['r0035']['root'],'commit':'55d1b3edb66d2c35679707120b01ee1d3455e4a3',
            'flags':'&r35arm='+writes+'&r35scope=all&r35amplitude=1&r35glass=0.5&r35margin=4',
            'producerProbe':{'path':'stars.status','equals':'active'}}
    return {'schemaVersion':1,'protocol':'salah-hosted-native-lanes/1','sequential':True,'workOrders':['R002F'],
        'scope':'One paired R002F Moon bfcache witness diagnostic; no product/owner-policy acceptance.',
        'evidenceRetention':False,'r0035Controls':{'guard':'default','scope':'all','mode':'both'},'r0035Stages':False,
        'r003fHarness':'published','r0040Mode':'options','r002fRoute':'bfcache-witness','r0035PlanPath':str(out/'r0035-plan.json'),
        'r0035Plan':{'kind':'independent-reconstruction','arms':arms},
        'lanes':[{'id':lane,'workOrder':'R002F','engine':'chromium','dpr':1,'cwd':str(roots['target']/'tools/qa/hosted-native'),
            'env':{'NODE_PATH':runtime['modules']},'output':str(output),'stdout':str(out/(lane+'.stdout')),'stderr':str(out/(lane+'.stderr')),
            'argv':[],'timeoutSeconds':4200,'postObservationCheckSeconds':120,
            'result':{'kind':'r002f-bfcache-witness','path':str(output/'result.json'),'expectedArms':['baseline','candidate'],
                'expectedEventsPerArm':3,'nativeQualification':'R002F_BFCACHE_MOON_WITNESS_ONLY'},
            'exitStatuses':{'0':'OBSERVED_BFCACHE_DIAGNOSTIC','2':'INCOMPLETE','86':'ISOLATION_FAIL'},
            'dependsOn':[],'stopScopeOnAndon':'R002F','stopAllOnExit':[86],
            'preparation':{'status':'INCOMPLETE','reason':'native current preparation is absent or rebound'},
            'bfcacheObservation':{'protocol':'r002f-bfcache-diagnostic/1','budget':budget,'captureCallsAdded':0},
            'evidenceRetention':{'instrumented':True,'output':str(output),'timingClass':'instrumented-existing-witness-retention',
                'timingComparableToOriginal':False,'overhead':'Existing return retention, source/owner checks, IPC and hashing add uncalibrated time; no added screenshots or page evaluations.'}}],
        'failurePolicy':{'isolation':'stop all observations','incompleteArm':'stop pair; retain actual evidence',
                         'timeout':'kill owned child; incomplete; namespace teardown remains separate'}}


def validate_blocked_plan(plan,prepared,task,roots,runtime,budget):
    need(same(plan,expected_blocked_plan(prepared,task,roots,runtime,budget)),
         'complete original blocked source-only plan differs or gained native authority')
    return plan


def validate_negative_process(process,expected,kind,task):
    need(all(same(process.get(k),v) for k,v in expected.items()),'original negative argv/cwd/ceiling differs')
    elapsed=process.get('elapsedSeconds')
    need(type(elapsed) in (int,float) and 0<=elapsed<=expected['timeoutSeconds'],'negative process elapsed outside original ceiling')
    verify_quiescence(process.get('quiescence',{}))
    if kind=='refuse-native-common':native_refusal(process)
    elif kind=='central-no-runtime':central_refusal(process,task)
    else:raise ValueError('unknown designated source-only refusal')


def run(task,workspace):
    os.umask(0o077);sys.dont_write_bytecode=True
    environment=clean_environment();os.environ.clear();os.environ.update(environment)
    task=fixed_task(task,environment);roots=roots_for(workspace);record=task/'records'
    need(not (record/'result.json').exists(),'source task cannot be reused')
    contract=validate_contract(load(CONTRACT));started=time.monotonic();overall=started+3450
    result={'protocol':PROTOCOL,'scope':'SOURCE_ONLY','status':'INCOMPLETE','nativeIsolationClaim':False,'nativeExecution':'NOT_RUN',
        'fullCentralAdmission':'NOT_CLAIMED','speed':'NOT_ESTABLISHED','stage':'input-validation','task':str(task),
        'roots':{k:str(v) for k,v in roots.items()},'actualProcesses':[],'failures':[]}
    sources={name:{'status':'NOT_ADMITTED','root':str(root)} for name,root in roots.items()};supervisor=None
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(Deadline('actual source-only phase ceiling reached')))
    arm_deadline(overall)
    try:
        module=load_supervisor();supervisor=module.Supervisor()
        save(record/'coordinator-identity.json',{'pid':supervisor.pid,'startTicks':supervisor.started})
        node,host,host_record=read_host(environment,record,supervisor,'host-node-version')
        sources=validate_inputs(contract,roots,host);save(record/'sources-before.json',sources)
        binding={**host,'workflowTree':sources['harness']['tree'],'targetCommit':sources['target']['commit'],
            'targetTree':sources['target']['tree'],'campaignSha256':contract['target']['campaignSha256'],
            'contractSha256':sha(CONTRACT.read_bytes())}
        save(record/'binding.json',binding);result.update(binding=binding,host=host_record)
        independent=target_physical_map(sources['target']);save(record/'target-physical-preimport.json',independent)
        central,physical=import_target(roots,sources,independent);save(record/'target-physical-before.json',physical)
        result['stage']='locked-source-runtime';arm_deadline(min(overall,time.monotonic()+720))
        runtime,dependency_before=install_source_runtime(task,roots,node,supervisor,environment,record)
        environment.update(NODE_PATH=runtime['modules'],PATH=str(Path(node).parent)+os.pathsep+environment['PATH'])
        os.environ.update(environment)
        preparation_started=time.monotonic();arm_deadline(min(overall,preparation_started+2160))
        for phase,prefix,process_path in (
                ('common',task/'capture/preparation',task/'capture/preparation-process.json'),
                ('r002f',task/'capture/r002f-preparation',task/'capture/r002f-preparation-process.json'),
                ('check-source',record/'source-check',record/'source-check-process.json')):
            result['stage']='original-'+phase
            command=command_for_phase(phase,task,roots,runtime)
            if phase=='common':
                save(task/'capture/preparation-context.json',{'protocol':'source-only-common-preparation-execution/1',**command,
                    'sourceSha256':sha((roots['target']/'tools/qa/hosted-native/prepare.py').read_bytes()),'nativeIsolationClaim':False})
            save(record/(phase+'-request.json'),command)
            process=supervisor.run(command['argv'],command['cwd'],environment,Path(str(prefix)+'.stdout'),Path(str(prefix)+'.stderr'),command['timeoutSeconds'])
            save(process_path,process);result['actualProcesses'].append(('task/' if process_path.is_relative_to(task/'capture') else 'records/')+
                (str(process_path.relative_to(task)) if process_path.is_relative_to(task/'capture') else process_path.name))
            module.successful(process)
            if phase=='common':need(process['stdout'].strip()=='PREPARATION READY','original common terminal differs')
            elif phase=='r002f':need(process['stdout'].strip()=='R002F_BUILD PASS','original R002F terminal differs')
            else:
                from bfcache_source_payload import load_json
                admission=load(record/'source-check-result.json')
                need(same(load_json(process['stdout']),admission) and admission['protocol']=='bfcache-hosted-source-only-admission/1'
                     and admission['status']=='PREPARED_SOURCE_ONLY' and admission['nativeIsolationClaim'] is False
                     and admission['nativeExecution']=='NOT_RUN' and admission['fullCentralAdmission']=='NOT_CLAIMED',
                     'fixed source child terminal authority differs')
            source_current(contract,roots,host,sources,physical,central,record/(phase+'-source-currentness.json'))
            source_only_absence(task)
        result['preparationElapsedSeconds']=time.monotonic()-preparation_started
        need(result['preparationElapsedSeconds']<=2160,'original combined BF preparation ceiling exceeded')
        post_started=time.monotonic();arm_deadline(min(overall,post_started+240))
        for phase in ('refuse-native-common','central-no-runtime'):
            result['stage']=phase;command=command_for_phase(phase,task,roots,runtime)
            save(record/(phase+'-request.json'),command)
            process=supervisor.run(command['argv'],command['cwd'],environment,record/(phase+'.stdout'),record/(phase+'.stderr'),command['timeoutSeconds'])
            save(record/(phase+'-process.json'),process);result['actualProcesses'].append('records/'+phase+'-process.json')
            validate_negative_process(process,command,phase,task)
            source_current(contract,roots,host,sources,physical,central,record/(phase+'-source-currentness.json'))
            source_only_absence(task)
        result['postSourceElapsedSeconds']=time.monotonic()-post_started
        need(result['postSourceElapsedSeconds']<=240,'designated post-source checks exceeded their bound')
        arm_deadline(overall);result['stage']='final-source-currentness'
        current=source_current(contract,roots,host,sources,physical,central,record/'final-source-currentness.json')
        save(record/'sources-after.json',current['sources']);save(record/'target-physical-after.json',current['targetPhysical'])
        runtime_current(task,dependency_before,record)
        result.update(status='PREPARED_SOURCE_ONLY',stage='complete',sourceUnchanged=True,
            originalNativeRefusal=NATIVE_REFUSAL,originalCentralRefusal='MISSING_ACQUIRED_RUNTIME_AT_ORIGINAL_LOAD',actualLaneCount=1,
            originalNativeLaneRunnable=False,originalDriverExecuted=False,originalCountersOrWaitsChanged=False)
    except BaseException as error:
        result['failures'].append({'stage':result['stage'],'type':type(error).__name__,'message':str(error)});traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if not (record/'sources-before.json').exists():save(record/'sources-before.json',sources)
        if supervisor is not None:
            try:
                quiet=supervisor.quiesce();save(record/'final-quiescence.json',quiet);verify_quiescence(quiet)
            except BaseException as error:
                result['status']='INCOMPLETE';result['failures'].append({'stage':'final-quiescence','type':type(error).__name__,'message':str(error)})
        else:save(record/'final-quiescence.json',{'protocol':'source-only-descendant-quiescence/1','quiescent':True,
            'unexpectedDescendants':False,'before':[],'remaining':[],'scope':'no source producer was started'})
        result['elapsedSeconds']=time.monotonic()-started
        if result['elapsedSeconds']>3450:
            result['status']='INCOMPLETE';result['failures'].append({'stage':'coordinator-ceiling','type':'Deadline','message':'source coordinator exceeded declared outer ceiling'})
        save(record/'result.json',result)
    return 0 if result['status']=='PREPARED_SOURCE_ONLY' else 1


def seal(task,workspace):
    os.umask(0o077);sys.dont_write_bytecode=True
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(Deadline('source-only sealing ceiling reached')))
    signal.setitimer(signal.ITIMER_REAL,1200)
    try:
        environment=clean_environment();os.environ.clear();os.environ.update(environment)
        task=fixed_task(task,environment);roots=roots_for(workspace);record=task/'records'
        contract=validate_contract(load(CONTRACT))
        own=source_identity(roots['harness'],contract['harnessFiles'])
        need(roots['harness']==ROOT and own['commit']==environment['GITHUB_SHA'],'actual sealing harness differs')
        validate_workflow(roots['harness'],contract)
        module=load_supervisor();supervisor=module.Supervisor()
        need(not supervisor.descendants(),'unexpected sealing descendant')
        _,host,_=read_host(environment,record,supervisor,'seal-node-version')
        binding={**host,'workflowTree':own['tree'],'targetCommit':contract['target']['commit'],'targetTree':contract['target']['tree'],
            'campaignSha256':contract['target']['campaignSha256'],'contractSha256':sha(CONTRACT.read_bytes())}
        if (record/'binding.json').exists():need(same(load(record/'binding.json'),binding),'source result and sealing workflow differ')
        else:save(record/'binding.json',binding)
        result=load(record/'result.json')
        need(result.get('protocol')==PROTOCOL and result.get('scope')=='SOURCE_ONLY' and result.get('nativeIsolationClaim') is False
             and result.get('nativeExecution')=='NOT_RUN' and result.get('status') in ('PREPARED_SOURCE_ONLY','INCOMPLETE'),
             'source-only terminal record missing or gained authority')
        verify_quiescence(load(record/'final-quiescence.json'))
        if (record/'coordinator-identity.json').exists():
            producer=load(record/'coordinator-identity.json');actual=module.process_table().get(producer['pid'])
            need(actual is None or actual['startTicks']!=producer['startTicks'],'source coordinator remains alive during sealing')
        before=load(record/'sources-before.json');errors=[]
        try:
            current=validate_inputs(contract,roots,host)
            need(same(current,before),'source changed between preparation and sealing')
            independent=target_physical_map(current['target']);central,physical=import_target(roots,current,independent)
            need(same(physical,load(record/'target-physical-before.json')),'physical source changed before sealing')
            save(record/'seal-source-currentness.json',{'sources':current,'targetPhysical':physical})
        except Exception as error:errors.append({'type':type(error).__name__,'message':str(error)})
        save(record/'seal-admission.json',{'protocol':'source-only-sealing-admission/1','binding':binding,'harness':own,
            'originalStatus':result['status'],'sourceCurrent':not errors,'errors':errors,'sourceOnlyAuthority':True,
            'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN'})
        collections=[{'prefix':'records','root':record,'names':None}]
        for name in ('capture','work/prepared','work/r002f-prepared'):
            if (task/name).exists():collections.append({'prefix':'task/'+name,'root':task/name,'names':None})
        for role in ROLES:
            value=before[role]
            if value.get('clean') is True:collections.append({'prefix':'sources/'+role,'root':roots[role],'names':sorted(value['files'])})
        from bfcache_source_payload import seal_collections,inventory_collections,canonical as payload_bytes
        logical,objects,_=inventory_collections(collections);unique=sum(row['bytes'] for row in objects)
        free=shutil.disk_usage(task).free;required=2*unique+4*(96<<20)+4*(18<<20)+(256<<20)
        save(record/'seal-space-preflight.json',{'protocol':'source-only-sealing-space/1','freeBytes':free,'requiredBytes':required,
            'existingLogicalBytes':sum(r['bytes'] for r in logical),'existingUniqueBytes':unique,
            'formula':'2*unique + 4*96MiB shard workspace + 4*18MiB index workspace + 256MiB margin'})
        need(free>=required,'insufficient actual space for source-only envelope set')
        packing=task/'packing';packing.mkdir(mode=0o700)
        logical_roots={**{k:str(v) for k,v in roots.items()},'task':str(task),'records':str(record)}
        identities={k:sha(payload_bytes(before[k])) for k in ROLES}
        seal_collections(collections,binding,identities,logical_roots,task/'sealed',packing,HERE/'recipient.crt')
        verify_quiescence(supervisor.quiesce())
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    print('SOURCE_ONLY_ENVELOPE_SET_SEALED');return 0


def verify_owned_quiescence(value,owner):
    verify_quiescence(value)
    need(type(owner) is dict and set(owner)=={'pid','startTicks'}
         and all(type(owner[k]) is int and owner[k]>0 for k in owner)
         and type(value.get('coordinatorPid')) is int and value['coordinatorPid']==owner['pid']
         and type(value.get('coordinatorStartTicks')) is int and value['coordinatorStartTicks']==owner['startTicks'],
         'retained supervisor ownership differs')


def verify_stream_process(value,expected,stdout,stderr,owner,negative=None,task=None):
    if negative is None:retained_process(value,expected)
    else:validate_negative_process(value,expected,negative,task)
    need(type(value.get('pid')) is int and value['pid']>0 and type(value.get('startTicks')) is int and value['startTicks']>0,
         'retained child PID/start identity is incomplete')
    verify_owned_quiescence(value['quiescence'],owner)
    need(type(stdout) is bytes and type(stderr) is bytes
         and value.get('stdout')==stdout.decode('utf-8',errors='replace')
         and value.get('stderr')==stderr.decode('utf-8',errors='replace'),'actual process and raw terminal streams differ')
    return value


def verify_source_child(start,process,expected,operation,task):
    need(type(start) is dict and set(start)=={'protocol','operation','pid','startTicks','argv','python','task','nativeExecution'}
         and start['protocol']=='fixed-bf-source-child-start/1' and start['operation']==operation
         and same(start['argv'],expected['argv'][2:]) and start['python']==expected['argv'][0]
         and start['task']==str(task) and start['nativeExecution']=='NOT_RUN'
         and type(start['pid']) is int and start['pid']==process['pid']
         and type(start['startTicks']) is int and start['startTicks']==process['startTicks'],
         'fixed original source child start/parent identity differs')
    return {k:start[k] for k in ('pid','startTicks')}


def success_record_names():
    names={'coordinator-identity.json','coordinator.stdout','coordinator.stderr','sources-before.json','binding.json','target-physical-preimport.json','target-physical-before.json',
        'dependency-identity.json','source-runtime.json','original-common-custody.json','original-r002f-admission.json',
        'source-only-plan.json','source-check-result.json','final-source-currentness.json','sources-after.json','target-physical-after.json',
        'dependency-files-after.json','dependency-currentness.json','final-quiescence.json','result.json',
        'seal-source-currentness.json','seal-admission.json','seal-space-preflight.json'}
    labels=['host-node-version','python-environment','node-packages','python-packages','package-identity','source-check',
        'generated-admission','check-source-node-version','refuse-native-common-node-version','refuse-native-common','central-no-runtime','seal-node-version']
    names|={label+suffix for label in labels for suffix in ('.stdout','.stderr','-process.json')}
    names|={phase+suffix for phase in ('common','r002f','check-source','refuse-native-common','central-no-runtime')
            for suffix in ('-request.json','-source-currentness.json')}
    names|={operation+suffix for operation in ('check-source','refuse-native-common')
            for suffix in ('-start.json','-source-before.json','-final-quiescence.json')}
    names|={'check-source-source-after.json','generated-admission-request.json'}
    return {'records/'+name for name in names}


def retained_source_metadata(index,logical,raw,before,contract):
    """Read metadata only; immutable Git membership is the independent root anchor's mandatory job."""
    from bfcache_source_payload import load_json
    roots=index['logicalRoots'];binding=index['binding'];counts={'harness':16,'target':111,'research':1012,'baseline':931,'historical':6}
    need(roots['records']==str(PurePosixPath(roots['task'])/'records')
         and PurePosixPath(roots['task']).name=='salah-bfcache-source-preparation-'+str(binding['runId'])+'-'+str(binding['runAttempt']),
         'fixed hosted task/records binding differs')
    workspace=PurePosixPath(roots['harness']).parent
    need(roots['harness']==str(workspace/'source-preparation')
         and all(roots[r]==str(workspace/r) for r in ('target','research','baseline','historical')),
         'fixed source workspace roles differ')
    source_dirs=[PurePosixPath(roots[r]) for r in ROLES]+[PurePosixPath(roots['task'])]
    need(all(a!=b and not a.is_relative_to(b) and not b.is_relative_to(a) for i,a in enumerate(source_dirs) for b in source_dirs[i+1:]),
         'hosted source/task roots overlap')
    target_manifest_path='sources/target/'+contract['target']['sourceManifestPath']
    need(sha(raw(target_manifest_path))==contract['target']['sourceManifestSha256'],'raw immutable target manifest pin differs')
    manifest=load_json(raw(target_manifest_path));target_names=manifest['sourceFiles']
    need(type(target_names) is list and target_names==sorted(set(target_names)) and len(target_names)==111,
         'declared target manifest population differs')
    for role in ROLES:
        value=before[role]
        need(type(value) is dict and set(value)=={'protocol','root','commit','tree','clean','files'}
             and value['protocol']=='source-only-declared-git-inputs/1' and value['root']==roots[role] and value['clean'] is True
             and type(value['files']) is dict and len(value['files'])==counts[role],'retained complete source role differs')
        pins=({'commit':binding['workflowCommit'],'tree':binding['workflowTree']} if role=='harness'
              else contract['target'] if role=='target' else contract['sources'][role])
        need(all(value[k]==pins[k] for k in ('commit','tree')),'retained immutable source role identity differs')
        files=value['files'];names=(contract['harnessFiles'] if role=='harness' else target_names if role=='target' else source_paths(role))
        need(set(files)==set(selected_source(files,names))
             and all(any(n==p or n.startswith(p+'/') for n in files) for p in names),'retained source declared path scope differs')
        if role in ('harness','target','historical'):need(set(files)==set(names),'retained exact declared source paths differ')
        need({n for n in logical if n.startswith('sources/'+role+'/')}=={'sources/'+role+'/'+n for n in files},
             'complete retained source logical population differs')
        for name,row in files.items():
            safe_relative(name)
            need(type(row) is dict and set(row)=={'bytes','sha256','gitBlob','mode'} and type(row['bytes']) is int and row['bytes']>=0
                 and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256'])
                 and type(row['gitBlob']) is str and re.fullmatch('[0-9a-f]{40}',row['gitBlob']) and row['mode'] in ('100644','100755')
                 and same(size_digest(logical['sources/'+role+'/'+name]),size_digest(row)),
                 'retained compact source row/body differs')
    for role in ('harness','target'):
        need(sha(raw('sources/'+role+'/.github/workflows/research-native-pilot.yml'))==contract['target']['nativeWorkflowSha256'],
             'unchanged native workflow bytes differ')
    need(sha(raw('sources/harness/'+contract['workflowPath']))==contract['workflowSha256']
         and sha(raw('sources/target/'+contract['target']['campaignPath']))==contract['target']['campaignSha256'],
         'fixed source-only workflow or receiving campaign differs')
    return counts


def verify_dependency_records(body,raw,task,roots,runtime,dependency,host,owner,contract):
    source_sdk_schema(runtime,task)
    need(type(dependency) is dict and set(dependency)=={'protocol','nativeIsolationClaim','nativeExecution','runtime',
         'nodePackages','python','binaries','installedFiles','managedBrowserPopulation'}
         and dependency['protocol']=='source-only-installed-driver-dependencies/1' and dependency['nativeIsolationClaim'] is False
         and dependency['nativeExecution']=='NOT_RUN' and same(dependency['runtime'],runtime)
         and same(dependency['nodePackages'],contract['runtime']['nodePackages']) and dependency['managedBrowserPopulation']==[],
         'actual source-only SDK identity differs')
    python=dependency['python']
    need(type(python) is dict and set(python)=={'python','version','site','packages'} and same(python['version'],[3,11])
         and same(python['packages'],{'playwright':'1.57.0','pyee':'13.0.0','greenlet':'3.2.4','typing_extensions':'4.15.0'})
         and python['python']==host['pythonVersion'] and type(python['site']) is str
         and PurePosixPath(python['site']).is_relative_to(PurePosixPath(task)/'source-runtime/python'),
         'actual locked Python source SDK differs')
    need(host['osRelease'].get('ID')=='ubuntu' and host['osRelease'].get('VERSION_ID')=='22.04'
         and host['nodeVersion']=='v24.14.0' and type(host['pythonVersion']) is str and host['pythonVersion'].startswith('3.11.'),
         'actual hosted source-only runtime pins differ')
    binaries=dependency['binaries'];host_python=host['pythonExecutable']
    need(type(binaries) is dict and set(binaries)=={'python','node'},'actual source SDK binary population differs')
    for name,row in binaries.items():
        need(type(row) is dict and set(row)=={'path','resolved','bytes','sha256'} and row['path']==runtime[name]
             and type(row['resolved']) is str and PurePosixPath(row['resolved']).is_absolute()
             and str(PurePosixPath(row['resolved']))==row['resolved'] and '..' not in PurePosixPath(row['resolved']).parts
             and type(row['bytes']) is int and 0<row['bytes']<=1<<30 and type(row['sha256']) is str
             and re.fullmatch('[0-9a-f]{64}',row['sha256']),'actual source SDK binary descriptor differs')
    need(type(host_python) is dict and set(host_python)=={'path','resolved','bytes','sha256'}
         and type(host_python['path']) is str and PurePosixPath(host_python['path']).is_absolute()
         and same({k:host_python[k] for k in ('resolved','bytes','sha256')},
                  {k:binaries['python'][k] for k in ('resolved','bytes','sha256')}),
         'source SDK Python does not match the actual setup interpreter')
    installed=dependency['installedFiles'];after=body('records/dependency-files-after.json')
    need(type(installed) is dict and installed and same(installed,after),'actual complete source SDK before/after inventory differs')
    for name,row in installed.items():
        safe_relative(name);need(name.startswith(('node/','python/')) and type(row) is dict,'unexpected installed source SDK population')
        if row.get('kind')=='file':
            need(set(row)=={'kind','bytes','sha256'} and type(row['bytes']) is int and 0<=row['bytes']<=1<<30
                 and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']),'installed SDK file descriptor differs')
        else:
            need(set(row)=={'kind','target'} and row['kind']=='symlink' and type(row['target']) is str and row['target'],
                 'installed SDK link descriptor differs')
    for filename,key in (('package.json','packageJsonSha256'),('package-lock.json','packageLockSha256')):
        need(installed['node/'+filename]['sha256']==contract['runtime'][key],'installed locked Node input differs')
    need(same(body('records/dependency-currentness.json'),{'protocol':'source-only-runtime-currentness/1',
        'beforeSha256':sha(canonical(installed)),'afterSha256':sha(canonical(after)),'files':len(installed),
        'binaries':binaries,'managedBrowserPopulation':[]}),'retained actual source SDK currentness differs')
    for label,argv,seconds in source_runtime_commands(task,roots,runtime['node'],host_python['path']):
        process=body('records/'+label+'-process.json')
        verify_stream_process(process,{'argv':argv,'cwd':str(task),'timeoutSeconds':seconds},
                              raw('records/'+label+'.stdout'),raw('records/'+label+'.stderr'),owner)
    from bfcache_source_payload import load_json
    need(same(load_json(raw('records/package-identity.stdout')),python),'actual package identity terminal differs')


def verify_original_common_children(logical,body,task,roots,runtime):
    expected=original_child_commands(task,roots,runtime);prefix='task/work/prepared/receipts/'
    paths=[prefix+str(i+1).zfill(2)+'-'+child['label']+'.json' for i,child in enumerate(expected)]
    extra={'prepared.json','baseline-files.json','research-files.json','r0040-patch.json','r0035-lab-identity.json','r003f-runtime-files.json'}
    wanted={prefix+n for n in extra}|set(paths)|{p[:-5]+'.'+s for p in paths for s in ('stdout','stderr')}
    need({n for n in logical if n.startswith(prefix)}==wanted,'complete original common receipt/stream population differs')
    for path,command in zip(paths,expected):
        process=body(path)
        need(type(process) is dict and set(process)=={'argv','cwd','elapsedSeconds','returncode','startedUnixSeconds','status','stdout','stderr','timeoutSeconds'}
             and process['status']=='PASS' and type(process['returncode']) is int and process['returncode']==0
             and type(process['timeoutSeconds']) is int and process['timeoutSeconds']==600
             and type(process['elapsedSeconds']) in (int,float) and 0<=process['elapsedSeconds']<=600
             and type(process['startedUnixSeconds']) in (int,float) and process['startedUnixSeconds']>0
             and same(process['argv'],command['argv']) and process['cwd']==command['cwd'],
             'actual original nested common child command or completion differs')
        for stream in ('stdout','stderr'):
            need(process[stream]==str(task/Path(path[5:]).with_suffix('.'+stream)),'original child raw stream path differs')
        if 'build-' in command['label'] and 'materialize' not in command['label']:
            terminal=body(path[:-5]+'.stdout')
            need(terminal.get('stage')=='complete-native-and-moon' and terminal.get('phase')=='published','original builder terminal missing')
            if command['label'].endswith('-2'):
                need(same({k:terminal.get(k) for k in ('written','removed','unchanged')},{'written':0,'removed':0,'unchanged':117}),
                     'original common second-build unchanged population differs')
    return len(paths)


def inspect_source_records(index,logical,raw):
    """Pure retained-record relations; no retained code, builder, Git or native execution.

    This seam is also usable for explicitly synthetic metadata controls. It has
    no raw-object or immutable-tree authority by itself. The public inspector
    first verifies every object and Git-body hash; the separate root anchor must
    still establish membership in the independently known five immutable trees.
    """
    from bfcache_source_payload import load_json,canonical as payload_bytes
    body=lambda name:load_json(raw(name))
    before=body('records/sources-before.json');result=body('records/result.json');sealed=body('records/seal-admission.json')
    binding=index['binding'];roots=index['logicalRoots'];task=Path(roots['task']);source_roots={k:Path(roots[k]) for k in ROLES}
    need(same(body('records/binding.json'),binding) and same(sealed.get('binding'),binding),
         'retained workflow/run/target binding differs')
    need(type(before) is dict and set(before)==set(ROLES)
         and all(sha(payload_bytes(before[k]))==index['sourceIdentities'][k] for k in ROLES),
         'retained complete source identity binding differs')
    need(result.get('protocol')==PROTOCOL and result.get('scope')=='SOURCE_ONLY' and result.get('nativeIsolationClaim') is False
         and result.get('nativeExecution')=='NOT_RUN' and result.get('fullCentralAdmission')=='NOT_CLAIMED'
         and result.get('status') in ('PREPARED_SOURCE_ONLY','INCOMPLETE') and type(result.get('failures')) is list,
         'retained source-only authority differs')
    need(sealed.get('protocol')=='source-only-sealing-admission/1' and sealed.get('originalStatus')==result['status']
         and sealed.get('sourceOnlyAuthority') is True and sealed.get('nativeIsolationClaim') is False
         and sealed.get('nativeExecution')=='NOT_RUN' and type(sealed.get('sourceCurrent')) is bool
         and type(sealed.get('errors')) is list,'retained source-only sealing authority differs')
    verify_quiescence(body('records/final-quiescence.json'))
    report={'protocol':'bfcache-hosted-source-preparation-process-review/1','status':'INCOMPLETE','binding':binding,
        'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','fullCentralAdmission':'NOT_CLAIMED',
        'immutableTreeAnchor':'REQUIRED_SEPARATELY','originalStatus':result['status'],'failures':result['failures'],
        'sourceCurrentAtSealing':sealed['sourceCurrent'],'sealingErrors':sealed['errors']}
    if result['status']=='INCOMPLETE' or sealed['sourceCurrent'] is not True:return report
    need(result['failures']==[] and sealed['errors']==[] and result.get('sourceUnchanged') is True
         and result.get('stage')=='complete' and result.get('speed')=='NOT_ESTABLISHED'
         and result.get('originalDriverExecuted') is False and result.get('originalCountersOrWaitsChanged') is False
         and result.get('originalNativeLaneRunnable') is False and type(result.get('actualLaneCount')) is int
         and result['actualLaneCount']==1 and result.get('task')==str(task)
         and same(result.get('roots'),{r:roots[r] for r in ROLES}) and same(result.get('binding'),binding),
         'successful source terminal conditions differ')
    need({n for n in logical if n.startswith('records/')}==success_record_names(),'complete successful source record population differs')
    capture_names={'preparation-context.json','preparation-process.json','preparation.stdout','preparation.stderr',
                   'r002f-preparation-process.json','r002f-preparation.stdout','r002f-preparation.stderr'}
    need({n for n in logical if n.startswith('task/capture/')}=={'task/capture/'+n for n in capture_names},
         'source-only capture population gained acquisition/native/unknown records')
    for name in logical:
        if name.startswith('task/work/prepared/'):
            need(name.startswith(tuple('task/work/prepared/'+p+'/' for p in ('receipts','trees/main','trees/r0040','trees/r0035','trees/r003f'))),
                 'source-only common task gained an unknown population')
    contract_path='sources/harness/tools/qa/hosted-native/bfcache-source-preparation.json'
    contract=validate_contract(body(contract_path))
    need(sha(raw(contract_path))==binding['contractSha256'],'retained raw source-only contract differs')
    source_counts=retained_source_metadata(index,logical,raw,before,contract)
    need(same(before,body('records/sources-after.json')) and same(sealed['harness'],before['harness']),
         'actual complete source before/after/sealing admission differs')
    physical=body('records/target-physical-before.json');independent=body('records/target-physical-preimport.json')
    join_target_identity(before['target'],independent,physical)
    need(same(physical,body('records/target-physical-after.json')),'actual complete physical source changed')
    current={'protocol':'bfcache-source-only-currentness/1','sources':before,'targetPhysical':physical}
    for phase in ('common','r002f','check-source','refuse-native-common','central-no-runtime','final'):
        need(same(body('records/'+phase+'-source-currentness.json'),current),'retained phase source currentness differs: '+phase)
    for name in ('check-source-source-before','refuse-native-common-source-before','seal-source-currentness'):
        need(same(body('records/'+name+'.json'),{k:current[k] for k in ('sources','targetPhysical')}),
             'retained child/sealer source before differs')
    need(same(body('records/check-source-source-after.json'),current),'retained source-check after differs')
    runtime=body('records/source-runtime.json');dependency=body('records/dependency-identity.json');owner=body('records/coordinator-identity.json')
    verify_owned_quiescence(body('records/final-quiescence.json'),owner)
    verify_dependency_records(body,raw,task,source_roots,runtime,dependency,result['host'],owner,contract)
    processes={}
    for phase,prefix,process_path in (
            ('common','task/capture/preparation','task/capture/preparation-process.json'),
            ('r002f','task/capture/r002f-preparation','task/capture/r002f-preparation-process.json'),
            ('check-source','records/source-check','records/source-check-process.json'),
            ('refuse-native-common','records/refuse-native-common','records/refuse-native-common-process.json'),
            ('central-no-runtime','records/central-no-runtime','records/central-no-runtime-process.json')):
        command=command_for_phase(phase,task,source_roots,runtime)
        need(same(body('records/'+phase+'-request.json'),command),'retained fixed phase request differs')
        process=body(process_path)
        verify_stream_process(process,command,raw(prefix+'.stdout'),raw(prefix+'.stderr'),owner,
                              negative=phase if phase in ('refuse-native-common','central-no-runtime') else None,task=task)
        processes[phase]=process
    actual_processes=['task/capture/preparation-process.json','task/capture/r002f-preparation-process.json',
                     'records/source-check-process.json','records/refuse-native-common-process.json','records/central-no-runtime-process.json']
    need(same(result['actualProcesses'],actual_processes),'complete ordered actual phase process list differs')
    context={'protocol':'source-only-common-preparation-execution/1',**command_for_phase('common',task,source_roots,runtime),
        'sourceSha256':before['target']['files']['tools/qa/hosted-native/prepare.py']['sha256'],'nativeIsolationClaim':False}
    need(same(body('task/capture/preparation-context.json'),context),'original source-only common context differs')
    need(raw('task/capture/preparation.stdout').strip()==b'PREPARATION READY'
         and raw('task/capture/r002f-preparation.stdout').strip()==b'R002F_BUILD PASS','original preparation terminal differs')
    child_owners={}
    for operation in ('check-source','refuse-native-common'):
        child_owner=verify_source_child(body('records/'+operation+'-start.json'),processes[operation],
            command_for_phase(operation,task,source_roots,runtime),operation,task)
        child_owners[operation]=child_owner
        verify_owned_quiescence(body('records/'+operation+'-final-quiescence.json'),child_owner)
    version_owners={'host-node-version':owner,**{op+'-node-version':value for op,value in child_owners.items()}}
    seal_version=body('records/seal-node-version-process.json')
    version_owners['seal-node-version']={'pid':seal_version['quiescence']['coordinatorPid'],
                                        'startTicks':seal_version['quiescence']['coordinatorStartTicks']}
    for label,version_owner in version_owners.items():
        process=body('records/'+label+'-process.json')
        verify_stream_process(process,{'argv':[runtime['node'],'--version'],'cwd':str(task),'timeoutSeconds':10},
                              raw('records/'+label+'.stdout'),raw('records/'+label+'.stderr'),version_owner)
        need(process['stdout'].strip()=='v24.14.0' and process['stderr']=='','actual pinned Node version terminal differs')
    generated_command_value=generated_command(task,source_roots,runtime)
    need(same(body('records/generated-admission-request.json'),generated_command_value),'original generated request differs')
    generated_process=body('records/generated-admission-process.json')
    verify_stream_process(generated_process,generated_command_value,raw('records/generated-admission.stdout'),
                          raw('records/generated-admission.stderr'),child_owners['check-source'])
    generated=body('records/generated-admission.stdout');prepared=body('task/work/prepared/receipts/prepared.json')
    need(prepared['trees']['main']['root']==str(task/'work/prepared/trees/main'),'original common task root differs')
    common_counts=verify_prepared_populations(logical,body,before,prepared)
    child_count=verify_original_common_children(logical,body,task,source_roots,runtime)
    build=body('task/work/r002f-prepared/build-result.json')
    need(build['python']==dependency['python']['python'],'original R002F actual interpreter version differs')
    r002f_counts=verify_r002f_populations(logical,body,before,build,generated,task)
    def record(name,with_bytes=False):
        need(name in logical and name.startswith('task/'),'original task record path absent')
        return {'path':str(task/name[5:]),**({k:logical[name][k] for k in ('bytes','sha256')} if with_bytes else {'sha256':logical[name]['sha256']})}
    common_custody={key:record(name) for key,name in (
        ('prepared','task/work/prepared/receipts/prepared.json'),('process','task/capture/preparation-process.json'),
        ('context','task/capture/preparation-context.json'))}
    need(same(body('records/original-common-custody.json'),common_custody),'original common custody differs')
    trees={}
    for arm in ('baseline','candidate'):
        inv=body('task/work/r002f-prepared/'+arm+'/GENERATED.json');arm_result=build['arms'][arm]
        trees[arm]={'root':str(task/'work/r002f-prepared'/arm),'fileCount':inv['fileCount'],'byteCount':inv['byteCount'],
            'sha256':{'index.html':arm_result['indexSha256'],'GENERATED.json':arm_result['inventorySha256']}}
    expected_admission={'status':'PASS','processReceipt':record('task/capture/r002f-preparation-process.json'),
        'receipt':record('task/work/r002f-prepared/build-result.json'),'trees':trees,
        'sourceManifestSha256':generated['sourceManifestSha256'],'sourceManifest':generated['sourceManifest'],
        'generated':{arm:generated[arm] for arm in ('baseline','candidate')},
        'custody':{'process':record('task/capture/r002f-preparation-process.json'),'actualProcess':processes['r002f'],
            'streams':{s:record('task/capture/r002f-preparation.'+s,True) for s in ('stdout','stderr')},
            'commonPreparation':record('task/work/prepared/receipts/prepared.json'),
            'build':record('task/work/r002f-prepared/build-result.json'),
            'generatedAdmissionProcess':{**generated_command_value,'returncode':0,'timedOut':False}}}
    need(same(body('records/original-r002f-admission.json'),expected_admission),'complete original narrower R002F admission differs')
    expected_check={'protocol':'bfcache-hosted-source-only-admission/1','status':'PREPARED_SOURCE_ONLY',
        'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','fullCentralAdmission':'NOT_CLAIMED',
        'task':str(task),'runtime':runtime,'common':common_custody,'r002f':expected_admission,'actualLaneCount':1,
        'originalNativeLaneRunnable':False,'originalDriverExecuted':False,'originalCountersOrWaitsChanged':False}
    need(same(body('records/source-check-result.json'),expected_check)
         and same(body('records/source-check.stdout'),expected_check),'fixed source check and terminal result differ')
    pins=body('sources/target/tools/qa/hosted-native/r002f-bfcache-pins.json')
    validate_blocked_plan(body('records/source-only-plan.json'),prepared,task,source_roots,runtime,pins['budget'])
    need(result['originalNativeRefusal']==NATIVE_REFUSAL
         and result['originalCentralRefusal']=='MISSING_ACQUIRED_RUNTIME_AT_ORIGINAL_LOAD','retained specific native refusal meanings differ')
    for key,ceiling in (('preparationElapsedSeconds',2160),('postSourceElapsedSeconds',240),('elapsedSeconds',3450)):
        need(type(result[key]) in (int,float) and 0<=result[key]<=ceiling,'retained source-only aggregate ceiling differs')
    need(result['preparationElapsedSeconds']>=sum(processes[p]['elapsedSeconds'] for p in ('common','r002f','check-source'))
         and result['postSourceElapsedSeconds']>=sum(processes[p]['elapsedSeconds'] for p in ('refuse-native-common','central-no-runtime'))
         and result['elapsedSeconds']>=result['preparationElapsedSeconds']+result['postSourceElapsedSeconds'],
         'retained phase elapsed accounting is inconsistent')
    space=body('records/seal-space-preflight.json');preflight_rows=[r for n,r in logical.items() if n!='records/seal-space-preflight.json']
    unique={r['sha256']:r['bytes'] for r in preflight_rows};unique_bytes=sum(unique.values())
    required=2*unique_bytes+4*(96<<20)+4*(18<<20)+(256<<20)
    need(type(space.get('freeBytes')) is int and space['freeBytes']>=required
         and same(space,{'protocol':'source-only-sealing-space/1','freeBytes':space['freeBytes'],'requiredBytes':required,
             'existingLogicalBytes':sum(r['bytes'] for r in preflight_rows),'existingUniqueBytes':unique_bytes,
             'formula':'2*unique + 4*96MiB shard workspace + 4*18MiB index workspace + 256MiB margin'}),
         'actual original source-only sealing capacity preflight differs')
    report.update(status='SOURCE_PROCESS_GATE_PASS_PENDING_IMMUTABLE_ANCHOR',sourceFiles=source_counts,
        originalNestedCommonChildren=child_count,preparedTreeFiles=common_counts,r002f=r002f_counts,
        originalNativeRefusal=NATIVE_REFUSAL,originalCentralRefusal=result['originalCentralRefusal'],
        actualLaneCount=1,originalNativeLaneRunnable=False,originalDriverExecuted=False,
        relocatedPathsUsedOnlyForReadback=True,preparedTaskRematerialized=False,
        requiredCombinedVerdict='THIS_PROCESS_GATE_AND_SEPARATE_IMMUTABLE_FIVE_TREE_ANCHOR_ON_THE_SAME_AUTHENTICATED_OPEN_POPULATION')
    return report


def inspect_source_task(index_path,object_root,binding_path):
    from bfcache_source_payload import load_index,inspect,read_logical,load_json,file_record,MAX_INDEX_BYTES
    index_file=literal(Path(index_path)/'index.json');binding_file=literal(binding_path)
    index_before=file_record(index_file,MAX_INDEX_BYTES);index_raw=index_file.read_bytes()
    need(len(index_raw)==index_before['bytes'] and sha(index_raw)==index_before['sha256'],'index changed before inspection')
    binding_before=file_record(binding_file,1<<20);binding_raw=binding_file.read_bytes()
    need(len(binding_raw)==binding_before['bytes'] and sha(binding_raw)==binding_before['sha256'],'external binding changed before inspection')
    expected=load_json(binding_raw);index=load_index(index_path,expected)
    need(same(index,load_json(index_raw)),'loaded index differs from the recorded input')
    custody=inspect(index,object_root)
    logical={row['path']:row for row in index['logicalFiles']}
    raw=lambda name:read_logical(index,object_root,name,16<<20)
    before_raw=raw('records/sources-before.json')
    before=load_json(before_raw)
    for role in ROLES:
        value=before[role]
        if value.get('clean') is not True:continue
        for name,row in value['files'].items():
            wanted=logical.get('sources/'+role+'/'+name)
            need(wanted is not None and same(size_digest(wanted),size_digest(row)),
                 'retained source body is absent or differs from the compact map')
            digest=hashlib.sha1(b'blob '+str(row['bytes']).encode()+b'\0')
            # The complete raw-object gate above and after this read bounds and
            # rechecks every object; this pass additionally binds each Git body.
            with (Path(object_root)/row['sha256']).open('rb') as stream:
                for chunk in iter(lambda:stream.read(1<<20),b''):digest.update(chunk)
            need(digest.hexdigest()==row['gitBlob'],'retained raw source Git body differs')
    report=inspect_source_records(index,logical,raw)
    need(same(inspect(index,object_root),custody),'complete raw object population changed during source review')
    need(same(file_record(index_file,MAX_INDEX_BYTES),index_before) and same(file_record(binding_file,1<<20),binding_before),
         'index or external binding changed during source review')
    report.update(custody=custody,indexSha256=index_before['sha256'],bindingSha256=binding_before['sha256'],
                  sourceRecordsSha256=sha(before_raw),rawObjectPopulationRechecked=True)
    print(json.dumps(report,sort_keys=True))
    return 0 if report['status']=='SOURCE_PROCESS_GATE_PASS_PENDING_IMMUTABLE_ANCHOR' else 1


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('run','seal','check-source','refuse-native-common','inspect'))
    parser.add_argument('--task',type=Path);parser.add_argument('--workspace',type=Path)
    parser.add_argument('--index',type=Path);parser.add_argument('--objects',type=Path);parser.add_argument('--binding',type=Path)
    args=parser.parse_args(argv)
    if args.operation=='inspect':
        need(args.index is not None and args.objects is not None and args.binding is not None
             and args.task is None and args.workspace is None,'fixed inspection arguments required')
        return inspect_source_task(args.index,args.objects,args.binding)
    need(args.task is not None and args.workspace is not None and args.index is None and args.objects is None and args.binding is None,
         'fixed source task/workspace arguments required')
    return {'run':run,'seal':seal,'check-source':check_source,'refuse-native-common':refuse_native_common}[args.operation](args.task,args.workspace)


if __name__=='__main__':raise SystemExit(main())
