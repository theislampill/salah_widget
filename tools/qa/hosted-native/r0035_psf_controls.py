"""Source-only adversarial controls for the explicit paired PSF caller."""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace,ModuleType
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import observe
import lanes


class Controls(unittest.TestCase):
    def module(self):
        return importlib.import_module('r0035_psf')

    def campaign(self):
        value = json.loads((HERE/'campaign.json').read_text())
        value.update(engine='chromium', workOrders=['R0035'], r0035Psf=True,
                     r0035={'guard':'off','scope':'all','mode':'timing'},
                     r0035Stages=False, r0035Costs=False, evidenceRetention=False,
                     r003fHarness='published', r0040Mode='options')
        value.pop('r003fMatrix', None); value.pop('r002fRoute', None)
        value['r002f']['enabled'] = False
        return value

    def test_opt_in_budget_is_complete_two_lane_population(self):
        self.assertEqual(observe.campaign_budget(self.campaign()),
                         {'coordinatorSeconds':3540,'workflowObservationMinutes':60})

    def test_unreviewed_supplemental_population_is_refused(self):
        for field, value in [('r0035Stages',True),('r0035Costs',True),('evidenceRetention',True),
                             ('engine','firefox'),('workOrders',['R0035','R0040'])]:
            with self.subTest(field=field):
                c=self.campaign();c[field]=value
                with self.assertRaises(ValueError):observe.campaign_budget(c)

    def test_boolean_selector_has_no_truthy_alias(self):
        for value in (1,0,'true',None,{},[]):
            c=self.campaign();c['r0035Psf']=value
            with self.subTest(value=value),self.assertRaises(ValueError):observe.campaign_budget(c)

    def test_exact_flags_no_tuning_or_scope_switch(self):
        for name,value in [('guard','default'),('scope','preview-members'),('mode','capture'),('mode','both')]:
            c=self.campaign();c['r0035'][name]=value
            with self.subTest(name=name,value=value),self.assertRaises(ValueError):observe.campaign_budget(c)

    def test_strict_json_rejects_boolean_integer_alias(self):
        p=self.module();self.assertFalse(p.same({'ordinal':True},{'ordinal':1}))
        with self.assertRaises(ValueError):p.same(float('nan'),float('nan'))

    def test_actual_process_cannot_be_inferred_from_receipt(self):
        p=self.module()
        good={'returncode':0,'timedOut':False,'elapsedSeconds':1.0}
        p.success(good,'test',30)
        for fields in ({'returncode':False},{'returncode':None},{'returncode':1},{'timedOut':0},
                       {'timedOut':True},{'elapsedSeconds':True},{'elapsedSeconds':float('inf')},
                       {'elapsedSeconds':31},{'error':'interrupted'},{'retentionError':'lost'}):
            with self.subTest(fields=fields),self.assertRaises(ValueError):p.success({**good,**fields},'test',30)

    def test_population_delta_requires_only_exact_two_files(self):
        p=self.module();before={'a':{'sha256':'a'},p.STELLAR:{'sha256':'b'}}
        after={**before,p.STELLAR:{'sha256':'c'},p.CANDIDATE:{'sha256':'d'}}
        p.check_delta(before,after)
        for changed in ({**after,'extra':{}},{k:v for k,v in after.items() if k!='a'},
                        {**after,'a':{'sha256':'changed'}},{**after,p.STELLAR:before[p.STELLAR]}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):p.check_delta(before,changed)

    def test_inventory_rejects_symlink_and_records_complete_bytes(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'a').write_bytes(b'a');(root/'empty').mkdir()
            self.assertEqual(set(p.inventory(root)),{'a'})
            (root/'link').symlink_to(root/'a')
            with self.assertRaises(ValueError):p.inventory(root)

    def test_derived_plan_is_distinct_and_preserves_original_flags(self):
        p=self.module()
        source={'kind':'independent-reconstruction','arms':{
            'main':{'root':'/main','commit':'b','flags':''},
            'unmodified':{'root':'/reference','commit':'r','flags':'full','producerProbe':{'path':'stars.status','equals':'active'}},
            'mitigated':{'root':'/reference','commit':'r','flags':'changed','producerProbe':{'path':'stars.status','equals':'active'}}}}
        derived=p.derived_plan(source,Path('/candidate'),{'path':'/identity','sha256':'x','bytes':1})
        self.assertEqual(derived['kind'],p.KIND);self.assertEqual(source['kind'],'independent-reconstruction')
        self.assertEqual(derived['arms']['main'],source['arms']['main'])
        for label in ('unmodified','mitigated'):
            self.assertEqual(derived['arms'][label],{**source['arms'][label],'root':'/candidate'})

    def test_explicit_private_adapter_keeps_original_scientific_predicates(self):
        entry=importlib.import_module('observe_r0035_psf')
        calls=[]
        class Driver:
            check_plan=lambda self,plan:calls.append(('original',plan))
            verify_reconstructed_flags=lambda self,arms:calls.append(('flags',arms))
            producer_flags=lambda self,*args:calls.append(('producer',args))
            assess=object()
        driver=Driver();original=driver.check_plan;assess=driver.assess
        source={'kind':'independent-reconstruction','arms':{'main':{'flags':''},'unmodified':{'flags':'full'},'mitigated':{'flags':'changed'}}}
        derived={**source,'kind':self.module().KIND}
        adapter=entry.PlanAdapter(driver,source,derived,'derived',lambda:calls.append(('current',None)))
        adapter(derived)
        self.assertIs(driver.assess,assess);self.assertEqual(driver.check_plan,original)
        self.assertEqual([x[0] for x in calls],['current','original','flags','producer','producer','producer'])
        with self.assertRaises(ValueError):adapter({**derived,'extra':True})

    def test_node_entry_uses_actual_reviewed_buffers_and_exact_inverse(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)/'base';candidate=Path(temporary)/'candidate'
            for root in (base,candidate):
                (root/'real-sky/core/src').mkdir(parents=True);(root/'tools/r0035').mkdir(parents=True)
                for name in (p.RENDERER,p.STELLAR):(root/name).write_bytes((ROOT/name).read_bytes())
            command=['node',str(HERE/'r0035_psf_transform.mjs'),'derive',str(base),str(candidate)]
            child=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(child.returncode,0,child.stderr)
            body=json.loads(child.stdout);self.assertEqual(body['protocol'],'r0035-psf-file-transform/1')
            child=subprocess.run([*command[:2],'check',*command[3:]],capture_output=True,text=True,timeout=30)
            self.assertEqual(child.returncode,0,child.stderr);self.assertEqual(json.loads(child.stdout),body)
            (candidate/p.CANDIDATE).write_bytes((candidate/p.CANDIDATE).read_bytes()+b'\n')
            self.assertNotEqual(subprocess.run([*command[:2],'check',*command[3:]],capture_output=True,timeout=30).returncode,0)

    def test_node_entry_cannot_overwrite_preexisting_derivation(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)/'base';base.mkdir();(base/'real-sky/core/src').mkdir(parents=True);(base/'tools/r0035').mkdir(parents=True)
            for name in (p.RENDERER,p.STELLAR):(base/name).write_bytes((ROOT/name).read_bytes())
            command=['node',str(HERE/'r0035_psf_transform.mjs'),'derive',str(base),str(base)]
            self.assertNotEqual(subprocess.run(command,capture_output=True,timeout=30).returncode,0)
            self.assertEqual((base/p.STELLAR).read_bytes(),(ROOT/p.STELLAR).read_bytes())

    def test_node_entry_refuses_output_hardlinks_before_any_write(self):
        p=self.module()
        for output,protected in ((p.STELLAR,p.STELLAR),(p.CANDIDATE,p.RENDERER),
                                 (p.STELLAR,'tools/r0035/other-stellar.mjs')):
            with self.subTest(output=output,protected=protected),tempfile.TemporaryDirectory() as temporary:
                base=Path(temporary)/'base';candidate=Path(temporary)/'candidate'
                for root in (base,candidate):
                    (root/'real-sky/core/src').mkdir(parents=True);(root/'tools/r0035').mkdir(parents=True)
                    for name in (p.RENDERER,p.STELLAR):(root/name).write_bytes((ROOT/name).read_bytes())
                if not (base/protected).exists():(base/protected).write_bytes((ROOT/p.STELLAR).read_bytes())
                target=candidate/output
                if target.exists():target.unlink()
                target.hardlink_to(base/protected)
                self.assertEqual((target.stat().st_dev,target.stat().st_ino),
                                 ((base/protected).stat().st_dev,(base/protected).stat().st_ino))
                before={root:{name:row for name,row in p.inventory(root).items()} for root in (base,candidate)}
                command=['node',str(HERE/'r0035_psf_transform.mjs'),'derive',str(base),str(candidate)]
                child=subprocess.run(command,capture_output=True,text=True,timeout=30)
                self.assertNotEqual(child.returncode,0,child.stdout)
                # Refusal must preserve all protected bytes and the complete
                # existing candidate population, before any new output exists.
                self.assertEqual(p.inventory(base),before[base],child.stderr)
                self.assertEqual(p.inventory(candidate),before[candidate],child.stderr)

    def test_node_entry_allows_read_only_input_hardlink_with_separate_output(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)/'base';candidate=Path(temporary)/'candidate'
            for root in (base,candidate):
                (root/'real-sky/core/src').mkdir(parents=True);(root/'tools/r0035').mkdir(parents=True)
                for name in (p.RENDERER,p.STELLAR):(root/name).write_bytes((ROOT/name).read_bytes())
            (candidate/p.RENDERER).unlink();(candidate/p.RENDERER).hardlink_to(base/p.RENDERER)
            before=p.inventory(base)
            command=['node',str(HERE/'r0035_psf_transform.mjs'),'derive',str(base),str(candidate)]
            child=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(child.returncode,0,child.stderr);self.assertEqual(p.inventory(base),before)
            checked=subprocess.run([*command[:2],'check',*command[3:]],capture_output=True,text=True,timeout=30)
            self.assertEqual(checked.returncode,0,checked.stderr);self.assertEqual(json.loads(checked.stdout),json.loads(child.stdout))

    def synthetic_pair(self):
        p=self.module();identity={'path':'/private/identity','sha256':'a'*64,'bytes':20}
        admission={'status':'PASS','identity':identity};runtime={'python':'/python','node':'/node'}
        rows=[];planned=[]
        for role in p.ROLES:
            identifier='r0035-chromium-psf-'+role
            intake={'protocol':'r0035-psf-original-intake/1','status':'COMPLETE','role':role,'originalStatus':'PASS',
                    'sourceAdmission':copy.deepcopy(admission),'runtime':copy.deepcopy(runtime),'browserVersion':'synthetic-browser',
                    'timingClass':p.TIMING,'summary':{'path':'/'+role+'/summary','sha256':'b'*64,'bytes':10},
                    'driver':{'path':'/'+role+'/driver','sha256':'c'*64,'bytes':10}}
            inner={'id':identifier,'status':p.OBSERVED,'stopAll':False,'returncode':0,'timedOut':False,
                   'originalStatus':'PASS','psfObservation':{'status':'COMPLETE','intake':intake},
                   'timingClass':p.TIMING,'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','humanAcceptance':'OUTSTANDING'}
            rows.append({**inner,'workOrder':'R0035','innerStatus':copy.deepcopy(inner),
                         'namespaceProcess':{'returncode':0,'timedOut':False,'elapsedSeconds':1.0}})
            planned.append({'id':identifier,'workOrder':'R0035','engine':'chromium','psfObservation':{
                'protocol':'r0035-psf-paired-diagnostic/1','role':role,'timingClass':p.TIMING},'preparation':admission,
                'result':{'kind':'r0035-trials'},'evidenceRetention':{'instrumented':True},'stopAllOnExit':[86]})
        plan={'r0035Psf':True,'workOrders':['R0035'],'lanes':planned}
        body={'r0035Psf':True,'lanes':rows};body['psfPair']=p.pair_status(plan,rows)
        return plan,body

    def test_pair_rejects_partial_failed_duplicate_and_mismatched_runtime(self):
        p=self.module();plan,body=self.synthetic_pair();self.assertEqual(body['psfPair']['status'],'OBSERVED')
        changes=[lambda x:x.pop(),lambda x:x[0].update(status='FAIL'),
                 lambda x:x[1].update(id=x[0]['id']),
                 lambda x:x[1]['psfObservation']['intake'].update(browserVersion='other'),
                 lambda x:x[1]['psfObservation']['intake']['runtime'].update(python='/other'),
                 lambda x:x[1]['psfObservation']['intake'].update(originalStatus='FAIL')]
        for change in changes:
            rows=copy.deepcopy(body['lanes']);change(rows)
            with self.subTest(change=change):self.assertEqual(p.pair_status(plan,rows)['status'],'INCOMPLETE')

    def test_pipeline_complete_record_explicitly_accepts_only_admitted_psf_pair(self):
        import capture_pipeline as pipeline
        plan,body=self.synthetic_pair()
        self.assertTrue(pipeline.psf_complete_record(self.campaign(),plan,body))
        body['psfPair']['status']='INCOMPLETE';body['psfPair']['reason']='controlled pair mismatch'
        self.assertFalse(pipeline.psf_complete_record(self.campaign(),plan,body))

    def test_pipeline_cannot_promote_original_failure_or_partial_pair(self):
        import capture_pipeline as pipeline
        for mutation in (lambda b:b['lanes'][0].update(status='FAIL'),
                         lambda b:b['lanes'][0].update(originalStatus='FAIL'),
                         lambda b:b['lanes'][0]['namespaceProcess'].update(timedOut=True),
                         lambda b:b['lanes'][0].update(returncode=False),
                         lambda b:b['psfPair']['members'].pop(),
                         lambda b:b['psfPair'].update(roles=['reference','reference'])):
            plan,body=self.synthetic_pair();mutation(body)
            with self.subTest(mutation=mutation),self.assertRaises(pipeline.Rejected):
                pipeline.psf_complete_record(self.campaign(),plan,body)

    def test_pipeline_refuses_psf_status_without_explicit_campaign(self):
        import capture_pipeline as pipeline
        plan,body=self.synthetic_pair();campaign=self.campaign();campaign.pop('r0035Psf')
        with self.assertRaises(pipeline.Rejected):pipeline.psf_complete_record(campaign,plan,body)

    def test_pipeline_actual_complete_record_path_preserves_failed_pair(self):
        import capture_pipeline as pipeline
        plan,body=self.synthetic_pair();campaign=self.campaign()
        plan.update(protocol='salah-hosted-native-lanes/1',sequential=True)
        body.update(protocol='salah-hosted-native-observation/1',engine='chromium',workOrders=['R0035'],
                    preparation={'returncode':0,'timedOut':False,'elapsedSeconds':1.0},status='OBSERVED')
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);code=0
            def loaded(path):
                if Path(path)==pipeline.HERE/'campaign.json':return campaign
                if Path(path)==task/'capture/observation.json':return body
                if Path(path)==task/'capture/lanes.json':return plan
                raise AssertionError('unplanned read')
            with patch.object(pipeline,'load',side_effect=loaded),patch.object(pipeline,'completed',side_effect=lambda t,r,phase:0 if phase=='acquisition' else code):
                self.assertEqual(pipeline.admit_producers(task,{}),'COMPLETED_OBSERVATION')
                code=2;body['lanes'][0]['status']='FAIL';body['lanes'][0]['originalStatus']='FAIL'
                body['psfPair'].update(status='INCOMPLETE',reason='original failure retained')
                body['status']='OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'
                self.assertEqual(pipeline.admit_producers(task,{}),'COMPLETED_OBSERVATION')
                body['status']='OBSERVED';code=0
                with self.assertRaises(pipeline.Rejected):pipeline.admit_producers(task,{})

    def test_pipeline_all_original_terminal_statuses_keep_their_original_disposition(self):
        import capture_pipeline as pipeline
        campaign={'engine':'chromium','r002f':{'enabled':False},'workOrders':['R003F']}
        plan={'protocol':'salah-hosted-native-lanes/1','sequential':True,'workOrders':['R003F'],
              'lanes':[{'id':'original','workOrder':'R003F','engine':'chromium'}]}
        body={'protocol':'salah-hosted-native-observation/1','engine':'chromium','workOrders':['R003F'],
              'preparation':{'returncode':0,'timedOut':False,'elapsedSeconds':1.0}}
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);code=0
            def loaded(path):
                return campaign if Path(path)==pipeline.HERE/'campaign.json' else plan if Path(path)==task/'capture/lanes.json' else body
            with patch.object(pipeline,'load',side_effect=loaded),patch.object(pipeline,'completed',side_effect=lambda t,r,phase:0 if phase=='acquisition' else code):
                for status in sorted(pipeline.LANE_STATUSES-{'OBSERVED_PSF_DIAGNOSTIC'}):
                    observed=status in pipeline.OBSERVED_LANE_STATUSES;code=0 if observed else 2
                    body['status']='OBSERVED' if observed else status if status in ('ISOLATION_FAIL','ISOLATION_UNCONFIRMED','EXTERNAL_CONTINUATION_VETOED') else 'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'
                    body['lanes']=[{'id':'original','workOrder':'R003F','status':status,'stopAll':False,'innerStatus':None,
                                    'namespaceProcess':{'returncode':0,'timedOut':False,'elapsedSeconds':1.0}}]
                    with self.subTest(status=status):
                        if status in ('OBSERVED_FIREFOX_POLICY','OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC',
                                      pipeline.mechanism.ADMITTED,pipeline.autoattach.ADMITTED,pipeline.bfcache.STATUS):
                            # This original Chromium fixture has no separately selected diagnostic route or custody.
                            with self.assertRaisesRegex(pipeline.Rejected,'^PRODUCER_INCOMPLETE$'):
                                pipeline.admit_producers(task,{})
                        else:self.assertEqual(pipeline.admit_producers(task,{}),'COMPLETED_OBSERVATION')

    def test_namespace_actual_process_precedes_psf_success(self):
        p=self.module();plan,body=self.synthetic_pair();lane=plan['lanes'][0];inner=body['lanes'][0]['innerStatus']
        self.assertEqual(observe.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],p.OBSERVED)
        for actual in ({'returncode':86,'timedOut':False},{'returncode':0,'timedOut':True},
                       {'returncode':False,'timedOut':False},{'returncode':None,'timedOut':False}):
            with self.subTest(actual=actual):
                self.assertNotEqual(observe.namespace_status(lane,actual,inner)['status'],p.OBSERVED)
        altered={**inner,'status':'PASS'}
        self.assertEqual(observe.namespace_status(lane,{'returncode':0,'timedOut':False},altered)['status'],'ISOLATION_UNCONFIRMED')

    def test_actual_child_failure_cannot_be_overruled_by_supplement(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'summary.json'
            body=[{'arm':name,'admitted':True,'qualification':{'verdict':'passed'}} for name in p.ARMS]
            path.write_text(json.dumps(body));lane={'result':{'kind':'r0035-trials','path':str(path)},
                 'psfObservation':{'protocol':'r0035-psf-paired-diagnostic/1','role':'reference'}}
            supplemental={'status':'COMPLETE','intake':{'originalStatus':'PASS'}}
            with patch.object(p,'post_observation',return_value=supplemental):
                self.assertEqual(observe.classify_lane(lane,0,False)['status'],p.OBSERVED)
                for code,timed in ((1,False),(0,True),(False,False),(None,False)):
                    with self.subTest(code=code,timed=timed):self.assertNotEqual(observe.classify_lane(lane,code,timed)['status'],p.OBSERVED)
                body[0]['qualification']['verdict']='failed';path.write_text(json.dumps(body))
                self.assertEqual(observe.classify_lane(lane,0,False)['status'],'FAIL')

    def test_runtime_authority_precedes_optional_receipt_driven_child(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);runtime={'python':sys.executable,'node':'/node','modules':'/modules',
                                         'playwright':'/modules/playwright','pngjs':'/modules/pngjs'}
            (task/'runtime.json').write_text(json.dumps(runtime));plan={'lanes':[{'preparation':{'status':'PASS'},
                'argv':['/unadmitted'], 'evidenceRetention':{'originalArgv':[sys.executable]}}]*2}
            with patch.object(p,'readmit',side_effect=AssertionError('must not launch optional verifier')):
                with self.assertRaisesRegex(ValueError,'executable'):p.admit_plan(plan,task,runtime)
            with self.assertRaises(ValueError):p.runtime_authority(task,{**runtime,'python':'/other'})

    def test_copied_runtime_and_environment_rebinding_precede_current_child(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);runtime={'python':sys.executable,'node':'/node','modules':'/modules',
                                         'playwright':'/modules/playwright','pngjs':'/modules/pngjs'}
            (task/'runtime.json').write_text(json.dumps(runtime))
            original={'preparation':{'status':'PASS','runtime':runtime},'argv':[sys.executable,'entry'],
                      'env':{'NODE_PATH':runtime['modules']},'evidenceRetention':{'originalArgv':[sys.executable,'driver']}}
            for change in (lambda x:x['env'].update(NODE_PATH='/foreign'),
                           lambda x:x['preparation']['runtime'].update(node='/foreign'),
                           lambda x:x['preparation']['runtime'].update(python='/foreign')):
                row=copy.deepcopy(original);change(row)
                with self.subTest(change=change),patch.object(p,'readmit',side_effect=AssertionError('must not launch optional verifier')):
                    with self.assertRaises(ValueError):p.admit_plan({'lanes':[row,copy.deepcopy(row)]},task,runtime)

    def test_preparation_entry_binds_actual_node_python_task_and_streams(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);where=p.paths(task);where['folder'].mkdir(parents=True);where['prepared'].parent.mkdir(parents=True)
            runtime={'python':sys.executable,'node':'/node','modules':'/modules','playwright':'/modules/playwright','pngjs':'/modules/pngjs'}
            (task/'runtime.json').write_text(json.dumps(runtime));where['prepared'].write_text(json.dumps({'trees':{'r0035':{'root':'/original'}}}))
            pin={'path':'/manifest','sha256':'a'*64,'bytes':1}
            entry={'protocol':'r0035-psf-preparation-entry/1','argv':p.prepare_argv(task,runtime),'cwd':str(HERE),
                   'timeoutSeconds':240,'sourcePins':pin,'returncode':0,'timedOut':False,'elapsedSeconds':1.0}
            child={'argv':p.transform_argv(runtime,'derive',Path('/original'),where['candidate']),'cwd':str(HERE),
                   'timeoutSeconds':30,'returncode':0,'timedOut':False,'elapsedSeconds':1.0,'stdout':'{}','stderr':''}
            for name,text in (('stdout','PSF SOURCE PAIR PREPARED; native NOT_RUN\n'),('stderr','')):
                (task/'capture'/('r0035-psf-preparation.'+name)).write_text(text)
            where['entry'].write_text(json.dumps(entry));where['transformProcess'].write_text(json.dumps(child))
            with patch.object(p,'source_pins',return_value=pin):
                p.entry_custody(task,runtime)
                for change in (lambda x:x['argv'].__setitem__(0,'/foreign'),lambda x:x['argv'].__setitem__(-1,'/other-task'),
                               lambda x:x.update(cwd='/other'),lambda x:x.update(timeoutSeconds=True),
                               lambda x:x.update(returncode=False),lambda x:x.update(timedOut=True)):
                    altered=copy.deepcopy(entry);change(altered);where['entry'].write_text(json.dumps(altered))
                    with self.subTest(change=change),self.assertRaises(ValueError):p.entry_custody(task,runtime)
                where['entry'].write_text(json.dumps(entry))
                changed=copy.deepcopy(child);changed['argv'][0]='/foreign';where['transformProcess'].write_text(json.dumps(changed))
                with self.assertRaises(ValueError):p.entry_custody(task,runtime)
                where['transformProcess'].write_text(json.dumps(child));(task/'capture/r0035-psf-preparation.stdout').write_text('forged success')
                with self.assertRaises(ValueError):p.entry_custody(task,runtime)

    def test_runtime_task_alias_is_refused(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);task=root/'task';task.mkdir();(task/'runtime.json').write_text('{}')
            with self.assertRaises(ValueError):p.paths(task/'..'/'task')

    def test_route_guard_refuses_before_real_external_action(self):
        entry=importlib.import_module('observe_r0035_psf');import retention_controls as fixtures
        owner=SimpleNamespace(loader=fixtures.retention,current={'base':'http://127.0.0.1:1234'},veto=None,errors=[])
        raw=fixtures.FakeRoute('https://outside.invalid/script')
        with self.assertRaises(ValueError):entry.Route(raw,owner).continue_()
        self.assertEqual(raw.actions,['abort']);self.assertIsNotNone(owner.veto)
        good=fixtures.FakeRoute('http://127.0.0.1:1234/source');entry.Route(good,owner).continue_()
        self.assertEqual(good.actions,['continue'])
        with self.assertRaises(ValueError):entry.Route(good,owner).fetch()
        self.assertEqual(good.actions,['continue'])

    def test_cleanup_retains_primary_and_close_failures_separately(self):
        entry=importlib.import_module('observe_r0035_psf')
        owner=SimpleNamespace(current={})
        def close():raise OSError('close fault')
        context=entry.Context(SimpleNamespace(close=close),owner)
        try:raise ValueError('original failure')
        except ValueError:
            with self.assertRaisesRegex(OSError,'close fault'):context.close()
        self.assertEqual(owner.current['unwinding']['message'],'original failure')
        self.assertEqual(owner.current['closeError']['message'],'close fault')

    def test_custody_calls_actual_original_trial_and_keeps_failed_report(self):
        entry=importlib.import_module('observe_r0035_psf');import retention_controls as fixtures
        loader=fixtures.retention;driver=loader.load_driver(ROOT/'tools/r0035/native_trials.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);evidence=root/'custody';evidence.mkdir()
            custody=entry.Custody(evidence,loader,'reference');original_assess=driver.assess;custody.install(driver)
            module=ModuleType('playwright.sync_api');module.TimeoutError=fixtures.BrowserTimeout
            args=SimpleNamespace(scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''),
                clock='ordinary',warmup=5,capture=False,seconds=15,observe_producer=True,scope='independent-reconstruction',driver_sha256={})
            browser=fixtures.FakeBrowser(driver);evaluate=browser.context.page.evaluate
            def failed(expression,*args):
                value=evaluate(expression,*args)
                if expression==driver.READ:value['prayersReady']=False
                return value
            browser.context.page.evaluate=failed
            with patch.dict(sys.modules,{'playwright.sync_api':module}):
                report=driver.trial(browser,'chromium','http://127.0.0.1:1234',{'root':str(root),'commit':'a'*40,'flags':''},'main',root/'trial',args)
            self.assertIs(driver.assess,original_assess);self.assertEqual(report['qualification']['verdict'],'failed')
            self.assertFalse(report['admitted']);self.assertEqual(json.loads((root/'trial/trial.json').read_text()),report)
            saved=json.loads((evidence/'trial-001-main.json').read_text())
            self.assertTrue(saved['contextClosed']);self.assertEqual(saved['pages'],1);self.assertEqual(custody.errors,[])

    def planning_fixture(self,task):
        p=self.module();where=p.paths(task);where['prepared'].parent.mkdir(parents=True)
        prepared={'sources':{'research':{'root':'/source'}},'trees':{'main':{'root':'/main'},'r0035':{'root':'/reference'}}}
        where['prepared'].write_text(json.dumps(prepared))
        runtime={'python':sys.executable,'node':'/node','modules':'/modules','playwright':'/modules/playwright','pngjs':'/modules/pngjs'}
        (task/'runtime.json').write_text(json.dumps(runtime))
        admission={'protocol':'r0035-psf-current-admission/1','status':'PASS','task':str(task),'runtime':runtime,'nativePreparation':False}
        plan=p.make_plan(prepared,task/'capture/lanes',runtime,admission)
        process={'argv':[runtime['python'],'-B',str(HERE/'r0035_psf.py'),'readmit','--task',str(task)],
                 'cwd':str(HERE),'timeoutSeconds':120,'returncode':0,'timedOut':False,'elapsedSeconds':1.0,'stdout':json.dumps(admission)}
        return runtime,plan,process

    def test_complete_canonical_plan_cannot_be_substituted_after_readmission(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);runtime,plan,process=self.planning_fixture(task)
            with patch.object(p,'readmit',return_value=process):
                self.assertEqual(p.admit_plan(plan,task,runtime),plan['lanes'])
                mutations=[lambda x:x['lanes'].pop(),lambda x:x['lanes'].reverse(),
                           lambda x:x['lanes'][1].update(id=x['lanes'][0]['id']),
                           lambda x:x['lanes'][0].update(timeoutSeconds=539),
                           lambda x:x['lanes'][0].update(dpr=True),
                           lambda x:x['lanes'][1]['psfObservation'].update(role='reference'),
                           lambda x:x['lanes'][0]['evidenceRetention']['originalArgv'].__setitem__(1,'/foreign/driver'),
                           lambda x:x['preparedReceipt'].update(sha256='0'*64)]
                for mutation in mutations:
                    changed=copy.deepcopy(plan);mutation(changed)
                    with self.subTest(mutation=mutation),self.assertRaises(ValueError):p.admit_plan(changed,task,runtime)

    def test_outer_dispatch_uses_reviewed_pair_bounds_and_keeps_both_failures(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);runtime,plan,_=self.planning_fixture(task);(task/'capture').mkdir(exist_ok=True)
            (task/'capture/lanes.json').write_text(json.dumps(plan));calls=[]
            args=SimpleNamespace(task=task,research=Path('/source'),baseline=Path('/baseline'),historical=Path('/history'),
                engine='chromium',r003f_dpr=1,work_orders=['R0035'],r002f=False,retain_evidence=False,
                r0035_guard='off',r0035_scope='all',r0035_mode='timing',r0035_psf=True)
            def bounded(argv,cwd,env,stdout,stderr,seconds):
                calls.append((argv,seconds))
                if '--lane' in argv:
                    identifier=argv[argv.index('--lane')+1]
                    observe.write_json(task/'capture/lane-status'/(identifier+'.json'),
                        {'id':identifier,'status':'FAIL','stopAll':False,'returncode':0,'timedOut':False,'originalStatus':'FAIL'})
                return {'returncode':0,'timedOut':False,'elapsedSeconds':1.0}
            with patch.object(observe,'admit_plan',return_value=plan['lanes']),patch.object(observe,'run_bounded',side_effect=bounded):
                self.assertEqual(observe.outside(args,runtime),2)
            self.assertEqual([x[1] for x in calls],[1350,885,885])
            self.assertTrue(all('--r0035-psf' in x[0] for x in calls))
            body=json.loads((task/'capture/observation.json').read_text())
            self.assertEqual([x['status'] for x in body['lanes']],['FAIL','FAIL'])
            self.assertEqual(body['psfPair']['status'],'INCOMPLETE')

    def test_original_replay_rejects_forged_qualification_metrics_and_control(self):
        p=self.module();import retention_controls as fixtures
        driver=fixtures.retention.load_driver(ROOT/'tools/r0035/native_trials.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);arm={'root':str(root),'commit':'a'*40,'flags':''}
            args=SimpleNamespace(scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''),
                clock='ordinary',warmup=5,capture=False,seconds=15,observe_producer=True,scope='independent-reconstruction',driver_sha256={})
            module=ModuleType('playwright.sync_api');module.TimeoutError=fixtures.BrowserTimeout
            with patch.dict(sys.modules,{'playwright.sync_api':module}):
                report=driver.trial(fixtures.FakeBrowser(driver),'chromium','http://127.0.0.1:1234',arm,'main',root/'trial',args)
            self.assertTrue(p.replay_trial(driver,report,arm,'main',args.scope)['admitted'])
            for mutate in (lambda x:x['qualification'].update(verdict='failed'),lambda x:x.update(p95FrameMs=0),
                           lambda x:x.update(clock='simulation'),lambda x:x.update(observedProducerDuringTrial=False),
                           lambda x:x['trace']['states'][0].update(prayersReady=False)):
                changed=copy.deepcopy(report);mutate(changed)
                with self.subTest(mutate=mutate),self.assertRaises(ValueError):p.replay_trial(driver,changed,arm,'main',args.scope)

    def raw_intake_fixture(self,task):
        """Actual pinned trial/assess functions over a fake browser; never native evidence."""
        p=self.module();entry=importlib.import_module('observe_r0035_psf')
        import retention_controls as fixtures
        import r0035_stage_materialize as material
        original_loader=material.support();driver=original_loader.load_driver(ROOT/'tools/r0035/native_trials.py')
        loader=SimpleNamespace(load_driver=original_loader.load_driver,verify_inputs=original_loader.verify_inputs,
                               verify_isolation=lambda value:{'sourceOnlyFixture':True})
        where=p.paths(task);where['folder'].mkdir(parents=True)
        runtime={'python':sys.executable,'node':'/node','modules':'/modules','playwright':'/modules/playwright','pngjs':'/modules/pngjs'}
        (task/'runtime.json').write_text(json.dumps(runtime))
        base=task/'reference';base.mkdir();main=task/'main';main.mkdir()
        prepared={'trees':{'main':{'root':str(main)},'r0035':{'root':str(base)}}};plan=p.original_plan(prepared)
        where['referencePlan'].write_text(json.dumps(plan));target=task/'capture/lanes/r0035-chromium-psf-reference';target.mkdir(parents=True)
        evidence=target.with_name(target.name+'-custody');evidence.mkdir()
        pin={'path':'/fixture/manifest','bytes':1,'sha256':'a'*64}
        admission={'protocol':'r0035-psf-current-admission/1','status':'PASS','task':str(task),'runtime':runtime,
                   'nativePreparation':True,'driver':str(ROOT/'tools/r0035/native_trials.py'),'sourcePins':pin,
                   'fixture':'SOURCE_ONLY_FAKE_BROWSER_NOT_NATIVE_EVIDENCE'}
        pre=task/'capture/r0035-psf-preadmission-reference.json';post=task/'capture/r0035-psf-postadmission-reference.json'
        process={'argv':[runtime['python'],'-B',str(HERE/'r0035_psf.py'),'readmit','--task',str(task),'--native'],
                 'cwd':str(HERE),'timeoutSeconds':120,'returncode':0,'timedOut':False,'elapsedSeconds':1.0,'stdout':json.dumps(admission)}
        pre.write_text(json.dumps(process));post.write_text(json.dumps(process))
        namespace=task/'capture/isolation/r0035-chromium-psf-reference/receipt.json';namespace.parent.mkdir(parents=True)
        namespace.write_text(json.dumps({'fixture':'SOURCE_ONLY_FAKE_BROWSER_NOT_NATIVE_EVIDENCE'}))
        hashes={name:material.pins()['files']['tools/r0035/'+name]['sha256'] for name in ('native_trials.py','trial_admission.py','trial_clock.js')}
        args=SimpleNamespace(plan=where['referencePlan'],output=target,engine='chromium',clock='ordinary',rounds=1,
                             seconds=15,warmup=5,scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',capture=False,
                             observe_producer=True,scope=plan['kind'],driver_sha256=hashes,scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''))
        custody=entry.Custody(evidence,loader,'reference');custody.install(driver)
        module=ModuleType('playwright.sync_api');module.TimeoutError=fixtures.BrowserTimeout
        reports=[]
        for arm in p.ARMS:
            browser=fixtures.FakeBrowser(driver);evaluate=browser.context.page.evaluate
            def trace(expression,*params,original=evaluate,label=arm):
                value=original(expression,*params)
                if 'window.__r0035.end=' in expression and label!='main':
                    events=[{'kind':'publication','at':t,'utcMs':1000+t,'ageMs':1,'id':'fixture-star','tier':'refined',
                             'identity':'accepted','changed':True,'nonempty':True,'writes':1,'epoch':1} for t in range(50,2001,50)]
                    value['publication']={'start':0,'end':2000,'initial':{'status':'active','tier':'refined','identity':'accepted'},
                                          'events':events,'overflow':False}
                return value
            browser.context.page.evaluate=trace
            with patch.dict(sys.modules,{'playwright.sync_api':module}):
                reports.append(driver.trial(browser,'chromium','http://127.0.0.1:1234',plan['arms'][arm],arm,target/('01-'+arm),args))
        keys=('arm','commit','clock','scene','motion','capture','observedProducerDuringTrial','qualification','p95FrameMs','p99FrameMs','maxFrameMs','framesOver50Ms','admitted')
        (target/'summary.json').write_text(json.dumps([{k:r[k] for k in keys} for r in reports]));(target/'plan.json').write_text(json.dumps(plan))
        final={'protocol':'r0035-psf-adapted-driver/1','status':'DRIVER_RETURNED','role':'reference','adapter':p.ADAPTER,
               'adapterCalls':1,'trialCalls':3,'errors':[],'originalException':None,'continuationVeto':None,
               'actualPython':runtime['python'],'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','humanAcceptance':'OUTSTANDING',
               'preadmission':p.record(pre),'sourceAdmission':admission,'sourcePins':pin,
               'actualOriginalArgv':[runtime['python'],admission['driver'],str(where['referencePlan']),str(target),*p.DRIVER_ARGS],
               'sources':loader.verify_inputs(Path(admission['driver'])),'isolation':p.record(namespace),
               'trials':custody.trials,'originalSummary':p.record(target/'summary.json')}
        (evidence/'driver.json').write_text(json.dumps(final))
        return runtime,plan,target,evidence,pin,loader,driver

    def test_full_original_intake_binds_all_reports_and_replays_real_original_assess(self):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);runtime,plan,target,evidence,pin,loader,driver=self.raw_intake_fixture(task)
            with patch.object(p,'source_pins',return_value=pin),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
                result=p.intake(task,runtime,'reference');self.assertEqual(result['originalStatus'],'PASS');self.assertEqual(len(result['trials']),3)
                # Make one complete original scientific failure and consistently
                # rebind custody. Complete intake must retain FAIL, never promote.
                path=target/'01-unmodified/trial.json';body=json.loads(path.read_text())
                body['trace']['publication']['events']=body['trace']['publication']['events'][:2]
                body['qualification']=driver.assess(body['before'],body['after'],body['trace'],body['trace']['publication'],
                    'dark',[-91,-20],'normal','ordinary',plan['arms']['unmodified']['producerProbe'],'unmodified',True)
                body['admitted']=False;path.write_text(json.dumps(body))
                receipt_path=evidence/'trial-002-unmodified.json';receipt=json.loads(receipt_path.read_text());receipt['originalReport']=p.record(path);receipt_path.write_text(json.dumps(receipt))
                summary=json.loads((target/'summary.json').read_text());summary[1]['qualification']=body['qualification'];summary[1]['admitted']=False
                (target/'summary.json').write_text(json.dumps(summary));final=json.loads((evidence/'driver.json').read_text())
                final['trials'][1]['receipt']=p.record(receipt_path);final['originalSummary']=p.record(target/'summary.json');(evidence/'driver.json').write_text(json.dumps(final))
                result=p.intake(task,runtime,'reference');self.assertEqual(result['status'],'COMPLETE');self.assertEqual(result['originalStatus'],'FAIL')

    def test_full_original_intake_rejects_extra_member_wrong_role_and_consistent_false_verdict(self):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        with tempfile.TemporaryDirectory() as temporary:
            task=Path(temporary);runtime,plan,target,evidence,pin,loader,driver=self.raw_intake_fixture(task)
            with patch.object(p,'source_pins',return_value=pin),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
                extra=target/'foreign.json';extra.write_text('{}')
                with self.assertRaises(ValueError):p.intake(task,runtime,'reference')
                extra.unlink();final_path=evidence/'driver.json';final=json.loads(final_path.read_text());final['role']='derived';final_path.write_text(json.dumps(final))
                with self.assertRaises(ValueError):p.intake(task,runtime,'reference')
                final['role']='reference';path=target/'01-main/trial.json';body=json.loads(path.read_text());body['before']['prayersReady']=False;path.write_text(json.dumps(body))
                receipt_path=evidence/'trial-001-main.json';receipt=json.loads(receipt_path.read_text());receipt['originalReport']=p.record(path);receipt_path.write_text(json.dumps(receipt))
                final['trials'][0]['receipt']=p.record(receipt_path);final_path.write_text(json.dumps(final))
                with self.assertRaisesRegex(ValueError,'original assessment replay'):p.intake(task,runtime,'reference')


if __name__=='__main__':unittest.main()
