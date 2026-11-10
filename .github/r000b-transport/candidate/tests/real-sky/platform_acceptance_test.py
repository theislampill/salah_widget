import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/cp9'))
from platform_acceptance import collect, REQUIRED_CHECKS

class CollectorTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  (self.root/'observations.json').write_text('{}')
  self.digest=hashlib.sha256(b'{}').hexdigest();self.tree='a'*64
  self.rows=[]
  for family in ['chromium','firefox','webkit']:
   for entry in ['http','file']:
    self.rows.append({'schemaVersion':1,'recordId':family+'-'+entry,'runtimeTreeSha256':self.tree,'sourceRequests':['http://localhost/index.html'],'environment':{'family':family,'os':'Windows','version':'test-version','platform':'test-host','executable':'test-executable'},'entry':{'form':entry,'url':('http://localhost/' if entry=='http' else 'file:///')+'index.html'},'checks':{name:{'status':'PASS','mode':'live' if name=='providers' else 'actual-navigation' if name=='navigation' else 'actual-entry','evidence':'observations.json','sha256':self.digest} for name in REQUIRED_CHECKS}})
 def tearDown(self):self.temp.cleanup()
 def result(self,rows=None):return collect(self.rows if rows is None else rows,self.tree,self.root)
 def test_missing_source_requests_are_rejected(self):
  self.rows[0]['sourceRequests']=[];self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_complete_records_qualify_observations_but_not_the_missing_dag_join_or_review(self):
  r=self.result();self.assertEqual(r['platformEvidence'],'PASS');self.assertEqual(r['status'],'PARTIAL')
 def test_wrong_runtime_is_rejected(self):
  self.rows[0]['runtimeTreeSha256']='b'*64;self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_wrong_windows_target_os_is_rejected(self):
  self.rows[0]['environment']['os']='Linux';self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_engine_launch_does_not_supply_actual_widget_sections(self):
  self.rows[0]['checks']={};self.rows[0]['status']='ENGINE_LAUNCH_ONLY';self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_missing_section_is_rejected(self):
  del self.rows[0]['checks']['composition'];self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_fixture_providers_cannot_supply_live_admission_evidence(self):
  self.rows[0]['checks']['providers']['mode']='controlled-fixture';self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_duplicate_results_are_rejected(self):
  self.rows.append(copy.deepcopy(self.rows[0]));self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_tampered_or_escaping_evidence_is_rejected(self):
  self.rows[0]['checks']['entry']['sha256']='f'*64;self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
  self.rows[0]['checks']['entry']['evidence']='../observations.json';self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_synthetic_page_event_cannot_supply_real_navigation(self):
  self.rows[0]['checks']['navigation']['mode']='synthetic-event';self.assertEqual(self.result()['platformEvidence'],'INCOMPLETE')
 def test_join_requires_two_pass_nodes_and_independent_review_on_the_same_tree(self):
  nodes={n:{'status':'PASS','runtimeTreeSha256':self.tree} for n in ['CP9-N001','CP9-N002']}
  review={'status':'PASS','runtimeTreeSha256':self.tree,'independent':True,'evidence':'review.json'}
  r=collect(self.rows,self.tree,self.root,nodes,review);self.assertNotEqual(r['status'],'PASS','A nonexistent review is not evidence')

if __name__=='__main__':unittest.main()
