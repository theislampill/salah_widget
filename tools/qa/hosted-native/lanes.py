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

from prepare import BASELINE, RESEARCH, digest, validate_prepared, write_json


def make_plan(prepared, out, *, python_playwright, node, node_modules, pngjs,
              engine='chromium', r003f_dpr=1):
    if engine not in ('chromium', 'firefox', 'webkit') or r003f_dpr not in (1, 2):
        raise ValueError('unsupported engine or R003F DPR')
    research = Path(prepared['sources']['research']['root'])
    historical = Path(prepared['sources']['historical']['root'])
    roots = {key: Path(value['root']) for key, value in prepared['trees'].items()}
    module = node_modules / 'playwright'
    star_plan_path = out / 'r0035-plan.json'
    arms = {'main': {'root': str(roots['main']), 'commit': BASELINE, 'flags': ''}}
    for label, writes in (('unmodified', 'full'), ('mitigated', 'changed')):
        arms[label] = {'root': str(roots['r0035']), 'commit': RESEARCH,
                       'flags': f'&r35arm={writes}&r35scope=all&r35amplitude=1&r35glass=0.5&r35margin=4',
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
        star = lane(f'r0035-{engine}-{label}', 'R0035', 1, 480, 'r0035-trials', 'summary.json',
                    {'0': 'INSPECT ADMISSION', '1': 'INCOMPLETE'})
        star['argv'] = list(map(str, [python_playwright, research / 'tools/r0035/native_trials.py',
                                     star_plan_path, star['output'], '--engine', engine, '--rounds', 1,
                                     '--seconds', 15, '--clock', 'ordinary', '--scene', 'dark', '--motion', 'normal']))
        star['result'].update(expectedRows=3, expectedArms=['main', 'unmodified', 'mitigated'],
                              requiresEveryRowAdmitted=True, capture=capture)
        if capture:
            star['argv'].append('--capture')
            star['dependsOn'] = [entries[-2]['id']]
            star['dependencyPolicy'] = 'finished; retain failed timing, classify captures independently'
    return {'schemaVersion': 1, 'protocol': 'salah-hosted-native-lanes/1', 'sequential': True,
            'scope': 'Initial native observations only; no work-order acceptance or owner selection.',
            'r0035PlanPath': str(star_plan_path), 'r0035Plan': star_plan, 'lanes': entries,
            'failurePolicy': {'isolation': 'stop all observations', 'R003FAndon': 'stop R003F progression',
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
    args = parser.parse_args()
    os.umask(0o077)
    admitted_out = None
    try:
        if args.out.exists() or args.out.is_symlink():
            raise ValueError('fresh plan output required')
        out = args.out.resolve()
        prepared = validate_prepared(args.prepared.resolve())
        roots = [Path(row['root']).resolve() for group in ('sources', 'trees') for row in prepared[group].values()]
        if any(root == out or root in out.parents for root in roots):
            raise ValueError('plan output must be outside source trees')
        out.mkdir(parents=True, mode=0o700)
        admitted_out = out
        executable(args.python_playwright)
        executable(args.node)
        dependency(args.node_modules / 'playwright', 'playwright', '1.62.1')
        dependency(args.pngjs, 'pngjs', '7.0.0')
        plan = make_plan(prepared, out, python_playwright=args.python_playwright, node=args.node,
                         node_modules=args.node_modules, pngjs=args.pngjs, engine=args.engine, r003f_dpr=args.r003f_dpr)
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
