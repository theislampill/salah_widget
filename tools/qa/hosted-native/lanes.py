#!/usr/bin/env python3
"""Emit the initial native command plan. This entry never launches a browser.

Run only after prepare.py. --out must be a new owner-private directory. Its
r0035-plan.json and the JSON on stdout contain private paths and must be retained
inside the encrypted capture. An isolated coordinator executes the declared argv
sequentially, captures both streams, and adjudicates the result files separately
from subprocess exit codes. No shell interpolation is needed.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

from prepare import BASELINE, RESEARCH, digest, validate_prepared, verify_generated, write_json
from r002f_prepare import BASE_INDEX, COMBINED_INDEX, BASE_INVENTORY, COMBINED_INVENTORY, PATCH

HERE = Path(__file__).resolve().parent
R002F_PROBE_SHA256 = '673c0656d8e2d8e1c343d1258be5070fa9447f3f43878460791ea8570468558f'
WORK_ORDERS = ('R0040', 'R003F', 'R0035', 'R002F')
STAR_DEFAULTS = {'guard': 'default', 'scope': 'all', 'mode': 'both'}


def star_controls(value=None):
    """Existing recipe options only; no admission, time or owner-policy changes."""
    if value is None:
        value = {}
    choices = {'guard': ('default', 'off'), 'scope': ('all', 'preview-members'),
               'mode': ('both', 'timing', 'capture')}
    if (not isinstance(value, dict) or any(key not in choices for key in value)
            or any(not isinstance(v, str) or v not in choices[k] for k, v in value.items())):
        raise ValueError('unsupported R0035 diagnostic controls')
    return {**STAR_DEFAULTS, **value}


def selected_work_orders(value, include_r002f):
    """An absent selection retains the existing CLI population; empty is invalid."""
    if type(include_r002f) is not bool:
        raise ValueError('R002F enabled must be boolean')
    if value is None:
        value = [order for order in WORK_ORDERS if order != 'R002F' or include_r002f]
    if (not isinstance(value, list) or not value
            or any(not isinstance(order, str) or order not in WORK_ORDERS for order in value)
            or len(set(value)) != len(value)):
        raise ValueError('work-order selection must be a nonempty list of distinct known identifiers')
    if ('R002F' in value) != include_r002f:
        raise ValueError('R002F enabled and work-order selection disagree')
    # Selection does not reorder dependencies or change the reviewed lane order.
    return [order for order in WORK_ORDERS if order in value]


def admit_r002f(path, process_path=None):
    """A failed optional build remains a blocked lane, not a failed common plan."""
    admission = {'status': 'INCOMPLETE'}
    try:
        if process_path is not None:
            process_path = Path(process_path).resolve()
            process = json.loads(process_path.read_text())
            admission['processReceipt'] = {'path': str(process_path), 'sha256': digest(process_path)}
            if (not isinstance(process, dict) or type(process.get('returncode')) is not int
                    or process['returncode'] != 0 or process.get('timedOut') is not False):
                raise ValueError('R002F preparation process did not complete successfully')
        path = Path(path).resolve()
        body = json.loads(path.read_text())
        admission['receipt'] = {'path': str(path), 'sha256': digest(path)}
        if (body.get('protocol') != 'r002f-hosted-build/1' or body.get('status') != 'PASS'
                or body.get('baseProvenance') != BASELINE or body.get('researchProvenance') != RESEARCH
                or body.get('wrapperSha256') != digest(HERE/'r002f_prepare.py')
                or body.get('patch', {}).get('patch') != PATCH):
            raise ValueError('R002F build receipt is absent, incomplete or has wrong custody')
        trees = {}
        for arm, index, inventory in (('baseline', BASE_INDEX, BASE_INVENTORY),
                                      ('candidate', COMBINED_INDEX, COMBINED_INVENTORY)):
            record = body.get('arms', {}).get(arm, {})
            builds = record.get('builds', [])
            if (record.get('path') != arm or record.get('indexSha256') != index
                    or record.get('inventorySha256') != inventory or len(builds) != 2
                    or any(run.get('indexSha256') != index for run in builds)
                    or any(builds[-1].get(k) != v for k, v in {'written': 0, 'removed': 0, 'unchanged': 117}.items())):
                raise ValueError('R002F generated arm receipt is incomplete: '+arm)
            root = path.parent/arm
            verified = verify_generated(root, {'index.html': index, 'GENERATED.json': inventory})
            trees[arm] = {**verified, 'root': str(root)}
        if digest(HERE/'r002f_probe.cjs') != R002F_PROBE_SHA256:
            raise ValueError('R002F probe differs from the reviewed source')
        admission.update(status='PASS', trees=trees)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        admission['reason'] = str(error)
    return admission


def make_plan(prepared, out, *, python_playwright, node, node_modules, pngjs,
              engine='chromium', r003f_dpr=1, include_r002f=False, r002f_preparation=None,
              r002f_dpr=1, r002f_rounds=1, r002f_section='all', work_orders=None, retain_evidence=False,
              r0035_guard='default', r0035_scope='all', r0035_mode='both'):
    if engine not in ('chromium', 'firefox', 'webkit') or type(r003f_dpr) is not int or r003f_dpr not in (1, 2):
        raise ValueError('unsupported engine or R003F DPR')
    if (type(include_r002f) is not bool or type(r002f_dpr) is not int or r002f_dpr not in (1, 2, 3)
            or type(r002f_rounds) is not int or not 1 <= r002f_rounds <= 10
            or r002f_section not in ('all', 'prayer', 'preview')):
        raise ValueError('unsupported R002F campaign controls')
    selected = selected_work_orders(work_orders, include_r002f)
    stars = star_controls({'guard': r0035_guard, 'scope': r0035_scope, 'mode': r0035_mode})
    if stars != STAR_DEFAULTS and 'R0035' not in selected:
        raise ValueError('R0035 diagnostic controls require selected R0035 observations')
    if type(retain_evidence) is not bool:
        raise ValueError('evidence retention must be boolean')
    research = Path(prepared['sources']['research']['root'])
    historical = Path(prepared['sources']['historical']['root'])
    roots = {key: Path(value['root']) for key, value in prepared['trees'].items()}
    module = node_modules / 'playwright'
    star_plan_path = out / 'r0035-plan.json'
    arms = {'main': {'root': str(roots['main']), 'commit': BASELINE, 'flags': ''}}
    for label, writes in (('unmodified', 'full'), ('mitigated', 'changed')):
        arms[label] = {'root': str(roots['r0035']), 'commit': RESEARCH,
                       'flags': f'&r35arm={writes}&r35scope={r0035_scope}&r35amplitude=1&r35glass=0.5&r35margin=4'
                                + ('&r35guard=off' if r0035_guard == 'off' else ''),
                       'producerProbe': {'path': 'stars.status', 'equals': 'active'}}
    star_plan = {'kind': 'independent-reconstruction', 'arms': arms}
    entries = []

    def lane(identifier, work_order, dpr, timeout, kind, filename, statuses):
        target = out / identifier
        row = {'id': identifier, 'workOrder': work_order, 'engine': engine, 'dpr': dpr,
               'cwd': str(research), 'env': {'NODE_PATH': str(node_modules)},
               'output': str(target), 'stdout': str(out / (identifier + '.stdout')),
               'stderr': str(out / (identifier + '.stderr')), 'timeoutSeconds': timeout,
               'result': {'kind': kind, 'path': str(target / filename)},
               'exitStatuses': statuses, 'dependsOn': [], 'stopScopeOnAndon': work_order}
        entries.append(row)
        return row

    rain = lane(f'r0040-{engine}', 'R0040', 1, 720, 'r0040-options', 'native-options.json',
                {'0': 'MEASURED', '1': 'FAIL'})
    rain['argv'] = list(map(str, [node, research / 'tools/qa/r0040/native-options.cjs', module,
                                 historical, roots['r0040'], rain['output'], engine]))
    rain['result']['expectedCells'] = ['day-rain', 'day-drizzle', 'day-thunder', 'night', 'twilight',
                                      'reduced-none', 'reduced-still', 'motion-full', 'dry']

    moon = lane(f'r003f-b0-{engine}-dpr{r003f_dpr}', 'R003F', r003f_dpr, 900, 'r003f-b0', 'summary.json',
                {'0': 'MEASURED', '1': 'FAIL', '2': 'INCOMPLETE', '3': 'ISOLATION FAIL', '4': 'ANDON'})
    moon['argv'] = list(map(str, [node, research / 'tools/qa/r003f_owner_baseline.cjs', '--root', roots['r003f'],
                                 '--out', moon['output'], '--engine', engine, '--dpr', r003f_dpr,
                                 '--playwright', module, '--pngjs', pngjs]))
    moon['result']['expectedCaptures'] = ['offset', 'b0', 'b0-repeat', 'reference']
    moon['stopAllOnExit'] = [3]

    for capture in (False, True):
        label = 'capture' if capture else 'timing'
        if r0035_mode not in ('both', label):
            continue
        star = lane(f'r0035-{engine}-{label}', 'R0035', 1, 480, 'r0035-trials', 'summary.json',
                    {'0': 'INSPECT ADMISSION', '1': 'INCOMPLETE'})
        star['argv'] = list(map(str, [python_playwright, research / 'tools/r0035/native_trials.py',
                                     star_plan_path, star['output'], '--engine', engine, '--rounds', 1,
                                     '--seconds', 15, '--clock', 'ordinary', '--scene', 'dark', '--motion', 'normal']))
        star['result'].update(expectedRows=3, expectedArms=['main', 'unmodified', 'mitigated'],
                              requiresEveryRowAdmitted=True, capture=capture)
        if capture:
            star['argv'].append('--capture')
            if r0035_mode == 'both':
                star['dependsOn'] = [entries[-2]['id']]
                star['dependencyPolicy'] = 'finished; retain failed timing, classify captures independently'
    if include_r002f:
        admission = r002f_preparation or {'status': 'INCOMPLETE', 'reason': 'requested R002F preparation is missing'}
        probe = lane(f'r002f-{engine}-dpr{r002f_dpr}', 'R002F', r002f_dpr, 900,
                     'r002f-probe', 'result.json', {'0': 'PASS', '1': 'FAIL', '2': 'INCOMPLETE or INCONCLUSIVE'})
        probe['preparation'] = admission
        probe['result'].update(expectedRounds=r002f_rounds, expectedSection=r002f_section,
                               expectedObserverSha256=R002F_PROBE_SHA256)
        probe['argv'] = []
        if admission.get('status') == 'PASS':
            trees = admission['trees']
            probe['argv'] = list(map(str, [node, HERE/'r002f_probe.cjs', '--playwright', module,
                                          '--baseline', trees['baseline']['root'], '--candidate', trees['candidate']['root'],
                                          '--out', probe['output'], '--engine', engine, '--dpr', r002f_dpr,
                                          '--rounds', r002f_rounds, '--section', r002f_section, '--timeout-ms', 60000]))
    entries = [row for row in entries if row['workOrder'] in selected]
    if retain_evidence:
        for row in entries:
            if row['workOrder'] not in ('R0040', 'R0035'):
                continue
            original = row['argv']
            evidence = str(out/(row['id']+'-retention'))
            wrapper = HERE/('retain_r0040.cjs' if row['workOrder'] == 'R0040' else 'retain_r0035.py')
            row['argv'] = [original[0], str(wrapper), '--driver', original[1], '--evidence', evidence,
                           '--', *original[2:]]
            row['evidenceRetention'] = {
                'instrumented': True, 'originalArgv': original, 'output': evidence,
                'timingComparableToOriginal': False,
                'overhead': 'Host serialization, hashing, fsync and evidence copies affect timing/capture; '
                            'these are instrumented observations, not original performance measurements.'}
            row['exitStatuses']['86'] = 'EXTERNAL_CONTINUATION_VETOED'
            row['stopAllOnExit'] = [86]
    return {'schemaVersion': 1, 'protocol': 'salah-hosted-native-lanes/1', 'sequential': True,
            'scope': 'Selected native observations only; no work-order acceptance or owner selection.',
            'workOrders': selected, 'evidenceRetention': retain_evidence,
            'r0035Controls': stars,
            'r0035PlanPath': str(star_plan_path), 'r0035Plan': star_plan, 'lanes': entries,
            'failurePolicy': {'isolation': 'stop all observations', 'R003FAndon': 'stop R003F progression',
                              'externalContinuationVeto': 'stop all observations; prevented continuation is not an actual network escape',
                              'ordinaryLaneFailure': 'retain outputs; independent lanes may continue',
                              'timeout': 'coordinator kills child process group and retains private logs'},
            'followUp': [
                'After inspected admission, obtain Firefox and WebKit counterparts; neither proves Safari or physical-device behavior.',
                'R003F B0 at DPR2 is available with --r003f-dpr 2; its product Andon stops proposal progression.',
                'R0035 nine-round WebKit timing, native reduced/full-motion and phase/glass evidence need separate plans with their actual inactive probes.',
                'The R0040 nine-cell option recipe fixes DPR1. Additional motion, lossless capture and DPR evidence require the owning recipes and fresh admission.',
            ]}


def check_star_plan(prepared, plan):
    """Use the published driver's unchanged clean-source and arm guards."""
    directory = Path(prepared['sources']['research']['root']) / 'tools/r0035'
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location('hosted_native_existing_trials', directory / 'native_trials.py')
        driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(driver)
        driver.check_plan(plan)
        driver.verify_reconstructed_flags(plan['arms'])
    finally:
        sys.path.pop(0)


def executable(path):
    # Keep a venv interpreter's symlink path: resolving it would select system
    # Python and silently lose the separately installed Python Playwright.
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError('explicit executable path required')
    return path


def dependency(path, name, version):
    if not path.is_absolute() or not path.is_dir():
        raise ValueError('explicit module directory required')
    meta = json.loads((path / 'package.json').read_text())
    if (meta.get('name'), meta.get('version')) != (name, version):
        raise ValueError('dependency package identity mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan-json', action='store_true', required=True)
    for name in ('prepared', 'out', 'python-playwright', 'node', 'node-modules', 'pngjs'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--engine', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--r003f-dpr', type=int, choices=(1, 2), default=1)
    parser.add_argument('--work-orders', nargs='+')
    parser.add_argument('--retain-evidence', action='store_true')
    parser.add_argument('--r0035-guard', choices=('default', 'off'), default='default')
    parser.add_argument('--r0035-scope', choices=('all', 'preview-members'), default='all')
    parser.add_argument('--r0035-mode', choices=('both', 'timing', 'capture'), default='both')
    parser.add_argument('--r002f', action='store_true')
    parser.add_argument('--r002f-prepared', type=Path)
    parser.add_argument('--r002f-process', type=Path)
    parser.add_argument('--r002f-dpr', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--r002f-rounds', type=int, choices=range(1, 11), default=1)
    parser.add_argument('--r002f-section', choices=('all', 'prayer', 'preview'), default='all')
    args = parser.parse_args()
    os.umask(0o077)
    admitted_out = None
    try:
        selected_work_orders(args.work_orders, args.r002f)
        if args.out.exists() or args.out.is_symlink():
            raise ValueError('fresh plan output required')
        out = args.out.resolve()
        prepared = validate_prepared(args.prepared.resolve())
        roots = [Path(row['root']).resolve() for group in ('sources', 'trees') for row in prepared[group].values()]
        r002f = (admit_r002f(args.r002f_prepared, args.r002f_process)
                 if args.r002f_prepared and args.r002f_process else None)
        if r002f and r002f['status'] == 'PASS':
            roots.extend(Path(row['root']).resolve() for row in r002f['trees'].values())
        if any(root == out or root in out.parents for root in roots):
            raise ValueError('plan output must be outside source trees')
        out.mkdir(parents=True, mode=0o700)
        admitted_out = out
        executable(args.python_playwright)
        executable(args.node)
        dependency(args.node_modules / 'playwright', 'playwright', '1.62.1')
        dependency(args.pngjs, 'pngjs', '7.0.0')
        plan = make_plan(prepared, out, python_playwright=args.python_playwright, node=args.node,
                         node_modules=args.node_modules, pngjs=args.pngjs, engine=args.engine, r003f_dpr=args.r003f_dpr,
                         include_r002f=args.r002f, r002f_preparation=r002f, r002f_dpr=args.r002f_dpr,
                         r002f_rounds=args.r002f_rounds, r002f_section=args.r002f_section,
                         work_orders=args.work_orders, retain_evidence=args.retain_evidence,
                         r0035_guard=args.r0035_guard, r0035_scope=args.r0035_scope, r0035_mode=args.r0035_mode)
        check_star_plan(prepared, plan['r0035Plan'])
        write_json(Path(plan['r0035PlanPath']), plan['r0035Plan'])
        plan['preparedReceipt'] = {'path': str(args.prepared.resolve()), 'sha256': digest(args.prepared)}
        print(json.dumps(plan, indent=2))
    except Exception as error:
        if admitted_out is not None:
            write_json(admitted_out / 'plan-error.json', {'status': 'INCOMPLETE', 'error': str(error)})
        print('LANE PLAN INCOMPLETE; inspect private preparation or plan receipts', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
