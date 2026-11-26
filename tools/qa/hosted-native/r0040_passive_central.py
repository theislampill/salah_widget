"""Bounded central custody for the opt-in, unchanged R0040 passive leaf.

No browser is imported here. Current source/preparation replay is a separate
bounded process, and final intake passes an actual retained Buffer to the leaf.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MODE = 'capture-passive'
KIND = 'r0040-capture-passive'
ADMITTED = 'ADMITTED_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION'
TIMING = 'instrumented-passive-date-only'
CHILD_SECONDS = 240
READMISSION_SECONDS = 120
FINAL_SECONDS = 30
POST_CAPTURE_SECONDS = 100 + FINAL_SECONDS
STOP_BYTES = 8 * 1024 * 1024
ENTRY_SHA256 = '7386366a391cb7e401d11a36da691771b1d88a09fa8c16584093184ebd8a7a5e'
SOURCE_PINS = {
    'r0040_passive.cjs': ENTRY_SHA256,
    'r0040_passive_sampler.cjs': '341d93e7ec2047133de8de80640963f8d9c476cbbad9361e57d23ececdb77fed',
    'r0040_passive_runtime.cjs': 'ece35bfbf3a8dfa79e83b84579eb265f0e9a12448015c98ef7172d7a95e14d4c',
    'r0040_dateonly.cjs': '214d4a3c6cb13dbfa69cf0330444aeb9f71d9816b43129091c93bb3121489c44',
    'retain_r0040_capture.cjs': 'd252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f',
    'retain_r0040.cjs': '5e4418ac9d5cda410404462d2f8051959eac53e59d4e7304ac68dc33e39d1328',
    'retention-pins.json': '32f31a2029adacb9c15e471e30bea69d41b2ca5d1ab5079d11b87efe2525bab3',
    'r0040_capture_prepare.py': '4ba6328ee9fe96aec4a96109c58d0d67e0d3e434756829fbe247816bcd001f68',
}
TERMINAL_SCOPE = 'Supplemental expected terminal status; external actual process result remains mandatory.'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def same(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def regular(path, limit=None):
    path = Path(path).absolute()
    need(not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file(),
         'regular passive custody path required')
    if limit is not None:
        need(0 < path.stat().st_size <= limit, 'bounded passive artifact required')
    data = path.read_bytes()
    if limit is not None:
        need(0 < len(data) <= limit, 'bounded passive artifact bytes required')
    return data


def record(path):
    path = Path(path).absolute()
    data = regular(path)
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def verify_sources():
    for name, expected in SOURCE_PINS.items():
        need(hashlib.sha256(regular(HERE/name)).hexdigest() == expected,
             'passive central source drift: '+name)
    return dict(SOURCE_PINS)


def preparation_runtime(entry_path, process_path, common_path, prepared, runtime, task):
    """Bind both real preparation executables before any receipt-driven verifier."""
    task = Path(task).absolute()
    for name in ('node', 'python', 'modules', 'playwright'):
        need(isinstance(runtime, dict) and isinstance(runtime.get(name), str)
             and Path(runtime[name]).is_absolute(), 'absolute acquired runtime required')
    need(runtime['playwright'] == str(Path(runtime['modules'])/'playwright'),
         'Playwright package differs from acquired runtime modules')
    entry_path, process_path, common_path = map(lambda p: Path(p).absolute(), (entry_path, process_path, common_path))
    folder = task/'capture/r0040-preparation'
    need(entry_path == task/'capture/r0040-preparation-entry.json' and process_path == folder/'process.json'
         and common_path == task/'work/prepared/receipts/prepared.json', 'passive preparation paths differ from this campaign')
    common_data = regular(common_path)
    need(same(json.loads(common_data), prepared), 'current common preparation differs from supplied source roots')
    entry, child = (json.loads(regular(p)) for p in (entry_path, process_path))
    # These comparisons precede source hashing or launching any optional verifier.
    need(isinstance(entry, dict) and isinstance(child, dict)
         and isinstance(entry.get('argv'), list) and bool(entry['argv'])
         and isinstance(child.get('argv'), list) and bool(child['argv'])
         and entry['argv'][0] == runtime['python'] == child['argv'][0],
         'actual preparation Python differs from acquired runtime')
    inputs = {'manifest': str(HERE.parents[2]/'docs/state-contracts/evidence/R0040/native-capture-preflight.json'),
              'research': prepared['sources']['research']['root'],
              'historical': prepared['sources']['historical']['root'],
              'main': prepared['trees']['main']['root'], 'out': str(task/'work/r0040-capture')}
    outer = [runtime['python'], str(HERE/'r0040_capture_prepare.py'),
             *[part for key in ('manifest', 'research', 'historical', 'main', 'out') for part in ('--'+key, inputs[key])],
             '--receipts', str(folder)]
    inner = [runtime['python'], '-I', '-B', '-X', 'pycache_prefix='+str(folder/'unused-bytecode-cache'), '-',
             *[inputs[key] for key in ('manifest', 'research', 'historical', 'main', 'out')]]
    need(entry['argv'] == outer and child['argv'] == inner and child.get('inputs') == inputs,
         'actual passive preparation argv or source roots differ')
    for value, protocol, seconds in ((entry, 'r0040-capture-preparation-entry/1', 240),
                                     (child, 'r0040-capture-preparation-process/1', 180)):
        need(value.get('protocol') == protocol and type(value.get('returncode')) is int and value['returncode'] == 0
             and value.get('timedOut') is False and type(value.get('timeoutSeconds')) is int
             and value['timeoutSeconds'] == seconds and value.get('retentionError') is None
             and value.get('error') is None and type(value.get('elapsedSeconds')) in (int, float)
             and math.isfinite(value['elapsedSeconds']) and value['elapsedSeconds'] >= 0,
             'actual passive preparation process did not complete successfully')
    need(entry.get('cwd') == str(HERE) and entry.get('wrapperSha256') == SOURCE_PINS['r0040_capture_prepare.py']
         and child.get('status') == 'PREPARED' and child.get('nativeStatus') == 'NOT_RUN',
         'passive preparation entry source or disposition differs')
    streams = {'entry': {}, 'recipe': {}}
    need(isinstance(child.get('streams'), dict) and set(child['streams']) == {'stdout', 'stderr'},
         'complete original preparation streams required')
    for label in ('stdout', 'stderr'):
        streams['entry'][label] = record(task/'capture'/('r0040-preparation.'+label))
        row = record(folder/('recipe.'+label))
        need(same(child['streams'][label], {'file': 'recipe.'+label, **row}),
             'actual original preparation stream bytes differ')
        streams['recipe'][label] = row
    return {'protocol': 'r0040-passive-preparation-runtime/1',
            **{name: runtime[name] for name in ('node', 'python', 'modules', 'playwright')},
            'entry': record(entry_path), 'process': record(process_path),
            'commonPreparation': record(common_path), 'streams': streams}


def bounded_check(argv, payload, timeout, env=None):
    """A failed/timeout read-only child retains streams and cannot leave its group."""
    environment = dict(os.environ if env is None else env)
    environment.pop('NODE_OPTIONS', None)
    process = None
    try:
        process = subprocess.Popen(argv, cwd=HERE, env=environment, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(json.dumps(payload, allow_nan=False).encode(), timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        return {'argv': argv, 'cwd': str(HERE), 'timeoutSeconds': timeout,
                'returncode': process.returncode, 'timedOut': timed_out,
                'stdout': stdout.decode('utf-8', errors='replace'), 'stderr': stderr.decode('utf-8', errors='replace')}
    except OSError as error:
        return {'argv': argv, 'cwd': str(HERE), 'timeoutSeconds': timeout,
                'returncode': None, 'timedOut': False, 'stdout': '', 'stderr': str(error)}
    except BaseException:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        raise


def readmit(common_path, runtime, task):
    return bounded_check([runtime['python'], '-B', str(Path(__file__).absolute()), '--readmit'],
                         {'common': str(common_path), 'runtime': runtime, 'task': str(task)}, READMISSION_SECONDS)


def check_tail(rows, final):
    terminal = {'protocol': 'r0040-passive-terminal-status/1', 'originalExitCode': final['originalExitCode'],
                'dateOnlyAdmissionExitCode': final['exitCode'], 'exitCode': 0,
                'continuationVetoed': False, 'issues': [], 'scope': TERMINAL_SCOPE}
    tails = [i for i, row in enumerate(rows) if row.get('event') == 'passive-terminal-status']
    need(tails == [len(rows)-1] and same({k: v for k, v in rows[-1].items()
         if k not in ('sequence', 'atUtc', 'monotonicNs', 'event')}, terminal),
         'one matching final passive terminal event required')


def final_check(lane, actual_exit_code, source, rows):
    """Require the original receipt plus complete separately retained stop bytes."""
    verify_sources()
    need(type(actual_exit_code) is int and actual_exit_code == 0, 'actual passive child exit zero required')
    report = lane['result']
    identity = report['passiveDiagnostic']
    need(same(source.get('passive'), identity) and identity.get('entrySha256') == ENTRY_SHA256,
         'current passive source identity differs')
    file = Path(report['passiveAdmissionPath']).absolute()
    evidence = Path(lane['evidenceRetention']['output']).absolute()
    need(file == evidence/'passive-observation.json', 'fixed passive final artifact required')
    receipt_bytes = regular(file)
    receipt = json.loads(receipt_bytes)
    observation = receipt['observation']
    samplers = [row for row in observation['samplers'] if row.get('start') is not None]
    need(len(samplers) == 1 and type(samplers[0].get('id')) is int and 1 <= samplers[0]['id'] <= 4,
         'one bounded original sampler identity required')
    sampler = samplers[0]
    stop_file = evidence/('passive-original-stop-'+str(sampler['id'])+'.json')
    need(sampler['originalStopResponse']['artifact']['file'] == stop_file.name,
         'original stop artifact name differs from bounded session')
    regular(stop_file, STOP_BYTES)
    def one(event):
        found = [(i, row) for i, row in enumerate(rows) if row.get('event') == event]
        need(len(found) == 1, 'one complete passive '+event+' event required')
        return found[0]
    instrument_index, instrument = one('passive-instrumentation')
    stop_index, stop = one('passive-original-stop-response')
    ended_index, ended = one('passive-observation-ended')
    driver_index, _ = one('driver-process-ended')
    need(instrument_index < stop_index < ended_index < driver_index == len(rows)-2
         and same(instrument.get('identity'), identity)
         and same(stop.get('sessionId'), sampler['id'])
         and same(stop.get('observation'), sampler['originalStopResponse'])
         and same(ended.get('observation'), observation)
         and same(ended.get('inspection'), receipt['inspection'])
         and same(ended.get('issues'), receipt['issues']), 'passive journal and retained receipt differ')
    artifacts = {'base': record(report['finalAdmissionPath']), 'passive': record(file), 'stop': record(stop_file)}
    script = r'''
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{isDeepStrictEqual}=require('util');
const x=JSON.parse(fs.readFileSync(0,'utf8')),need=(ok,msg)=>{if(!ok)throw Error(msg)},sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function read(row,limit){let q=path.resolve(row.path);for(;;){need(!fs.lstatSync(q).isSymbolicLink(),'regular passive ancestry required');const p=path.dirname(q);if(p===q)break;q=p;}
 const fd=fs.openSync(row.path,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const st=fs.fstatSync(fd);need(st.isFile()&&(!limit||(st.size>0&&st.size<=limit)),'regular bounded passive artifact required');
 const b=fs.readFileSync(fd);need(b.length===row.bytes&&sha(b)===row.sha256&&(!limit||b.length<=limit),'retained passive artifact bytes changed');return b;}finally{fs.closeSync(fd);}}
const entry=process.argv[1];need(sha(fs.readFileSync(entry))===x.entrySha256,'passive entry source differs');
const p=require(entry),identity=p.passiveIdentity(x.driver);need(isDeepStrictEqual(identity,x.identity),'current passive leaf identity differs');
const baseBytes=read(x.artifacts.base),passiveBytes=read(x.artifacts.passive),originalStopBytes=read(x.artifacts.stop,8*1024*1024);
const receipt=JSON.parse(passiveBytes);
const inspection=p.admitPassiveReceipt(receipt,baseBytes,identity,x.dateOnlyDiagnostic,x.actualExitCode,originalStopBytes);
process.stdout.write(JSON.stringify({protocol:'r0040-passive-central-inspection/1',status:'OBSERVED',identity,inspection,artifacts:x.artifacts,actualExitCode:x.actualExitCode}));
'''
    process = bounded_check([lane['evidenceRetention']['originalArgv'][0], '-e', script, str(HERE/'r0040_passive.cjs')],
        {'driver': lane['evidenceRetention']['originalArgv'][1], 'entrySha256': ENTRY_SHA256,
         'identity': identity, 'dateOnlyDiagnostic': report['diagnostic'], 'actualExitCode': actual_exit_code,
         'artifacts': artifacts}, FINAL_SECONDS)
    return process, artifacts


def main():
    need(sys.argv[1:] == ['--readmit'], 'only bounded passive source readmission is supported')
    value = json.load(sys.stdin)
    runtime, task, common = value['runtime'], Path(value['task']).absolute(), Path(value['common']).absolute()
    need(runtime['python'] == sys.executable, 'readmission Python differs from acquired runtime')
    from prepare import validate_prepared
    from lanes import admit_r0040
    prepared = validate_prepared(common)
    admission = admit_r0040(prepared, task/'work/r0040-capture', task/'capture/r0040-preparation/process.json',
                           task/'capture/r0040-preparation-entry.json', task/'capture/lanes',
                           Path(runtime['node']), Path(runtime['playwright']), mode=MODE,
                           python=runtime['python'], common_prepared=common, task=task,
                           modules=runtime['modules'])
    print(json.dumps(admission, allow_nan=False))
    return 0 if admission['status'] == 'PASS' else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print('Passive source readmission incomplete: '+str(error), file=sys.stderr)
        sys.exit(2)
