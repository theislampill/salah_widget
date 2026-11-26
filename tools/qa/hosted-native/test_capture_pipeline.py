#!/usr/bin/env python3
"""Synthetic caller controls and real local crypto; no native observation."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

try:
    import capture_pipeline as P
except ModuleNotFoundError as error:
    if error.name != 'capture_pipeline':
        raise
    P = None


def population(root):
    return {p.relative_to(root).as_posix(): None if p.is_dir() else p.read_bytes()
            for p in root.rglob('*')}


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory(prefix='pipeline-test-recipient-')
        cls.key = Path(cls.keys.name)/'key.pem'
        cls.cert = Path(cls.keys.name)/'cert.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-nodes',
                        '-keyout', str(cls.key), '-out', str(cls.cert), '-days', '1',
                        '-subj', '/CN=Synthetic pipeline control'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.key.chmod(0o600)
        cls.cert.chmod(0o600)

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    def setUp(self):
        self.assertIsNotNone(P, 'integrated private capture caller is absent')
        self.tmp = tempfile.TemporaryDirectory(prefix='pipeline-control-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.task = self.root/'task'
        self.capture = self.task/'capture'
        self.capture.mkdir(parents=True, mode=0o700)
        self.task.chmod(0o700)
        self.roots = {k: self.root/k for k in ('research','baseline','historical')}
        for path in self.roots.values(): path.mkdir()
        (self.capture/'b0-initial.png').write_bytes(b'lower\x00\xff')
        (self.capture/'B0-initial.png').write_bytes(b'UPPER\xff\x00')
        (self.capture/'empty/nested').mkdir(parents=True)
        self.control = self.capture/'producer-control'
        self.control.mkdir(mode=0o700)
        self.fixture_producer('acquisition', 0)
        self.fixture_producer('observation', 2)
        campaign=json.loads((P.HERE/'campaign.json').read_text())
        self.engine=campaign['engine']
        requested=campaign.get('workOrders',[x for x in ('R0040','R003F','R0035','R002F')
                                             if x!='R002F' or campaign['r002f']['enabled']])
        self.orders=[x for x in ('R0040','R003F','R0035','R002F') if x in requested]
        self.observation = {
            'protocol':'salah-hosted-native-observation/1', 'engine':self.engine,
            'workOrders':self.orders, 'preparation':{'returncode':0,'timedOut':False,'elapsedSeconds':1.0},
            'lanes':[{'id':'fixture-lane','workOrder':self.orders[0],'status':'INCOMPLETE','stopAll':False,'innerStatus':None,
                      'namespaceProcess':{'returncode':0,'timedOut':False,'elapsedSeconds':1.0}}],
            'status':'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'}
        (self.capture/'observation.json').write_text(json.dumps(self.observation))
        self.plan={'protocol':'salah-hosted-native-lanes/1','sequential':True,'workOrders':self.orders,
                   'lanes':[{'id':'fixture-lane','workOrder':self.orders[0],'engine':self.engine}]}
        (self.capture/'lanes.json').write_text(json.dumps(self.plan))

    def fixture_producer(self, phase, returncode):
        identity = P.producer_identity(phase, self.task, self.roots)
        start = {'protocol':P.PRODUCER_PROTOCOL, 'identity':identity, 'phase':phase}
        result = {**start, 'returned':True, 'interrupted':False,
                  'process':{'returncode':returncode,'elapsedSeconds':1.0}}
        (self.control/(phase+'-started.json')).write_text(json.dumps(start))
        (self.control/(phase+'-completed.json')).write_text(json.dumps(result))

    def alter_producer(self, phase, change):
        p = self.control/(phase+'-completed.json')
        body = json.loads(p.read_text()); change(body); p.write_text(json.dumps(body))

    def seal(self):
        return P.seal_capture(self.task, self.roots, self.cert)

    def assert_refused_without_output(self):
        with self.assertRaises(P.Rejected): self.seal()
        self.assertFalse((self.task/'sealed').exists())
        self.assertFalse((self.task/'transport-work').exists())

    def test_complete_failed_lane_retains_case_distinct_bytes_through_real_crypto(self):
        original = population(self.capture)
        self.seal()
        self.assertEqual(set(p.name for p in (self.task/'sealed').iterdir()), {'capture.p7m','envelope.json'})
        restored = self.root/'restored'
        P.open_capture(self.task/'sealed', restored, self.cert, self.key, list(self.roots.values()))
        self.assertEqual(population(restored), original)
        self.assertFalse((self.task/'transport-work').exists())
        self.assertFalse(list(self.root.glob('capture-open-*')))

    def test_missing_completion_refuses_even_with_terminal_observation(self):
        (self.control/'observation-completed.json').unlink()
        self.assert_refused_without_output()

    def test_signaled_outer_process_refuses(self):
        self.alter_producer('observation', lambda b:b['process'].update(returncode=-9))
        self.assert_refused_without_output()

    def test_interrupted_outer_process_refuses_even_after_normal_child_return(self):
        self.alter_producer('observation', lambda b:b.update(interrupted=True))
        self.assert_refused_without_output()

    def test_copied_status_without_matching_started_identity_refuses(self):
        self.alter_producer('observation', lambda b:b['identity'].update(argv=['foreign']))
        self.assert_refused_without_output()

    def test_current_source_substitution_refuses(self):
        self.alter_producer('observation', lambda b:b['identity']['sources'].update({'observe.py':'0'*64}))
        self.assert_refused_without_output()

    def test_outer_error_refuses_even_with_prior_terminal_record(self):
        (self.capture/'coordinator-error-outer.json').write_text('{"type":"InterruptedError"}')
        self.assert_refused_without_output()

    def test_initial_incomplete_record_is_not_terminal(self):
        self.observation.update(status='INCOMPLETE',lanes=[])
        (self.capture/'observation.json').write_text(json.dumps(self.observation))
        self.assert_refused_without_output()

    def test_missing_namespace_process_refuses(self):
        self.observation['lanes'][0].pop('namespaceProcess')
        (self.capture/'observation.json').write_text(json.dumps(self.observation))
        self.assert_refused_without_output()

    def test_shortened_terminal_lane_population_refuses(self):
        (self.capture/'lanes.json').write_text(json.dumps({'lanes':[{'id':'fixture-lane'},{'id':'second'}]}))
        self.assert_refused_without_output()

    def test_completed_namespace_timeout_preserves_failure_evidence(self):
        self.observation['lanes'][0].update(status='ISOLATION_UNCONFIRMED')
        self.observation['lanes'][0]['namespaceProcess'].update(returncode=-15,timedOut=True)
        self.observation['status']='ISOLATION_UNCONFIRMED'
        (self.capture/'observation.json').write_text(json.dumps(self.observation))
        self.seal()
        self.assertTrue((self.task/'sealed/capture.p7m').is_file())

    def test_completed_failed_preparation_retains_no_fictitious_lanes(self):
        self.observation.update(status='INCOMPLETE',lanes=[])
        self.observation['preparation']['returncode']=2
        (self.capture/'observation.json').write_text(json.dumps(self.observation))
        (self.capture/'lanes.json').unlink()
        self.seal()
        self.assertTrue((self.task/'sealed/capture.p7m').is_file())

    def test_ordinary_acquisition_failure_can_retain_only_its_completed_evidence(self):
        self.fixture_producer('acquisition',1)
        for p in self.control.glob('observation-*'): p.unlink()
        (self.capture/'observation.json').unlink(); (self.capture/'lanes.json').unlink()
        self.seal()
        self.assertTrue((self.task/'sealed/capture.p7m').is_file())

    def test_acquisition_failure_with_an_observation_is_ambiguous(self):
        self.fixture_producer('acquisition',1)
        self.assert_refused_without_output()

    def test_sealing_failure_cleans_added_plaintext_and_preserves_original(self):
        original=population(self.capture)
        broken=self.root/'bad-cert'; broken.write_text('not a certificate')
        with self.assertRaises(P.Rejected): P.seal_capture(self.task,self.roots,broken)
        self.assertEqual(population(self.capture),original)
        self.assertFalse((self.task/'sealed').exists())
        self.assertFalse((self.task/'transport-work').exists())

    def test_tampered_ciphertext_never_restores_plaintext(self):
        self.seal(); sealed=self.task/'sealed'
        cipher=sealed/'capture.p7m'; raw=bytearray(cipher.read_bytes());raw[-1]^=1;cipher.write_bytes(raw)
        meta=sealed/'envelope.json'; body=json.loads(meta.read_text());body['ciphertext_sha256']=hashlib.sha256(raw).hexdigest();meta.write_text(json.dumps(body))
        with self.assertRaises(P.Rejected):P.open_capture(sealed,self.root/'restored',self.cert,self.key,list(self.roots.values()))
        self.assertFalse((self.root/'restored').exists())
        self.assertFalse(list(self.root.glob('capture-open-*')))

    def test_symlinked_runtime_protection_root_refuses(self):
        alias=self.root/'alias';alias.symlink_to(self.roots['research'],target_is_directory=True)
        roots={**self.roots,'research':alias}
        with self.assertRaises(P.Rejected):P.seal_capture(self.task,roots,self.cert)
        self.assertFalse((self.task/'sealed').exists())

    def test_existing_output_is_not_replaced(self):
        out=self.task/'sealed';out.mkdir();(out/'keep').write_bytes(b'untouched')
        with self.assertRaises(P.Rejected):self.seal()
        self.assertEqual((out/'keep').read_bytes(),b'untouched')

    def test_real_child_failure_streams_and_exit_are_recorded_without_public_content(self):
        for p in self.control.glob('observation-*'):p.unlink()
        ident={'syntheticControl':True,'argv':[sys.executable,'-c','import sys; print("PRIVATE-CANARY"); sys.exit(2)']}
        result=P.run_command(ident,self.task,'observation')
        self.assertEqual(result,2)
        body=json.loads((self.control/'observation-completed.json').read_text())
        self.assertEqual(body['process']['returncode'],2)
        self.assertTrue(body['returned']);self.assertFalse(body['interrupted'])
        self.assertIn('PRIVATE-CANARY',(self.capture/'observation.stdout').read_text())

    def test_cli_failure_category_does_not_publish_private_path_or_content(self):
        private=self.root/'PRIVATE-CANARY';private.mkdir()
        stream=io.StringIO()
        with contextlib.redirect_stderr(stream):
            code=P.main(['seal','--task',str(private),'--research',str(self.roots['research']),
                         '--baseline',str(self.roots['baseline']),'--historical',str(self.roots['historical']),
                         '--certificate',str(self.cert)])
        self.assertEqual(code,1)
        self.assertEqual(stream.getvalue(),'CAPTURE_PIPELINE_REJECTED:PRODUCER_INCOMPLETE\n')

    def test_capture_alias_is_refused_before_control_or_stream_writes(self):
        shutil.rmtree(self.capture)
        self.capture.symlink_to(self.roots['research'],target_is_directory=True)
        argv=['run','--phase','acquisition','--task',str(self.task)]
        for key,path in self.roots.items():argv += ['--'+key,str(path)]
        with mock.patch.object(P.subprocess,'Popen',side_effect=AssertionError('must not launch')) as launch:
            with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(P.main(argv),1)
        self.assertFalse(launch.called)
        self.assertEqual(population(self.roots['research']),{})

    def test_collapsed_symlink_component_cannot_change_actual_source_root(self):
        external=self.root/'external';(external/'inner').mkdir(parents=True)
        (external/'research').mkdir()
        (self.root/'jump').symlink_to(external/'inner',target_is_directory=True)
        raw=self.root/'jump/../research'
        self.assertNotEqual(raw.resolve(),Path(os.path.abspath(raw)))
        task=external/'research/task';(task/'capture').mkdir(parents=True,mode=0o700);task.chmod(0o700)
        roots={**self.roots,'research':raw}
        with self.assertRaises(P.Rejected):P.roots_checked(task,roots)
        with self.assertRaises(P.Rejected):P.producer_identity('acquisition',task,roots)

    def test_terminal_identity_population_and_status_fields_are_required(self):
        mutations=[lambda b:b.pop('engine'),lambda b:b.update(engine='FOREIGN'),
                   lambda b:b.pop('workOrders'),lambda b:b.update(workOrders=['FOREIGN']),
                   lambda b:b['lanes'][0].pop('status'),lambda b:b['lanes'][0].update(status='FOREIGN'),
                   lambda b:b['lanes'][0].pop('workOrder'),lambda b:b['lanes'][0].update(workOrder='FOREIGN'),
                   lambda b:b['lanes'][0].pop('stopAll'),lambda b:b['lanes'][0].update(stopAll=1),
                   lambda b:b['lanes'][0].pop('innerStatus')]
        for index,change in enumerate(mutations):
            with self.subTest(index=index):
                body=json.loads(json.dumps(self.observation));change(body)
                (self.capture/'observation.json').write_text(json.dumps(body))
                with self.assertRaises(P.Rejected):P.admit_producers(self.task,self.roots)

    def test_terminal_plan_identity_fields_are_required(self):
        mutations=[lambda b:b.pop('protocol'),lambda b:b.update(sequential=1),
                   lambda b:b.pop('workOrders'),lambda b:b['lanes'][0].pop('workOrder'),
                   lambda b:b['lanes'][0].update(engine='FOREIGN')]
        for index,change in enumerate(mutations):
            with self.subTest(index=index):
                body=json.loads(json.dumps(self.plan));change(body)
                (self.capture/'lanes.json').write_text(json.dumps(body))
                with self.assertRaises(P.Rejected):P.admit_producers(self.task,self.roots)

    def test_original_not_run_forms_and_failed_controls_remain_retainable(self):
        for status in ('FAIL','INCOMPLETE','INCONCLUSIVE','ANDON','NOT_RUN'):
            with self.subTest(status=status):
                body=json.loads(json.dumps(self.observation));row=body['lanes'][0];row['status']=status
                if status=='NOT_RUN':
                    row.pop('namespaceProcess');row.pop('stopAll');row.pop('innerStatus')
                    row['reason']='workstream stopped by scoped Andon'
                (self.capture/'observation.json').write_text(json.dumps(body))
                self.assertEqual(P.admit_producers(self.task,self.roots),'COMPLETED_OBSERVATION')

    def test_offline_parent_open_failure_creates_no_temporary_reservation(self):
        source=self.root/'sealed';source.mkdir();real_open=P.os.open
        def failure(path,*args,**kwargs):
            if Path(path)==self.root:raise OSError('injected parent descriptor failure')
            return real_open(path,*args,**kwargs)
        with mock.patch.object(P.os,'open',side_effect=failure):
            with self.assertRaises(Exception):
                P.open_capture(source,self.root/'restored',self.cert,self.key,list(self.roots.values()))
        self.assertFalse(list(self.root.glob('capture-open-*')))

    def test_unknown_post_mkdir_identity_refuses_before_payload_and_never_guesses_cleanup(self):
        target=self.task/'transport-work';real_stat=P.os.stat;T=P.transport()
        def failure(path,*args,**kwargs):
            if path==target.name and kwargs.get('dir_fd') is not None:raise OSError('injected identity failure')
            return real_stat(path,*args,**kwargs)
        with mock.patch.object(P.os,'stat',side_effect=failure):
            with self.assertRaisesRegex(P.Rejected,'^CLEANUP$'):
                with P.owned_directory(target,T):self.fail('identity failure must not reach payload operations')
        self.assertTrue(target.is_dir());self.assertEqual(population(target),{})


if __name__=='__main__':unittest.main()
