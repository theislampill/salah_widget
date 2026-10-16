"""Run inherited analyzer controls against v3 with tiny synthetic custody pins.
Synthetic pin substitution exists only in this offline test process. Production
network controls separately exercise the exact real pins; no browser is run.
"""
from pathlib import Path
import hashlib,json,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import offline_controls_v2 as prior
import analyse_cost_v3 as revised
import network_evidence_v4 as network
from run_cost_v3 import Network

OLD_BATCH=prior.batch
TEST_DATA={p:('synthetic '+p).encode() for p in network.ASSET_PINS}
TEST_PINS={p:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for p,b in TEST_DATA.items()}
def batch(out,*args,**kwargs):
 r=OLD_BATCH(out,*args,**kwargs);out=Path(out);m=out/'runtime.json'
 manifest=json.loads(m.read_text())
 for p,b in TEST_DATA.items():
  f=out/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);manifest['files'][p]=TEST_PINS[p]
 m.write_text(json.dumps(manifest));r['inputs'][str(m)]=hashlib.sha256(m.read_bytes()).hexdigest();r['runtime']={s:manifest for s in 'AB'}
 r.update(assetPins=TEST_PINS,engine='chromium',requests=[])
 for s in r['slots']:
  s.update(origin='http://127.0.0.1:54321',consumptionProvedAtMonotonic=15,quietStartMonotonic=20,network=[{'id':1,'url':'http://127.0.0.1:54321/index.html','method':'GET','type':'document','startMonotonic':2,'endMonotonic':3,'failed':False,'failure':None,'responseStatus':200}])
  s['networkClassification']=network.validate_network(s,r)
 return r
prior.batch=batch;prior.analyse=revised.analyse

class NewControls(unittest.TestCase):
 def test_forged_classification(self):
  with prior.tempfile.TemporaryDirectory() as name:
   out=Path(name);r=batch(out);r['slots'][0]['networkClassification']['startupAbortsWithCurrentConsumption']=[{'forged':True}]
   self.assertEqual(revised.analyse(out,r)['scopes']['main.render']['status'],'INCOMPLETE')
 def test_raw_network_collector(self):
  class Q:
   url='http://127.0.0.1:54321/salah_widget/moon/assets/dem.bin.gz';method='GET';resource_type='fetch';failure='net::ERR_ABORTED'
  q=Q();slot={'origin':'http://127.0.0.1:54321','network':[],'networkViolations':[]};n=Network(slot);n.start(q)
  class Response:request=q;url=q.url;status=200;headers={'content-length':'20137935'}
  n.response(Response());n.finish(q,True)
  self.assertEqual(slot['network'][0]['failure'],'net::ERR_ABORTED');self.assertEqual(slot['networkViolations'],[])
  q=Q();q.failure='net::ERR_FAILED';n.start(q);n.finish(q,True);self.assertTrue(slot['networkViolations'])

if __name__=='__main__':
 with patch.object(revised,'ASSET_PINS',TEST_PINS),patch.object(network,'ASSET_PINS',TEST_PINS):
  suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(prior.Controls),unittest.defaultTestLoader.loadTestsFromTestCase(NewControls)])
  result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
