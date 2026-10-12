"""Root-only proposal: one widget-positive case, externally guarded before Python output."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess

W = Path(__file__).resolve().parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda path: json.loads(path.read_bytes())
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def require(value, message):
    if not value: raise ValueError(message)
def save(path, value): path.write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))
def fresh_no_output(output, accounting=None):
    # No logging, mkdir, metadata, ledger write or child call before this test.
    require(not os.path.lexists(output), 'occupied metadata output; preserve it and use a distinct reviewed attempt')
    if accounting is not None: require(not os.path.lexists(accounting), 'occupied dispatch accounting; preserve it')
def verify_sealed(root, expected):
    raw = (root / 'SEAL.json').read_bytes(); require(sha(raw) == expected, 'seal drift: ' + str(root))
    seal = json.loads(raw); files = seal['files']
    if isinstance(files, dict): files = [{'path': name, **entry} for name, entry in files.items()]
    for entry in files:
        file = (root / entry['path']).resolve(); require(file.is_relative_to(root.resolve()), 'unsafe sealed path')
        raw = file.read_bytes(); require(len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], 'sealed file drift: ' + str(file))
    return seal
def compare_write(path, expected, value):
    require(path.read_bytes() == expected, 'ledger byte drift; refusing overwrite')
    save(path, value)
def node(ledger): return next(row for row in ledger['nodes'] if row['id'] == 'R0023-METADATA')
def transaction(command, cwd, output, accounting, ledger_path, lease_id, runner, scope, bindings=None):
    fresh_no_output(output, accounting)
    before = ledger_path.read_bytes(); ledger = json.loads(before); lease = ledger['resourceLeases']['heavy-browser']
    require(lease['capacity'] == 1 and lease['status'] == 'FREE' and lease['holder'] is None, 'exclusive capacity1 unavailable')
    require(lease_id and lease_id != lease.get('leaseId'), 'fresh root lease ID required')
    accounting.parent.mkdir(parents=True, exist_ok=True); accounting.mkdir()
    (accounting / 'ACTIVE_LEDGER.before.json').write_bytes(before)
    receipt = {'schema': 'root-r0023-metadata-single-dispatch/v1', 'atUtc': now(), 'status': 'CLAIM_PENDING',
               'scope': scope, 'command': command, 'output': str(output), 'leaseId': lease_id,
               'case': 'widget-positive', 'selectedCases': 1, 'automaticRetries': 0, 'nodeCredit': False,
               'freshBeforeAnyPythonOutput': True, 'standaloneDriverOverwriteGuard': 'ABSENT_UNCHANGED',
               'childCompletion': 'NOT_STARTED'}
    child_completion = 'NOT_STARTED'
    lease.update(bindings or {})
    lease.pop('finishedAtUtc', None); lease.pop('processId', None); lease.pop('attentionAtUtc', None)
    lease.update(status='ACTIVE', holder='root', leaseId=lease_id, startedAtUtc=now(), command=command[4],
                 scope='R0023-METADATA original widget-positive only; exclusive output writer, no remaining56 or policy.',
                 currentCase='widget-positive', sessionId=None, completedCases=0, totalCases=1,
                 childCompletion=child_completion, attentionRequired=False)
    node(ledger)['progress'].update(state='EXECUTING', exitCriteriaVerified=False, owners=['root'],
                                   reason='One guarded reviewed metadata lifecycle attempt; native/raw/pixel acceptance remains pending.')
    ledger['updatedAtUtc'] = now()
    path = accounting / 'dispatch.json'
    try: compare_write(ledger_path, before, ledger)
    except BaseException as error:
        receipt.update(status='CLAIM_REFUSED_NO_CHILD', error=repr(error)); save(path, receipt); raise
    try:
        receipt['status'] = 'COMMAND_ATTEMPT_PENDING'; save(path, receipt)
        # Immediately precedes the original Python front door. Root's sole writer
        # must prevent another claimant between this read and child invocation.
        fresh_no_output(output)
        receipt['freshImmediatelyBeforeFrontDoor'] = True
        # A start/Popen failure can itself leave child existence uncertain.
        # Enter uncertainty before crossing the runner's effect boundary.
        child_completion = receipt['childCompletion'] = 'COMPLETION_UNKNOWN'
        result = runner(command, cwd, accounting / 'stdout.log', accounting / 'stderr.log')
        if type(getattr(result, 'pid', None)) is int and result.pid > 0: receipt['processId'] = result.pid
        require(type(getattr(result, 'returncode', None)) is int and getattr(result, 'chainCompletion', None) == 'TERMINAL',
                'original chain completion unknown; root process/descendant readback required')
        child_completion = receipt['childCompletion'] = 'TERMINAL'
        if hasattr(result, 'cleanupReceipt'): receipt['chainCleanupReceipt'] = result.cleanupReceipt
        receipt.update(status='RETURNED_ACTUAL_CONSUMER_REVIEW_REQUIRED', exitCode=result.returncode)
        receipt['files'] = [{'path': file.relative_to(output).as_posix(), 'bytes': file.stat().st_size, 'sha256': sha(file.read_bytes())}
                            for file in output.rglob('*') if file.is_file()] if output.exists() else []
        return receipt
    except BaseException as error:
        if type(getattr(error, 'pid', None)) is int and error.pid > 0: receipt['processId'] = error.pid
        receipt.update(status='ATTEMPT_REFUSED_OR_EXCEPTION_READBACK_REQUIRED', error=repr(error)); raise
    finally:
        if child_completion != 'COMPLETION_UNKNOWN': receipt['finishedAtUtc'] = now()
        else: receipt['attentionAtUtc'] = now()
        try:
            before_release = ledger_path.read_bytes(); current = json.loads(before_release); held = current['resourceLeases']['heavy-browser']
            require(held['holder'] == 'root' and held['status'] == 'ACTIVE' and held['leaseId'] == lease_id, 'ownership changed; no release of another holder')
            held.update(childCompletion=child_completion, lastResult=str(path))
            progress = node(current)['progress']
            if child_completion == 'COMPLETION_UNKNOWN':
                held.update(attentionRequired=True, attentionAtUtc=now())
                if 'processId' in receipt: held['processId'] = receipt['processId']
                progress.update(state='ATTENTION_REQUIRED', exitCriteriaVerified=False,
                    reason='Original child/descendant completion unknown. Preserve ACTIVE capacity and partial output; root process readback required before release or any retry.')
                receipt['capacityRelease'] = 'RETAINED_OWN_ACTIVE_COMPLETION_UNKNOWN'
            else:
                held.update(holder=None, status='FREE', currentCase=None, sessionId=None, finishedAtUtc=now(), attentionRequired=False)
                progress.update(state='AWAITING_REVIEW', exitCriteriaVerified=False,
                    reason='Guarded widget-positive chain terminal or proven not started; exact raw/environment/crop review required before distinct remaining56.')
                receipt['capacityRelease'] = 'RELEASED_OWN_MATCHING_LEASE'
            progress['evidence'] = list(dict.fromkeys(progress.get('evidence', []) + [str(path)])); current['updatedAtUtc'] = now()
            compare_write(ledger_path, before_release, current)
        except BaseException as error:
            receipt['capacityRelease'] = 'REFUSED_ROOT_READBACK_REQUIRED'; receipt['releaseError'] = repr(error); raise
        finally: save(path, receipt)
def runner(command, cwd, stdout, stderr):
    with stdout.open('wb') as out, stderr.open('wb') as err: result = subprocess.run(command, cwd=cwd, stdout=out, stderr=err)
    # Exact retained CJS writes this receipt only after awaited browser/server
    # finally cleanup. Parent process exit alone cannot establish that chain.
    require(type(getattr(result, 'returncode', None)) is int and result.returncode in (0, 1), 'original chain return lacks cleanup proof')
    output = Path(command[command.index('--out') + 1]); receipt_path = output / 'results.json'
    raw = receipt_path.read_bytes(); chain = json.loads(raw)
    require(chain.get('schema') == 'residual-native-results/v1' and chain.get('group') == 'r0023-metadata'
            and chain.get('sourceRef') == command[command.index('--source-ref') + 1]
            and chain.get('selected') == ['widget-positive'] and chain.get('notRun') == [], 'wrong original cleanup receipt identity')
    executed = chain.get('executed', [])
    require(len(executed) == 1 and executed[0].get('name') == 'widget-positive'
            and executed[0].get('status') == ('PASS' if result.returncode == 0 else 'FAIL')
            and Path(executed[0]['result']).resolve() == (output / 'widget-positive/result.json').resolve(), 'original cleanup receipt is not terminal for this case')
    result.chainCompletion = 'TERMINAL'
    result.cleanupReceipt = {'path': str(receipt_path), 'sha256': sha(raw), 'basis': 'EXACT_RETAINED_CJS_RECEIPT_AFTER_AWAITED_FINALLY',
                             'nativeAcceptance': False}
    return result
def execute(plan, args):
    output, accounting = Path(plan['output']), Path(plan['accounting'])
    fresh_no_output(output, accounting)
    require(args.expected_seal and args.admission and args.capacity_lease and args.lease_id,
            'actual root admission/lease/ID and exact proposal seal required')
    verify_sealed(W, args.expected_seal)
    for identity in plan['inputsSealed']: verify_sealed(Path(identity['path']), identity['sealSha256'])
    C = Path(plan['sourceRoot']); records = []
    for rel, entry in plan['runtimeFiles'].items():
        file = (C / rel).resolve(); require(file.is_relative_to(C.resolve()), 'runtime path escape')
        raw = file.read_bytes(); require(len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], 'runtime drift: ' + rel)
        records.append(entry['sha256'] + '  ' + rel + '\n')
    require(len(records) == 139 and sha(''.join(records).encode()) == plan['runtimeTreeSha256'], 'wrong e718 inventory')
    for rel, expected in plan['sourceFiles'].items(): require(sha((C / rel).read_bytes()) == expected, 'source drift: ' + rel)
    for entry in plan['toolIdentities'].values():
        file = Path(entry['path']); require(file.is_file() and file.stat().st_size == entry['bytes'] and sha(file.read_bytes()) == entry['sha256'], 'tool drift: ' + str(file))
    admission, capacity = read(args.admission), read(args.capacity_lease)
    for key, expected in plan['admissionRequiredFields'].items(): require(admission.get(key) == expected, 'admission mismatch: ' + key)
    for key, expected in plan['capacityRequiredFields'].items(): require(capacity.get(key) == expected, 'capacity mismatch: ' + key)
    require(capacity.get('leaseId') == args.lease_id and capacity.get('dispatchSealSha256') == args.expected_seal, 'wrong real lease/seal binding')
    require(capacity.get('admissionSha256') == sha(args.admission.read_bytes()), 'lease does not bind actual admission')
    expiry = dt.datetime.fromisoformat(capacity['expiresAtUtc'].replace('Z', '+00:00'))
    require(expiry.tzinfo is not None and expiry > dt.datetime.now(dt.timezone.utc), 'expired/unzoned lease')
    require(output.parent.resolve() == (W / 'native').resolve() and accounting.resolve().is_relative_to(Path(plan['runRoot']) / 'evidence/R0023'), 'wrong output scope')
    descriptor = next(row for row in read(W / 'native/CASE_REGISTRY.json')['cases'] if row['name'] == 'widget-positive')
    bindings = {'sourceCommit': admission['sourceRefProvenance'], 'runtimeSha256': plan['runtimeTreeSha256'],
                'sourceRoot': plan['sourceRoot'], 'sourceFiles': plan['sourceFiles'], 'engine': 'chromium', 'outputPath': str(output),
                'caseSha256': sha(json.dumps(descriptor, sort_keys=True, separators=(',', ':')).encode()),
                'caseHashScope': 'canonical retained widget-positive CASE_REGISTRY descriptor',
                'privatePacketSha256': plan['privatePacketSha256'], 'dispatchSealSha256': args.expected_seal,
                'admissionSha256': capacity['admissionSha256'], 'expiresAtUtc': capacity['expiresAtUtc']}
    return transaction(plan['argv'], W, output, accounting, Path(plan['runRoot']) / 'ACTIVE_LEDGER.json', args.lease_id,
                       runner, 'ACTUAL_ROOT_METADATA_ONE_CASE_ATTEMPT_NOT_QUALIFICATION', bindings)
def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--execute', action='store_true'); p.add_argument('--expected-seal')
    p.add_argument('--admission', type=Path); p.add_argument('--capacity-lease', type=Path); p.add_argument('--lease-id'); args = p.parse_args()
    plan = read(W / 'ROOT_COMMAND.json'); fresh_no_output(Path(plan['output']), Path(plan['accounting']))
    if not args.execute:
        print(json.dumps({'status': 'PROPOSED_NOT_EXECUTED', 'argv': plan['argv'], 'native': 'NOT_RUN'})); return 0
    receipt = execute(plan, args); print(json.dumps({'status': receipt['status'], 'exitCode': receipt.get('exitCode'),
                                                   'capacityRelease': receipt['capacityRelease'], 'nodeCredit': False}))
    return receipt.get('exitCode', 1)
if __name__ == '__main__': raise SystemExit(main())
