"""Root-only finite R0011 batch using the retained singleton carrier and its actual cleanup guards."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import types

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
L = RUN / 'ACTIVE_LEDGER.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda path: json.loads(path.read_bytes())

def carrier():
    module = types.ModuleType('exact_r0011_carrier_functions')
    module.__file__ = str(HERE / 'RUN_PREPARED.py')
    exec(compile((HERE / 'RUN_PREPARED.py').read_bytes(), module.__file__, 'exec'), module.__dict__)
    return module

def validate_batch_identity(value, catalogue, batch, binding, seal_sha):
    assert value['schema'] == 'root-r0011-finite-original-batch-admission/1'
    assert value['status'] == 'ADMITTED_FINITE_REVIEWED_ORIGINAL_BATCH'
    assert value['batch'] == batch
    assert value['allowedCaseIds'] == catalogue['batches'][batch]
    assert len(value['allowedCaseIds']) == len(set(value['allowedCaseIds']))
    assert not set(value['allowedCaseIds']) & set(catalogue['excludedCompletedIds'])
    assert value['packetSealSha256'] == seal_sha and value['caseContractsSha256'] == binding['caseContractsSha256']
    assert value['sourceRoot'] == binding['sourceRoot'] and value['runtimeSha256'] == binding['sourceBinding']['runtimeSha256']
    assert set(value['caseAdmissionPins']) == set(value['allowedCaseIds'])
    assert value['sourceReviewGrantedByRoot'] is True and value['nativeEffectsAdmittedByRoot'] is True
    assert value['owner'] == '/root'
    prepared = dt.datetime.fromisoformat(value['preparedAtUtc'])
    expires = dt.datetime.fromisoformat(value['expiresAtUtc'])
    current = dt.datetime.now(dt.timezone.utc)
    assert prepared.tzinfo is not None and expires.tzinfo is not None and prepared <= current < expires
    expected_root = RUN / ('evidence/R0011/whole-owner-main-r2-batch-' + batch)
    assert Path(value['batchEffectRoot']).resolve() == expected_root.resolve()
    return expected_root

def case_lease(binding, approval, expiry):
    fresh = binding['freshRootIdentity']
    return {'capacity': 1, 'status': 'FREE', 'holder': None, 'node': 'R0011-EVIDENCE',
        'leaseId': fresh['leaseId'], 'preparedForLeaseId': fresh['leaseId'],
        'preparedCaseIds': [binding['caseContract']['id']], 'totalCases': 1, 'completedCases': 0,
        'finishedAtUtc': None, 'unknownChildCompletion': False, 'attentionRequired': False,
        'preparedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(), 'expiresAtUtc': expiry,
        'caseContractsSha256': binding['caseContractsSha256'], 'driverSha256': binding['nativeReferences']['residual-location-actions.cjs']['sha256'],
        'rootDriverSha256': sha((HERE / 'RUN_PREPARED.py').read_bytes()), 'reviewSealSha256': approval['seal']['sha256'],
        'sourceRoot': binding['sourceRoot'], 'runtimeSha256': binding['sourceBinding']['runtimeSha256'],
        'outputPath': fresh['nativeOutput'], 'effectRoot': fresh['effectRoot'],
        'scope': 'One original R0011 context from the independently reviewed finite batch; unchanged native predicates; serial actual cleanup required.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', choices=['remaining-positive-and-warning', 'reset-mutant-after-accepted-positive'], default='remaining-positive-and-warning')
    parser.add_argument('--execute-native', action='store_true')
    parser.add_argument('--root-batch-admission', type=Path)
    parser.add_argument('--reset-positive-review', type=Path)
    args = parser.parse_args()
    c = carrier()
    catalogue, base = read(HERE / 'CASE_CONTRACTS.json'), read(HERE / 'BINDING.json')
    cases = catalogue['batches'][args.batch]
    _, packet = c.verify([cases[0]])
    if not args.execute_native:
        for case_id in cases:
            b = c.select_context(base, case_id)
            c.validate_selector([case_id])
            c.fresh(Path(b['freshRootIdentity']['effectRoot']))
            c.fresh(Path(b['freshRootIdentity']['nativeOutput']))
        print(json.dumps({'status': 'PASS_READ_ONLY_FINITE_ORIGINAL_BATCH', 'cases': cases, 'native': 'NOT_RUN', 'batch': args.batch}))
        return 0
    assert args.root_batch_admission is not None, 'Actual finite root batch admission required'
    envelope_raw = args.root_batch_admission.read_bytes()
    envelope = json.loads(envelope_raw)
    root = validate_batch_identity(envelope, catalogue, args.batch, base, packet)
    c.fresh(root)
    approval_pin = envelope['reviewApproval']
    approval = c.review_reference(approval_pin)
    approval_path = Path(approval_pin['path'])
    for case_id in cases:
        b = c.select_context(base, case_id)
        c.validate_review_approval(approval, b, packet)
        admission_pin = envelope['caseAdmissionPins'][case_id]
        admission = c.review_reference(admission_pin)
        assert Path(admission_pin['path']).resolve() == Path(b['freshRootIdentity']['admission']).resolve()
        c.validate_admission(admission, b, packet, approval, approval_pin['sha256'])
        c.fresh(Path(b['freshRootIdentity']['effectRoot']))
        c.fresh(Path(b['freshRootIdentity']['nativeOutput']))
    if args.batch == 'reset-mutant-after-accepted-positive':
        assert args.reset_positive_review is not None
        c.validate_reset_positive_review(read(args.reset_positive_review), base, packet)
    root.mkdir(parents=True, exist_ok=False)
    c.write_new(root / 'root-batch-admission.json', envelope_raw)
    summary = {'schema': 'r0011-finite-original-batch-result/1', 'batch': args.batch, 'cases': cases,
        'packetSealSha256': packet, 'caseContractsSha256': base['caseContractsSha256'], 'runtimeSha256': base['sourceBinding']['runtimeSha256'],
        'startedAtUtc': c.now(), 'executed': [], 'status': 'ADMITTED_NOT_LAUNCHED', 'independentPixels': 'PENDING', 'closure': 'NOT_AUTHORIZED'}
    try:
        for index, case_id in enumerate(cases):
            b = c.select_context(base, case_id)
            c.verify([case_id])
            validate_batch_identity(envelope, catalogue, args.batch, base, packet)
            previous_index = approval['allowedCaseIds'].index(case_id) - 1
            previous = None if previous_index < 0 else Path(catalogue['cases'][approval['allowedCaseIds'][previous_index]]['fresh']['effectRoot']) / 'rolling-cleanup.json'
            c.validate_previous_completion(previous, b, approval, packet)
            ledger_before = L.read_bytes()
            ledger = json.loads(ledger_before)
            current = ledger['resourceLeases']['heavy-browser']
            assert current['capacity'] == 1 and current['status'] == 'FREE' and current['holder'] is None
            assert current.get('unknownChildCompletion', False) is False and current.get('attentionRequired', False) is False
            prepared_lease = case_lease(b, approval, envelope['expiresAtUtc'])
            c.validate_finite_lease(prepared_lease, b, approval)
            ledger['resourceLeases']['heavy-browser'] = prepared_lease
            ledger['updatedAtUtc'] = c.now()
            c.write_new(root / (str(index).zfill(2) + '-ledger-before-stage.json'), ledger_before)
            replacement = root / (str(index).zfill(2) + '-ledger-stage.json')
            c.json_new(replacement, ledger)
            assert L.read_bytes() == ledger_before, 'Canonical ledger changed before serial root lease staging'
            replacement.replace(L)
            argv = [base['tools']['python']['path'], '-I', '-S', '-B', str(HERE / 'RUN_PREPARED.py'), '--only', case_id,
                '--execute-native', '--root-admission', b['freshRootIdentity']['admission'], '--review-approval', str(approval_path)]
            if previous is not None:
                argv += ['--previous-completion', str(previous)]
            if b['caseContract'].get('requiresIndependentResetPositive'):
                argv += ['--reset-positive-review', str(args.reset_positive_review)]
            with (root / (str(index).zfill(2) + '-stdout.log')).open('xb') as stdout, (root / (str(index).zfill(2) + '-stderr.log')).open('xb') as stderr:
                child = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
                result = child.wait()
            dispatch_path = Path(b['freshRootIdentity']['effectRoot']) / 'dispatch-result.json'
            row = {'caseId': case_id, 'argv': argv, 'ownedCarrierPid': c.positive_pid(child.pid), 'exitCode': result,
                   'dispatch': str(dispatch_path), 'finishedAtUtc': c.now()}
            summary['executed'].append(row)
            print(json.dumps(row), flush=True)
            assert result == 0 and dispatch_path.is_file(), 'Finite batch stops on failure or unknown completion; preserve all outputs'
            dispatch = read(dispatch_path)
            assert dispatch['nativeComplete'] is True and dispatch['unknownCompletion'] is False
            assert dispatch['consumerStatus'] == b['caseContract']['expectedStatus']
            c.validate_native_terminal(b, b['caseContract']['recipe'], dispatch['exitCode'], {})
            c.validate_cleanup(read(Path(b['freshRootIdentity']['effectRoot']) / 'rolling-cleanup.json'), b, dispatch)
            final_lease = read(L)['resourceLeases']['heavy-browser']
            assert final_lease['status'] == 'FREE' and final_lease['holder'] is None and final_lease['leaseId'] == b['freshRootIdentity']['leaseId']
        summary['status'] = 'COMPLETE_FINITE_NATIVE_BATCH_PENDING_TRACE_PIXEL_REVIEW'
    except BaseException as error:
        summary.update(status='STOPPED_BOUNDED_BATCH_NO_RETRY', error=repr(error))
    finally:
        summary['finishedAtUtc'] = c.now()
        summary['notRun'] = [case_id for case_id in cases if case_id not in [row['caseId'] for row in summary['executed']]]
        c.json_new(root / 'batch-result.json', summary)
    return 0 if summary['status'] == 'COMPLETE_FINITE_NATIVE_BATCH_PENDING_TRACE_PIXEL_REVIEW' else 1

if __name__ == '__main__':
    raise SystemExit(main())
