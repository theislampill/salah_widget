#!/usr/bin/env python3
"""Native-free refusal controls for exact runner dispatch and system acquisition."""
import copy
import base64
from contextlib import contextmanager, ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def feature(test, name):
    path = HERE / (name + '.py')
    test.assertTrue(path.is_file(), name + ' is not implemented')
    spec = importlib.util.spec_from_file_location(name + '_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def campaign(bfcache=True):
    return {'schemaVersion': 1, 'engine': 'chromium', 'workOrders': ['R002F'] if bfcache else ['R0040'],
            'r002f': {'enabled': bfcache, 'dpr': 1, 'rounds': 1, 'section': 'all'},
            'r002fRoute': 'bfcache-witness' if bfcache else 'offscreen', 'r003fDpr': 1,
            'r003fHarness': 'published', 'r0040Mode': 'options', 'evidenceRetention': False,
            'r0035Stages': False, 'r0035Costs': False, 'r0035Psf': False}


def context_fixture(module, job):
    return module.workflow_context(job, {
        'GITHUB_JOB': job, 'GITHUB_REPOSITORY': 'theislampill/salah_widget',
        'GITHUB_REF': 'refs/heads/chatgpt/hosted-native-research-20261125', 'GITHUB_SHA': 'a' * 40,
        'GITHUB_WORKFLOW_REF': 'theislampill/salah_widget/.github/workflows/research-native-pilot.yml@refs/heads/chatgpt/hosted-native-research-20261125',
        'GITHUB_WORKFLOW_SHA': 'a' * 40, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1',
        'GITHUB_EVENT_NAME': 'push', 'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
        'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64', 'RUNNER_NAME': 'synthetic-source-control-' + job})


def host_fixture(version):
    return {'release': {'ID': 'ubuntu', 'VERSION_ID': version, 'VERSION_CODENAME': 'noble' if version == '24.04' else 'jammy'},
            'kernel': {'sysname': 'Linux', 'machine': 'x86_64'}, 'imageOS': 'ubuntu24' if version == '24.04' else 'ubuntu22',
            'imageVersion': 'SYNTHETIC_SOURCE_CONTROL_ONLY'}


def packet_fixture(module, selected):
    sources = {'commit': 'a' * 40, 'tree': 'b' * 40, 'files': {'actual-source.py': {'bytes': 3, 'sha256': 'c' * 64, 'mode': '100644', 'gitBlob': 'd' * 40}}}
    value = {'protocol': module.PROTOCOL, 'sourceOnly': True, 'nativeObservation': False, 'selection': selected,
             'sources': sources, 'context': context_fixture(module, 'select_runner'), 'host': host_fixture('22.04')}
    return value, sources, context_fixture(module, 'observe'), host_fixture(selected['version'])


def retain_control(name, body, folder=None):
    """Optional author/reviewer retention; never changes any tested predicate."""
    target = os.environ.get('SALAH_BFCACHE_CONTROL_EVIDENCE')
    if not target: return
    target = Path(target) / name; target.mkdir(parents=True)
    if folder is not None:
        for path in Path(folder).iterdir():
            if path.is_file() and not path.is_symlink(): shutil.copyfile(path, target / path.name)
    (target / 'control.json').write_text(json.dumps({'scope': 'SOURCE_CONTROL_ONLY', 'nativeObservation': False, 'actual': body}, indent=2) + '\n')


@contextmanager
def bootstrap_metadata_fixture(test, module, read_error=None):
    """Synthetic UID/mode observations; real receipt I/O and no command authority."""
    with tempfile.TemporaryDirectory(prefix='bfcache-bootstrap-metadata-control-') as directory, ExitStack() as stack:
        root = Path(directory); task = root / 'task'; folder = task / 'capture/r002f-bfcache-tools'
        folder.mkdir(parents=True, mode=0o700)
        fake = root / 'synthetic-system'; fake.mkdir()
        actual_record = module.tools.file_record; literals = {}; rows = {}; calls = []
        for name in module.BOOTSTRAP:
            path = fake / name; path.write_bytes(('SOURCE_CONTROL_ONLY metadata ' + name).encode())
            path.chmod(0o644 if name in ('archiveKeyring', 'caCertificates') else 0o755)
            literals[name] = str(path); rows[name] = actual_record(path, system=True)
            rows[name]['uid'] = 0  # Explicit metadata fixture, never actual root custody.
        names = {value: name for name, value in literals.items()}
        def record(path, **kwargs):
            name = names.get(str(path))
            if name is None: return actual_record(path, **kwargs)
            test.assertEqual(kwargs, {'system': True}); calls.append(name)
            if name == read_error: raise OSError('SOURCE_CONTROL_ONLY descriptor read failed')
            return copy.deepcopy(rows[name])
        selected = {'scope': 'SOURCE_CONTROL_ONLY', 'selection': {
            'scope': 'R002F_BFCACHE_UBUNTU24_DIAGNOSTIC', 'runner': 'ubuntu-24.04'}}
        stack.enter_context(patch.object(module, 'BOOTSTRAP', literals))
        stack.enter_context(patch.object(module.tools, 'file_record', side_effect=record))
        stack.enter_context(patch.object(module.runner, 'current', return_value=selected))
        workspace = stack.enter_context(patch.object(module, 'create_workspace',
            side_effect=AssertionError('metadata control must stop before package configuration')))
        yield task, folder, literals, rows, calls, workspace


@contextmanager
def package_transport_fixture(test, module, fault):
    """Mock APT/root authority; only harmless Python children actually execute.

    This fixture checks orchestration and readmission. Its explicit synthetic
    root marker is rejected by the real privileged reader and is never native evidence.
    """
    with tempfile.TemporaryDirectory(prefix='bfcache-source-package-fixture-') as directory, ExitStack() as stack:
        root = Path(directory); task = root / 'task'; folder = task / 'capture/r002f-bfcache-tools'; folder.mkdir(parents=True, mode=0o700)
        (task / 'capture').chmod(0o700); task.chmod(0o700)
        fake = root / 'synthetic-system'; fake.mkdir()
        actual_record = module.tools.file_record
        for name in module.REQUIRED:
            (fake / name).write_bytes(('SOURCE_CONTROL_ONLY ' + name).encode()); (fake / name).chmod(0o755)
        for name in ('status', 'md5sums'): (fake / name).write_text('SOURCE_CONTROL_ONLY ' + name)
        runner_file = root / 'synthetic-runner.json'; runner_file.write_text('{"scope":"SOURCE_CONTROL_ONLY"}\n')
        runner = {'receipt': actual_record(runner_file), 'selection': {'scope':'R002F_BFCACHE_UBUNTU24_DIAGNOSTIC','runner':'ubuntu-24.04'}}
        def record(path, **kwargs):
            if str(path) == '/var/lib/dpkg/status': path = fake / 'status'
            if str(path) == '/var/lib/dpkg/info/ffmpeg.md5sums': path = fake / 'md5sums'
            return actual_record(path, **kwargs)
        def synthetic_records(literals, *, observed=None):
            rows = {name: actual_record(fake / name) for name in literals}
            if observed is not None: observed.update(rows)
            return rows
        stack.enter_context(patch.object(module.runner, 'current', return_value=runner))
        stack.enter_context(patch.object(module, 'records', side_effect=synthetic_records))
        stack.enter_context(patch.object(module.tools, 'file_record', side_effect=record))
        bodies = {}; calls = []; workspaces = []
        def root_admission(value, argv, current_folder, label):
            test.assertEqual(value, {'scope': 'SYNTHETIC_ROOT_TRANSPORT_NOT_AUTHORITY', 'label': label})
            test.assertEqual(bodies[label]['argv'], argv)
            return {'command': bodies[label]}
        stack.enter_context(patch.object(module.privileged, 'admit', side_effect=root_admission))
        def execute(argv, output, label, timeout, **kwargs):
            calls.append(label); work = Path(kwargs['env']['APT_CONFIG']).parent
            if work not in workspaces: workspaces.append(work)
            version = '7:4.4.2' if fault == 'old-version' else '7:6.1.1-3ubuntu5'
            rows = [[name, 'install ok installed', version if name == 'ffmpeg' else '1.0-SOURCE-CONTROL', 'amd64'] for name in module.PACKAGES]
            if fault == 'missing-package': rows = rows[:-1]
            outputs = {'apt-effective-config': module.config_text(work), 'apt-update': 'SOURCE_CONTROL_UPDATE\n',
                'decoder-policy': 'ffmpeg:\n  Installed: (none)\n  Candidate: ' + version + '\n  Version table:\n',
                'decoder-madison': 'ffmpeg | ' + version + ' | https://archive.ubuntu.com/ubuntu noble/universe amd64 Packages\n',
                'apt-install': 'SOURCE_CONTROL_INSTALL\n', 'system-packages': '\n'.join('\t'.join(row) for row in rows) + '\n',
                'decoder-package-verify': 'SOURCE_CONTROL_CHANGED_PACKAGE\n' if fault == 'package-integrity' else ''}
            code = 7 if (fault == 'failed-update' and label == 'apt-update') or (fault == 'failed-install' and label == 'apt-install') else 0
            stderr = b'Download is performed unsandboxed as root\n' if fault == 'unsandboxed' and label == 'apt-update' else b''
            program = 'import base64,sys;sys.stdout.buffer.write(base64.b64decode(sys.argv[1]));sys.stderr.buffer.write(base64.b64decode(sys.argv[2]));raise SystemExit(int(sys.argv[3]))'
            actual_argv = [sys.executable, '-B', '-c', program, base64.b64encode(outputs[label].encode()).decode(), base64.b64encode(stderr).decode(), str(code)]
            row = module.tools.run_bounded(actual_argv, output, label, timeout, **kwargs)
            row['syntheticTransport'] = {'scope':'SOURCE_CONTROL_ONLY','actualArgv':actual_argv,'packageCommandExecuted':False}
            row['argv'] = argv
            if label in module.privileged.LABELS:
                bodies[label] = copy.deepcopy(row)
                row['privilegedController'] = {'scope':'SYNTHETIC_ROOT_TRANSPORT_NOT_AUTHORITY','label':label}
            if label == 'apt-update' and code == 0:
                release_names = sorted(module.RELEASES)
                if fault == 'missing-release': release_names = release_names[:-1]
                for name in release_names: (work / 'lists' / name).write_bytes(b'SOURCE_CONTROL_ONLY_NOT_A_SIGNED_INDEX')
            if label == 'apt-install' and fault == 'bootstrap-replaced':
                replacement = fake / 'new-unshare'; replacement.write_bytes((fake / 'unshare').read_bytes()); replacement.chmod(0o755)
                replacement.replace(fake / 'unshare')
            return row
        try: yield task, folder, execute, calls
        finally:
            retain_control('mock-package-transport-' + fault, {'scope':'MOCK_APT_AND_ROOT_AUTHORITY_WITH_ACTUAL_SAFE_CHILDREN',
                'calls':calls,'packageCommandExecuted':False,'hostedRootQualification':False}, folder)
            for work in workspaces: shutil.rmtree(work)


class AcquisitionControls(unittest.TestCase):
    def test_exact_campaign_selects_only_bfcache_on_ubuntu24(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'campaign.json'
            for selected, expected in ((True, 'ubuntu-24.04'), (False, 'ubuntu-22.04')):
                value = campaign(selected)
                value['purpose'] = 'bfcache-witness ubuntu-24.04 marker is not selection authority'
                path.write_text(json.dumps(value))
                self.assertEqual(m.selection(path)['runner'], expected)

    def test_mixed_or_malformed_campaign_refuses_before_runner_selection(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'campaign.json'
            for delta in ({'engine': 'firefox'}, {'workOrders': ['R002F', 'R0040']},
                          {'r0035Psf': True}, {'r003fDpr': True}, {'r002fRoute': 'unknown'}):
                path.write_text(json.dumps({**campaign(), **delta}))
                with self.subTest(delta=delta), self.assertRaises(ValueError): m.selection(path)

    def test_official_decoder_candidate_rejects_old_unknown_and_ppa_versions(self):
        m = feature(self, 'r002f_bfcache_system')
        policy = 'ffmpeg:\n  Installed: (none)\n  Candidate: 7:6.1.1-3ubuntu5\n  Version table:\n'
        madison = ' ffmpeg | 7:6.1.1-3ubuntu5 | https://archive.ubuntu.com/ubuntu noble/universe amd64 Packages\n'
        self.assertEqual(m.decoder_candidate(policy, madison), '7:6.1.1-3ubuntu5')
        for actual_policy, actual_madison in ((policy.replace('6.1.1', '4.4.2'), madison.replace('6.1.1', '4.4.2')),
                                            (policy.replace('6.1.1', '9.0.0'), madison),
                                            (policy, madison.replace('archive.ubuntu.com/ubuntu', 'ppa.example/ubuntu')),
                                            (policy, madison.replace('noble/', 'jammy/')),
                                            (policy, ''), (policy + '  Candidate: other\n', madison)):
            with self.subTest(policy=actual_policy, madison=actual_madison), self.assertRaises(ValueError):
                m.decoder_candidate(actual_policy, actual_madison)

    def test_provisioning_contract_preserves_literal_decoder_and_existing_budgets(self):
        m = feature(self, 'r002f_bfcache_system')
        import r002f_bfcache_tools as tools
        import r002f_bfcache_central as central
        self.assertEqual(tools.decoder_argv('/usr/bin/ffmpeg', '/private/input.webm'),
                         ['/usr/bin/ffmpeg', '-v', 'error', '-i', '/private/input.webm',
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        self.assertEqual(central.budget()['toolAcquisitionSeconds'], 180)
        self.assertEqual(central.budget()['workflowAcquisitionMinutes'], 15)
        self.assertEqual(central.budget()['workflowObservationMinutes'], 117)
        self.assertEqual(set(m.INSTALL_PACKAGES), {'ffmpeg', 'xvfb', 'binutils', 'libc-bin', 'dpkg', 'iproute2', 'util-linux'})
        self.assertNotIn('--allow-unauthenticated', m.apt_options(Path('/task')))
        self.assertNotIn('--allow-downgrades', m.apt_options(Path('/task')))

    def test_complete_dispatch_roundtrip_rejects_digest_encoding_and_population_changes(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'campaign.json'; path.write_text(json.dumps(campaign()))
            selected = m.selection(path); packet, sources, context, host = packet_fixture(m, selected)
            encoded, digest = m.encode_dispatch(packet)
            self.assertEqual(m.decode_dispatch(encoded, digest), packet)
            self.assertTrue(m.validate_dispatch(packet, selected, sources, context, host))
            for payload, identity in ((encoded[:-4], digest), ('!' + encoded, digest), (encoded, '0' * 64), (None, digest)):
                with self.subTest(payload=payload), self.assertRaises(ValueError): m.decode_dispatch(payload, identity)
            for key, value in (('protocol', 'other'), ('sourceOnly', False), ('nativeObservation', True), ('unknown', 1)):
                changed = {**packet, key: value}
                with self.subTest(key=key), self.assertRaises(ValueError): m.validate_dispatch(changed, selected, sources, context, host)

    def test_changed_campaign_source_run_attempt_and_job_are_refused(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'campaign.json'; path.write_text(json.dumps(campaign()))
            selected = m.selection(path); packet, sources, context, host = packet_fixture(m, selected)
            edits = [('selection', 'runner', 'ubuntu-22.04'), ('sources', 'tree', 'e' * 40)]
            for outer, key, value in edits:
                changed = copy.deepcopy(packet); changed[outer][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): m.validate_dispatch(changed, selected, sources, context, host)
            for key, value in (('GITHUB_RUN_ID', '124'), ('GITHUB_RUN_ATTEMPT', '2'), ('GITHUB_SHA', 'e' * 40)):
                changed = copy.deepcopy(packet); changed['context']['workflow'][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): m.validate_dispatch(changed, selected, sources, context, host)
            changed = copy.deepcopy(packet); changed['context']['job']['id'] = 'observe'
            with self.assertRaises(ValueError): m.validate_dispatch(changed, selected, sources, context, host)

    def test_saved_dispatch_cannot_rebind_both_job_contexts_to_another_workflow(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'campaign.json'; path.write_text(json.dumps(campaign()))
            selected = m.selection(path); original, sources, context, host = packet_fixture(m, selected)
            for key, value in (('GITHUB_REF', 'refs/heads/other'), ('GITHUB_REPOSITORY', 'other/repository'),
                               ('GITHUB_WORKFLOW_REF', 'another workflow'), ('GITHUB_RUN_ID', '0'),
                               ('GITHUB_RUN_ATTEMPT', '0'), ('GITHUB_EVENT_NAME', 'pull_request'),
                               ('GITHUB_WORKFLOW_SHA', 'f' * 40)):
                packet = copy.deepcopy(original); worker = copy.deepcopy(context)
                packet['context']['workflow'][key] = value; worker['workflow'][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): m.validate_dispatch(packet, selected, sources, worker, host)

    def test_wrong_actual_os_distribution_image_or_architecture_is_refused(self):
        m = feature(self, 'runner_environment')
        self.assertEqual(m.admit_host(host_fixture('24.04'), '24.04'), host_fixture('24.04'))
        for group, key, value in (('release', 'VERSION_ID', '22.04'), ('release', 'ID', 'debian'),
                                  ('release', 'VERSION_CODENAME', 'jammy'), ('kernel', 'machine', 'aarch64')):
            host = host_fixture('24.04'); host[group][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): m.admit_host(host, '24.04')
        for key, value in (('imageOS', 'ubuntu22'), ('imageVersion', ''), ('imageVersion', None)):
            host = host_fixture('24.04'); host[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): m.admit_host(host, '24.04')

    def test_actual_git_bytes_and_modes_cannot_hide_behind_skip_worktree(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / 'actual.py'; source.write_text('value = 1\n'); source.chmod(0o644)
            env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
            env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', GIT_NO_LAZY_FETCH='1')
            def git(*args):
                return subprocess.run(['git', '-c', 'protocol.allow=never', '-C', str(root), *args], env=env,
                                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            git('init'); git('add', 'actual.py')
            git('-c', 'user.name=Source Control', '-c', 'user.email=source-control.invalid@example.invalid', 'commit', '-m', 'local fixture')
            original = m.source_snapshot(root, ['actual.py'])
            self.assertEqual(original['files']['actual.py']['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
            git('update-index', '--skip-worktree', 'actual.py'); source.write_text('value = 2\n')
            with self.assertRaises(ValueError): m.source_snapshot(root, ['actual.py'])
            source.write_text('value = 1\n'); source.chmod(0o755)
            with self.assertRaises(ValueError): m.source_snapshot(root, ['actual.py'])
            source.unlink()
            with self.assertRaises((OSError, ValueError)): m.source_snapshot(root, ['actual.py'])

    def test_capture_symlink_cannot_redirect_runner_admission(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / 'task'; task.mkdir(mode=0o700)
            other = Path(directory) / 'other'; other.mkdir(mode=0o700)
            (task / 'capture').symlink_to(other, target_is_directory=True)
            with self.assertRaises(ValueError): m.task_paths(task)

    def test_single_write_acknowledgement_cannot_hide_partial_output_bytes(self):
        m = feature(self, 'runner_environment'); s = feature(self, 'r002f_bfcache_system')
        actual_write = os.write
        for family in ('workflow-output', 'dependency-metadata'):
            for mode in ('short', 'zero', 'full-count-partial-bytes'):
                with self.subTest(family=family, mode=mode), tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / 'output'
                    if family == 'workflow-output': path.write_bytes(b'earlier=value\n')
                    calls = []
                    def partial(fd, raw):
                        calls.append(len(raw)); written = actual_write(fd, raw[:max(1, len(raw) // 2)])
                        return len(raw) if mode == 'full-count-partial-bytes' else 0 if mode == 'zero' else written
                    with patch.object(os, 'write', side_effect=partial), self.assertRaises(ValueError):
                        if family == 'workflow-output': m.append_outputs(path, {'runner': 'ubuntu-24.04'})
                        else: s.write_bytes(path, b'official dependency metadata\n')
                    self.assertEqual(len(calls), 1)

    def test_missing_dispatch_retains_failure_and_never_admits_worker(self):
        m = feature(self, 'runner_environment')
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory); (task / 'capture').mkdir(mode=0o700)
            with patch.dict(os.environ, {}, clear=True): result = m.admit_worker(task)
            self.assertEqual(result['status'], 'INCOMPLETE'); self.assertFalse(result['nativeObservation'])
            self.assertIn('dispatcher output absent', result['error'])
            self.assertEqual(json.loads((task / 'capture/runner-environment.json').read_text()), result)

    def test_same_uid_detached_descendant_control_is_actual_and_not_hosted_authority(self):
        m = feature(self, 'r002f_bfcache_privileged')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            code = ('import json,sys,time;sys.path.insert(0,sys.argv[1]);import r002f_bfcache_privileged as p;'
                    'print(json.dumps(p.source_control(sys.argv[2])))')
            result = subprocess.run([sys.executable, '-B', '-c', code, str(HERE), str(out)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            value = json.loads(result.stdout)
            self.assertEqual(value['scope'], 'SOURCE_CONTROL_SAME_UID_ONLY')
            self.assertEqual(value['status'], 'QUALIFIED'); self.assertFalse(value['hostedRootQualification'])
            self.assertEqual(len(value['escaped']), 1); self.assertEqual(value['remaining'], [])
            self.assertEqual(value['reaped'][0]['signal'], 9)
            retain_control('actual-same-uid-detached-tree', value, out)
            with self.assertRaises(ValueError): m.admit_qualification(value)
            promoted = {**value, 'scope': 'HOSTED_ROOT_PID_NAMESPACE', 'hostedRootQualification': True}
            with self.assertRaises(ValueError): m.admit_qualification(promoted)

    def test_privileged_entry_refuses_before_package_on_this_unprivileged_host(self):
        feature(self, 'r002f_bfcache_privileged')
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / 'request.json'; request.write_text('{}')
            result = subprocess.run([sys.executable, '-B', str(HERE / 'r002f_bfcache_privileged.py'), '--request', str(request)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'owned root PID namespace', result.stderr)
            retain_control('actual-unprivileged-entry-refusal', {'returncode': result.returncode, 'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()})

    def test_private_apt_configuration_is_preloaded_and_refuses_hooks_or_root_sandbox(self):
        m = feature(self, 'r002f_bfcache_system'); work = Path('/tmp/salah-bfcache-apt-source-control')
        self.assertEqual(m.command_environment(work)['APT_CONFIG'], str(work / 'apt.conf'))
        self.assertIn('Dir::Etc::parts "' + str(work / 'empty.conf.d') + '";', m.config_text(work))
        self.assertIn('APT::Sandbox::User "_apt";', m.config_text(work))
        effective = m.config_text(work)
        self.assertTrue(m.admit_effective_config(effective, work))
        for changed in (effective + 'DPkg::Pre-Invoke:: "unreviewed command";\n',
                        effective.replace('"_apt"', '"root"'),
                        effective.replace('AllowUnauthenticated "false"', 'AllowUnauthenticated "true"'),
                        effective.replace(str(work / 'empty.conf.d'), '/etc/apt/apt.conf.d')):
            with self.subTest(config=changed), self.assertRaises(ValueError): m.admit_effective_config(changed, work)

    def test_private_configuration_excludes_host_preferences_credentials_and_unsafe_paths(self):
        m = feature(self, 'r002f_bfcache_system'); work = Path('/tmp/salah-bfcache-apt-source-control')
        settings = dict(m.apt_settings(work))
        for key, name in (('preferences', 'empty.conf'), ('preferencesparts', 'empty.conf.d'),
                          ('netrc', 'empty.conf'), ('netrcparts', 'empty.conf.d')):
            with self.subTest(setting=key): self.assertEqual(settings.get('Dir::Etc::' + key), str(work / name))
        for name in ('salah-bfcache-apt-x\";DPkg::Pre-Invoke::\"x', 'salah-bfcache-apt-../other', 'unbound-workspace'):
            with self.subTest(name=name), self.assertRaises(ValueError): m.config_text(Path('/tmp') / name)

    def test_retained_controller_refuses_changed_program_source_population_and_qualification_bounds(self):
        """Isolate the reader with synthetic root authority, never execute it."""
        m = feature(self, 'r002f_bfcache_privileged')
        import r002f_bfcache_system as system
        import runner_environment as runner
        sandbox_code = ('import os,sys;from pathlib import Path;os.setgroups([]);os.setgid(int(sys.argv[2]));os.setuid(int(sys.argv[1]));'
            'root=Path(sys.argv[3]);'
            '[p.read_bytes() for p in (root/"apt.conf",root/"sources.list",Path(sys.argv[4]))];'
            'a=root/"lists/partial/source-access-control";b=root/"cache/archives/partial/source-access-control";'
            'a.write_bytes(b"APT_SANDBOX_CONTROL");b.write_bytes(b"APT_SANDBOX_CONTROL");a.unlink();b.unlink();'
            'print("APT_SANDBOX_ACCESS_CONFIRMED")')
        for mutation in ('unchanged', 'sandbox-program', 'missing-source', 'sandbox-deadline', 'launcher-cwd'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory) / 'task/capture/r002f-bfcache-tools'; folder.mkdir(parents=True)
                work = Path('/tmp/salah-bfcache-apt-source-control'); label = 'apt-update'; seconds = 60
                argv = system.command(label, work, work / 'sources.list')
                request = {'protocol':m.REQUEST,'label':label,'task':str(folder.parent.parent),'folder':str(folder),'work':str(work),
                    'argv':argv,'version':None,'timeoutSeconds':seconds,'deadlineMonotonic':time.monotonic()+seconds,
                    'environment':system.command_environment(work),'uid':os.getuid(),'gid':os.getgid(),
                    'parentNamespaces':{'pid':'SOURCE_PARENT_PID','mnt':'SOURCE_PARENT_MNT','net':'SOURCE_NET'},
                    'maxBytes':{'stdout':4*1024*1024,'stderr':4*1024*1024},
                    'launcherInputsScope':'HISTORICAL_PRE_LAUNCH_SYSTEM_FILES','launcherInputs':{},
                    'sources':{name:m.tools.file_record(runner.ROOT/name) for name in runner.source_files()}}
                if mutation == 'missing-source': request['sources'].pop('tools/qa/hosted-native/test_envelope.py')
                request_record = m.tools.save(folder / (label + '.request.json'), request)
                safe_argv = [sys.executable,'-B','-c','print("APT_SANDBOX_ACCESS_CONFIRMED")']
                process = m.tools.run_bounded(safe_argv,folder,label+'-apt-access',5,max_stdout=4096,max_stderr=4096,cwd=folder)
                process['syntheticTransport'] = {'scope':'SOURCE_CONTROL_ONLY','actualArgv':safe_argv,'rootCommandExecuted':False}
                process['argv'] = ['/usr/bin/python3','-B','-c',sandbox_code,'42','42',str(work),system.KEYRING]
                if mutation == 'sandbox-program': process['argv'][3] = 'print("APT_SANDBOX_ACCESS_CONFIRMED")'
                if mutation == 'sandbox-deadline': process['elapsedSeconds'] = 6
                body = {'protocol':m.PROTOCOL,'status':'COMPLETE','nativeObservation':False,'request':request_record,
                    'root':{'uid':0,'pid':1,'namespaces':{'pid':'SOURCE_ROOT_PID','mnt':'SOURCE_ROOT_MNT','net':'SOURCE_NET'}},
                    'launcherInputsAdmittedBeforeCommand':hashlib.sha256(json.dumps(request['launcherInputs'],sort_keys=True).encode()).hexdigest(),
                    'qualification':{'scope':'SOURCE_CONTROL_ONLY','hostedRootQualification':False},
                    'aptSandbox':{'status':'PASS','uid':42,'gid':42,'process':process},
                    'unexpectedDescendants':[],'cleanup':{'killed':[],'reaped':[],'remaining':[]},'command':{}}
                result_record = m.tools.save(folder / (label+'.controller.json'),body)
                launch = {'argv':m.launcher(request_record['path'],request_record['sha256'],seconds,request['environment']),
                    'cwd':str(folder),'environment':request['environment'],'pid':123,'returned':True,'returncode':0,
                    'interrupted':None,'timeoutSeconds':seconds,'elapsedSeconds':0.1,'streams':{}}
                if mutation == 'launcher-cwd': launch['cwd'] = '/unbound'
                launch_record = m.tools.save(folder / (label+'.launcher.json'),launch)
                value = {'request':request_record,'result':result_record,'launcher':launch_record}
                with self.assertRaises(ValueError): m.admit(value,argv,folder,label)
                # This patch isolates structural readmission. It is expressly
                # not actual root qualification or a native-success fixture.
                with patch.object(m,'admit_qualification',return_value=True):
                    if mutation == 'unchanged': self.assertEqual(m.admit(value,argv,folder,label),body)
                    else:
                        with self.assertRaises(ValueError): m.admit(value,argv,folder,label)

    def test_public_package_workspace_preserves_private_capture_and_literal_sources(self):
        m = feature(self, 'r002f_bfcache_system')
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / 'task'; task.mkdir(mode=0o700); capture = task / 'capture'; capture.mkdir(mode=0o700)
            work, retained = m.create_workspace(capture)
            try:
                self.assertEqual(work.parent, Path('/tmp')); self.assertTrue(work.name.startswith('salah-bfcache-apt-'))
                self.assertEqual(work.stat().st_mode & 0o777, 0o755)
                self.assertEqual(capture.stat().st_mode & 0o777, 0o700)
                self.assertEqual((work / 'sources.list').read_text(), m.SOURCES)
                self.assertEqual((work / 'apt.conf').read_text(), m.config_text(work))
                self.assertNotIn(str(task), (work / 'apt.conf').read_text())
                self.assertTrue(m.workspace_current(work, os.getuid()))
                self.assertEqual(set(retained), {'sources.list', 'apt.conf', 'empty.conf'})
                (work / 'empty.conf.d').chmod(0o755)
                (work / 'empty.conf.d/unexpected-hook.conf').write_text('unreviewed hook')
                (work / 'empty.conf.d').chmod(0o555)
                with self.assertRaises(ValueError): m.workspace_current(work, os.getuid())
            finally:
                (work / 'empty.conf.d').chmod(0o755)
                shutil.rmtree(work)

    def test_actual_apt_config_proves_late_overrides_do_not_suppress_loaded_hooks(self):
        m = feature(self, 'r002f_bfcache_system')
        self.assertTrue(Path('/usr/bin/apt-config').is_file(), 'local source-control apt-config is unavailable')
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory); work, retained = m.create_workspace(folder)
            try:
                bad = work / 'simulated-host.conf.d'; bad.mkdir()
                (bad / 'hook.conf').write_text('DPkg::Pre-Invoke { "SOURCE_CONTROL_NEVER_EXECUTED"; };\n')
                initial = work / 'simulated-host.conf'
                initial.write_text('Dir::Etc::parts "' + str(bad) + '";\nDir::Etc::main "' + str(work / 'empty.conf') + '";\n')
                argv = ['/usr/bin/apt-config', *m.apt_options(work), 'dump']
                before = subprocess.run(argv, env={**m.ENV, 'APT_CONFIG': str(initial)}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                self.assertEqual(before.returncode, 0)
                self.assertIn(b'SOURCE_CONTROL_NEVER_EXECUTED', before.stdout)
                with self.assertRaises(ValueError): m.admit_effective_config(before.stdout.decode(), work)
                after = subprocess.run(argv, env=m.command_environment(work), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
                (folder / 'before.stdout').write_bytes(before.stdout); (folder / 'before.stderr').write_bytes(before.stderr)
                (folder / 'after.stdout').write_bytes(after.stdout); (folder / 'after.stderr').write_bytes(after.stderr)
                retain_control('actual-apt-configuration-order', {'argv': argv, 'beforeReturncode': before.returncode,
                    'afterReturncode': after.returncode, 'beforeEnvironment': {**m.ENV, 'APT_CONFIG': str(initial)},
                    'afterEnvironment': m.command_environment(work), 'packageInvocation': False}, folder)
                self.assertEqual(after.returncode, 0, after.stderr.decode())
                self.assertNotIn(b'SOURCE_CONTROL_NEVER_EXECUTED', after.stdout)
                self.assertTrue(m.admit_effective_config(after.stdout.decode(), work))
            finally: shutil.rmtree(work)

    def test_general_observer_refuses_runner_failure_before_any_browser_dispatch(self):
        import observe
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory); (task / 'runtime.json').write_text('{}'); (task / 'capture').mkdir(mode=0o700)
            path = task / 'campaign.json'; path.write_text(json.dumps(campaign(False)))
            argv = ['observe.py', '--task', str(task), '--research', '/source/research', '--baseline', '/source/baseline',
                    '--historical', '/source/history', '--campaign', str(path)]
            previous = os.umask(0o077)
            try:
                with patch.object(sys, 'argv', argv), patch.object(observe.signal, 'signal'), \
                     patch.object(observe.runner_environment, 'current', side_effect=ValueError('actual runner admission missing')), \
                     patch.object(observe, 'outside') as outside, patch.object(observe, 'inside') as inside:
                    self.assertEqual(observe.main(), 2)
                    outside.assert_not_called(); inside.assert_not_called()
            finally: os.umask(previous)
            error = json.loads((task / 'capture/coordinator-error-outer.json').read_text())
            self.assertEqual(error['error'], 'actual runner admission missing')

    def test_all_route_producer_maps_include_shared_and_selected_dispatcher_inputs(self):
        import capture_pipeline as pipeline
        import r002f_bfcache_central as central
        import runner_environment as runner
        self.assertIn('tools/qa/hosted-native/test_envelope.py', central.source_files())
        for value in (campaign(), campaign(False), {**campaign(False), 'r003fHarness': 'corrected-matrix'}):
            expected = set(runner.producer_source_files(value))
            with patch.object(pipeline, 'load', return_value=value):
                for phase in ('acquisition', 'observation'):
                    identity = pipeline.producer_identity(phase, Path('/source-control-task'),
                        {key: Path('/source-control-' + key) for key in ('research', 'baseline', 'historical')})
                    self.assertTrue(expected <= set(identity['sources']))
                    prefix = ['capture_pipeline.py', 'acquire.sh' if phase == 'acquisition' else 'observe.py', 'campaign.json']
                    self.assertEqual(list(identity['sources'])[:3], prefix)
            self.assertEqual('r003f-matrix-catalogue.json' in expected, value.get('r003fHarness') == 'corrected-matrix')

    def test_successful_producer_requires_runner_readmission_but_actual_failure_is_retained(self):
        import capture_pipeline as pipeline
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / 'task'; capture = task / 'capture'; control = capture / 'producer-control'; control.mkdir(parents=True)
            roots = {key: Path(directory) / key for key in ('research', 'baseline', 'historical')}
            for path in roots.values(): path.mkdir()
            identity = pipeline.producer_identity('acquisition', task, roots)
            started = {'protocol': pipeline.PRODUCER_PROTOCOL, 'phase': 'acquisition', 'identity': identity}
            (control / 'acquisition-started.json').write_text(json.dumps(started))
            for code in (0, 2):
                completed = {**started, 'returned': True, 'interrupted': False, 'process': {'returncode': code, 'elapsedSeconds': 1.0}}
                (control / 'acquisition-completed.json').write_text(json.dumps(completed))
                with patch.object(pipeline.runner_environment, 'current', side_effect=ValueError('current admission missing')) as guard:
                    if code == 0:
                        with self.assertRaises(pipeline.Rejected): pipeline.completed(task, roots, 'acquisition')
                        guard.assert_called_once_with(task)
                    else:
                        self.assertEqual(pipeline.completed(task, roots, 'acquisition'), 2); guard.assert_not_called()

    def test_actual_descendants_are_reaped_after_timeout_overflow_cancel_and_outer_deadline(self):
        feature(self, 'r002f_bfcache_privileged')
        for mode in ('timeout', 'overflow', 'cancel', 'outer-deadline'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                code = ('import json,sys;sys.path.insert(0,sys.argv[1]);import r002f_bfcache_privileged as p;'
                        'print(json.dumps(p.source_failure_control(sys.argv[2],sys.argv[3])))')
                argv = [sys.executable, '-B', '-c', code, str(HERE), str(folder), mode]
                process = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
                (folder / 'controller.stdout').write_bytes(process.stdout); (folder / 'controller.stderr').write_bytes(process.stderr)
                retain_control('actual-tree-' + mode, {'argv': argv, 'returncode': process.returncode}, folder)
                self.assertEqual(process.returncode, 0, process.stderr.decode())
                value = json.loads(process.stdout)
                self.assertEqual(value['status'], 'EXPECTED_REFUSAL_WITH_ACTUAL_TEARDOWN')
                self.assertEqual(value['scope'], 'SOURCE_CONTROL_SAME_UID_ONLY')
                self.assertFalse(value['hostedRootQualification']); self.assertFalse(value['nativeObservation'])
                self.assertIn(len(value['escaped']), (1, 2)); self.assertEqual(len(value['reaped']), len(value['escaped']))
                self.assertEqual(value['remaining'], [])

    def test_nonroot_caller_cannot_claim_privileged_stream_ownership(self):
        import r002f_bfcache_tools as tools
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                tools.run_bounded([sys.executable, '-c', 'raise SystemExit(0)'], Path(directory), 'must-not-start', 1,
                                  output_owner=(os.getuid(), os.getgid()))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_installed_package_population_requires_every_original_and_namespace_dependency(self):
        m = feature(self, 'r002f_bfcache_system'); version = '7:6.1.1-3ubuntu5'
        rows = [[name, 'install ok installed', version if name == 'ffmpeg' else 'source-control-version', 'amd64'] for name in m.PACKAGES]
        text = lambda value: '\n'.join('\t'.join(row) for row in value) + '\n'
        self.assertEqual(m.installed_rows(text(rows), version), rows)
        for index, field, value in ((0, 1, 'deinstall ok config-files'), (0, 2, '7:4.4.2'), (1, 3, 'arm64')):
            changed = copy.deepcopy(rows); changed[index][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): m.installed_rows(text(changed), version)
        for changed in (rows[:-1], rows + [rows[0]], rows[:-1] + [rows[0]]):
            with self.assertRaises(ValueError): m.installed_rows(text(changed), version)

    def test_system_file_record_refuses_nonroot_or_writable_substitution(self):
        m = feature(self, 'r002f_bfcache_system')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'substitute'; path.write_bytes(b'not an acquired system tool'); path.chmod(0o777)
            with self.assertRaises(ValueError): m.records({'decoder': str(path)})

    def test_bootstrap_identity_refusal_retains_complete_observed_descriptors_before_commands(self):
        """Losing the pre-guard rows prevents diagnosis of a genuine refusal."""
        m = feature(self, 'r002f_bfcache_system')
        names = ('sudo', 'env', 'aptGet', 'aptCache', 'aptConfig', 'gpgv', 'git', 'bash',
                 'openssl', 'archiveKeyring', 'caCertificates', 'timeout', 'unshare', 'systemPython')
        self.assertGreater(os.getuid(), 0, 'this is an actual nonroot source control')
        with tempfile.TemporaryDirectory(prefix='bfcache-bootstrap-retention-control-') as directory:
            root = Path(directory); task = root / 'task'; folder = task / 'capture/r002f-bfcache-tools'
            folder.mkdir(parents=True, mode=0o700)
            inputs = root / 'synthetic-system'; inputs.mkdir()
            literals = {}; expected = {}
            for name in names:
                file = inputs / name; body = ('SOURCE_CONTROL_ONLY bootstrap ' + name + '\n').encode()
                file.write_bytes(body)
                mode = 0o777 if name == 'openssl' else 0o644 if name in ('archiveKeyring', 'caCertificates') else 0o755
                file.chmod(mode); literals[name] = str(file)
                expected[name] = {'path': str(file), 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                                  'mode': mode, 'uid': file.stat().st_uid}
            selected = {'scope': 'SOURCE_CONTROL_ONLY', 'selection': {
                'scope': 'R002F_BFCACHE_UBUNTU24_DIAGNOSTIC', 'runner': 'ubuntu-24.04'}}
            result = None
            try:
                with patch.object(m, 'BOOTSTRAP', literals), patch.object(m.runner, 'current', return_value=selected), \
                     patch.object(m, 'create_workspace', side_effect=AssertionError('refusal must precede package configuration')):
                    result = m.provision(task, folder, time.monotonic() + 180)
                self.assertEqual(result['status'], 'INCOMPLETE')
                self.assertEqual(result['error'], 'ValueError: root-owned system executable/keyring identity differs')
                self.assertEqual(result['commands'], [])
                self.assertNotIn('configuration', result)
                self.assertFalse(result['nativeObservation'])
                self.assertIn('bootstrapRefusal', result,
                              'complete original bootstrap descriptors must survive the unchanged ownership refusal')
                self.assertEqual(result['bootstrapRefusal']['scope'], 'HISTORICAL_UNADMITTED_BOOTSTRAP_SYSTEM_FILES')
                retained = result['bootstrapRefusal']['records']
                self.assertEqual(set(retained), set(names))
                for name in names:
                    self.assertEqual({key: retained[name][key] for key in expected[name]}, expected[name])
                    self.assertTrue(retained[name]['system'])
                self.assertNotIn('bootstrapBefore', result)
                self.assertFalse((folder / 'bootstrap-before.json').exists())
                self.assertEqual(m.tools.load(folder / 'system-provision.json'), result)
                with self.assertRaisesRegex(ValueError, 'selected system provision incomplete'):
                    m.current(result, task, folder)
            finally:
                retain_control('bootstrap-before-identity-refusal', {'result': result, 'expectedDescriptors': expected,
                    'deliberateWritableFixture': 'openssl', 'native35OffendingPath': 'NOT_INFERRED'}, folder)

    def test_failed_system_provision_stops_before_managed_query_or_decoder_capability(self):
        import r002f_bfcache_tools as tools
        import r002f_bfcache_central as central
        import r002f_bfcache_system as system
        import runner_environment as runner
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory); (task / 'capture').mkdir(mode=0o700)
            actual_load = tools.load
            def load(path):
                if Path(path) == tools.HERE / 'campaign.json': return campaign()
                return actual_load(path)
            with patch.object(tools, 'load', side_effect=load), patch.object(central, 'source_identity', return_value={'scope':'SOURCE_CONTROL_ONLY'}), \
                 patch.object(runner, 'current', return_value={'scope':'SOURCE_CONTROL_ONLY'}), \
                 patch.object(system, 'provision', return_value={'status':'INCOMPLETE','error':'actual package command failed'}), \
                 patch.object(system, 'current', side_effect=AssertionError('failed system receipt cannot be admitted')), \
                 patch.object(tools, 'acquired_runtime', side_effect=AssertionError('managed query must not run')) as managed, \
                 patch.object(tools, 'run_fixture', side_effect=AssertionError('decoder capability must not run')) as capability:
                value = tools.acquire(task)
                self.assertEqual(value['status'], 'INCOMPLETE'); managed.assert_not_called(); capability.assert_not_called()
            self.assertEqual(value['provision']['error'], 'actual package command failed')
            self.assertFalse(value['nativeObservation'])
            self.assertEqual(tools.load(task / 'capture/r002f-bfcache-tools/receipt.json'), value)

    def test_bootstrap_policy_refusals_keep_complete_first_and_last_rows_unadmitted(self):
        m = feature(self, 'r002f_bfcache_system')
        faults = (('sudo', 'uid', 1001), ('systemPython', 'uid', 1001),
                  ('openssl', 'mode', 0o775), ('openssl', 'mode', 0o757), ('openssl', 'mode', 0o644),
                  ('archiveKeyring', 'mode', 0o664), ('caCertificates', 'uid', 1001))
        for index, (name, field, value) in enumerate(faults):
            with self.subTest(name=name, field=field, value=value), bootstrap_metadata_fixture(self, m) as fixture:
                task, folder, literals, rows, calls, workspace = fixture
                rows[name][field] = value
                result = m.provision(task, folder, time.monotonic() + 180)
                self.assertEqual(calls, list(literals)); self.assertEqual(len(calls), 14)
                self.assertEqual(result['status'], 'INCOMPLETE')
                self.assertEqual(result['error'], 'ValueError: root-owned system executable/keyring identity differs')
                self.assertEqual(result['bootstrapRefusal'], {
                    'scope': 'HISTORICAL_UNADMITTED_BOOTSTRAP_SYSTEM_FILES', 'records': rows})
                self.assertEqual(result['commands'], []); workspace.assert_not_called()
                self.assertNotIn('bootstrapBefore', result); self.assertNotIn('configuration', result)
                self.assertFalse((folder / 'bootstrap-before.json').exists())
                self.assertEqual(m.tools.load(folder / 'system-provision.json'), result)
                with self.assertRaisesRegex(ValueError, 'selected system provision incomplete'):
                    m.current(result, task, folder)
                retain_control('bootstrap-policy-refusal-' + str(index), {
                    'result': result, 'syntheticDescriptors': rows, 'readOrder': calls,
                    'packageOrPrivilegedCommandExecuted': False}, folder)

    def test_bootstrap_valid_metadata_keeps_original_setuid_and_data_exceptions(self):
        m = feature(self, 'r002f_bfcache_system')
        with bootstrap_metadata_fixture(self, m) as fixture:
            task, folder, literals, rows, calls, workspace = fixture
            rows['sudo']['mode'] = 0o4755
            for name in ('archiveKeyring', 'caCertificates'): rows[name]['mode'] = 0o444
            self.assertEqual(m.records(literals), rows)
            self.assertEqual(calls, list(literals)); workspace.assert_not_called()
            retain_control('bootstrap-valid-metadata', {'syntheticDescriptors': rows, 'readOrder': calls,
                'packageOrPrivilegedCommandExecuted': False})

    def test_bootstrap_writer_failure_after_valid_guard_is_not_identity_refusal(self):
        m = feature(self, 'r002f_bfcache_system')
        with bootstrap_metadata_fixture(self, m) as fixture:
            task, folder, literals, rows, calls, workspace = fixture
            collision = folder / 'bootstrap-before.json'; original = b'SOURCE_CONTROL_ONLY existing bootstrap receipt\n'
            collision.write_bytes(original)
            result = m.provision(task, folder, time.monotonic() + 180)
            self.assertEqual(result['status'], 'INCOMPLETE'); self.assertTrue(result['error'].startswith('FileExistsError:'))
            self.assertNotIn('bootstrapRefusal', result); self.assertNotIn('bootstrapBefore', result)
            self.assertEqual(calls, list(literals)); self.assertEqual(result['commands'], []); workspace.assert_not_called()
            self.assertEqual(collision.read_bytes(), original)
            self.assertEqual(m.tools.load(folder / 'system-provision.json'), result)
            retain_control('bootstrap-valid-guard-writer-refusal', {'result': result, 'readOrder': calls}, folder)

    def test_bootstrap_early_descriptor_failure_does_not_invent_complete_rows(self):
        m = feature(self, 'r002f_bfcache_system')
        with bootstrap_metadata_fixture(self, m, read_error='openssl') as fixture:
            task, folder, literals, rows, calls, workspace = fixture
            result = m.provision(task, folder, time.monotonic() + 180)
            self.assertEqual(result['status'], 'INCOMPLETE')
            self.assertEqual(result['error'], 'OSError: SOURCE_CONTROL_ONLY descriptor read failed')
            self.assertEqual(calls, list(literals)[:list(literals).index('openssl') + 1])
            self.assertNotIn('bootstrapRefusal', result); self.assertNotIn('bootstrapBefore', result)
            self.assertEqual(result['commands'], []); workspace.assert_not_called()
            self.assertFalse((folder / 'bootstrap-before.json').exists())
            self.assertEqual(m.tools.load(folder / 'system-provision.json'), result)
            retain_control('bootstrap-incomplete-descriptor-collection', {'result': result, 'readOrder': calls}, folder)

    def test_bootstrap_final_receipt_collision_keeps_original_writer_exception(self):
        m = feature(self, 'r002f_bfcache_system')
        with bootstrap_metadata_fixture(self, m) as fixture:
            task, folder, literals, rows, calls, workspace = fixture
            rows['sudo']['uid'] = 1001
            collision = folder / 'system-provision.json'; original = b'SOURCE_CONTROL_ONLY existing final receipt\n'
            collision.write_bytes(original)
            with self.assertRaises(FileExistsError): m.provision(task, folder, time.monotonic() + 180)
            self.assertEqual(calls, list(literals)); workspace.assert_not_called()
            self.assertFalse((folder / 'bootstrap-before.json').exists())
            self.assertEqual(collision.read_bytes(), original)
            retain_control('bootstrap-final-receipt-writer-refusal', {'readOrder': calls,
                'observedException': 'FileExistsError', 'newReceiptPersisted': False}, folder)

    def test_complete_mock_package_transport_and_currentness_keep_historical_bootstrap_separate(self):
        m = feature(self, 'r002f_bfcache_system')
        for fault in ('none', 'bootstrap-replaced'):
            with self.subTest(fault=fault), package_transport_fixture(self, m, fault) as (task, folder, execute, calls):
                result = m.provision(task, folder, time.monotonic() + 180, execute=execute)
                self.assertEqual(result['status'], 'COMPLETE', result.get('error'))
                self.assertEqual(calls, list(m.LIMITS))
                self.assertEqual(m.current(result, task, folder)['decoderVersion'], '7:6.1.1-3ubuntu5')
                before = m.tools.load(folder / 'bootstrap-before.json')
                if fault == 'bootstrap-replaced':
                    self.assertNotEqual(before['unshare']['inode'], result['bootstrap']['unshare']['inode'])
                    self.assertEqual(before['unshare']['sha256'], result['bootstrap']['unshare']['sha256'])
                self.assertFalse(result['nativeObservation']); self.assertFalse(result['fallbackDecoder'])

    def test_failed_or_incomplete_mock_package_step_stops_without_retry(self):
        m = feature(self, 'r002f_bfcache_system')
        expected_last = {'failed-update':'apt-update', 'failed-install':'apt-install', 'old-version':'decoder-madison',
                         'missing-package':'system-packages', 'package-integrity':'decoder-package-verify',
                         'unsandboxed':'apt-update', 'missing-release':'apt-update'}
        for fault, last in expected_last.items():
            with self.subTest(fault=fault), package_transport_fixture(self, m, fault) as (task, folder, execute, calls):
                result = m.provision(task, folder, time.monotonic() + 180, execute=execute)
                self.assertEqual(result['status'], 'INCOMPLETE'); self.assertTrue(result['error'])
                self.assertEqual(calls[-1], last); self.assertEqual(len(calls), len(set(calls)))
                self.assertFalse(result['nativeObservation'])
                self.assertEqual(m.tools.load(folder / 'system-provision.json'), result)
                with self.assertRaises(ValueError): m.current(result, task, folder)


if __name__ == '__main__': unittest.main()
