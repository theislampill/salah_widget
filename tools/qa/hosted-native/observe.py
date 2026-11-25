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
import shutil
import socket
import subprocess
import sys
import time

from lanes import selected_work_orders, star_controls, STAR_DEFAULTS

CAP_FIELDS = ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')
RAIN_CELLS = ('day-rain', 'day-drizzle', 'day-thunder', 'night', 'twilight',
              'reduced-none', 'reduced-still', 'motion-full', 'dry')
HERE = Path(__file__).resolve().parent
ISOLATION_EXIT = 86
VETO_STATUS = 'EXTERNAL_CONTINUATION_VETOED'
VETO_REASON = ('retention wrapper prevented external continuation before the real continue action; '
               'not evidence of an actual network escape')


def read_campaign(path):
    value = json.loads(Path(path).read_text())
    if (not isinstance(value, dict) or value.get('schemaVersion') != 1
            or value.get('engine') not in ('chromium', 'firefox', 'webkit')
            or type(value.get('r003fDpr')) is not int or value['r003fDpr'] not in (1, 2)):
        raise ValueError('unsupported hosted campaign')
    r002f = value.get('r002f')
    if (not isinstance(r002f, dict) or type(r002f.get('enabled')) is not bool
            or type(r002f.get('dpr')) is not int or r002f['dpr'] not in (1, 2, 3)
            or type(r002f.get('rounds')) is not int or not 1 <= r002f['rounds'] <= 10
            or r002f.get('section') not in ('all', 'prayer', 'preview')):
        raise ValueError('unsupported R002F campaign controls')
    if 'workOrders' in value and not isinstance(value['workOrders'], list):
        raise ValueError('work-order selection must be a list')
    selected = selected_work_orders(value.get('workOrders'), r002f['enabled'])
    if 'r0035' in value and (not isinstance(value['r0035'], dict) or 'R0035' not in selected):
        raise ValueError('explicit R0035 controls require a dictionary and selected R0035')
    star_controls(value.get('r0035'))
    if type(value.get('evidenceRetention', False)) is not bool:
        raise ValueError('evidence retention must be boolean')
    return value


def campaign_selection(args):
    if type(getattr(args, 'retain_evidence', False)) is not bool:
        raise ValueError('evidence retention must be boolean')
    return selected_work_orders(getattr(args, 'work_orders', None), getattr(args, 'r002f', False))


def star_campaign(args):
    controls = star_controls({key: getattr(args, 'r0035_'+key, default) for key, default in STAR_DEFAULTS.items()})
    if controls != STAR_DEFAULTS and 'R0035' not in campaign_selection(args):
        raise ValueError('R0035 diagnostic controls require selected R0035 observations')
    return controls


def star_arguments(args):
    return [part for key, value in star_campaign(args).items() for part in ('--r0035-'+key, value)]


def retained_lane(lane):
    evidence = lane.get('evidenceRetention')
    return isinstance(evidence, dict) and evidence.get('instrumented') is True and 86 in lane.get('stopAllOnExit', [])


def admit_plan(plan, args):
    """Require the selected identities; preserve missing observations as blocked rows."""
    selected = campaign_selection(args)
    stars = star_campaign(args)
    retention = getattr(args, 'retain_evidence', False)
    if (plan.get('protocol') != 'salah-hosted-native-lanes/1' or plan.get('sequential') is not True
            or plan.get('workOrders') != selected or plan.get('evidenceRetention') is not retention
            or plan.get('r0035Controls', STAR_DEFAULTS) != stars
            or not isinstance(plan.get('lanes'), list)):
        raise ValueError('unadmitted lane plan or campaign controls')
    engine = args.engine
    population = [(f'r0040-{engine}', 'R0040', 720),
                  (f'r003f-b0-{engine}-dpr{getattr(args, "r003f_dpr", 1)}', 'R003F', 900),
                  (f'r0035-{engine}-timing', 'R0035', 480), (f'r0035-{engine}-capture', 'R0035', 480),
                  (f'r002f-{engine}-dpr{getattr(args, "r002f_dpr", 1)}', 'R002F', 900)]
    population = [row for row in population if row[1] != 'R0035'
                  or stars['mode'] == 'both' or row[0].endswith('-'+stars['mode'])]
    expected = {identifier: (order, timeout) for identifier, order, timeout in population if order in selected}
    actual = {}
    for lane in plan['lanes']:
        if (not isinstance(lane, dict) or not isinstance(lane.get('id'), str) or lane['id'] not in expected
                or lane['id'] in actual or lane.get('workOrder') != expected[lane['id']][0]):
            raise ValueError('duplicate, unknown or unselected lane identity')
        evidence = lane.get('evidenceRetention')
        instrumented = isinstance(evidence, dict) and evidence.get('instrumented') is True
        if (('evidenceRetention' in lane and not instrumented)
                or instrumented != (retention and lane['workOrder'] in ('R0040', 'R0035'))
                or instrumented and not retained_lane(lane)):
            raise ValueError('lane retention mode differs from the selected campaign')
        actual[lane['id']] = lane
    return [actual.get(identifier, {'id': identifier, 'workOrder': order, 'timeoutSeconds': timeout,
                                   'preparation': {'status': 'INCOMPLETE',
                                                   'reason': f'requested {order} lane {identifier} is missing from the plan'}})
            for identifier, (order, timeout) in expected.items()]


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


def r002f_report_status(body, lane, returncode, timed_out):
    """A complete selected population is necessary for PASS, never a status word."""
    if not isinstance(body, dict) or body.get('protocol') != 'r002f-hosted-native/1':
        return 'FAIL' if returncode == 1 else 'INCOMPLETE'
    pairs, preview = body.get('prayerPairs'), body.get('preview')
    def verdict(row):
        value = row.get('verdict') if isinstance(row, dict) else None
        return value.get('status') if isinstance(value, dict) else None
    recorded = [verdict(row) for group in (pairs, preview) if isinstance(group, list) for row in group]
    if body.get('status') == 'FAIL' or 'FAIL' in recorded:
        return 'FAIL'
    if body.get('status') in ('INCOMPLETE', 'INCONCLUSIVE'):
        return body['status']
    if timed_out or not isinstance(pairs, list) or not isinstance(preview, list):
        return 'INCOMPLETE'
    expected = lane['result']
    rounds, section = expected.get('expectedRounds'), expected.get('expectedSection')
    if (type(rounds) is not int or not 1 <= rounds <= 10 or section not in ('all', 'prayer', 'preview')
            or type(body.get('dpr')) is not int or type(body.get('rounds')) is not int
            or body.get('engine') != lane.get('engine') or body.get('dpr') != lane.get('dpr')
            or body.get('rounds') != rounds or body.get('section') != section
            or not expected.get('expectedObserverSha256')
            or body.get('observerSha256') != expected['expectedObserverSha256']):
        return 'INCOMPLETE'
    sources = body.get('sources')
    for arm, index in (('baseline', '88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1'),
                       ('candidate', '55a8bdbc7b7ab5cb53ede3b58c0ef1e4101c7c89bc6936860bd4bc5f3acb8fe2')):
        source = sources.get(arm) if isinstance(sources, dict) else None
        if not isinstance(source, dict) or source.get('indexSha256') != index:
            return 'INCOMPLETE'
    wanted_pairs = {(scenario, round_) for round_ in range(1, rounds + 1)
                    for scenario in ('fajr', 'maghrib', 'midnight')} if section != 'preview' else set()
    actual_pairs = []
    for row in pairs:
        if not isinstance(row, dict) or type(row.get('round')) is not int or not isinstance(row.get('scenario'), str):
            return 'INCOMPLETE'
        actual_pairs.append((row['scenario'], row['round']))
        if any(row.get(arm) != f'{arm}-{row["scenario"]}-{row["round"]}.json' for arm in ('baseline', 'candidate')):
            return 'INCOMPLETE'
    wanted_preview = {'baseline', 'candidate'} if section != 'prayer' else set()
    actual_preview = []
    for row in preview:
        if not isinstance(row, dict) or not isinstance(row.get('arm'), str) or row.get('file') != row['arm']+'-preview.json':
            return 'INCOMPLETE'
        actual_preview.append(row['arm'])
    if (len(actual_pairs) != len(wanted_pairs) or set(actual_pairs) != wanted_pairs
            or len(actual_preview) != len(wanted_preview) or set(actual_preview) != wanted_preview):
        return 'INCOMPLETE'
    statuses = [verdict(row) for row in pairs]
    for row in preview:
        if row['arm'] == 'baseline' and verdict(row) != 'OBSERVED':
            return 'INCOMPLETE'
        statuses.append('PASS' if row['arm'] == 'baseline' and verdict(row) == 'OBSERVED' else verdict(row))
    if any(status not in ('PASS', 'INCONCLUSIVE') for status in statuses):
        return 'INCOMPLETE'
    if 'INCONCLUSIVE' in statuses:
        return 'INCONCLUSIVE'
    if returncode == 1:
        return 'FAIL'
    return 'PASS' if body.get('status') == 'PASS' and statuses and returncode == 0 else 'INCOMPLETE'


def classify_lane(lane, returncode, timed_out=False):
    kind = lane['result']['kind']
    result = {'status': 'INCOMPLETE', 'stopAll': False, 'returncode': returncode, 'timedOut': timed_out}
    if 'evidenceRetention' in lane:
        result['evidenceRetention'] = lane['evidenceRetention']
    if returncode == 86 and retained_lane(lane):
        return {**result, 'status': VETO_STATUS, 'stopAll': True, 'reason': VETO_REASON}
    if returncode == ISOLATION_EXIT or kind == 'r003f-b0' and returncode == 3:
        return {**result, 'status': 'ISOLATION_FAIL', 'stopAll': True}
    try: body = json.loads(Path(lane['result']['path']).read_text())
    except (OSError, ValueError): body = None
    if kind == 'r002f-probe':
        return {**result, 'status': r002f_report_status(body, lane, returncode, timed_out)}
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
    else:
        raise ValueError('unknown recipe result kind')
    result['status'] = 'PASS' if returncode == 0 and passed else ('FAIL' if declared == 'FAIL' else 'INCOMPLETE')
    return result


def namespace_status(lane, process, inner):
    """An inner observation cannot overrule abnormal wrapper completion."""
    admitted = (isinstance(inner, dict) and inner.get('id') == lane['id']
                and inner.get('status') in ('PASS', 'FAIL', 'INCOMPLETE', 'INCONCLUSIVE', 'ANDON', 'ISOLATION_FAIL', VETO_STATUS)
                and isinstance(inner.get('stopAll'), bool))
    if admitted:
        admitted = inner['stopAll'] == (inner['status'] in ('ISOLATION_FAIL', VETO_STATUS))
    if admitted and inner['status'] == VETO_STATUS:
        admitted = retained_lane(lane) and inner.get('returncode') == 86 and inner['stopAll'] is True
    result = {**(inner if admitted else {}), 'id': lane['id'],
              'innerStatus': inner, 'namespaceProcess': process}
    if process['returncode'] == ISOLATION_EXIT or admitted and inner['status'] == 'ISOLATION_FAIL':
        result.update(status='ISOLATION_FAIL', stopAll=True, reason='namespace boundary reported isolation failure')
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
    selected = campaign_selection(args)
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
        if (destination/'receipts').exists():
            shutil.copytree(destination/'receipts', args.task/'capture'/'preparation')
        write_json(args.task/'capture'/'preparation-process.json', result)
        if result['returncode'] or result['timedOut']: return 2
        r002f_destination = args.task/'work'/'r002f-prepared'
        if getattr(args, 'r002f', False):
            command = [runtime['python'], str(HERE/'r002f_prepare.py'), '--research', str(args.research),
                       '--baseline', str(args.baseline), '--out', str(r002f_destination), '--node', runtime['node']]
            try:
                optional = run_bounded(command, str(HERE), dict(os.environ),
                                       args.task/'capture'/'r002f-preparation.stdout',
                                       args.task/'capture'/'r002f-preparation.stderr', 900)
            except (OSError, ValueError) as error:
                optional = {'returncode': None, 'timedOut': False, 'error': str(error)}
            write_json(args.task/'capture'/'r002f-preparation-process.json',
                       {**optional, 'argv': command, 'cwd': str(HERE), 'timeoutSeconds': 900})
            # The wrapper writes only receipts/logs at its root. Its source arms
            # and materialized patch stay outside the encrypted evidence capture.
            retained = args.task/'capture'/'r002f-preparation'
            retained.mkdir(mode=0o700)
            if r002f_destination.exists():
                for path in sorted(r002f_destination.iterdir()):
                    if path.is_file() and not path.is_symlink() and path.suffix in ('.json', '.stdout', '.stderr'):
                        shutil.copy2(path, retained/path.name)
            # Failed optional preparation is interpreted by the planner as a
            # blocked R002F lane; it cannot erase the already prepared recipes.
        command = [runtime['python'], str(HERE/'lanes.py'), '--plan-json', '--prepared',
                   str(destination/'receipts'/'prepared.json'), '--out', str(args.task/'capture'/'lanes'),
                   '--python-playwright', runtime['python'], '--node', runtime['node'],
                   '--node-modules', runtime['modules'], '--pngjs', runtime['pngjs'], '--engine', args.engine,
                   '--r003f-dpr', str(getattr(args, 'r003f_dpr', 1)), '--work-orders', *selected]
        command += star_arguments(args)
        if getattr(args, 'retain_evidence', False):
            command.append('--retain-evidence')
        if getattr(args, 'r002f', False):
            command += ['--r002f', '--r002f-prepared', str(r002f_destination/'build-result.json'),
                        '--r002f-process', str(args.task/'capture'/'r002f-preparation-process.json'),
                        '--r002f-dpr', str(args.r002f_dpr), '--r002f-rounds', str(args.r002f_rounds),
                        '--r002f-section', args.r002f_section]
        plan = run_bounded(command, str(HERE), dict(os.environ), args.task/'capture'/'lanes.json',
                           args.task/'capture'/'plan.stderr', 30)
        return 0 if plan['returncode'] == 0 and not plan['timedOut'] else 2
    plan = json.loads((args.task/'capture'/'lanes.json').read_text())
    lane = next(x for x in admit_plan(plan, args) if x['id'] == args.lane)
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
    # A retained child veto is carried by its admitted receipt, including its
    # actual exit 86. Normal coordinator completion does not claim child success;
    # outer 86 remains reserved for an actual namespace/boundary failure.
    return ISOLATION_EXIT if verdict['stopAll'] and verdict['status'] != VETO_STATUS else 0


def isolated_command(args, runtime, phase, lane=None):
    selected = campaign_selection(args)
    env = clean_environment(runtime['node'], runtime['python'], args.task, args.task/'node-browsers',
                            runtime['modules'], args.baseline, args.research)
    inner = [runtime['python'], str(HERE/'observe.py'), '--task', str(args.task), '--research', str(args.research),
             '--baseline', str(args.baseline), '--historical', str(args.historical), '--engine', args.engine,
             '--r003f-dpr', str(getattr(args, 'r003f_dpr', 1)), '--work-orders', *selected,
             '--inside', '--phase', phase, '--outer-netns', os.readlink('/proc/self/ns/net')]
    inner += star_arguments(args)
    if getattr(args, 'retain_evidence', False):
        inner.append('--retain-evidence')
    if getattr(args, 'r002f', False):
        inner += ['--r002f', '--r002f-dpr', str(args.r002f_dpr), '--r002f-rounds', str(args.r002f_rounds),
                  '--r002f-section', args.r002f_section]
    if lane: inner += ['--lane', lane]
    return ['/usr/bin/sudo', '-n', '/usr/bin/unshare', '--net', '--pid', '--fork', '--mount-proc',
            '--kill-child=KILL', '/bin/bash', str(HERE/'namespace.sh'), str(os.getuid()), str(os.getgid()),
            *[k+'='+v for k, v in env.items()], *inner]


def outside(args, runtime):
    selected = campaign_selection(args)
    capture = args.task/'capture'
    parent_env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
    deadline = time.monotonic() + 2640  # leaves sealing/upload time within the job ceiling
    preparation = run_bounded(isolated_command(args, runtime, 'prepare'), str(HERE), parent_env,
                              capture/'namespace-preparation.stdout', capture/'namespace-preparation.stderr',
                              1920 if getattr(args, 'r002f', False) else 1020)
    overall = {'protocol': 'salah-hosted-native-observation/1', 'engine': args.engine,
               'workOrders': selected, 'evidenceRetention': getattr(args, 'retain_evidence', False),
               'r0035Controls': star_campaign(args),
               'preparation': preparation, 'lanes': [], 'status': 'INCOMPLETE'}
    write_json(capture/'observation.json', overall)
    if preparation['returncode'] or preparation['timedOut']:
        overall['status'] = 'ISOLATION_FAIL' if preparation['returncode'] == ISOLATION_EXIT else 'INCOMPLETE'
        write_json(capture/'observation.json', overall); return 2
    plan = json.loads((capture/'lanes.json').read_text())
    lanes = admit_plan(plan, args)
    stopped = set(); stop_all = False; stop_reason = None
    for lane in lanes:
        remaining = deadline - time.monotonic()
        if lane.get('preparation', {}).get('status', 'PASS') != 'PASS':
            status = {'id': lane['id'], 'status': 'NOT_RUN', 'preparationStatus': 'INCOMPLETE',
                      'reason': lane['preparation'].get('reason', 'lane preparation incomplete')}
        elif remaining <= 75:
            status = {'id': lane['id'], 'status': 'NOT_RUN', 'reason': 'bounded observation budget exhausted'}
        elif stop_all or lane['workOrder'] in stopped:
            status = {'id': lane['id'], 'status': 'NOT_RUN',
                      'reason': stop_reason if stop_all else 'workstream stopped by scoped Andon'}
        else:
            result = run_bounded(isolated_command(args, runtime, 'lane', lane['id']), str(HERE), parent_env,
                                 capture/'namespaces'/(lane['id']+'.stdout'), capture/'namespaces'/(lane['id']+'.stderr'),
                                 min(lane['timeoutSeconds'] + 75, remaining))
            path = capture/'lane-status'/(lane['id']+'.json')
            try: inner = json.loads(path.read_text())
            except (OSError, ValueError): inner = None
            status = namespace_status(lane, result, inner)
            if status.get('stopAll'):
                stop_all = True
                stop_reason = status.get('reason', status['status'])
            if status['status'] == 'ANDON': stopped.add(lane['workOrder'])
        status['workOrder'] = lane['workOrder']
        overall['lanes'].append(status); write_json(capture/'observation.json', overall)
    overall['status'] = ('ISOLATION_FAIL' if any(x['status'] == 'ISOLATION_FAIL' for x in overall['lanes']) else
                         'ISOLATION_UNCONFIRMED' if any(x['status'] == 'ISOLATION_UNCONFIRMED' for x in overall['lanes']) else
                         VETO_STATUS if any(x['status'] == VETO_STATUS for x in overall['lanes']) else
                         'OBSERVED' if overall['lanes'] and all(x['status'] == 'PASS' for x in overall['lanes']) else
                         'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')
    write_json(capture/'observation.json', overall)
    return 0 if overall['status'] == 'OBSERVED' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'research', 'baseline', 'historical'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--engine', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--r003f-dpr', type=int, choices=(1, 2), default=1)
    parser.add_argument('--work-orders', nargs='+')
    parser.add_argument('--retain-evidence', action='store_true')
    parser.add_argument('--r0035-guard', choices=('default', 'off'), default='default')
    parser.add_argument('--r0035-scope', choices=('all', 'preview-members'), default='all')
    parser.add_argument('--r0035-mode', choices=('both', 'timing', 'capture'), default='both')
    parser.add_argument('--r002f', action='store_true')
    parser.add_argument('--r002f-dpr', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--r002f-rounds', type=int, choices=range(1, 11), default=1)
    parser.add_argument('--r002f-section', choices=('all', 'prayer', 'preview'), default='all')
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
        if args.campaign:
            campaign = read_campaign(args.campaign)
            args.engine = campaign['engine']; args.r003f_dpr = campaign['r003fDpr']
            args.r002f = campaign['r002f']['enabled']; args.r002f_dpr = campaign['r002f']['dpr']
            args.r002f_rounds = campaign['r002f']['rounds']; args.r002f_section = campaign['r002f']['section']
            args.work_orders = campaign.get('workOrders'); args.retain_evidence = campaign.get('evidenceRetention', False)
            for key, value in star_controls(campaign.get('r0035')).items():
                setattr(args, 'r0035_'+key, value)
            write_json(args.task/'capture'/'campaign.json', campaign)
        args.work_orders = campaign_selection(args)
        star_campaign(args)
        return inside(args, runtime) if args.inside else outside(args, runtime)
    except Exception as exc:
        write_json(args.task/'capture'/('coordinator-error-'+(args.lane or args.phase or 'outer')+'.json'),
                   {'type': type(exc).__name__, 'error': str(exc)})
        return 2


if __name__ == '__main__': sys.exit(main())
