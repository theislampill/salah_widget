"""Root-only original remaining56 metadata batch; no accepted first-case replay."""
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
    seal = json.loads(raw)
    if 'files' in seal: files = seal['files']
    else:
        manifest_raw = (root/'MANIFEST.json').read_bytes()
        require(sha(manifest_raw) == seal['manifestSha256'], 'manifest drift')
        manifest = json.loads(manifest_raw); files = manifest['files']
        require(len(files) == seal['declaredFiles'] and sha((root/'REPORT.json').read_bytes()) == seal['reportSha256'], 'manifest/report association differs')
        require({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} == {r['path'] for r in files}|{'MANIFEST.json','SEAL.json'}, 'immutable review population differs')
    if isinstance(files, dict): files = [{'path': name, **entry} for name, entry in files.items()]
    for entry in files:
        file = (root / entry['path']).resolve(); require(file.is_relative_to(root.resolve()), 'unsafe sealed path')
        raw = file.read_bytes(); require(len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], 'sealed file drift: ' + str(file))
    if root.resolve() == W.resolve():
        require(seal['rootExecutionOutputsExcluded'] == ['native/root-native-remaining56-r1'], 'only exact future native output may be excluded')
        present = {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file()} - {'SEAL.json'}
        present = {name for name in present if not name.startswith('native/root-native-remaining56-r1/')}
        require(present == {entry['path'] for entry in files}, 'unexpected owned source population')
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
    receipt = {'schema': 'root-r0023-metadata-remaining56-dispatch/v1', 'atUtc': now(), 'status': 'CLAIM_PENDING',
               'scope': scope, 'command': command, 'output': str(output), 'leaseId': lease_id,
               'bodyKey': 'chromium:metadata:remaining56', 'caseNames': read(W/'ROOT_COMMAND.json')['selectedCases'], 'selectedCases': 56, 'automaticRetries': 0, 'nodeCredit': False,
               'freshBeforeAnyPythonOutput': True, 'standaloneDriverOverwriteGuard': 'ABSENT_UNCHANGED',
               'childCompletion': 'NOT_STARTED'}
    child_completion = 'NOT_STARTED'
    lease.update(bindings or {})
    lease.pop('finishedAtUtc', None); lease.pop('processId', None); lease.pop('attentionAtUtc', None)
    lease.update(status='ACTIVE', holder='root', leaseId=lease_id, startedAtUtc=now(), command=command[4],
                 scope='R0023-METADATA original remaining56 only; exclusive output writer, first accepted case retained, no policy.',
                 currentCase='ORIGINAL_ORDERED_REMAINING56_BATCH', sessionId=None, completedCases=0, totalCases=56,
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
                    reason='Guarded original remaining56 chain terminal or proven not started; raw partial/full expected/observed and independent pixel review required before closure.')
                receipt['capacityRelease'] = 'RELEASED_OWN_MATCHING_LEASE'
            progress['evidence'] = list(dict.fromkeys(progress.get('evidence', []) + [str(path)])); current['updatedAtUtc'] = now()
            compare_write(ledger_path, before_release, current)
        except BaseException as error:
            receipt['capacityRelease'] = 'REFUSED_ROOT_READBACK_REQUIRED'; receipt['releaseError'] = repr(error); raise
        finally: save(path, receipt)
def terminal_chain(command, returncode, chain):
    # The unchanged original CJS writes results only after awaited finally.
    plan = read(W/'ROOT_COMMAND.json')
    selected = plan['selectedCases']
    output = Path(command[command.index('--out') + 1])
    require(type(returncode) is int and returncode in (0, 1), 'original chain return lacks cleanup proof')
    require(chain.get('schema') == 'residual-native-results/v1' and chain.get('group') == 'r0023-metadata'
            and chain.get('sourceRef') == command[command.index('--source-ref') + 1]
            and chain.get('selected') == selected, 'wrong original batch cleanup identity')
    executed = chain.get('executed', [])
    require(executed and [r.get('name') for r in executed] == selected[:len(executed)]
            and chain.get('notRun') == selected[len(executed):], 'original stop-on-failure prefix/suffix differs')
    descriptors = {r['name']: r for r in read(W/'native/CASE_REGISTRY.json')['cases']}
    for index, row in enumerate(executed):
        name = row['name']
        require(Path(row['result']).resolve() == (output/name/'result.json').resolve(), 'foreign batch case receipt')
        expected = 'CAUGHT' if descriptors[name].get('mutant') else 'PASS'
        require(row['status'] == expected or (returncode == 1 and index == len(executed)-1 and row['status'] == 'FAIL'), 'unexpected original case/control status')
    require((returncode == 0 and len(executed) == 56 and not chain['notRun'] and executed[-1]['status'] != 'FAIL')
            or (returncode == 1 and executed[-1]['status'] == 'FAIL'), 'batch exit/status/stop association differs')
    return {'executedCases': len(executed), 'notRunCases': len(chain['notRun']), 'unexpectedFailureRetained': returncode == 1, 'expectedCaughtMutants': [r['name'] for r in executed if r['status'] == 'CAUGHT']}

def runner(command, cwd, stdout, stderr):
    with stdout.open('wb') as out, stderr.open('wb') as err: result = subprocess.run(command, cwd=cwd, stdout=out, stderr=err)
    output = Path(command[command.index('--out') + 1]); receipt_path = output/'results.json'
    raw = receipt_path.read_bytes(); chain = json.loads(raw)
    association = terminal_chain(command, result.returncode, chain)
    result.chainCompletion = 'TERMINAL'
    result.cleanupReceipt = {'path': str(receipt_path), 'sha256': sha(raw), 'basis': 'EXACT_RETAINED_CJS_RECEIPT_AFTER_AWAITED_FINALLY', 'nativeAcceptance': False, **association}
    return result

def binding(plan, require_first=True):
    old_root = W.parent/'location_metadata_root_dispatch_r2'
    require(plan['originalDispatchRoot'] == str(old_root), 'original dispatch path differs')
    verify_sealed(old_root, '3c94ad2b0abab475b8b0697ce0701008a88f56d5fb7d5fa30982e2196c60c417')
    verify_sealed(W.parent/'location_metadata_dispatch_review_r2', 'b572ac78b4418b2a78c350c81495dd61fce6b2170da66d80a6b305b74172f9ce')
    old = read(old_root/'ROOT_COMMAND.json')
    require(plan['runRoot'] == old['runRoot'] and Path(plan['runRoot']).resolve() == W.parents[1], 'run-root authority differs')
    require(all(plan[k] == old[k] for k in ['inputsSealed', 'sourceRoot', 'sourceFiles', 'runtimeFiles', 'runtimeTreeSha256', 'toolIdentities', 'privateFiles', 'privatePacketSha256']), 'original source/tool/case packet bindings differ')
    for identity in plan['inputsSealed']: verify_sealed(Path(identity['path']), identity['sealSha256'])
    for name, entry in plan['privateFiles'].items():
        require((W/name).read_bytes() == (old_root/name).read_bytes() and len((W/name).read_bytes()) == entry['bytes'] and sha((W/name).read_bytes()) == entry['sha256'], 'unchanged native source differs: '+name)
    C = Path(plan['sourceRoot']); records = []
    for rel, entry in plan['runtimeFiles'].items():
        file = (C/rel).resolve(); require(file.is_relative_to(C.resolve()), 'runtime path escape')
        raw = file.read_bytes(); require(len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], 'runtime drift: '+rel)
        records.append(entry['sha256']+'  '+rel+'\n')
    require(len(records) == 139 and sha(''.join(records).encode()) == plan['runtimeTreeSha256'], 'wrong e718 inventory')
    for rel, expected in plan['sourceFiles'].items(): require(sha((C/rel).read_bytes()) == expected, 'source drift: '+rel)
    for entry in plan['toolIdentities'].values():
        file = Path(entry['path']); require(file.is_file() and file.stat().st_size == entry['bytes'] and sha(file.read_bytes()) == entry['sha256'], 'tool drift: '+str(file))
    registry = read(W/'native/CASE_REGISTRY.json')['cases']
    names = [r['name'] for r in registry if r['name'] != 'widget-positive']
    require(len(registry) == 57 and len(names) == len(set(names)) == 56 and plan['selectedCases'] == names, 'exact original remaining56 required')
    output, accounting = W/'native/root-native-remaining56-r1', Path(plan['runRoot'])/'evidence/R0023/metadata-remaining-r1'
    expected = old['argv'][:-2]
    expected[4] = str(W/'native/residual-location-native.py')
    expected[expected.index('--out')+1] = str(output)
    for name in names: expected += ['--only', name]
    require(plan['argv'] == expected and plan['output'] == str(output) and plan['accounting'] == str(accounting), 'original selected argv/fresh output scope differs')
    require(plan['automaticRetries'] == 0 and plan['nodeComplete'] is False and plan['bodyKey'] == 'chromium:metadata:remaining56', 'batch must not grant node/retry authority')
    first = plan['firstActualReview']
    require(first['root'] == str(W.parent/'location_metadata_first_actual_review_r1'), 'first actual review root differs')
    if require_first:
        verify_sealed(Path(first['root']), first['sealSha256'])
        proof = read(Path(first['root'])/'REPORT.json')
        require(proof.get('schema') == 'r0023-metadata-first-actual-independent-review/1' and proof.get('status') == 'PASS_R0023_METADATA_FIRST_WIDGET_POSITIVE_NATIVE_BOUND_SCOPE' and proof.get('reviewer') == '/root/r0008_qualify_final_review_r1' and proof.get('node') == 'R0023-METADATA' and proof.get('bodyKey') == 'chromium:metadata:widget-positive' and proof.get('case') == 'widget-positive' and proof.get('acceptedCases') == 1 and proof.get('remainingCases') == 56 and proof.get('nativeExecutedByReviewer') is False and proof.get('nodeComplete') is False and proof.get('nodeCredit') == 0, 'first original independent actual PASS absent')
        for item in plan['firstRawPins']:
            file = Path(item['path']); raw = file.read_bytes(); require(len(raw) == item['bytes'] and sha(raw) == item['sha256'], 'first native raw custody differs')
        require([proof['subjects'][k] for k in ['dispatch','results','caseResult']] == plan['firstSubjectPins'], 'first review does not bind exact subjects')
        dispatch = read(Path(plan['firstDispatch']['path']))
        require(dispatch['exitCode'] == 0 and dispatch['childCompletion'] == 'TERMINAL' and dispatch['capacityRelease'] == 'RELEASED_OWN_MATCHING_LEASE' and dispatch['chainCleanupReceipt']['basis'] == 'EXACT_RETAINED_CJS_RECEIPT_AFTER_AWAITED_FINALLY', 'first attempt known cleanup absent')
        raw = read(Path(old['output'])/'results.json')
        require(raw['selected'] == ['widget-positive'] and raw['notRun'] == [] and [r['name'] for r in raw['executed']] == ['widget-positive'] and raw['executed'][0]['status'] == 'PASS', 'first original native PASS identity differs')
    return old

def source_review(plan, admission, carrier_seal):
    root = W.parent/'location_metadata_remaining_source_review_r1'
    verify_sealed(root, admission['remainingSourceReviewSealSha256'])
    report = read(root/'REPORT.json')
    require(report['schema'] == 'r0023-metadata-remaining56-source-admission/1' and report['disposition'] == 'PASS_BOUNDARY_ONLY' and report['bodyKey'] == plan['bodyKey'] and report['carrierSealSha256'] == carrier_seal and report['rootCommandSha256'] == sha((W/'ROOT_COMMAND.json').read_bytes()) and report['reviewer'] == '/root/r0008_qualify_final_review_r1' and report['nativeExecuted'] is False, 'exact remaining56 affected source admission absent')

def execute(plan, args):
    output, accounting = Path(plan['output']), Path(plan['accounting'])
    fresh_no_output(output, accounting)
    require(args.expected_seal and args.admission and args.capacity_lease and args.lease_id, 'actual root admission/lease/ID and exact proposal seal required')
    verify_sealed(W, args.expected_seal)
    binding(plan)
    admission, capacity = read(args.admission), read(args.capacity_lease)
    for key, expected in plan['admissionRequiredFields'].items(): require(admission.get(key) == expected, 'admission mismatch: '+key)
    for key, expected in plan['capacityRequiredFields'].items(): require(capacity.get(key) == expected, 'capacity mismatch: '+key)
    source_review(plan, admission, args.expected_seal)
    require(admission['remainingCarrierSealSha256'] == args.expected_seal and admission['remainingRootCommandSha256'] == sha((W/'ROOT_COMMAND.json').read_bytes()) and admission['firstActualReviewSealSha256'] == plan['firstActualReview']['sealSha256'], 'remaining/first admission binding differs')
    require(capacity.get('leaseId') == args.lease_id and capacity.get('dispatchSealSha256') == args.expected_seal and capacity.get('admissionSha256') == sha(args.admission.read_bytes()), 'wrong real lease/seal/admission binding')
    expiry = dt.datetime.fromisoformat(capacity['expiresAtUtc'].replace('Z', '+00:00'))
    require(expiry.tzinfo is not None and expiry > dt.datetime.now(dt.timezone.utc), 'expired/unzoned lease')
    bindings = {'sourceCommit': admission['sourceRefProvenance'], 'runtimeSha256': plan['runtimeTreeSha256'], 'sourceRoot': plan['sourceRoot'], 'sourceFiles': plan['sourceFiles'], 'engine': 'chromium', 'outputPath': str(output), 'caseSha256': sha(json.dumps(plan['selectedCases'], sort_keys=True, separators=(',', ':')).encode()), 'caseHashScope': 'canonical ordered original CASE_REGISTRY remaining56 names; seven unchanged packet file pins retained', 'privatePacketSha256': plan['privatePacketSha256'], 'dispatchSealSha256': args.expected_seal, 'admissionSha256': capacity['admissionSha256'], 'expiresAtUtc': capacity['expiresAtUtc'], 'firstActualReviewSealSha256': plan['firstActualReview']['sealSha256'], 'remainingSourceReviewSealSha256': admission['remainingSourceReviewSealSha256']}
    return transaction(plan['argv'], W, output, accounting, Path(plan['runRoot'])/'ACTIVE_LEDGER.json', args.lease_id, runner, 'ACTUAL_ROOT_METADATA_ORIGINAL_REMAINING56_ATTEMPT_NOT_QUALIFICATION', bindings)

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--execute', action='store_true'); p.add_argument('--verify-only', action='store_true'); p.add_argument('--expected-seal')
    p.add_argument('--admission', type=Path); p.add_argument('--capacity-lease', type=Path); p.add_argument('--lease-id'); args = p.parse_args()
    require(not (args.execute and args.verify_only), 'read-only and execute modes are mutually exclusive')
    plan = read(W / 'ROOT_COMMAND.json'); fresh_no_output(Path(plan['output']), Path(plan['accounting']))
    binding(plan, require_first=bool(args.execute or plan['firstActualReview']['sealSha256']))
    if args.expected_seal: verify_sealed(W, args.expected_seal)
    if not args.execute:
        print(json.dumps({'status': 'PROPOSED_NOT_EXECUTED', 'argv': plan['argv'], 'native': 'NOT_RUN'})); return 0
    receipt = execute(plan, args); print(json.dumps({'status': receipt['status'], 'exitCode': receipt.get('exitCode'),
                                                   'capacityRelease': receipt['capacityRelease'], 'nodeCredit': False}))
    return receipt.get('exitCode', 1)
if __name__ == '__main__': raise SystemExit(main())
