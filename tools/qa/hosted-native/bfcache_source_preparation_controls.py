"""Fixed BF source-only controls. Fixtures supply no native or genuine preparation authority."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import signal
import sys
import re
import contextlib
import io
from unittest.mock import patch

import bfcache_source_preparation as subject


class FixedSourceControls(unittest.TestCase):
    def setUp(self):
        retained=os.environ.get('SALAH_CONTROL_ROOT')
        if retained:self.root=Path(tempfile.mkdtemp(prefix='source-',dir=retained))
        else:
            temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.task=self.root/'task';self.task.mkdir(mode=0o700)
        self.roots={name:self.root/name for name in subject.ROLES}
        self.roots['harness']=self.root/'source-preparation'
        self.runtime={'python':str(self.task/'source-runtime/python/bin/python'),'node':'/fixed/bin/node',
                      'modules':str(self.task/'source-runtime/node/node_modules'),
                      'playwright':str(self.task/'source-runtime/node/node_modules/playwright'),
                      'pngjs':str(self.task/'source-runtime/node/node_modules/pngjs')}

    def physical_fixture(self):
        root=self.root/'physical';root.mkdir(mode=0o700)
        rows={};physical={}
        for i in range(111):
            name=f'inputs/source-{i:03}.txt';p=root/name;p.parent.mkdir(exist_ok=True)
            raw=('fixture '+str(i)).encode();p.write_bytes(raw);p.chmod(0o755 if i==1 else 0o644)
            rows[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                        'gitBlob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
                        'mode':'100755' if i==1 else '100644'}
            physical[name]=subject.physical_file_record(p)
        compact={'protocol':'source-only-declared-git-inputs/1','root':str(root),'commit':'a'*40,
                 'tree':'b'*40,'clean':True,'files':rows}
        original={'protocol':'r002f-bfcache-current-source/1',**{k:compact[k] for k in ('root','commit','tree','clean')},
                  'files':copy.deepcopy(physical)}
        return compact,physical,original

    def test_original_common_and_r002f_argv_and_bounds_are_exact(self):
        here=self.roots['target']/'tools/qa/hosted-native'
        common=subject.command_for_phase('common',self.task,self.roots,self.runtime)
        self.assertEqual(common,{'argv':[self.runtime['python'],str(here/'prepare.py'),'--research',str(self.roots['research']),
            '--baseline',str(self.roots['baseline']),'--historical',str(self.roots['historical']),'--out',str(self.task/'work/prepared')],
            'cwd':str(here),'timeoutSeconds':900})
        derived=subject.command_for_phase('r002f',self.task,self.roots,self.runtime)
        self.assertEqual(derived,{'argv':[self.runtime['python'],str(here/'r002f_prepare.py'),'--research',str(self.roots['research']),
            '--baseline',str(self.roots['baseline']),'--out',str(self.task/'work/r002f-prepared'),'--node',self.runtime['node']],
            'cwd':str(here),'timeoutSeconds':900})

    def test_only_fixed_source_children_and_original_central_refusal_exist(self):
        here=self.roots['target']/'tools/qa/hosted-native';collector=self.roots['harness']/'tools/qa/hosted-native/bfcache_source_preparation.py'
        for phase in ('check-source','refuse-native-common'):
            self.assertEqual(subject.command_for_phase(phase,self.task,self.roots,self.runtime),
                {'argv':[self.runtime['python'],'-B',str(collector),phase,'--task',str(self.task),'--workspace',str(self.root)],
                 'cwd':str(here),'timeoutSeconds':120})
        self.assertEqual(subject.command_for_phase('central-no-runtime',self.task,self.roots,self.runtime),
            {'argv':[self.runtime['python'],'-B',str(here/'r002f_bfcache_central.py'),'admit','--task',str(self.task),'--native'],
             'cwd':str(here),'timeoutSeconds':120})
        for phase in ('derived','readmit','native','acquire','observe','arbitrary'):
            with self.subTest(phase=phase),self.assertRaises(ValueError):subject.command_for_phase(phase,self.task,self.roots,self.runtime)

    def test_original_source_population_extensions_are_exact(self):
        research=subject.source_paths('research');baseline=subject.source_paths('baseline')
        self.assertEqual(research,list(subject.SOURCE_DIRS)+['docs/state-contracts/evidence/R0040/phase1-options.patch.gz',
            'index.html','offline.html','config.js','builder.html','GENERATED.json','_config.yml',
            'docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json'])
        self.assertEqual(baseline,list(subject.SOURCE_DIRS)+['index.html','offline.html','config.js','builder.html','GENERATED.json',
            '.gitignore','_config.yml','docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json'])
        self.assertEqual(subject.source_paths('historical'),subject.HISTORICAL)
        with self.assertRaises(ValueError):subject.source_paths('target')

    def test_compact_and_full_physical_maps_join_without_dropping_fields(self):
        compact,physical,original=self.physical_fixture()
        self.assertNotEqual(compact['files'],original['files'])
        joined=subject.join_target_identity(compact,physical,original)
        self.assertEqual(subject.canonical(joined),subject.canonical(original))
        self.assertEqual(set(next(iter(joined['files'].values()))),{'path','resolvedPath','bytes','sha256','device','inode','links',
                         'mode','uid','mtimeNs','ctimeNs','system','symlinks'})

    def test_physical_join_rejects_changed_original_metadata_and_identity(self):
        compact,physical,original=self.physical_fixture();name=next(iter(physical))
        mutations={'path':'/other/source','resolvedPath':'/other/source','bytes':True,'sha256':'0'*64,
                   'device':'different','inode':'different','links':2,'mode':0o600,'uid':True,
                   'mtimeNs':'different','ctimeNs':'different','system':True,'symlinks':[{'path':'alias','target':'elsewhere'}]}
        for key,value in mutations.items():
            changed=copy.deepcopy(original);changed['files'][name][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):subject.join_target_identity(compact,physical,changed)
        for key,value in (('commit','c'*40),('tree','d'*40),('root','/different'),('clean',1),('protocol','other')):
            changed=copy.deepcopy(original);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):subject.join_target_identity(compact,physical,changed)

    def test_matching_false_physical_path_mode_or_source_population_still_refuses(self):
        compact,physical,original=self.physical_fixture();name=next(iter(physical))
        for key,value in (('path','/other'),('resolvedPath','/other'),('links',True),('mode',0o600),('system',0),('symlinks',['alias'])):
            first=copy.deepcopy(physical);second=copy.deepcopy(original)
            first[name][key]=value;second['files'][name][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):subject.join_target_identity(compact,first,second)
        for side in ('compact','physical','original'):
            a,b,c=copy.deepcopy((compact,physical,original))
            (a['files'] if side=='compact' else b if side=='physical' else c['files']).pop(name)
            with self.subTest(side=side),self.assertRaises(ValueError):subject.join_target_identity(a,b,c)

    def test_descriptor_rejects_symlink_hardlink_and_wrong_kind(self):
        source=self.root/'body';source.write_bytes(b'body');source.chmod(0o644)
        self.assertEqual(subject.physical_file_record(source)['bytes'],4)
        alias=self.root/'symbolic';alias.symlink_to(source)
        with self.assertRaises(ValueError):subject.physical_file_record(alias)
        link=self.root/'hard';os.link(source,link)
        with self.assertRaises(ValueError):subject.physical_file_record(source)
        with self.assertRaises(ValueError):subject.physical_file_record(self.task)

    def test_sdk_schema_has_exact_five_source_paths_and_no_native_engine(self):
        self.assertEqual(subject.source_sdk_schema(self.runtime,self.task),self.runtime)
        for key,value in (('engine','chromium'),('python','/other/python'),('modules','/other/modules'),
                          ('playwright','/other/playwright'),('node','relative-node')):
            changed={**self.runtime,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):subject.source_sdk_schema(changed,self.task)

    def test_native_runtime_and_managed_browser_populations_remain_absent(self):
        subject.source_only_absence(self.task)
        (self.task/'runtime.json').write_text('{}')
        with self.assertRaises(ValueError):subject.source_only_absence(self.task)

    def test_original_native_common_refusal_is_specific(self):
        good={'returncode':1,'timedOut':False,'error':None,'retentionError':None,'stdout':'',
              'stderr':'Traceback retained\n'+subject.NATIVE_REFUSAL+'\n'}
        self.assertTrue(subject.native_refusal(good))
        for key,value in (('returncode',True),('returncode',0),('timedOut',True),('stdout','PASS'),('stderr','FileNotFoundError: missing')):
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):subject.native_refusal({**good,key:value})

    def test_fixed_contract_workflow_and_unchanged_target_pins(self):
        contract=subject.validate_contract(subject.load(subject.CONTRACT))
        self.assertEqual(len(contract['harnessFiles']),16)
        self.assertEqual(contract['target']['sourceFiles'],111)
        self.assertEqual(contract['target']['commit'],'ff50cffa4292db608bbdead4fedd7f9319e4ca4e')
        self.assertEqual({key:contract['limits'][key] for key in ('commonSeconds','r002fSeconds','sourceCheckSeconds','generatedSeconds',
            'preparationSeconds','postSourceSeconds','sourceCoordinatorSeconds','dependencySeconds','sealSeconds')},
            {'commonSeconds':900,'r002fSeconds':900,'sourceCheckSeconds':120,'generatedSeconds':30,
             'preparationSeconds':2160,'postSourceSeconds':240,'sourceCoordinatorSeconds':3450,'dependencySeconds':720,'sealSeconds':1200})
        subject.validate_workflow(subject.ROOT,contract)
        for key in ('campaignSha256','sourceManifestSha256','nativeWorkflowSha256'):
            path={'campaignSha256':contract['target']['campaignPath'],'sourceManifestSha256':contract['target']['sourceManifestPath'],
                  'nativeWorkflowSha256':'.github/workflows/research-native-pilot.yml'}[key]
            self.assertEqual(subject.sha((subject.ROOT/path).read_bytes()),contract['target'][key])
        workflow=(subject.ROOT/contract['workflowPath']).read_text()
        self.assertIn('runs-on: ubuntu-22.04',workflow)
        self.assertIn('timeout-minutes: 90',workflow);self.assertIn('timeout-minutes: 59',workflow)
        scripts='\n'.join(re.findall(r'^        run: \|\n(.*?)(?=^      - name:|\Z)',workflow,re.M|re.S))
        self.assertNotIn('acquire.sh',scripts);self.assertNotIn('observe.py',scripts);self.assertNotIn('native_trials.py',scripts)
        changed=copy.deepcopy(contract);changed['limits']['commonSeconds']+=1
        with self.assertRaises(ValueError):subject.validate_contract(changed)

    def test_blocked_plan_matches_original_pure_planner_and_refuses_promotions(self):
        import r002f_bfcache_central as original
        prepared={'trees':{'main':{'root':str(self.task/'work/prepared/trees/main')},
                           'r0035':{'root':str(self.task/'work/prepared/trees/r0035')}}}
        roots={**self.roots,'target':subject.ROOT}
        plan=original.make_plan(prepared,self.task/'capture/lanes',self.runtime,{'status':'PASS'})
        subject.validate_blocked_plan(plan,prepared,self.task,roots,self.runtime,original.budget())
        for change in ('argv','native','count','budget','starFlags','boolean'):
            bad=copy.deepcopy(plan)
            if change=='argv':bad['lanes'][0]['argv']=['node','native']
            elif change=='native':bad['lanes'][0]['preparation']={'status':'PASS','native':True}
            elif change=='count':bad['lanes'].append(copy.deepcopy(bad['lanes'][0]))
            elif change=='budget':bad['lanes'][0]['timeoutSeconds']+=1
            elif change=='starFlags':bad['r0035Plan']['arms']['mitigated']['flags']+='&r35guard=off'
            else:bad['lanes'][0]['dpr']=True
            with self.subTest(change=change),self.assertRaises(ValueError):
                subject.validate_blocked_plan(bad,prepared,self.task,roots,self.runtime,original.budget())

    def test_central_missing_runtime_refusal_is_distinct_and_exact(self):
        command=subject.command_for_phase('central-no-runtime',self.task,self.roots,self.runtime)
        value={**command,'returncode':1,'timedOut':False,'error':None,'retentionError':None,'stdout':'','elapsedSeconds':0.1,
               'stderr':"Traceback retained\nFileNotFoundError: [Errno 2] No such file or directory: "+repr(str(self.task/'runtime.json'))+'\n',
               'quiescence':{'quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[]}}
        subject.validate_negative_process(value,command,'central-no-runtime',self.task)
        for key,changed in (('stderr',subject.NATIVE_REFUSAL),('returncode',0),('timeoutSeconds',121),('elapsedSeconds',121),
                            ('quiescence',{'quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[{'pid':1}]})):
            with self.subTest(key=key),self.assertRaises(ValueError):
                subject.validate_negative_process({**value,key:changed},command,'central-no-runtime',self.task)

    def test_actual_supervisor_kills_detached_nested_child_on_timeout(self):
        module=subject.load_supervisor();supervisor=module.Supervisor()
        code="import subprocess,sys,time; child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True);print(child.pid,flush=True);time.sleep(30)"
        process=supervisor.run([sys.executable,'-B','-c',code],str(self.task),subject.clean_environment(),
            self.root/'nested.stdout',self.root/'nested.stderr',1)
        subject.save(self.root/'nested-process.json',process)
        self.assertTrue(process['timedOut']);self.assertEqual(process['returncode'],-9)
        self.assertEqual(process['quiescence']['remaining'],[]);self.assertTrue(process['quiescence']['quiescent'])
        nested=int(process['stdout'].strip());self.assertNotIn(nested,module.process_table())
        with self.assertRaises(ValueError):module.successful(process)

    def test_actual_supervisor_retains_exception_and_quiescent_failure(self):
        module=subject.load_supervisor();supervisor=module.Supervisor()
        class SyntheticDeadline(Exception):pass
        prior=signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(SyntheticDeadline('bounded synthetic interruption')))
        signal.setitimer(signal.ITIMER_REAL,0.2)
        try:
            process=supervisor.run([sys.executable,'-B','-c','import time;print("started",flush=True);time.sleep(30)'],
                str(self.task),subject.clean_environment(),self.root/'interrupt.stdout',self.root/'interrupt.stderr',2)
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prior)
        subject.save(self.root/'interrupt-process.json',process)
        self.assertEqual(process['error']['type'],'SyntheticDeadline');self.assertEqual(process['stdout'],'started\n')
        self.assertEqual(process['returncode'],-9);self.assertEqual(process['quiescence']['remaining'],[])
        with self.assertRaises(ValueError):module.successful(process)

    def test_generated_runner_refuses_changed_original_call_before_launch(self):
        class Never:
            def run(self,*a,**kw):raise AssertionError('changed command reached a process')
        run=subject.generated_runner(self.task,self.roots,self.runtime,{},Never())
        expected=subject.generated_command(self.task,self.roots,self.runtime)
        kwargs={'cwd':Path(expected['cwd']),'stdout':-1,'stderr':-1,'timeout':30,'check':False}
        for key,value in (('timeout',31),('timeout',True),('check',True),('cwd',Path('/different'))):
            with self.subTest(key=key),self.assertRaises(ValueError):run(expected['argv'],**{**kwargs,key:value})
        with self.assertRaises(ValueError):run(expected['argv']+['--native'],**kwargs)

    def test_generated_runner_rejects_incomplete_process_even_with_success_stdout(self):
        (self.task/'records').mkdir()
        class Incomplete:
            def run(self,argv,cwd,env,out,err,seconds):
                out.write_bytes(b'{"status":"PASS"}');err.write_bytes(b'')
                return {'argv':argv,'cwd':cwd,'timeoutSeconds':seconds,'returncode':0,'timedOut':False,'error':None,
                        'retentionError':{'type':'Synthetic','message':'lost terminal'},'elapsedSeconds':0.1,
                        'stdout':'{"status":"PASS"}','stderr':'','quiescence':{'quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[]}}
        run=subject.generated_runner(self.task,self.roots,self.runtime,{},Incomplete())
        expected=subject.generated_command(self.task,self.roots,self.runtime)
        with self.assertRaises(ValueError):run(expected['argv'],cwd=Path(expected['cwd']),stdout=-1,stderr=-1,timeout=30,check=False)
        self.assertTrue((self.task/'records/generated-admission-process.json').is_file())
        self.assertEqual((self.task/'records/generated-admission.stdout').read_bytes(),b'{"status":"PASS"}')

    def test_retained_process_requires_exact_owner_raw_streams_and_nonboolean_pid(self):
        owner={'pid':42,'startTicks':123};expected={'argv':['/fixed/python','-B','source.py'],'cwd':'/fixed','timeoutSeconds':30}
        value={**expected,'returncode':0,'timedOut':False,'error':None,'retentionError':None,'pid':43,'startTicks':124,
            'elapsedSeconds':0.1,'stdout':'actual\n','stderr':'','quiescence':{'quiescent':True,'unexpectedDescendants':False,
                'before':[],'remaining':[],'coordinatorPid':42,'coordinatorStartTicks':123}}
        subject.verify_stream_process(value,expected,b'actual\n',b'',owner)
        for mutation in ('raw','owner','pid','ticks','elapsed','argv','quiescence'):
            changed=copy.deepcopy(value);out=b'actual\n';wanted=copy.deepcopy(owner)
            if mutation=='raw':out=b'replacement\n'
            elif mutation=='owner':wanted['startTicks']=125
            elif mutation=='pid':changed['pid']=True
            elif mutation=='ticks':changed['startTicks']=None
            elif mutation=='elapsed':changed['elapsedSeconds']=31
            elif mutation=='argv':changed['argv'].append('--native')
            else:changed['quiescence']['before']=[{'pid':44,'startTicks':126}]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                subject.verify_stream_process(changed,expected,out,b'',wanted)

    def test_fixed_child_start_must_join_the_actual_parent_process(self):
        command=subject.command_for_phase('check-source',self.task,self.roots,self.runtime)
        process={'pid':100,'startTicks':1234}
        start={'protocol':'fixed-bf-source-child-start/1','operation':'check-source','pid':100,'startTicks':1234,
               'argv':command['argv'][2:],'python':self.runtime['python'],'task':str(self.task),'nativeExecution':'NOT_RUN'}
        self.assertEqual(subject.verify_source_child(start,process,command,'check-source',self.task),process)
        for key,value in (('pid',101),('startTicks',True),('python','/different'),('argv',command['argv']),
                          ('task','/different'),('nativeExecution','OBSERVED'),('operation','refuse-native-common')):
            with self.subTest(key=key),self.assertRaises(ValueError):
                subject.verify_source_child({**start,key:value},process,command,'check-source',self.task)

    def test_fixed_cli_rejects_cross_route_and_mixed_arguments_before_actions(self):
        with patch.object(subject,'run',side_effect=AssertionError('forbidden dispatch')),\
             patch.object(subject,'inspect_source_task',side_effect=AssertionError('forbidden inspect')):
            for argv in (['run'],['run','--task','/task','--workspace','/workspace','--index','/index'],
                         ['inspect','--task','/task','--index','/index','--objects','/objects','--binding','/binding']):
                with self.subTest(argv=argv),self.assertRaises(ValueError):subject.main(argv)
            for operation in ('acquire','observe','native','prepare-arbitrary'):
                with self.subTest(operation=operation),self.assertRaises(SystemExit):subject.main([operation])

    def test_incomplete_original_prefix_remains_incomplete_without_backfill(self):
        before={r:{'status':'NOT_ADMITTED','root':'/fixed/'+r} for r in subject.ROLES}
        binding={'label':'SYNTHETIC_METADATA_ONLY'};failure={'stage':'original-common','type':'ValueError','message':'actual source process failed'}
        result={'protocol':subject.PROTOCOL,'scope':'SOURCE_ONLY','status':'INCOMPLETE','nativeIsolationClaim':False,
                'nativeExecution':'NOT_RUN','fullCentralAdmission':'NOT_CLAIMED','failures':[failure]}
        sealed={'protocol':'source-only-sealing-admission/1','binding':binding,'originalStatus':'INCOMPLETE',
                'sourceOnlyAuthority':True,'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','sourceCurrent':False,
                'errors':[{'type':'ValueError','message':'original source never admitted'}]}
        records={'records/sources-before.json':before,'records/result.json':result,'records/seal-admission.json':sealed,
                 'records/binding.json':binding,'records/final-quiescence.json':{'quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[]}}
        index={'binding':binding,'logicalRoots':{**{r:'/fixed/'+r for r in subject.ROLES},'task':'/task','records':'/task/records'},
               'sourceIdentities':{r:subject.sha(subject.canonical(before[r])) for r in subject.ROLES}}
        observed=[]
        def raw(name):observed.append(name);return subject.canonical(records[name])
        value=subject.inspect_source_records(index,{},raw)
        self.assertEqual(value['status'],'INCOMPLETE');self.assertEqual(value['failures'],[failure])
        self.assertEqual(value['immutableTreeAnchor'],'REQUIRED_SEPARATELY')
        self.assertFalse(any('source-runtime' in name or 'prepared.json' in name for name in observed))

    def test_success_population_does_not_admit_native_or_unproduced_child_records(self):
        names=subject.success_record_names()
        self.assertIn('records/central-no-runtime-process.json',names)
        self.assertIn('records/refuse-native-common-final-quiescence.json',names)
        self.assertIn('records/generated-admission-process.json',names)
        self.assertTrue(all(n.startswith('records/') for n in names))
        self.assertFalse(any('native-admission' in n or 'acquisition' in n or 'bfcache-tools' in n or 'runtime.json'==n for n in names))

    def incomplete_payload_fixture(self):
        import bfcache_source_payload as payload
        contract=subject.load(subject.CONTRACT)
        binding={'repository':subject.REPOSITORY,'workflowPath':subject.WORKFLOW,
            'workflowRef':subject.REPOSITORY+'/'+subject.WORKFLOW+'@refs/heads/'+subject.BRANCH,
            'workflowCommit':'1'*40,'workflowTree':'2'*40,'runId':1,'runAttempt':1,
            'targetCommit':contract['target']['commit'],'targetTree':contract['target']['tree'],
            'campaignSha256':contract['target']['campaignSha256'],'contractSha256':subject.sha(subject.CONTRACT.read_bytes())}
        before={r:{'status':'NOT_ADMITTED','root':'/synthetic/'+r} for r in subject.ROLES}
        result={'protocol':subject.PROTOCOL,'scope':'SOURCE_ONLY','status':'INCOMPLETE','nativeIsolationClaim':False,
            'nativeExecution':'NOT_RUN','fullCentralAdmission':'NOT_CLAIMED','failures':[{'stage':'input-validation','type':'Synthetic','message':'fixture only'}]}
        sealed={'protocol':'source-only-sealing-admission/1','binding':binding,'originalStatus':'INCOMPLETE',
            'sourceOnlyAuthority':True,'nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','sourceCurrent':False,'errors':[]}
        records={'records/sources-before.json':before,'records/binding.json':binding,'records/result.json':result,
                 'records/seal-admission.json':sealed,'records/final-quiescence.json':{'quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[]}}
        raw={n:subject.canonical(v) for n,v in records.items()}
        logical=[{'path':n,'bytes':len(b),'sha256':subject.sha(b)} for n,b in sorted(raw.items())]
        objects=[{'sha256':k,'bytes':v} for k,v in sorted({r['sha256']:r['bytes'] for r in logical}.items())]
        ids={r:subject.sha(subject.canonical(before[r])) for r in subject.ROLES};shards=payload.assign_shards(objects)
        for row in shards:
            row.update(ciphertext={'bytes':100,'sha256':'5'*64},envelope={'bytes':100,'sha256':'6'*64},
                       portableMappingSha256='7'*64,stagedBytes=row['rawBytes']+1000,
                       descriptorSha256=subject.sha(payload.canonical(payload.descriptor(binding,ids,row['id'],objects))))
        roots={r:'/synthetic/'+r for r in subject.ROLES};roots.update(task='/synthetic/task',records='/synthetic/task/records')
        index=payload.make_index(binding,ids,roots,logical,objects,shards)
        index_root=self.root/'synthetic-index';index_root.mkdir(mode=0o700)
        object_root=self.root/'synthetic-objects';object_root.mkdir(mode=0o700)
        (index_root/'index.json').write_bytes(payload.canonical(index))
        for data in raw.values():(object_root/subject.sha(data)).write_bytes(data)
        binding_path=self.root/'synthetic-binding.json';binding_path.write_bytes(subject.canonical(binding))
        return index_root,object_root,binding_path

    def test_full_raw_object_inspector_preserves_incomplete_synthetic_source_task(self):
        index,objects,binding=self.incomplete_payload_fixture();terminal=io.StringIO()
        with contextlib.redirect_stdout(terminal):self.assertEqual(subject.inspect_source_task(index,objects,binding),1)
        report=json.loads(terminal.getvalue())
        self.assertEqual(report['status'],'INCOMPLETE');self.assertEqual(report['custody']['status'],'COMPLETE_RAW_OBJECT_CUSTODY')
        self.assertTrue(report['rawObjectPopulationRechecked']);self.assertEqual(report['immutableTreeAnchor'],'REQUIRED_SEPARATELY')
        self.assertFalse(report['nativeIsolationClaim'])

    def test_full_inspector_refuses_index_mutation_during_metadata_read(self):
        import bfcache_source_payload as payload
        index,objects,binding=self.incomplete_payload_fixture();original=payload.read_logical;changed=False
        def mutate(*args,**kwargs):
            nonlocal changed
            raw=original(*args,**kwargs)
            if not changed:
                changed=True
                with (index/'index.json').open('ab') as stream:stream.write(b'\n')
            return raw
        with patch.object(payload,'read_logical',side_effect=mutate),self.assertRaisesRegex(ValueError,'changed during source review'):
            subject.inspect_source_task(index,objects,binding)

    def test_each_failed_original_phase_stops_before_the_next_and_retains_actual_prefix(self):
        # This control stubs every source/runtime/build launch. It exercises only
        # the coordinator's failure precedence, never the original builders.
        preparer=self.roots['target']/'tools/qa/hosted-native/prepare.py'
        preparer.parent.mkdir(parents=True);preparer.write_bytes((subject.HERE/'prepare.py').read_bytes())
        for failed_phase in ('common','r002f','check-source'):
            task=self.root/('synthetic-failure-'+failed_phase)
            for n in ('','records','capture','work'):(task/n).mkdir(parents=True,exist_ok=True,mode=0o700)
            commands=[];sources={r:{'status':'SYNTHETIC_CONTROL_ONLY','root':str(self.roots[r]),'tree':'b'*40,'commit':'a'*40} for r in subject.ROLES}
            host={'repository':subject.REPOSITORY,'workflowPath':subject.WORKFLOW,'workflowRef':'synthetic','workflowCommit':'a'*40,'runId':1,'runAttempt':1}
            class FakeSupervisor:
                pid=10;started=20
                def quiesce(self):return {'quiescent':True,'unexpectedDescendants':False,'before':[],'remaining':[]}
                def run(self,argv,cwd,env,out,err,seconds):
                    phase=('common' if str(argv[1]).endswith('/prepare.py') else 'r002f' if str(argv[1]).endswith('/r002f_prepare.py') else 'check-source')
                    commands.append(phase);failed=phase==failed_phase
                    terminal='' if failed else ('PREPARATION READY\n' if phase=='common' else 'R002F_BUILD PASS\n')
                    out.write_text(terminal);err.write_text('retained synthetic interruption\n' if failed else '')
                    return {'argv':argv,'cwd':cwd,'timeoutSeconds':seconds,'returncode':-9 if failed else 0,'timedOut':False,
                        'error':None,'retentionError':None,'elapsedSeconds':0.1,'stdout':terminal,'stderr':err.read_text(),
                        'quiescence':self.quiesce()}
            class FakeModule:
                Supervisor=FakeSupervisor
                successful=staticmethod(subject.load_supervisor().successful)
            old_env=dict(os.environ);old_handler=signal.getsignal(signal.SIGALRM)
            try:
                with patch.object(subject,'fixed_task',return_value=task),patch.object(subject,'roots_for',return_value=self.roots),\
                     patch.object(subject,'load_supervisor',return_value=FakeModule),patch.object(subject,'read_host',return_value=(self.runtime['node'],host,{})),\
                     patch.object(subject,'validate_inputs',return_value=sources),patch.object(subject,'target_physical_map',return_value={}),\
                     patch.object(subject,'import_target',return_value=(object(),{})),\
                     patch.object(subject,'install_source_runtime',return_value=(self.runtime,{})),patch.object(subject,'source_current',return_value={}),\
                     patch.object(subject,'source_only_absence',return_value=None):
                    self.assertEqual(subject.run(task,self.root),1)
            finally:
                signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler)
                os.environ.clear();os.environ.update(old_env)
            result=subject.load(task/'records/result.json')
            expected=['common','r002f','check-source'][:['common','r002f','check-source'].index(failed_phase)+1]
            self.assertEqual(commands,expected);self.assertEqual(result['status'],'INCOMPLETE')
            self.assertEqual(result['failures'][0]['stage'],'original-'+failed_phase)
            self.assertEqual(len(result['actualProcesses']),len(expected))
            self.assertFalse((task/'records/refuse-native-common-request.json').exists())
            self.assertFalse((task/'records/source-check-result.json').exists())
            self.assertFalse(result['nativeIsolationClaim']);self.assertEqual(result['nativeExecution'],'NOT_RUN')


if __name__=='__main__':unittest.main()
