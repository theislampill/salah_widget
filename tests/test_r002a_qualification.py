"""R002A (issue 91) qualification gate and delivery-identity controls. Headless, offline, stdlib only.

Fixture Git repositories are created in the temporary directory; no network, no real Pages host, no provider.
G-02 (parity), G-03 (suite verdict partition), G-05 (pin coherence), G-06 (least privilege, static) and
G-09 (readback discrimination) at the unit level; the hosted rows are in docs/state-contracts/R002A.md.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'qualification'))
sys.path.insert(0, str(ROOT / 'tools'))
import qualification_gate as gate  # noqa: E402
import delivery_identity as di  # noqa: E402

WORKFLOWS = ('.github/workflows/qualification.yml', '.github/workflows/delivery-identity.yml')


def git(root, *args):
    return subprocess.run(['git', '-c', 'user.name=fixture', '-c', 'user.email=fixture@invalid', '-c',
                           'commit.gpgsign=false', '-c', 'core.autocrlf=false', *args], cwd=root, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


def write(root, name, data):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def quiet(fn, *args, **kwargs):
    with redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix='r002a-')
        self.root = Path(self._tmp.name) / 'repo'
        self.root.mkdir()
        self.n = 0
        os.environ.pop('GITHUB_STEP_SUMMARY', None)
        os.environ.pop('GITHUB_ACTIONS', None)

    def tearDown(self):
        self._tmp.cleanup()

    def out(self):
        self.n += 1
        path = Path(self._tmp.name) / ('out' + str(self.n))
        path.mkdir()
        return path

    def commit(self, message='c'):
        git(self.root, 'add', '-A')
        git(self.root, 'commit', '-q', '-m', message)
        return git(self.root, 'rev-parse', 'HEAD')


class PinCoherence(Fixture):
    """G-05: J5(a) strict docs-receipt pins; J5(b) README installer pins with declared divergence."""

    def setUp(self):
        super().setUp()
        git(self.root, 'init', '-q')
        write(self.root, 'install.sh', '#!/bin/sh\necho v1\n')
        write(self.root, 'install.ps1', 'Write-Output v1\n')
        self.pinned = self.commit('installers')
        write(self.root, 'src/native/builder.html', '<p>builder</p>\n')
        write(self.root, 'src/native/config.js', 'config\n')
        self.readme(self.pinned)
        self.divergence([])
        self.repin()
        self.commit('docs')

    def readme(self, commit, ps1=None):
        write(self.root, 'README.md', "# r\n\nINSTALL_COMMIT='" + commit + "'\n$InstallCommit = '" + (ps1 or commit) + "'\n")

    def repin(self):
        digest = lambda name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
        write(self.root, gate.DOCS_PINS_FILE, ''.join(
            " if(bindings['" + name + "'].sha256!=='" + digest(name) + "')throw Error('x');\n"
            for name in gate.DOCS_PINNED))

    def divergence(self, records):
        write(self.root, gate.DIVERGENCE_FILE, json.dumps({'schema': gate.DIVERGENCE_SCHEMA, 'records': records}))

    def run_pins(self):
        out = self.out()
        code = quiet(gate.pins, self.root, out)
        return code, json.loads((out / 'pins.json').read_text())

    def record(self, **overrides):
        current = gate.git_blob_id((self.root / 'install.sh').read_bytes())
        record = {'pinnedCommit': self.pinned, 'path': 'install.sh',
                  'pinnedBlob': git(self.root, 'rev-parse', self.pinned + ':install.sh'), 'currentBlob': current,
                  'reason': 'fixture', 'owner': 'R002A', 'date': '2026-11-13', 'trigger': 'README re-pinned'}
        record.update(overrides)
        return record

    def test_clean_tree_passes(self):
        code, receipt = self.run_pins()
        self.assertEqual((code, receipt['verdict']), (0, 'PASS'))
        self.assertEqual([r['state'] for r in receipt['installerPins']['rows']], ['equal', 'equal'])

    def test_a_readme_change_without_repin_fails(self):
        write(self.root, 'README.md', (self.root / 'README.md').read_text() + 'more\n')
        code, receipt = self.run_pins()
        self.assertEqual((code, receipt['verdict']), (1, 'FAIL'))
        self.assertTrue(any('README.md SHA-256' in e for e in receipt['docsReceipt']['errors']))

    def test_a_builder_or_config_change_without_repin_fails(self):
        for name in ('src/native/builder.html', 'src/native/config.js'):
            original = (self.root / name).read_bytes()
            write(self.root, name, original + b'x')
            code, receipt = self.run_pins()
            self.assertEqual(code, 1, name)
            self.assertTrue(any(e.startswith(name) for e in receipt['docsReceipt']['errors']), name)
            write(self.root, name, original)

    def test_a_has_no_divergence_path(self):
        write(self.root, 'README.md', (self.root / 'README.md').read_text() + 'more\n')
        self.divergence([self.record(path='install.sh')])  # an installer record cannot excuse a docs pin
        code, _ = self.run_pins()
        self.assertEqual(code, 1)

    def test_a_missing_or_duplicated_pin_fails_closed(self):
        text = (self.root / gate.DOCS_PINS_FILE).read_text()
        write(self.root, gate.DOCS_PINS_FILE, text.splitlines(True)[0])
        self.assertEqual(self.run_pins()[0], 1)
        write(self.root, gate.DOCS_PINS_FILE, text + text.splitlines(True)[0])
        self.assertEqual(self.run_pins()[0], 1)

    def test_b_installer_change_without_repin_or_record_fails(self):
        write(self.root, 'install.sh', '#!/bin/sh\necho v2\n')
        code, receipt = self.run_pins()
        self.assertEqual(code, 1)
        self.assertEqual(receipt['installerPins']['rows'][0]['state'], 'diverged')

    def test_b_valid_record_is_declared_not_plain_pass(self):
        write(self.root, 'install.sh', '#!/bin/sh\necho v2\n')
        self.divergence([self.record()])
        code, receipt = self.run_pins()
        self.assertEqual((code, receipt['verdict']), (0, 'PASS_WITH_DECLARED_DIVERGENCE (1)'))

    def test_b_stale_record_fails(self):
        write(self.root, 'install.sh', '#!/bin/sh\necho v2\n')
        self.divergence([self.record(currentBlob='0' * 40)])
        code, receipt = self.run_pins()
        self.assertEqual(code, 1)
        self.assertEqual(receipt['installerPins']['rows'][0]['state'], 'stale-record')

    def test_b_record_outliving_its_trigger_fails(self):
        self.divergence([self.record()])  # installers equal the pin: nothing left to declare
        self.assertEqual(self.run_pins()[0], 1)

    def test_b_record_with_wrong_pinned_commit_fails(self):
        write(self.root, 'install.sh', '#!/bin/sh\necho v2\n')
        self.divergence([self.record(pinnedCommit='1' * 40)])
        self.assertEqual(self.run_pins()[0], 1)

    def test_b_malformed_divergence_file_fails(self):
        write(self.root, gate.DIVERGENCE_FILE, '{}')
        self.assertEqual(self.run_pins()[0], 1)
        (self.root / gate.DIVERGENCE_FILE).unlink()
        self.assertEqual(self.run_pins()[0], 1)
        self.divergence([{'path': 'install.sh'}])
        self.assertEqual(self.run_pins()[0], 1)

    def test_b_duplicate_record_fails(self):
        write(self.root, 'install.sh', '#!/bin/sh\necho v2\n')
        self.divergence([self.record(), self.record(reason='again')])
        code, receipt = self.run_pins()
        self.assertEqual(code, 1)
        self.assertTrue(any('duplicate record' in e for e in receipt['installerPins']['errors']))

    def test_b_unresolvable_pin_fails(self):
        self.readme('2' * 40)
        self.repin()
        code, receipt = self.run_pins()
        self.assertEqual(code, 1)
        self.assertEqual({r['state'] for r in receipt['installerPins']['rows']}, {'unresolved'})

    def test_b_repinned_readme_passes(self):
        write(self.root, 'install.sh', '#!/bin/sh\necho v2\n')
        new = self.commit('installer change')
        self.readme(new)
        self.repin()
        self.assertEqual(self.run_pins()[0], 0)


FAKE_BUILDER = '''import json, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
mode = (root / "mode").read_text().strip()
count = root / "count"
n = int(count.read_text()) if count.exists() else 0
count.write_text(str(n + 1))
written = 0
if mode == "dirty":
    (root / "index.html").write_text("hand edit undone by the builder? no: changed\\n"); written = 1
if mode == "second-writes" and n == 1:
    written = 1
if mode == "crash":
    sys.exit(7)
print(json.dumps({"stage": "complete", "phase": "published", "written": written, "unchanged": 3, "removed": 0}, indent=2))
'''


class Parity(Fixture):
    """G-02 at the unit level: build twice, clean tree, the second build writes nothing."""

    def setUp(self):
        super().setUp()
        git(self.root, 'init', '-q')
        write(self.root, 'tools/build_native.py', FAKE_BUILDER)
        write(self.root, 'index.html', 'generated\n')
        write(self.root, '.gitignore', 'count\nmode\n')
        self.commit()

    def run_parity(self, mode):
        write(self.root, 'mode', mode)
        (self.root / 'count').unlink(missing_ok=True)
        out = self.out()
        code = quiet(gate.parity, self.root, out)
        return code, json.loads((out / 'parity.json').read_text())

    def test_clean_builds_pass(self):
        code, receipt = self.run_parity('clean')
        self.assertEqual((code, receipt['verdict']), (0, 'PASS'))
        self.assertTrue(receipt['secondBuildWroteNothing'] and receipt['firstBuildWroteNothing'])

    def test_dirty_tree_fails_naming_the_file(self):
        code, receipt = self.run_parity('dirty')
        self.assertEqual(code, 1)
        self.assertTrue(any('index.html' in line for line in receipt['statusPorcelain']))
        self.assertEqual(receipt['diffExitCode'], 1)

    def test_second_build_writing_fails(self):
        code, receipt = self.run_parity('second-writes')
        self.assertEqual(code, 1)
        self.assertFalse(receipt['secondBuildWroteNothing'])

    def test_builder_failure_fails(self):
        code, receipt = self.run_parity('crash')
        self.assertEqual(code, 1)
        self.assertEqual(len(receipt['builds']), 1)

    def test_untracked_output_fails(self):
        write(self.root, 'stray.js', 'x')
        code, receipt = self.run_parity('clean')
        self.assertEqual(code, 1)
        self.assertTrue(any('stray.js' in line for line in receipt['statusPorcelain']))


def row(name, status, python=False, ledger=None):
    return {'name': name, 'status': status, 'command': [sys.executable if python else 'node', 'x'],
            'ledger': ledger or {}}


class SuitesVerdict(unittest.TestCase):
    """G-03 at the unit level: the gate partitions one runner receipt and never upgrades it."""

    def results(self, rows, status, verdict=None, setup=()):
        return {'commands': rows, 'status': status, 'verdict': verdict or status, 'setupErrors': list(setup),
                'ledger': {'capabilities': {'symlink-unavailable': False}, 'declared': []}}

    def test_declared_is_reported_verbatim(self):
        rows = [row('docs', gate.DECLARED, ledger={'expectedFail': [{'id': 'D1', 'case': 'c'}]}),
                row('py', 'PASS', python=True)]
        s = gate.summarize_suites(self.results(rows, gate.DECLARED, gate.DECLARED + ' (1)'), sys.executable)
        self.assertEqual(s['status'], 'DECLARED')
        self.assertEqual(s['runnerVerdict'], gate.DECLARED + ' (1)')
        self.assertEqual((s['jobs']['J2']['verdict'], s['jobs']['J3']['verdict']), (gate.DECLARED + ' (1)', 'PASS'))

    def test_unexpected_failure_and_incomplete_are_red(self):
        rows = [row('docs', 'FAIL', ledger={'unexpectedPass': ['D1']}), row('py', 'INCOMPLETE', python=True)]
        s = gate.summarize_suites(self.results(rows, 'FAIL'), sys.executable)
        self.assertEqual((s['status'], s['jobs']['J2']['status'], s['jobs']['J3']['status']), ('FAIL', 'FAIL', 'INCOMPLETE'))
        self.assertEqual(s['jobs']['J2']['notPass'][0]['unexpected'], {'unexpectedPass': ['D1']})

    def test_setup_errors_make_both_partitions_incomplete(self):
        rows = [row('docs', 'PASS'), row('py', 'PASS', python=True)]
        s = gate.summarize_suites(self.results(rows, 'INCOMPLETE', setup=['unregistered instrument']), sys.executable)
        self.assertEqual((s['status'], s['jobs']['J2']['status'], s['jobs']['J3']['status']),
                         ('INCOMPLETE', 'INCOMPLETE', 'INCOMPLETE'))

    def test_unknown_runner_status_is_never_a_pass(self):
        s = gate.summarize_suites(self.results([row('docs', 'PASS')], 'RUNNING'), sys.executable)
        self.assertEqual(s['status'], 'INCOMPLETE')

    def test_condition_gated_entry_observation(self):
        entry = {'id': 'L12', 'status': 'active', 'kind': 'case-fail', 'command': 'py', 'case': 'symlink case',
                 'condition': 'symlink-unavailable'}
        s = gate.summarize_suites(self.results([row('py', 'PASS', python=True)], 'PASS'), sys.executable, [entry])
        self.assertEqual(s['conditionalEntries'][0]['observed'], 'case passed (entry inert on this host)')
        bad = row('py', 'FAIL', python=True, ledger={'unexpectedFail': [{'case': 'symlink case', 'message': 'boom'}]})
        s = gate.summarize_suites(self.results([bad], 'FAIL'), sys.executable, [entry])
        self.assertTrue(s['conditionalEntries'][0]['observed'].startswith('case did not pass'))

    def test_runner_exit_disagreement_is_not_a_pass(self):
        with tempfile.TemporaryDirectory(prefix='r002a-suites-') as tmp:
            root = Path(tmp)
            results = self.results([row('docs', 'PASS')], 'PASS')
            write(root, 'tools/cp9/run_native_regressions.py',
                  'import json,sys,pathlib\nout=pathlib.Path(sys.argv[sys.argv.index("--output")+1]);out.mkdir()\n'
                  '(out/"results.json").write_text(' + repr(json.dumps(results)) + ')\nsys.exit(1)\n')
            write(root, 'tests/expected-failures.json', '{"entries": []}')
            out = root / 'out'
            out.mkdir()
            code = quiet(gate.suites, root, out)
            receipt = json.loads((out / 'suites.json').read_text())
        self.assertEqual(code, 1)
        self.assertEqual(receipt['verdict'], 'INCOMPLETE')


class AcceptedHistory(Fixture):
    """Precondition control: a missing accepted-history object makes suites INCOMPLETE, naming it."""

    def run_suites(self, locators):
        git(self.root, 'init', '-q')
        write(self.root, 'index.html', 'accepted\n')
        head = self.commit()
        results = {'commands': [row('docs', 'PASS')], 'status': 'PASS', 'verdict': 'PASS', 'setupErrors': [],
                   'ledger': {'capabilities': {}, 'declared': []}}
        write(self.root, 'tools/cp9/run_native_regressions.py',
              'import json, pathlib, sys\nHISTORY_INPUTS = ' + repr({'r0022-baseline-balance': tuple(
                  loc.replace('HEAD', head) for loc in locators)}) + '\n'
              'if __name__ == "__main__":\n    out = pathlib.Path(sys.argv[sys.argv.index("--output") + 1]); out.mkdir()\n'
              '    (out / "results.json").write_text(' + repr(json.dumps(results)) + ')\n    sys.exit(0)\n')
        write(self.root, 'tests/expected-failures.json', '{"entries": []}')
        out = self.out()
        code = quiet(gate.suites, self.root, out)
        return code, json.loads((out / 'suites.json').read_text())

    def test_present_objects_pass(self):
        code, receipt = self.run_suites(['HEAD:index.html'])
        self.assertEqual((code, receipt['verdict']), (0, 'PASS'))
        self.assertEqual(receipt['acceptedHistory']['missing'], [])

    def test_missing_object_is_incomplete_and_named(self):
        missing = '8b83df029966c203a503ab217d121c48b8ee6e8a:index.html'
        code, receipt = self.run_suites(['HEAD:index.html', missing])
        self.assertEqual((code, receipt['verdict']), (1, 'INCOMPLETE'))
        self.assertIn(missing, receipt['reason'])
        self.assertEqual([o['available'] for o in receipt['acceptedHistory']['objects']], [True, False])

    def test_repository_runner_inputs_are_present_here(self):
        rows, missing = gate.accepted_history(ROOT)
        self.assertEqual(missing, [])
        self.assertGreaterEqual(len(rows), 7)


class Delivery(Fixture):
    """G-09 at the unit level: no identical without a built status for the exact commit."""

    def setUp(self):
        super().setUp()
        git(self.root, 'init', '-q')
        self.files = {'index.html': b'<p>i</p>', 'offline.html': b'o', 'config.js': b'c', 'builder.html': b'b',
                      'install.sh': b'#!/bin/sh\n', 'install.ps1': b'ps', 'presets/p.json': b'{}',
                      'v1/index.html': b'v1', 'v1/.gitattributes': b'* -text\n', 'real-sky/native-sky.js': b'sky',
                      'docs/rlgwo-execution/x/evidence.json': b'{}',
                      '_config.yml': b'exclude:\n  - docs/rlgwo-execution\n'}
        inventory = {'files': {p: {} for p in ('index.html', 'offline.html', 'config.js', 'builder.html',
                                                'real-sky/native-sky.js')}}
        self.files['GENERATED.json'] = json.dumps(inventory).encode()
        for name, data in self.files.items():
            write(self.root, name, data)
        self.first = self.commit('first')
        self.files['README.md'] = ("INSTALL_COMMIT='" + self.first + "'\n"
                                   'curl "https://raw.githubusercontent.com/theislampill/salah_widget/$INSTALL_COMMIT/install.sh"\n'
                                   'curl https://raw.githubusercontent.com/theislampill/salah_widget/main/install.sh\n').encode()
        write(self.root, 'README.md', self.files['README.md'])
        self.commit_sha = self.commit('readme')
        self.served = {}
        for name, data in self.files.items():
            self.served[di.SITE + name] = data
        self.served[di.RAW + self.first + '/install.sh'] = self.files['install.sh']
        self.served[di.RAW + 'main/install.sh'] = self.files['install.sh']
        self.builds = [{'status': 'built', 'commit': self.commit_sha}]
        self.main = self.commit_sha
        self.fetched = []
        self.clock = [0.0]

    def api(self, path):
        if path.endswith('/commits/main'):
            return {'sha': self.main}, None
        build = self.builds.pop(0) if len(self.builds) > 1 else self.builds[0]
        return (dict(build) if build else None), (None if build else 'gh unavailable')

    def fetch(self, url, timeout, max_bytes):
        self.fetched.append(url)
        base = url.split('?')[0]
        value = self.served.get(base)
        if callable(value):
            return value(url)
        if value is None:
            return 404, None, 'HTTP 404'
        return 200, value, None

    def sleep(self, seconds):
        self.clock[0] += seconds

    def run_di(self, commit=None, **kwargs):
        return di.run(self.root, commit or self.commit_sha, api=self.api, fetch=self.fetch, sleep=self.sleep,
                      clock=lambda: self.clock[0], **kwargs)

    def test_identical(self):
        receipt = self.run_di()
        self.assertEqual(receipt['verdict'], 'identical')
        self.assertEqual(receipt['states'], ['awaiting-build', 'built', 'reading-back', 'identical'])
        paths = {r['path'] for r in receipt['rows']}
        self.assertTrue({'GENERATED.json', 'real-sky/native-sky.js', 'presets/p.json', 'v1/index.html'} <= paths)
        self.assertEqual({r['kind'] for r in receipt['rows']}, {'pages', 'raw-pinned', 'raw-main'})
        self.assertIn('v1/.gitattributes', {r['path'] for r in receipt['notPublished']})

    def test_excluded_path_is_not_published_and_stays_identical(self):
        receipt = self.run_di(extra=['docs/rlgwo-execution/x/evidence.json', 'tests/_private.json'])
        self.assertEqual(receipt['verdict'], 'identical')
        reasons = {r['path']: r['reason'] for r in receipt['notPublished']}
        self.assertEqual(reasons['docs/rlgwo-execution/x/evidence.json'], '_config.yml exclude prefix')
        self.assertIn('tests/_private.json', reasons)
        self.assertNotIn(di.SITE + 'docs/rlgwo-execution/x/evidence.json', self.fetched)

    def test_changed_byte_is_a_named_mismatch(self):
        self.served[di.SITE + 'config.js'] = b'C'
        receipt = self.run_di()
        self.assertEqual(receipt['verdict'], 'mismatch')
        self.assertIn('config.js', receipt['reason'])

    def test_missing_published_file_is_a_mismatch(self):
        del self.served[di.SITE + 'v1/index.html']
        receipt = self.run_di()
        self.assertEqual(receipt['verdict'], 'mismatch')
        self.assertIn('v1/index.html (pages, absent)', receipt['reason'])

    def test_pinned_raw_route_mismatch(self):
        self.served[di.RAW + self.first + '/install.sh'] = b'other'
        self.assertEqual(self.run_di()['verdict'], 'mismatch')

    def test_http_error_is_inconclusive(self):
        self.served[di.SITE + 'index.html'] = lambda url: (503, None, 'HTTP 503')
        self.assertEqual(self.run_di()['verdict'], 'inconclusive')

    def test_build_in_progress_is_inconclusive_and_reads_nothing(self):
        self.builds = [{'status': 'building', 'commit': self.commit_sha}]
        receipt = self.run_di()
        self.assertEqual(receipt['verdict'], 'inconclusive')
        self.assertEqual(self.fetched, [])
        self.assertEqual({r['state'] for r in receipt['rows']} - {'skipped'}, {'not-read'})

    def test_wrong_commit_is_inconclusive_never_identical(self):
        receipt = self.run_di(commit=self.first)
        self.assertEqual(receipt['verdict'], 'inconclusive')
        self.assertIn('latest Pages build is for', receipt['reason'])

    def test_errored_build_is_inconclusive(self):
        self.builds = [{'status': 'errored', 'commit': self.commit_sha}]
        receipt = self.run_di()
        self.assertEqual((receipt['verdict'], receipt['states'][-1]), ('inconclusive', 'errored'))

    def test_no_api_is_inconclusive(self):
        self.builds = [None]
        self.assertEqual(self.run_di()['verdict'], 'inconclusive')

    def test_bounded_wait_reaches_the_build(self):
        self.builds = [{'status': 'building', 'commit': self.commit_sha}, {'status': 'built', 'commit': self.commit_sha}]
        self.assertEqual(self.run_di(wait_build=120)['verdict'], 'identical')

    def test_cdn_retry_window_recovers_and_records_attempts(self):
        calls = []

        def stale(url):
            calls.append(url)
            return (200, b'old', None) if len(calls) == 1 else (200, self.files['index.html'], None)
        self.served[di.SITE + 'index.html'] = stale
        receipt = self.run_di(retry_window=60)
        self.assertEqual(receipt['verdict'], 'identical')
        row = next(r for r in receipt['rows'] if r['path'] == 'index.html')
        self.assertEqual(len(row['attempts']), 2)
        self.assertIn('?delivery-identity=', row['attempts'][1]['url'])
        self.served[di.SITE + 'index.html'] = lambda url: (200, b'old', None)
        self.assertEqual(self.run_di(retry_window=60)['verdict'], 'mismatch')

    def test_build_changing_during_readback_is_inconclusive(self):
        self.builds = [{'status': 'built', 'commit': self.commit_sha}, {'status': 'building', 'commit': '3' * 40}]
        self.assertEqual(self.run_di()['verdict'], 'inconclusive')

    def test_unpinned_main_route_skipped_when_main_advanced(self):
        self.main = '4' * 40
        receipt = self.run_di()
        self.assertEqual(receipt['verdict'], 'identical')
        self.assertEqual(next(r for r in receipt['rows'] if r['kind'] == 'raw-main')['state'], 'skipped')

    def test_bad_input_is_an_instrument_error(self):
        with self.assertRaises(di.InstrumentError):
            self.run_di(commit=self.commit_sha[:8])
        with self.assertRaises(di.InstrumentError):
            self.run_di(site='https://example.com/')
        with self.assertRaises(di.InstrumentError):
            di.http_get('https://api.open-meteo.com/v1/forecast', 1, 10)

    def test_bounds_are_enforced(self):
        with self.assertRaises(di.InstrumentError):
            self.run_di(limits={'maxFiles': 3})
        with self.assertRaises(di.InstrumentError):
            self.run_di(limits={'maxTotalBytes': 5})


class WorkflowGuards(unittest.TestCase):
    """G-06 static: least privilege, pinned actions, bounded steps, trigger semantics."""

    def text(self, name):
        return (ROOT / name).read_text(encoding='utf-8')

    def steps(self, text):
        jobs = text.split('\njobs:\n', 1)[1]
        return [block for block in re.split(r'\n(?=      - )', jobs) if block.lstrip().startswith('- ')]

    def test_guards(self):
        for name in WORKFLOWS:
            text = self.text(name)
            uses = re.findall(r'uses:\s*(\S+)', text)
            self.assertTrue(uses, name)
            for ref in uses:
                self.assertRegex(ref, r'^[\w.-]+/[\w.-]+@[0-9a-f]{40}$', name)
            self.assertNotIn('secrets.', text, name)
            self.assertNotRegex(text, r':\s*write\b', name)
            triggers = text.split('\non:', 1)[1].split('\npermissions:', 1)[0]
            self.assertNotRegex(triggers, r'\n  schedule:', name)
            self.assertEqual(text.count('actions/checkout@'), text.count('persist-credentials: false'), name)
            jobs = re.findall(r'\n  ([\w-]+):\n    (?:name|if|runs-on)', text)
            self.assertEqual(text.count('\n    timeout-minutes:'), len(jobs), name)
            for block in self.steps(text):
                self.assertIn('timeout-minutes:', block, name + ': ' + block.strip().splitlines()[0])
        self.assertIn('permissions:\n  contents: read\n\n', self.text(WORKFLOWS[0]))
        self.assertIn('permissions:\n  contents: read\n  pages: read\n\n', self.text(WORKFLOWS[1]))

    def test_gate_triggers_and_concurrency(self):
        text = self.text(WORKFLOWS[0])
        self.assertIn('pull_request:\n    branches: [main]', text)
        self.assertIn("branches: [main, 'claude/r002a-*']", text)
        self.assertIn('workflow_dispatch:', text)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", text)
        self.assertIn("github.event_name == 'pull_request' && 'pr' || github.sha", text)
        self.assertIn('github.event.pull_request.head.sha', text)
        for job in ('parity', 'suites', 'v1', 'pins'):
            self.assertIn('qualification_gate.py ' + job + ' ', text)
        self.assertNotIn('deploy', text.split('\njobs:\n', 1)[1].lower())

    def test_readback_triggers(self):
        text = self.text(WORKFLOWS[1])
        self.assertIn('  page_build:\n', text)
        self.assertIn('  workflow_dispatch:\n', text)
        self.assertIn('git show "$GITHUB_SHA:tools/qualification/delivery_identity.py"', text)


if __name__ == '__main__':
    unittest.main()
