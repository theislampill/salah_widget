"""Opt-in mechanism custody. Original passive admission remains mandatory.

The combined replay consumes the actual retained stop Buffer and actual child
exit in one existing thirty-second ceiling. This module launches no browser.
"""
import hashlib
import json
from pathlib import Path
import sys

import r0040_passive_central as passive

HERE = Path(__file__).resolve().parent
MODE = 'capture-mechanism'
KIND = 'r0040-capture-mechanism'
ADMITTED = 'ADMITTED_MECHANISM_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION'
TIMING = 'instrumented-mechanism-passive-date-only'
ENTRY_SHA256 = 'cc7a791fba7438a36743a424d6bd063289217b54bea05ec10be07206356abf93'
SOURCE_PINS = {
    'r0040_mechanism.cjs': ENTRY_SHA256,
    'r0040_mechanism_bracket.cjs': 'b2a2e73433055ab90f4ae617f70268e0d5f02563e36c6a5ffc071ce0445c5757',
    'r0040_mechanism_network.cjs': '77d40fa3519d0328fb3fcfda34f5c5001e0d82790b365801f989a5126a978af7',
}
CALLER_FILES = ('r0040_mechanism_central.py', 'r0040_passive_central.py', 'lanes.py',
                'observe.py', 'capture_pipeline.py', 'prepare.py', 'r0040_capture_prepare.py')
CHILD_SECONDS = passive.CHILD_SECONDS
READMISSION_SECONDS = passive.READMISSION_SECONDS
FINAL_SECONDS = passive.FINAL_SECONDS
POST_CAPTURE_SECONDS = passive.POST_CAPTURE_SECONDS
ARTIFACT_BYTES = 4 * 1024 * 1024
need, same, regular, record = passive.need, passive.same, passive.regular, passive.record


def verify_sources():
    old = passive.verify_sources()
    for name, expected in SOURCE_PINS.items():
        need(hashlib.sha256(regular(HERE/name)).hexdigest() == expected,
             'mechanism central source drift: '+name)
    return {**old, **SOURCE_PINS}


def caller_sources():
    """Current caller bytes bound separately from the immutable leaf pins."""
    return {name: record(HERE/name) for name in CALLER_FILES}


def readmit(common_path, runtime, task):
    return passive.bounded_check([runtime['python'], '-B', str(Path(__file__).absolute()), '--readmit'],
        {'common': str(common_path), 'runtime': runtime, 'task': str(task)}, READMISSION_SECONDS, raw=True)


REPLAY_SCRIPT = r'''
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{isDeepStrictEqual}=require('util');
const x=JSON.parse(fs.readFileSync(0,'utf8')),need=(ok,msg)=>{if(!ok)throw Error(msg)},sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function read(row,limit){let q=path.resolve(row.path);for(;;){need(!fs.lstatSync(q).isSymbolicLink(),'regular mechanism ancestry required');const p=path.dirname(q);if(p===q)break;q=p;}
 const fd=fs.openSync(row.path,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const st=fs.fstatSync(fd);need(st.isFile()&&(!limit||(st.size>0&&st.size<=limit)),'regular bounded mechanism artifact required');
 const b=fs.readFileSync(fd);need(b.length===row.bytes&&sha(b)===row.sha256&&(!limit||b.length<=limit),'retained mechanism artifact bytes changed');return b;}finally{fs.closeSync(fd);}}
const entry=process.argv[1];need(sha(fs.readFileSync(entry))===x.entrySha256,'mechanism entry source differs');
const m=require(entry),identity=m.mechanismIdentity(x.driver);need(isDeepStrictEqual(identity,x.identity),'current mechanism leaf identity differs');
const baseBytes=read(x.artifacts.base),passiveBytes=read(x.artifacts.passive),originalStopBytes=read(x.artifacts.stop,8*1024*1024),receipt=JSON.parse(read(x.artifacts.mechanism,4*1024*1024));
const inspection=m.admitMechanismReceipt(receipt,baseBytes,passiveBytes,identity,x.dateOnlyDiagnostic,x.actualExitCode,originalStopBytes);
process.stdout.write(JSON.stringify({protocol:'r0040-mechanism-central-inspection/1',status:'OBSERVED',identity,inspection,artifacts:x.artifacts,actualExitCode:x.actualExitCode}));
'''


def replay_argv(lane):
    return [lane['evidenceRetention']['originalArgv'][0], '-e', REPLAY_SCRIPT, str(HERE/'r0040_mechanism.cjs')]


def final_check(lane, actual_exit_code, source, rows):
    verify_sources()
    need(type(actual_exit_code) is int and actual_exit_code == 0, 'actual mechanism child exit zero required')
    report, preparation = lane['result'], lane['preparation']
    identity, old_identity = report['mechanismDiagnostic'], report['passiveDiagnostic']
    need(same(source.get('mechanism'), identity) and identity.get('entrySha256') == ENTRY_SHA256
         and same(identity.get('passive'), old_identity) and same(source.get('passive'), old_identity)
         and old_identity.get('entrySha256') == passive.ENTRY_SHA256
         and same(preparation.get('mechanismSources'), verify_sources())
         and same(preparation.get('mechanismCallerSources'), caller_sources()),
         'current mechanism/passive source or caller identity differs')
    evidence = Path(lane['evidenceRetention']['output']).absolute()
    old_file, file = Path(report['passiveAdmissionPath']).absolute(), Path(report['mechanismAdmissionPath']).absolute()
    need(old_file == evidence/'passive-observation.json' and file == evidence/'mechanism-observation.json',
         'fixed original passive and mechanism artifacts required')
    receipt = json.loads(regular(file, ARTIFACT_BYTES))
    old = json.loads(regular(old_file))
    observation, old_observation = receipt['observation'], old['observation']
    samplers = [row for row in old_observation['samplers'] if row.get('start') is not None]
    need(len(samplers) == 1 and type(samplers[0].get('id')) is int and 1 <= samplers[0]['id'] <= 4,
         'one bounded original sampler identity required')
    sampler = samplers[0]
    stop_file = evidence/('passive-original-stop-'+str(sampler['id'])+'.json')
    need(sampler['originalStopResponse']['artifact']['file'] == stop_file.name,
         'original stop artifact name differs from bounded session')
    regular(stop_file, passive.STOP_BYTES)

    def one(event):
        found = [(i, row) for i, row in enumerate(rows) if row.get('event') == event]
        need(len(found) == 1, 'one complete mechanism '+event+' event required')
        return found[0]

    instrument_index, instrument = one('passive-instrumentation')
    stop_index, stop = one('passive-original-stop-response')
    ended_index, ended = one('passive-observation-ended')
    driver_index, _ = one('driver-process-ended')
    need(instrument_index < stop_index < ended_index < driver_index == len(rows)-2
         and same(instrument.get('identity'), old_identity) and same(stop.get('sessionId'), sampler['id'])
         and same(stop.get('observation'), sampler['originalStopResponse'])
         and same(ended.get('observation'), old_observation)
         and same(ended.get('inspection'), old['inspection']) and same(ended.get('issues'), old['issues']),
         'original passive journal and retained receipt differ')
    passive.check_tail(rows, json.loads(regular(report['finalAdmissionPath'])))
    new_index, new = one('mechanism-instrumentation')
    bracket_index, bracket = one('mechanism-bracket-prefix')
    finish_index, finish = one('mechanism-observation-ended')
    prefixes = [(i, row) for i, row in enumerate(rows) if row.get('event') == 'mechanism-network-prefix']
    need(new_index < stop_index < bracket_index < finish_index < ended_index
         and same(new.get('identity'), identity) and same(bracket.get('observation'), observation['bracket'])
         and same(finish.get('observation'), observation) and same(finish.get('inspection'), receipt['inspection'])
         and [row.get('phase') for _, row in prefixes] ==
             ['before-context-creation', 'readiness-returned', 'after-original-context-close']
         and new_index < prefixes[0][0] < prefixes[1][0] < stop_index < bracket_index < prefixes[2][0] < finish_index
         and same(prefixes[-1][1].get('observation'), observation['network']),
         'complete ordered mechanism prefixes and final receipt differ')
    artifacts = {'base': record(report['finalAdmissionPath']), 'passive': record(old_file),
                 'stop': record(stop_file), 'mechanism': record(file)}

    process = passive.bounded_check(replay_argv(lane),
        {'driver': lane['evidenceRetention']['originalArgv'][1], 'entrySha256': ENTRY_SHA256,
         'identity': identity, 'dateOnlyDiagnostic': report['diagnostic'], 'actualExitCode': actual_exit_code,
         'artifacts': artifacts}, FINAL_SECONDS)
    return process, artifacts


def namespace_admitted(lane, inner, date_identity):
    """A mechanism label requires both independent components and the old gate."""
    if inner.get('status') != ADMITTED:
        return True
    result = lane.get('result', {})
    inspection, process = inner.get('mechanismInspection', {}), inner.get('mechanismVerification', {})
    if any(type(value) is not dict for value in (result, inspection, process,
            inner.get('mechanismDiagnostic'), inner.get('passiveDiagnostic'), inner.get('passiveInspection'),
            inner.get('mechanismArtifacts'), inspection.get('bracket') if type(inspection) is dict else None,
            inspection.get('network') if type(inspection) is dict else None)):
        return False
    try:
        replay = json.loads(process['stdout'])
        replay_matches = same(replay, {'protocol': 'r0040-mechanism-central-inspection/1', 'status': 'OBSERVED',
            'identity': inner['mechanismDiagnostic'], 'inspection': {'protocol': 'r0040-mechanism-admission/1',
                'status': 'OBSERVED', 'passive': inner['passiveInspection'], 'mechanism': inspection},
            'artifacts': inner['mechanismArtifacts'], 'actualExitCode': 0})
        command_matches = same(process.get('argv'), replay_argv(lane))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False
    return (result.get('kind') == KIND and type(inner.get('returncode')) is int and inner['returncode'] == 0
            and inner.get('timedOut') is False and inner.get('nativeQualification') == 'NOT_VERIFIED'
            and inner.get('humanAcceptance') == 'OUTSTANDING' and inner.get('timingClass') == TIMING
            and inner.get('dateOnlyStatus') == 'ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION'
            and same(inner.get('diagnostic'), date_identity)
            and same(inner.get('passiveDiagnostic'), result.get('passiveDiagnostic'))
            and inner.get('passiveDiagnostic', {}).get('entrySha256') == passive.ENTRY_SHA256
            and same(inner.get('mechanismDiagnostic'), result.get('mechanismDiagnostic'))
            and inner.get('mechanismDiagnostic', {}).get('entrySha256') == ENTRY_SHA256
            and type(process.get('returncode')) is int and process['returncode'] == 0 and process.get('timedOut') is False
            and type(process.get('timeoutSeconds')) is int and process['timeoutSeconds'] == FINAL_SECONDS
            and process.get('cwd') == str(HERE) and command_matches and replay_matches
            and inner.get('passiveInspection', {}).get('status') == 'OBSERVED'
            and inspection.get('protocol') == 'r0040-mechanism-inspection/1' and inspection.get('status') == 'OBSERVED'
            and all(inspection.get(name, {}).get('status') == 'OBSERVED' for name in ('bracket', 'network'))
            and inspection.get('cause') == 'NOT_ESTABLISHED')


def main():
    need(sys.argv[1:] == ['--readmit'], 'only bounded mechanism source readmission is supported')
    value = json.load(sys.stdin)
    runtime, task, common = value['runtime'], Path(value['task']).absolute(), Path(value['common']).absolute()
    need(runtime['python'] == sys.executable, 'readmission Python differs from acquired runtime')
    from prepare import validate_prepared
    from lanes import admit_r0040
    prepared = validate_prepared(common)
    admission = admit_r0040(prepared, task/'work/r0040-capture', task/'capture/r0040-preparation/process.json',
        task/'capture/r0040-preparation-entry.json', task/'capture/lanes', Path(runtime['node']),
        Path(runtime['playwright']), mode=MODE, python=runtime['python'], common_prepared=common,
        task=task, modules=runtime['modules'])
    print(json.dumps(admission, allow_nan=False))
    return 0 if admission['status'] == 'PASS' else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print('Mechanism source readmission incomplete: '+str(error), file=sys.stderr)
        sys.exit(2)
