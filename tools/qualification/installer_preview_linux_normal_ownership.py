#!/usr/bin/env python3
"""Owned Linux root-view discriminator, followed only by the original normal pair.

The first two cases execute no installer code. Their guard interpretation is a
source-bound predicate over actual ownership observations. Product guard results
come only from the optional unchanged original normal/NoOpen entries.
"""
import argparse, ast, hashlib, importlib.util, json, os, platform
from pathlib import Path
import re, secrets, shutil, signal, stat, subprocess, sys, tarfile, time

sys.dont_write_bytecode=True
INPUTS={
    'install.sh':'d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5',
    'tests/install-preview.py':'6be6f8109ce0e219b1bbc124aecde8c59190fffbb5c9e490d8beffa1ecce415e',
    'tests/install-entry-bash.py':'d46dfc53b61406d18883a08cd77a0788ed2b46131904329c7dded865e214b093',
    'tools/qualification/installer_preview_linux_namespace_successor.py':'8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328',
}
SUPPORT='tools/qualification/installer_preview_linux_namespace_successor.py'
SYSTEM_DIRS=('/usr','/bin','/sbin','/lib','/lib64','/etc')
SYSCALLS=('socket','socketpair','connect','sendto','sendmsg','sendmmsg')
CONTROL_SECONDS=30
NORMAL_SECONDS=60
CLEANUP_SECONDS=5
CAPTURE_BYTES=4*1024*1024
CANCELLED=False

CONTROL=r'''import ctypes, errno, hashlib, json, os, stat, subprocess, sys, time
from pathlib import Path
spec=json.loads(Path(sys.argv[1]).read_text());case=Path(spec['case'])
def save(path,value):
    temporary=path.with_name(path.name+'.partial');temporary.write_text(json.dumps(value,sort_keys=True)+'\n');temporary.replace(path)
def identity():
    return dict(pid=os.getpid(),ppid=os.getppid(),uid=os.getuid(),euid=os.geteuid(),gid=os.getgid(),egid=os.getegid(),groups=os.getgroups(),
        namespaceIds={n:os.readlink('/proc/self/ns/'+n) for n in ('user','net','mnt','pid')},
        status=Path('/proc/self/status').read_text(),uidMap=Path('/proc/self/uid_map').read_text(),gidMap=Path('/proc/self/gid_map').read_text())
def row(path):
    p=Path(path);s=p.lstat()
    return dict(path=str(p),physical=str(p.resolve()),uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),
        device=s.st_dev,inode=s.st_ino,kind='link' if stat.S_ISLNK(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else 'file')
def ancestors(path):
    p=Path(path);return [row(x) for x in [*reversed(p.parents),p]]
def write_probe(path,expected):
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        try:os.write(fd,b'owned containment discriminator\n')
        finally:os.close(fd)
    except OSError as error:return dict(path=path,expected=expected,succeeded=False,errno=error.errno)
    return dict(path=path,expected=expected,succeeded=True,errno=None)
result=dict(schema='r0016-linux-owned-root-control.v1',nonce=spec['nonce'],view=spec['view'],complete=False,installerExecuted=False)
try:
    before=identity();ready=dict(nonce=spec['nonce'],identity=before,phase='pre-effect-ready')
    save(case/'ready.json',ready)
    while not (case/'go.json').exists():
        if time.monotonic_ns()>=spec['deadlineMonotonicNs']:raise TimeoutError('Readiness release exceeded subject deadline')
        time.sleep(.01)
    if json.loads((case/'go.json').read_text())!={'nonce':spec['nonce']}:raise ValueError('Wrong readiness release')
    result.update(identity=identity(),ancestors={k:ancestors(v) for k,v in spec['parents'].items()},
        shellIdentity={k:os.environ.get(k) for k in ('USER','LOGNAME','SHELL')},mountinfo=Path('/proc/self/mountinfo').read_text())
    fds=[]
    for name in os.listdir('/proc/self/fd'):
        try:target=os.readlink('/proc/self/fd/'+name)
        except FileNotFoundError:continue
        fds.append(dict(fd=int(name),target=target))
    result['openFileDescriptors']=fds
    result['writes']=[write_probe(x['path'],x['expected']) for x in spec['writeProbes']]
    owned=case/'allowed-write.bin';owned.write_bytes(spec['nonce'].encode())
    result['ownedWrite']=dict(path=str(owned),bytes=owned.stat().st_size,sha256=hashlib.sha256(owned.read_bytes()).hexdigest())
    libc=ctypes.CDLL(None,use_errno=True);calls=[];pair=(ctypes.c_int*2)()
    arguments={'socket':(2,1,0),'socketpair':(1,1,0,ctypes.byref(pair)),
        'connect':(-1,None,0),'sendto':(-1,None,0,0,None,0),'sendmsg':(-1,None,0),'sendmmsg':(-1,None,0,0)}
    for name in ('socket','socketpair','connect','sendto','sendmsg','sendmmsg'):
        operation=getattr(libc,name);operation.restype=ctypes.c_ssize_t if name in ('sendto','sendmsg') else ctypes.c_int
        ctypes.set_errno(0);value=operation(*arguments[name]);code=ctypes.get_errno()
        calls.append(dict(syscall=name,returnValue=value,errno=code))
        if name=='socket' and value>=0:os.close(value)
        if name=='socketpair' and value==0:
            for descriptor in pair:os.close(descriptor)
    result['transports']=calls
    bash=subprocess.run(['/bin/bash','--noprofile','--norc','--version'],stdin=subprocess.DEVNULL,capture_output=True,timeout=5)
    result['bash']=dict(command=['/bin/bash','--noprofile','--norc','--version'],exit=bash.returncode,
        stdout=bash.stdout.decode('utf-8'),stderr=bash.stderr.decode('utf-8'))
    result['complete']=True
except BaseException as error:result['error']=dict(type=type(error).__name__,message=str(error))
result['finishedMonotonicNs']=time.monotonic_ns()
save(case/'control-result.json',result);print(json.dumps(result,sort_keys=True),flush=True)
raise SystemExit(0 if result['complete'] else 70)
'''

def require(value,reason):
    if not value:raise ValueError(reason)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def regular(path):
    path=Path(path).absolute()
    for p in [path,*path.parents]:require(not p.is_symlink(),'Link in owned input path')
    require(stat.S_ISREG(path.lstat().st_mode),'Regular input required')
    raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=sha(raw))

def save(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.partial')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)

def strict_json(raw):
    def pairs(items):
        value={}
        for k,v in items:require(k not in value,'Duplicate JSON key');value[k]=v
        return value
    def bad(value):raise ValueError('Nonfinite JSON number')
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs,parse_constant=bad)

def load_support(path):
    require(regular(path)['sha256']==INPUTS[SUPPORT],'Lifecycle support differs')
    spec=importlib.util.spec_from_file_location('r16_linux_owned_lifecycle',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def enforcement_fields(identity):
    rows=[line.split(':',1) for line in identity['status'].splitlines() if ':' in line]
    names=('NoNewPrivs','Seccomp','CapInh','CapPrm','CapEff','CapBnd','CapAmb')
    require(all(sum(k==name for k,v in rows)==1 for name in names),'Missing or duplicate bootstrap enforcement field')
    fields={k:v.strip() for k,v in rows if k in names}
    require(fields['NoNewPrivs']=='1' and fields['Seccomp'] in ('0','2'),'Bootstrap NNP/seccomp state differs')
    require(all(re.fullmatch('[0-9a-fA-F]{16}',fields[k]) for k in names[2:]),'Malformed bootstrap capability set')
    return fields

def verify_bootstrap_identity(identity,host,zero=False):
    require(all(type(identity.get(k)) is int and identity[k]==0 for k in ('uid','euid','gid','egid')),'Bootstrap is not mapped root')
    require(all(type(identity.get(k)) is int and identity[k]>0 for k in ('pid','ppid')),'Bootstrap PID identity is incomplete')
    for field,key in [('uidMap','uid'),('gidMap','gid')]:
        require(type(host[key]) is int and host[key]>0 and
            [[int(x) for x in line.split()] for line in identity[field].splitlines()]==[[0,host[key],1]],'Bootstrap exact one-ID map differs')
    require(set(identity['namespaceIds'])==set(host['namespaces'])=={'user','net','mnt','pid'} and
        all(identity['namespaceIds'][k]!=host['namespaces'][k] for k in host['namespaces']),'Bootstrap private namespace differs')
    fields=enforcement_fields(identity);caps={k:int(fields[k],16) for k in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb')}
    if zero:require(all(v==0 for v in caps.values()),'Bootstrap did not drop all five capability sets')
    else:require(caps['CapPrm']==caps['CapEff']==256 and caps['CapInh'] in (0,256) and caps['CapAmb'] in (0,256),'Bootstrap requires only namespace-local CAP_SETPCAP')
    return caps

def assess_bootstrap(value,spec,phase=None):
    require(value.get('schema')=='r0016-linux-capability-bootstrap.v1' and value.get('status')=='CAPABILITIES_DROPPED_EXEC_PENDING' and
        value.get('nonce')==spec['nonce'] and value.get('command')==spec['command'] and 'error' not in value,'Incomplete or replayed capability bootstrap')
    before=verify_bootstrap_identity(value['before'],spec['host']);verify_bootstrap_identity(value['after'],spec['host'],zero=True)
    stable=('pid','ppid','uid','euid','gid','egid','groups','namespaceIds','uidMap','gidMap')
    require(all(value['before'][k]==value['after'][k] for k in stable),'Bootstrap identity changed during capability drop')
    require(enforcement_fields(value['before'])['Seccomp']==enforcement_fields(value['after'])['Seccomp'],'Bootstrap changed inherited seccomp mode')
    reads=value['boundingRead'];drops=value['boundingDrop']
    require(10<=len(reads)<=65 and all(type(r.get(k)) is int for r in reads for k in ('cap','returnValue','errno')),'Incomplete bounding capability enumeration')
    last=len(reads)-2
    require(reads[-1]==dict(cap=last+1,returnValue=-1,errno=22) and
        all(r==dict(cap=n,returnValue=r['returnValue'],errno=0) and r['returnValue'] in (0,1) for n,r in enumerate(reads[:-1])),'Bounding enumeration is not complete and contiguous')
    require(sum(r['returnValue']<<r['cap'] for r in reads[:-1])==before['CapBnd'],'Bounding enumeration differs from actual status')
    require(all(type(r.get(k)) is int for r in drops for k in ('cap','returnValue','errno')) and
        drops==[dict(cap=n,returnValue=0,errno=0) for n in range(last+1)],'Not every supported bounding capability was dropped')
    for name in ('ambientClear','capsetZero'):
        require(all(type(value[name].get(k)) is int for k in ('returnValue','errno')) and value[name]==dict(returnValue=0,errno=0),'Ambient or capset drop failed')
    require(type(value.get('startedMonotonicNs')) is int and type(value.get('finishedMonotonicNs')) is int and
        0<value['startedMonotonicNs']<=value['finishedMonotonicNs'],'Unassociated bootstrap transition time')
    if phase is not None:
        require(all(type(phase.get(k)) is int for k in ('startedMonotonicNs','terminalObservedMonotonicNs')) and
            phase['startedMonotonicNs']<=value['startedMonotonicNs']<=value['finishedMonotonicNs']<=phase['terminalObservedMonotonicNs'],
            'Capability transition is outside the associated native process lifetime')
    return dict(status='ZERO_CAPABILITIES_BEFORE_HARNESS_EXEC',nativeExecProof='Separate terminal/readiness evidence required')

def perform_capability_drop(spec,backend,record):
    record.update(schema='r0016-linux-capability-bootstrap.v1',nonce=spec['nonce'],command=spec['command'],
        status='BOOTSTRAP_INCOMPLETE',startedMonotonicNs=backend.clock(),before=backend.read_identity(),boundingRead=[],boundingDrop=[])
    verify_bootstrap_identity(record['before'],spec['host'])
    for cap in range(65):
        result,code=backend.prctl(23,cap);record['boundingRead'].append(dict(cap=cap,returnValue=result,errno=code))
        if result==-1 and code==22:
            require(9<=cap<=64,'Unsupported bounding capability range');break
        require(cap<64 and result in (0,1) and code==0,'Bounding capability enumeration failed')
    else:raise ValueError('Bounding capability enumeration has no terminal EINVAL')
    require(sum(r['returnValue']<<r['cap'] for r in record['boundingRead'][:-1])==int(enforcement_fields(record['before'])['CapBnd'],16),'Bounding enumeration/status mismatch')
    for cap in range(len(record['boundingRead'])-1):
        result,code=backend.prctl(24,cap);record['boundingDrop'].append(dict(cap=cap,returnValue=result,errno=code))
        require(result==0 and code==0,'PR_CAPBSET_DROP failed')
    result,code=backend.prctl(47,4);record['ambientClear']=dict(returnValue=result,errno=code)
    require(result==0 and code==0,'PR_CAP_AMBIENT_CLEAR_ALL failed')
    result,code=backend.capset_zero();record['capsetZero']=dict(returnValue=result,errno=code)
    require(result==0 and code==0,'capset zero failed')
    record.update(after=backend.read_identity(),finishedMonotonicNs=backend.clock(),status='CAPABILITIES_DROPPED_EXEC_PENDING')
    assess_bootstrap(record,spec)

def run_capability_bootstrap(spec,backend,emit):
    record={};attempted=False
    try:
        perform_capability_drop(spec,backend,record)
        emit(record)  # This is a pre-exec observation, never proof that exec succeeded.
        attempted=True;backend.execute(spec['command'])
        raise RuntimeError('Bootstrap exec unexpectedly returned')
    except BaseException as error:
        record.update(status='BOOTSTRAP_REFUSED',dispatchAttempted=attempted,error=dict(type=type(error).__name__,message=str(error)))
        emit(record);return 70

def capability_bootstrap(path):
    # Only the controlled copied route starts with the temporary capability.
    # Isolated/no-site Python excludes writable user/site import customization.
    import ctypes
    from types import SimpleNamespace
    require(platform.system()=='Linux' and platform.machine()=='x86_64' and sys.executable=='/usr/bin/python3','Native x86_64 system Python bootstrap required')
    require(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode,'Isolated no-site bootstrap required')
    source=Path(__file__).resolve();inputs=source.parents[2];spec=strict_json(Path(path).read_bytes());case=Path(spec['case'])
    require(spec.get('schema')=='r0016-linux-capability-bootstrap-spec.v1' and re.fullmatch('[0-9a-f]{32}',spec['nonce']),'Wrong capability specification')
    require(case.parent==inputs.parent/'fixture' and case.name in ('host-root','owned-scaffold','normal','no-open') and
        Path(path)==inputs/(case.name+'.capability-spec.json'),'Wrong owned bootstrap boundary')
    require(spec['command'][:3]==['/usr/bin/python3',str(inputs/'tests/install-preview.py'),'--sandbox-child'],'Wrong original seccomp entry')
    require(regular(source)==spec['route'] and regular(inputs/'tests/install-preview.py')==spec['harness'],'Bootstrap input identity differs')
    libc=ctypes.CDLL(None,use_errno=True)
    libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong];libc.prctl.restype=ctypes.c_int
    libc.syscall.argtypes=[ctypes.c_long,ctypes.c_void_p,ctypes.c_void_p];libc.syscall.restype=ctypes.c_long
    class Header(ctypes.Structure):_fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
    class Data(ctypes.Structure):_fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
    def prctl(operation,argument):
        ctypes.set_errno(0);result=libc.prctl(operation,argument,0,0,0);return result,ctypes.get_errno()
    def capset_zero():
        header=Header(0x20080522,0);data=(Data*2)();ctypes.set_errno(0)
        result=libc.syscall(126,ctypes.byref(header),ctypes.byref(data));return result,ctypes.get_errno()
    def read_identity():
        return dict(pid=os.getpid(),ppid=os.getppid(),uid=os.getuid(),euid=os.geteuid(),gid=os.getgid(),egid=os.getegid(),groups=os.getgroups(),
            namespaceIds={n:os.readlink('/proc/self/ns/'+n) for n in ('user','net','mnt','pid')},
            status=Path('/proc/self/status').read_text(),uidMap=Path('/proc/self/uid_map').read_text(),gidMap=Path('/proc/self/gid_map').read_text())
    backend=SimpleNamespace(prctl=prctl,capset_zero=capset_zero,read_identity=read_identity,clock=time.monotonic_ns,
        execute=lambda command:os.execve(command[0],command,dict(os.environ)))
    return run_capability_bootstrap(spec,backend,lambda value:save(case/'capability-bootstrap.json',value))

def prepare_bootstrap(inputs,case,host,harness,command,fixed):
    specification=inputs/(case.name+'.capability-spec.json');require(not specification.exists(),'Bootstrap specification already exists')
    spec=dict(schema='r0016-linux-capability-bootstrap-spec.v1',nonce=secrets.token_hex(16),case=str(case),
        host={k:host[k] for k in ('uid','gid','namespaces')},command=['/usr/bin/python3',str(harness),'--sandbox-child']+list(command),
        route=regular(inputs/'tools/qualification/installer_preview_linux_normal_ownership.py'),harness=regular(harness))
    save(specification,spec);fixed.append(regular(specification));return spec

def cleanup_owned(N,process,deadline):
    """Reap natural direct-child zombies before unchanged forced cleanup."""
    reaped=[];errors=[]
    try:
        require(time.monotonic()<deadline,'Owned cleanup deadline reached before natural reap')
        process.poll()  # Only Popen may reap its own direct process.
        for pid in N.children(os.getpid()):
            if pid==process.pid:continue
            require(time.monotonic()<deadline,'Owned cleanup deadline reached during natural reap')
            identity=N.proc_identity(pid,full=False)
            require(identity['pid']==pid and identity['ppid']==os.getpid(),'Natural reap lacks direct-child ownership')
            if identity['state']!='Z':continue
            done,status=os.waitpid(pid,os.WNOHANG)
            require(type(done) is int and done==pid and type(status) is int,'Nonblocking natural reap did not return the exact child')
            reaped.append(dict(identity=identity,pid=done,waitStatus=status))
            require(os.WIFEXITED(status) and os.WEXITSTATUS(status)==0,'Adopted child did not exit naturally with status zero')
    except BaseException as error:errors.append(type(error).__name__+': '+str(error))
    try:record=N.cleanup(process,deadline)
    except BaseException as error:record=dict(complete=False,signals=[],errors=[type(error).__name__+': '+str(error)])
    record['preSignalReaps']=reaped;record.setdefault('errors',[]).extend(errors)
    record['complete']=record.get('complete') is True and not record['errors']
    return record

def path_row(path):
    p=Path(path);s=p.lstat()
    return dict(path=str(p),physical=str(p.resolve()),uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),
        device=s.st_dev,inode=s.st_ino,kind='link' if p.is_symlink() else 'directory' if p.is_dir() else 'file')

def interpret_trusted_parent(rows,uid,kind):
    """Exact ownership/mode decisions, not execution of the installer function."""
    require(type(uid) is int and kind in ('home','temp') and rows,'Invalid guard interpretation input')
    for row in rows:
        require(type(row.get('uid')) is int and type(row.get('mode')) is int and 0<=row['mode']<=0o7777,'Incomplete ownership facts')
        if row['kind']!='directory':return dict(accepted=False,reason='ancestor-type',path=row['path'])
        if row['uid'] not in (0,uid):return dict(accepted=False,reason='ancestor-owner',path=row['path'])
        if row['mode']&0o022 and not (row['uid']==0 and row['mode']&0o1000):return dict(accepted=False,reason='ancestor-writable',path=row['path'])
    last=rows[-1]
    if kind=='home' or last['uid']!=0 or not last['mode']&0o1000:
        if last['uid']!=uid or last['mode']&0o022:return dict(accepted=False,reason='private-parent',path=last['path'])
    if last['physical']!=last['path']:return dict(accepted=False,reason='physical-alias',path=last['path'])
    return dict(accepted=True,reason=None,path=last['path'])

def prepare_scaffold(scaffold,fixture,inputs,outside):
    require(not fixture.is_relative_to(scaffold) and not scaffold.is_relative_to(fixture),'Scaffold must be outside writable fixture')
    scaffold.mkdir(mode=0o700)
    for target in [*SYSTEM_DIRS,'/proc','/dev',str(fixture),str(inputs),str(outside)]:
        p=scaffold/Path(target).relative_to('/')
        p.mkdir(parents=True,exist_ok=True,mode=0o700)
    # Explicitly make every newly owned scaffold directory private; no existing
    # host ancestor is changed. No target-side directory creation is necessary.
    for p in [scaffold,*scaffold.rglob('*')]:
        require(p.is_dir() and not p.is_symlink(),'Scaffold contains an unexpected entry');p.chmod(0o700)
    (scaffold/'r0016-readonly-sentinel').write_bytes(b'owned read-only guest-root sentinel\n')
    (scaffold/'r0016-readonly-sentinel').chmod(0o600)

def build_command(view,fixture,scaffold,inputs,outside,case,env,harness,command):
    require(view in ('host-root','owned-scaffold'),'Unknown root-view selector')
    require(all(p.is_absolute() for p in (fixture,scaffold,inputs,outside,case,harness)) and case.is_relative_to(fixture) and case!=fixture,'Owned absolute child fixture required')
    require(harness==inputs/'tests/install-preview.py','Exact copied seccomp harness required')
    require(not scaffold.is_relative_to(fixture) and not inputs.is_relative_to(fixture) and not outside.is_relative_to(fixture),'Read-only input is inside writable fixture')
    prefix=['/usr/bin/unshare','--user','--map-root-user','--net','/usr/bin/bwrap',
        '--die-with-parent','--unshare-pid','--cap-drop','ALL','--cap-add','CAP_SETPCAP']
    if view=='host-root':mounts=['--ro-bind','/','/']
    else:
        mounts=['--ro-bind',str(scaffold),'/']
        for path in SYSTEM_DIRS:mounts+=['--ro-bind',path,path]
        for path in (inputs,outside):mounts+=['--ro-bind',str(path),str(path)]
    mounts+=['--bind',str(fixture),str(fixture),'--proc','/proc','--dev','/dev','--chdir',str(case),'--clearenv']
    for k,v in sorted(env.items()):mounts+=['--setenv',k,v]
    return prefix+mounts+['/usr/bin/python3','-I','-S','-B',
        str(inputs/'tools/qualification/installer_preview_linux_normal_ownership.py'),'--capability-bootstrap',
        str(inputs/(case.name+'.capability-spec.json'))]

def common_environment(case):
    for p in (case/'home',case/'tmp'):p.mkdir(mode=0o700)
    return dict(PATH='/usr/bin:/bin',LANG='C.UTF-8',HOME=str(case/'home'),TMPDIR=str(case/'tmp'),
        USER='root',LOGNAME='root',SHELL='/bin/bash',SALAH_TEST_BASH='/bin/bash',PYTHONDONTWRITEBYTECODE='1',
        R0016_TRANSPORT_LOG=str(case/'network.jsonl'))

def descendants(N,pid):
    pending=N.children(pid);rows=[];seen=set()
    while pending:
        child=pending.pop();require(child not in seen,'Repeated owned process identity');seen.add(child)
        require(len(seen)<=128,'Owned process census bound exceeded')
        try:row=N.proc_identity(child);pending.extend(N.children(child))
        except FileNotFoundError:continue
        rows.append(row)
    return rows

def observe_ready(N,path,nonce,process,expected_child):
    ready=strict_json(path.read_bytes());identity=ready.get('identity',{})
    require(ready.get('nonce')==nonce and ready.get('phase')=='pre-effect-ready' and type(identity.get('pid')) is int,'Wrong readiness identity')
    rows=descendants(N,os.getpid());matches=[]
    for row in rows:
        fields=N.status_fields(row);nspid=fields.get('NSpid','').split()
        argv=row['commandLine'].get('text','').rstrip('\x00').split('\x00')
        if row['namespaceIds']==identity['namespaceIds'] and nspid and int(nspid[-1])==identity['pid'] and argv==expected_child:matches.append(row)
    require(len(matches)==1,'Readiness lacks one exact host-PID/namespace/argv association')
    indexed={r['pid']:r for r in rows};cursor=matches[0];chain=[]
    while cursor['pid']!=process.pid:
        chain.append(cursor);require(cursor['ppid'] in indexed,'Ready process is outside launched ancestry');cursor=indexed[cursor['ppid']]
    chain.append(cursor)
    return dict(subject=ready,hostPid=matches[0]['pid'],parentReadAncestry=chain)

def run_phase(N,command,env,case,capture,fixture,seconds,expected_child=None,nonce=None):
    capture.mkdir(mode=0o700);require(not N.children(os.getpid()),'Prior owned descendants remain')
    before=N.inventory(fixture);save(capture/'fixture.before.json',before);require(before['complete'],'Incomplete prelaunch fixture inventory')
    start_ns=time.monotonic_ns();deadline_ns=start_ns+seconds*10**9;start=start_ns/1e9;deadline=deadline_ns/1e9
    record=dict(command=command,environment=env,cwd=str(case),timeoutSeconds=seconds,returncode=None,
        executionOutcome='NOT_LAUNCHED',startNewSession=True,stdin='DEVNULL',capture='direct files',
        startedMonotonicNs=start_ns,deadlineMonotonicNs=deadline_ns)
    record['bootstrapSpecification']=regular(Path(command[-1]))
    save(capture/'launch.json',record);process=None
    with (capture/'stdout.raw').open('xb',buffering=0) as stdout,(capture/'stderr.raw').open('xb',buffering=0) as stderr:
        try:
            process=subprocess.Popen(command,env=env,cwd=case,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                start_new_session=True,close_fds=True)
            record.update(launchPid=process.pid,executionOutcome='RUNNING')
            while process.poll() is None:
                if expected_child and (case/'ready.json').exists() and 'readiness' not in record:
                    record['readiness']=observe_ready(N,case/'ready.json',nonce,process,expected_child)
                    save(capture/'readiness.json',record['readiness']);save(case/'go.json',dict(nonce=nonce))
                require(max(os.fstat(stdout.fileno()).st_size,os.fstat(stderr.fileno()).st_size)<=CAPTURE_BYTES,'Capture bound exceeded')
                if time.monotonic_ns()>=deadline_ns:record['executionOutcome']='TIMEOUT';break
                time.sleep(.01)
            if process.returncode is not None:
                now_ns=time.monotonic_ns();record.update(terminalObservedMonotonicNs=now_ns,executionOutcome='TERMINAL_EXIT' if now_ns<=deadline_ns else 'LATE_TERMINAL_EXIT')
        except BaseException as error:record.update(error=dict(type=type(error).__name__,message=str(error)),executionOutcome='CONTROLLER_ERROR')
        finally:
            if process is not None:
                try:record['cleanup']=cleanup_owned(N,process,min(time.monotonic()+CLEANUP_SECONDS,deadline+CLEANUP_SECONDS))
                except BaseException as error:record['cleanup']=dict(complete=False,signals=[],errors=[type(error).__name__+': '+str(error)])
                record['returncode']=process.returncode
            else:record['cleanup']=dict(complete=not N.children(os.getpid()),signals=[],notLaunched=True)
    record['elapsedSeconds']=time.monotonic()-start
    try:record['capabilityBootstrap']=strict_json((case/'capability-bootstrap.json').read_bytes())
    except BaseException as error:record['bootstrapObservationError']=dict(type=type(error).__name__,message=str(error))
    record['captures']={name:regular(capture/(name+'.raw')) for name in ('stdout','stderr')}
    after=N.inventory(fixture) if record['cleanup']['complete'] else dict(complete=False,reason='Owned termination unconfirmed')
    save(capture/'fixture.after.json',after);record['fixtureObservationComplete']=before['complete'] and after['complete']
    save(capture/'result.json',record)
    if CANCELLED:raise InterruptedError('Owned phase interrupted; raw capture and cleanup result retained')
    return record

def check_terminal(record,command,seconds):
    require(record.get('command')==command and type(record.get('returncode')) is int and record['returncode']==0,'Wrong command or integer terminal')
    require(record.get('executionOutcome')=='TERMINAL_EXIT' and 'error' not in record and type(record.get('timeoutSeconds')) is int and record['timeoutSeconds']==seconds,'Incomplete or late terminal')
    require(all(type(record.get(k)) is int for k in ('startedMonotonicNs','deadlineMonotonicNs','terminalObservedMonotonicNs')) and
        record['deadlineMonotonicNs']-record['startedMonotonicNs']==seconds*10**9 and
        record['startedMonotonicNs']<=record['terminalObservedMonotonicNs']<=record['deadlineMonotonicNs'],'Terminal time is not associated with the bounded launch')
    require(record.get('cleanup',{}).get('complete') is True and not record['cleanup'].get('signals') and not record['cleanup'].get('errors'),'Natural owned cleanup was not established')
    require(record['cleanup'].get('remainingDirectChildren')==[] and type(record['cleanup'].get('directExit')) is int and record['cleanup']['directExit']==record['returncode'],'Cleanup contradicts the associated terminal')
    require(record.get('fixtureObservationComplete') is True and record.get('capture')=='direct files','Incomplete full observation/capture')
    require(set(record['captures'])=={'stdout','stderr'} and all(type(v['bytes']) is int and 0<=v['bytes']<=CAPTURE_BYTES for v in record['captures'].values()),'Incomplete or oversized capture')

def assess_control(value,record,spec,host,transport):
    require(value.get('schema')=='r0016-linux-owned-root-control.v1' and value.get('nonce')==spec['nonce'] and value.get('view')==spec['view'] and value.get('complete') is True and value.get('installerExecuted') is False,'Incomplete or replayed control')
    child=value['identity'];ready=record['readiness']['subject']['identity']
    stable=('pid','ppid','uid','euid','gid','egid','groups','namespaceIds','uidMap','gidMap')
    require(all(child.get(k)==ready.get(k) for k in stable),'Control identity changed after held readiness')
    # Complete status text is retained at both phases. Memory/counter fields
    # naturally change; identity and enforcement fields are checked explicitly.
    require(all(type(child[k]) is int and child[k]==0 for k in ('uid','euid','gid','egid')),'Expected mapped root identity absent')
    for field,expected in [('uidMap',host['uid']),('gidMap',host['gid'])]:
        require([[int(x) for x in line.split()] for line in child[field].splitlines()]==[[0,expected,1]],'Wrong exact one-ID namespace map')
    require(all(child['namespaceIds'][k]!=host['namespaces'][k] for k in ('user','net','mnt','pid')),'Required private namespace missing')
    for identity in (ready,child):
        status_rows=[line.split(':',1) for line in identity['status'].splitlines() if ':' in line]
        status=dict(status_rows)
        capability_fields=('CapInh','CapPrm','CapEff','CapBnd','CapAmb')
        require(all(sum(key==field for key,value in status_rows)==1 for field in ('NoNewPrivs','Seccomp')+capability_fields),'Missing or duplicate enforcement status field')
        require(status['NoNewPrivs'].strip()=='1' and status['Seccomp'].strip()=='2','NNP/seccomp readback failed')
        require(all(re.fullmatch(r'[0-9a-fA-F]{16}',status[field].strip()) and int(status[field].strip(),16)==0 for field in capability_fields),'All five capability sets must be well-formed and zero')
    require(value['shellIdentity']==dict(USER='root',LOGNAME='root',SHELL='/bin/bash'),'Known native shell identity changed')
    require(len(value['openFileDescriptors'])==3 and all(type(r['fd']) is int for r in value['openFileDescriptors']) and {r['fd'] for r in value['openFileDescriptors']}=={0,1,2},'Incomplete or unexpected inherited file descriptors')
    mounts=[]
    for line in value['mountinfo'].splitlines():
        fields=line.split();require(len(fields)>=10,'Malformed mountinfo')
        point=re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),fields[4]);mounts.append((point,fields[5].split(',')))
    require(any(p=='/' and 'ro' in opts for p,opts in mounts),'Guest root is not read-only')
    require(any(p==spec['fixture'] and 'rw' in opts for p,opts in mounts),'Original fixture is not the writable bind')
    require(all('rw' not in opts or p==spec['fixture'] or p=='/proc' or p.startswith('/proc/') or p=='/dev' or p.startswith('/dev/') for p,opts in mounts),'Unexpected writable filesystem mount')
    require(len(value['writes'])==len(spec['writeProbes']),'Incomplete write controls')
    for actual,expected in zip(value['writes'],spec['writeProbes']):
        require(actual['path']==expected['path'] and actual['expected']==expected['expected'] and actual['succeeded'] is False,'Read-only control wrote or changed identity')
        errors={'EROFS':(30,),'ENOENT':(2,),'PROC_ALIAS_DENIED':(1,2,13,30)}
        require(type(actual['errno']) is int and actual['errno'] in errors[expected['expected']],'Wrong read-only/absent-alias errno')
    require(value['ownedWrite']==dict(path=str(Path(spec['case'])/'allowed-write.bin'),bytes=len(spec['nonce']),sha256=sha(spec['nonce'].encode())),'Writable fixture control failed')
    require(all(type(r['returnValue']) is int and type(r['errno']) is int for r in value['transports']) and value['transports']==[dict(syscall=n,returnValue=-1,errno=1) for n in SYSCALLS],'All six explicit transport syscalls must return EPERM')
    require(all(type(r['pid']) is int for r in transport) and transport==[dict(pid=child['pid'],syscall=n,decision='DENIED_EPERM') for n in SYSCALLS],'Missing/extra/unattributed raw seccomp records')
    require(value['bash']['command']==['/bin/bash','--noprofile','--norc','--version'] and type(value['bash']['exit']) is int and value['bash']['exit']==0 and not value['bash']['stderr'] and value['bash']['stdout'].startswith('GNU bash, version '),'Native Bash startup was not healthy')
    interpretations={}
    for kind,path in spec['parents'].items():
        expected_paths=[str(x) for x in [*reversed(Path(path).parents),Path(path)]]
        rows=value['ancestors'][kind];require([r['path'] for r in rows]==expected_paths,'Ancestor chain incomplete or reordered')
        interpretations[kind]=interpret_trusted_parent(rows,child['euid'],kind)
    if spec['view']=='host-root':
        require(all(v==dict(accepted=False,reason='ancestor-owner',path='/') for v in interpretations.values()),'Original root-owner failure was not reproduced by actual facts')
    else:require(all(v['accepted'] for v in interpretations.values()),'Owned scaffold does not satisfy the unchanged ownership/mode predicate')
    return dict(status='OBSERVED',guardPredicate=interpretations,guardExecution='NOT_EXECUTED; source-bound interpretation only',installerExecuted=False)

def controller(args):
    require(platform.system()=='Linux' and platform.machine()=='x86_64' and os.getuid()!=0 and os.geteuid()==os.getuid(),'Unprivileged native Linux x86_64 required')
    require(sys.executable=='/usr/bin/python3','Run the pinned system Python entry')
    source=Path(__file__).resolve();repo=source.parents[2];output=args.output.absolute()
    require(output.parent.is_dir() and output.parent.resolve()==output.parent and not output.exists() and not output.is_symlink() and not output.is_relative_to(repo),'Fresh canonical external output required')
    output.mkdir(mode=0o700);fixture=output/'fixture';fixture.mkdir(mode=0o700)
    inputs=output/'inputs';inputs.mkdir(mode=0o700);outside=output/'outside';outside.mkdir(mode=0o700)
    (outside/'sentinel').write_bytes(b'owned outside sentinel\n');scaffold=output/'scaffold'
    result=dict(schema='r0016-linux-normal-ownership.v1',status='INCOMPLETE',normalHarnessInvocationsAttempted=0,normalRowsQualified=0,sourceCommit=args.source_commit,
        fixture=str(fixture),scaffold=str(scaffold),sourceFreeControls=[],normalResults=[],publicationAuthority=False)
    save(output/'result.json',result);fixed=[];N=None;host=None
    try:
        identity_command=['/usr/bin/git','-C',str(repo),'rev-parse','--verify','HEAD']
        identity=subprocess.run(identity_command,stdin=subprocess.DEVNULL,capture_output=True,timeout=5,
            env=dict(PATH='/usr/bin:/bin',LANG='C.UTF-8',HOME=str(output)))
        result['checkoutIdentity']=dict(command=identity_command,exit=identity.returncode,
            stdout=identity.stdout.decode('utf-8'),stderr=identity.stderr.decode('utf-8'))
        require(identity.returncode==0 and identity.stdout.decode('ascii').strip()==args.source_commit and not identity.stderr,'Checkout commit differs from the requested exact source')
        roles=dict(INPUTS);roles['tools/qualification/installer_preview_linux_normal_ownership.py']=regular(source)['sha256']
        for role,digest in roles.items():
            original=regular(repo/role);require(original['sha256']==digest,'Pinned role differs: '+role)
            target=inputs/role;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/role,target)
            copied=regular(target);require(copied['sha256']==digest and copied['bytes']==original['bytes'],'Copied input differs')
            fixed.extend([original,copied])
        control=inputs/'ownership-control.py';control.write_text(CONTROL);fixed.append(regular(control))
        N=load_support(inputs/SUPPORT);result['subreaper']=N.enable_subreaper()
        host=dict(uid=os.getuid(),gid=os.getgid(),euid=os.geteuid(),groups=os.getgroups(),kernel=platform.release(),
            namespaces={n:os.readlink('/proc/self/ns/'+n) for n in ('user','net','mnt','pid')},root=path_row('/'),
            namespacePolicy={p:N.fact(Path(p)) for p in N.POLICY_FILES},executables={p:N.binding(Path(p)) for p in ['/usr/bin/unshare','/usr/bin/bwrap','/usr/bin/python3','/bin/bash','/usr/bin/git']})
        require(host['root']['uid']==0,'Host root ownership premise differs');result['host']=host
        prepare_scaffold(scaffold,fixture,inputs,outside)
        for root,name in [(scaffold,'scaffold'),(outside,'outside')]:
            before=N.inventory(root);require(before['complete'],'Incomplete read-only control inventory');save(output/(name+'.before.json'),before)
        save(output/'input-bindings.json',fixed)
        scaffold_before=N.inventory(scaffold);outside_before=N.inventory(outside)
        for view in ('host-root','owned-scaffold'):
            case=fixture/view;case.mkdir(mode=0o700);env=common_environment(case);nonce=secrets.token_hex(16)
            sentinel=str(scaffold/'r0016-readonly-sentinel') if view=='host-root' else '/r0016-readonly-sentinel'
            probes=[dict(path=sentinel,expected='EROFS'),dict(path=str(outside/'sentinel'),expected='EROFS'),
                dict(path='/proc/self/root'+sentinel,expected='EROFS')]
            if view=='owned-scaffold':
                probes.extend([dict(path='/proc/1/root/r0016-readonly-sentinel',expected='PROC_ALIAS_DENIED'),
                    dict(path='/proc/1/root'+str(outside/'sentinel'),expected='PROC_ALIAS_DENIED'),
                    dict(path='/proc/1/root'+str(scaffold/'r0016-readonly-sentinel'),expected='PROC_ALIAS_DENIED'),
                    dict(path=str(scaffold/'r0016-readonly-sentinel'),expected='ENOENT'),
                    dict(path='/proc/'+str(os.getpid())+'/root/r0016-readonly-sentinel',expected='ENOENT')])
            spec=dict(view=view,nonce=nonce,case=str(case),fixture=str(fixture),parents=dict(home=env['HOME'],temp=env['TMPDIR']),
                writeProbes=probes,deadlineMonotonicNs=time.monotonic_ns()+CONTROL_SECONDS*10**9)
            specification=inputs/(view+'-spec.json');save(specification,spec);fixed.append(regular(specification))
            child=['/usr/bin/python3',str(control),str(specification)]
            bootstrap_spec=prepare_bootstrap(inputs,case,host,inputs/'tests/install-preview.py',child,fixed)
            command=build_command(view,fixture,scaffold,inputs,outside,case,env,inputs/'tests/install-preview.py',child)
            record=run_phase(N,command,env,case,output/(view+'-capture'),fixture,CONTROL_SECONDS,child,nonce)
            check_terminal(record,command,CONTROL_SECONDS)
            record['capabilityAssessment']=assess_bootstrap(record['capabilityBootstrap'],bootstrap_spec,record)
            bootstrap_identity=record['capabilityBootstrap']['after'];ready_identity=record['readiness']['subject']['identity']
            require(ready_identity['ppid']==bootstrap_identity['pid'] and ready_identity['namespaceIds']==bootstrap_identity['namespaceIds'],
                'Held control is not the capability-dropped original harness child')
            value=strict_json((case/'control-result.json').read_bytes())
            require(strict_json((output/(view+'-capture/stdout.raw')).read_bytes())==value and not (output/(view+'-capture/stderr.raw')).read_bytes(),'Raw control capture differs')
            transport=[strict_json(line) for line in (case/'network.jsonl').read_bytes().splitlines()]
            assessment=assess_control(value,record,spec,host,transport)
            require(N.inventory(scaffold)==scaffold_before and N.inventory(outside)==outside_before,'Read-only scaffold/outside state changed')
            result['sourceFreeControls'].append(dict(view=view,spec=regular(specification),record=record,control=value,assessment=assessment))
            save(output/'result.json',result)
        result['status']='OWNERSHIP_AND_CONTAINMENT_DISCRIMINATOR_OBSERVED'
        if args.run_normal_pair:
            harness=inputs/'tests/install-preview.py';tree=ast.parse(harness.read_bytes())
            names={'digest','require','fixture','normal','transport_attempts'}
            nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
            require({n.name for n in nodes}==names and len(nodes)==len(names),'Original normal interface drift')
            denials=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DENIALS' for t in n.targets)]
            require(len(denials)==1,'Original fixture bootstrap literal differs')
            namespace=dict(__file__=str(harness),ROOT=fixture,FROZEN=inputs/'install.sh',HARNESS=inputs/'tests/install-entry-bash.py',
                HOST='Linux',ARGS=argparse.Namespace(bash='/bin/bash'),DENIALS=denials[0],pathlib=__import__('pathlib'),hashlib=hashlib,
                sys=sys,json=json,secrets=secrets)
            def sandbox_run(command,case,env,timeout):
                require(case.name in ('normal','no-open') and timeout==NORMAL_SECONDS,'Only original two normal cases admitted')
                expected=[sys.executable,str(harness),'--positive-child',str(inputs/'install.sh'),str(inputs/'tests/install-entry-bash.py'),'1' if case.name=='no-open' else '0']
                require(command==expected and 'BASH_ENV' not in env and all(env[k]==v for k,v in [('USER','root'),('LOGNAME','root'),('SHELL','/bin/bash')]),'Original normal invocation or startup environment differs')
                bootstrap_spec=prepare_bootstrap(inputs,case,host,harness,command,fixed)
                launch=build_command('owned-scaffold',fixture,scaffold,inputs,outside,case,env,harness,command)
                result['normalHarnessInvocationsAttempted']+=1;save(output/'result.json',result)
                capture=output/(case.name+'-capture');record=run_phase(N,launch,env,case,capture,fixture,timeout)
                result.setdefault('normalAcquisitions',[]).append(record);save(output/'result.json',result)
                rawout=(capture/'stdout.raw').read_bytes();rawerr=(capture/'stderr.raw').read_bytes()
                (case/'stdout.txt').write_bytes(rawout);(case/'stderr.txt').write_bytes(rawerr)
                check_terminal(record,launch,timeout)
                record['capabilityAssessment']=assess_bootstrap(record['capabilityBootstrap'],bootstrap_spec,record)
                return subprocess.CompletedProcess(command,record['returncode'],rawout.decode('utf-8'),rawerr.decode('utf-8'))
            namespace['sandbox_run']=sandbox_run
            exec(compile(ast.Module(body=nodes,type_ignores=[]),str(harness),'exec'),namespace)
            for name,no_open in [('normal',False),('no-open',True)]:
                try:
                    observation=namespace['normal'](name,no_open=no_open);row=dict(case=name,pass_=True,observation=observation)
                    result['normalRowsQualified']+=1
                except InterruptedError:raise
                except Exception as error:row=dict(case=name,pass_=False,error=type(error).__name__+': '+str(error))
                result['normalResults'].append(row);save(output/'result.json',result)
            result['status']='ORIGINAL_NORMAL_PAIR_PASSED' if len(result['normalResults'])==2 and all(r['pass_'] for r in result['normalResults']) else 'ORIGINAL_NORMAL_PAIR_FAILED'
        require(N.inventory(scaffold)==scaffold_before and N.inventory(outside)==outside_before,'Read-only state changed during original pair')
    except BaseException as error:result.update(status='ACQUISITION_OR_ASSERTION_FAILED',error=dict(type=type(error).__name__,message=str(error)))
    finally:
        custody=[]
        for item in fixed:
            try:require(regular(item['path'])==item,'Input custody changed')
            except BaseException as error:custody.append(str(error))
        result['inputCustodyErrors']=custody
        if custody:result['status']='INPUT_CUSTODY_FAILED'
        if N:
            observation_errors=[]
            if host:
                try:
                    result['hostExecutablesAfter']={p:N.binding(Path(p)) for p in host['executables']}
                    if result['hostExecutablesAfter']!=host['executables']:observation_errors.append('Native executable identities changed')
                except BaseException as error:observation_errors.append(type(error).__name__+': '+str(error))
            for root,name in [(fixture,'fixture'),(scaffold,'scaffold'),(outside,'outside')]:
                if root.exists():
                    observation=N.inventory(root);save(output/(name+'.final.json'),observation)
                    if not observation['complete']:observation_errors.append(name+': final full observation incomplete')
            result['finalObservationErrors']=observation_errors
            if observation_errors:result['status']='FINAL_OBSERVATION_FAILED'
        save(output/'result.json',result)
    print(json.dumps(result,indent=2));return 0 if result['status'] in ('OWNERSHIP_AND_CONTAINMENT_DISCRIMINATOR_OBSERVED','ORIGINAL_NORMAL_PAIR_PASSED') else 2

def archive(output,destination):
    require(output.is_absolute() and output.is_dir() and not output.is_symlink() and destination.parent==output.parent and not destination.exists(),'Invalid exclusive archive boundary')
    with tarfile.open(destination,'x:gz',dereference=False) as stream:
        pending=[output]
        while pending:
            path=pending.pop();info=path.lstat();name='installer-evidence'+('' if path==output else '/'+path.relative_to(output).as_posix())
            require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode),'Unsupported archive entry')
            stream.add(path,arcname=name,recursive=False)
            if stat.S_ISDIR(info.st_mode):pending.extend(sorted(path.iterdir(),reverse=True))

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--capability-bootstrap':return capability_bootstrap(Path(sys.argv[2]))
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--source-commit');parser.add_argument('--run-normal-pair',action='store_true');parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if args.archive:
        require(not args.run_normal_pair and args.source_commit is None,'Archive is a separate action');archive(args.output.absolute(),args.archive.absolute());return 0
    require(isinstance(args.source_commit,str) and re.fullmatch('[0-9a-f]{40}',args.source_commit),'Exact source commit required')
    def interrupted(signum,frame):
        global CANCELLED
        CANCELLED=True
        raise InterruptedError('Owned controller received signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    return controller(args)

if __name__=='__main__':raise SystemExit(main())
