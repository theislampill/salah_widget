"""Returned currentness retention controls; all positive native prerequisites are doubles.

Real observer/plan/terminal and producer gates execute against real temporary files.
No browser or positive native namespace runs. The subprocess byte control is an
actual bounded child; generated-source and prepared-tree prerequisites are named
doubles, not native evidence.
"""
import contextlib
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import observe as O
import lanes as L
import capture_pipeline as P
import r003f_diagnostics as D
import r0040_passive_central as R
import r003f_diagnostic_controls as diagnostic_fixtures
import r0040_passive_central_controls as passive_fixtures

HERE = Path(__file__).resolve().parent
RAW_OUT = b'known refusal\x00\xff\n'
RAW_ERR = b'actual retained error\xfe\n'


class ReturnedCurrentness(unittest.TestCase):
    def diagnostic(self, mode):
        fixture = diagnostic_fixtures.DiagnosticCentral('runTest')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        plan = fixture.plan(mode, fixture.admission(mode))
        runtime = fixture.runtime(mode); args = fixture.arguments(mode)
        return SimpleNamespace(task=fixture.task, plan=plan, runtime=runtime, args=args,
            campaign=fixture.campaign(mode), prepared=fixture.prepared(), module=D,
            child=[runtime['python'], '-B', str(HERE/'r003f_diagnostics.py'), 'readmit'], seconds=120,
            patches=[patch.object(D, 'custody_prefix', return_value={'prepared':fixture.prepared()})])

    def passive(self):
        fixture = passive_fixtures.PassiveCentral('runTest')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        f = fixture.fixture()
        return SimpleNamespace(task=f.task, plan=f.plan, runtime=f.runtime, args=f.args,
            campaign={'engine':'chromium', 'workOrders':['R0040'], 'r0040Mode':'capture-passive',
                      'r002f':{'enabled':False}}, prepared=f.prepared, module=R,
            child=[f.runtime['python'], '-B', str(HERE/'r0040_passive_central.py'), '--readmit'],
            seconds=120, patches=[])

    def tabhide(self):
        fixture = self.diagnostic('firefox-policy')
        task=fixture.task; runtime={**fixture.runtime,'engine':'chromium'}; prepared=fixture.prepared
        build=task/'work/r002f-prepared/build-result.json'; build.parent.mkdir(parents=True)
        O.write_json(build,{})
        process=task/'capture/r002f-preparation-process.json'
        O.write_json(process,{'argv':[runtime['python'],str(HERE/'r002f_prepare.py'),
            '--research',prepared['sources']['research']['root'],'--baseline',prepared['sources']['baseline']['root'],
            '--out',str(build.parent),'--node',runtime['node']], 'cwd':str(HERE),
            'timeoutSeconds':900,'returncode':0,'timedOut':False,'elapsedSeconds':0.1})
        process.with_name('r002f-preparation.stdout').write_bytes(b'R002F_BUILD PASS\n')
        process.with_name('r002f-preparation.stderr').write_bytes(b'')
        base={'status':'PASS','trees':{arm:{'root':str(build.parent/arm)} for arm in ('baseline','candidate')},
              'receipt':{'path':str(build),'sha256':O.digest(build)},
              'processReceipt':{'path':str(process),'sha256':O.digest(process)}}
        generated={'sourceManifest':L.tabhide_manifest(),'sourceManifestSha256':L.R002F_TABHIDE_MANIFEST_SHA256,
                   'baseline':{'explicitSyntheticGeneratedAdmission':True},'candidate':{'explicitSyntheticGeneratedAdmission':True}}
        common=task/'work/prepared/receipts/prepared.json'
        with patch.object(L,'admit_r002f',side_effect=lambda *a:copy.deepcopy(base)), \
             patch.object(L.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(generated).encode(),stderr=b'')):
            admission=L.admit_r002f_tabhide(build,process,prepared,common,Path(runtime['node']))
        self.assertEqual(admission['status'],'PASS',admission)
        plan=L.make_plan(prepared,task/'capture/lanes',python_playwright=Path(runtime['python']),
            node=Path(runtime['node']),node_modules=Path(runtime['modules']),pngjs=Path(runtime['pngjs']),
            include_r002f=True,work_orders=['R002F'],r002f_route='tabhide',r002f_preparation=admission)
        plan['preparedReceipt']={'path':str(common),'sha256':O.digest(common)}
        args=SimpleNamespace(**{**vars(fixture.args),'engine':'chromium','work_orders':['R002F'],
            'r003f_harness':'published','r002f':True,'r002f_route':'tabhide','r002f_dpr':1,'r002f_rounds':1,'r002f_section':'all'})
        return SimpleNamespace(task=task,plan=plan,runtime=runtime,args=args,
            campaign={'engine':'chromium','workOrders':['R002F'],'r002fRoute':'tabhide','r002f':{'enabled':True}},
            prepared=prepared,module=None,child=[runtime['node'],str(HERE/'r002f_tabhide.cjs'),'--admit-generated',
                str(build.parent/'baseline'),str(build.parent/'candidate')],seconds=30,
            patches=[patch.object(L,'admit_r002f',side_effect=lambda *a:copy.deepcopy(base)),
                     patch.object(O,'validate_prepared',return_value=prepared)])

    def process(self, f, *, code=2, timed=False):
        return {'argv':f.child,'cwd':str(HERE),'timeoutSeconds':f.seconds,'returncode':code,'timedOut':timed,
                'stdout':RAW_OUT.decode('utf8','replace'),'stderr':RAW_ERR.decode('utf8','replace'),
                'stdoutBytes':RAW_OUT,'stderrBytes':RAW_ERR}

    def execute(self, f, process, mutate=None, exception=None, write_failure=False):
        plan=copy.deepcopy(f.plan)
        if mutate:mutate(plan)
        O.write_json(f.task/'runtime.json',f.runtime)
        O.write_json(f.task/'capture/acquisition-identity.json',
                     {'protocol':'salah-hosted-native-acquisition/1','runtime':f.runtime})
        O.write_json(f.task/'capture/lanes.json',plan)
        original_plan=(f.task/'capture/lanes.json').read_bytes()
        args=['observe.py','--task',str(f.task),'--engine',f.args.engine,'--work-orders',*f.args.work_orders]
        for key in ('research','baseline','historical'):args+=['--'+key,str(getattr(f.args,key))]
        if f.module is D:args+=['--r003f-harness',f.args.r003f_harness]
        elif f.module is R:args+=['--r0040-mode','capture-passive']
        else:args+=['--r002f','--r002f-route','tabhide']
        runs=[]
        def prepare_only(*a):
            runs.append(a)
            if len(runs)>1:raise AssertionError('refused currentness launched a lane')
            return {'returncode':0,'timedOut':False,'elapsedSeconds':0.01}
        with contextlib.ExitStack() as stack:
            for p in f.patches:stack.enter_context(p)
            # Keep this existing route-currentness control downstream of the
            # separately tested source-only runner prerequisite.
            stack.enter_context(patch.object(O.runner_environment,'current',return_value={'scope':'SOURCE_CONTROL_ONLY'}))
            stack.enter_context(patch.object(sys,'argv',args))
            stack.enter_context(patch.object(O,'isolated_command',return_value=['synthetic-preparation']))
            stack.enter_context(patch.object(O,'run_bounded',side_effect=prepare_only))
            if f.module:
                child=stack.enter_context(patch.object(f.module,'readmit',return_value=process,side_effect=exception))
            else:
                child=stack.enter_context(patch.object(L.subprocess,'run',side_effect=exception,
                    return_value=SimpleNamespace(returncode=process['returncode'],stdout=process['stdoutBytes'],stderr=process['stderrBytes'])))
            if write_failure:
                write=O.write_json
                def fail_retention(path,body):
                    if 'currentness' in Path(path).parts:raise OSError('synthetic retention refusal')
                    return write(path,body)
                stack.enter_context(patch.object(O,'write_json',side_effect=fail_retention))
            code=O.main();calls=child.call_count
        self.assertEqual((f.task/'capture/lanes.json').read_bytes(),original_plan,'original plan was rewritten')
        body=json.loads((f.task/'capture/observation.json').read_bytes())
        original_load=P.load
        def load(path):return f.campaign if Path(path)==P.HERE/'campaign.json' else original_load(path)
        with patch.object(P,'completed',side_effect=lambda t,r,phase:0 if phase=='acquisition' else code),patch.object(P,'load',side_effect=load):
            try:gate=P.admit_producers(f.task,{})
            except P.Rejected as error:gate='REJECTED:'+str(error)
        return code,body,gate,calls

    def known_refusal(self, f, process):
        code,body,gate,calls=self.execute(f,process)
        self.assertEqual(code,2);self.assertEqual(calls,1)
        self.assertEqual(body['status'],'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')
        self.assertEqual([(r['id'],r['workOrder'],r['status']) for r in body['lanes']],
                         [(f.plan['lanes'][0]['id'],f.plan['lanes'][0]['workOrder'],'NOT_RUN')])
        self.assertNotIn('namespaceProcess',body['lanes'][0])
        self.assertEqual(gate,'COMPLETED_OBSERVATION')
        self.assertFalse((f.task/'capture/coordinator-error-outer.json').exists())
        receipts=list((f.task/'capture/currentness').glob('*/process.json'));self.assertEqual(len(receipts),1)
        receipt=json.loads(receipts[0].read_bytes())
        self.assertEqual(receipt['process']['returncode'],process['returncode'])
        self.assertEqual(receipt['process']['timedOut'],process['timedOut'])
        for label,wanted in (('stdout',RAW_OUT),('stderr',RAW_ERR)):
            row=receipt['streams'][label]
            self.assertEqual(Path(row['path']).read_bytes(),wanted)
            self.assertEqual(row['sha256'],hashlib.sha256(wanted).hexdigest())
            self.assertEqual(row['bytes'],len(wanted))

    def test_firefox_completed_refusal_is_retained_without_dispatch(self):
        f=self.diagnostic('firefox-policy');self.known_refusal(f,self.process(f))

    def test_webkit_completed_refusal_is_retained_without_dispatch(self):
        f=self.diagnostic('preconnect-input');self.known_refusal(f,self.process(f))

    def test_firefox_drained_timeout_is_retained_without_dispatch(self):
        f=self.diagnostic('firefox-policy');self.known_refusal(f,self.process(f,code=-9,timed=True))

    def test_webkit_drained_timeout_is_retained_without_dispatch(self):
        f=self.diagnostic('preconnect-input');self.known_refusal(f,self.process(f,code=-9,timed=True))

    def test_passive_completed_refusal_preserves_original_plan_and_streams(self):
        f=self.passive();self.known_refusal(f,self.process(f))

    def test_passive_drained_timeout_preserves_original_plan_and_streams(self):
        f=self.passive();self.known_refusal(f,self.process(f,code=-9,timed=True))

    def test_r002f_completed_generated_refusal_preserves_original_plan_and_streams(self):
        f=self.tabhide();self.known_refusal(f,self.process(f))

    def test_unknown_return_boolean_signal_or_missing_raw_streams_stay_unsealable(self):
        for change in ({'returncode':None},{'returncode':False},{'returncode':-9},
                       {'timedOut':'true'},{'error':'unknown process failure'},
                       {'interrupted':True},{'stdoutBytes':None}):
            with self.subTest(change=change):
                f=self.diagnostic('firefox-policy');p={**self.process(f),**change}
                code,body,gate,_=self.execute(f,p)
                self.assertEqual(code,2);self.assertEqual(body['lanes'],[])
                self.assertEqual(gate,'REJECTED:PRODUCER_INCOMPLETE')

    def test_invalid_or_incomplete_canonical_plan_never_reaches_readmission(self):
        for change in (lambda x:x['lanes'].clear(),lambda x:x['lanes'].append(copy.deepcopy(x['lanes'][0])),
                       lambda x:x['lanes'][0].update(timeoutSeconds=1),
                       lambda x:x['lanes'][0].update(output='/foreign/capture')):
            with self.subTest(change=change):
                f=self.diagnostic('preconnect-input')
                code,body,gate,calls=self.execute(f,self.process(f),mutate=change)
                self.assertEqual((code,calls),(2,0));self.assertEqual(body['lanes'],[])
                self.assertEqual(gate,'REJECTED:PRODUCER_INCOMPLETE')

    def test_zero_return_malformed_output_still_has_no_recovery_authority(self):
        f=self.diagnostic('firefox-policy')
        code,body,gate,_=self.execute(f,self.process(f,code=0))
        self.assertEqual(code,2);self.assertEqual(body['lanes'],[])
        self.assertEqual(gate,'REJECTED:PRODUCER_INCOMPLETE')

    def test_interruption_and_retention_error_cannot_be_converted_to_not_run(self):
        for exception,write_failure in ((InterruptedError('controlled interruption'),False),(None,True)):
            f=self.diagnostic('firefox-policy')
            code,body,gate,_=self.execute(f,self.process(f),exception=exception,write_failure=write_failure)
            self.assertEqual(code,2);self.assertEqual(body['lanes'],[])
            self.assertEqual(gate,'REJECTED:PRODUCER_INCOMPLETE')

    def test_r002f_timeout_without_waited_return_is_not_inferred_complete(self):
        f=self.tabhide()
        code,body,gate,_=self.execute(f,self.process(f),exception=subprocess.TimeoutExpired(f.child,30,output=b'partial'))
        self.assertEqual(code,2);self.assertEqual(body['lanes'],[])
        self.assertEqual(gate,'REJECTED:PRODUCER_INCOMPLETE')

    def test_actual_diagnostic_readmission_preserves_undecodable_stream_bytes(self):
        f=self.diagnostic('firefox-policy')
        command=[sys.executable,'-c',"import os;os.write(1,b'\\xff\\x00');os.write(2,b'\\xfe');raise SystemExit(2)"]
        actual=D.bounded(command,{},5,raw=True)
        self.assertEqual((actual['returncode'],actual['timedOut']),(2,False))
        self.assertEqual(actual['stdoutBytes'],b'\xff\x00');self.assertEqual(actual['stderrBytes'],b'\xfe')
        with patch.object(D,'bounded',return_value=actual) as child:
            retained=D.readmit('firefox-policy',f.task,f.runtime)
        self.assertEqual(retained['stdoutBytes'],b'\xff\x00')
        self.assertIs(child.call_args.kwargs.get('raw'),True)

    def test_passive_readmission_requests_raw_bytes_without_changing_bound(self):
        f=self.passive()
        actual=R.bounded_check([sys.executable,'-c',
            "import os;os.write(1,b'\\xff\\x00');os.write(2,b'\\xfe');raise SystemExit(2)"],{},5,raw=True)
        self.assertEqual((actual['returncode'],actual['timedOut']),(2,False))
        self.assertEqual(actual['stdoutBytes'],b'\xff\x00');self.assertEqual(actual['stderrBytes'],b'\xfe')
        with patch.object(R,'bounded_check',return_value=self.process(f)) as child:
            R.readmit(f.task/'work/prepared/receipts/prepared.json',f.runtime,f.task)
        self.assertEqual(child.call_args.args[2],120)
        self.assertIs(child.call_args.kwargs.get('raw'),True)


if __name__=='__main__':unittest.main()
