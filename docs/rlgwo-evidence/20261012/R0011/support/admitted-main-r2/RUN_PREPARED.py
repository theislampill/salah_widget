"""Root-only first Settings caller; default is read-only checks, never native.

Uses the existing root capacity-one grant/try/finally pattern. An unknown child
completion holds the lease for attention rather than falsely freeing capacity.
"""
import argparse
import copy
import socket
import time
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
D = RUN / 'evidence/R0011/whole-owner-main-r1-top-read-getter'
O = D / 'native-runs/first-root'
L = RUN / 'ACTIVE_LEDGER.json'
LEASE_ID = 'root-r0011-whole-main-r1-top-read-getter'
CASE = 'top-read-getter'
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda path: json.loads(path.read_bytes())
now = lambda: dt.datetime.now(dt.timezone.utc).isoformat()

def fresh(path):
    # lstat semantics retain occupied files, directories and dangling links.
    if os.path.lexists(path):
        raise ValueError('Occupied output identity is preserved: ' + str(path))

def write_new(path, data):
    fresh(path)
    with path.open('xb') as handle:
        handle.write(data)

def json_new(path, value):
    write_new(path, (json.dumps(value, indent=2) + '\n').encode())

"""Definitions inserted into the retained standalone carrier, not a new runtime."""
def validate_selector(ids):
    assert isinstance(ids, list) and len(ids) == 1 and ids[0] in case_catalogue()['preparedCaseIds'], 'Exactly one prepared remaining original case; no unknown, duplicate or completed replay'
    return ids

def review_reference(pin):
    assert isinstance(pin, dict) and set(pin) == {'path', 'bytes', 'sha256'}
    path = Path(pin['path']).resolve()
    assert path.is_relative_to(RUN.resolve()) and not path.is_relative_to(HERE.resolve()), 'Actual independent root/review reference required'
    raw = path.read_bytes()
    assert len(raw) == pin['bytes'] and sha(raw) == pin['sha256']
    return json.loads(raw)

def validate_review_approval(approval, binding, packet_seal):
    assert approval['schema'] == 'r0011-original-remaining-frozen-review-approval/1'
    assert approval['status'] == 'SCOPED_SOURCE_CARRIER_PASS'
    assert approval['packetSealSha256'] == packet_seal
    allowed = approval['allowedCaseIds']
    prepared = case_catalogue()['preparedCaseIds']
    assert isinstance(allowed, list) and allowed and allowed == prepared[:len(allowed)] and CASE in allowed, 'Exact independently reviewed original prefix required; no inherited singleton grant'
    assert approval['caseContractsSha256'] == binding['caseContractsSha256']
    assert approval['driverSha256'] == binding['nativeReferences']['residual-location-actions.cjs']['sha256']
    assert approval['runtimeSha256'] == binding['sourceBinding']['runtimeSha256']
    report = review_reference(approval['report'])
    seal = review_reference(approval['seal'])
    source_admission = review_reference(approval['sourceAdmission'])
    assert seal['reportSha256'] == approval['report']['sha256']
    assert source_admission['reportSha256'] == approval['report']['sha256']
    assert source_admission['status'] == 'SCOPED_SOURCE_ADMISSION_PASS'
    assert source_admission['allowedNextRootCaseIds'] == report['allowedNextRootCaseIds'] == allowed
    assert source_admission['packetSealSha256'] == report['packetSealSha256'] == packet_seal
    assert source_admission['caseContractsSha256'] == report['caseContractsSha256'] == binding['caseContractsSha256']
    assert source_admission['driverSha256'] == approval['driverSha256']
    assert source_admission['runtimeSha256'] == approval['runtimeSha256']
    assert source_admission['carrierSha256'] == sha((HERE / 'RUN_PREPARED.py').read_bytes())
    assert isinstance(source_admission['reviewer'], str) and source_admission['reviewer'].strip()
    assert source_admission['reviewer'] not in ['/root/r0011_whole_owner', '/root/persistence_native', HERE.name]
    assert report['reviewer'] == source_admission['reviewer']
    assert approval['priorPositiveReportSha256'] == binding['priorPositive']['reviewReportSha256']
    assert approval['priorPositiveSealSha256'] == binding['priorPositive']['reviewSealSha256']
    assert approval['priorIgnoreSaveReportSha256'] == binding['priorIgnoreSave']['reviewReportSha256']
    assert approval['priorIgnoreSaveSealSha256'] == binding['priorIgnoreSave']['reviewSealSha256']
    return source_admission['reviewer']

def validate_finite_lease(lease, binding, approval, active=False):
    assert type(lease['capacity']) is int and lease['capacity'] == 1
    assert lease['status'] == ('ACTIVE' if active else 'FREE')
    assert lease['holder'] == ('root' if active else None)
    assert lease['leaseId'] == LEASE_ID and lease['preparedForLeaseId'] == LEASE_ID
    assert lease['node'] == 'R0011-EVIDENCE'
    assert lease['driverSha256'] == binding['nativeReferences']['residual-location-actions.cjs']['sha256']
    assert lease['rootDriverSha256'] == sha((HERE / 'RUN_PREPARED.py').read_bytes())
    assert lease['reviewSealSha256'] == approval['seal']['sha256']
    assert lease['sourceRoot'] == binding['sourceRoot'] and lease['runtimeSha256'] == binding['sourceBinding']['runtimeSha256']
    assert lease['outputPath'] == str(O) and lease['effectRoot'] == str(D)
    assert lease['preparedCaseIds'] == [CASE]
    assert lease['caseContractsSha256'] == binding['caseContractsSha256']
    assert lease['totalCases'] == 1 and lease['completedCases'] == 0 and lease['finishedAtUtc'] is None
    assert lease['unknownChildCompletion'] is False and lease['attentionRequired'] is False
    prepared = dt.datetime.fromisoformat(lease['preparedAtUtc'])
    expires = dt.datetime.fromisoformat(lease['expiresAtUtc'])
    assert prepared.tzinfo is not None and expires.tzinfo is not None
    current = dt.datetime.now(dt.timezone.utc)
    assert prepared <= current < expires, 'Fresh finite currently valid lease required; no fabricated duration estimate'

def acquisition_snapshot(binding, approval):
    raw = L.read_bytes()
    ledger = json.loads(raw)
    lease = ledger['resourceLeases']['heavy-browser']
    validate_finite_lease(lease, binding, approval, active=True)
    write_new(D / 'actual-acquisition-ledger.json', raw)
    json_new(D / 'actual-acquisition-snapshot.json', {'schema': 'r0011-active-lease-acquisition-snapshot/1',
        'phase': 'ACTIVE_LEASE_BEFORE_NATIVE_START', 'observedAtUtc': now(),
        'ledgerSha256': sha(raw), 'lease': lease, 'caseIds': [CASE],
        'nativeStarted': False, 'nativeOrDescendantCensusClaim': False})

def validate_admission(admission, binding, packet_seal, approval, approval_sha):
    # Exact identity from the retained ROOT_ADMISSION_SCHEMA.json proposal.
    # Passing these fields is not evidence of actual root owner authority.
    assert admission['schema'] == 'root-r0011-rolling-single-case-admission/1'
    assert admission['status'] == 'ADMITTED_SCOPED_ONE_REMAINING_CASE'
    assert admission['packetSealSha256'] == packet_seal
    assert admission['sourceReviewReportSha256'] == binding['sourceReview']['reportSha256']
    assert admission['sourceReviewSealSha256'] == binding['sourceReview']['sealSha256']
    assert admission['sourceReviewer'] == binding['sourceReview']['reviewer']
    assert admission['nativeDriverSha256'] == binding['nativeReferences']['residual-location-actions.cjs']['sha256']
    assert admission['sourceRoot'] == binding['sourceRoot']
    assert admission['toolBindingsSha256'] == binding['toolBindingsSha256']
    assert admission['effectRoot'] == str(D) and admission['nativeOutput'] == str(O)
    assert admission['leaseId'] == LEASE_ID
    assert admission['runtimeSha256'] == binding['sourceBinding']['runtimeSha256']
    assert admission['allowedCaseIds'] == [CASE]
    assert admission['caseContractsSha256'] == binding['caseContractsSha256']
    assert admission['priorIgnoreSaveReportSha256'] == binding['priorIgnoreSave']['reviewReportSha256']
    assert admission['priorIgnoreSaveSealSha256'] == binding['priorIgnoreSave']['reviewSealSha256']
    assert admission['reviewApprovalSha256'] == approval_sha
    assert admission['guardReviewReportSha256'] == approval['report']['sha256']
    assert admission['guardReviewSealSha256'] == approval['seal']['sha256']
    assert admission['caseSourceAdmissionSha256'] == approval['sourceAdmission']['sha256']
    assert admission['priorPositiveReportSha256'] == binding['priorPositive']['reviewReportSha256']
    assert admission['priorPositiveSealSha256'] == binding['priorPositive']['reviewSealSha256']
    assert admission['guardReviewed'] is True and admission['freshSourceDiscussionAdmission'] is True
    assert isinstance(admission['reviewer'], str) and admission['reviewer'].strip() and admission['reviewer'] not in ['persistence_native_root_dispatch_r1', HERE.name, '/root/persistence_native', '/root/r0011_whole_owner']
    if 'guardReviewReportSha256' in admission:
        digest = admission['guardReviewReportSha256']
        assert isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)

def validate_native_terminal(binding, expected_case, frontend_return, receipt):
    contract = binding['caseContract']
    case_id = expected_case['name']
    output = Path(contract['fresh']['nativeOutput'])
    assert expected_case == contract['recipe']
    terminal_path = output / 'results.json'
    assert terminal_path.is_file(), 'Expected post-cleanup native terminal manifest is missing'
    raw = terminal_path.read_bytes()
    receipt['resultsSha256'] = sha(raw)
    terminal = json.loads(raw)
    receipt['results'] = terminal
    assert isinstance(terminal, dict)
    assert set(terminal) == {'schema', 'sourceRef', 'group', 'selected', 'executed', 'notRun', 'independentPixels', 'closure'}
    assert terminal['schema'] == 'residual-native-results/v1'
    assert terminal['sourceRef'] == binding['sourceBinding']['sourceRef']
    assert terminal['group'] == 'r0011' and terminal['selected'] == [case_id]
    assert terminal['notRun'] == [] and terminal['independentPixels'] == 'PENDING' and terminal['closure'] == 'NOT_AUTHORIZED'
    assert isinstance(terminal['executed'], list) and len(terminal['executed']) == 1
    executed = terminal['executed'][0]
    assert isinstance(executed, dict) and set(executed) == {'name', 'status', 'result'}
    assert executed['name'] == case_id and executed['status'] in [contract['expectedStatus'], 'FAIL']
    result_path = output / case_id / 'result.json'
    normalized = lambda value: os.path.normcase(os.path.normpath(value))
    assert isinstance(executed['result'], str) and normalized(executed['result']) == normalized(str(result_path))
    assert result_path.is_file(), 'Expected executed case readback is missing'
    row_raw = result_path.read_bytes()
    receipt['caseResultSha256'] = sha(row_raw)
    row = json.loads(row_raw)
    assert isinstance(row, dict)
    for key, value in expected_case.items(): assert row[key] == value, 'Unexpected exact case identity: ' + key
    assert row.get('mutant') == expected_case.get('mutant') and row['status'] == executed['status']
    assert isinstance(row['out'], str) and normalized(row['out']) == normalized(str(output / case_id))
    assert row['sourceRef'] == binding['sourceBinding']['sourceRef'] and row['runtimeSha256'] == binding['sourceBinding']['runtimeSha256']
    assert row['sourceBinding'] == binding['expectedTerminalSourceBinding'], 'Unexpected actual consumer source binding'
    assert row['sourceKind'] == contract['sourceKind']
    assert isinstance(row['native'], dict) and row['native']['browser'] == 'chromium'
    assert row['independentReview'] == 'PENDING'
    assert isinstance(row['checks'], list) and isinstance(row['snapshots'], dict) and isinstance(row['crops'], list)
    assert all(isinstance(c, dict) and type(c['passed']) is bool for c in row['checks'])
    if row['status'] in ['PASS', 'CAUGHT']:
        validate_case_prerequisites(row, contract)
        if row['status'] == 'CAUGHT':
            assert row['mutantConsumerFailurePreserved'] is True
            assert row['error']['code'] == 'CONSUMER_ASSERTION' and row['error']['assertion'] == contract['mutation']['oracle']
            assert row['checks'][-1]['passed'] is False and row['checks'][-1]['name'] == row['error']['assertion']
            assert all(c['passed'] is True for c in row['checks'][:-1])
        else:
            assert not row.get('error') and all(c['passed'] is True for c in row['checks'])
    else:
        assert isinstance(row['error'], dict) and isinstance(row['error']['message'], str) and row['error']['message']
    assert type(frontend_return) is int and frontend_return == (1 if row['status'] == 'FAIL' else 0), 'Opaque or inconsistent frontend completion'
    receipt['nativeCompletionBasis'] = 'VALIDATED_EXPECTED_POST_CLEANUP_TERMINAL_MANIFEST_AND_CASE_READBACK'
    receipt['consumerStatus'] = row['status']
    return row['status']

def verify(ids=None):
    seal = read(HERE / 'SEAL.json')
    files = seal['files']
    payload = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p != HERE / 'SEAL.json'}
    assert payload == set(files), 'Exact sealed dispatch payload membership required'
    for name, row in files.items():
        path = (HERE / name).resolve()
        assert path.is_relative_to(HERE)
        data = path.read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], name
    canonical = ''.join(f"{v['sha256']}  {k}\n" for k,v in sorted(files.items()))
    assert sha(canonical.encode()) == seal['treeSha256']
    binding = select_context(read(HERE / 'BINDING.json'), (ids or [CASE])[0])
    assert sha((HERE / 'CASE_CONTRACTS.json').read_bytes()) == binding['caseContractsSha256']
    delta = read(HERE / 'DELTA_BINDING.json')
    for row in binding['references'] + delta['references']:
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['path']
    source = Path(binding['sourceRoot'])
    for name, row in binding['sourceBinding']['runtimeEntries'].items():
        path = (source / name).resolve()
        assert path.is_relative_to(source.resolve())
        data = path.read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], name
    assert sha((source / 'src/native/index.html').read_bytes()) == binding['sourceBinding']['authoredIndexSha256']
    for name, row in binding['tools'].items():
        if not isinstance(row, dict):
            continue
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], name
    fresh(D)
    fresh(O)
    assert D.resolve().is_relative_to(RUN.resolve())
    return binding, sha((HERE / 'SEAL.json').read_bytes())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-native', action='store_true')
    parser.add_argument('--root-admission', type=Path)
    parser.add_argument('--review-approval', type=Path)
    parser.add_argument('--only', action='append', default=[])
    parser.add_argument('--previous-completion', type=Path)
    parser.add_argument('--reset-positive-review', type=Path)
    args = parser.parse_args()
    validate_selector(args.only or [CASE])
    binding, packet_seal = verify(args.only or [CASE])
    if not args.execute_native:
        print(json.dumps({'status': 'PASS_READ_ONLY_ROOT_GUARDS', 'case': CASE, 'runtime': binding['sourceBinding']['runtimeSha256'], 'dispatch': str(D), 'output': str(O), 'outputFresh': True, 'native': 'NOT_RUN'}))
        return 0
    if args.root_admission is None:
        parser.error('Actual root guard/source/discussion/case admission receipt required')
    admission_bytes = args.root_admission.read_bytes()
    admission = json.loads(admission_bytes)
    if args.review_approval is None:
        parser.error('Frozen independent one-case source/carrier approval required')
    approval_bytes = args.review_approval.read_bytes()
    approval = json.loads(approval_bytes)
    validate_review_approval(approval, binding, packet_seal)
    validate_admission(admission, binding, packet_seal, approval, sha(approval_bytes))
    if binding['caseContract'].get('requiresIndependentResetPositive'):
        assert args.reset_positive_review is not None, 'Independent actual reset-positive trace/pixel acceptance required before ignoreReset'
        validate_reset_positive_review(read(args.reset_positive_review), read(HERE / 'BINDING.json'), packet_seal)
    expected_case = binding['caseContract']['recipe']
    validate_previous_completion(args.previous_completion, binding, approval, packet_seal)
    before = L.read_bytes()
    ledger = json.loads(before)
    lease = ledger['resourceLeases']['heavy-browser']
    assert lease['status'] == 'FREE' and lease['holder'] is None and lease['capacity'] == 1
    validate_finite_lease(lease, binding, approval)
    # This receiving identity is atomically reserved before any staged files.
    fresh(D)
    fresh(O)
    D.mkdir(parents=True, exist_ok=False)
    native_dir = D / 'native'
    fresh(native_dir)
    native_dir.mkdir(exist_ok=False)
    for name in ['residual-location-native.py', 'residual-location-actions.cjs', 'residual-location-native.html', 'source-binding.json']:
        write_new(native_dir / name, (HERE / 'native' / name).read_bytes())
    write_new(D / 'root-admission.json', admission_bytes)
    write_new(D / 'review-approval.json', approval_bytes)
    write_new(D / 'ledger-before-grant.json', before)
    tools = binding['tools']
    argv = [tools['python']['path'], '-I', '-S', '-B', str(native_dir / 'residual-location-native.py'), '--source-root', binding['sourceRoot'], '--source-ref', binding['sourceBinding']['sourceRef'], '--group', 'r0011', '--browser', 'chromium', '--node', tools['node']['path'], '--package-root', tools['packageRoot'], '--executable', tools['executable']['path'], '--only', CASE, '--out', str(O), '--lease-authorized']
    receipt = {'schema': 'root-r0011-first-native-dispatch/1', 'status': 'PREPARED_NOT_LAUNCHED', 'leaseId': LEASE_ID, 'startedAtUtc': now(), 'command': argv, 'sourceRuntime': binding['sourceBinding']['runtimeSha256'], 'packetSealSha256': packet_seal, 'sourceReviewReportSha256': binding['sourceReview']['reportSha256'], 'sourceReviewSealSha256': binding['sourceReview']['sealSha256'], 'sourceReviewer': binding['sourceReview']['reviewer'], 'nativeDriverSha256': binding['nativeReferences']['residual-location-actions.cjs']['sha256'], 'sourceRoot': binding['sourceRoot'], 'toolBindingsSha256': binding['toolBindingsSha256'], 'effectRoot': str(D), 'nativeOutput': str(O), 'rootAdmissionSha256': sha(admission_bytes), 'onlyCase': CASE, 'negativeLater': None, 'nativeStarted': False, 'nativeComplete': False, 'independentTracePixelReview': 'PENDING'}
    receipt.update(caseContractsSha256=binding['caseContractsSha256'], rootDriverSha256=sha((HERE / 'RUN_PREPARED.py').read_bytes()), reviewApprovalSha256=sha(approval_bytes), guardReviewReportSha256=approval['report']['sha256'], guardReviewSealSha256=approval['seal']['sha256'])
    json_new(D / 'dispatch-start.json', receipt)
    granted = False
    known_complete = False
    try:
        lease.update(status='ACTIVE', holder='root', leaseId=LEASE_ID, command=str(HERE / 'RUN_PREPARED.py'), startedAtUtc=now(), finishedAtUtc=None, currentCase=CASE, totalCases=1, completedCases=0, scope='One original R0011 e718 save/reset/read/recovery context, bound to the exact selected recipe. No real-host/reload/speech/node closure credit.')
        ledger['updatedAtUtc'] = now()
        replacement = D / 'ledger-grant.json'
        json_new(replacement, ledger)
        assert L.read_bytes() == before, 'Root ledger drift before grant'
        replacement.replace(L)
        granted = True
        acquisition_snapshot(binding, approval)
        # Recheck all fresh launch artifacts immediately before the front door.
        fresh(O)
        fresh(D / 'stdout.log')
        fresh(D / 'stderr.log')
        with (D / 'stdout.log').open('xb') as stdout, (D / 'stderr.log').open('xb') as stderr:
            managed_census(D, native_dir / 'residual-location-native.py', 'PRE_NATIVE')
            receipt['nativeStarted'] = True
            child = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
            receipt['processId'] = positive_pid(child.pid)
            frontend_return = child.wait()
        receipt['exitCode'] = frontend_return
        consumer_status = validate_native_terminal(binding, expected_case, frontend_return, receipt)
        capture_cleanup(binding, receipt, native_dir)
        known_complete = True
        receipt.update(nativeComplete=True, status='CONTROL_CAUGHT_PENDING_TRACE_PIXEL_REVIEW' if consumer_status == 'CAUGHT' else 'PASSED_NATIVE_CASE_PENDING_TRACE_PIXEL_REVIEW' if consumer_status == 'PASS' else 'FAILED_NATIVE_CONSUMER_PENDING_TRACE_PIXEL_REVIEW')
    except BaseException as error:
        receipt.update(status='STOPPED_EXCEPTION_NO_RETRY', error=repr(error))
        write_new(D / 'exception.txt', traceback.format_exc().encode())
    finally:
        receipt['finishedAtUtc'] = now()
        receipt['unknownCompletion'] = receipt['nativeStarted'] and not known_complete
        json_new(D / 'dispatch-result.json', receipt)
        if granted:
            release_before = L.read_bytes()
            final_ledger = json.loads(release_before)
            final_lease = final_ledger['resourceLeases']['heavy-browser']
            assert final_lease['holder'] == 'root' and final_lease['leaseId'] == LEASE_ID
            write_new(D / 'ledger-before-finally.json', release_before)
            if receipt['unknownCompletion']:
                final_lease.update(status='ATTENTION_REQUIRED', lastResult=str(D / 'dispatch-result.json'), scope='Unknown first Settings consumer completion. Preserve outputs and verify child/browser/server termination before release or retry.')
            else:
                final_lease.update(status='FREE', holder=None, currentCase=None, sessionId=None, finishedAtUtc=now(), completedCases=1 if known_complete else 0, lastResult=str(D / 'dispatch-result.json'))
            final_ledger['updatedAtUtc'] = now()
            replacement = D / 'ledger-finally.json'
            json_new(replacement, final_ledger)
            assert L.read_bytes() == release_before, 'Root ledger drift before finally'
            replacement.replace(L)
        print(json.dumps({'status': receipt['status'], 'receipt': str(D / 'dispatch-result.json'), 'unknownCompletion': receipt['unknownCompletion'], 'nodeComplete': False}), flush=True)
    return 0 if receipt.get('exitCode') == 0 and known_complete else 1

def positive_pid(value):
    if type(value)is not int or value<=0:raise ValueError('Positive actual owned PID required')
    return value


def census_rows(stdout):
    value=json.loads(stdout.decode('utf-8-sig'))if stdout.strip()else[]
    rows=value if isinstance(value,list)else[value]
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Unknown process census shape')
        positive_pid(row.get('ProcessId'))
    return rows


def probe_owned_endpoint(host,port,connect=None):
    if host not in('127.0.0.1','localhost')or type(port)is not int or not 0<port<65536:raise ValueError('Exact owned loopback endpoint required')
    connect=connect or socket.create_connection;started=time.monotonic()
    result={'host':host,'port':port,'timeoutSeconds':5,'closed':False}
    try:
        with connect(('127.0.0.1',port),timeout=5):result['result']='CONNECTED'
    except ConnectionRefusedError as error:result.update(result='CONNECTION_REFUSED',closed=True,errno=error.errno,winerror=getattr(error,'winerror',None),errorType=type(error).__name__)
    except OSError as error:result.update(result='UNRESOLVED_SOCKET_ERROR',errno=error.errno,winerror=getattr(error,'winerror',None),errorType=type(error).__name__)
    result['elapsedSeconds']=time.monotonic()-started;return result


def case_catalogue():
    return read(HERE / 'CASE_CONTRACTS.json')


def validate_evidence_transfer(base):
    # Reuse the sealed r4 source leg; this fixed main receiver adds no native credit.
    receiver = base['productionReceiver']
    assert receiver['schema'] == 'r0011-specific-main135-six-anchor-receiver/1'
    private = review_reference(receiver['privateBinding'])
    private_seal = review_reference(receiver['privatePacketSeal'])
    assert private_seal['files']['BINDING.json']['sha256'] == receiver['privateBinding']['sha256']
    assert private_seal['files']['RUN_PREPARED.py']['sha256'] == receiver['privateCarrier']['sha256']
    carrier_path = Path(receiver['privateCarrier']['path']).resolve()
    assert carrier_path == Path(receiver['privateBinding']['path']).resolve().with_name('RUN_PREPARED.py')
    carrier_raw = carrier_path.read_bytes()
    assert len(carrier_raw) == receiver['privateCarrier']['bytes'] and sha(carrier_raw) == receiver['privateCarrier']['sha256']
    report = review_reference(receiver['privateReview'])
    seal = review_reference(receiver['privateReviewSeal'])
    admission = review_reference(receiver['privateSourceAdmission'])
    assert seal['reportSha256'] == admission['reportSha256'] == receiver['privateReview']['sha256']
    assert admission['status'] == 'SCOPED_SOURCE_ADMISSION_PASS'
    assert admission['packetSealSha256'] == receiver['privatePacketSeal']['sha256']
    assert admission['carrierSha256'] == receiver['privateCarrier']['sha256']
    assert admission['runtimeSha256'] == private['sourceBinding']['runtimeSha256']
    assert admission['driverSha256'] == private['nativeReferences']['residual-location-actions.cjs']['sha256']
    assert report['allowedNextRootCaseIds'] == admission['allowedNextRootCaseIds'] == case_catalogue()['preparedCaseIds']
    assert report['reviewer'] == admission['reviewer'] and admission['reviewer'] not in ['/root/r0011_whole_owner', '/root/persistence_native', HERE.name]
    import types
    inherited = types.ModuleType('sealed_r4_source_equivalence_only')
    inherited.__file__ = str(carrier_path)
    exec(compile(carrier_raw, str(carrier_path), 'exec'), inherited.__dict__)
    retained_base, retained_catalogue = inherited.validate_evidence_transfer(private)
    assert base['evidenceTransfer'] == private['evidenceTransfer'] and base['acceptedPrefix'] == private['acceptedPrefix']
    for key in ['tools', 'toolBindingsSha256', 'priorPositive', 'priorIgnoreSave']:
        assert base[key] == private[key]
    assert base['caseContractsSha256'] == sha((HERE / 'CASE_CONTRACTS.json').read_bytes())
    build = review_reference(receiver['mainBuild'])
    assert build['schema'] == 'r0011-exact-current-main-guard-release-build/1'
    assert build['status'] == 'PASS_ISOLATED_CURRENT_MAIN_SOURCE19_DETERMINISTIC_GUARD_ONLY_BUILD_NO_NATIVE'
    assert build['base'] == '1536779492a4c687a6e3ebe6c56d72dd7e6ba968'
    assert build['correctedRoot'] == base['sourceRoot'] and Path(base['sourceRoot']).resolve().is_relative_to(RUN.resolve())
    assert build['changedRuntimeMembers'] == ['index.html', 'offline.html', 'real-sky/native-host-hooks.js']
    for key in ['baselineReproducesExactMain', 'guardedRepeatDeterministic', 'generatedEntriesOnlyExactHostReplacement', 'allOtherTrackedFilesIncludingREADMEUnchanged']:
        assert build[key] is True
    assert build['sourceTests19'] == 'PASS' and build['frozenV1'] == 'PASS_UNCHANGED'
    assert build['native'] == 'NOT_RUN' and build['nativeOrPixelTransferFromPrivate'] is False
    baseline = review_reference(receiver['mainBaselineRuntime'])
    runtime = review_reference(receiver['mainRuntime'])
    assert baseline['treeSha256'] == build['oldRuntimeSha256'] == 'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
    assert runtime['treeSha256'] == build['newRuntimeSha256'] == base['sourceBinding']['runtimeSha256']
    assert set(baseline['files']) == set(runtime['files']) and len(runtime['files']) == build['runtimeMemberCount'] == 135
    assert runtime['files'] == base['sourceBinding']['runtimeEntries']
    for identity in [baseline, runtime]:
        assert sha(''.join(v['sha256'] + '  ' + k + '\n' for k, v in sorted(identity['files'].items())).encode()) == identity['treeSha256']
    assert [k for k in sorted(runtime['files']) if runtime['files'][k] != baseline['files'][k]] == build['changedRuntimeMembers']
    old_hook = (Path(build['baselineRoot']) / 'real-sky/native-host-hooks.js').read_bytes()
    new_hook = (Path(base['sourceRoot']) / 'real-sky/native-host-hooks.js').read_bytes()
    assert old_hook == (Path(retained_base['sourceRoot']) / 'real-sky/native-host-hooks.js').read_bytes()
    assert new_hook == (Path(private['sourceRoot']) / 'real-sky/native-host-hooks.js').read_bytes()
    for root, identity in [(build['baselineRoot'], baseline), (base['sourceRoot'], runtime)]:
        for name in build['changedRuntimeMembers']:
            raw = (Path(root) / name).read_bytes()
            assert len(raw) == identity['files'][name]['bytes'] and sha(raw) == identity['files'][name]['sha256']
    for name in ['index.html', 'offline.html']:
        before = (Path(build['baselineRoot']) / name).read_bytes()
        after = (Path(base['sourceRoot']) / name).read_bytes()
        assert before.count(old_hook) == 1 and before.replace(old_hook, new_hook) == after
    pages = review_reference(receiver['mainPageAnchors'])
    assert len(pages['widget']['attrs']) == 6 and len(pages['builder']['attrs']) == 2
    expected = copy.deepcopy(private['sourceBinding'])
    expected.update(sourceRoot=base['sourceRoot'], sourceRef=build['base'],
        sourceRefMeaning='Exact153677 production base plus independently reviewed guard/test in disposable receiver; not yet committed/deployed',
        authoredIndexSha256='19dd9ba814fdb426b75e4282aca2e3bf20569b5b55ef9764d13e786c84c7b012',
        runtimeEntries=runtime['files'], runtimeFiles=sorted(runtime['files']), runtimeSha256=runtime['treeSha256'],
        buildReceipt=receiver['mainBuild']['path'], pages=pages)
    assert base['sourceBinding'] == expected
    for name in ['index.html', 'builder.html']:
        import re
        raw = (Path(base['sourceRoot']) / name).read_bytes()
        scripts = re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>', raw.decode(), re.I)
        key = 'widget' if name == 'index.html' else 'builder'
        assert pages[key] == {'sha': sha(raw), 'attrs': [a for a, _ in scripts], 'bodiesSha256': [sha(b.encode()) for _, b in scripts]}
    assert receiver['regionalSource'] == 'REGIONAL_MAIN_BINDING.json'
    region = read(HERE / receiver['regionalSource'])
    assert region['schema'] == 'r0011-exact-persistence-regions-main-binding/1'
    assert region['oldNativeSourceRoot'] == retained_base['sourceRoot'] and region['mainSourceRoot'] == base['sourceRoot'] and region['mainBase'] == build['base']
    assert region['oldNativeAndPixelEvidenceScope'] == 'ORIGINAL_E718_ONLY_NO_MAIN_PROMOTION'
    assert region['changedBootSceneStyleNativeCredit'] == 'PENDING_ACTUAL_REMAINING22' and region['acceptedNativeReplayed'] is False
    old_text = (Path(retained_base['sourceRoot']) / 'src/native/index.html').read_text(encoding='utf-8')
    main_raw = (Path(base['sourceRoot']) / 'src/native/index.html').read_bytes()
    assert sha(main_raw) == expected['authoredIndexSha256']
    generated = (Path(base['sourceRoot']) / 'index.html').read_text(encoding='utf-8')
    assert [row['name'] for row in region['sharedPersistenceSpans']] == list(private['sourceBinding']['sourceEquivalence'])
    for row in region['sharedPersistenceSpans']:
        original = private['sourceBinding']['sourceEquivalence'][row['name']]
        assert {k: row[k] for k in original} == original and row['oldEqualsMainAuthoredAndGenerated'] is True
        for text in [old_text, main_raw.decode(), generated]:
            start = text.index(row['start']); clip = text[start:text.index(row['end'], start)].encode()
            assert len(clip) == row['bytes'] and sha(clip) == row['sha256']
    assert [row['path'] for row in region['samePhysicalAndStorageModules']] == ['config.js', 'src/native/config.js', 'real-sky/native-contract.mjs', 'real-sky/native-preview.mjs', 'real-sky/native-lifecycle.mjs', 'real-sky/native-host.mjs']
    for row in region['samePhysicalAndStorageModules']:
        before = (Path(retained_base['sourceRoot']) / row['path']).read_bytes()
        after = (Path(base['sourceRoot']) / row['path']).read_bytes()
        assert before == after and len(after) == row['bytes'] and sha(after) == row['sha256']
    old_driver = (carrier_path.parent / 'native/residual-location-actions.cjs').read_bytes()
    new_driver = (HERE / 'native/residual-location-actions.cjs').read_bytes()
    assert len(old_driver) == private['nativeReferences']['residual-location-actions.cjs']['bytes'] and sha(old_driver) == private['nativeReferences']['residual-location-actions.cjs']['sha256']
    old_count, new_count = b'assert.equal(binding.pages.widget.attrs.length,4);', b'assert.equal(binding.pages.widget.attrs.length,6);'
    assert old_driver.count(old_count) == 1
    main_driver = old_driver.replace(old_count, new_count)
    correction = base['projectionCorrection']
    proposal = review_reference(correction['proposal'])
    subject = review_reference(correction['subjectSeal'])
    assert subject['files']['PROJECTION_PROPOSAL.json']['sha256'] == correction['proposal']['sha256']
    assert proposal['schema'] == 'r0011-nonoperative-nullable-active-config-consumer-proposal/1'
    assert proposal['changedClauseCount'] == 1 and proposal['assertionNameDetailAndAllOtherBytesUnchanged'] is True
    assert proposal['productSourceChanged'] is False
    assert proposal['from'] == 'before.config.lat===null&&before.config.lon===null'
    assert proposal['to'] == 'before.config===null&&before.app.config.lat===null&&before.app.config.lon===null'
    assert sha(main_driver) == proposal['preimage']['sha256'] == '5a13ab571cdcebf13579168d992f1703c32c31402b503f41203948a92d491207'
    assert main_driver == Path(proposal['preimage']['path']).read_bytes()
    before_clause, after_clause = proposal['from'].encode(), proposal['to'].encode()
    assert main_driver.count(before_clause) == 1 and main_driver.replace(before_clause, after_clause) == new_driver
    assert sha(new_driver) == proposal['proposed']['sha256'] == 'ef86c4f4fdd1bf074bb80d89bd64b9a634fbfcf03f445bae07d683112ed971bd'
    assert new_driver == Path(proposal['proposed']['path']).read_bytes()
    controls = review_reference(correction['controls'])
    assert subject['files']['PROJECTION_CONTROLS.json']['sha256'] == correction['controls']['sha256']
    assert controls['status'] == 'PASS_SOURCE_CONSUMER_CONTROLS_ONLY' and controls['controlCount'] == 8
    assert controls['newNativeBrowserRuns'] == 0 and controls['originalNativeAcceptanceConferred'] is False
    assert base['nativeReferences']['residual-location-actions.cjs']['sha256'] == sha(new_driver)
    assert base['nativeReferences']['residual-location-native.py'] == private['nativeReferences']['residual-location-native.py']
    for name, reference in base['nativeReferences'].items():
        raw = (HERE / 'native' / name).read_bytes()
        assert reference['path'] == 'native/' + name and len(raw) == reference['bytes'] and sha(raw) == reference['sha256']
    assert read(HERE / 'native/source-binding.json') == base['sourceBinding']
    current_catalogue = case_catalogue()
    inherited_catalogue = inherited.case_catalogue()
    assert current_catalogue['preparedCaseIds'] == inherited_catalogue['preparedCaseIds'] and current_catalogue['excludedCompletedIds'] == inherited_catalogue['excludedCompletedIds']
    for case_id in current_catalogue['preparedCaseIds']:
        before = copy.deepcopy(inherited_catalogue['cases'][case_id]); after = copy.deepcopy(current_catalogue['cases'][case_id])
        for key in ['fresh', 'sourceOverride']: before.pop(key); after.pop(key)
        assert before == after
    return retained_base, retained_catalogue


def case_binding(base, case_id):
    validate_evidence_transfer(base)
    catalogue = case_catalogue()
    assert case_id in catalogue['preparedCaseIds'], 'Unprepared or completed original case is not executable'
    contract = copy.deepcopy(catalogue['cases'][case_id])
    assert contract['prepared'] is True
    assert contract['recipe']['type'] in ['saveDenied', 'resetDenied', 'readFault', 'saveRecovery', 'resetSuccess']
    binding = dict(base)
    expected = copy.deepcopy(base['sourceBinding'])
    expected['pages']['widget'] = contract['sourceOverride']['widgetPage']
    expected['fixtureMutation'] = contract['sourceOverride']['fixtureMutation']
    binding.update(caseContract=contract, expectedTerminalSourceBinding=expected,
                   expectedMutation=contract['mutation'], freshRootIdentity=contract['fresh'])
    return binding


def select_context(base, case_id):
    global CASE, D, O, LEASE_ID
    binding = case_binding(base, case_id)
    CASE = case_id
    D = Path(binding['freshRootIdentity']['effectRoot'])
    O = Path(binding['freshRootIdentity']['nativeOutput'])
    LEASE_ID = binding['freshRootIdentity']['leaseId']
    return binding


def managed_census_command(launcher, owned_pid=None):
    explicit = '' if owned_pid is None else '$_.ProcessId -eq ' + str(positive_pid(owned_pid)) + ' -or '
    wrapper = str(Path(launcher)).replace('/', '\\').replace("'", "''")
    actions = str(Path(launcher).with_name('residual-location-actions.cjs')).replace('/', '\\').replace("'", "''")
    # The observer embeds the searched fragments; explicit owned PID still wins.
    predicate = "$_.ProcessId -gt 0 -and (" + explicit + "($_.ProcessId -ne $PID -and ($_.CommandLine -like '*" + wrapper + "*' -or $_.CommandLine -like '*" + actions + "*' -or ($_.Name -eq 'chrome.exe' -and $_.CommandLine -like '*playwright_chromiumdev_profile-*'))))"
    return "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); ConvertTo-Json -InputObject @((Get-CimInstance Win32_Process | Where-Object { " + predicate + " }) | Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath) -Depth 4 -Compress"


def managed_census(effect_root, launcher, phase, pid=None, runner=None):
    assert phase in ['PRE_NATIVE', 'POST_FRONTEND_BEFORE_RELEASE']
    if phase == 'POST_FRONTEND_BEFORE_RELEASE': positive_pid(pid)
    command = managed_census_command(launcher, pid)
    runner = runner or subprocess.run
    result = runner([read(HERE / 'BINDING.json')['tools']['powershell']['path'], '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, timeout=5)
    stem = 'prelaunch' if phase == 'PRE_NATIVE' else 'postflight'
    stdout = effect_root / (stem + '-managed-census.stdout')
    stderr = effect_root / (stem + '-managed-census.stderr')
    write_new(stdout, result.stdout)
    write_new(stderr, result.stderr)
    assert type(result.returncode) is int and result.returncode == 0 and result.stdout.strip() and result.stderr == b'', 'Actual explicit managed census required; empty/failed/diagnostic output is unknown'
    rows = census_rows(result.stdout)
    observation = {'schema': 'r0011-bounded-managed-process-observation/1', 'phase': phase,
        'observedAtUtc': now(), 'launcher': str(launcher), 'ownedLauncherPid': pid,
        'command': command, 'exitCode': result.returncode, 'rows': rows,
        'stdout': {'path': str(stdout), 'bytes': len(result.stdout), 'sha256': sha(result.stdout)},
        'stderr': {'path': str(stderr), 'bytes': len(result.stderr), 'sha256': sha(result.stderr)},
        'scope': 'Actual owned launcher PID, exact staged native Python/Node command fragments, and Playwright chromium profile command lines; not complete historical descendants or user Chrome',
        'completeHistoricalDescendantInventory': False, 'ownedEndpointInventory': 'NOT_RECORDED'}
    json_new(effect_root / (stem + '-managed-census.json'), observation)
    assert rows == [], 'Managed scope still occupied; no launch/known cleanup/queue advancement'
    return observation


def source_postflight(binding):
    source = Path(binding['sourceRoot'])
    for name, pin in binding['sourceBinding']['runtimeEntries'].items():
        raw = (source / name).read_bytes()
        assert len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'Postflight source drift: ' + name
    assert sha((source / 'src/native/index.html').read_bytes()) == binding['sourceBinding']['authoredIndexSha256']
    return {'schema': 'r0011-exact-source-postflight/1', 'status': 'PASS_SOURCE_CURRENT_BOUND_SCOPE',
        'observedAtUtc': now(), 'sourceRoot': binding['sourceRoot'], 'runtimeSha256': binding['sourceBinding']['runtimeSha256'],
        'runtimeEntriesVerified': len(binding['sourceBinding']['runtimeEntries']), 'authoredSha256': binding['sourceBinding']['authoredIndexSha256'],
        'cleanupClaim': False, 'current07Equivalent': False}


def observed_pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def capture_cleanup(binding, receipt, native_dir):
    positive_pid(receipt['processId'])
    managed_census(D, native_dir / 'residual-location-native.py', 'POST_FRONTEND_BEFORE_RELEASE', receipt['processId'])
    json_new(D / 'source-postflight.json', source_postflight(binding))
    cleanup = {'schema': 'r0011-rolling-known-cleanup/1', 'caseId': CASE, 'effectRoot': str(D),
        'nativeOutput': str(O), 'launcherPid': receipt['processId'], 'nativeStarted': receipt['nativeStarted'],
        'frontendWaitReturn': receipt['exitCode'], 'terminalSha256': receipt['resultsSha256'],
        'caseResultSha256': receipt['caseResultSha256'],
        'managedCensus': observed_pin(D / 'postflight-managed-census.json'),
        'sourcePostflight': observed_pin(D / 'source-postflight.json'),
        'ownedEndpointInventory': 'NOT_RECORDED', 'ownedEndpointProbes': [],
        'completeHistoricalDescendantInventory': False}
    json_new(D / 'rolling-cleanup.json', cleanup)
    receipt['actualBoundedCleanup'] = observed_pin(D / 'rolling-cleanup.json')
    receipt['cleanupLimits'] = 'Actual wrapper wait and managed-process readback plus pinned awaited browser/server terminal. No explicit endpoint inventory or complete historical descendants.'


def effect_reference(pin, root):
    assert isinstance(pin, dict) and set(pin) == {'path', 'bytes', 'sha256'}
    path = Path(pin['path']).resolve()
    assert path.is_relative_to(root.resolve())
    raw = path.read_bytes()
    assert len(raw) == pin['bytes'] and sha(raw) == pin['sha256']
    return raw


def validate_cleanup(cleanup, binding, dispatch):
    contract = binding['caseContract']
    root = Path(contract['fresh']['effectRoot'])
    assert cleanup['schema'] == 'r0011-rolling-known-cleanup/1'
    assert cleanup['caseId'] == contract['id'] and cleanup['effectRoot'] == str(root)
    assert cleanup['nativeOutput'] == contract['fresh']['nativeOutput']
    pid = positive_pid(cleanup['launcherPid'])
    assert pid == dispatch['processId'] and cleanup['frontendWaitReturn'] == dispatch['exitCode']
    assert cleanup['nativeStarted'] is dispatch['nativeStarted'] is True
    assert cleanup['terminalSha256'] == dispatch['resultsSha256'] and cleanup['caseResultSha256'] == dispatch['caseResultSha256']
    managed = json.loads(effect_reference(cleanup['managedCensus'], root))
    assert managed['phase'] == 'POST_FRONTEND_BEFORE_RELEASE' and managed['ownedLauncherPid'] == pid and managed['exitCode'] == 0
    assert managed['launcher'] == str(root / 'native/residual-location-native.py')
    assert managed['command'] == managed_census_command(root / 'native/residual-location-native.py', pid)
    stdout = effect_reference(managed['stdout'], root)
    assert stdout.strip() and census_rows(stdout) == managed['rows'] == []
    assert effect_reference(managed['stderr'], root) == b''
    observed = dt.datetime.fromisoformat(managed['observedAtUtc'])
    assert dt.datetime.fromisoformat(dispatch['startedAtUtc']) <= observed <= dt.datetime.fromisoformat(dispatch['finishedAtUtc'])
    source = json.loads(effect_reference(cleanup['sourcePostflight'], root))
    assert source['status'] == 'PASS_SOURCE_CURRENT_BOUND_SCOPE' and source['sourceRoot'] == binding['sourceRoot']
    assert source['runtimeSha256'] == binding['sourceBinding']['runtimeSha256'] and source['runtimeEntriesVerified'] == len(binding['sourceBinding']['runtimeEntries'])
    assert cleanup['ownedEndpointInventory'] == 'NOT_RECORDED' and cleanup['ownedEndpointProbes'] == []
    assert cleanup['completeHistoricalDescendantInventory'] is False
    return True


def validate_previous_completion(path, binding, approval, packet_seal):
    allowed = approval['allowedCaseIds']
    index = allowed.index(CASE)
    if index == 0:
        assert CASE == 'top-read-getter' and path is None, 'First remaining case requires exact accepted-prefix bridge; no replay or predecessor bypass'
        retained_base, retained_catalogue = validate_evidence_transfer(binding)
        prefix = binding['acceptedPrefix']
        report = review_reference(prefix['report'])
        seal = review_reference(prefix['seal'])
        old_seal = review_reference(prefix['originalPacketSeal'])
        old_catalogue = review_reference(prefix['originalContracts'])
        old_base = review_reference(prefix['originalBinding'])
        catalogue = case_catalogue()
        assert report['schema'] == 'r0011-independent-actual-batch-and-open-only-source-review/1'
        assert report['status'] == 'PASS_SCOPED_ACTUAL8_AND_PROSPECTIVE_OPEN_CORRECTION_WITH_RESET_FAIL_PRESERVED'
        assert seal['reportSha256'] == prefix['report']['sha256']
        assert report['reviewer'] == prefix['reviewer'] and report['reviewer'] not in ['/root/r0011_whole_owner', '/root/persistence_native', HERE.name]
        assert report['acceptedCaseIds'] == prefix['caseIds'] == old_catalogue['preparedCaseIds'][:8]
        assert len(prefix['caseIds']) == 8 and len(set(prefix['caseIds'])) == 8
        assert report['remainingCaseIds'] == old_catalogue['preparedCaseIds'][8:]
        assert catalogue['preparedCaseIds'] == report['remainingCaseIds'][1:]
        assert CASE == catalogue['preparedCaseIds'][0] and not set(prefix['caseIds']) & set(catalogue['preparedCaseIds'])
        assert set(catalogue['excludedCompletedIds']) == set(old_catalogue['excludedCompletedIds'] + prefix['caseIds'] + ['top-reset-denied'])
        assert report['qualifiedAncestry']['preparedSeal'] == prefix['originalPacketSeal']
        assert report['qualifiedAncestry']['caseContracts'] == prefix['originalContracts']
        assert old_seal['files']['RUN_PREPARED.py']['sha256'] == prefix['originalCarrierSha256']
        assert old_base['sourceRoot'] == retained_base['sourceRoot'] and old_base['sourceBinding'] == retained_base['sourceBinding']
        correction = report['boundedSourceCorrection']
        assert correction['verdict'] == 'PASS_EXACT_OPEN_ONLY_PROSPECTIVE_SOURCE'
        assert correction['driver']['sha256'] == review_reference(binding['productionReceiver']['privateBinding'])['nativeReferences']['residual-location-actions.cjs']['sha256']
        assert correction['allOtherDriverBytesIdentical'] is True and correction['original10000msWaitAndNativeKeyboardAssertionsUnchanged'] is True
        assert correction['correctionAddsFocusCalls'] is False and correction['sourceRuntimeProductChanges'] == 0
        old_driver = old_base['nativeReferences']['residual-location-actions.cjs']['sha256']
        assert report['exactSourcePins']['actualNativeDriver']['sha256'] == old_driver
        assert report['exactSourcePins']['runtimeSha256'] == retained_base['sourceBinding']['runtimeSha256']
        assert [row['caseId'] for row in report['perCaseEvidence']] == prefix['caseIds'] + ['top-reset-denied']
        failed = report['perCaseEvidence'][-1]
        assert failed['rawNativeStatus'] == 'FAIL' and failed['acceptedOriginalNativeContext'] is False
        assert review_reference(failed['caseResult'])['status'] == 'FAIL', 'Partial reset is retained adverse evidence, never the accepted prefix'
        accepted_proofs = report['perCaseEvidence'][:-1]
        for proof in accepted_proofs:
            contract = copy.deepcopy(old_catalogue['cases'][proof['caseId']])
            root = Path(contract['fresh']['effectRoot'])
            output = Path(contract['fresh']['nativeOutput'])
            expected_paths = {'caseResult': output / contract['id'] / 'result.json', 'dispatch': root / 'dispatch-result.json',
                              'terminal': output / 'results.json', 'cleanup': root / 'rolling-cleanup.json'}
            observed = {}
            for key, expected_path in expected_paths.items():
                assert Path(proof[key]['path']).resolve() == expected_path.resolve()
                observed[key] = review_reference(proof[key])
            assert proof['acceptedOriginalNativeContext'] is True and proof['nativeKnownComplete'] is True and proof['cleanupAcceptedWithinOriginalScope'] is True
            assert proof['trace']['verdict'] == 'PASS_ORIGINAL_SELECTED_PREDICATES' and proof['trace']['caseResult'] == proof['caseResult']
            assert proof['pixelVerdict'] == 'PASS_SELECTED_STORAGE_WARNING_LAYOUT_SCOPE'
            expected = copy.deepcopy(old_base['sourceBinding'])
            expected['pages']['widget'] = contract['sourceOverride']['widgetPage']
            expected['fixtureMutation'] = contract['sourceOverride']['fixtureMutation']
            prior = dict(old_base, caseContract=contract, expectedTerminalSourceBinding=expected,
                         expectedMutation=contract['mutation'], freshRootIdentity=contract['fresh'])
            dispatch = observed['dispatch']
            assert dispatch['packetSealSha256'] == prefix['originalPacketSeal']['sha256']
            assert dispatch['caseContractsSha256'] == prefix['originalContracts']['sha256']
            assert dispatch['rootDriverSha256'] == prefix['originalCarrierSha256'] and dispatch['nativeDriverSha256'] == old_driver
            assert dispatch['onlyCase'] == contract['id'] and dispatch['nativeComplete'] is True and dispatch['unknownCompletion'] is False
            assert dispatch['sourceRuntime'] == retained_base['sourceBinding']['runtimeSha256']
            status = validate_native_terminal(prior, contract['recipe'], dispatch['exitCode'], {})
            assert status == contract['expectedStatus'] == proof['rawNativeStatus'] == dispatch['consumerStatus']
            validate_cleanup(observed['cleanup'], prior, dispatch)
            crops = {Path(row['file']).stem: row for row in observed['caseResult']['crops']}
            assert [row['label'] for row in proof['pixelPins']] == list(crops)
            for crop in proof['pixelPins']:
                raw_crop = crops[crop['label']]
                assert set(crop['files']) == {key for key in raw_crop if key == 'file' or key.endswith('File')}
                for key, reference in crop['files'].items():
                    assert Path(reference['path']).resolve() == Path(raw_crop[key]).resolve()
                    effect_reference({name: reference[name] for name in ['path', 'bytes', 'sha256']}, root)
        validate_reset_positive_review(binding['evidenceTransfer']['resetPositive'], binding, packet_seal)
        retained_review = review_reference(binding['evidenceTransfer']['resetReport'])
        failed_getter = retained_review['getterFailureDecision']
        assert failed_getter['caseId'] == 'top-read-getter' and failed_getter['originalChecksObserved'] == 0
        assert review_reference(failed_getter['caseResult'])['status'] == 'FAIL'
        assert review_reference(failed_getter['dispatchResult'])['unknownCompletion'] is False
        return
    assert path is not None, 'Actual successful predecessor/cleanup required before advancing'
    previous = case_binding(read(HERE / 'BINDING.json'), allowed[index - 1])
    root = Path(previous['freshRootIdentity']['effectRoot'])
    assert path.resolve() == (root / 'rolling-cleanup.json').resolve()
    dispatch = read(root / 'dispatch-result.json')
    assert dispatch['packetSealSha256'] == packet_seal and dispatch['onlyCase'] == previous['caseContract']['id']
    assert dispatch['leaseId'] == previous['freshRootIdentity']['leaseId']
    assert dispatch['effectRoot'] == str(root) and dispatch['nativeOutput'] == previous['freshRootIdentity']['nativeOutput']
    assert dispatch['sourceRuntime'] == binding['sourceBinding']['runtimeSha256']
    assert dispatch['nativeDriverSha256'] == binding['nativeReferences']['residual-location-actions.cjs']['sha256']
    assert dispatch['nativeComplete'] is True and dispatch['unknownCompletion'] is False
    status = validate_native_terminal(previous, previous['caseContract']['recipe'], dispatch['exitCode'], {})
    assert status == previous['caseContract']['expectedStatus'], 'FAIL or unknown predecessor stops this rolling queue'
    assert dispatch['consumerStatus'] == status
    validate_cleanup(read(path), previous, dispatch)




def validate_case_prerequisites(row, contract):
    # These are the original producer's named demands, not substitute success predicates.
    names = [check['name'] for check in row['checks']]
    assert names == contract['expectedCheckNames'], 'Complete exact source-shaped assertion order/count required'
    prerequisite = contract['prerequisite']
    required = prerequisite.get('checks', [])
    if prerequisite.get('check'):
        required = required + [prerequisite['check']]
    if prerequisite.get('deniedOperationCheck'):
        required = required + [prerequisite['deniedOperationCheck']]
    for name in required:
        reached = [check for check in row['checks'] if check['name'] == name]
        assert len(reached) == 1 and reached[0]['passed'] is True, 'Missing/failed original prerequisite: ' + name
    if contract['type'] in ['saveDenied', 'resetDenied']:
        assert row.get('mutantReached') is True, 'Successful denied-storage terminal requires the actual selected fault'


def validate_reset_positive_review(pin, base, packet_seal):
    # The exact accepted reset stays on its r3/e718 identity; source equivalence is separate.
    retained_base, retained_catalogue = validate_evidence_transfer(base)
    transfer = base['evidenceTransfer']
    assert pin == transfer['resetPositive'], 'Only the exact independently accepted original reset receipt may be consumed'
    review = review_reference(pin)
    assert review['schema'] == 'r0011-original-reset-positive-independent-review/1'
    assert review['status'] == 'ACTUAL_RESET_POSITIVE_ACCEPTED'
    assert review['reviewer'] not in ['/root/r0011_whole_owner', '/root/persistence_native', HERE.name]
    assert isinstance(review['reviewer'], str) and review['reviewer'].strip()
    assert review['packetSealSha256'] == transfer['oldPacketSeal']['sha256']
    assert review['runtimeSha256'] == retained_base['sourceBinding']['runtimeSha256']
    assert review['driverSha256'] == retained_base['nativeReferences']['residual-location-actions.cjs']['sha256']
    assert review['caseContractsSha256'] == transfer['oldContracts']['sha256'] and review['carrierSha256'] == transfer['oldCarrier']['sha256']
    assert review['caseId'] == 'top-reset-denied'
    contract = copy.deepcopy(retained_catalogue['cases'][review['caseId']])
    expected = copy.deepcopy(retained_base['sourceBinding'])
    expected['pages']['widget'] = contract['sourceOverride']['widgetPage']
    expected['fixtureMutation'] = contract['sourceOverride']['fixtureMutation']
    positive = dict(retained_base, caseContract=contract, expectedTerminalSourceBinding=expected,
                    expectedMutation=contract['mutation'], freshRootIdentity=contract['fresh'])
    root = Path(positive['freshRootIdentity']['effectRoot'])
    actual = review_reference(review['caseResult'])
    assert Path(review['caseResult']['path']).resolve() == (Path(positive['freshRootIdentity']['nativeOutput']) / review['caseId'] / 'result.json').resolve()
    dispatch = review_reference(review['dispatchResult'])
    assert Path(review['dispatchResult']['path']).resolve() == (root / 'dispatch-result.json').resolve()
    assert dispatch['packetSealSha256'] == transfer['oldPacketSeal']['sha256'] and dispatch['onlyCase'] == review['caseId']
    assert dispatch['caseContractsSha256'] == transfer['oldContracts']['sha256'] and dispatch['rootDriverSha256'] == transfer['oldCarrier']['sha256']
    assert dispatch['nativeDriverSha256'] == review['driverSha256'] and dispatch['sourceRuntime'] == review['runtimeSha256']
    assert dispatch['nativeStarted'] is True and dispatch['nativeComplete'] is True and dispatch['unknownCompletion'] is False
    assert actual['status'] == 'PASS' and actual.get('mutant') is None
    assert actual['runtimeSha256'] == retained_base['sourceBinding']['runtimeSha256']
    assert actual['sourceBinding'] == positive['expectedTerminalSourceBinding']
    validate_case_prerequisites(actual, positive['caseContract'])
    assert all(check['passed'] is True for check in actual['checks'])
    assert actual['native']['os'] == 'win32' and actual['native']['browser'] == 'chromium'
    assert review['traceVerdict'] == 'PASS' and review['pixelVerdict'] == 'PASS'
    assert dispatch['caseResultSha256'] == review['caseResult']['sha256']
    assert validate_native_terminal(positive, contract['recipe'], dispatch['exitCode'], {}) == 'PASS'
    assert Path(review['terminal']['path']).resolve() == (Path(contract['fresh']['nativeOutput']) / 'results.json').resolve()
    review_reference(review['terminal'])
    assert Path(review['cleanup']['path']).resolve() == (root / 'rolling-cleanup.json').resolve()
    cleanup = review_reference(review['cleanup'])
    validate_cleanup(cleanup, positive, dispatch)
    crops = {Path(row['file']).stem: row for row in actual['crops']}
    assert [row['label'] for row in review['pixels']] == list(crops)
    for crop in review['pixels']:
        raw_crop = crops[crop['label']]
        assert crop['actuallyViewedAllOriginalFiles'] is True
        assert set(crop['files']) == {key for key in raw_crop if key == 'file' or key.endswith('File')}
        for key, reference in crop['files'].items():
            assert Path(reference['path']).resolve() == Path(raw_crop[key]).resolve()
            effect_reference({name: reference[name] for name in ['path', 'bytes', 'sha256']}, root)
    return review['reviewer']


if __name__ == '__main__':
    raise SystemExit(main())
