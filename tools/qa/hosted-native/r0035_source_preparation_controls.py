"""Source-only controls. No original builder, native driver or browser is run."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import time

import r0035_source_preparation as subject


class ContractControls(unittest.TestCase):
    def contract(self):
        return json.loads((Path(__file__).with_name('r0035-source-preparation.json')).read_bytes())

    def test_exact_receiving_contract(self):
        value=subject.validate_contract(self.contract())
        self.assertEqual(value['target']['commit'],'cc86ce71132be6cb7b93d20a6579dfb42cbc6f92')
        self.assertEqual(value['target']['tree'],'7ee18182b1c0729086798a59903046948e2e4431')
        self.assertIs(value['nativeIsolationClaim'],False)

    def test_unknown_contract_key_is_rejected(self):
        value=self.contract();value['nativeCommand']='observe'
        with self.assertRaises(ValueError):subject.validate_contract(value)

    def test_wrong_target_commit_or_tree_is_rejected(self):
        for field in ('commit','tree'):
            value=self.contract();value['target'][field]='0'*40
            with self.subTest(field=field),self.assertRaises(ValueError):subject.validate_contract(value)

    def test_wrong_campaign_is_rejected(self):
        value=self.contract();value['target']['campaignSha256']='0'*64
        with self.assertRaises(ValueError):subject.validate_contract(value)

    def test_native_authority_is_rejected(self):
        value=self.contract();value['nativeIsolationClaim']=True
        with self.assertRaises(ValueError):subject.validate_contract(value)

    def test_wrong_original_source_is_rejected(self):
        value=self.contract();value['sources']['research']['commit']='f'*40
        with self.assertRaises(ValueError):subject.validate_contract(value)

    def test_wrong_original_ceilings_are_rejected(self):
        for name in ('commonSeconds','derivedSeconds','readmissionSeconds','preparationSeconds'):
            value=self.contract();value['limits'][name]+=1
            with self.subTest(name=name),self.assertRaises(ValueError):subject.validate_contract(value)

    def test_no_native_command_selector_exists(self):
        roots={name:Path('/work')/name for name in ['target','research','baseline','historical']}
        runtime={'python':'/runtime/python/bin/python','node':'/runtime/node/bin/node','modules':'/runtime/node_modules'}
        for phase in ('observe','acquire','namespace','native-driver','browser-install','intake'):
            with self.subTest(phase=phase),self.assertRaises(ValueError):
                subject.command_for_phase(phase,Path('/task'),roots,runtime)
        common=subject.command_for_phase('common',Path('/task'),roots,runtime)
        derived=subject.command_for_phase('derived',Path('/task'),roots,runtime)
        self.assertEqual(common['timeoutSeconds'],900);self.assertEqual(derived['timeoutSeconds'],240)
        self.assertEqual(Path(common['argv'][1]).name,'prepare.py')
        self.assertEqual(derived['argv'][3],'prepare')

    def test_loader_and_git_fetch_injection_removed(self):
        with mock.patch.dict(os.environ,{'NODE_OPTIONS':'--require /untrusted','PYTHONPATH':'/untrusted',
              'PYTHONHOME':'/untrusted','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.sshCommand',
              'GIT_CONFIG_VALUE_0':'bad','GIT_ALLOW_PROTOCOL':'https','LD_PRELOAD':'/untrusted'},clear=False):
            env=subject.clean_environment()
        for name in ['NODE_OPTIONS','PYTHONPATH','PYTHONHOME','GIT_CONFIG_COUNT','GIT_CONFIG_KEY_0','GIT_CONFIG_VALUE_0','LD_PRELOAD']:
            self.assertNotIn(name,env)
        self.assertEqual(env['GIT_ALLOW_PROTOCOL'],'');self.assertEqual(env['GIT_NO_LAZY_FETCH'],'1')

    def test_specific_native_refusal_is_required(self):
        process={'returncode':1,'timedOut':False,'stdout':'','stderr':'ValueError: native common preparation was not isolated by hosted execution\n'}
        self.assertTrue(subject.native_refusal(process))
        for changed in ({'returncode':0},{'returncode':2},{'returncode':True},{'timedOut':True},
                        {'stderr':'ValueError: unrelated failure\n'},{'stdout':'NATIVE ADMITTED'}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):subject.native_refusal({**process,**changed})

    def test_runner_and_runtime_are_source_pinned(self):
        env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'theislampill/salah_widget',
             'GITHUB_REF':'refs/heads/chatgpt/r0035-source-preparation-20261127',
             'GITHUB_WORKFLOW_REF':'theislampill/salah_widget/.github/workflows/r0035-source-preparation.yml@refs/heads/chatgpt/r0035-source-preparation-20261127',
             'GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123','GITHUB_RUN_ATTEMPT':'1'}
        value=subject.validate_host(env,{'ID':'ubuntu','VERSION_ID':'22.04'},'v24.14.0',(3,11))
        self.assertEqual(value['runId'],123)
        for os_release,node,python in [({'ID':'ubuntu','VERSION_ID':'24.04'},'v24.14.0',(3,11)),
                ({'ID':'ubuntu','VERSION_ID':'22.04'},'v24.22.3',(3,11)),
                ({'ID':'ubuntu','VERSION_ID':'22.04'},'v24.14.0',(3,12))]:
            with self.subTest(node=node,python=python),self.assertRaises(ValueError):
                subject.validate_host(env,os_release,node,python)
        with self.assertRaises(ValueError):subject.validate_host({**env,'GITHUB_REF':'refs/heads/chatgpt/hosted-native-research-20261125'}, {'ID':'ubuntu','VERSION_ID':'22.04'},'v24.14.0',(3,11))


class SourceIdentityControls(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)/'source';self.root.mkdir();self.names=['source.txt','nested/driver.py']
        (self.root/'nested').mkdir();(self.root/'source.txt').write_text('source\n');(self.root/'nested/driver.py').write_text('pass\n')
        self.git('init','-q');self.git('config','user.name','Source Control');self.git('config','user.email','control@example.invalid')
        self.git('add','.');self.git('commit','-qm','fixture')

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.root),*args],env=subject.clean_environment(),stderr=subprocess.PIPE).decode().strip()

    def test_source_identity_binds_complete_declared_blobs(self):
        value=subject.source_identity(self.root,self.names)
        self.assertEqual(value['commit'],self.git('rev-parse','HEAD'))
        self.assertEqual(set(value['files']),set(self.names))

    def test_skip_worktree_source_mutation_is_rejected(self):
        self.git('update-index','--skip-worktree','source.txt');(self.root/'source.txt').write_text('tampered\n')
        self.assertEqual(self.git('status','--porcelain'),'')
        with self.assertRaises(ValueError):subject.source_identity(self.root,self.names)

    def test_missing_declared_file_is_rejected(self):
        with self.assertRaises(ValueError):subject.source_identity(self.root,[*self.names,'missing.py'])

    def test_nonregular_or_symlink_source_is_rejected(self):
        self.git('update-index','--skip-worktree','source.txt');(self.root/'source.txt').unlink();(self.root/'source.txt').symlink_to('nested/driver.py')
        with self.assertRaises(ValueError):subject.source_identity(self.root,self.names)

    def test_duplicate_or_traversing_declared_paths_rejected(self):
        for names in ([*self.names,self.names[0]],['../outside'],['/absolute']):
            with self.subTest(names=names),self.assertRaises(ValueError):subject.source_identity(self.root,names)

    def test_ignored_bytecode_cannot_replace_admitted_source(self):
        (self.root/'.gitignore').write_text('__pycache__/\n');self.git('add','.gitignore');self.git('commit','-qm','ignore cache fixture')
        folder=self.root/'nested/__pycache__';folder.mkdir();(folder/'driver.cpython-311.pyc').write_bytes(b'foreign cache')
        self.assertEqual(self.git('status','--porcelain'),'')
        with self.assertRaises(ValueError):subject.source_identity(self.root,self.names)


class WorkflowControls(unittest.TestCase):
    def test_all_target_dependency_files_are_materialized(self):
        here=Path(subject.__file__).parent;root=here.parents[2]
        workflow=(root/'.github/workflows/r0035-source-preparation.yml').read_text()
        required=json.loads((here/'r0035-publish-pins.json').read_bytes())['sourceFiles']
        self.assertEqual(len(required),107)
        target=workflow.split('path: target\n',1)[1].split('      - name:',1)[0]
        actual=[line.strip()[1:] for line in target.splitlines() if line.strip().startswith('/')]
        self.assertEqual(actual,required)

    def test_workflow_never_invokes_native_or_browser_installation(self):
        here=Path(subject.__file__).parent;root=here.parents[2];workflow=(root/'.github/workflows/r0035-source-preparation.yml').read_text()
        lines=[];inside=False
        for line in workflow.splitlines():
            if line.startswith('      - name:'):inside=False
            if line.strip()=='run: |':inside=True
            elif inside:lines.append(line)
        commands='\n'.join(lines)
        for forbidden in ('workflow_dispatch','capture_pipeline.py','acquire.sh','namespace.sh','observe.py','native_trials.py',
                          'playwright install','run: sudo','salah-native-${{'):
            with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden,commands)
        self.assertNotIn('workflow_dispatch',workflow)
        self.assertIn('branches: [chatgpt/r0035-source-preparation-20261127]',workflow)
        self.assertIn('runs-on: ubuntu-22.04',workflow);self.assertIn('contents: read',workflow)
        self.assertIn('compression-level: 0',workflow)
        self.assertEqual(workflow.count('r0035_source_preparation.py run --task'),1)
        self.assertEqual(workflow.count('r0035_source_preparation.py seal --task'),1)

    def test_workflow_and_original_transport_are_exactly_pinned(self):
        here=Path(subject.__file__).parent;root=here.parents[2];contract=subject.validate_contract(json.loads((here/'r0035-source-preparation.json').read_bytes()))
        subject.validate_workflow(root,contract)
        for name,digest in contract['transport'].items():self.assertEqual(subject.sha((here/name).read_bytes()),digest)
        self.assertEqual(subject.sha((here/'recipient.crt').read_bytes()),contract['recipient']['pemSha256'])
        self.assertEqual(subject.sha((root/'.github/workflows/research-native-pilot.yml').read_bytes()),contract['target']['nativeWorkflowSha256'])
        wrong=copy.deepcopy(contract);wrong['workflowSha256']='0'*64
        with self.assertRaises(ValueError):subject.validate_workflow(root,wrong)

    def test_harness_closure_includes_every_new_module_and_control(self):
        here=Path(subject.__file__).parent;contract=json.loads((here/'r0035-source-preparation.json').read_bytes())
        files=contract['harnessFiles']
        for name in ('r0035_source_preparation.py','r0035_source_supervisor.py','r0035_source_payload.py',
                     'r0035_source_preparation_controls.py','r0035_source_payload_controls.py'):
            self.assertIn('tools/qa/hosted-native/'+name,files)
        self.assertEqual(files,sorted(set(files)))


class SupervisorControls(unittest.TestCase):
    def setUp(self):
        from r0035_source_supervisor import Supervisor
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.supervisor=Supervisor()

    def run_fixture(self,code,seconds=5):
        return self.supervisor.run([sys.executable,'-B','-c',code],str(self.root),subject.clean_environment(),
                                   self.root/'stdout',self.root/'stderr',seconds)

    def test_actual_success_retains_both_raw_streams(self):
        from r0035_source_supervisor import successful
        result=self.run_fixture("import sys;print('source');print('diagnostic',file=sys.stderr)")
        successful(result);self.assertEqual(result['stdout'],'source\n');self.assertEqual(result['stderr'],'diagnostic\n')
        self.assertEqual((self.root/'stdout').read_bytes(),b'source\n')

    def test_actual_failure_is_not_promoted(self):
        from r0035_source_supervisor import successful
        result=self.run_fixture("import sys;print('original failure',file=sys.stderr);sys.exit(7)")
        self.assertEqual(result['returncode'],7);self.assertFalse(result['timedOut'])
        with self.assertRaises(ValueError):successful(result)

    def test_actual_timeout_is_retained_and_quiescent(self):
        from r0035_source_supervisor import successful
        result=self.run_fixture('import time;time.sleep(10)',1)
        self.assertTrue(result['timedOut']);self.assertEqual(result['returncode'],-9);self.assertTrue(result['quiescence']['quiescent'])
        with self.assertRaises(ValueError):successful(result)

    def test_detached_orphan_is_observed_killed_and_not_a_pass(self):
        from r0035_source_supervisor import successful
        code="import subprocess,sys; p=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(20)'],start_new_session=True);print(p.pid,flush=True)"
        result=self.run_fixture(code);self.assertEqual(result['returncode'],0)
        self.assertTrue(result['quiescence']['unexpectedDescendants']);self.assertTrue(result['quiescence']['quiescent'])
        self.assertEqual(result['quiescence']['remaining'],[]);self.assertTrue(result['quiescence']['signals'])
        with self.assertRaises(ValueError):successful(result)

    def test_existing_log_population_is_never_reused(self):
        from r0035_source_supervisor import successful
        (self.root/'stdout').write_bytes(b'old failure')
        result=self.run_fixture("print('replacement')")
        self.assertEqual((self.root/'stdout').read_bytes(),b'old failure')
        self.assertIsNotNone(result['error']);self.assertIsNone(result['returncode'])
        with self.assertRaises(ValueError):successful(result)

    def test_nonnative_command_spies_preserve_original_calls_and_bounds(self):
        roots={name:Path('/sources')/name for name in ['target','research','baseline','historical']};runtime={'python':'/python','node':'/node','modules':'/modules'}
        calls=[subject.command_for_phase(name,Path('/task'),roots,runtime) for name in ('common','derived','readmit','refusal')]
        self.assertEqual([r['timeoutSeconds'] for r in calls],[900,240,120,120])
        self.assertEqual(calls[0]['argv'],['/python','/sources/target/tools/qa/hosted-native/prepare.py','--research','/sources/research','--baseline','/sources/baseline','--historical','/sources/historical','--out','/task/work/prepared'])
        self.assertEqual(calls[3]['argv'],calls[2]['argv']+['--native'])
        self.assertTrue(all('native_trials.py' not in ' '.join(row['argv']) for row in calls))

    def test_retained_process_cannot_hide_failure_or_change_argv(self):
        expected={'argv':['/python','source.py'],'cwd':'/source','timeoutSeconds':120}
        value={**expected,'returncode':0,'timedOut':False,'elapsedSeconds':1,'quiescence':{'quiescent':True,'unexpectedDescendants':False}}
        subject.retained_process(value,expected)
        for changed in ({'returncode':-9},{'elapsedSeconds':121},{'argv':['/python','native_trials.py']},{'timeoutSeconds':121},
                        {'quiescence':{'quiescent':True,'unexpectedDescendants':True}}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):subject.retained_process({**value,**changed},expected)


class PreparedPopulationControls(unittest.TestCase):
    def fixture(self):
        def row(letter):return {'bytes':1,'sha256':letter*64}
        source={'src/native/index.html':{**row('a'),'gitBlob':'a'*40,'mode':'100644'},
                'tools/input.py':{**row('b'),'gitBlob':'b'*40,'mode':'100644'}}
        before={role:{'files':copy.deepcopy(source)} for role in ('baseline','research')};logical={};bodies={};prepared={'trees':{}}
        for role in ('baseline','research'):bodies['task/work/prepared/receipts/'+role+'-files.json']=copy.deepcopy(source)
        for label in ('main','r0040','r0035'):
            prefix='task/work/prepared/trees/'+label;actual={name:{k:value[k] for k in ('bytes','sha256')} for name,value in source.items()}
            actual.update({'index.html':row('c'),'GENERATED.json':row('d')})
            if label=='main':actual.update({'.git':row('e'),'.gitignore':row('f')})
            elif label=='r0040':
                actual['src/native/index.html']=row('0');bodies['task/work/prepared/receipts/r0040-patch.json']={'postimage':'0'*64}
            else:
                actual['src/native/index.html']=row('1');actual['r0035-lab-identity.json']=row('2')
                bodies[prefix+'/r0035-lab-identity.json']={'sha256':{'src/native/index.html':'1'*64}}
            logical.update({prefix+'/'+name:{'path':prefix+'/'+name,**value} for name,value in actual.items()})
            bodies[prefix+'/GENERATED.json']={'fileCount':1,'byteCount':1,'files':{'index.html':row('c')}}
            prepared['trees'][label]={'fileCount':1,'byteCount':1,'sha256':{'index.html':'c'*64}}
        bodies['task/work/prepared/receipts/r003f-runtime-files.json']={'index.html':row('c')}
        logical['task/work/prepared/trees/r003f/index.html']={'path':'task/work/prepared/trees/r003f/index.html',**row('c')}
        return logical,bodies,before,prepared

    def test_complete_raw_generated_and_source_population_is_checked(self):
        logical,bodies,before,prepared=self.fixture()
        self.assertEqual(subject.verify_prepared_populations(logical,bodies.__getitem__,before,prepared),{'main':6,'r0040':4,'r0035':5,'r003f':1})

    def test_missing_extra_or_changed_generated_member_refuses(self):
        for change in ('missing','extra','changed'):
            logical,bodies,before,prepared=self.fixture();name='task/work/prepared/trees/main/index.html'
            if change=='missing':logical.pop(name)
            elif change=='extra':logical[name+'extra']=copy.deepcopy(logical[name])
            else:logical[name]['sha256']='9'*64
            with self.subTest(change=change),self.assertRaises(ValueError):subject.verify_prepared_populations(logical,bodies.__getitem__,before,prepared)

    def test_unlisted_original_source_mutation_refuses(self):
        logical,bodies,before,prepared=self.fixture();logical['task/work/prepared/trees/r0035/tools/input.py']['sha256']='9'*64
        with self.assertRaises(ValueError):subject.verify_prepared_populations(logical,bodies.__getitem__,before,prepared)

    def test_original_generated_count_and_r003f_population_refuse(self):
        for change in ('count','runtime'):
            logical,bodies,before,prepared=self.fixture()
            if change=='count':bodies['task/work/prepared/trees/main/GENERATED.json']['fileCount']=2
            else:logical.pop('task/work/prepared/trees/r003f/index.html')
            with self.subTest(change=change),self.assertRaises(ValueError):subject.verify_prepared_populations(logical,bodies.__getitem__,before,prepared)

    def test_all_twelve_original_nested_commands_keep_literal_operands(self):
        roots={'research':Path('/research'),'baseline':Path('/baseline')};runtime={'python':'/python'}
        rows=subject.original_child_commands(Path('/task'),roots,runtime)
        self.assertEqual(len(rows),12);self.assertTrue(all(row['timeoutSeconds']==600 for row in rows))
        self.assertEqual(rows[3]['argv'],['/python','-B','tools/build_native.py'])
        self.assertEqual(rows[9]['argv'],['/python','-B','/research/tools/r0035/materialize_lab.py','/task/work/prepared/trees/r0035'])
        self.assertEqual(rows[11]['argv'],['/python','-B','tools/verify_v1.py','--negative-control'])


if __name__=='__main__':unittest.main()
