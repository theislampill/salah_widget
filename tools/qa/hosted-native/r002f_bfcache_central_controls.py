#!/usr/bin/env python3
"""Native-free selector/currentness/producer controls; fixture receipts are not native evidence."""
import copy
import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def feature(test):
    source = HERE/'r002f_bfcache_central.py'
    test.assertTrue(source.is_file(), 'additive central route is not implemented')
    spec = importlib.util.spec_from_file_location('bfcache_central_under_test', source)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def campaign():
    return {'schemaVersion': 1, 'engine': 'chromium', 'r003fDpr': 1, 'workOrders': ['R002F'],
            'r002f': {'enabled': True, 'dpr': 1, 'rounds': 1, 'section': 'all'}, 'r002fRoute': 'bfcache-witness',
            'r003fHarness': 'published', 'r0040Mode': 'options', 'r0035Stages': False, 'r0035Costs': False,
            'r0035Psf': False, 'evidenceRetention': False}


class CentralControls(unittest.TestCase):
    def test_exact_selector_and_incompatible_route_populations(self):
        m = feature(self); self.assertTrue(m.campaign_selected(campaign()))
        for key, value in [('engine','firefox'),('workOrders',['R002F','R003F']),('r003fDpr',2),
                           ('r003fHarness','firefox-policy'),('r003fHarness','preconnect-input'),
                           ('r003fHarness','corrected-matrix'),('r0040Mode','capture-passive'),
                           ('r0040Mode','capture-mechanism'),('r0035Psf',True),('r0035Stages',True),
                           ('r0035Costs',True),('evidenceRetention',True)]:
            with self.subTest(key=key,value=value):
                bad = campaign(); bad[key] = value
                with self.assertRaises(ValueError): m.campaign_selected(bad)
        for route in ['offscreen','tabhide']:
            other = campaign(); other['r002fRoute'] = route; self.assertFalse(m.campaign_selected(other))

    def test_all_approved_aggregate_caps_sum_without_changing_original_waits(self):
        m = feature(self); b = m.budget()
        self.assertEqual(sum(b['phases'].values()),1680)
        self.assertEqual(60+b['childSeconds']+210+60+30,b['armSeconds'])
        self.assertEqual(2*b['armSeconds']+120,b['pairSeconds'])
        self.assertEqual(45+900+900+120+195,b['preparationSeconds'])
        self.assertEqual(45+120+b['pairSeconds']+120+75,b['namespaceSeconds'])
        self.assertEqual(b['preparationSeconds']+120+b['namespaceSeconds']+120,b['coordinatorSeconds'])
        self.assertEqual(b['coordinatorSeconds']+60,b['workflowObservationMinutes']*60)
        self.assertEqual((b['workflowAcquisitionMinutes']+b['workflowObservationMinutes']+20)*60,9120)
        self.assertEqual(b['originalLaunchDefaultSeconds'],180)
        self.assertEqual(b['calibration'],'UNCALIBRATED_OUTER_CEILINGS')

    def test_one_pair_lane_keeps_exact_original_arguments_and_unique_new_status(self):
        m = feature(self); task = Path('/private/current-task'); runtime = {k:'/actual/'+k for k in ('node','python','modules','playwright','pngjs')}; runtime['engine']='chromium'
        admission = {'status':'PASS','protocol':m.ADMISSION,'native':True,'task':str(task)}
        lane = m.make_lane(task,runtime,admission)
        self.assertEqual(lane['id'],'r002f-bfcache-chromium-dpr1'); self.assertEqual(lane['timeoutSeconds'],4200)
        self.assertEqual(lane['postObservationCheckSeconds'],120)
        self.assertEqual(lane['argv'],[runtime['node'],str(HERE/'r002f_bfcache.cjs'),'--task',str(task),'--out',str(task/'capture/lanes/r002f-bfcache-chromium-dpr1')])
        for arm in ('baseline','candidate'):
            args=m.child_argv(runtime,'/actual/root','/actual/out',arm)
            self.assertEqual(args[1:3],['--require',str(HERE/'r002f_bfcache_preload.cjs')])
            self.assertEqual(args[-7:],['/actual/root','/actual/out','chromium','bfcache','2026-11-18T16:30:00Z','3','--label='+arm])
        self.assertEqual(lane['exitStatuses']['0'],'OBSERVED_BFCACHE_DIAGNOSTIC')
        self.assertEqual(lane['result']['kind'],m.KIND)

    def test_missing_or_source_only_preparation_cannot_create_native_argv(self):
        m = feature(self); task=Path('/private/task'); runtime={'node':'/actual/node'}
        for admission in [None,{'status':'INCOMPLETE'},{'status':'PASS','native':False},
                          {'status':'PASS','native':True,'protocol':m.ADMISSION,'task':'/relocated/task'}]:
            lane=m.make_lane(task,runtime,admission); self.assertEqual(lane['argv'],[])

    def test_currentness_requires_literal_current_tool_task_and_six_key_runtime(self):
        m = feature(self)
        with tempfile.TemporaryDirectory() as directory:
            task=Path(directory); (task/'capture/r002f-bfcache-tools').mkdir(parents=True)
            runtime={k:str(task/k) for k in ('node','python','modules','playwright','pngjs')};runtime['engine']='chromium'
            (task/'runtime.json').write_text(json.dumps(runtime))
            with self.assertRaises(ValueError):m.tools_current(task,runtime)

    def test_terminal_summary_never_admits_VOID_missing_arm_cleanup_or_changed_qualification(self):
        m=feature(self)
        good={'protocol':m.RESULT,'status':m.STATUS,'nativeQualification':m.QUALIFICATION,'humanAcceptance':'OUTSTANDING',
              'timingClass':m.TIMING,'timingComparableToOriginal':False,'captureCallsAdded':0,'errors':[],
              'arms':[{'label':arm,'status':'COMPLETE','originalValid':True,'originalVerdict':'an adverse original result'} for arm in ('baseline','candidate')]}
        self.assertTrue(m.summary_shape(good))
        for change in [{'status':'PASS'},{'arms':good['arms'][:1]},{'nativeQualification':'R002F_ACCEPTED'},
                       {'humanAcceptance':'PASS'},{'captureCallsAdded':1},{'timingComparableToOriginal':True},{'errors':['cleanup failed']}]:
            self.assertFalse(m.summary_shape({**good,**change}))
        bad=copy.deepcopy(good);bad['arms'][1]['originalValid']=False;bad['arms'][1]['originalVerdict']='VOID';self.assertFalse(m.summary_shape(bad))

    def test_process_success_requires_actual_integer_zero_bound_cwd_and_argv(self):
        m=feature(self);args=['/actual/node','source.cjs'];good={'argv':args,'cwd':str(HERE),'timeoutSeconds':4200,'returncode':0,'timedOut':False,'elapsedSeconds':3}
        m.process_success(good,args,4200)
        for delta in [{'returncode':False},{'returncode':1},{'timedOut':True},{'timeoutSeconds':1},{'cwd':'/relocated'},
                      {'argv':['node','source.cjs']},{'elapsedSeconds':4201},{'elapsedSeconds':float('nan')},{'error':'actual failure'}]:
            with self.subTest(delta=delta),self.assertRaises(ValueError):m.process_success({**good,**delta},args,4200)

    def test_pipeline_refuses_cross_route_diagnostic_status_and_absent_currentness(self):
        m=feature(self);row={'id':'r002f-bfcache-chromium-dpr1','status':m.STATUS,'returncode':0,'timedOut':False}
        self.assertFalse(m.pipeline_admitted({'r002fRoute':'offscreen'}, {}, {}, {}, row, Path('/private/task')))
        self.assertFalse(m.pipeline_admitted(campaign(), {}, {}, {}, row, Path('/private/task')))

    def test_source_closure_declares_original_leaves_actual_callers_and_capability_fixture(self):
        m=feature(self);files=set(m.source_files())
        for name in ['tools/qa/r0041/real-witness.cjs','tools/qa/r0041/iso.cjs','tools/qa/r0041/png.cjs',
                     '.github/workflows/research-native-pilot.yml','tools/qa/hosted-native/acquire.sh',
                     'tools/qa/hosted-native/observe.py','tools/qa/hosted-native/capture_pipeline.py',
                     'tools/qa/hosted-native/r002f_bfcache_tools.py','tools/qa/hosted-native/fixtures/r002f-bfcache-decode-control.webm',
                     'tools/qa/hosted-native/r0040_autoattach_central.py','tools/qa/hosted-native/r0040_autoattach.cjs',
                     'tools/qa/hosted-native/r0040_autoattach_network.cjs','tools/qa/hosted-native/r0040_mechanism.cjs',
                     'tools/qa/hosted-native/r0040_mechanism_bracket.cjs','tools/qa/hosted-native/r0040_mechanism_network.cjs',
                     'tools/qa/hosted-native/r0040_passive.cjs','tools/qa/hosted-native/r0040_passive_sampler.cjs',
                     'tools/qa/hosted-native/r0040_passive_runtime.cjs','tools/qa/hosted-native/r0040_dateonly.cjs',
                     'tools/qa/hosted-native/retain_r0040_capture.cjs','tools/qa/hosted-native/retain_r0040.cjs',
                     'tools/qa/hosted-native/retention-pins.json','docs/state-contracts/R0040-native-capture-preflight.md',
                     'docs/state-contracts/evidence/R0040/native-capture-preflight.json']:
            self.assertIn(name,files)
        self.assertEqual(len(files),len(m.source_files()))

    def test_both_new_routes_bind_acquisition_and_observation_to_the_complete_merged_closure(self):
        import capture_pipeline as P
        import r0040_autoattach_central as automatic
        m=feature(self)
        with tempfile.TemporaryDirectory() as directory:
            task=Path(directory)/'task';task.mkdir(mode=0o700)
            roots={k:Path(directory)/k for k in ('research','baseline','historical')}
            for root in roots.values():root.mkdir()
            load=P.load
            for selected in (campaign(),{'engine':'chromium','workOrders':['R0040'],'r0040Mode':automatic.MODE,'r002f':{'enabled':False}}):
                with patch.object(P,'load',side_effect=lambda file: selected if Path(file)==P.HERE/'campaign.json' else load(file)):
                    for phase in ('acquisition','observation'):
                        actual=P.producer_identity(phase,task,roots)['sources']
                        self.assertEqual(set(actual),set(m.producer_source_files()))
                        for name in m.producer_source_files():self.assertEqual(actual[name],hashlib.sha256((HERE/name).read_bytes()).hexdigest())
                        self.assertIn('r0040_autoattach.cjs',actual)
                        self.assertIn('r002f_bfcache_preload.cjs',actual)
            with patch.object(P,'load',return_value={'workOrders':['R0040'],'r0040Mode':'capture-mechanism'}):
                self.assertEqual(set(P.producer_identity('acquisition',task,roots)['sources']),{'capture_pipeline.py','acquire.sh','campaign.json'})

    def test_actual_retained_currentness_refusal_requires_original_bytes_exact_invocation_and_phase(self):
        m=feature(self)
        self.assertTrue(hasattr(m,'admit_currentness_reference'),'retained actual currentness gate is missing')
        with tempfile.TemporaryDirectory() as directory:
            task=Path(directory);folder=task/'capture/currentness'/('outer-'+m.LANE+'-fixture');folder.mkdir(parents=True)
            runtime={k:str(task/k) for k in ('node','python','modules','playwright','pngjs')};runtime['engine']='chromium'
            lane=m.make_lane(task,runtime,{'protocol':m.ADMISSION,'status':'PASS','native':True,'task':str(task)})
            check={'argv':[runtime['python'],'-B',str(HERE/'r002f_bfcache_central.py'),'readmit'],'cwd':str(HERE),
                   'timeoutSeconds':120,'returncode':2,'timedOut':False,'elapsedSeconds':.02,'stdout':'','stderr':'source-control refusal\n'}
            streams={}
            for key in ('stdout','stderr'):
                file=folder/key;file.write_bytes(check[key].encode());streams[key]={'path':str(file),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
            value={'protocol':'salah-returned-currentness/1','phase':'outer','lane':m.LANE,'workOrder':'R002F','process':check,
                   'streams':streams,'knownReturnedRefusal':True,'scope':'SOURCE_CONTROL_ONLY'}
            receipt=folder/'process.json';receipt.write_text(json.dumps(value));ref={'path':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest()}
            self.assertTrue(m.admit_currentness_reference(task,lane,runtime,check,ref,'outer',refused=True))
            for delta in [{'returncode':False},{'returncode':-9},{'timedOut':None},{'argv':['/rebound/python']},{'cwd':'/elsewhere'},{'timeoutSeconds':121}]:
                with self.subTest(delta=delta),self.assertRaises(ValueError):
                    m.admit_currentness_reference(task,lane,runtime,{**check,**delta},ref,'outer',refused=True)
            (folder/'stderr').write_bytes(b'rewritten refusal\n')
            with self.assertRaises(ValueError):m.admit_currentness_reference(task,lane,runtime,check,ref,'outer',refused=True)

    def test_intake_process_requires_exact_post_command_directory_bound_streams_and_reaped_group(self):
        m=feature(self);self.assertTrue(hasattr(m,'admit_intake_process'),'actual complete-pair process gate is missing')
        argv=['/actual/node',str(HERE/'r002f_bfcache.cjs'),'--admit','--task','/task','--out','/task/capture/lanes/'+m.LANE]
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);streams={}
            for key in ('stdout','stderr'):
                file=folder/('complete-pair.'+key);file.write_bytes(b'{}\n' if key=='stdout' else b'');streams[key]=m.record(file)
            check={'argv':argv,'cwd':str(folder),'timeoutSeconds':60,'returncode':0,'timedOut':False,'elapsedSeconds':1,
                   'complete':True,'overflow':False,'groupStopped':True,'streams':streams}
            m.admit_intake_process(check,argv,folder)
            for delta in [{'argv':['node','different.cjs']},{'cwd':'/relocated'},{'timeoutSeconds':120},{'returncode':False},
                          {'groupStopped':False},{'overflow':True},{'complete':False},{'elapsedSeconds':61}]:
                with self.subTest(delta=delta),self.assertRaises(ValueError):m.admit_intake_process({**check,**delta},argv,folder)

    def test_actual_campaign_planner_and_coordinator_select_one_pair_with_original_arguments(self):
        import observe,lanes
        with tempfile.TemporaryDirectory() as directory:
            task=Path(directory);file=task/'campaign.json';file.write_text(json.dumps(campaign()))
            value=observe.read_campaign(file);self.assertEqual(value,campaign())
            self.assertEqual(observe.campaign_budget(value),{'coordinatorSeconds':6960,'workflowObservationMinutes':117,'workflowAcquisitionMinutes':15})
            prepared={'trees':{k:{'root':str(task/'source'/k)} for k in ('main','r0035','r003f','r0040')}}
            runtime={k:str(task/'acquired'/k) for k in ('node','python','modules')};runtime.update(playwright=runtime['modules']+'/playwright',pngjs=runtime['modules']+'/pngjs',engine='chromium')
            plan=lanes.make_plan(prepared,task/'capture/lanes',python_playwright=Path(runtime['python']),node=Path(runtime['node']),
                node_modules=Path(runtime['modules']),pngjs=Path(runtime['pngjs']),engine='chromium',include_r002f=True,
                work_orders=['R002F'],r002f_route='bfcache-witness',r002f_preparation={'status':'INCOMPLETE','reason':'source-control missing native preparation'})
            args=SimpleNamespace(task=task,engine='chromium',work_orders=['R002F'],r002f=True,r002f_dpr=1,r002f_rounds=1,
                r002f_section='all',r002f_route='bfcache-witness',research=task/'research',baseline=task/'baseline',historical=task/'historical')
            self.assertEqual(observe.admit_plan(plan,args,runtime),plan['lanes']);self.assertEqual(plan['lanes'][0]['argv'],[])
            for key,change in [('timeoutSeconds',4199),('postObservationCheckSeconds',121),('engine','firefox'),('argv',['/invented/native'])]:
                changed=copy.deepcopy(plan);changed['lanes'][0][key]=change
                with self.subTest(key=key),self.assertRaises(ValueError):observe.admit_plan(changed,args,runtime)
            with patch.object(observe,'run_bounded',side_effect=AssertionError('source selection cannot launch namespace')):
                command=observe.isolated_command(args,runtime,'lane',plan['lanes'][0]['id'])
            self.assertIn('bfcache-witness',command);self.assertIn('--r002f-route',command)

    def test_selected_tools_refusal_precedes_unchanged_shared_chromium_boundary(self):
        import observe
        args=SimpleNamespace(task=Path('/source-control/task'),engine='chromium',work_orders=['R002F'],r002f=True,
                             r002f_route='bfcache-witness',lane=None)
        with patch.object(observe.bfcache,'tools_current',side_effect=ValueError('actual capability missing')) as gate,\
             patch.object(observe,'controls',side_effect=AssertionError('boundary must not start')) as boundary,\
             self.assertRaisesRegex(ValueError,'actual capability missing'):
            observe.inside(args,{'engine':'chromium'})
        gate.assert_called_once();boundary.assert_not_called()

    def test_complete_namespace_receipt_stays_distinct_from_generic_or_original_acceptance(self):
        import observe
        m=observe.bfcache;runtime={k:'/actual/'+k for k in ('node','python','modules','playwright','pngjs')};runtime['engine']='chromium'
        lane=m.make_lane('/private/task',runtime,None);inner={'id':m.LANE,'status':m.STATUS,'returncode':0,'timedOut':False,'stopAll':False,
            'nativeQualification':m.QUALIFICATION,'humanAcceptance':'OUTSTANDING','timingClass':m.TIMING,'bfcacheIntake':{'result':{'status':'COMPLETE'}}}
        process={'returncode':0,'timedOut':False,'elapsedSeconds':1}
        self.assertEqual(observe.namespace_status(lane,process,inner)['status'],m.STATUS)
        for delta in [{'status':'PASS'},{'humanAcceptance':'PASS'},{'returncode':False},{'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY'}]:
            self.assertEqual(observe.namespace_status(lane,process,{**inner,**delta})['status'],'ISOLATION_UNCONFIRMED')
        self.assertEqual(observe.namespace_status({'id':m.LANE,'result':{'kind':'r002f-tabhide'}},process,inner)['status'],'ISOLATION_UNCONFIRMED')

    def test_readmission_cannot_execute_a_jointly_rebound_runtime_interpreter(self):
        m=feature(self)
        with tempfile.TemporaryDirectory() as directory:
            task=Path(directory);(task/'capture/r002f-bfcache-tools').mkdir(parents=True)
            runtime={k:str(task/k) for k in ('node','python','modules','playwright','pngjs')};runtime.update(python=sys.executable,engine='chromium')
            (task/'runtime.json').write_text(json.dumps(runtime))
            receipt=task/'capture/r002f-bfcache-tools/receipt.json';receipt.write_text(json.dumps({'acquired':{'runtime':runtime,'python':m.record(sys.executable,system=True)}}))
            m.runtime_authority(task,runtime)
            wrong={**runtime,'python':str(task/'other-python')};(task/'runtime.json').write_text(json.dumps(wrong))
            body=json.loads(receipt.read_text());body['acquired']['runtime']=wrong;receipt.write_text(json.dumps(body))
            with patch('r003f_diagnostics.bounded',side_effect=AssertionError('must refuse before execution')),self.assertRaises(ValueError):m.readmit(task,wrong)

    def test_unselected_campaign_preserves_existing_budget_and_skips_new_acquisition(self):
        import observe,capture_pipeline
        m=observe.bfcache;original=observe.read_campaign(HERE/'campaign.json')
        self.assertEqual(original['r002fRoute'],'tabhide');self.assertFalse(m.campaign_selected(original))
        budget=observe.campaign_budget(original);self.assertNotIn('workflowAcquisitionMinutes',budget)
        with patch.object(m,'tools_current',side_effect=AssertionError('unselected tools must not run')):
            self.assertTrue(m.pipeline_admitted(original,{}, {},{'result':{'kind':'r002f-tabhide'}},{'status':'OBSERVED_TABHIDE_DIAGNOSTIC'},Path('/task')))
        self.assertFalse(m.pipeline_admitted(original,{}, {},{'result':{'kind':'r002f-tabhide'}},{'status':m.STATUS},Path('/task')))

    def test_complete_pipeline_requires_all_coupled_original_process_and_currentness_receipts(self):
        import observe,capture_pipeline as P
        m=observe.bfcache
        # All process/event fields below are synthetic contract fixtures. No browser or namespace is run.
        with tempfile.TemporaryDirectory() as directory:
            task=Path(directory)/'task';p=m.paths(task);p['output'].mkdir(parents=True);(p['capture']/'lane-status').mkdir()
            runtime={k:str(task/k) for k in ('node','python','modules','playwright','pngjs')};runtime['engine']='chromium'
            (task/'runtime.json').write_text(json.dumps(runtime))
            admission={'protocol':m.ADMISSION,'status':'PASS','native':True,'task':str(task),'scope':'SOURCE_CONTROL_ONLY'}
            lane=m.make_lane(task,runtime,admission)
            result={'protocol':m.RESULT,'status':m.STATUS,'nativeQualification':m.QUALIFICATION,'humanAcceptance':'OUTSTANDING',
                'timingClass':m.TIMING,'timingComparableToOriginal':False,'captureCallsAdded':0,'errors':[],
                'arms':[{'label':label,'status':'COMPLETE','originalValid':True,'originalVerdict':'retained adverse original fixture verdict'} for label in ('baseline','candidate')]}
            def write(file,value):
                file=Path(file);file.parent.mkdir(parents=True,exist_ok=True);file.write_text(json.dumps(value));return m.record(file)
            pair=write(p['result'],result)
            for key in ('stdout','stderr'):Path(lane[key]).write_bytes(b'source-control entry\n' if key=='stdout' else b'')
            entry={'argv':lane['argv'],'cwd':str(HERE),'timeoutSeconds':4200,'returncode':0,'timedOut':False,'elapsedSeconds':3,
                   'streams':{key:m.record(lane[key]) for key in ('stdout','stderr')}}
            entry_record=write(p['entryProcess'],entry)
            def current(phase):
                check={'argv':[runtime['python'],'-B',str(HERE/'r002f_bfcache_central.py'),'readmit'],'cwd':str(HERE),'timeoutSeconds':120,
                       'returncode':0,'timedOut':False,'elapsedSeconds':.1,'stdout':json.dumps(admission),'stderr':''}
                args=SimpleNamespace(task=task,inside=phase=='inner')
                return observe.retain_currentness(args,lane,{**check,'stdoutBytes':check['stdout'].encode(),'stderrBytes':b''},check['argv'],120)[:2]
            outer,outer_ref=current('outer');inner_check,inner_ref=current('inner')
            folder=p['capture']/'r002f-bfcache-intake';folder.mkdir()
            post={**outer,'timeoutSeconds':60};post_streams={}
            for key in ('stdout','stderr'):
                file=folder/('source-current.'+key);file.write_bytes(post[key].encode());post_streams[key]=m.record(file)
            post_record=write(folder/'source-current-process.json',{**post,'streams':post_streams})
            intake={'protocol':'r002f-bfcache-final-intake/1','status':'COMPLETE','pair':pair,'nativeQualification':m.QUALIFICATION,
                    'humanAcceptance':'OUTSTANDING','arms':[{'label':'baseline'},{'label':'candidate'}]}
            streams={}
            for key in ('stdout','stderr'):
                file=folder/('complete-pair.'+key);file.write_bytes(json.dumps(intake).encode() if key=='stdout' else b'');streams[key]=m.record(file)
            check={'argv':[runtime['node'],str(HERE/'r002f_bfcache.cjs'),'--admit','--task',str(task),'--out',str(p['output'])],
                   'cwd':str(folder),'timeoutSeconds':60,'returncode':0,'timedOut':False,'elapsedSeconds':1,'complete':True,'overflow':False,
                   'groupStopped':True,'streams':streams}
            proof={'process':write(folder/'process.json',check),'result':intake,'pair':pair,'entry':entry_record,'sourceCheck':post_record,'elapsedSeconds':2}
            inner={'id':m.LANE,'status':m.STATUS,'returncode':0,'timedOut':False,'stopAll':False,'nativeQualification':m.QUALIFICATION,
                   'humanAcceptance':'OUTSTANDING','timingClass':m.TIMING,'bfcacheIntake':proof,
                   'preExecutionCurrentness':inner_check,'preExecutionCurrentnessReceipt':inner_ref}
            write(p['capture']/'lane-status'/(m.LANE+'.json'),inner)
            row={**observe.namespace_status(lane,{'returncode':0,'timedOut':False,'elapsedSeconds':1},inner),
                 'workOrder':'R002F','outerCurrentness':outer,'outerCurrentnessReceipt':outer_ref}
            plan={'r002fRoute':m.MODE,'lanes':[lane]};body={'r002fRoute':m.MODE}
            with patch.object(m,'tools_current',return_value={'scope':'SOURCE_CONTROL_ONLY'}):
                self.assertTrue(m.pipeline_admitted(campaign(),plan,body,lane,row,task))
                # Enter the real shared producer gate, without keys, sealing, or a browser.
                # Only the campaign/tool authorities are disclosed synthetic source fixtures.
                roots={k:Path(directory)/k for k in ('research','baseline','historical')}
                for root in roots.values():root.mkdir()
                task.chmod(0o700);p['capture'].chmod(0o700)
                producer=p['capture']/'producer-control';producer.mkdir()
                actual_load=P.load
                def source_fixture_load(file,*args):
                    return campaign() if Path(file)==P.HERE/'campaign.json' else actual_load(file,*args)
                plan.update(protocol='salah-hosted-native-lanes/1',sequential=True,workOrders=['R002F'])
                body.update(protocol='salah-hosted-native-observation/1',engine='chromium',workOrders=['R002F'],
                            preparation={'returncode':0,'timedOut':False,'elapsedSeconds':1},lanes=[row],status='OBSERVED')
                with patch.object(P,'load',side_effect=source_fixture_load):
                    for phase in ('acquisition','observation'):
                        identity=P.producer_identity(phase,task,roots)
                        self.assertIn('r002f_bfcache_preload.cjs',identity['sources'])
                        start={'protocol':P.PRODUCER_PROTOCOL,'phase':phase,'identity':identity}
                        write(producer/(phase+'-started.json'),start)
                        write(producer/(phase+'-completed.json'),{**start,'returned':True,'interrupted':False,
                              'process':{'returncode':0,'elapsedSeconds':1}})
                    write(p['capture']/'lanes.json',plan);write(p['capture']/'observation.json',body)
                    self.assertEqual(P.admit_producers(task,roots),'COMPLETED_OBSERVATION')
                    with patch.object(m,'pipeline_admitted',return_value=False),self.assertRaises(P.Rejected):
                        P.admit_producers(task,roots)
                    wrong=copy.deepcopy(body);wrong['lanes'][0]['status']='PASS'
                    write(p['capture']/'observation.json',wrong)
                    with self.assertRaises(P.Rejected):P.admit_producers(task,roots)
                    write(p['capture']/'observation.json',body)
                for delta in [{'status':'PASS'},{'humanAcceptance':'PASS'},{'outerCurrentnessReceipt':{}},{'bfcacheIntake':{}},
                              {'namespaceProcess':{'returncode':1,'timedOut':False}},{'innerStatus':None}]:
                    with self.subTest(delta=delta):self.assertFalse(m.pipeline_admitted(campaign(),plan,body,lane,{**row,**delta},task))
                # Jointly rewriting a process and its referenced hash still cannot alter the declared bound.
                altered={**check,'timeoutSeconds':120};proof['process']=write(folder/'process.json',altered)
                write(p['capture']/'lane-status'/(m.LANE+'.json'),inner)
                row['bfcacheIntake']=proof;row['innerStatus']=copy.deepcopy(inner)
                self.assertFalse(m.pipeline_admitted(campaign(),plan,body,lane,row,task))

    def test_sparse_population_covers_every_selected_runtime_source_and_python_import(self):
        import ast
        import re
        import r0040_autoattach_central as automatic
        m=feature(self);declared=set(m.source_files());root=HERE.parents[2]
        self.assertEqual(sorted(declared),json.loads((HERE/'r002f-bfcache-pins.json').read_text())['sourceFiles'])
        for name in automatic.verify_sources():self.assertIn('tools/qa/hosted-native/'+name,declared)
        for name in json.loads((HERE/'r002f-tabhide-pins.json').read_text())['modules']:
            self.assertIn('tools/qa/hosted-native/'+name,declared)
        yaml=(root/'.github/workflows/research-native-pilot.yml').read_text()
        block=yaml.split('sparse-checkout: |',1)[1].split('      - name:',1)[0]
        patterns=[line.strip().lstrip('/') for line in block.splitlines() if line.strip().startswith('/')]
        for name in declared:
            self.assertTrue(any(name.startswith(p) if p.endswith('/') else name==p for p in patterns),name)
        for name in declared:
            file=root/name
            self.assertTrue(file.is_file() and not file.is_symlink(),name)
            if file.suffix=='.cjs':
                for literal in re.findall(r"require\(['\"](\.[^'\"]+)['\"]\)",file.read_text()):
                    target=(file.parent/literal).resolve()
                    self.assertTrue(target.is_file(),str(target))
                    self.assertIn(target.relative_to(root).as_posix(),declared)
            if file.suffix!='.py' or not file.is_file():continue
            for node in ast.walk(ast.parse(file.read_text())):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.module else []
                for imported in names:
                    local=HERE/(imported.split('.')[0]+'.py')
                    if local.is_file():self.assertIn(local.relative_to(root).as_posix(),declared)


if __name__=='__main__':unittest.main()
