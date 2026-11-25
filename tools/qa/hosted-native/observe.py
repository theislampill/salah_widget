"""Run admitted recipes sequentially in fresh Linux network/PID namespaces.

This wrapper qualifies observation isolation, not product acceptance. Every
recipe stream and all result detail remain beneath the private capture root.
"""
import argparse
import errno
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

CAP_FIELDS = ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')
RAIN_CELLS = ('day-rain', 'day-drizzle', 'day-thunder', 'night', 'twilight',
              'reduced-none', 'reduced-still', 'motion-full', 'dry')
HERE = Path(__file__).resolve().parent
ISOLATION_EXIT = 86


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')
    path.chmod(0o600)


def validate_snapshot(snapshot, outer_netns):
    if len(snapshot['uids']) != 3 or min(snapshot['uids']) <= 0 or len(set(snapshot['uids'])) != 1:
        raise ValueError('nonroot real/effective/saved UID required')
    if len(snapshot['gids']) != 3 or min(snapshot['gids']) <= 0 or len(set(snapshot['gids'])) != 1:
        raise ValueError('nonroot real/effective/saved GID required')
    if snapshot['groups']:
        raise ValueError('supplementary groups retained')
    if not outer_netns or snapshot['netns'] == outer_netns:
        raise ValueError('fresh network namespace required')
    links = snapshot['links']
    if len(links) != 1 or links[0]['ifname'] != 'lo' or not {'LOOPBACK', 'UP'} <= set(links[0]['flags']):
        raise ValueError('only an active loopback interface is allowed')
    for route in snapshot['routes4'] + snapshot['routes6']:
        dst = route.get('dst')
        if route.get('dev') != 'lo' or route.get('gateway') or dst in (None, 'default'):
            raise ValueError('non-loopback route')
        network = ipaddress.ip_network(dst, strict=False)
        if not network.is_loopback and str(network) != 'ff00::/8':
            raise ValueError('external destination route')
    for name in CAP_FIELDS:
        if int(snapshot['status'][name], 16) != 0:
            raise ValueError('retained capability ' + name)
    if snapshot['status'].get('NoNewPrivs') != '1':
        raise ValueError('no-new-privileges missing')
    if snapshot['externalSocketErrno'] not in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        raise ValueError('external socket was not refused by routing boundary')


def kernel_snapshot():
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect(('192.0.2.1', 443)); result = 0
        except OSError as exc:
            result = exc.errno
    ip = '/usr/sbin/ip' if Path('/usr/sbin/ip').exists() else '/sbin/ip'
    read_ip = lambda *args: json.loads(subprocess.check_output([ip, '-j', *args], text=True))
    return {'uids': list(os.getresuid()), 'gids': list(os.getresgid()), 'groups': os.getgroups(),
            'netns': os.readlink('/proc/self/ns/net'), 'links': read_ip('link', 'show'),
            'routes4': read_ip('-4', 'route', 'show', 'table', 'all'),
            'routes6': read_ip('-6', 'route', 'show', 'table', 'all'),
            'status': {k: status[k].strip() for k in (*CAP_FIELDS, 'NoNewPrivs')},
            'externalSocketErrno': result}


def clean_environment(node, python, task, browsers, modules, baseline, research):
    task = Path(task)
    return {'PATH': ':'.join((str(Path(node).parent), str(Path(python).parent), '/usr/local/bin',
                             '/usr/bin', '/bin', '/usr/sbin', '/sbin')),
            'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
            'PLAYWRIGHT_BROWSERS_PATH': str(browsers), 'NODE_PATH': str(modules),
            'TMPDIR': str(task/'temporary'), 'XDG_CACHE_HOME': str(task/'cache'),
            'XDG_CONFIG_HOME': str(task/'config'), 'XDG_RUNTIME_DIR': str(task/'runtime'),
            'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'safe.directory',
            'GIT_CONFIG_VALUE_0': str(baseline), 'GIT_CONFIG_KEY_1': 'safe.directory',
            'GIT_CONFIG_VALUE_1': str(research)}


def run_bounded(argv, cwd, env, stdout, stderr, timeout):
    stdout, stderr = Path(stdout), Path(stderr)
    stdout.parent.mkdir(parents=True, exist_ok=True); stderr.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with stdout.open('wb') as out, stderr.open('wb') as err:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try: proc.wait(timeout=2)
            except subprocess.TimeoutExpired: pass
            # The leader can exit before its descendants. Kill the process group
            # even when wait() already returned; namespace teardown is a second fence.
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
        except BaseException:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
            raise
    return {'returncode': proc.returncode, 'timedOut': timed_out,
            'elapsedSeconds': time.monotonic() - started}


def classify_lane(lane, returncode, timed_out=False):
    kind = lane['result']['kind']
    result = {'status': 'INCOMPLETE', 'stopAll': False, 'returncode': returncode, 'timedOut': timed_out}
    if returncode == ISOLATION_EXIT or kind == 'r003f-b0' and returncode == 3:
        return {**result, 'status': 'ISOLATION_FAIL', 'stopAll': True}
    try: body = json.loads(Path(lane['result']['path']).read_text())
    except (OSError, ValueError): body = None
    # Preserve observed recipe failures even if later acquisition is interrupted.
    # Return codes alone do not distinguish failed admission from missing evidence.
    if kind == 'r003f-b0':
        if isinstance(body, dict) and (body.get('isolation', {}).get('ok') is False
                                      or body.get('status') == 'ISOLATION FAIL'):
            return {**result, 'status': 'ISOLATION_FAIL', 'stopAll': True}
        if returncode == 4 or isinstance(body, dict) and body.get('status') == 'FAIL (Andon)':
            return {**result, 'status': 'ANDON'}
    elif kind == 'r0035-trials' and isinstance(body, list):
        if any(isinstance(row, dict) and row.get('qualification', {}).get('verdict') == 'failed' for row in body):
            return {**result, 'status': 'FAIL'}
    if timed_out: return result
    defaults = {'r003f-b0': {'1': 'FAIL', '2': 'INCOMPLETE'},
                'r0040-options': {'1': 'FAIL'}, 'r0035-trials': {'1': 'INCOMPLETE'},
                'r002f-probe': {'1': 'FAIL', '2': 'INCOMPLETE'}}
    declared = lane.get('exitStatuses', defaults.get(kind, {})).get(str(returncode))
    if body is None:
        return {**result, 'status': 'FAIL' if declared == 'FAIL' else 'INCOMPLETE'}
    if kind == 'r003f-b0':
        passed = (isinstance(body, dict) and body.get('status') == 'MEASURED'
                  and body.get('isolation', {}).get('ok') is True)
    elif kind == 'r0040-options':
        cells = body.get('cells', []) if isinstance(body, dict) else []
        passed = (isinstance(cells, list) and len(cells) == len(RAIN_CELLS)
                  and all(isinstance(c, dict) for c in cells)
                  and sorted(c.get('id', '') for c in cells) == sorted(RAIN_CELLS))
    elif kind == 'r0035-trials':
        expected_rows = lane['result'].get('expectedRows', 3)
        expected_arms = lane['result'].get('expectedArms', ['main', 'unmodified', 'mitigated'])
        passed = (isinstance(body, list) and len(body) == expected_rows and expected_rows > 0
                  and all(isinstance(row, dict) for row in body)
                  and expected_rows % len(expected_arms) == 0
                  and sorted(r.get('arm', '') for r in body) == sorted(expected_arms * (expected_rows // len(expected_arms))))
        passed = passed and all(r.get('admitted') is True and r.get('qualification', {}).get('verdict') == 'passed'
                                for r in body)
    elif kind == 'r002f-probe':
        passed = isinstance(body, dict) and body.get('status') == 'PASS'
    else:
        raise ValueError('unknown recipe result kind')
    result['status'] = 'PASS' if returncode == 0 and passed else ('FAIL' if declared == 'FAIL' else 'INCOMPLETE')
    return result


def namespace_status(lane, process, inner):
    """An inner observation cannot overrule abnormal wrapper completion."""
    admitted = (isinstance(inner, dict) and inner.get('id') == lane['id']
                and inner.get('status') in ('PASS', 'FAIL', 'INCOMPLETE', 'ANDON', 'ISOLATION_FAIL')
                and isinstance(inner.get('stopAll'), bool))
    result = {**(inner if admitted else {}), 'id': lane['id'],
              'innerStatus': inner, 'namespaceProcess': process}
    if process['returncode'] == ISOLATION_EXIT or admitted and inner['status'] == 'ISOLATION_FAIL':
        result.update(status='ISOLATION_FAIL', stopAll=True)
    elif process['returncode'] != 0 or process['timedOut'] or not admitted:
        result.update(status='ISOLATION_UNCONFIRMED', stopAll=True,
                      reason='namespace completion or inner admission receipt is unconfirmed')
    return result


def controls(args, runtime, label):
    folder = args.task/'capture'/'isolation'/label
    folder.mkdir(parents=True, exist_ok=False)
    receipt = {'protocol': 'salah-hosted-native-isolation/1', 'passed': False,
               'outerNetns': args.outer_netns, 'uid': os.getuid()}
    try:
        snapshot = kernel_snapshot(); receipt['kernel'] = snapshot; receipt['netns'] = snapshot['netns']
        validate_snapshot(snapshot, args.outer_netns)
        env = dict(os.environ)
        env['PLAYWRIGHT_BROWSERS_PATH'] = str(args.task/'node-browsers')
        command = [runtime['node'], str(HERE/'browser-control.cjs'), runtime['playwright'], str(folder/'browser.json')]
        result = run_bounded(command, str(HERE), env, folder/'browser.stdout', folder/'browser.stderr', 45)
        receipt['browserProcess'] = result
        if result['returncode'] or result['timedOut']: raise ValueError('real browser boundary control failed')
        browser = json.loads((folder/'browser.json').read_text())
        if browser.get('passed') is not True: raise ValueError('real browser boundary control incomplete')
        receipt['browserControl'] = browser
        # Recheck the namespace after running the real browser, before any recipe.
        validate_snapshot(kernel_snapshot(), args.outer_netns)
        receipt['passed'] = True
    except Exception as exc:
        receipt['error'] = str(exc)
    path = folder/'receipt.json'; write_json(path, receipt)
    if not receipt['passed']: return None
    return str(path)


def inside(args, runtime):
    label = args.lane or 'preparation'
    receipt = controls(args, runtime, label)
    if not receipt: return ISOLATION_EXIT
    os.environ['SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT'] = receipt
    if args.phase == 'prepare':
        destination = args.task/'work'/'prepared'
        command = [runtime['python'], str(HERE/'prepare.py'), '--research', str(args.research),
                   '--baseline', str(args.baseline), '--historical', str(args.historical), '--out', str(destination)]
        result = run_bounded(command, str(HERE), dict(os.environ),
                             args.task/'capture'/'preparation.stdout', args.task/'capture'/'preparation.stderr', 900)
        # Source bodies are public and reproducible; seal only private receipts/logs.
        import shutil
        if (destination/'receipts').exists():
            shutil.copytree(destination/'receipts', args.task/'capture'/'preparation')
        write_json(args.task/'capture'/'preparation-process.json', result)
        if result['returncode'] or result['timedOut']: return 2
        command = [runtime['python'], str(HERE/'lanes.py'), '--plan-json', '--prepared',
                   str(destination/'receipts'/'prepared.json'), '--out', str(args.task/'capture'/'lanes'),
                   '--python-playwright', runtime['python'], '--node', runtime['node'],
                   '--node-modules', runtime['modules'], '--pngjs', runtime['pngjs'], '--engine', args.engine]
        plan = run_bounded(command, str(HERE), dict(os.environ), args.task/'capture'/'lanes.json',
                           args.task/'capture'/'plan.stderr', 30)
        return 0 if plan['returncode'] == 0 and not plan['timedOut'] else 2
    plan = json.loads((args.task/'capture'/'lanes.json').read_text())
    lane = next(x for x in plan['lanes'] if x['id'] == args.lane)
    env = dict(os.environ)
    # Recipe env is declarative data from the reviewed planner; arbitrary variables
    # cannot restore a credential/proxy/loader setting that the wrapper removed.
    for key, value in lane.get('env', {}).items():
        if key not in ('NODE_PATH',): raise ValueError('unapproved lane environment variable')
        env[key] = value
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(args.task/('python-browsers' if lane['result']['kind'] == 'r0035-trials' else 'node-browsers'))
    result = run_bounded(lane['argv'], lane['cwd'], env, lane['stdout'], lane['stderr'], lane['timeoutSeconds'])
    verdict = classify_lane(lane, result['returncode'], result['timedOut'])
    write_json(args.task/'capture'/'lane-status'/(args.lane+'.json'), {**result, **verdict, 'id': args.lane})
    # All in-namespace descendants are also killed when the namespace init exits.
    return ISOLATION_EXIT if verdict['stopAll'] else 0


def isolated_command(args, runtime, phase, lane=None):
    env = clean_environment(runtime['node'], runtime['python'], args.task, args.task/'node-browsers',
                            runtime['modules'], args.baseline, args.research)
    inner = [runtime['python'], str(HERE/'observe.py'), '--task', str(args.task), '--research', str(args.research),
             '--baseline', str(args.baseline), '--historical', str(args.historical), '--engine', args.engine,
             '--inside', '--phase', phase, '--outer-netns', os.readlink('/proc/self/ns/net')]
    if lane: inner += ['--lane', lane]
    return ['/usr/bin/sudo', '-n', '/usr/bin/unshare', '--net', '--pid', '--fork', '--mount-proc',
            '--kill-child=KILL', '/bin/bash', str(HERE/'namespace.sh'), str(os.getuid()), str(os.getgid()),
            *[k+'='+v for k, v in env.items()], *inner]


def outside(args, runtime):
    capture = args.task/'capture'
    parent_env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
    deadline = time.monotonic() + 2640  # leaves sealing/upload time within the job ceiling
    preparation = run_bounded(isolated_command(args, runtime, 'prepare'), str(HERE), parent_env,
                              capture/'namespace-preparation.stdout', capture/'namespace-preparation.stderr', 1020)
    overall = {'protocol': 'salah-hosted-native-observation/1', 'engine': args.engine,
               'preparation': preparation, 'lanes': [], 'status': 'INCOMPLETE'}
    write_json(capture/'observation.json', overall)
    if preparation['returncode'] or preparation['timedOut']:
        overall['status'] = 'ISOLATION_FAIL' if preparation['returncode'] == ISOLATION_EXIT else 'INCOMPLETE'
        write_json(capture/'observation.json', overall); return 2
    plan = json.loads((capture/'lanes.json').read_text())
    if plan.get('protocol') != 'salah-hosted-native-lanes/1' or plan.get('sequential') is not True:
        raise ValueError('unadmitted lane plan')
    stopped = set(); stop_all = False
    for lane in plan['lanes']:
        remaining = deadline - time.monotonic()
        if remaining <= 75:
            status = {'id': lane['id'], 'status': 'NOT_RUN', 'reason': 'bounded observation budget exhausted'}
        elif stop_all or lane['workOrder'] in stopped:
            status = {'id': lane['id'], 'status': 'NOT_RUN', 'reason': 'isolation or scoped Andon'}
        else:
            result = run_bounded(isolated_command(args, runtime, 'lane', lane['id']), str(HERE), parent_env,
                                 capture/'namespaces'/(lane['id']+'.stdout'), capture/'namespaces'/(lane['id']+'.stderr'),
                                 min(lane['timeoutSeconds'] + 75, remaining))
            path = capture/'lane-status'/(lane['id']+'.json')
            try: inner = json.loads(path.read_text())
            except (OSError, ValueError): inner = None
            status = namespace_status(lane, result, inner)
            if status.get('stopAll'): stop_all = True
            if status['status'] == 'ANDON': stopped.add(lane['workOrder'])
        overall['lanes'].append(status); write_json(capture/'observation.json', overall)
    overall['status'] = ('ISOLATION_FAIL' if any(x['status'] == 'ISOLATION_FAIL' for x in overall['lanes']) else
                         'ISOLATION_UNCONFIRMED' if stop_all else
                         'OBSERVED' if overall['lanes'] and all(x['status'] == 'PASS' for x in overall['lanes']) else
                         'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')
    write_json(capture/'observation.json', overall)
    return 0 if overall['status'] == 'OBSERVED' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'research', 'baseline', 'historical'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--engine', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--inside', action='store_true')
    parser.add_argument('--phase', choices=('prepare', 'lane'))
    parser.add_argument('--outer-netns'); parser.add_argument('--lane')
    args = parser.parse_args()
    os.umask(0o077)
    def interrupted(signum, _frame):
        raise InterruptedError('observation interrupted by signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    runtime = json.loads((args.task/'runtime.json').read_text())
    try:
        return inside(args, runtime) if args.inside else outside(args, runtime)
    except Exception as exc:
        write_json(args.task/'capture'/('coordinator-error-'+(args.lane or args.phase or 'outer')+'.json'),
                   {'type': type(exc).__name__, 'error': str(exc)})
        return 2


if __name__ == '__main__': sys.exit(main())
