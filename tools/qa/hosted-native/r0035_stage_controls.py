"""Offline admission/extraction controls for the explicitly instrumented lab."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import r0035_stage_materialize as material
import observe_r0035_stages as observation
import retention_controls as fixtures

HERE = Path(__file__).resolve().parent


class StageEntryControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='r0035-stages-'); self.root = Path(self.temp.name)
        self.loader = material.support(); self.driver_path = HERE.parents[1]/'r0035/native_trials.py'
        self.driver = self.loader.load_driver(self.driver_path)
        self.prior_umask = os.umask(0o077)
    def tearDown(self):
        os.umask(self.prior_umask); self.temp.cleanup()
    def test_stage_entries_exist(self):
        self.assertTrue((HERE/'r0035_stage_materialize.py').is_file())
        self.assertTrue((HERE/'observe_r0035_stages.py').is_file())

    def source_fixture(self):
        base, main = self.root/'base', self.root/'main'; base.mkdir(); main.mkdir()
        for name in material.pins()['files']:
            target=base/name; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((HERE.parents[2]/name).read_bytes())
        (base/'index.html').write_text('bounded lab entry')
        rows={name:row['sha256'] for name,row in material.inventory(base).items()}
        (base/'r0035-lab-identity.json').write_text(json.dumps({'sourceHead':material.pins()['researchCommit'],'sha256':rows}))
        (main/'index.html').write_text('bounded main entry')
        env=dict(os.environ,GIT_AUTHOR_NAME='Offline control',GIT_AUTHOR_EMAIL='control@example.invalid',
                 GIT_COMMITTER_NAME='Offline control',GIT_COMMITTER_EMAIL='control@example.invalid')
        for args in [['init','-q'],['add','index.html'],['commit','-qm','bounded source fixture']]:
            subprocess.run(['git','-C',str(main),*args],check=True,capture_output=True,env=env)
        head=subprocess.check_output(['git','-C',str(main),'rev-parse','HEAD'],text=True).strip()
        flags='&r35scope=all&r35amplitude=1&r35glass=0.5&r35margin=4&r35guard=off'
        plan={'kind':'independent-reconstruction','arms':{'main':{'root':str(main),'commit':head,'flags':''}}}
        for label,arm in [('unmodified','full'),('mitigated','changed')]:
            plan['arms'][label]={'root':str(base),'commit':material.pins()['researchCommit'],'flags':'&r35arm='+arm+flags,
                                 'producerProbe':{'path':'stars.status','equals':'active'}}
        plan_path=self.root/'original-plan.json';plan_path.write_text(json.dumps(plan))
        return base,plan,plan_path

    def prepared(self):
        base,plan,source=self.source_fixture();out=self.root/'derived';receipt=self.root/'identity.json';mapped=self.root/'mapped-plan.json'
        material.prepare(self.driver_path,source,out,receipt,mapped)
        return base,plan,out,receipt,json.loads(mapped.read_bytes())

    def test_exact_reversible_sources_and_source_drift(self):
        for name in (material.LIVE,material.WORKER):
            raw=(HERE.parents[2]/name).read_bytes();changed,proof=material.transform(name,raw)
            self.assertNotEqual(raw,changed);self.assertEqual(proof['sourceSha256'],hashlib.sha256(raw).hexdigest())
            with self.assertRaisesRegex(ValueError,'source drift'):material.transform(name,raw+b'\n')

    def test_missing_and_duplicate_seams_refuse_before_a_patch(self):
        raw=(HERE.parents[2]/material.LIVE).read_bytes()
        for seam in ('not an original seam','return'):
            with patch.object(material,'replacements',return_value={material.LIVE:[('bounded',seam,'replacement')]}):
                with self.assertRaisesRegex(ValueError,'missing or duplicate'):material.transform(material.LIVE,raw)

    def test_distinct_derivative_admission_keeps_original_checker_strict(self):
        base,plan,out,receipt,mapped=self.prepared()
        self.assertEqual((base/'r0035-lab-identity.json').read_bytes(),(out/'r0035-lab-identity.json').read_bytes())
        claimed_original=copy.deepcopy(plan)
        for label in ('unmodified','mitigated'):claimed_original['arms'][label]['root']=str(out)
        with self.assertRaisesRegex(ValueError,'lab build digest mismatch'):self.driver.check_plan(claimed_original)
        record=material.admit(mapped,self.driver,receipt)
        self.assertEqual(set(record['changedFiles']),{material.LIVE,material.WORKER})
        self.driver.check_plan(plan)
        for label in plan['arms']:
            expected=copy.deepcopy(plan['arms'][label])
            if label!='main':expected['root']=str(out)
            self.assertEqual(mapped['arms'][label],expected)

    def test_source_population_plan_and_receipt_drift_are_refused(self):
        base,plan,out,receipt,mapped=self.prepared()
        (out/'unrecorded').write_text('extra')
        with self.assertRaisesRegex(ValueError,'population'):material.admit(mapped,self.driver,receipt)
        (out/'unrecorded').unlink()
        altered=copy.deepcopy(mapped);altered['arms']['unmodified']['flags']+='&r35tile=32'
        with self.assertRaisesRegex(ValueError,'flags, probes or main'):material.admit(altered,self.driver,receipt)
        raw=receipt.read_bytes();body=json.loads(raw);body['status']='INCOMPLETE';receipt.write_text(json.dumps(body));altered=copy.deepcopy(mapped)
        altered['diagnostic']['sha256']=material.digest(receipt.read_bytes())
        with self.assertRaisesRegex(ValueError,'prepared diagnostic'):material.admit(altered,self.driver,receipt)
        receipt.write_bytes(raw);(base/material.LIVE).write_bytes((base/material.LIVE).read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'digest mismatch'):material.admit(mapped,self.driver,receipt)
        original_receipt=base/'r0035-lab-identity.json';body=json.loads(original_receipt.read_bytes());body['sha256']['../outside']='0'*64
        original_receipt.write_text(json.dumps(body))
        with patch.object(self.driver,'check_plan',side_effect=AssertionError('original checker should not read an unsafe path')):
            with self.assertRaisesRegex(ValueError,'unsafe original lab receipt path'):material.original_plan(self.driver,plan)

    def test_failed_materialization_preserves_partial_tree_and_failed_receipt(self):
        base,plan,source=self.source_fixture();real_copy=shutil.copy2
        def interrupted(src,dst,*args,**kwargs):
            result=real_copy(src,dst,*args,**kwargs)
            if Path(src).name=='index.html':raise OSError('bounded copy failure')
            return result
        with patch.object(material.shutil,'copy2',side_effect=interrupted):
            with self.assertRaisesRegex(OSError,'bounded copy failure'):
                material.prepare(self.driver_path,source,self.root/'partial',self.root/'identity.json',self.root/'mapped.json')
        self.assertTrue((self.root/'partial/index.html').exists())
        self.assertEqual(json.loads((self.root/'identity.json.failure.json').read_bytes())['status'],'INCOMPLETE')
        self.assertFalse((self.root/'mapped.json').exists())

    def test_rebound_receipt_cannot_authorize_an_unlisted_transformation(self):
        base,plan,out,receipt,mapped=self.prepared()
        # Even a newly hashed receipt cannot expand the identified transform.
        (out/'index.html').write_text('unexpected extra transformation')
        body=json.loads(receipt.read_bytes())
        data=(out/'index.html').read_bytes()
        body['files']['index.html']={'sha256':material.digest(data),'bytes':len(data)}
        raw=(json.dumps(body,indent=2)+'\n').encode()
        receipt.write_bytes(raw);(out/'r0035-stage-identity.json').write_bytes(raw)
        rebound=copy.deepcopy(mapped);rebound['diagnostic']['sha256']=material.digest(raw)
        with self.assertRaisesRegex(ValueError,'only the two identified stage modules'):
            material.admit(rebound,self.driver,receipt)

    def test_missing_overflow_and_mixed_clocks_cannot_supply_intervals(self):
        with self.assertRaisesRegex(ValueError,'missing'):observation.inspect(None)
        trace=stage_trace();trace['overflow']=True
        with self.assertRaisesRegex(ValueError,'overflow'):observation.inspect(trace)
        with self.assertRaisesRegex(ValueError,'mixed clock'):observation.elapsed({'at':1,'clockDomain':observation.MAIN_CLOCK},{'at':900001,'clockDomain':observation.WORKER_CLOCK})
        result=observation.inspect(stage_trace());row=result['epochs'][0]
        self.assertEqual(row['mainDurationsMs']['ownerToFirstPublication'],232)
        self.assertEqual(row['workerDurationsMs']['stellarPreparation'],3)
        self.assertNotIn('transferLatency',row)
        malformed=stage_trace();malformed['events'][5]['worker']['marks'].pop(4)
        with self.assertRaisesRegex(ValueError,'stage sequence'):observation.inspect(malformed)
        trace=stage_trace();trace['events'] += [{'kind':'owner','epoch':2,'at':500},{'kind':'owner','epoch':3,'at':600}]
        result=observation.inspect(trace);self.assertTrue(result['epochs'][1]['supersededWithoutObservedDispatch'])
        self.assertIsNone(result['epochs'][1]['mainDurationsMs']['ownerToFirstPublication'])

    def trial_fixture(self,driver,label='main',bad=False,trace=None):
        args=types.SimpleNamespace(scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''),
            clock='ordinary',warmup=5,capture=False,seconds=15,observe_producer=True,scope=material.KIND,driver_sha256={},plan=Path('bounded-plan'),output=Path('bounded-output'))
        arm={'root':str(self.root),'commit':'a'*40,'flags':'','producerProbe':{'path':'stars.status','equals':'active'}}
        browser=fixtures.FakeBrowser(driver);evaluate=browser.context.page.evaluate
        def read(expression,*values):
            if expression==observation.READ_STAGES:
                self.assertTrue((self.root/'wrapped/trial.json').exists())
                self.assertEqual(browser.context.page.shots,0)
                return trace
            value=evaluate(expression,*values)
            if expression==driver.READ and bad:value['prayersReady']=False
            return value
        browser.context.page.evaluate=read
        api=types.ModuleType('playwright.sync_api');api.TimeoutError=fixtures.BrowserTimeout
        return args,arm,browser,api

    def test_actual_original_trial_reports_are_unchanged_and_stage_extraction_adds_no_capture(self):
        for bad in (False,True):
            with self.subTest(original_failure=bad):
                for name in ('baseline','wrapped','evidence'):
                    shutil.rmtree(self.root/name,ignore_errors=True)
                driver=self.loader.load_driver(self.driver_path)
                args,arm,browser,api=self.trial_fixture(driver,bad=bad)
                driver.time=types.SimpleNamespace(monotonic_ns=iter([0,2000000000]).__next__)
                with patch.dict(sys.modules,{'playwright.sync_api':api}):driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'main',self.root/'baseline',args)
                baseline=(self.root/'baseline/trial.json').read_bytes()
                observer=observation.Observer(self.root/'evidence',self.loader);observer.install(driver)
                args,arm,browser,api=self.trial_fixture(driver,bad=bad)
                driver.time=types.SimpleNamespace(monotonic_ns=iter([0,2000000000]).__next__)
                def written_after_close(path,value):
                    self.assertIn('close',browser.context.calls);return original_write(path,value)
                original_write=material.write_json
                with patch.dict(sys.modules,{'playwright.sync_api':api}),patch.object(material,'write_json',side_effect=written_after_close):
                    result=driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'main',self.root/'wrapped',args)
                self.assertEqual(baseline,(self.root/'wrapped/trial.json').read_bytes())
                self.assertEqual(result['qualification']['verdict'],'failed' if bad else 'passed')
                self.assertFalse(observer.errors);self.assertEqual(browser.context.page.shots,0)

    def test_extraction_failure_does_not_replace_an_original_trial_exception(self):
        marker=ValueError('original admission failure');driver=self.driver
        driver.assess=lambda *a,**k:(_ for _ in ()).throw(marker)
        observer=observation.Observer(self.root/'evidence',self.loader);observer.install(driver)
        args,arm,browser,api=self.trial_fixture(driver)
        original=browser.context.page.evaluate
        browser.context.page.evaluate=lambda expr,*a:(_ for _ in ()).throw(OSError('secondary observation failure')) if expr==observation.READ_STAGES else original(expr,*a)
        with patch.dict(sys.modules,{'playwright.sync_api':api}):
            with self.assertRaises(ValueError) as caught:driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'unmodified',self.root/'wrapped',args)
        self.assertIs(caught.exception,marker);self.assertIn('close',browser.context.calls)
        record=json.loads((self.root/'evidence/trial-001-unmodified.json').read_bytes())
        self.assertEqual(record['originalException']['message'],str(marker));self.assertEqual(record['observations'][0]['status'],'UNAVAILABLE')
        self.assertEqual(record['observations'][0]['extractionError']['message'],'secondary observation failure')
        self.assertIsNone(record['observations'][0]['trace'])

    def test_rejected_stage_prefix_survives_actual_original_cleanup_and_exception(self):
        for fault in ('overflow','missing-startup','worker-prefix','primary-exception'):
            with self.subTest(fault=fault):
                for name in ('wrapped','evidence'):shutil.rmtree(self.root/name,ignore_errors=True)
                driver=self.loader.load_driver(self.driver_path);trace=stage_trace()
                if fault in ('overflow','primary-exception'):trace['overflow']=True
                elif fault=='missing-startup':trace['events'].pop(0)
                else:trace['events'][5]['worker']['marks'].pop(4)
                marker=ValueError('original assessment failure')
                if fault=='primary-exception':driver.assess=lambda *a,**k:(_ for _ in ()).throw(marker)
                observer=observation.Observer(self.root/'evidence',self.loader);observer.install(driver)
                args,arm,browser,api=self.trial_fixture(driver,label='unmodified')
                original=browser.context.page.evaluate
                browser.context.page.evaluate=lambda expr,*args:trace if expr==observation.READ_STAGES else original(expr,*args)
                with patch.dict(sys.modules,{'playwright.sync_api':api}):
                    if fault=='primary-exception':
                        with self.assertRaises(ValueError) as caught:
                            driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'unmodified',self.root/'wrapped',args)
                        self.assertIs(caught.exception,marker);self.assertFalse((self.root/'wrapped/trial.json').exists())
                    else:
                        result=driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'unmodified',self.root/'wrapped',args)
                        self.assertEqual(json.loads((self.root/'wrapped/trial.json').read_bytes()),result)
                record=json.loads((self.root/'evidence/trial-001-unmodified.json').read_bytes())
                row=record['observations'][0]
                self.assertEqual(row['status'],'INCOMPLETE');self.assertEqual(row['trace'],trace)
                self.assertIn('validationError',row);self.assertNotIn('extractionError',row)
                self.assertTrue(record['contextClosed']);self.assertTrue(observer.errors)
                if fault=='primary-exception':self.assertEqual(record['originalException']['message'],str(marker))

    def test_experimental_stage_trace_is_extracted_after_the_actual_original_report(self):
        observer=observation.Observer(self.root/'evidence',self.loader);observer.install(self.driver)
        args,arm,browser,api=self.trial_fixture(self.driver,label='unmodified',trace=stage_trace())
        with patch.dict(sys.modules,{'playwright.sync_api':api}):
            self.driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'unmodified',self.root/'wrapped',args)
        record=json.loads((self.root/'evidence/trial-001-unmodified.json').read_bytes())
        self.assertFalse(observer.errors);self.assertEqual(browser.context.page.shots,0)
        self.assertEqual(record['observations'][0]['status'],'OBSERVED')
        self.assertEqual(record['observations'][0]['intervals']['epochs'][0]['workerDurationsMs']['stellarPreparation'],3)
        self.assertTrue(record['contextClosed'])
        self.assertEqual(record['originalReport']['sha256'],material.digest((self.root/'wrapped/trial.json').read_bytes()))

    def test_routes_precede_pages_and_unknown_external_continuation_is_vetoed(self):
        observer=observation.Observer(self.root/'evidence',self.loader);trial={'base':'http://127.0.0.1:8765','pages':[]}
        raw=fixtures.FakeBrowser(self.driver).context;context=observation.Context(raw,observer,trial)
        with self.assertRaisesRegex(ValueError,'route.*before'):context.new_page()
        self.assertEqual(raw.calls,[]);context.route('**/*',lambda route:route.continue_())
        route=fixtures.FakeRoute('https://unknown.invalid/data')
        with self.assertRaisesRegex(ValueError,'external continuation'):raw.handler(route)
        self.assertEqual(route.actions,['abort']);self.assertIsNotNone(observer.veto)

    def test_cli_isolation_refusal_precedes_source_plan_or_browser_loading(self):
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT',None)
        result=subprocess.run([sys.executable,'-B',str(HERE/'observe_r0035_stages.py'),'--driver',str(self.driver_path),
            '--identity','unopened-identity','--preparation-process','unopened-process','--preparation-sha256','0'*64,
            '--evidence',str(self.root/'evidence'),
            '--','unopened-plan',str(self.root/'out')],capture_output=True,text=True,env=env)
        self.assertNotEqual(result.returncode,0);self.assertIn('admitted isolation receipt required',result.stderr)
        self.assertFalse((self.root/'evidence').exists())

    def test_terminal_observation_failure_preserves_primary_status_and_veto_precedence(self):
        for mode in ('primary','exit','veto','secondary','primary-read','veto-read'):
            with self.subTest(mode=mode):
                evidence=self.root/mode;plan=self.root/(mode+'-plan.json');identity=self.root/(mode+'-identity.json')
                plan.write_text('{}');identity.write_text('{}');primary=ValueError('original driver failure')
                def run():
                    if mode.endswith('-read'):identity.unlink()
                    if mode.startswith('veto'):owners[0].veto=ValueError('prevented continuation')
                    if mode.startswith(('primary','veto')):raise primary
                    if mode=='exit':raise SystemExit(7)
                driver=types.SimpleNamespace(main=run,trial=lambda:None,check_plan=lambda p:None,verify_reconstructed_flags=lambda a:None)
                loader=types.SimpleNamespace(verify_isolation=lambda f:{},verify_inputs=lambda f:[],load_driver=lambda f:driver)
                owners=[];real_observer=observation.Observer
                def owner(*args):
                    value=real_observer(*args);owners.append(value);return value
                with patch.object(material,'support',return_value=loader),patch.object(material,'admit',return_value={}),\
                     patch.object(material,'preparation_process',return_value={}),\
                     patch.object(observation,'Observer',side_effect=owner),patch.object(material,'write_json',side_effect=OSError('terminal fsync failure')):
                    expected=SystemExit if mode.startswith('veto') or mode=='exit' else ValueError if mode.startswith('primary') else RuntimeError
                    with self.assertRaises(expected) as caught:
                        observation.main(['--driver',str(self.driver_path),'--identity',str(identity),'--preparation-process','unopened-process',
                                          '--preparation-sha256','0'*64,'--evidence',str(evidence),'--',str(plan),str(self.root/(mode+'-out'))])
                if mode.startswith('primary'):self.assertIs(caught.exception,primary)
                elif mode.startswith('veto') or mode=='exit':self.assertEqual(caught.exception.code,86 if mode.startswith('veto') else 7)


def stage_trace():
    marks=[('received',900000),('catalogue-start',900001),('catalogue-ready',900002),('source-verified',900004),
           ('stars-prepared',900007),('replay-prepared',900012),('nominal-verified',900013),('census-complete',900014),('candidate-returned',900014),('ready-post',900015)]
    return {'protocol':'r0035-stage-observation/1','clockDomain':observation.MAIN_CLOCK,'limit':2048,'overflow':False,
            'events':[{'kind':'installed','at':100},{'kind':'owner','at':200,'epoch':1},
                {'kind':'prepare-dispatch-start','at':210,'messageEpoch':1},{'kind':'prepare-message-built','at':212,'messageEpoch':1},
                {'kind':'prepare-dispatch-returned','at':213,'messageEpoch':1},
                {'kind':'prepare-reply','at':400,'op':'ready','messageEpoch':1,'activeEpoch':1,'terminal':False,
                 'worker':{'protocol':'r0035-worker-stages/1','clockDomain':observation.WORKER_CLOCK,'epoch':1,'marks':[{'kind':k,'at':t} for k,t in marks]}},
                {'kind':'first-sample-request','at':416,'epoch':1},{'kind':'first-publication','at':432,'epoch':1}]}


if __name__ == '__main__': unittest.main()
