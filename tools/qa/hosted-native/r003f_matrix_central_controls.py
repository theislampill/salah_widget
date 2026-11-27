"""Offline matrix integration controls; synthetic process receipts are not native evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('matrix_campaign', HERE/'r003f_matrix_campaign.py')
M = importlib.util.module_from_spec(SPEC) if SPEC and (HERE/'r003f_matrix_campaign.py').exists() else None
if M: SPEC.loader.exec_module(M)
OWNER = 'owner_11150942_owner_wax_-81.9_150_clear_shipped_reduce_default'

class MatrixControls(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(M, 'matrix campaign admission implementation is required')
    def select(self, value=None, **kw):
        return M.matrix_controls(value or {'id': OWNER, 'variant': 'B0'}, kw.get('harness','corrected-matrix'),
                                 kw.get('selected',['R003F']), kw.get('engine','chromium'), kw.get('dpr',1))
    def test_original_catalogue_complete(self):
        script = "const g=require(process.argv[1]),v=require(process.argv[2]);console.log(JSON.stringify({variants:v.variants,populations:['chromium','firefox','webkit'].flatMap(engine=>[1,2].map(dpr=>({engine,dpr,cells:g.cells(engine,dpr)})))}))"
        actual = json.loads(subprocess.check_output(['node','-e',script,str(HERE.parent/'r003f_grid.cjs'),str(HERE.parent/'r003f_variants.cjs')]))
        c = M.catalogue()
        self.assertEqual({k:c[k] for k in ('variants','populations')},actual)
        self.assertEqual(sum(len(p['cells']) for p in c['populations']),761)
    def test_owner_single_variant_is_diagnostic(self):
        s = self.select()
        self.assertEqual(s['names'],['B0']); self.assertEqual(s['cell']['group'],'owner')
        self.assertEqual(s['budget']['nativeSeconds'],1800)
        self.assertGreater(s['budget']['coordinatorSeconds'],1800+1020+75)
    def test_absent_preserves_legacy(self):
        self.assertIsNone(M.matrix_controls(None,'published',['R003F'],'chromium',1))
        self.assertIsNone(M.matrix_controls(None,'corrected-b0',['R003F'],'chromium',1))
    def test_unknown_or_contradictory_selection_rejected(self):
        for value in ({}, {'id':OWNER}, {'id':OWNER,'variant':['B0','B0']}, {'id':'unknown','variant':'B0'},
                      {'id':OWNER,'variant':'invalid'}, {'id':OWNER,'variant':'B0','extra':True}):
            with self.subTest(value=value),self.assertRaises(ValueError): M.matrix_controls(value,'corrected-matrix',['R003F'],'chromium',1)
        for kw in ({'harness':'published'},{'selected':['R003F','R002F']},{'selected':[]},{'dpr':True}):
            with self.subTest(kw=kw),self.assertRaises(ValueError): self.select(**kw)
    def test_motion_and_unbound_software_trace_blocked(self):
        for engine,group,gpu in [('chromium','motion','default'),('webkit','buckle','software')]:
            cell=next(c for p in M.catalogue()['populations'] if p['engine']==engine and p['dpr']==1 for c in p['cells'] if c['group']==group and c['gpu']==gpu)
            with self.assertRaisesRegex(ValueError,'unsupported'): self.select({'id':cell['id'],'variant':'B0'},engine=engine)
    def test_all_variants_budget_is_not_single_variant_budget(self):
        full=self.select({'id':OWNER,'variant':'all'})
        self.assertEqual(full['names'],M.catalogue()['variants'])
        self.assertGreater(full['budget']['nativeSeconds'],self.select()['budget']['nativeSeconds'])
        self.assertGreater(full['budget']['intakeSeconds'],self.select()['budget']['intakeSeconds'])
    def test_repetition_budget_counts_each_original_pair(self):
        c=next(c for p in M.catalogue()['populations'] if p['engine']=='chromium' and p['dpr']==1 for c in p['cells'] if c['group']=='buckle')
        v=self.select({'id':c['id'],'variant':'B0'})
        self.assertEqual(v['budget']['shots'],80)
        self.assertGreater(v['budget']['nativeSeconds'],80*152.5)
        with self.assertRaisesRegex(ValueError,'budget'):self.select({'id':c['id'],'variant':'all'})
    def test_process_custody_rejects_actual_failures_and_wrong_types(self):
        M.success({'returncode':0,'timedOut':False},'synthetic')
        for change in ({'returncode':1},{'returncode':False},{'returncode':None},{'timedOut':True},{'timedOut':0}, {'retentionError':'disk'},{'error':'transport'}):
            with self.subTest(change=change),self.assertRaises(ValueError):M.success({'returncode':0,'timedOut':False,**change},'synthetic')
    def test_regular_receipt_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/'a',Path(d)/'b';a.write_text('{}');b.symlink_to(a)
            with self.assertRaises(ValueError):M.record(b)
    def test_exclusive_receipt_does_not_rewrite_previous_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'failure.json';M.save(p,{'returncode':2});before=p.read_bytes()
            with self.assertRaises(FileExistsError):M.save(p,{'returncode':0})
            self.assertEqual(p.read_bytes(),before)

    def test_actual_common_process_and_context_are_admitted_without_relabeling(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d); prepared_path=folder/'prepared/receipts/prepared.json';prepared_path.parent.mkdir(parents=True);prepared_path.write_text('{}')
            prepared={'sources':{k:{'root':str(folder/k)} for k in ('research','baseline','historical')}}
            process,context=folder/'process.json',folder/'context.json'
            process.write_text(json.dumps({'returncode':0,'timedOut':False}))
            value={'protocol':'source-only-common-preparation-execution/1','argv':['/synthetic/python',str(HERE/'prepare.py'),
                   '--research',prepared['sources']['research']['root'],'--baseline',prepared['sources']['baseline']['root'],
                   '--historical',prepared['sources']['historical']['root'],'--out',str(prepared_path.parent.parent)],
                   'cwd':str(HERE),'timeoutSeconds':900,'sourceSha256':M.COMMON_PREPARER,'nativeIsolationClaim':False}
            context.write_text(json.dumps(value));saved=context.read_bytes()
            with mock.patch.object(M,'validate_prepared',return_value=prepared):
                admitted,custody=M.common_custody(prepared_path,process,context)
                self.assertEqual(admitted,prepared);self.assertEqual(custody['context'],M.record(context))
                with self.assertRaisesRegex(ValueError,'not isolated'):M.common_custody(prepared_path,process,context,native=True)
                for change in ({'returncode':1},{'timedOut':True},{'retentionError':''}):
                    process.write_text(json.dumps({'returncode':0,'timedOut':False,**change}))
                    with self.assertRaises(ValueError):M.common_custody(prepared_path,process,context)
                process.write_text(json.dumps({'returncode':0,'timedOut':False}))
                value['argv'][-1]=str(folder/'substitute');context.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError,'inputs differ'):M.common_custody(prepared_path,process,context)
            self.assertNotEqual(context.read_bytes(),saved) # Only the control fixture changed.

    def test_original_kernel_predicate_matches_the_coordinator_without_native_operations(self):
        import ast,inspect
        a=ast.parse(inspect.getsource(M.validate_original_snapshot)).body[0]
        source=ast.parse((HERE/'observe.py').read_text())
        b=next(x for x in source.body if isinstance(x,ast.FunctionDef) and x.name=='validate_snapshot')
        fields=next(x.value for x in source.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CAP_FIELDS' for t in x.targets))
        self.assertEqual([ast.dump(x) for x in a.body],[ast.dump(x) for x in b.body])
        self.assertEqual(M.CAP_FIELDS,ast.literal_eval(fields))

    def common_fixture(self,folder,protocol):
        prepared_path=folder/'prepared/receipts/prepared.json';prepared_path.parent.mkdir(parents=True);prepared_path.write_text('{}')
        prepared={'sources':{k:{'root':str(folder/k)} for k in ('research','baseline','historical')}}
        process,context=folder/'capture/preparation-process.json',folder/'capture/preparation-context.json';process.parent.mkdir()
        process.write_text(json.dumps({'returncode':0,'timedOut':False}))
        value={'protocol':protocol,'argv':['/synthetic/python',str(HERE/'prepare.py'),
               '--research',prepared['sources']['research']['root'],'--baseline',prepared['sources']['baseline']['root'],
               '--historical',prepared['sources']['historical']['root'],'--out',str(prepared_path.parent.parent)],
               'cwd':str(HERE),'timeoutSeconds':900,'sourceSha256':M.COMMON_PREPARER,
               'nativeIsolationClaim':protocol=='hosted-common-preparation-execution/1'}
        return prepared_path,prepared,process,context,value

    def test_source_only_common_context_cannot_be_promoted_by_boolean_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);p,prepared,process,context,value=self.common_fixture(folder,'source-only-common-preparation-execution/1')
            fake=folder/'thin-isolation.json';fake.write_text(json.dumps({'passed':True,'browserControl':{'passed':True}}))
            value.update(nativeIsolationClaim=True,isolation=M.record(fake));context.write_text(json.dumps(value))
            with mock.patch.object(M,'validate_prepared',return_value=prepared):
                for native in (False,True):
                    with self.subTest(native=native),self.assertRaises(ValueError):M.common_custody(p,process,context,native=native)

    def test_hosted_protocol_requires_original_structural_isolation_not_boolean_success(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);p,prepared,process,context,value=self.common_fixture(folder,'hosted-common-preparation-execution/1')
            iso=process.parent/'isolation/preparation/receipt.json';iso.parent.mkdir(parents=True)
            iso.write_text(json.dumps({'protocol':'salah-hosted-native-isolation/1','passed':True,'browserControl':{'passed':True}}))
            value['isolation']=M.record(iso);context.write_text(json.dumps(value))
            with mock.patch.object(M,'validate_prepared',return_value=prepared):
                for native in (False,True):
                    with self.subTest(native=native),self.assertRaises(ValueError):M.common_custody(p,process,context,native=native)

    def test_original_namespace_browser_identity_and_retained_body_are_bound_together(self):
        # A synthetic complete model tests the parser; it is not a native receipt.
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);p,prepared,process,context,value=self.common_fixture(folder,'hosted-common-preparation-execution/1')
            iso=process.parent/'isolation/preparation/receipt.json';iso.parent.mkdir(parents=True)
            base={'protocol':'salah-hosted-native-isolation/1','passed':True,'uid':1200,'netns':'net:[22]','outerNetns':'net:[11]',
                  'kernel':{'uids':[1200]*3,'gids':[1200]*3,'groups':[],'netns':'net:[22]',
                    'links':[{'ifname':'lo','flags':['UP','LOOPBACK']}],'routes4':[{'dst':'127.0.0.0/8','dev':'lo'}],
                    'routes6':[{'dst':'::1/128','dev':'lo'},{'dst':'ff00::/8','dev':'lo'}],
                    'status':{**{k:'0000000000000000' for k in M.CAP_FIELDS},'NoNewPrivs':'1'},'externalSocketErrno':101},
                  'browserProcess':{'returncode':0,'timedOut':False},
                  'browserControl':{'protocol':'salah-hosted-browser-boundary/1','passed':True,'uid':1200,'netns':'net:[22]',
                    'chromiumSandbox':True,'postNegativePage':'fresh-page-same-browser','loopbackRequests':2,
                    'externalNavigationError':'net::ERR_NETWORK_UNREACHABLE',
                    'processes':[{'exe':'/synthetic/chrome','sha256':'a'*64,'cmdline':['/synthetic/chrome','--headless']} ]}}
            for name in ('browser.stdout','browser.stderr'):(iso.parent/name).write_text('')
            def retain(receipt):
                iso.write_text(json.dumps(receipt));(iso.parent/'browser.json').write_text(json.dumps(receipt['browserControl']))
                value['isolation']=M.record(iso);context.write_text(json.dumps(value))
            with mock.patch.object(M,'validate_prepared',return_value=prepared):
                retain(base);M.common_custody(p,process,context,native=True)
                mutations=[lambda x:x.update(uid=1201),lambda x:x.update(outerNetns='net:[22]'),
                  lambda x:x['kernel'].update(uids=[0]*3),lambda x:x['kernel'].update(uids=[True]*3),
                  lambda x:x['kernel'].update(groups=[1200]),lambda x:x['kernel']['status'].update(CapEff='1'),
                  lambda x:x['kernel']['links'].append({'ifname':'eth0','flags':['UP']}),
                  lambda x:x['kernel']['routes4'].append({'dst':'default','dev':'lo'}),
                  lambda x:x['kernel'].update(externalSocketErrno=110),lambda x:x['browserProcess'].update(returncode=False),
                  lambda x:x['browserProcess'].update(timedOut=True),lambda x:x['browserProcess'].update(error='retained failure'),
                  lambda x:x['browserControl'].update(uid=1201),lambda x:x['browserControl'].update(netns='net:[other]'),
                  lambda x:x['browserControl'].update(loopbackRequests=True),lambda x:x['browserControl'].update(postNegativePage='same-page'),
                  lambda x:x['browserControl'].update(externalNavigationError='net::ERR_TIMED_OUT'),
                  lambda x:x['browserControl'].update(processes=[]),lambda x:x['browserControl']['processes'][0].update(sha256=''),
                  lambda x:x['browserControl']['processes'][0]['cmdline'].append('--no-sandbox')]
                for index,mutate in enumerate(mutations):
                    changed=copy.deepcopy(base);mutate(changed);retain(changed)
                    with self.subTest(index=index),self.assertRaises(ValueError):M.common_custody(p,process,context,native=True)
                retain(base);(iso.parent/'browser.json').write_text('{}')
                with self.assertRaisesRegex(ValueError,'browser report differs'):M.common_custody(p,process,context,native=True)
                retain(base);(iso.parent/'browser.stderr').unlink()
                with self.assertRaises(ValueError):M.common_custody(p,process,context,native=True)

    def test_outer_and_child_entry_custody_reject_each_corrupt_process_field(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);receipt=folder/'process.json';entry=folder/'entry.json'
            inputs={k:str(folder/k) for k in ('prepared','common-process','common-context','out','receipts','node')}
            inputs['receipts']=str(folder);inputs['pins-sha256']='synthetic-pin'
            prepared={'sources':{'research':{'root':'/source/research'}},'trees':{'r003f':{'root':'/runtime'}}}
            common={'prepared':{'path':'/source/receipt','sha256':'synthetic'}};central={'path':'/source/central','sha256':'synthetic-pin'}
            harness={'outputFiles':[{}]*16};materialization={'path':str(folder/'out/materialization.json'),'sha256':M.MATERIALIZATION}
            child={'protocol':M.PROTOCOL,'status':'PREPARED','nativeExecution':'NOT_RUN','inputs':inputs,'returncode':0,'timedOut':False,
                   'central':central,'cwd':str(HERE),'timeoutSeconds':60,'materializerSha256':M.MATERIALIZER,
                   'common':common,'harness':harness,'materialization':materialization,
                   'argv':[inputs['node'],str(HERE/'r003f_matrix_materialize.cjs'),'--source','/source/research','--out',inputs['out']]}
            outer={'protocol':M.ENTRY_PROTOCOL,'returncode':0,'timedOut':False,'cwd':str(HERE),'timeoutSeconds':180,
                   'argv':M.prepare_argv('/synthetic/python',inputs),'process':str(receipt)}
            def store():receipt.write_text(json.dumps(child));entry.write_text(json.dumps(outer))
            real_record=M.record
            with mock.patch.object(M,'verify_pins',return_value=central),mock.patch.object(M,'common_custody',return_value=(prepared,common)),mock.patch.object(M,'source_closure',return_value=harness),mock.patch.object(M,'record',side_effect=lambda p:materialization if str(p)==materialization['path'] else real_record(p)):
                store();self.assertEqual(M.admit(entry,'synthetic-pin')['status'],'PASS')
                for target,field,bad in [(outer,'returncode',1),(outer,'timedOut',True),(outer,'retentionError','disk'),(outer,'cwd','/substitute'),
                                         (child,'returncode',2),(child,'timedOut',True),(child,'argv',['substitute']),(child,'central',{}),(child,'harness',{})]:
                    before=copy.deepcopy(target);target[field]=bad;store()
                    with self.subTest(field=field,bad=bad),self.assertRaises(ValueError):M.admit(entry,'synthetic-pin')
                    target.clear();target.update(before)

    def test_actual_source_closure_rejects_missing_extra_or_changed_output(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'derived'
            run=subprocess.run(['node',str(HERE/'r003f_matrix_materialize.cjs'),'--source',str(HERE.parents[2]),'--out',str(out)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(len(M.source_closure(out,'node')['outputFiles']),16)
            p=out/'tools/qa/r003f_capture.cjs';original=p.read_bytes();p.write_bytes(original+b'// source drift')
            with self.assertRaises(ValueError):M.source_closure(out,'node')
            p.write_bytes(original);extra=out/'extra';extra.write_text('unregistered')
            with self.assertRaises(ValueError):M.source_closure(out,'node')
            extra.unlink();p.unlink()
            with self.assertRaises(ValueError):M.source_closure(out,'node')

if __name__=='__main__':unittest.main()
