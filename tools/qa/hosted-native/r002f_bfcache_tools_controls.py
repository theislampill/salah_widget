#!/usr/bin/env python3
"""Native-free controls for the separately acquired bfcache decoder contract."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'r002f_bfcache_tools.py'


def feature(test):
    test.assertTrue(SOURCE.is_file(), 'selected-route tool admission has not been implemented')
    spec = importlib.util.spec_from_file_location('bfcache_tools_under_test', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def campaign():
    return {'schemaVersion': 1, 'engine': 'chromium', 'workOrders': ['R002F'],
            'r002f': {'enabled': True, 'dpr': 1, 'rounds': 1, 'section': 'all'},
            'r002fRoute': 'bfcache-witness', 'r003fHarness': 'published', 'r0040Mode': 'options',
            'r0035': {'guard': 'default', 'scope': 'all', 'mode': 'both'},
            'r0035Stages': False, 'r0035Costs': False, 'r0035Psf': False, 'evidenceRetention': False}


class ToolsControls(unittest.TestCase):
    def test_only_exact_selected_route_can_acquire_tools(self):
        m = feature(self)
        self.assertFalse(m.selected({'r002fRoute': 'offscreen'}))
        self.assertTrue(m.selected(campaign()))
        for key, value in [('engine', 'firefox'), ('workOrders', ['R002F', 'R0035']),
                           ('r003fHarness', 'corrected-matrix'), ('r0040Mode', 'capture-passive'),
                           ('r0035Psf', True), ('r0035Stages', True), ('r0035Costs', True),
                           ('evidenceRetention', True), ('r003fMatrix', {'variant': 'b0'})]:
            with self.subTest(key=key):
                x = campaign(); x[key] = value
                with self.assertRaises(ValueError): m.selected(x)
        for key, value in [('enabled', False), ('dpr', True), ('rounds', 3), ('section', 'preview')]:
            with self.subTest(key=key):
                x = campaign(); x['r002f'][key] = value
                with self.assertRaises(ValueError): m.selected(x)

    def test_original_decoder_arguments_are_executed_without_option_substitution(self):
        m = feature(self)
        self.assertEqual(m.decoder_argv('/usr/bin/ffmpeg', '/private/input.webm'),
                         ['/usr/bin/ffmpeg', '-v', 'error', '-i', '/private/input.webm',
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])

    def test_one_exact_stream_required_no_ignored_second_stream_or_rate(self):
        m = feature(self)
        stream = {'index': 0, 'codec_type': 'video', 'codec_name': 'vp8', 'width': 326,
                  'height': 530, 'r_frame_rate': '25/1', 'avg_frame_rate': '25/1', 'time_base': '1/1000'}
        self.assertEqual(m.admit_metadata({'streams': [stream], 'format': {'duration': '0.080'}}), stream)
        for key, value in [('codec_type', 'audio'), ('codec_name', 'vp9'), ('width', 325),
                           ('height', 529), ('r_frame_rate', '30/1'), ('avg_frame_rate', '0/0')]:
            x = dict(stream); x[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): m.admit_metadata({'streams': [x]})
        for rows in [[], [stream, stream], None]:
            with self.subTest(rows=rows), self.assertRaises(ValueError): m.admit_metadata({'streams': rows})

    def test_file_identity_rechecks_descriptor_and_rejects_capture_aliases(self):
        m = feature(self)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'bytes'; p.write_bytes(b'original')
            row = m.file_record(p)
            self.assertEqual(row['bytes'], 8)
            self.assertEqual(row['sha256'], '0682c5f2076f099c34cfdd15a9e063849ed437a49677e6fcc5b4198c76575be5')
            p.write_bytes(b'changed!')
            with self.assertRaises(ValueError): m.require_record(row)
            link = p.with_name('link'); link.symlink_to(p)
            with self.assertRaises(ValueError): m.file_record(link)
            hard = p.with_name('hard'); os.link(p, hard)
            with self.assertRaises(ValueError): m.file_record(hard)

    def test_cross_language_descriptor_records_preserve_nanoseconds_and_symlink_chain(self):
        m = feature(self)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'actual'; p.write_bytes(b'bytes')
            row = m.file_record(p)
            self.assertEqual(row['mtimeNs'], str(p.stat().st_mtime_ns))
            self.assertEqual(row['inode'], str(p.stat().st_ino))
            link = p.with_name('library-link'); link.symlink_to('actual')
            linked = m.file_record(link, system=True)
            self.assertEqual(linked['symlinks'], [{'path': str(link), 'target': 'actual'}])
            self.assertEqual(linked['resolvedPath'], str(p))

    def test_actual_process_output_overflow_and_timeout_never_claim_success(self):
        m = feature(self)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            overflow = m.run_bounded([sys.executable, '-c', 'import sys;sys.stdout.buffer.write(b"x"*10000)'],
                                     out, 'overflow', 3, max_stdout=64)
            self.assertTrue(overflow['overflow']); self.assertFalse(overflow['complete'])
            self.assertEqual((out/'overflow.stdout').stat().st_size, 64)
            timeout = m.run_bounded([sys.executable, '-c', 'import time;time.sleep(10)'],
                                    out, 'timeout', 0.05)
            self.assertTrue(timeout['timedOut']); self.assertFalse(timeout['complete'])
            self.assertIsInstance(timeout['returncode'], int)

    def test_actual_success_requires_zero_return_and_no_truncation(self):
        m = feature(self)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            got = m.run_bounded([sys.executable, '-c', 'print("source-control")'], p, 'ok', 3)
            self.assertTrue(got['complete']); self.assertEqual(got['returncode'], 0)
            self.assertEqual((p/'ok.stdout').read_bytes(), b'source-control\n')
            failed = m.run_bounded([sys.executable, '-c', 'raise SystemExit(7)'], p, 'failed', 3)
            self.assertEqual(failed['returncode'], 7); self.assertFalse(failed['complete'])

    def test_runtime_schema_has_no_hidden_decoder_key(self):
        m = feature(self)
        good = {key: '/actual/'+key for key in ('node', 'python', 'modules', 'playwright', 'pngjs')}
        good['engine'] = 'chromium'
        self.assertEqual(m.runtime_schema(good), good)
        for delta in ({'ffmpeg': '/usr/bin/ffmpeg'}, {'node': 'node'}, {'modules': None}, {'engine': 'firefox'}):
            with self.subTest(delta=delta), self.assertRaises(ValueError): m.runtime_schema({**good, **delta})
        with self.assertRaises(ValueError): m.runtime_schema({k:v for k,v in good.items() if k != 'engine'})
        # Original writer is read, never changed: the approved design's five-key wording was erroneous.
        import ast
        tree = ast.parse((HERE/'identities.py').read_text())
        values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'runtime' for t in n.targets)]
        self.assertEqual(len(values), 1)
        self.assertEqual({k.value for k in values[0].keys}, set(good))

    def test_synthetic_fixture_custody_requires_original_complete_bytes(self):
        m = feature(self)
        self.assertTrue(hasattr(m, 'admit_fixture'), 'fixture admission is not implemented')
        body = m.admit_fixture()
        expected = bytes(326*530*3) + bytes([255])*(326*530*3)
        self.assertEqual(body['scope'], 'SOURCE_CONTROL_ONLY')
        self.assertEqual(body['expectedDecodedBytes'], 1036680)
        self.assertEqual(body['expectedDecodedSha256'], hashlib.sha256(expected).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('r002f-bfcache-decode-control.webm', 'r002f-bfcache-decode-control.json'):
                (root/name).write_bytes((HERE/'fixtures'/name).read_bytes())
            (root/'r002f-bfcache-decode-control.webm').write_bytes(b'changed fixture')
            with self.assertRaises(ValueError): m.admit_fixture(root)

    def test_capability_failure_cannot_be_replaced_by_a_native_or_partial_result(self):
        m = feature(self)
        self.assertTrue(hasattr(m, 'run_fixture'), 'source capability admission is not implemented')
        original = bytes(326*530*3) + bytes([255])*(326*530*3)
        metadata = {'streams': [{'index': 0, 'codec_type': 'video', 'codec_name': 'vp8', 'width': 326,
                                'height': 530, 'r_frame_rate': '25/1', 'avg_frame_rate': '25/1', 'time_base': '1/1000'}],
                    'format': {'duration': '0.080'}}
        for failure in (None, 'unsupported', 'one-byte-short', 'trailing-byte', 'wrong-pixel', 'wrong-rate'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                out = Path(directory)
                def execute(argv, target, label, timeout, **kwargs):
                    if label == 'fixture-probe':
                        body = json.loads(json.dumps(metadata))
                        if failure == 'wrong-rate': body['streams'][0]['avg_frame_rate'] = '24/1'
                        payload = json.dumps(body).encode()
                    else:
                        self.assertEqual(argv[1:4], ['-v', 'error', '-i'])
                        self.assertEqual(argv[5:], ['-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
                        payload = (original[:-1] if failure == 'one-byte-short' else original+b'!' if failure == 'trailing-byte'
                                   else b'!'+original[1:] if failure == 'wrong-pixel' else original)
                    (target/(label+'.stdout')).write_bytes(payload)
                    (target/(label+'.stderr')).write_bytes(b'unsupported option' if failure == 'unsupported' else b'')
                    return {'argv': argv, 'returncode': 1 if failure == 'unsupported' else 0,
                            'complete': failure != 'unsupported', 'timedOut': False, 'overflow': False,
                            'streams': {k: m.file_record(target/(label+'.'+k)) for k in ('stdout', 'stderr')}}
                if failure:
                    with self.assertRaises(ValueError): m.run_fixture('/usr/bin/ffmpeg', '/usr/bin/ffprobe', out, execute=execute)
                else:
                    got = m.run_fixture('/usr/bin/ffmpeg', '/usr/bin/ffprobe', out, execute=execute)
                    self.assertEqual(got['scope'], 'SOURCE_CONTROL_ONLY'); self.assertEqual(got['status'], 'COMPLETE')

    def test_missing_or_ambiguous_elf_dependency_is_refused(self):
        m = feature(self)
        self.assertTrue(hasattr(m, 'parse_ldd'), 'ELF dependency closure is not implemented')
        got = m.parse_ldd('linux-vdso.so.1 (0x123)\nlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x456)\n/lib64/ld-linux-x86-64.so.2 (0x789)\n')
        self.assertEqual(got, ['/lib/x86_64-linux-gnu/libc.so.6', '/lib64/ld-linux-x86-64.so.2'])
        for body in ['libmissing.so => not found\n', 'libc.so.6 => relative/lib.so (0x1)\n', 'unexpected diagnostic\n']:
            with self.subTest(body=body), self.assertRaises(ValueError): m.parse_ldd(body)

    def test_elf_metadata_and_full_dependency_names_are_required(self):
        m = feature(self)
        self.assertTrue(hasattr(m, 'parse_elf'), 'ELF interpreter/dependency admission is not implemented')
        got = m.parse_elf('ELF Header:\n  Magic: 7f 45 4c 46\n [Requesting program interpreter: /lib64/ld-linux.so.2]\n 0x1 (NEEDED) Shared library: [libc.so.6]\n')
        self.assertEqual(got, {'interpreter': '/lib64/ld-linux.so.2', 'needed': ['libc.so.6']})
        for text in ['not an ELF', 'ELF Header:\n [Requesting program interpreter: relative]\n',
                     'ELF Header:\n 0x1 (NEEDED) Shared library: [../lib.so]\n']:
            with self.subTest(text=text), self.assertRaises(ValueError): m.parse_elf(text)

    def test_receipt_currentness_refuses_changed_dependency_and_source(self):
        m = feature(self)
        self.assertTrue(hasattr(m, 'current_records'), 'complete receipt currentness is not implemented')
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'library'; file.write_bytes(b'original library')
            row = m.file_record(file)
            receipt = {'closure': {'files': [row]}, 'sources': {'file': row}}
            self.assertEqual(m.current_records(receipt), 1)
            file.write_bytes(b'altered library!')
            with self.assertRaises(ValueError): m.current_records(receipt)

    def test_package_population_refuses_new_missing_or_alias_bytes(self):
        m = feature(self)
        self.assertTrue(hasattr(m, 'file_tree'), 'complete installed population is not implemented')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'one').write_bytes(b'one'); (root/'sub').mkdir(); (root/'sub/two').write_bytes(b'two')
            first = m.file_tree(root)
            self.assertEqual(set(first), {'one', 'sub/two'})
            (root/'added').write_bytes(b'added'); self.assertNotEqual(m.file_tree(root), first)
            (root/'alias').symlink_to(root/'one')
            with self.assertRaises(ValueError): m.file_tree(root)

    def test_loader_cache_and_locale_data_are_explicit_current_dependencies(self):
        m=feature(self)
        self.assertTrue(hasattr(m,'mapping_data'),'loader metadata dependency admission is not implemented')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'etc').mkdir();(root/'etc/ld.so.cache').write_bytes(b'source-only loader cache')
            (root/'usr/lib/locale/C.utf8').mkdir(parents=True);(root/'usr/lib/locale/C.utf8/LC_CTYPE').write_bytes(b'source-only locale')
            rows=m.mapping_data(root)
            self.assertEqual({Path(r['path']).relative_to(root).as_posix() for r in rows},{'etc/ld.so.cache','usr/lib/locale/C.utf8/LC_CTYPE'})
            (root/'etc/ld.so.cache').write_bytes(b'changed loader cache')
            with self.assertRaises(ValueError):m.current_records(rows)

    def test_actual_capability_child_refuses_unknown_mappings_and_keeps_failure_receipt(self):
        m=feature(self)
        self.assertTrue(hasattr(m,'mapped_files'),'actual capability mapping admission is missing')
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            bad=m.run_bounded([sys.executable,'-c','import time;time.sleep(2)'],folder,'unknown-map',3,mapping_rows=[])
            self.assertFalse(bad['complete']);self.assertTrue(bad['mappingErrors']);self.assertTrue(bad['signals'])
            rows=[m.file_record(p,system=True) for p in m.mapped_files(os.getpid())]
            good=m.run_bounded([sys.executable,'-c','import time;time.sleep(.1);print("source-control-only")'],
                               folder,'admitted-map',3,mapping_rows=rows)
            self.assertTrue(good['complete'],json.dumps(good));self.assertTrue(good['mappingsComplete']);self.assertGreater(good['mappingSnapshots'],0)
            self.assertEqual((folder/'admitted-map.stdout').read_bytes(),b'source-control-only\n')

    def test_failed_capability_keeps_the_actual_process_record_before_refusing(self):
        m=feature(self)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);returned=[]
            def execute(argv,target,label,timeout,**kwargs):
                (target/(label+'.stdout')).write_bytes(b'')
                (target/(label+'.stderr')).write_bytes(b'actual source-control probe refusal\n')
                row={'argv':argv,'cwd':str(target),'timeoutSeconds':timeout,'returncode':7,
                     'complete':False,'timedOut':False,'overflow':False,
                     'streams':{k:m.file_record(target/(label+'.'+k)) for k in ('stdout','stderr')}}
                returned.append(row);return row
            with self.assertRaisesRegex(ValueError,'synthetic probe'):
                m.run_fixture('/usr/bin/ffmpeg','/usr/bin/ffprobe',folder,execute=execute)
            self.assertEqual(len(returned),1)
            self.assertEqual(m.load(folder/'fixture-probe-process.json'),returned[0])

    def test_mapping_snapshot_distinguishes_actual_exit_from_empty_live_population(self):
        m=feature(self);real=m.mapped_files
        rows=[m.file_record(p,system=True) for p in real(os.getpid())]
        calls=[]
        def exit_during_snapshot(pid):
            calls.append(pid)
            if len(calls)==1:return real(pid)
            until=time.monotonic()+2
            while time.monotonic()<until:
                file=Path('/proc',str(pid),'stat')
                if not file.exists() or file.read_text().split(') ',1)[1].startswith('Z '):return []
                time.sleep(.002)
            self.fail('source-control child did not actually exit')
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            with patch.object(m,'mapped_files',side_effect=exit_during_snapshot):
                stopped=m.run_bounded([sys.executable,'-c','import time;time.sleep(.1)'],folder,'exited',3,mapping_rows=rows)
            self.assertGreaterEqual(len(calls),2)
            self.assertTrue(stopped['complete'],json.dumps(stopped));self.assertEqual(stopped['returncode'],0)
            self.assertEqual(stopped['mappingSnapshots'],1)
            with patch.object(m,'mapped_files',return_value=[]):
                live=m.run_bounded([sys.executable,'-c','import time;time.sleep(10)'],folder,'empty-live',3,mapping_rows=rows)
            self.assertFalse(live['complete']);self.assertTrue(live['mappingErrors']);self.assertTrue(live['signals'])


if __name__ == '__main__': unittest.main()
