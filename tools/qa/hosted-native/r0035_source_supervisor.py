"""Own only this source coordinator's descendants; retain actual exits and raw logs."""
import ctypes
import errno
import os
from pathlib import Path
import signal
import subprocess
import time


def need(value,message):
    if not value:raise ValueError(message)


def process_table():
    rows={}
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():continue
        try:
            raw=(path/'stat').read_text();parts=raw[raw.rfind(')')+2:].split()
            rows[int(path.name)]={'pid':int(path.name),'ppid':int(parts[1]),'state':parts[0],'startTicks':int(parts[19])}
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    return rows


class Supervisor:
    def __init__(self):
        need(os.name=='posix' and Path('/proc').is_dir(),'Linux process ownership required')
        self.pid=os.getpid();self.started=process_table()[self.pid]['startTicks']
        libc=ctypes.CDLL(None,use_errno=True)
        need(libc.prctl(36,1,0,0,0)==0,'source subreaper unavailable')  # PR_SET_CHILD_SUBREAPER
        self.records=[]

    def descendants(self):
        table=process_table();need(table.get(self.pid,{}).get('startTicks')==self.started,'coordinator PID identity changed')
        owned={self.pid};changed=True
        while changed:
            changed=False
            for pid,row in table.items():
                if pid not in owned and row['ppid'] in owned:owned.add(pid);changed=True
        return [table[pid] for pid in sorted(owned-{self.pid})]

    def quiesce(self):
        before=self.descendants();signals=[];until=time.monotonic()+5
        while True:
            rows=self.descendants()
            if not rows:break
            for row in rows:
                descriptor=None
                try:
                    descriptor=os.pidfd_open(row['pid'])
                    current=process_table().get(row['pid'])
                    if current is None:continue
                    need(current['startTicks']==row['startTicks'],'owned descendant PID reused')
                    signal.pidfd_send_signal(descriptor,signal.SIGKILL)
                    signals.append({'pid':row['pid'],'startTicks':row['startTicks']})
                except ProcessLookupError:pass
                finally:
                    if descriptor is not None:os.close(descriptor)
            while True:
                try:
                    pid,_=os.waitpid(-1,os.WNOHANG)
                    if not pid:break
                except ChildProcessError:break
            if time.monotonic()>=until:break
            time.sleep(0.01)
        remaining=self.descendants()
        result={'protocol':'source-only-descendant-quiescence/1','coordinatorPid':self.pid,'coordinatorStartTicks':self.started,
                'before':before,'signals':signals,'remaining':remaining,'quiescent':not remaining,'unexpectedDescendants':bool(before)}
        self.records.append(result);return result

    def run(self,argv,cwd,env,stdout_path,stderr_path,seconds):
        need(type(seconds) is int and seconds>0 and type(argv) is list and argv and all(type(x) is str for x in argv),'bounded literal command required')
        need(not self.descendants(),'previous source producer still alive')
        result={'argv':argv,'cwd':str(cwd),'timeoutSeconds':seconds,'returncode':None,'timedOut':False,'error':None,'retentionError':None}
        started=time.monotonic();child=None
        try:
            with Path(stdout_path).open('xb') as out,Path(stderr_path).open('xb') as err:
                child=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
                result['pid']=child.pid;result['startTicks']=process_table().get(child.pid,{}).get('startTicks')
                try:result['returncode']=child.wait(timeout=seconds)
                except subprocess.TimeoutExpired:
                    result['timedOut']=True
                    # Kill the actual leader first; detached descendants are then
                    # adopted by this subreaper and terminated below by PID token.
                    child.kill();result['returncode']=child.wait(timeout=5)
        except BaseException as error:
            result['error']={'type':type(error).__name__,'message':str(error)}
            if child is not None and child.poll() is None:
                child.kill();result['returncode']=child.wait(timeout=5)
        finally:
            result['elapsedSeconds']=time.monotonic()-started
            try:result['quiescence']=self.quiesce()
            except BaseException as error:result['retentionError']={'type':type(error).__name__,'message':str(error)}
            for name,path in (('stdout',stdout_path),('stderr',stderr_path)):
                try:
                    need(Path(path).stat().st_size<=16<<20,'terminal stream exceeds summary bound')
                    result[name]=Path(path).read_bytes().decode('utf-8',errors='replace')
                except BaseException as error:
                    result[name]='';result['retentionError']={'type':type(error).__name__,'message':str(error)}
        return result


def successful(process):
    need(type(process.get('returncode')) is int and process['returncode']==0 and process.get('timedOut') is False
         and process.get('error') is None and process.get('retentionError') is None,'actual source process failed')
    need(type(process.get('elapsedSeconds')) in (int,float) and 0<=process['elapsedSeconds']<=process['timeoutSeconds'],'source process exceeded original deadline')
    need(process.get('quiescence',{}).get('quiescent') is True and process['quiescence'].get('unexpectedDescendants') is False,'source producer did not finish quiescently')
    return process
