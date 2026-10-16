"""Synthetic hostile controls for the prospective network classification only."""
from pathlib import Path
import copy,sys,unittest
sys.path.insert(0,str(Path(__file__).parent))
from network_evidence_v4 import validate_network,ASSET_PINS

ORIGIN='http://127.0.0.1:54321'
PINS=ASSET_PINS
def fixture():
 job={'id':2,'key':'current','epoch':1}
 worker={'id':1,'reachable':True,'terminated':False,'kinds':{'boot':1},'boot':{'at':1,'base':ORIGIN+'/salah_widget/moon/','offline':False,'embedded':False,'workerSourceLength':123},'readyCount':1,'readyAt':4,'lastResult':{'at':8,'id':2,'identity':job},'errors':[]}
 owner={'instanceCount':1,'workerId':1,'workerPresent':True,'scalars':{'ready':True,'disposed':False,'epoch':1},'acceptedJob':job}
 state={'at':10,'moon':{'current':True,'pending':False,'visibleSource':'refined-terrain','workerAlive':True,'retryCount':0,'errors':[]},'owners':{'moon':owner},'workers':[worker]}
 slot={'id':'0-0-A','side':'A','origin':ORIGIN,'network':[],'networkViolations':[],'quietStartMonotonic':20,'consumptionProvedAtMonotonic':15,'readyState':state}
 record={'requests':[],'assetPins':PINS,'engine':'chromium'}
 for i,(path,pin) in enumerate(PINS.items()):
  slot['network'].append({'id':i+1,'url':ORIGIN+'/salah_widget/'+path,'method':'GET','type':'fetch','startMonotonic':2,'endMonotonic':3,'failed':True,'failure':'net::ERR_ABORTED','responseStatus':200,'responseBytes':pin['bytes'],'responseAtMonotonic':2.2})
  record['requests'].append({'slot':slot['id'],'side':'A','path':'/salah_widget/'+path,'monotonic':2.1,'servedSha256':pin['sha256'],'bytes':pin['bytes'],'status':200,'writeComplete':True,'writeEndedMonotonic':2.9})
 return slot,record

class Controls(unittest.TestCase):
 def setUp(self):self.s,self.r=fixture()
 def check(self):return validate_network(self.s,self.r)
 def rejected(self,mutate):
  mutate(self.s,self.r)
  with self.assertRaises((AssertionError,KeyError,TypeError,ValueError)):self.check()
 def test_positive_retains_abort_classification(self):
  result=self.check();self.assertEqual(len(result['startupAbortsWithCurrentConsumption']),2);self.assertTrue(all(n['failed'] for n in self.s['network']))
 def test_successful_ordinary_request(self):
  for n in self.s['network']:n.update(failed=False,failure=None)
  self.assertEqual(self.check()['startupAbortsWithCurrentConsumption'],[])
 def test_wrong_url_and_failure(self):
  self.rejected(lambda s,r:s['network'][0].update(url=ORIGIN+'/wrong'))
 def test_other_failure(self):self.rejected(lambda s,r:s['network'][0].update(failure='net::ERR_FAILED'))
 def test_other_engine(self):self.rejected(lambda s,r:r.update(engine='firefox'))
 def test_other_type(self):self.rejected(lambda s,r:s['network'][0].update(type='image'))
 def test_missing_or_error_response(self):self.rejected(lambda s,r:s['network'][0].update(responseStatus=503))
 def test_truncated_body(self):self.rejected(lambda s,r:s['network'][0].update(responseBytes=5))
 def test_wrong_hash(self):self.rejected(lambda s,r:r['requests'][0].update(servedSha256='0'*64))
 def test_partial_server_write(self):self.rejected(lambda s,r:r['requests'][0].update(writeComplete=False))
 def test_missing_receipt(self):self.rejected(lambda s,r:r['requests'].pop())
 def test_duplicate_request(self):self.rejected(lambda s,r:s['network'].append(copy.deepcopy(s['network'][0])))
 def test_duplicate_server_receipt(self):self.rejected(lambda s,r:r['requests'].append(copy.deepcopy(r['requests'][0])))
 def test_non_refined(self):self.rejected(lambda s,r:s['readyState']['moon'].update(visibleSource='terrain-preview'))
 def test_not_current(self):self.rejected(lambda s,r:s['readyState']['moon'].update(current=False))
 def test_pending(self):self.rejected(lambda s,r:s['readyState']['moon'].update(pending=True))
 def test_replaced_worker(self):self.rejected(lambda s,r:s['readyState']['owners']['moon'].update(workerId=3))
 def test_duplicate_owner(self):self.rejected(lambda s,r:s['readyState']['owners']['moon'].update(instanceCount=2))
 def test_second_boot(self):self.rejected(lambda s,r:s['readyState']['workers'][0]['kinds'].update(boot=2))
 def test_ready_missing(self):self.rejected(lambda s,r:s['readyState']['workers'][0].update(readyCount=0))
 def test_wrong_base(self):self.rejected(lambda s,r:s['readyState']['workers'][0]['boot'].update(base=ORIGIN+'/old/'))
 def test_wrong_job(self):self.rejected(lambda s,r:s['readyState']['workers'][0]['lastResult'].update(identity={'id':1,'key':'stale','epoch':0}))
 def test_error(self):self.rejected(lambda s,r:s['readyState']['workers'][0]['errors'].append({'kind':'boot-error'}))
 def test_closed(self):self.rejected(lambda s,r:s['readyState']['workers'][0].update(terminated=True))
 def test_warmup_overlap(self):self.rejected(lambda s,r:s['network'][0].update(endMonotonic=20))
 def test_unfinished(self):self.rejected(lambda s,r:s['network'][0].pop('endMonotonic'))
 def test_late_consumption(self):self.rejected(lambda s,r:s.update(consumptionProvedAtMonotonic=21))
 def test_other_violation(self):self.rejected(lambda s,r:s['networkViolations'].append('unplanned'))

if __name__=='__main__':unittest.main(verbosity=2)
