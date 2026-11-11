"""Inert receipt/inventory tests. No process, namespace, observer or product launch."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('namespace_probe', ROOT / 'installer_preview_linux_namespace_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class NamespaceReceiptTests(unittest.TestCase):
    def healthy(self):
        host = {'namespaceIds': {'user': 'user:[1]', 'net': 'net:[1]', 'mnt': 'mnt:[1]', 'pid': 'pid:[1]'}}
        identity = {'pid': 100, 'ppid': 99, 'uid': 0, 'euid': 0, 'gid': 0, 'egid': 0,
                    'groups': [0], 'pgid': 98, 'sid': 98,
                    'namespaceIds': {'user': 'user:[2]', 'net': 'net:[2]', 'mnt': 'mnt:[2]', 'pid': 'pid:[1]'},
                    'status': {'text': 'voluntary_ctxt_switches:\t1\n'}}
        result_identity = copy.deepcopy(identity)
        result_identity['status']['text'] = 'voluntary_ctxt_switches:\t3\n'
        uid = str(os.getuid())
        record = {'executionOutcome': 'TERMINAL_EXIT', 'returncode': 0,
                  'cleanup': {'complete': True, 'signals': []}, 'stdoutEqualsControlResult': True,
                  'readiness': {'subject': {'identity': identity}, 'parentReadAncestry': [
                      {'status': {'text': 'Uid:\t' + '\t'.join([uid] * 4) + '\nNoNewPrivs:\t1\nSeccomp:\t2\n'}}]},
                  'controlResult': {'nonce': 'fixture', 'complete': True, 'identity': result_identity,
                                    'outsideWrites': [{'name': n, 'denied': True, 'errno': 30} for n in ('new-file', 'sentinel')],
                                    'transports': [{'transport': n, 'denied': True, 'errno': 1, 'stage': 'socket'} for n in ('TCP', 'UDP')]},
                  'ownedWriteMatches': True,
                  'transportAttempts': [{'pid': 100, 'syscall': 'socket', 'decision': 'DENIED_EPERM'} for _ in range(2)]}
        snapshot = {'complete': True, 'passes': [{'rows': [{'name': 'sentinel', 'sha256': 'owned'}]} for _ in range(2)]}
        return record, snapshot, host

    def test_healthy_receipt_with_retained_volatile_process_status(self):
        record, snap, host = self.healthy()
        self.assertTrue(probe.assess(record, snap, snap, 'fixture', host)['containmentControlObserved'])

    def test_missing_denial_record_is_not_zero_attempts(self):
        record, snap, host = self.healthy()
        record['transportAttempts'] = None
        self.assertFalse(probe.assess(record, snap, snap, 'fixture', host)['containmentControlObserved'])

    def test_wrong_namespace_wrong_pid_and_cleanup_cannot_pass(self):
        original, snap, host = self.healthy()
        changes = [lambda r: r['readiness']['subject']['identity']['namespaceIds'].update(net='net:[1]'),
                   lambda r: r['transportAttempts'][0].update(pid=999),
                   lambda r: r['cleanup'].update(complete=False),
                   lambda r: r['cleanup'].update(signals=[{'signal': 'SIGKILL'}]),
                   lambda r: r.update(returncode=2),
                   lambda r: r.update(ownedWriteMatches=False),
                   lambda r: r.update(stdoutEqualsControlResult=False)]
        for change in changes:
            record = copy.deepcopy(original)
            change(record)
            with self.subTest(change=change):
                self.assertFalse(probe.assess(record, snap, snap, 'fixture', host)['containmentControlObserved'])

    def test_outside_state_change_and_incomplete_acquisition_cannot_pass(self):
        record, snap, host = self.healthy()
        after = copy.deepcopy(snap)
        after['passes'][1]['rows'][0]['sha256'] = 'changed'
        self.assertFalse(probe.assess(record, snap, after, 'fixture', host)['containmentControlObserved'])
        incomplete = {'complete': False, 'passes': []}
        self.assertFalse(probe.assess(record, snap, incomplete, 'fixture', host)['containmentControlObserved'])

    def test_stable_complete_inventory(self):
        with tempfile.TemporaryDirectory(prefix='namespace-inert-', dir=ROOT) as temporary:
            root = Path(temporary)
            (root / 'sentinel').write_bytes(b'owned')
            receipt = probe.inventory(root)
            self.assertTrue(receipt['complete'])
            self.assertEqual(receipt['passes'][0]['rows'], receipt['passes'][1]['rows'])

    def test_missed_late_file_and_mixed_time_inventory_is_incomplete(self):
        with tempfile.TemporaryDirectory(prefix='namespace-inert-', dir=ROOT) as temporary:
            root = Path(temporary)
            existing = root / 'existing'
            existing.write_bytes(b'old')
            actual_lstat = Path.lstat
            changed = False
            def late_creation(path):
                nonlocal changed
                if path == existing and not changed:
                    changed = True
                    (root / 'late-file').write_bytes(b'late')
                    existing.write_bytes(b'newer existing content')
                return actual_lstat(path)
            with mock.patch.object(Path, 'lstat', late_creation):
                receipt = probe.inventory(root)
            first, second = receipt['passes']
            self.assertEqual(first['errors'], [])
            self.assertNotIn('late-file', [r['name'] for r in first['rows']])
            self.assertEqual(next(r['sha256'] for r in first['rows'] if r['name'] == 'existing'),
                             hashlib.sha256(b'newer existing content').hexdigest())
            self.assertIn('late-file', [r['name'] for r in second['rows']])
            self.assertFalse(receipt['complete'])

    def test_route_change_preserves_common_filesystem_bind_arguments(self):
        args = (Path('/owned/fixture'), Path('/owned/fixture/case'), {'HOME': '/owned/fixture/home'},
                Path('/frozen/install-preview.py'), Path('/frozen/control.py'), Path('/owned/spec.json'))
        original, original_common = probe.build_command('original-unshare', *args)
        packaged, packaged_common = probe.build_command('packaged-bwrap', *args)
        self.assertEqual(original_common, packaged_common)
        self.assertEqual(original[-6:], packaged[-6:])
        self.assertNotIn('sudo', original + packaged)
        self.assertNotIn('--unshare-user-try', original + packaged)
        self.assertEqual(probe.ROUTES, ('original-unshare', 'packaged-bwrap'))
        with self.assertRaises(ValueError):
            probe.build_command('uncontained', *args)


if __name__ == '__main__':
    unittest.main(verbosity=2)
