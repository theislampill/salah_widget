#!/usr/bin/env python3
"""Private transport caller; producer custody is not native/product acceptance.

Ordinary returned observation is admitted only after its complete terminal
namespace records. Forced/unknown outer termination refuses sealing. This is
not generic descendant containment or an atomic freeze against another writer.
Sender/run/artifact authentication remains mandatory before offline opening.
"""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import types

HERE = Path(__file__).absolute().parent
PRODUCER_PROTOCOL = 'salah-capture-producer-return/1'
TRANSPORT_SHA256 = '6815cfdb68bea413a740d58e2ddf8e9d4c1185d65638274e8108e37637f3dbfe'
PUBLIC_ERRORS = {'ARGUMENT', 'DEPENDENCY', 'PRODUCER_INCOMPLETE', 'PATH',
                 'STAGING', 'ENVELOPE', 'RESTORATION', 'CLEANUP', 'INTERRUPTED', 'INTERNAL'}


class Rejected(Exception):
    pass


def need(value, category):
    if not value: raise Rejected(category)


def transport():
    path = HERE/'capture_transport.py'
    need(all(not p.is_symlink() for p in [path, *path.parents]), 'DEPENDENCY')
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == TRANSPORT_SHA256, 'DEPENDENCY')
    module = types.ModuleType('private_capture_transport')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def load(path, limit=8 << 20):
    T = transport(); E = T.envelope()
    return E.load_json(E.read_bounded(E.no_symlink_path(path), limit))


def safe_path(path, E):
    try:return E.no_symlink_path(path)
    except Exception:raise Rejected('PATH') from None


def roots_checked(task, roots):
    T = transport(); E = T.envelope()
    need(type(roots) is dict and set(roots) == {'research','baseline','historical'}, 'ARGUMENT')
    task = safe_path(task,E)
    protected = [safe_path(p,E) for p in roots.values()]
    protected.append(safe_path(HERE.parents[2],E))
    need(task.is_dir() and (task/'capture').is_dir(), 'PRODUCER_INCOMPLETE')
    need(stat.S_IMODE(task.stat().st_mode) == 0o700
         and stat.S_IMODE((task/'capture').stat().st_mode) == 0o700, 'PATH')
    need(all(p.is_dir() for p in protected), 'PATH')
    need(all(not task.is_relative_to(p) and not p.is_relative_to(task) for p in protected), 'PATH')
    # These are actual acquisition/build locations, not paths supplied by capture metadata.
    protected += [safe_path(task/name,E) for name in
                  ('work','runtime','node','python','node-browsers','python-browsers','cache','config','temporary')]
    return task, protected


def producer_identity(phase, task, roots):
    need(phase in ('acquisition','observation'), 'ARGUMENT')
    task = Path(task).absolute()
    paths = {k:Path(v).absolute() for k,v in roots.items()}
    need(set(paths) == {'research','baseline','historical'}, 'ARGUMENT')
    if phase == 'acquisition':
        command = [shutil.which('bash'), str(HERE/'acquire.sh'), str(task),
                   *[str(paths[k]) for k in ('research','baseline','historical')]]
        files = ['capture_pipeline.py','acquire.sh','campaign.json']
    else:
        command = [sys.executable, str(HERE/'observe.py'), '--task', str(task)]
        for key in ('research','baseline','historical'): command += ['--'+key,str(paths[key])]
        command += ['--campaign',str(HERE/'campaign.json')]
        files = ['capture_pipeline.py','observe.py','campaign.json']
    need(all(isinstance(x,str) and x for x in command), 'DEPENDENCY')
    return {'argv':command, 'sources':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in files}}


def write_exclusive(path, body):
    data=(json.dumps(body,sort_keys=True,indent=2)+'\n').encode()
    fd=os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as stream:
            stream.write(data);stream.flush();os.fsync(fd)
    finally:os.close(fd)


def run_command(identity, task, phase):
    """Record the actual waited child. Never infer that an interrupted tree drained."""
    capture=Path(task)/'capture'; control=capture/'producer-control'
    if phase=='acquisition': control.mkdir(mode=0o700)
    need(control.is_dir() and not control.is_symlink(), 'PATH')
    started={'protocol':PRODUCER_PROTOCOL,'phase':phase,'identity':identity}
    write_exclusive(control/(phase+'-started.json'),started)
    began=time.monotonic();proc=None;interrupted=False;returned=False
    try:
        with (capture/(phase+'.stdout')).open('xb') as out, (capture/(phase+'.stderr')).open('xb') as err:
            proc=subprocess.Popen(identity['argv'],stdout=out,stderr=err)
            try:
                proc.wait();returned=True
            except BaseException:
                interrupted=True
                # The original observer receives TERM and performs its existing cleanup.
                # Even if it returns, this wrapper marks the entire outer interruption
                # inadmissible for seal. No PGID scan invents escaped-child custody.
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill();proc.wait()
                returned=True
    finally:
        write_exclusive(control/(phase+'-completed.json'),
                        {**started,'returned':returned,'interrupted':interrupted,
                         'process':{'returncode':None if proc is None else proc.returncode,
                                    'elapsedSeconds':time.monotonic()-began}})
    need(returned and not interrupted, 'PRODUCER_INCOMPLETE')
    return proc.returncode


def known_process(value, timeout_field=True):
    return (type(value) is dict and type(value.get('returncode')) is int
            and (not timeout_field or type(value.get('timedOut')) is bool)
            and type(value.get('elapsedSeconds')) in (int,float)
            and math.isfinite(value['elapsedSeconds']) and value['elapsedSeconds'] >= 0)


def completed(task, roots, phase):
    control=task/'capture/producer-control'
    start=load(control/(phase+'-started.json'))
    end=load(control/(phase+'-completed.json'))
    wanted={'protocol':PRODUCER_PROTOCOL,'phase':phase,'identity':producer_identity(phase,task,roots)}
    need(start==wanted and type(end) is dict and set(end)==set(wanted)|{'returned','interrupted','process'}
         and all(end[k]==v for k,v in wanted.items()) and end['returned'] is True
         and end['interrupted'] is False and known_process(end['process'],False), 'PRODUCER_INCOMPLETE')
    return end['process']['returncode']


def admit_producers(task, roots):
    """Only return of the complete known synchronous source path permits seal."""
    try:
        code=completed(task,roots,'acquisition')
        need(0 <= code < 126,'PRODUCER_INCOMPLETE')
        capture=task/'capture'
        if code:
            need(not any((capture/'producer-control').glob('observation-*'))
                 and not (capture/'observation.json').exists(), 'PRODUCER_INCOMPLETE')
            return 'ACQUISITION_ONLY'
        code=completed(task,roots,'observation')
        need(code in (0,2) and not (capture/'coordinator-error-outer.json').exists(), 'PRODUCER_INCOMPLETE')
        body=load(capture/'observation.json')
        need(type(body) is dict and body.get('protocol')=='salah-hosted-native-observation/1'
             and known_process(body.get('preparation')) and type(body.get('lanes')) is list,
             'PRODUCER_INCOMPLETE')
        prep=body['preparation']
        if prep['returncode'] or prep['timedOut']:
            need(code==2 and body['lanes']==[] and body.get('status') in ('INCOMPLETE','ISOLATION_FAIL'),
                 'PRODUCER_INCOMPLETE')
            return 'COMPLETED_PREPARATION_FAILURE'
        need(body.get('status') in ('OBSERVED','OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES',
                                   'ISOLATION_FAIL','ISOLATION_UNCONFIRMED','EXTERNAL_CONTINUATION_VETOED')
             and (code==0)==(body['status']=='OBSERVED'), 'PRODUCER_INCOMPLETE')
        plan=load(capture/'lanes.json')
        need(type(plan) is dict and type(plan.get('lanes')) is list and plan['lanes'], 'PRODUCER_INCOMPLETE')
        ids=[x.get('id') if type(x) is dict else None for x in plan['lanes']]
        need(all(type(x) is str and x for x in ids) and len(set(ids))==len(ids)
             and [x.get('id') if type(x) is dict else None for x in body['lanes']]==ids,
             'PRODUCER_INCOMPLETE')
        for row in body['lanes']:
            if row.get('status')=='NOT_RUN':
                need('namespaceProcess' not in row and type(row.get('reason')) is str and bool(row['reason']),
                     'PRODUCER_INCOMPLETE')
            else:need(known_process(row.get('namespaceProcess')), 'PRODUCER_INCOMPLETE')
        return 'COMPLETED_OBSERVATION'
    except Rejected:raise
    except Exception:raise Rejected('PRODUCER_INCOMPLETE') from None


@contextlib.contextmanager
def owned_directory(path, T):
    E=T.envelope();path=safe_path(path,E)
    parent=os.open(path.parent,T.DIR_FLAGS)
    identity=None
    try:
        os.mkdir(path.name,0o700,dir_fd=parent)
        info=os.stat(path.name,dir_fd=parent,follow_symlinks=False)
        identity=(info.st_dev,info.st_ino)
        yield path
    finally:
        try:
            if identity is not None:T.remove_owned(parent,path.name,identity)
        except Exception:raise Rejected('CLEANUP') from None
        finally:os.close(parent)


def seal_capture(task, roots, certificate):
    os.umask(0o077)
    T=transport();E=T.envelope()
    task,protected=roots_checked(task,roots)
    admit_producers(task,roots)
    need(not (task/'sealed').exists() and not (task/'sealed').is_symlink(), 'PATH')
    try:
        with owned_directory(task/'transport-work',T) as work:
            try:T.execute('stage',task/'capture',work/'staged',protected_roots=protected)
            except Exception:raise Rejected('STAGING') from None
            try:E.execute('seal',work/'staged',task/'sealed',certificate)
            except Exception:raise Rejected('ENVELOPE') from None
    except Rejected:raise
    except Exception:raise Rejected('PATH') from None


def open_capture(source, output, certificate, key, protected_roots):
    """Caller must authenticate sender/run/attempt/artifact before calling."""
    os.umask(0o077)
    T=transport();E=T.envelope()
    source=safe_path(source,E);output=safe_path(output,E)
    protected=[safe_path(p,E) for p in protected_roots]
    protected += [source,safe_path(HERE.parents[2],E)]
    need(protected_roots and output.parent.is_dir() and not output.exists()
         and not output.is_symlink(), 'PATH')
    need(all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in protected), 'PATH')
    # Fresh trusted private parent, with bounded owned cleanup; no pre-existing
    # destination is replaced and tentative authenticated-decryption output stays inside it.
    path=Path(tempfile.mkdtemp(prefix='capture-open-',dir=output.parent))
    descriptor=os.open(path.parent,T.DIR_FLAGS)
    info=path.stat();identity=(info.st_dev,info.st_ino)
    try:
        try:E.execute('open',source,path/'opened-stage',certificate,key)
        except Exception:raise Rejected('ENVELOPE') from None
        try:T.execute('restore',path/'opened-stage',output,protected_roots=protected)
        except Exception:raise Rejected('RESTORATION') from None
    finally:
        try:T.remove_owned(descriptor,path.name,identity)
        except Exception:raise Rejected('CLEANUP') from None
        finally:os.close(descriptor)


class Parser(argparse.ArgumentParser):
    def error(self,message):raise Rejected('ARGUMENT')


def main(argv=None):
    try:
        parser=Parser(description=__doc__)
        sub=parser.add_subparsers(dest='operation',required=True,parser_class=Parser)
        for op in ('run','seal'):
            p=sub.add_parser(op)
            for key in ('task','research','baseline','historical'):p.add_argument('--'+key,type=Path,required=True)
            if op=='run':p.add_argument('--phase',choices=('acquisition','observation'),required=True)
            else:p.add_argument('--certificate',type=Path,required=True)
        p=sub.add_parser('open')
        for key in ('source','out','certificate','key'):p.add_argument('--'+key,type=Path,required=True)
        p.add_argument('--protect',type=Path,action='append',required=True)
        args=parser.parse_args(argv);os.umask(0o077)
        if args.operation=='run':
            roots={k:getattr(args,k) for k in ('research','baseline','historical')}
            task,_=roots_checked(args.task,roots)
            code=run_command(producer_identity(args.phase,task,roots),task,args.phase)
            print('PRODUCER_RETURNED')
            return code if 0 <= code < 126 else 1
        if args.operation=='seal':
            seal_capture(args.task,{k:getattr(args,k) for k in ('research','baseline','historical')},args.certificate)
        else:open_capture(args.source,args.out,args.certificate,args.key,args.protect)
    except Rejected as error:
        category=str(error) if str(error) in PUBLIC_ERRORS else 'INTERNAL'
        print('CAPTURE_PIPELINE_REJECTED:'+category,file=sys.stderr);return 1
    except KeyboardInterrupt:
        print('CAPTURE_PIPELINE_REJECTED:INTERRUPTED',file=sys.stderr);return 1
    except Exception:
        print('CAPTURE_PIPELINE_REJECTED:INTERNAL',file=sys.stderr);return 1
    print('CAPTURE_PIPELINE_SEALED' if args.operation=='seal' else 'CAPTURE_PIPELINE_OPENED')
    return 0


if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda *unused:(_ for _ in ()).throw(KeyboardInterrupt()))
    sys.exit(main())
