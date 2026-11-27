"""Synthetic source/custody controls for bounded R0035 preparation costs."""
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

import r0035_cost_materialize as material
import r0035_stage_controls as base_controls

HERE=Path(__file__).resolve().parent


class CostControls(unittest.TestCase):
    def setUp(self):
        self.fixture=base_controls.StageEntryControls();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.root=self.fixture.root;self.driver=self.fixture.driver;self.driver_path=self.fixture.driver_path

    def observer(self):
        self.assertTrue((HERE/'observe_r0035_costs.py').is_file(), 'distinct cost observation entry has not been implemented')
        return importlib.import_module('observe_r0035_costs')

    def prepared(self):
        base,source,source_path=self.fixture.source_fixture()
        output=self.root/'costs';identity=self.root/'identity.json';plan_path=self.root/'plan.json'
        record=material.prepare(self.driver_path,source_path,output,identity,plan_path)
        return base,source,output,identity,json.loads(plan_path.read_bytes()),record

    def test_full_reversible_transform_and_exact_original_condition(self):
        for name in material.MODIFIED:
            raw=(HERE.parents[2]/name).read_bytes();changed,proof=material.transform(name,raw)
            self.assertTrue(proof['originalRecoveredExactly']);self.assertEqual(proof['sourceSha256'],material.digest(raw))
            with self.assertRaisesRegex(ValueError,'source drift'):material.transform(name,raw+b'\n')
            if name==material.LIVE:
                stage,_=material.stages.transform(name,raw);self.assertEqual(changed,stage)
                self.assertEqual(proof['costEdits'],[])

    def test_only_four_original_modules_and_one_collector_change_with_full_closure(self):
        base,source,out,identity,plan,record=self.prepared()
        admitted=material.admit(plan,self.driver,identity)
        self.assertEqual(set(record['changedFiles']),set(material.MODIFIED))
        self.assertEqual(record['addedFiles'],[material.HELPER]);self.assertEqual(admitted,record)
        claimed=copy.deepcopy(source)
        for label in ('unmodified','mitigated'):claimed['arms'][label]['root']=str(out)
        with self.assertRaisesRegex(ValueError,'lab build digest mismatch'):self.driver.check_plan(claimed)
        self.driver.check_plan(source)

    def test_changed_collector_and_rebound_source_population_cannot_be_admitted(self):
        base,source,out,identity,plan,record=self.prepared()
        (out/material.HELPER).write_bytes((out/material.HELPER).read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'source drift'):material.admit(plan,self.driver,identity)
        (out/material.HELPER).write_bytes(material.helper_bytes());(out/'unexpected').write_text('extra')
        with self.assertRaisesRegex(ValueError,'population'):material.admit(plan,self.driver,identity)

    def test_cost_trace_uses_existing_stage_domains_and_exposes_only_aggregate_buckets(self):
        observation=self.observer();trace=cost_trace(observation)
        result=observation.inspect(trace);row=result['epochs'][0]
        self.assertEqual(result['protocol'],'r0035-cost-intervals/1')
        self.assertEqual(row['preparationCosts']['status'],'COMPLETE')
        self.assertEqual(row['preparationCosts']['counts']['transportSamples'],95)
        self.assertEqual(row['preparationCosts']['stellarMeasuredMs'],2)
        self.assertEqual(row['preparationCosts']['replayMeasuredMs'],2.75)
        self.assertNotIn('transferLatency',row)

    def test_inconsistent_counts_domains_intervals_and_partial_claims_are_rejected(self):
        observation=self.observer();original=cost_trace(observation)
        def costs(trace):return next(e for e in trace['events'] if e['kind']=='prepare-reply')['worker']['costs']
        changes=[lambda c:c.update(clockDomain='page-performance-now-ms'),
                 lambda c:c['counts'].update(transportSamples=94),lambda c:c['counts'].update(referenceGaussianCalls=5),
                 lambda c:c['counts'].update(variablePixels=True),lambda c:c['buckets']['spectralFlux'].update(ms=50),
                 lambda c:c['buckets']['psfRaster'].update(failed=1),lambda c:c['buckets'].pop('centerRanking'),
                 lambda c:c.update(status='COLLECTING'),lambda c:c['faults'].update(clock=True)]
        for mutate in changes:
            trace=copy.deepcopy(original);mutate(costs(trace))
            with self.assertRaises(ValueError):observation.inspect(trace)

    def test_distinct_driver_composition_does_not_mutate_existing_stage_entry(self):
        observation=self.observer();import observe_r0035_stages as original
        entry=observation.entry_support()
        self.assertIs(entry.material,material);self.assertIs(entry.inspect,observation.inspect)
        self.assertIsNot(original.material,material);self.assertIsNot(original.inspect,observation.inspect)
        self.assertEqual(entry.__file__,str(HERE/'observe_r0035_costs.py'))

    def test_cost_population_and_failed_prefix_bind_existing_worker_stage_marks(self):
        observation=self.observer();original=cost_trace(observation)
        for kind,change in (('source-verified',{'projected':0}),('source-verified',{'preview':True}),
                            ('stars-prepared',{'stars':2}),('replay-prepared',{'sources':0}),
                            ('replay-prepared',{'variablePixels':2})):
            trace=copy.deepcopy(original);worker=next(e for e in trace['events'] if e['kind']=='prepare-reply')['worker']
            next(m for m in worker['marks'] if m['kind']==kind).update(change)
            with self.subTest(kind=kind,change=change),self.assertRaises(ValueError):observation.inspect(trace)
        trace=copy.deepcopy(original);reply=next(e for e in trace['events'] if e['kind']=='prepare-reply')
        reply['op']='failed';worker=reply['worker'];worker['marks']=worker['marks'][:5]+[{'kind':'failed','at':900008}]
        costs=worker['costs'];costs.update(status='FAILED',endedAt=900008,lastAt=900008)
        for name in observation.BUCKETS[2:]:costs['buckets'][name]={'calls':0,'completed':0,'failed':0,'ms':0}
        costs['counts'].update({name:0 for name in observation.COUNTS[9:]})
        self.assertEqual(observation.inspect(trace)['epochs'][0]['preparationCosts']['status'],'FAILED')
        costs['buckets']['centerRanking']={'calls':1,'completed':0,'failed':1,'ms':.1}
        with self.assertRaises(ValueError):observation.inspect(trace)

    def test_invalid_cost_prefix_is_retained_before_original_cleanup_and_failure(self):
        observation=self.observer();entry=observation.entry_support()
        trace=cost_trace(observation);next(e for e in trace['events'] if e['kind']=='prepare-reply')['worker']['costs']['counts']['transportSamples']=94
        observer=entry.Observer(self.root/'evidence',self.fixture.loader);observer.install(self.driver)
        args,arm,browser,api=self.fixture.trial_fixture(self.driver,label='unmodified',trace=trace)
        with patch.dict(sys.modules,{'playwright.sync_api':api}):
            result=self.driver.trial(browser,'chromium','http://127.0.0.1:8765',arm,'unmodified',self.root/'wrapped',args)
        retained=json.loads((self.root/'evidence/trial-001-unmodified.json').read_bytes())
        self.assertEqual(retained['protocol'],'r0035-cost-trial/1');self.assertTrue(retained['contextClosed'])
        self.assertEqual(retained['observations'][0]['trace'],trace)
        self.assertEqual(retained['observations'][0]['status'],'INCOMPLETE');self.assertTrue(observer.errors)
        self.assertEqual(result,json.loads((self.root/'wrapped/trial.json').read_bytes()))

    def test_actual_entry_refuses_missing_namespace_before_source_or_browser_access(self):
        self.observer();env=dict(os.environ);env.pop('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT',None)
        run=subprocess.run([sys.executable,'-B',str(HERE/'observe_r0035_costs.py'),'--driver',str(self.driver_path),
            '--identity','unopened','--preparation-process','unopened','--preparation-sha256','0'*64,
            '--evidence',str(self.root/'evidence'),'--','unopened',str(self.root/'output')],env=env,capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0);self.assertIn('admitted isolation receipt required',run.stderr)
        self.assertFalse((self.root/'evidence').exists())


def cost_trace(observation):
    trace=base_controls.stage_trace();worker=next(e for e in trace['events'] if e['kind']=='prepare-reply')['worker']
    # Existing source fixture has 3ms stellar and 5ms replay intervals. These
    # values are deliberately synthetic and remain within their worker domain.
    buckets={name:{'calls':1,'completed':1,'failed':0,'ms':1 if i<2 else .25}
             for i,name in enumerate(observation.BUCKETS)}
    counts=dict.fromkeys(observation.COUNTS,0)
    counts.update(fullInputSources=1,spectralSources=1,transportSamples=95,patchCalls=1,drawnPatches=1,
                  referencePsfChannels=3,referenceGaussianCalls=6,patchPixelsRequested=4,replayInputSources=1,
                  replaySelectedSources=1,envelopePatchPixelsScheduled=4,variablePixels=1,variablePatchOffsets=1,
                  inputGatherValues=6,withdrawalCenters=1,fullComposeCalls=3,centerComposeCalls=1)
    marks={r['kind']:r['at'] for r in worker['marks']}
    for row in worker['marks']:
        row.update({'source-verified':{'projected':1,'preview':False},'stars-prepared':{'stars':1},
                    'replay-prepared':{'sources':1,'variablePixels':1}}.get(row['kind'],{}))
    worker['costs']={'protocol':'r0035-worker-costs/1','clockDomain':'worker-performance-now-ms','epoch':worker['epoch'],
        'status':'COMPLETE','startedAt':worker['marks'][0]['at'],'endedAt':marks['candidate-returned'],
        'lastAt':marks['candidate-returned'],'active':None,'faults':dict.fromkeys(('clock','overlap','name','count','lifecycle'),False),
        'buckets':buckets,'counts':counts}
    return trace


if __name__=='__main__':unittest.main()
