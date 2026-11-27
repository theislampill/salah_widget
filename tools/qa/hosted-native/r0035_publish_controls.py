"""Bounded synthetic controls for the explicit publish observation route."""
import copy
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace,ModuleType
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


class PublishRoute(unittest.TestCase):
    def module(self):
        self.assertTrue((HERE/'r0035_publish.py').is_file(),'publish route is not implemented')
        return importlib.import_module('r0035_publish')

    def runtime(self,task):
        value={'python':sys.executable,'node':'/node','modules':'/modules','playwright':'/modules/playwright','pngjs':'/modules/pngjs'}
        (task/'runtime.json').write_text(json.dumps(value));return value

    def prepared(self,task):
        import prepare
        return {'sources':{'research':{'root':str(task/'research'),'commit':prepare.RESEARCH},
                           'baseline':{'root':str(task/'baseline'),'commit':prepare.BASELINE}},
                'trees':{'main':{'root':str(task/'main')},'r0035':{'root':str(task/'lab')}}}

    def test_exact_selector_and_existing_envelope(self):
        p=self.module();self.assertTrue(p.mode(True,['R0035'],p.CONTROLS,'chromium'))
        self.assertFalse(p.mode(False,['R0040'],{},'firefox'))
        self.assertEqual(p.budget(),{'coordinatorSeconds':2640,'workflowObservationMinutes':45})
        self.assertEqual(p.DRIVER_ARGS,['--engine','chromium','--rounds','1','--seconds','15','--clock','ordinary','--scene','dark','--motion','normal'])
        self.assertEqual((p.CHILD_SECONDS,p.READMISSION_SECONDS,p.POST_SECONDS,p.LANE_SECONDS,p.PREPARATION_SECONDS),(540,120,150,885,1350))
        for value in (1,None,'yes'):
            with self.subTest(value=value),self.assertRaises(ValueError):p.mode(value,['R0035'],p.CONTROLS,'chromium')
        for kwargs in ({'psf':True},{'stages':True},{'costs':True},{'retained':True},{'r002f':True},
                       {'moon':'corrected-b0'},{'rain':'capture'},{'matrix':{}},{'r002f_route':'tabhide'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):p.mode(True,['R0035'],p.CONTROLS,'chromium',**kwargs)
        for selected,controls,engine in [(['R0035','R0040'],p.CONTROLS,'chromium'),(['R0035'],{**p.CONTROLS,'guard':'default'},'chromium'),(['R0035'],p.CONTROLS,'firefox')]:
            with self.subTest(selected=selected,controls=controls,engine=engine),self.assertRaises(ValueError):p.mode(True,selected,controls,engine)

    def test_complete_population_changes_exactly_original_live_file(self):
        p=self.module();before={p.LIVE:{'bytes':1,'sha256':'a'},'unchanged':{'bytes':2,'sha256':'b'}}
        after=copy.deepcopy(before);after[p.LIVE]={'bytes':3,'sha256':'c'};p.check_delta(before,after)
        for value in (before,{**after,'extra':{}},{p.LIVE:after[p.LIVE]}, {**after,'unchanged':{}}):
            with self.subTest(value=value),self.assertRaises(ValueError):p.check_delta(before,value)

    def test_owned_population_refuses_links_to_protected_source(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'base';base.mkdir();out=root/'out';out.mkdir()
            (base/'file').write_text('original');(out/'file').write_text('original')
            p.owned_population(out,base)
            (out/'file').unlink();os.link(base/'file',out/'file')
            with self.assertRaises(ValueError):p.owned_population(out,base)
            self.assertEqual((base/'file').read_text(),'original')

    def test_derived_plan_preserves_original_and_all_arm_semantics(self):
        p=self.module();reference={'kind':'independent-reconstruction','arms':{x:{'root':'/old/'+x,'commit':'source','flags':'exact'} for x in p.ARMS}}
        before=copy.deepcopy(reference);derived=p.derived_plan(reference,Path('/candidate'),{'path':'/identity','sha256':'a'})
        self.assertEqual(reference,before);self.assertEqual(derived['kind'],p.KIND)
        for name in p.ARMS:
            self.assertEqual(derived['arms'][name],{**reference['arms'][name],**({'root':'/candidate'} if name!='main' else {})})
        self.assertEqual(derived['publishDiagnostic']['protocol'],p.IDENTITY)

    def test_plan_contains_one_exact_original_three_arm_lane(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);where=p.paths(task);where['prepared'].parent.mkdir(parents=True)
            prepared=self.prepared(task);where['prepared'].write_text(json.dumps(prepared))
            source={'protocol':'source','files':{'full':'bound'}}
            admission={'status':'PASS','runtime':runtime,'sources':source}
            with patch.object(p,'original_plan',return_value={'kind':'independent-reconstruction','arms':{}}):
                plan=p.make_plan(prepared,task/'capture/lanes',runtime,admission)
            self.assertEqual(len(plan['lanes']),1);lane=plan['lanes'][0]
            self.assertEqual(lane['id'],p.LANE);self.assertEqual(lane['result']['expectedArms'],list(p.ARMS));self.assertEqual(lane['result']['expectedRows'],3)
            self.assertEqual(lane['timeoutSeconds'],540);self.assertEqual(lane['stopAllOnExit'],[86]);self.assertFalse(plan['r0035Psf'])
            self.assertEqual(lane['argv'][-len(p.DRIVER_ARGS):],p.DRIVER_ARGS)
            self.assertEqual(lane['evidenceRetention']['originalArgv'][0],runtime['python'])
            self.assertFalse(lane['result']['capture']);self.assertEqual(lane['dependsOn'],[])
            self.assertTrue(plan['r0035Publish']);self.assertEqual(plan['publishSources'],source)

    def test_unprepared_plan_never_emits_executable_substitute(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);where=p.paths(task);where['prepared'].parent.mkdir(parents=True);where['prepared'].write_text('{}')
            with patch.object(p,'original_plan',return_value={}):
                plan=p.make_plan(self.prepared(task),task/'capture/lanes',runtime,{'status':'INCOMPLETE','reason':'source absent'})
            self.assertEqual(plan['lanes'][0]['argv'],[])

    def test_runtime_authority_is_checked_before_readmission_child(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task)
            row={'preparation':{'status':'PASS','runtime':runtime},'argv':['/forged'],
                 'env':{'NODE_PATH':runtime['modules']},'evidenceRetention':{'originalArgv':[runtime['python']]}}
            with patch.object(p,'readmit',side_effect=AssertionError('unadmitted child launched')):
                with self.assertRaises(ValueError):p.admit_plan({'lanes':[row]},task,runtime)
            row['argv'][0]=runtime['python'];row['env']['NODE_PATH']='/foreign'
            with patch.object(p,'readmit',side_effect=AssertionError('unadmitted child launched')):
                with self.assertRaises(ValueError):p.admit_plan({'lanes':[row]},task,runtime)

    def test_current_process_requires_actual_argv_cwd_bound_and_terminal_source(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task)
            body={'protocol':p.ADMISSION,'status':'PASS','task':str(task),'runtime':runtime,'nativePreparation':True,'sources':{}}
            process={'argv':p.readmit_argv(task,runtime,True),'cwd':str(HERE),'timeoutSeconds':120,'returncode':0,
                     'timedOut':False,'elapsedSeconds':1.0,'stdout':json.dumps(body),'stderr':''}
            self.assertEqual(p.admitted_process(process,task,runtime,True),body)
            for change in (lambda x:x['argv'].__setitem__(0,'/forged'),lambda x:x.update(cwd='/foreign'),
                           lambda x:x.update(timeoutSeconds=True),lambda x:x.update(returncode=False),
                           lambda x:x.update(timedOut=True),lambda x:x.update(elapsedSeconds=121)):
                bad=copy.deepcopy(process);change(bad)
                with self.subTest(change=change),self.assertRaises(ValueError):p.admitted_process(bad,task,runtime,True)

    def test_private_adapter_calls_original_admission_and_flags_without_replacing_science(self):
        p=self.module();entry=importlib.import_module('observe_r0035_publish');calls=[]
        reference={'kind':'independent-reconstruction','arms':{name:{'flags':name} for name in p.ARMS}}
        derived=p.derived_plan(reference,'/candidate',{'sha256':'identity'})
        science=object();driver=SimpleNamespace(assess=science,
            check_plan=lambda value:calls.append(('check',copy.deepcopy(value))),
            verify_reconstructed_flags=lambda value:calls.append(('flags',copy.deepcopy(value))),
            producer_flags=lambda *args:calls.append(('producer',args)))
        adapter=entry.PlanAdapter(driver,reference,derived,lambda:calls.append(('current',)))
        adapter(derived);self.assertEqual(driver.assess,science);self.assertEqual(adapter.calls,1)
        self.assertEqual(calls[0],('current',));self.assertEqual(calls[1],('check',reference));self.assertEqual(len(calls),6)
        with self.assertRaises(ValueError):adapter(reference)
        self.assertEqual(adapter.calls,1)

    def test_original_route_prevents_external_continuation_before_action(self):
        self.module();entry=importlib.import_module('observe_r0035_publish');import retention_controls as fixture
        owner=SimpleNamespace(loader=fixture.retention,current={'base':'http://127.0.0.1:1234'},veto=None,errors=[])
        route=fixture.FakeRoute('https://outside.invalid/x')
        with self.assertRaises(ValueError):entry.Route(route,owner).continue_()
        self.assertEqual(route.actions,['abort']);self.assertIsNotNone(owner.veto)
        good=fixture.FakeRoute('http://127.0.0.1:1234/index.html');entry.Route(good,owner).continue_()
        self.assertEqual(good.actions,['continue'])
        with self.assertRaises(ValueError):entry.Route(good,owner).fetch()

    def test_actual_original_trial_calls_and_failed_report_are_preserved(self):
        p=self.module();entry=importlib.import_module('observe_r0035_publish');import retention_controls as fixture
        outputs=[]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);module=ModuleType('playwright.sync_api');module.TimeoutError=fixture.BrowserTimeout
            for adapted in (False,True):
                driver=fixture.retention.load_driver(ROOT/'tools/r0035/native_trials.py')
                driver.time=SimpleNamespace(monotonic_ns=iter([0,15000000000]).__next__)
                browser=fixture.FakeBrowser(driver);page=browser.context.page;calls=[]
                for name in ('goto','wait_for_function','wait_for_timeout','evaluate','locator','screenshot'):
                    original=getattr(page,name)
                    def observed(*args,_name=name,_original=original,**kwargs):
                        calls.append((_name,args,kwargs));value=_original(*args,**kwargs)
                        if _name=='evaluate' and args[0]==driver.READ:value['prayersReady']=False
                        return value
                    setattr(page,name,observed)
                science=driver.assess;out=root/('adapted' if adapted else 'original')
                args=SimpleNamespace(scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''),
                    clock='ordinary',warmup=5,capture=False,seconds=15,observe_producer=True,scope=p.KIND,driver_sha256={})
                if adapted:
                    custody_dir=root/'custody';custody_dir.mkdir();custody=entry.Custody(custody_dir,fixture.retention);custody.install(driver)
                with patch.dict(sys.modules,{'playwright.sync_api':module}):
                    report=driver.trial(browser,'chromium','http://127.0.0.1:1234',{'root':str(root),'commit':'a'*40,'flags':''},'main',out,args)
                self.assertIs(driver.assess,science);self.assertEqual(report['qualification']['verdict'],'failed');self.assertFalse(report['admitted'])
                self.assertEqual(json.loads((out/'trial.json').read_text()),report)
                self.assertEqual([c[1][0] for c in calls if c[0]=='wait_for_timeout'],[5000,15000])
                self.assertEqual([c for c in calls if c[0]=='screenshot'],[])
                if adapted:
                    saved=json.loads((custody_dir/'trial-001-main.json').read_text())
                    self.assertTrue(saved['contextClosed']);self.assertEqual(saved['pages'],1);self.assertEqual(custody.errors,[])
                outputs.append((calls,browser.context.calls,report))
            self.assertEqual(outputs[0],outputs[1])

    def complete_fixture(self):
        p=self.module();admission={'protocol':p.ADMISSION,'status':'PASS','sources':{'full':'actual'},'runtime':{'python':'/python'}}
        lane={'id':p.LANE,'preparation':admission,'publishObservation':{'protocol':'r0035-publish-diagnostic/1'}}
        intake={'protocol':'r0035-publish-original-intake/1','status':'COMPLETE','originalStatus':'PASS',
                'sourceAdmission':admission,'history':{'protocol':'r0035-publish-history-intake/1','status':'COMPLETE'},
                'speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}
        inner={'id':p.LANE,'status':p.OBSERVED,'stopAll':False,'returncode':0,'timedOut':False,'originalStatus':'PASS',
               'publishObservation':{'status':'COMPLETE','intake':intake},'timingClass':p.TIMING,
               'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}
        return p,lane,inner

    def test_classification_never_promotes_original_fail_or_incomplete_process(self):
        p,lane,inner=self.complete_fixture();supplement=inner['publishObservation']
        self.assertEqual(p.classify(lane,{'status':'PASS'},supplement,0,False)['status'],p.OBSERVED)
        for status in ('FAIL','INCOMPLETE','INCONCLUSIVE'):
            result=p.classify(lane,{'status':status},supplement,0,False)
            self.assertEqual(result['status'],status);self.assertEqual(result['originalStatus'],status)
        for code,timed in ((1,False),(False,False),(None,False),(0,True)):
            self.assertEqual(p.classify(lane,{'status':'PASS'},supplement,code,timed)['status'],'INCOMPLETE')
        changed=copy.deepcopy(supplement);changed['intake']['originalStatus']='FAIL'
        self.assertEqual(p.classify(lane,{'status':'PASS'},changed,0,False)['status'],'INCOMPLETE')

    def test_namespace_admission_requires_every_supplemental_binding(self):
        p,lane,inner=self.complete_fixture();self.assertTrue(p.namespace_admitted(lane,inner))
        for change in (lambda x:x.update(status='PASS'),lambda x:x.update(returncode=False),lambda x:x.update(timedOut=True),
                       lambda x:x.update(originalStatus='FAIL'),lambda x:x.update(speed='FASTER'),
                       lambda x:x['publishObservation']['intake'].update(sourceAdmission={}),
                       lambda x:x['publishObservation']['intake']['history'].update(status='INCOMPLETE')):
            altered=copy.deepcopy(inner);change(altered)
            with self.subTest(change=change):self.assertFalse(p.namespace_admitted(lane,altered))
        self.assertFalse(p.namespace_admitted({},inner))

    def test_complete_plan_comparison_cannot_drop_source_or_change_native_arguments(self):
        p=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);where=p.paths(task);where['prepared'].parent.mkdir(parents=True)
            prepared=self.prepared(task);where['prepared'].write_text(json.dumps(prepared))
            admission={'protocol':p.ADMISSION,'status':'PASS','task':str(task),'runtime':runtime,'nativePreparation':True,'sources':{'all':'bound'}}
            process={'argv':p.readmit_argv(task,runtime,True),'cwd':str(HERE),'timeoutSeconds':120,'returncode':0,
                     'timedOut':False,'elapsedSeconds':1,'stdout':json.dumps(admission),'stderr':''}
            with patch.object(p,'original_plan',return_value={}),patch.object(p,'readmit',return_value=process):
                plan=p.make_plan(prepared,task/'capture/lanes',runtime,admission)
                self.assertEqual(p.admit_plan(plan,task,runtime,True),plan['lanes'])
                for change in (lambda x:x.update(publishSources={}),lambda x:x['lanes'][0].update(timeoutSeconds=541),
                               lambda x:x['lanes'][0]['argv'].__setitem__(-1,'reduced'),lambda x:x['lanes'][0]['result'].update(expectedRows=6),
                               lambda x:x['lanes'][0]['preparation'].update(sources={}),lambda x:x['lanes'][0].update(stopAllOnExit=[])):
                    bad=copy.deepcopy(plan);change(bad)
                    with self.subTest(change=change),self.assertRaises(ValueError):p.admit_plan(bad,task,runtime,True)

    def raw_fixture(self,task,failed=False):
        """Run pinned trial/assessment with synthetic browser surfaces only."""
        p=self.module();entry=importlib.import_module('observe_r0035_publish')
        import retention_controls as fixtures
        import r0035_stage_materialize as material
        original_loader=material.support();driver=original_loader.load_driver(ROOT/'tools/r0035/native_trials.py')
        loader=SimpleNamespace(load_driver=original_loader.load_driver,verify_inputs=original_loader.verify_inputs,
                               verify_isolation=lambda value:{'sourceOnlyFixture':True})
        where=p.paths(task);where['folder'].mkdir(parents=True);runtime=self.runtime(task)
        runtime['node']=shutil.which('node');(task/'runtime.json').write_text(json.dumps(runtime))
        base=task/'reference';base.mkdir();main=task/'main';main.mkdir();where['candidate'].mkdir(parents=True)
        prepared={'trees':{'main':{'root':str(main)},'r0035':{'root':str(base)}}}
        plan=p.derived_plan(p.original_plan(prepared),where['candidate'],{'synthetic':'source-only'})
        where['derivedPlan'].write_text(json.dumps(plan));target=task/'capture/lanes'/p.LANE;target.mkdir(parents=True)
        evidence=target.with_name(p.LANE+'-custody');evidence.mkdir();sources={'fixture':'SOURCE_ONLY_FAKE_BROWSER_NOT_NATIVE_EVIDENCE'}
        admission={'protocol':p.ADMISSION,'status':'PASS','task':str(task),'runtime':runtime,'nativePreparation':True,
                   'driver':str(ROOT/'tools/r0035/native_trials.py'),'sources':sources}
        pre=task/'capture/r0035-publish-preadmission.json';post=task/'capture/r0035-publish-postadmission.json'
        process={'argv':p.readmit_argv(task,runtime,True),'cwd':str(HERE),'timeoutSeconds':120,'returncode':0,
                 'timedOut':False,'elapsedSeconds':1.0,'stdout':json.dumps(admission),'stderr':''}
        pre.write_text(json.dumps(process));post.write_text(json.dumps(process))
        namespace=task/'capture/isolation'/p.LANE/'receipt.json';namespace.parent.mkdir(parents=True)
        namespace.write_text(json.dumps(sources))
        hashes={name:material.pins()['files']['tools/r0035/'+name]['sha256'] for name in ('native_trials.py','trial_admission.py','trial_clock.js')}
        args=SimpleNamespace(plan=where['derivedPlan'],output=target,engine='chromium',clock='ordinary',rounds=1,
            seconds=15,warmup=5,scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',capture=False,observe_producer=True,
            scope=p.KIND,driver_sha256=hashes,scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''))
        custody=entry.Custody(evidence,loader);custody.install(driver)
        module=ModuleType('playwright.sync_api');module.TimeoutError=fixtures.BrowserTimeout;reports=[]
        for label in p.ARMS:
            browser=fixtures.FakeBrowser(driver);evaluate=browser.context.page.evaluate
            def trace(expression,*params,original=evaluate,arm=label):
                value=original(expression,*params)
                if expression==driver.READ and failed and arm=='unmodified':value['prayersReady']=False
                if 'window.__r0035.end=' in expression and arm!='main':
                    event={'at':1,'kind':'owner','epoch':2,'tier':'refined','identity':'accepted','r0035Publish':{
                        'protocol':'r0035-publish-decision/1','previousEpoch':1,'hadSource':True,'evaluatedMask':1,'equalMask':0,
                        'wasPrepared':True,'samplePending':False,'preparingEpoch':None,'latestQueued':False}}
                    events=[event]+[{'kind':'publication','at':t,'utcMs':1000+t,'ageMs':1,'id':'fixture-star','tier':'refined',
                        'identity':'accepted','changed':True,'nonempty':True,'writes':1,'epoch':2} for t in range(50,2001,50)]
                    value['publication']={'start':0,'end':2000,'initial':{'status':'active','tier':'refined','identity':'accepted'},
                                          'events':events,'overflow':False}
                return value
            browser.context.page.evaluate=trace
            with patch.dict(sys.modules,{'playwright.sync_api':module}):
                reports.append(driver.trial(browser,'chromium','http://127.0.0.1:1234',plan['arms'][label],label,target/('01-'+label),args))
        keys=('arm','commit','clock','scene','motion','capture','observedProducerDuringTrial','qualification','p95FrameMs','p99FrameMs','maxFrameMs','framesOver50Ms','admitted')
        (target/'summary.json').write_text(json.dumps([{k:r[k] for k in keys} for r in reports]));(target/'plan.json').write_text(json.dumps(plan))
        final={'protocol':'r0035-publish-adapted-driver/1','status':'DRIVER_RETURNED','adapter':p.ADAPTER,
               'adapterCalls':1,'trialCalls':3,'errors':[],'originalException':None,'continuationVeto':None,
               'actualPython':runtime['python'],'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','humanAcceptance':'OUTSTANDING',
               'speed':'NOT_ESTABLISHED','preadmission':p.record(pre),'sourceAdmission':admission,'sources':sources,
               'actualOriginalArgv':[runtime['python'],admission['driver'],str(where['derivedPlan']),str(target),*p.DRIVER_ARGS],
               'originalSources':loader.verify_inputs(Path(admission['driver'])),'isolation':p.record(namespace),
               'trials':custody.trials,'originalSummary':p.record(target/'summary.json')}
        (evidence/'driver.json').write_text(json.dumps(final));return runtime,plan,target,evidence,sources,loader,driver

    def test_complete_intake_replays_real_science_and_actual_node_history_while_preserving_fail(self):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        for failed in (False,True):
            with self.subTest(failed=failed),tempfile.TemporaryDirectory() as tmp:
                task=Path(tmp);runtime,plan,target,evidence,sources,loader,driver=self.raw_fixture(task,failed)
                before=p.inventory(target)
                with patch.object(p,'source_identity',return_value=sources),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
                    result=p.intake(task,runtime)
                self.assertEqual(result['originalStatus'],'FAIL' if failed else 'PASS');self.assertEqual(result['status'],'COMPLETE')
                self.assertEqual(result['history']['totalOwners'],2);self.assertEqual(result['speed'],'NOT_ESTABLISHED')
                process=p.load(task/'capture/r0035-publish-history-process.json')
                self.assertEqual(process['returncode'],0);self.assertEqual(process['argv'][0],runtime['node']);self.assertEqual(p.inventory(target),before)

    def rebind_trial(self,p,target,evidence,label,body):
        ordinal=p.ARMS.index(label)+1;trial=target/f'01-{label}/trial.json';trial.write_text(json.dumps(body))
        receipt_path=evidence/f'trial-{ordinal:03}-{label}.json';receipt=p.load(receipt_path);receipt['originalReport']=p.record(trial)
        receipt_path.write_text(json.dumps(receipt));final=p.load(evidence/'driver.json');final['trials'][ordinal-1]['receipt']=p.record(receipt_path)
        (evidence/'driver.json').write_text(json.dumps(final))

    def test_consistently_rebound_false_scientific_verdict_is_still_rejected(self):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime,plan,target,evidence,sources,loader,driver=self.raw_fixture(task)
            body=p.load(target/'01-main/trial.json');body['before']['prayersReady']=False;self.rebind_trial(p,target,evidence,'main',body)
            with patch.object(p,'source_identity',return_value=sources),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
                with self.assertRaisesRegex(ValueError,'original assessment replay'):p.intake(task,runtime)

    def test_missing_supplement_cannot_be_repaired_by_rebinding_original_report_custody(self):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime,plan,target,evidence,sources,loader,driver=self.raw_fixture(task)
            body=p.load(target/'01-unmodified/trial.json');del body['trace']['publication']['events'][0]['r0035Publish']
            self.rebind_trial(p,target,evidence,'unmodified',body)
            with patch.object(p,'source_identity',return_value=sources),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
                with self.assertRaisesRegex(ValueError,'owner-history'):p.intake(task,runtime)
            failed=p.load(task/'capture/r0035-publish-history-process.json');self.assertNotEqual(failed['returncode'],0)

    def test_intake_refuses_extra_files_or_changed_complete_source_before_history_child(self):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime,plan,target,evidence,sources,loader,driver=self.raw_fixture(task)
            with patch.object(p,'source_identity',return_value=sources),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
                (target/'extra.json').write_text('{}')
                with self.assertRaisesRegex(ValueError,'population'):p.intake(task,runtime)
                (target/'extra.json').unlink();post=task/'capture/r0035-publish-postadmission.json';body=p.load(post)
                admission=json.loads(body['stdout']);admission['sources']={};body['stdout']=json.dumps(admission);post.write_text(json.dumps(body))
                with patch.object(p,'run_process',side_effect=AssertionError('must not launch history child')):
                    with self.assertRaisesRegex(ValueError,'pre/post'):p.intake(task,runtime)

    def campaign(self):
        return {'schemaVersion':1,'engine':'chromium','r003fDpr':1,'workOrders':['R0035'],
                'r0035Publish':True,'r0035':{'guard':'off','scope':'all','mode':'timing'},
                'r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'}}

    def test_central_campaign_is_explicit_exclusive_and_uses_original_envelope(self):
        p=self.module();import observe
        self.assertTrue(hasattr(observe,'publish_campaign'),'central publish route selector missing')
        self.assertEqual(observe.campaign_budget(self.campaign()),p.budget())
        self.assertEqual(observe.campaign_budget({}),{'coordinatorSeconds':2640,'workflowObservationMinutes':45})
        for change in ({'r0035Psf':True},{'r0035Stages':True},{'r0035Costs':True},{'r0035Publish':'true'},
                       {'r0040Mode':'capture-mechanism-autoattach'},{'r002fRoute':'bfcache-witness'}):
            with self.subTest(change=change),self.assertRaises(ValueError):observe.campaign_budget({**self.campaign(),**change})

    def test_central_planner_and_inner_dispatch_keep_the_exact_new_selector(self):
        p=self.module();import lanes;import observe
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);where=p.paths(task);where['prepared'].parent.mkdir(parents=True)
            prepared=self.prepared(task);where['prepared'].write_text(json.dumps(prepared))
            marker={'status':'PASS','runtime':runtime,'sources':{'complete':'source'}}
            planned=lanes.make_plan(prepared,task/'capture/lanes',python_playwright=Path(runtime['python']),node=Path(runtime['node']),
                node_modules=Path(runtime['modules']),pngjs=Path(runtime['pngjs']),work_orders=['R0035'],
                r0035_guard='off',r0035_scope='all',r0035_mode='timing',r0035_publish=True,r0035_publish_preparation=marker)
            self.assertEqual(planned,p.make_plan(prepared,task/'capture/lanes',runtime,marker))
            args=SimpleNamespace(task=task,research=task/'research',baseline=task/'baseline',historical=task/'history',
                work_orders=['R0035'],engine='chromium',r0035_guard='off',r0035_scope='all',r0035_mode='timing',
                r0035_publish=True,r002f=False,retain_evidence=False,r003f_dpr=1)
            command=observe.isolated_command(args,runtime,'lane',p.LANE)
            self.assertEqual(command.count('--r0035-publish'),1);self.assertNotIn('--r0035-psf',command)
            with patch.object(p,'admit_plan',return_value=planned['lanes']) as admitted:
                self.assertEqual(observe.admit_plan(planned,args,runtime),planned['lanes'])
                self.assertEqual(admitted.call_args.kwargs['retain'],task/'capture/r0035-publish-outer-admission.json')

    def test_central_classifier_and_namespace_keep_original_failure(self):
        p,lane,inner=self.complete_fixture();import observe
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'summary.json';lane['result']={'kind':'r0035-trials','path':str(target)}
            rows=[{'arm':arm,'admitted':True,'qualification':{'verdict':'passed'}} for arm in p.ARMS]
            target.write_text(json.dumps(rows))
            with patch.object(p,'post_observation',return_value=inner['publishObservation']):
                self.assertEqual(observe.classify_lane(lane,0,False)['status'],p.OBSERVED)
                rows[1]['qualification']['verdict']='failed';rows[1]['admitted']=False;target.write_text(json.dumps(rows))
                self.assertEqual(observe.classify_lane(lane,0,False)['status'],'FAIL')
            self.assertEqual(observe.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],p.OBSERVED)
            self.assertEqual(observe.namespace_status(lane,{'returncode':0,'timedOut':True},inner)['status'],'ISOLATION_UNCONFIRMED')

    def test_producer_complete_gate_binds_full_plan_and_preserves_original_fail(self):
        p,lane,inner=self.complete_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);where=p.paths(task);where['prepared'].parent.mkdir(parents=True)
            prepared=self.prepared(task);where['prepared'].write_text(json.dumps(prepared));sources={'full':'actual'}
            admission={'protocol':p.ADMISSION,'status':'PASS','runtime':runtime,'sources':sources}
            plan=p.make_plan(prepared,task/'capture/lanes',runtime,admission);lane=plan['lanes'][0]
            inner['publishObservation']['intake']['sourceAdmission']=admission
            row={**copy.deepcopy(inner),'innerStatus':copy.deepcopy(inner),'namespaceProcess':{'returncode':0,'timedOut':False,'elapsedSeconds':1}}
            body={'r0035Publish':True,'lanes':[row]}
            status_file=task/'capture/lane-status'/(p.LANE+'.json');status_file.parent.mkdir(parents=True)
            status_file.write_text(json.dumps(inner))
            with patch.object(p,'source_identity',return_value=sources),patch.object(p,'retained_supplement') as retained:
                self.assertTrue(p.producer_gate(self.campaign(),plan,body,task))
                self.assertEqual(retained.call_count,1)
                for change in (lambda x:x['lanes'][0]['argv'].__setitem__(-1,'other'),lambda x:x.update(publishSources={}),
                               lambda x:x['lanes'][0].update(timeoutSeconds=999),lambda x:x['preparedReceipt'].update(sha256='forged')):
                    changed=copy.deepcopy(plan);change(changed)
                    with self.subTest(change=change),self.assertRaises(ValueError):p.producer_gate(self.campaign(),changed,body,task)
                failed=copy.deepcopy(body)
                for value in (failed['lanes'][0],failed['lanes'][0]['innerStatus']):
                    value['status']='FAIL';value['originalStatus']='FAIL';value['publishObservation']['intake']['originalStatus']='FAIL'
                status_file.write_text(json.dumps(failed['lanes'][0]['innerStatus']))
                self.assertFalse(p.producer_gate(self.campaign(),plan,failed,task))
                status_file.write_text(json.dumps(inner))
                bad=copy.deepcopy(body);bad['lanes'][0]['innerStatus']['publishObservation']['intake']['sourceAdmission']={}
                with self.assertRaises(ValueError):p.producer_gate(self.campaign(),plan,bad,task)

    def test_pipeline_calls_the_selected_complete_gate(self):
        self.module();import capture_pipeline as pipeline
        self.assertTrue(hasattr(pipeline,'publish_complete_record'),'publish producer complete equality seam missing')
        with patch('r0035_publish.producer_gate',return_value=False) as gate:
            self.assertFalse(pipeline.publish_complete_record(self.campaign(),{}, {},Path('/synthetic')))
            self.assertEqual(gate.call_count,1)
        with patch('r0035_publish.producer_gate',side_effect=ValueError('unbound source')):
            with self.assertRaises(pipeline.Rejected):pipeline.publish_complete_record(self.campaign(),{}, {},Path('/synthetic'))

    def test_actual_git_closure_refuses_dirty_hidden_missing_and_unknown_source(self):
        p=self.module();names=p.source_files()
        self.assertEqual(names,json.loads((HERE/'r0035-publish-pins.json').read_text())['sourceFiles'])
        self.assertEqual(names,json.loads((HERE/'r002f-bfcache-pins.json').read_text())['sourceFiles'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);here=root/'tools/qa/hosted-native'
            for name in names:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
            def git(*args):
                return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,
                    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='')).stdout.decode().strip()
            git('init','-q');git('add','--all')
            git('-c','user.name=Source control fixture','-c','user.email=source-control@example.invalid','commit','-qm','Synthetic source-currentness fixture; no native evidence')
            with patch.object(p,'ROOT',root),patch.object(p,'HERE',here):
                identity=p.source_identity()
                self.assertEqual(identity['commit'],git('rev-parse','HEAD'));self.assertEqual(identity['tree'],git('rev-parse','HEAD^{tree}'))
                self.assertEqual(set(identity['files']),set(names))
                selected='tools/qa/hosted-native/observe.py';original=(root/selected).read_bytes()
                (root/selected).write_bytes(original+b'\n# synthetic drift\n')
                with self.assertRaisesRegex(ValueError,'not clean'):p.source_identity()
                git('update-index','--skip-worktree',selected)
                self.assertEqual(git('status','--porcelain'),'')
                with self.assertRaisesRegex(ValueError,'source blob mismatch'):p.source_identity()
                (root/selected).unlink()
                with self.assertRaisesRegex(ValueError,'missing or nonregular'):p.source_identity()
                (root/selected).write_bytes(original);git('update-index','--no-skip-worktree',selected)
                with patch.object(p,'source_files',return_value=names+['unknown']):
                    with self.assertRaisesRegex(ValueError,'declared complete'):p.source_identity()
                self.assertEqual(p.source_identity(),identity)

    def test_both_producer_phases_bind_the_whole_composed_closure_only_when_selected(self):
        p=self.module();import capture_pipeline as pipeline;import r0040_autoattach_central as auto
        expected={name:p.original_support.sha((HERE/name).read_bytes()) for name in p.producer_source_files()}
        self.assertEqual(set(auto.caller_sources()),set(expected))
        campaigns=[self.campaign(),{'workOrders':['R002F'],'engine':'chromium','r002fRoute':'bfcache-witness',
                    'r002f':{'enabled':True,'dpr':1,'rounds':1,'section':'all'}},
                   {'workOrders':['R0040'],'engine':'chromium','r0040Mode':'capture-mechanism-autoattach'}]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);task=root/'task';task.mkdir()
            roots={name:str(root/name) for name in ('research','baseline','historical')}
            for value in roots.values():Path(value).mkdir()
            for campaign in campaigns:
                for phase in ('acquisition','observation'):
                    with self.subTest(campaign=campaign,phase=phase),patch.object(pipeline,'load',return_value=campaign):
                        actual=pipeline.producer_identity(phase,task,roots)
                    self.assertEqual(actual['sources'],expected)
            with patch.object(pipeline,'load',return_value={}):
                self.assertEqual(set(pipeline.producer_identity('acquisition',task,roots)['sources']),{'capture_pipeline.py','acquire.sh','campaign.json'})

    def retained_fixture(self,task):
        p=self.module();import r0035_stage_materialize as material;import r003f_matrix_campaign as boundary
        runtime,plan,target,evidence,sources,loader,driver=self.raw_fixture(task)
        with patch.object(p,'source_identity',return_value=sources),patch.object(material,'support',return_value=loader),patch.object(boundary,'original_isolation',return_value={}):
            body=p.intake(task,runtime)
        checked={'argv':[runtime['python'],'-B',str(HERE/'r0035_publish.py'),'intake','--task',str(task),'--native'],
                 'cwd':str(HERE),'timeoutSeconds':30,'returncode':0,'timedOut':False,'elapsedSeconds':1.0,
                 'stdout':json.dumps(body),'stderr':''}
        p.save(task/'capture/r0035-publish-intake.json',checked)
        current=p.load(task/'capture/r0035-publish-postadmission.json')
        p.save(task/'capture/r0035-publish-outer-admission.json',current)
        supplement={'status':'COMPLETE','currentSourceProcess':current,'intakeProcess':checked,'intake':body,
                    'currentSourceRecord':p.record(task/'capture/r0035-publish-postadmission.json'),
                    'intakeRecord':p.record(task/'capture/r0035-publish-intake.json')}
        return runtime,{'preparation':body['sourceAdmission']},supplement,target,evidence

    def test_final_gate_reads_actual_currentness_intake_and_raw_report_records(self):
        p=self.module()
        self.assertTrue(hasattr(p,'retained_supplement'),'actual retained-file final gate missing')
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime,lane,value,target,evidence=self.retained_fixture(task)
            p.retained_supplement(task,runtime,lane,value)
            for path in (target/'summary.json',target/'01-unmodified/trial.json',evidence/'driver.json',
                         evidence/'trial-002-unmodified.json',task/'capture/r0035-publish-history-process.json',
                         task/'capture/r0035-publish-postadmission.json',task/'capture/r0035-publish-intake.json'):
                saved=path.read_bytes();path.write_bytes(saved+b' ')
                with self.subTest(path=path),self.assertRaises(ValueError):p.retained_supplement(task,runtime,lane,value)
                path.write_bytes(saved)
            bad=copy.deepcopy(value);bad['intakeProcess']['timeoutSeconds']=31
            with self.assertRaises(ValueError):p.retained_supplement(task,runtime,lane,bad)
            bad=copy.deepcopy(value);bad['intake']['history']={'protocol':'r0035-publish-history-intake/1','status':'COMPLETE'}
            with self.assertRaises(ValueError):p.retained_supplement(task,runtime,lane,bad)

    def test_malformed_supplement_is_a_refusal_without_an_exception(self):
        p,lane,inner=self.complete_fixture()
        for malformed in ({'intake':None},{'intake':[]},{'intake':{'history':None}},{'intake':{'history':[]}}):
            with self.subTest(malformed=malformed):self.assertFalse(p.complete_supplement(lane,malformed,'PASS'))

    def test_actual_outer_dispatch_uses_one_lane_and_original_namespace_envelope(self):
        p,unused,inner=self.complete_fixture();import observe
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);where=p.paths(task);where['prepared'].parent.mkdir(parents=True)
            prepared=self.prepared(task);where['prepared'].write_text(json.dumps(prepared))
            admission={'status':'PASS','runtime':runtime,'sources':{'synthetic':'source-only'}}
            plan=p.make_plan(prepared,task/'capture/lanes',runtime,admission);lane=plan['lanes'][0]
            inner['publishObservation']['intake']['sourceAdmission']=admission
            (task/'capture').mkdir();p.save(task/'capture/lanes.json',plan)
            status=task/'capture/lane-status'/(p.LANE+'.json');status.parent.mkdir()
            p.save(status,inner)
            args=SimpleNamespace(task=task,research=task/'research',baseline=task/'baseline',historical=task/'history',
                work_orders=['R0035'],engine='chromium',r0035_guard='off',r0035_scope='all',r0035_mode='timing',
                r0035_publish=True,r002f=False,retain_evidence=False,r003f_dpr=1)
            observed=[]
            def run(*values):
                observed.append(values);return {'returncode':0,'timedOut':False,'elapsedSeconds':1.0}
            with patch.object(observe,'run_bounded',side_effect=run),patch.object(observe,'admit_plan',return_value=[lane]):
                self.assertEqual(observe.outside(args,runtime),0)
            self.assertEqual([v[-1] for v in observed],[1350,885]);self.assertEqual(len(observed),2)
            self.assertEqual([v[0].count('--r0035-publish') for v in observed],[1,1])
            self.assertIn(p.LANE,observed[1][0]);body=p.load(task/'capture/observation.json')
            self.assertEqual([row['id'] for row in body['lanes']],[p.LANE]);self.assertEqual(body['budget'],p.budget())

    def test_inner_source_refusal_cannot_dispatch_the_original_native_child(self):
        p=self.module();import observe
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp);runtime=self.runtime(task);(task/'capture').mkdir();p.save(task/'capture/lanes.json',{})
            args=SimpleNamespace(task=task,inside=True,phase='lane',lane=p.LANE,work_orders=['R0035'],engine='chromium',
                r0035_guard='off',r0035_scope='all',r0035_mode='timing',r0035_publish=True,r002f=False,retain_evidence=False)
            with patch.dict(os.environ),patch.object(observe,'controls',return_value='/synthetic/source-only-isolation'),\
                 patch.object(observe,'admit_plan',side_effect=ValueError('actual source refusal')),\
                 patch.object(observe,'run_bounded',side_effect=AssertionError('unadmitted native child launched')):
                self.assertEqual(observe.inside(args,runtime),0)
            result=p.load(task/'capture/lane-status'/(p.LANE+'.json'))
            self.assertEqual(result['nativeStatus'],'NOT_RUN');self.assertEqual(result['status'],'INCOMPLETE')


if __name__=='__main__':unittest.main(verbosity=2)
