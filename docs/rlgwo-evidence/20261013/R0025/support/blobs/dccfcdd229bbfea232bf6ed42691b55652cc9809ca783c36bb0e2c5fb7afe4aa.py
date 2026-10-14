#!/usr/bin/env python3
"""Guarded R0025 actual selected-painter comparison; preflight never opens a browser."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import platform
import runpy
import statistics
import traceback
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
library = runpy.run_path(str(BASE / 'prepare_cost.py'), run_name='r0025_cost_library')
classic, select_engine = library['classic'], library['select_engine']

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8', newline='\n')

def stats(values):
    if not values or not all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0 for x in values):
        raise ValueError('missing/nonfinite/negative raw duration')
    ordered = sorted(values)
    return {'count': len(values), 'median': statistics.median(values),
        'p95': ordered[math.ceil(.95 * len(values)) - 1], 'min': ordered[0], 'max': ordered[-1]}

def summarize(batches, adopted):
    reports, raw = {}, {'before': [], 'after': []}
    problems = []
    expected = [(block, position, arm) for block in range(4)
        for position, arm in enumerate(['before', 'after', 'after', 'before'])]
    actual = [(b.get('block'), b.get('position'), b.get('arm')) for b in batches]
    if actual != expected:
        problems.append('not all four predeclared complete ABBA blocks retained in order')
    for batch in batches:
        arm = batch['arm']
        raw[arm].extend(batch['invocationDurationsMs'])
        batch['statistics'] = stats(batch['invocationDurationsMs'])
        if batch['exceptions'] or batch['containmentLimitReached'] or not batch['finiteState']['pass'] or not batch['retainedBindingsEqual']:
            problems.append('batch invariant/exception ' + str(batch.get('block')) + '/' + str(batch.get('position')))
        if batch['blockElapsedMs'] < 5000:
            problems.append('batch did not reach predeclared duration')
    for arm in raw:
        reports[arm] = stats(raw[arm])
    comparisons = {}
    for statistic in ['median', 'p95']:
        baseline = reports['before'][statistic]
        tolerance = max(adopted['absoluteMs'], adopted['relative'] * baseline)
        delta = reports['after'][statistic] - baseline
        within_arm_ranges = {arm: max(b['statistics'][statistic] for b in batches if b['arm'] == arm)
            - min(b['statistics'][statistic] for b in batches if b['arm'] == arm) for arm in raw}
        comparisons[statistic] = {'before': baseline, 'after': reports['after'][statistic], 'deltaMs': delta,
            'adoptedToleranceMs': tolerance, 'withinBudget': delta <= tolerance,
            'withinArmBlockRangesMs': within_arm_ranges, 'noiseWithinPredeclaredRule': all(v <= tolerance for v in within_arm_ranges.values())}
    budget_met = all(c['withinBudget'] for c in comparisons.values())
    stable = all(c['noiseWithinPredeclaredRule'] for c in comparisons.values())
    terminal = 'INCOMPLETE' if problems or not stable else 'PASS_SELECTED_SCOPE' if budget_met else 'FAIL_SELECTED_BUDGET'
    return {'terminal': terminal, 'statistics': reports, 'comparisons': comparisons, 'problems': problems,
        'budgetStatus': 'MET' if budget_met else 'EXCEEDED', 'noiseStatus': 'WITHIN_PREDECLARED_RULE' if stable else 'NOISY_INCOMPLETE',
        'scope': 'actual synchronous selected painter call elapsed only; no GPU/battery/provider/full-widget/exclusive CPU conclusion'}

def load_receipt(path, expected_sha):
    if not path or not expected_sha:
        raise ValueError('exact receipt path and SHA-256 are required')
    raw = path.read_bytes()
    if sha(raw) != expected_sha:
        raise ValueError('receipt drift: ' + str(path))
    return json.loads(raw.decode('utf-8'))

def entry(args, protocol, fixture_sha, before_sha, after_sha):
    adopted = load_receipt(args.budget_adoption, args.budget_sha256)
    if adopted.get('schema') != 'r0025-cost-budget-adoption/1' or adopted.get('status') != 'ADOPTED_BEFORE_RUN':
        raise ValueError('r0025-cost-budget/v1 PENDING_DECISION: trusted owner/cold pre-run adoption is absent')
    if not adopted.get('ownerAuthorityReference') or not adopted.get('independentColdReviewReference'):
        raise ValueError('adoption requires explicit owner and independent cold authority references')
    proposed = protocol['budgetProposal']
    if adopted.get('absoluteMs') != proposed['absoluteMs'] or adopted.get('relative') != proposed['relative'] or adopted.get('statistics') != ['median', 'p95']:
        raise ValueError('budget differs from retained G proposal; no widening/reinterpretation allowed')
    if adopted.get('protocolSha256') != sha((BASE / 'PROTOCOL.json').read_bytes()) or adopted.get('fixtureSha256') != fixture_sha:
        raise ValueError('adoption not bound to exact protocol/fixture')
    if adopted.get('beforeSourceSha256') != before_sha or adopted.get('afterSourceSha256') != after_sha:
        raise ValueError('adoption source identity mismatch')
    if args.engine not in adopted.get('engines', []):
        raise ValueError('engine outside adoption')
    if adopted.get('noiseRule') != protocol['statistics']['noiseRuleForAdoption']:
        raise ValueError('noisy-setup rule not pre-adopted')
    adopted_at = datetime.fromisoformat(adopted['adoptedAtUtc'])
    if adopted_at.tzinfo is None or adopted_at > datetime.now(timezone.utc):
        raise ValueError('adoption timestamp must be prior to this launch and timezone aware')
    lease = load_receipt(args.resource_lease, args.lease_sha256)
    if lease.get('resource') != 'heavy-browser' or lease.get('status') != 'EXCLUSIVE_ACTIVE' or lease.get('node') != 'R0025-COST' or not lease.get('rootLiveReconciliationReference'):
        raise ValueError('exclusive root heavy-browser lease/live reconciliation missing')
    if lease.get('afterSourceSha256') != after_sha or lease.get('fixtureSha256') != fixture_sha:
        raise ValueError('resource lease source/fixture mismatch')
    expiry = datetime.fromisoformat(lease['expiresAtUtc'])
    if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
        raise ValueError('exclusive root lease is expired or lacks timezone')
    admission = load_receipt(args.scene_admission, args.scene_sha256)
    if admission.get('schema') != 'r0025-painter-scene-admission/1' or admission.get('status') != 'SATISFIED':
        raise ValueError('actual current consumer scene/admission and parity receipt missing')
    if admission.get('afterSourceSha256') != after_sha or admission.get('fixtureSha256') != fixture_sha or admission.get('protocolSha256') != adopted['protocolSha256'] or admission.get('engine') != args.engine:
        raise ValueError('actual consumer scene/admission identity mismatch')
    if admission.get('sameSceneVerified') is not True or admission.get('selectedFixtureParity') is not True:
        raise ValueError('consumer/selected-fixture equivalence remains unverified')
    inventory = admission.get('nativeConsumerInventory', {})
    for check in ['noExtraProviderRequests', 'noExtraPermanentRafChain', 'noUnboundedHistoryOrPerClusterRetention']:
        if inventory.get(check) is not True:
            raise ValueError('native consumer inventory remains unverified: ' + check)
    return adopted, lease, admission

def fixture_identity():
    names = ['r0025-painter-cost.py', 'cost_boundary.js', 'prepare_cost.py']
    files = {name: sha((BASE / name).read_bytes()) for name in names}
    return sha(json.dumps(files, sort_keys=True, separators=(',', ':')).encode('utf-8')), files

def run(args):
    if args.output.exists():
        raise ValueError('output must be new; no evidence overwrite')
    args.output.mkdir(parents=True)
    protocol = json.loads((BASE / 'PROTOCOL.json').read_text(encoding='utf-8'))
    raw_before, raw_after = args.before_source.read_bytes(), (args.after_workspace / 'index.html').read_bytes()
    before_sha, after_sha = sha(raw_before), sha(raw_after)
    if before_sha != protocol['before']['sha256'] or after_sha != protocol['after']['sha256']:
        raise ValueError('guarded before/current source identity drift')
    engines = {'before': select_engine(classic(raw_before.decode('utf-8')))[0],
        'after': select_engine(classic(raw_after.decode('utf-8')))[0]}
    config = {'scene': protocol['scene'], 'sources': engines}
    fixture_sha, fixture_files = fixture_identity()
    report = {'schema': 'r0025-painter-cost/v1', 'node': 'R0025-COST', 'atUtc': now(),
        'status': 'PREFLIGHT_ONLY' if not args.run else 'ENTRY_PENDING', 'measurementExecuted': False,
        'before': {'path': str(args.before_source), 'sha256': before_sha},
        'after': {'workspace': str(args.after_workspace), 'indexSha256': after_sha, 'runtimeSha256': protocol['afterRuntimeSha256']},
        'fixtureSha256': fixture_sha, 'fixtureFiles': fixture_files, 'protocolSha256': sha((BASE / 'PROTOCOL.json').read_bytes()),
        'protocol': protocol, 'warmup': [], 'batches': [], 'exceptions': [],
        'claims': {'nativeQualification': False, 'nodeComplete': False, 'exclusiveCpuProfiler': False,
            'gpu': False, 'battery': False, 'networkSavings': False, 'wholeWidgetPerformance': False}}
    save(args.output / 'CONFIG.json', config)
    save(args.output / 'results.json', report)
    if not args.run:
        print(json.dumps({'status': 'PREFLIGHT_ONLY', 'fixtureSha256': fixture_sha, 'measurementExecuted': False}))
        return 0
    attempted_requests, errors = [], []
    try:
        adopted, lease, admission = entry(args, protocol, fixture_sha, before_sha, after_sha)
        report.update({'adoptedBudget': adopted, 'resourceLease': lease, 'sceneAdmission': admission, 'entryVerifiedAtUtc': now()})
        # Every required authority/identity gate is checked before importing or starting a browser.
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            options = {'headless': False if args.headed else True}
            if args.executable:
                if not args.executable.is_file():
                    raise ValueError('explicit browser executable missing')
                options['executable_path'] = str(args.executable.resolve())
            if args.engine == 'chromium':
                options['chromium_sandbox'] = True
            browser = getattr(playwright, args.engine).launch(**options)
            try:
                context = browser.new_context(viewport=protocol['environment']['viewport'], device_scale_factor=1, reduced_motion='no-preference')
                page = context.new_page()
                def deny(route):
                    attempted_requests.append({'url': route.request.url, 'method': route.request.method})
                    route.abort()
                page.route('**/*', deny)
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.set_content('<!doctype html><meta charset="utf-8"><canvas id="cost" width="144" height="232"></canvas>', wait_until='load')
                page.add_script_tag(content=(BASE / 'cost_boundary.js').read_text(encoding='utf-8'))
                page.evaluate('(config)=>{window.__cost=R0025CostBoundary.setup(document.getElementById("cost"),config,performance.now.bind(performance));}', config)
                report['environment'] = page.evaluate('({ua:navigator.userAgent,dpr:devicePixelRatio,viewport:{width:innerWidth,height:innerHeight},visibility:document.visibilityState})')
                report['environment'].update({'engine': args.engine, 'version': browser.version, 'python': platform.python_version(), 'os': platform.platform(),
                    'executable': str(args.executable) if args.executable else 'explicit requested Playwright-managed engine', 'headed': args.headed, 'cpuThrottle': 1})
                if report['environment']['dpr'] != 1 or report['environment']['viewport'] != protocol['environment']['viewport'] or report['environment']['visibility'] != 'visible':
                    raise ValueError('native environment does not match predeclared protocol')
                report['measurementExecuted'] = True
                report['timerCalibration'] = page.evaluate('''()=>{
                  const gaps=[];let previous=performance.now(),attempts=0;
                  while(gaps.length<100 && attempts++<1000000){const next=performance.now();if(next>previous){gaps.push(next-previous);previous=next;}}
                  return {positiveStepsMs:gaps,minimumPositiveStepMs:gaps.length?Math.min(...gaps):null,attempts,
                    scope:'instrument-clock resolution control outside every painter duration'};
                }''')
                for arm in ['before', 'after']:
                    entry(args, protocol, fixture_sha, before_sha, after_sha)
                    warm = page.evaluate('(arm)=>__cost.runBatch(arm,5000)', arm)
                    report['warmup'].append(warm)
                    save(args.output / 'results.json', report)
                    if warm['exceptions'] or warm['containmentLimitReached'] or not warm['finiteState']['pass'] or not warm['retainedBindingsEqual']:
                        raise ValueError('warmup invalid; all raw samples retained')
                for block in range(4):
                    for position, arm in enumerate(['before', 'after', 'after', 'before']):
                        entry(args, protocol, fixture_sha, before_sha, after_sha)
                        batch = page.evaluate('(arm)=>__cost.runBatch(arm,5000)', arm)
                        batch.update({'block': block, 'position': position, 'completedAtUtc': now()})
                        report['batches'].append(batch)
                        save(args.output / 'results.json', report)
                summary = summarize(report['batches'], adopted)
                if sha(args.before_source.read_bytes()) != before_sha or sha((args.after_workspace / 'index.html').read_bytes()) != after_sha:
                    summary['terminal']='INCOMPLETE'
                    summary['problems'].append('source drifted during native measurement')
                quantum=report['timerCalibration']['minimumPositiveStepMs']
                if quantum is None or quantum > adopted['absoluteMs']:
                    summary['terminal']='INCOMPLETE'
                    summary['problems'].append('native timer resolution insufficient for adopted absolute tolerance')
                if attempted_requests or errors:
                    summary['terminal'] = 'INCOMPLETE'
                    summary['problems'].append('native request/page exception; raw retained')
                report.update({'status': summary['terminal'], 'summary': summary, 'finishedAtUtc': now()})
                context.close()
            finally:
                browser.close()
    except Exception as error:
        report['exceptions'].append({'atUtc': now(), 'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()})
        report['status'] = 'INCOMPLETE' if report['measurementExecuted'] else 'BLOCKED_ENTRY_NO_MEASUREMENT'
    finally:
        report['nativeAttemptedRequests'] = attempted_requests
        report['pageErrors'] = errors
        save(args.output / 'results.json', report)
    print(json.dumps({'status': report['status'], 'measurementExecuted': report['measurementExecuted'], 'batchesRetained': len(report['batches']), 'exceptions': len(report['exceptions'])}))
    return 0 if report['status'] == 'PASS_SELECTED_SCOPE' else 2

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-source', type=Path, required=True)
    parser.add_argument('--after-workspace', type=Path, required=True)
    parser.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true', help='root-only native execution after all exact gates')
    parser.add_argument('--budget-adoption', type=Path)
    parser.add_argument('--budget-sha256')
    parser.add_argument('--resource-lease', type=Path)
    parser.add_argument('--lease-sha256')
    parser.add_argument('--scene-admission', type=Path)
    parser.add_argument('--scene-sha256')
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--headed', action='store_true')
    args = parser.parse_args()
    try:
        return run(args)
    except Exception as error:
        if args.output.is_dir() and not (args.output / 'results.json').exists():
            save(args.output / 'results.json', {'schema': 'r0025-painter-cost/v1', 'status': 'BLOCKED_PREFLIGHT_NO_MEASUREMENT',
                'measurementExecuted': False, 'exception': {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}})
        print(json.dumps({'status': 'BLOCKED_PREFLIGHT_NO_MEASUREMENT', 'error': str(error)}))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
