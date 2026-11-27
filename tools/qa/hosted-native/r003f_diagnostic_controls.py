"""Bounded central source controls; no browser, native observation or owner key.

Positive preparation/namespace observations below are explicit doubles. Actual
source, retained bytes and subprocess refusal checks are identified separately.
"""
import copy
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest import mock

try:
    import r003f_diagnostics as D
except ModuleNotFoundError as error:
    if error.name != 'r003f_diagnostics':
        raise
    D = None

import lanes as L
import observe as O
import capture_pipeline as P

HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[2]
MODES = ('firefox-policy', 'preconnect-input')
ENGINES = ('firefox', 'webkit')


class DiagnosticCentral(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(D, 'shared R003F diagnostic integration is absent')
        self.tmp = tempfile.TemporaryDirectory(prefix='r003f-central-control-')
        self.addCleanup(self.tmp.cleanup)
        self.task = Path(self.tmp.name)/'task'
        (self.task/'capture/lanes').mkdir(parents=True)
        (self.task/'work/prepared/receipts').mkdir(parents=True)

    def runtime(self, mode):
        modules = self.task/'node/node_modules'
        return {'python': sys.executable, 'node': str(Path(shutil.which('node')).resolve()),
                'modules': str(modules), 'playwright': str(modules/'playwright'),
                'pngjs': str(modules/'pngjs'), 'engine': ENGINES[MODES.index(mode)]}

    def admission(self, mode):
        return {'status': 'PASS', 'protocol': D.ADMISSION, 'mode': mode,
                'task': str(self.task), 'runtime': self.runtime(mode),
                'research': '/synthetic/research', 'runtimeRoot': str(self.task/'work/prepared/trees/r003f'),
                'common': {'prepared': {'path': str(self.task/'work/prepared/receipts/prepared.json'),
                                         'sha256': 'a'*64}},
                'source': {'synthetic': 'explicit preparation/namespace double'}}

    def lane(self, mode):
        return D.make_lane(mode, self.admission(mode), self.task, self.runtime(mode))

    def inner(self, mode):
        lane = self.lane(mode)
        return {'id': lane['id'], 'status': D.ROUTES[mode]['status'], 'stopAll': False,
                'returncode': 0, 'timedOut': False, **D.scope_fields(mode)}

    def write(self, path, body):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(body if isinstance(body,bytes) else json.dumps(body).encode())

    def prepared(self):
        return {'status':'PREPARED','sources':{k:{'root':'/synthetic/'+k} for k in ('research','baseline','historical')},
            'trees':{k:{'root':str(self.task/'work/prepared/trees'/k)} for k in ('main','r0040','r0035','r003f')}}

    def arguments(self, mode):
        return SimpleNamespace(task=self.task,engine=D.ROUTES[mode]['engine'],work_orders=['R003F'],
            r003f_harness=mode,r003f_dpr=1,r003f_matrix=None,retain_evidence=False,r002f=False,
            research=Path('/synthetic/research'),baseline=Path('/synthetic/baseline'),historical=Path('/synthetic/historical'))

    def campaign(self, mode):
        return {'schemaVersion':1,'engine':D.ROUTES[mode]['engine'],'r003fDpr':1,'workOrders':['R003F'],
            'r003fHarness':mode,'evidenceRetention':False,
            'r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'}}

    def plan(self, mode, admission=None):
        runtime=self.runtime(mode)
        value=L.make_plan(self.prepared(),self.task/'capture/lanes',python_playwright=Path(runtime['python']),
            node=Path(runtime['node']),node_modules=Path(runtime['modules']),pngjs=Path(runtime['pngjs']),
            engine=runtime['engine'],r003f_harness=mode,work_orders=['R003F'],r003f_diagnostic_preparation=admission)
        self.write(self.task/'work/prepared/receipts/prepared.json',self.prepared())
        value['preparedReceipt']=D.record(self.task/'work/prepared/receipts/prepared.json')
        return value

    def custody(self, mode):
        """Actual files around explicitly synthetic preparation/acquisition values."""
        p=D.paths(self.task,mode);runtime=self.runtime(mode);prepared=self.prepared()
        self.write(self.task/'runtime.json',runtime)
        self.write(self.task/'capture/acquisition-identity.json',{'protocol':'salah-hosted-native-acquisition/1','runtime':runtime})
        self.write(p['common'],prepared)
        self.write(p['commonProcess'],{'returncode':0,'timedOut':False})
        argv=[runtime['python'],str(HERE/'prepare.py')]
        for key in ('research','baseline','historical'):argv+=['--'+key,prepared['sources'][key]['root']]
        argv+=['--out',str(self.task/'work/prepared')]
        context={'protocol':'source-only-common-preparation-execution/1','argv':argv,'cwd':str(HERE),
            'timeoutSeconds':900,'sourceSha256':D.PINS['prepare.py'],'nativeIsolationClaim':False}
        self.write(p['commonContext'],context)
        for name in ('preparation.stdout','preparation.stderr','r003f-diagnostic-preparation.stdout','r003f-diagnostic-preparation.stderr'):
            self.write(self.task/'capture'/name,b'explicit synthetic producer bytes\x00\xff')
        for name in ('stdout','stderr'):self.write(p['preparation']/('child.'+name),b'explicit child bytes\x00\xff')
        common={k:D.record(p[n]) for k,n in [('prepared','common'),('process','commonProcess'),('context','commonContext')]}
        child={'protocol':D.PREPARATION,'status':'PREPARED','nativeExecution':'NOT_RUN','mode':mode,'task':str(self.task),
            'runtime':runtime,'argv':D.preparation_child(mode,self.task,runtime,prepared),'cwd':str(HERE),'timeoutSeconds':60,
            'returncode':0,'timedOut':False,'streams':{k:D.artifact(p['preparation']/('child.'+k)) for k in ('stdout','stderr')},
            'common':common,'sources':D.verify_sources(),'binding':D.runtime_binding(self.task,runtime,mode),
            'source':{'synthetic':'explicit source-verifier double'}}
        self.write(p['preparationProcess'],child)
        entry={'protocol':D.PREPARATION_ENTRY,'argv':D.preparation_argv(mode,self.task,runtime),'cwd':str(HERE),
            'timeoutSeconds':180,'sourceSha256':D.sha(HERE/'r003f_diagnostics.py'),'process':str(p['preparationProcess']),
            'returncode':0,'timedOut':False}
        self.write(p['preparationEntry'],entry)
        return p,prepared,context,child,entry

    def source_fixture(self, mode):
        """Real source verifier input around non-executable, synthetic acquisition."""
        runtime=self.runtime(mode);prepared=self.prepared();prepared['sources']['research']['root']=str(ROOT)
        versions={'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'}
        for name,version in versions.items():
            self.write(Path(runtime['modules'])/name/'package.json',{'name':name,'version':version,'main':'index.cjs'})
        relative='node-browsers/'+D.ROUTES[mode]['engine']+'-987654/'+('firefox/firefox' if mode=='firefox-policy' else 'pw_run.sh')
        executable=self.task/relative;self.write(executable,b'SYNTHETIC NON-EXECUTABLE FILE: no browser exists in this fixture\n')
        entry=("throw Error('Firefox source check must not import Playwright');" if mode=='firefox-policy' else
            "module.exports={webkit:{executablePath:()=>require('node:path').join(process.env.PLAYWRIGHT_BROWSERS_PATH,'webkit-987654','pw_run.sh')}};")
        self.write(Path(runtime['playwright'])/'index.cjs',entry.encode())
        descriptor={'browsers':[{'name':runtime['engine'],'revision':'987654','browserVersion':'synthetic','installByDefault':True}]}
        descriptor_file=Path(runtime['modules'])/'playwright-core/browsers.json';self.write(descriptor_file,descriptor)
        locks={}
        for name in ('node/package.json','node/package-lock.json'):
            self.write(self.task/name,(HERE/name).read_bytes());locks[name]=D.sha(HERE/name)
        acquisition={'protocol':'salah-hosted-native-acquisition/1','runtime':runtime,'nodePackages':versions,
            'locks':locks,'browserDescriptors':{'node':{'sha256':D.sha(descriptor_file),'body':descriptor}},
            'browserExecutables':{relative:{'size':executable.stat().st_size,'sha256':D.sha(executable)}}}
        self.write(self.task/'runtime.json',runtime);self.write(self.task/'capture/acquisition-identity.json',acquisition)
        if mode=='preconnect-input':
            self.write(Path(prepared['trees']['r003f']['root'])/'index.html',(ROOT/'index.html').read_bytes())
            result=D.bounded(D.preparation_child(mode,self.task,runtime,prepared),{},60,raw=True)
            self.assertEqual(result['returncode'],0,result['stderr'])
            p=D.paths(self.task,mode);self.write(p['preparation']/'child.stdout',result['stdoutBytes'])
            self.assertEqual(D.sha(p['source']/'materialization.json'),D.WEBKIT_MATERIALIZATION)
        return prepared,runtime,executable

    @contextlib.contextmanager
    def producer(self, mode):
        """Exercise the real producer gate without transport, encryption or keys."""
        campaign=self.campaign(mode);plan=self.plan(mode,self.admission(mode));runtime=self.runtime(mode)
        self.write(self.task/'runtime.json',runtime)
        self.write(self.task/'capture/acquisition-identity.json',{'protocol':'salah-hosted-native-acquisition/1','runtime':runtime})
        roots={k:Path(self.tmp.name)/k for k in ('research','baseline','historical')}
        for root in roots.values():root.mkdir(exist_ok=True)
        original=P.load
        def load(path):return copy.deepcopy(campaign) if Path(path)==HERE/'campaign.json' else original(path)
        # Runner admission is an explicit source-control prerequisite here;
        # dedicated acquisition controls test its real refusal boundary.
        with mock.patch.object(P,'load',side_effect=load), \
             mock.patch.object(P.runner_environment,'current',return_value={'scope':'SOURCE_CONTROL_ONLY'}):
            def completed(phase,code):
                identity=P.producer_identity(phase,self.task,roots)
                value={'protocol':P.PRODUCER_PROTOCOL,'identity':identity,'phase':phase}
                self.write(self.task/'capture/producer-control'/(phase+'-started.json'),value)
                self.write(self.task/'capture/producer-control'/(phase+'-completed.json'),
                    {**value,'returned':True,'interrupted':False,'process':{'returncode':code,'elapsedSeconds':1.0}})
            completed('acquisition',0);completed('observation',0)
            process={'returncode':0,'timedOut':False,'elapsedSeconds':1.0}
            row={**O.namespace_status(plan['lanes'][0],process,self.inner(mode)),'workOrder':'R003F'}
            observation={'protocol':'salah-hosted-native-observation/1','engine':runtime['engine'],'workOrders':['R003F'],
                'r003fHarness':mode,'preparation':process,'status':'OBSERVED','lanes':[row]}
            def save():
                self.write(self.task/'capture/lanes.json',plan);self.write(self.task/'capture/observation.json',observation)
            save();yield SimpleNamespace(campaign=campaign,plan=plan,observation=observation,row=row,roots=roots,save=save,completed=completed)

    def test_selection_is_exactly_one_engine_one_dpr_and_one_work_order(self):
        for mode, engine in zip(MODES, ENGINES):
            self.assertEqual(D.controls(mode, ['R003F'], engine, 1)['mode'], mode)
            for orders, wrong_engine, dpr, retained in [
                    (['R003F','R0035'], engine, 1, False), (['R003F'], 'chromium', 1, False),
                    (['R003F'], engine, 2, False), (['R003F'], engine, True, False),
                    (['R003F'], engine, 1, True)]:
                with self.subTest(mode=mode,orders=orders,engine=wrong_engine,dpr=dpr), self.assertRaises(ValueError):
                    D.controls(mode, orders, wrong_engine, dpr, retained)
        self.assertIsNone(D.controls('published', ['R003F'], 'chromium', 1))

    def test_canonical_routes_bind_distinct_output_argv_status_and_scope(self):
        ff, wk = (self.lane(mode) for mode in MODES)
        self.assertEqual(ff['output'], str(self.task/'capture/firefox-policy'))
        self.assertEqual(ff['argv'][1], str(HERE/'firefox_policy_probe.cjs'))
        self.assertEqual(ff['argv'][2:], ['--task',str(self.task),'--out',ff['output'],
            '--isolation',str(self.task/'capture/isolation'/ff['id']/'receipt.json'),
            '--pins-sha256',D.FIREFOX_PINS])
        self.assertEqual(wk['argv'][1], str(self.task/'work/r003f-preconnect/tools/qa/r003f_owner_baseline.cjs'))
        self.assertEqual(wk['argv'][-2:], ['--materialization-sha256',D.WEBKIT_MATERIALIZATION])
        self.assertNotEqual(ff['result']['kind'], wk['result']['kind'])
        self.assertNotIn('evidenceRetention', ff)
        self.assertNotIn('evidenceRetention', wk)

    def test_incomplete_preparation_never_falls_back_to_original_b0(self):
        for mode in MODES:
            lane=D.make_lane(mode, None, self.task, self.runtime(mode))
            self.assertEqual(lane['argv'], [])
            self.assertEqual(lane['preparation']['status'], 'INCOMPLETE')
            self.assertNotEqual(lane['result']['kind'], 'r003f-b0')

    def test_budget_components_are_explicit_and_fit_real_selected_envelopes(self):
        expected={'firefox-policy':(330,90,615,2085,2640,45),
                  'preconnect-input':(960,120,1275,2745,2880,49)}
        for mode,values in expected.items():
            b=D.budget(mode)
            self.assertEqual(tuple(b[x] for x in ('entrySeconds','finalSeconds','namespaceSeconds',
                'accountedSeconds','coordinatorSeconds','workflowObservationMinutes')),values)
            self.assertEqual(b['namespaceSeconds'],b['entrySeconds']+b['currentSeconds']+b['finalSeconds']+75)
            self.assertEqual(b['accountedSeconds'],1350+120+b['namespaceSeconds'])
            self.assertGreater(b['coordinatorSeconds'],b['accountedSeconds'])
            self.assertEqual(b['workflowObservationMinutes']*60-b['coordinatorSeconds'],60)
        self.assertEqual(D.budget('preconnect-input')['originalCaptureSeconds'],900)
        self.assertEqual(D.budget('firefox-policy')['originalChildSeconds'],270)

    def test_campaign_selector_rejects_cross_engine_and_supplemental_composition(self):
        for mode, engine in zip(MODES, ENGINES):
            c={'schemaVersion':1,'engine':engine,'r003fDpr':1,'workOrders':['R003F'],
               'r003fHarness':mode,'evidenceRetention':False,
               'r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'}}
            path=self.task/'campaign.json';path.write_text(json.dumps(c))
            self.assertEqual(O.read_campaign(path),c)
            self.assertEqual(O.campaign_budget(c),{k:D.budget(mode)[k] for k in
                ('coordinatorSeconds','workflowObservationMinutes')})
            for change in [{'engine':'chromium'},{'r003fDpr':2},{'evidenceRetention':True},
                           {'r003fMatrix':{'id':'foreign','variant':'B0'}},{'r0035Costs':True}]:
                path.write_text(json.dumps({**c,**change}))
                with self.assertRaises(ValueError):O.read_campaign(path)

    def test_runtime_is_bound_before_optional_source_execution(self):
        for mode in MODES:
            lane=self.lane(mode);runtime=self.runtime(mode)
            O.admit_lane_runtime(lane,runtime)
            for mutate in [lambda x:x['argv'].__setitem__(0,'/synthetic/untrusted-node'),
                           lambda x:x['env'].update(NODE_PATH='/synthetic/modules'),
                           lambda x:x['diagnosticRuntime'].update(python='/synthetic/python')]:
                changed=copy.deepcopy(lane);mutate(changed)
                with mock.patch.object(D,'readmit',side_effect=AssertionError('must not run')), self.assertRaises(ValueError):
                    O.admit_lane_runtime(changed,runtime)

    def test_source_manifest_and_original_guard_bytes_are_exact(self):
        identity=D.verify_sources()
        self.assertEqual(identity['firefoxManifest']['sha256'],D.FIREFOX_PINS)
        self.assertEqual(identity['webkitMaterialization'],D.WEBKIT_MATERIALIZATION)
        self.assertEqual(hashlib.sha256((HERE/'firefox-policy-pins.json').read_bytes()).hexdigest(),D.FIREFOX_PINS)
        self.assertEqual(identity['files']['r003f_preconnect_input.cjs'],
                         '25ad6457e98f1090bb7f234d6f4cdeed451a6b72b5c9a5a9c2d820e57ada50ca')

    def test_native_preparation_paths_and_executables_are_not_receipt_selected(self):
        mode=MODES[0];runtime=self.runtime(mode);paths=D.paths(self.task,mode)
        paths['preparation'].mkdir()
        for path in (paths['common'],paths['commonProcess'],paths['commonContext'],paths['preparationEntry'],paths['preparationProcess']):
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
        with mock.patch.object(D,'node_source',side_effect=AssertionError('must not execute')), \
             self.assertRaises(ValueError):
            D.admit(mode,self.task,runtime,native=True)

    def test_native_readmission_does_not_accept_source_only_preparation(self):
        p,prepared,*_=self.custody('firefox-policy')
        with mock.patch.object(D.common_support,'validate_prepared',return_value=prepared), \
             mock.patch.object(D,'node_source',side_effect=AssertionError('source-only promotion must stop before Node')):
            with self.assertRaisesRegex(ValueError,'not isolated'):
                D.admit('firefox-policy',self.task,self.runtime('firefox-policy'),native=True)
        with mock.patch.object(D.common_support,'validate_prepared',return_value=prepared):
            self.assertEqual(D.common_custody(p,False)[0],prepared)

    def test_new_namespace_success_is_bound_to_kind_and_scope(self):
        for mode in MODES:
            lane=self.lane(mode);inner=self.inner(mode)
            result=O.namespace_status(lane,{'returncode':0,'timedOut':False},inner)
            self.assertEqual(result['status'],inner['status'])
            for change in [{'status':'PASS'},{'status':D.ROUTES[MODES[1-MODES.index(mode)]]['status']},
                           {'nativeQualification':'ORIGINAL_COMPLETE_EIGHT_REPLAY_ONLY'},
                           {'nativeProductAcceptance':'PASS'},{'humanAcceptance':'ACCEPTED'},
                           {'returncode':False},{'timedOut':0},{'diagnosticMode':'foreign'}]:
                result=O.namespace_status(lane,{'returncode':0,'timedOut':False},{**inner,**change})
                self.assertEqual(result['status'],'ISOLATION_UNCONFIRMED')

    def test_foreign_diagnostic_success_never_qualifies_original_b0(self):
        original={'id':'original','result':{'kind':'r003f-b0'}}
        for mode in MODES:
            inner={**self.inner(mode),'id':'original'}
            self.assertEqual(O.namespace_status(original,{'returncode':0,'timedOut':False},inner)['status'],
                             'ISOLATION_UNCONFIRMED')

    def test_outer_namespace_failure_overrides_both_diagnostic_successes(self):
        for mode in MODES:
            lane=self.lane(mode);inner=self.inner(mode)
            for process in [{'returncode':1,'timedOut':False},{'returncode':0,'timedOut':True},
                            {'returncode':False,'timedOut':False},{'returncode':0,'timedOut':0}]:
                self.assertEqual(O.namespace_status(lane,process,inner)['status'],'ISOLATION_UNCONFIRMED')
            self.assertEqual(O.namespace_status(lane,{'returncode':86,'timedOut':False},inner)['status'],'ISOLATION_FAIL')

    def test_missing_terminal_bytes_and_actual_nonzero_stay_incomplete(self):
        for mode in MODES:
            lane=self.lane(mode)
            with mock.patch.object(D,'final_check',side_effect=AssertionError('no final replay for absent report')):
                self.assertEqual(O.classify_lane(lane,0)['status'],'INCOMPLETE')
                self.assertEqual(O.classify_lane(lane,2)['status'],'INCOMPLETE')
                self.assertEqual(O.classify_lane(lane,False)['status'],'INCOMPLETE')

    def test_original_isolation_and_andon_precedence_remain_strict(self):
        for mode in MODES:
            lane=self.lane(mode)
            self.assertEqual(O.classify_lane(lane,86)['status'],'ISOLATION_FAIL')
        lane=self.lane('preconnect-input')
        self.assertEqual(O.classify_lane(lane,3)['status'],'ISOLATION_FAIL')
        self.assertEqual(O.classify_lane(lane,4)['status'],'ANDON')

    def test_shared_boundary_remains_chromium_before_any_diagnostic_firefox(self):
        source=(HERE/'browser-control.cjs').read_text()
        self.assertIn('require(playwright).chromium.launch({headless:true, chromiumSandbox:true})',source)
        self.assertNotIn('.firefox.launch(',source)
        calls=[];args=SimpleNamespace(task=self.task,outer_netns='net:[100]')
        def run(argv,cwd,env,stdout,stderr,timeout):
            calls.append(argv)
            Path(argv[-1]).write_text(json.dumps({'passed':True}))
            return {'returncode':0,'timedOut':False}
        with mock.patch.object(O,'kernel_snapshot',return_value={'netns':'net:[101]'}),mock.patch.object(O,'validate_snapshot'), \
             mock.patch.object(O,'run_bounded',side_effect=run):
            self.assertIsNotNone(O.controls(args,self.runtime('firefox-policy'),'preparation'))
        self.assertEqual(calls,[[self.runtime('firefox-policy')['node'],str(HERE/'browser-control.cjs'),
            self.runtime('firefox-policy')['playwright'],str(self.task/'capture/isolation/preparation/browser.json')]])
        self.assertNotIn('preparePolicy(',D.NODE_SOURCE)
        self.assertNotIn('.launch(',D.NODE_SOURCE)

    def test_workflow_sparse_source_closure_includes_both_original_firefox_guards(self):
        workflow=(ROOT/'.github/workflows/research-native-pilot.yml').read_text()
        for name in ('r0033_isolation.cjs','v1_net_guard.cjs'):
            self.assertIn('/tools/qa/'+name,workflow)
        campaign_bytes=(HERE/'campaign.json').read_bytes()
        self.assertEqual(hashlib.sha256(campaign_bytes).hexdigest(),
                         '496a769675733d9e8e26d9a211c0a53028557b8b1ce852e85fd8bf4ecfdbda3c')
        campaign=json.loads(campaign_bytes)
        self.assertEqual(campaign['workOrders'],['R002F'])
        self.assertEqual(campaign['r002fRoute'],'tabhide')
        self.assertEqual(campaign['r002f'],{'enabled':True,'dpr':1,'rounds':1,'section':'all'})
        self.assertEqual(campaign['engine'],'chromium')
        self.assertNotIn(campaign.get('r003fHarness'),D.ROUTES)

    def test_real_planner_dispatches_only_the_selected_diagnostic(self):
        for mode in MODES:
            plan=self.plan(mode,self.admission(mode))
            self.assertEqual(plan['lanes'],[self.lane(mode)])
            incomplete=self.plan(mode)
            self.assertEqual(len(incomplete['lanes']),1);self.assertEqual(incomplete['lanes'][0]['argv'],[])

    def test_complete_current_plan_is_readmitted_with_bound_actual_runtime(self):
        for mode in MODES:
            admission=self.admission(mode);plan=self.plan(mode,admission);calls=[]
            def prefix(*args):calls.append('prefix');return {'prepared':self.prepared()}
            def readmit(*args):calls.append('readmit');return {'returncode':0,'timedOut':False,'stdout':json.dumps(admission)}
            with mock.patch.object(D,'custody_prefix',side_effect=prefix),mock.patch.object(D,'readmit',side_effect=readmit):
                result=O.admit_plan(plan,self.arguments(mode),self.runtime(mode))
            self.assertEqual(calls,['prefix','readmit']);self.assertEqual(result[0]['preparation'],admission)
            self.assertEqual(result[0]['preExecutionCurrentness']['returncode'],0)

    def test_copied_plan_change_cannot_authorize_any_optional_verifier(self):
        mode='firefox-policy';plan=self.plan(mode,self.admission(mode))
        for change in [lambda x:x['lanes'][0]['argv'].__setitem__(0,'/synthetic/foreign-node'),
                       lambda x:x['lanes'][0].update(timeoutSeconds=5),
                       lambda x:x['lanes'][0]['diagnosticObservation']['budget'].update(finalSeconds=1),
                       lambda x:x['lanes'][0]['result'].update(kind='r003f-b0'),
                       lambda x:x['preparedReceipt'].update(sha256='0'*64)]:
            altered=copy.deepcopy(plan);change(altered)
            with mock.patch.object(D,'custody_prefix',side_effect=AssertionError('must not run')), \
                 mock.patch.object(D,'readmit',side_effect=AssertionError('must not run')),self.assertRaises(ValueError):
                O.admit_plan(altered,self.arguments(mode),self.runtime(mode))

    def test_entire_current_admission_is_compared_not_only_digest_or_status(self):
        for mode in MODES:
            original=self.admission(mode);changed=copy.deepcopy(original);changed['source']['synthetic']='stale copied source'
            plan=self.plan(mode,changed)
            with mock.patch.object(D,'custody_prefix',return_value={'prepared':self.prepared()}), \
                 mock.patch.object(D,'readmit',return_value={'returncode':0,'timedOut':False,'stdout':json.dumps(original)}), \
                 self.assertRaisesRegex(ValueError,'complete preparation'):
                O.admit_plan(plan,self.arguments(mode),self.runtime(mode))

    def test_parent_child_and_common_executable_custody_precedes_verifier(self):
        mode='firefox-policy';p,prepared,context,child,entry=self.custody(mode)
        cases=[('preparationEntry',entry,lambda x:x['argv'].__setitem__(0,'/foreign/python')),
               ('preparationProcess',child,lambda x:x['argv'].__setitem__(0,'/foreign/node')),
               ('commonContext',context,lambda x:x['argv'].__setitem__(0,'/foreign/python')),
               ('preparationEntry',entry,lambda x:x.update(process='/foreign/process.json')),
               ('preparationProcess',child,lambda x:x.update(timeoutSeconds=True)),
               ('preparationEntry',entry,lambda x:x.update(sourceSha256='0'*64)),
               ('preparationProcess',child,lambda x:x['streams']['stdout'].update(bytes=1))]
        for key,original,change in cases:
            altered=copy.deepcopy(original);change(altered);self.write(p[key],altered)
            with mock.patch.object(D,'node_source',side_effect=AssertionError('must not run')),self.assertRaises(ValueError):
                D.admit(mode,self.task,self.runtime(mode),native=True)
            self.write(p[key],original)

    def test_source_only_claim_cannot_be_relabelled_hosted_without_original_boundary(self):
        mode='firefox-policy';p,prepared,context,*_=self.custody(mode)
        context.update(protocol='hosted-common-preparation-execution/1',nativeIsolationClaim=True,
                       isolation={'path':str(p['isolation']),'sha256':'0'*64})
        self.write(p['commonContext'],context)
        with mock.patch.object(D.common_support,'validate_prepared',return_value=prepared),self.assertRaises(ValueError):
            D.common_custody(p,True)

    def test_actual_subprocess_retains_exact_binary_streams_and_nonzero(self):
        result=D.bounded([sys.executable,'-c',"import os;os.write(1,b'\\x00\\xffout');os.write(2,b'\\x80err');raise SystemExit(7)"],{},5,raw=True)
        self.assertEqual(result['returncode'],7);self.assertIs(result['timedOut'],False)
        self.assertEqual(result['stdoutBytes'],b'\x00\xffout');self.assertEqual(result['stderrBytes'],b'\x80err')
        with self.assertRaises(ValueError):D.actual_success(result,'controlled nonzero')

    def test_actual_timeout_terminates_the_subprocess_group(self):
        script="import subprocess,sys,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);print(p.pid,flush=True);time.sleep(30)"
        result=D.bounded([sys.executable,'-c',script],{},.3)
        self.assertIs(result['timedOut'],True);self.assertLess(result['returncode'],0)
        descendant=int(result['stdout'].strip());status=Path('/proc')/str(descendant)/'stat'
        if status.exists():self.assertEqual(status.read_text().split(') ',1)[1].split()[0],'Z','no live descendant may remain')

    def test_failed_optional_preparation_retains_actual_bytes_without_fabricated_source(self):
        mode='firefox-policy';prepared=self.prepared();runtime=self.runtime(mode);p=D.paths(self.task,mode)
        self.write(p['commonContext'],{'argv':[runtime['python']]})
        argv=[sys.executable,'-c',"import os;os.write(1,b'\\x00\\xffout');os.write(2,b'\\x80err');raise SystemExit(7)"]
        with mock.patch.object(D,'runtime_binding',return_value={'synthetic':'runtime'}), \
             mock.patch.object(D,'common_custody',return_value=(prepared,{'synthetic':'common'})), \
             mock.patch.object(D,'preparation_child',return_value=argv):
            result=D.prepare(mode,self.task,runtime)
        self.assertEqual(result['status'],'INCOMPLETE');self.assertEqual(result['returncode'],7)
        self.assertNotIn('source',result);self.assertEqual((p['preparation']/'child.stdout').read_bytes(),b'\x00\xffout')
        self.assertEqual((p['preparation']/'child.stderr').read_bytes(),b'\x80err')
        self.assertEqual(D.load(p['preparationProcess']),result)

    def test_actual_entry_record_binds_raw_streams_and_is_exclusive(self):
        lane=self.lane('firefox-policy')
        for name in ('stdout','stderr'):self.write(lane[name],b'\x00\xff'+name.encode())
        actual={'returncode':7,'timedOut':False,'elapsedSeconds':.2}
        record=D.record_entry(lane,actual)
        self.assertEqual(record['returncode'],7);self.assertEqual(record['streams']['stdout'],D.artifact(lane['stdout']))
        with self.assertRaises(FileExistsError):D.record_entry(lane,actual)

    def test_final_wrapper_rejects_changed_entry_before_any_node_replay(self):
        for mode in MODES:
            lane=self.lane(mode)
            for name in ('stdout','stderr'):self.write(lane[name],b'actual retained fixture bytes')
            D.record_entry(lane,{'returncode':0,'timedOut':False})
            record=D.load(lane['result']['entryProcessPath'])
            record['argv'][0]='/synthetic/foreign-node';self.write(lane['result']['entryProcessPath'],record)
            with mock.patch.object(D,'admit',return_value=self.admission(mode)), \
                 mock.patch.object(D,'bounded',side_effect=AssertionError('no Node replay')),self.assertRaises(ValueError):
                D.final_intake({'lane':lane,'returncode':0,'timedOut':False})

    def test_final_verifier_timeout_and_foreign_scope_never_promote_success(self):
        for mode in MODES:
            lane=self.lane(mode);good={'protocol':D.FINAL,'status':D.ROUTES[mode]['status'],**D.scope_fields(mode)}
            for change in [{'returncode':1},{'returncode':False},{'timedOut':True},
                           {'stdout':json.dumps({**good,'nativeQualification':'ORIGINAL_B0'})}]:
                check={'returncode':0,'timedOut':False,'stdout':json.dumps(good),**change}
                with mock.patch.object(D,'final_check',return_value=check):
                    self.assertEqual(D.classify(lane,{},0,False)['status'],'INCOMPLETE')
            with mock.patch.object(D,'final_check',return_value={'returncode':0,'timedOut':False,'stdout':json.dumps(good)}):
                self.assertEqual(D.classify(lane,{},0,False)['status'],good['status'])

    def test_malformed_nested_terminal_records_stay_incomplete(self):
        for mode in MODES:
            lane=self.lane(mode)
            with mock.patch.object(D,'final_check',return_value={'returncode':2,'timedOut':False,'stdout':''}):
                for body in ({'isolation':None},{'network':[]},{'isolation':'unconfirmed'}):
                    self.assertEqual(D.classify(lane,body,0,False)['status'],'INCOMPLETE')

    def test_optional_preparation_occurs_after_original_boundary_and_common_success(self):
        mode='firefox-policy';args=self.arguments(mode);args.phase='prepare';args.lane=None;args.outer_netns='net:[100]'
        calls=[];receipt=self.task/'capture/isolation/preparation/receipt.json';self.write(receipt,{'synthetic':'boundary'})
        def bounded(argv,cwd,env,stdout,stderr,seconds):
            calls.append(('common' if argv[1]==str(HERE/'prepare.py') else 'planner',seconds))
            if argv[1]==str(HERE/'lanes.py'):
                self.write(self.task/'capture/lanes.json',{'synthetic':'planner'})
            return {'returncode':0,'timedOut':False}
        with mock.patch.object(O,'controls',side_effect=lambda *a:calls.append(('chromium-boundary',None)) or str(receipt)), \
             mock.patch.object(O,'run_bounded',side_effect=bounded), \
             mock.patch.object(O,'prepare_diagnostic',side_effect=lambda *a:calls.append(('diagnostic-source',180))), \
             mock.patch.dict(os.environ,{},clear=False):
            self.assertEqual(O.inside(args,self.runtime(mode)),0)
        self.assertEqual(calls,[('chromium-boundary',None),('common',900),('diagnostic-source',180),('planner',120)])

    def test_outer_uses_selected_namespace_ceiling_and_remaining_time(self):
        for mode in MODES:
            for remaining in (2000,100):
                args=self.arguments(mode);lane=self.lane(mode);calls=[];self.write(self.task/'capture/lanes.json',{})
                self.write(self.task/'capture/lane-status'/(lane['id']+'.json'),self.inner(mode))
                def run(argv,cwd,env,stdout,stderr,seconds):
                    calls.append(seconds);return {'returncode':0,'timedOut':False,'elapsedSeconds':1}
                with mock.patch.object(O,'isolated_command',return_value=['synthetic-no-namespace']), \
                     mock.patch.object(O,'admit_plan',return_value=[lane]),mock.patch.object(O,'run_bounded',side_effect=run), \
                     mock.patch.object(O.time,'monotonic',side_effect=[0,D.budget(mode)['coordinatorSeconds']-remaining]):
                    self.assertEqual(O.outside(args,self.runtime(mode)),0)
                self.assertEqual(calls,[1350,min(D.budget(mode)['namespaceSeconds'],remaining)])

    def test_exhausted_outer_budget_never_starts_a_diagnostic_namespace(self):
        mode='preconnect-input';lane=self.lane(mode);self.write(self.task/'capture/lanes.json',{})
        with mock.patch.object(O,'isolated_command',return_value=['synthetic-no-namespace']), \
             mock.patch.object(O,'admit_plan',return_value=[lane]), \
             mock.patch.object(O,'run_bounded',return_value={'returncode':0,'timedOut':False,'elapsedSeconds':1}) as run, \
             mock.patch.object(O.time,'monotonic',side_effect=[0,D.budget(mode)['coordinatorSeconds']-75]):
            self.assertEqual(O.outside(self.arguments(mode),self.runtime(mode)),2)
        self.assertEqual(run.call_count,1);body=D.load(self.task/'capture/observation.json')
        self.assertEqual(body['lanes'][0]['status'],'NOT_RUN');self.assertNotIn('namespaceProcess',body['lanes'][0])

    def test_actual_producer_gate_accepts_only_exact_diagnostic_success_scope(self):
        for mode in MODES:
            with self.producer(mode) as f:
                self.assertEqual(P.admit_producers(self.task,f.roots),'COMPLETED_OBSERVATION')
                for mutation in [lambda x:x.row.update(status='PASS'),
                                 lambda x:x.row.update(nativeProductAcceptance='PASS'),
                                 lambda x:x.row['innerStatus'].update(humanAcceptance='ACCEPTED'),
                                 lambda x:x.row['namespaceProcess'].update(returncode=False),
                                 lambda x:x.row['namespaceProcess'].update(timedOut=0),
                                 lambda x:x.plan.update(r003fHarness='corrected-b0'),
                                 lambda x:x.plan['lanes'][0].update(timeoutSeconds=1),
                                 lambda x:x.plan['lanes'][0]['argv'].__setitem__(1,'/foreign/b0.cjs')]:
                    plan=copy.deepcopy(f.plan);observation=copy.deepcopy(f.observation);mutation(f);f.save()
                    with self.assertRaises(P.Rejected):P.admit_producers(self.task,f.roots)
                    f.plan.clear();f.plan.update(plan);f.observation.clear();f.observation.update(observation);f.row=f.observation['lanes'][0];f.save()

    def test_foreign_diagnostic_status_cannot_be_relabelled_as_other_engine_or_b0(self):
        for mode in MODES:
            with self.producer(mode) as f:
                other=MODES[1-MODES.index(mode)];f.row['status']=D.ROUTES[other]['status'];f.save()
                with self.assertRaises(P.Rejected):P.admit_producers(self.task,f.roots)
                f.campaign.update(r003fHarness='published');f.completed('observation',0)
                f.plan.update(r003fHarness='published');f.observation.update(r003fHarness='published')
                f.plan['lanes'][0]['result']['kind']='r003f-b0';f.save()
                with self.assertRaises(P.Rejected):P.admit_producers(self.task,f.roots)

    def test_known_completed_diagnostic_failure_and_not_run_remain_retainable(self):
        for mode in MODES:
            with self.producer(mode) as f:
                f.completed('observation',2);f.observation['status']='OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'
                f.row.update(status='INCOMPLETE',innerStatus=None);f.save()
                self.assertEqual(P.admit_producers(self.task,f.roots),'COMPLETED_OBSERVATION')
                f.row.clear();f.row.update(id=D.ROUTES[mode]['id'],workOrder='R003F',status='NOT_RUN',reason='explicit fixture exhaustion');f.save()
                self.assertEqual(P.admit_producers(self.task,f.roots),'COMPLETED_OBSERVATION')

    def test_new_producer_identity_binds_full_diagnostic_source_and_rejects_old_receipts(self):
        for mode in MODES:
            with self.producer(mode) as f:
                identity=P.producer_identity('observation',self.task,f.roots)
                self.assertTrue(set(D.producer_source_files())<=set(identity['sources']))
                self.assertIn('r003f_diagnostic_replay.cjs',identity['sources']);self.assertIn('../r0033_isolation.cjs',identity['sources'])
                file=self.task/'capture/producer-control/observation-completed.json';body=D.load(file)
                body['identity']['sources'].pop('r003f_diagnostic_replay.cjs');self.write(file,body)
                with self.assertRaises(P.Rejected):P.admit_producers(self.task,f.roots)

    def test_actual_firefox_source_check_never_imports_playwright_or_installs_policy(self):
        prepared,runtime,executable=self.source_fixture('firefox-policy')
        result=D.node_source('firefox-policy',self.task,runtime,prepared)
        self.assertEqual(result['acquired']['executable'],str(executable))
        self.assertIsNone(result['materialization']);self.assertFalse((executable.parent/'distribution/policies.json').exists())

    def test_actual_webkit_source_check_binds_complete_derived_closure_and_original_document(self):
        prepared,runtime,executable=self.source_fixture('preconnect-input')
        result=D.node_source('preconnect-input',self.task,runtime,prepared)
        self.assertEqual(result['acquired']['executable'],str(executable))
        self.assertEqual(result['materialization']['materializationSha256'],D.WEBKIT_MATERIALIZATION)
        self.assertEqual(len(result['materialization']['outputFiles']),8)
        self.assertEqual(result['harness']['protocol'],'R003F/preconnect-input-harness/1')

    def test_actual_source_check_rejects_current_acquired_binary_and_lock_drift(self):
        prepared,runtime,executable=self.source_fixture('firefox-policy')
        original=executable.read_bytes();executable.write_bytes(original+b'drift')
        with self.assertRaises(ValueError):D.node_source('firefox-policy',self.task,runtime,prepared)
        executable.write_bytes(original);self.write(self.task/'node/package-lock.json',b'{}')
        with self.assertRaises(ValueError):D.node_source('firefox-policy',self.task,runtime,prepared)

    def test_actual_source_check_rejects_webkit_derived_population_and_document_drift(self):
        prepared,runtime,_=self.source_fixture('preconnect-input');p=D.paths(self.task,'preconnect-input')
        extra=p['source']/'undeclared.txt';extra.write_text('drift')
        with self.assertRaises(ValueError):D.node_source('preconnect-input',self.task,runtime,prepared)
        extra.unlink();index=Path(prepared['trees']['r003f']['root'])/'index.html';index.write_bytes(index.read_bytes()+b'drift')
        with self.assertRaises(ValueError):D.node_source('preconnect-input',self.task,runtime,prepared)

    def test_full_readmission_compares_current_package_files_to_actual_preparation(self):
        mode='firefox-policy';prepared,runtime,_=self.source_fixture(mode)
        source=D.node_source(mode,self.task,runtime,prepared);common={'synthetic':'complete source proof is a separate test'}
        prefix={'paths':D.paths(self.task,mode),'prepared':prepared,'sources':D.verify_sources(),'binding':D.runtime_binding(self.task,runtime,mode),
            'child':{'common':common,'source':source},'streams':{},'outerStreams':{},'commonStreams':{}}
        prefix['child'].update(sources=prefix['sources'],binding=prefix['binding'])
        module=Path(runtime['playwright'])/'index.cjs';module.write_bytes(module.read_bytes()+b'\n// current package byte drift\n')
        with mock.patch.object(D,'custody_prefix',return_value=prefix), \
             mock.patch.object(D,'common_custody',return_value=(prepared,common)),self.assertRaisesRegex(ValueError,'source/acquisition differs'):
            D.admit(mode,self.task,runtime,native=False)


if __name__=='__main__':
    unittest.main()
