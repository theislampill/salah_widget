"""Currentness must follow captured pixels across preview/refined handoffs."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/cp9'))
from hotfix_stress_check import displayed_sky_currentness

class PresentedSkyOwnerTest(unittest.TestCase):
 def test_recorded_firefox_handoff_uses_captured_preview(self):
  s={'sky':{'age':30120},'presentedFrame':{'owner':'preview','ageMs':10560}}
  self.assertTrue(all(displayed_sky_currentness(s).values()))

 def test_expired_displayed_owners_fail_even_with_fresh_other_metadata(self):
  for owner in ['preview','refined']:
   with self.subTest(owner=owner):
    s={'sky':{'age':0},'utc':1000,'preview':{'utcMs':1000},'presentedFrame':{'owner':owner,'ageMs':30001}}
    self.assertFalse(all(displayed_sky_currentness(s).values()))

 def test_unknown_or_nonfinite_marker_is_not_admitted(self):
  for owner,age in [('invalid',0),('preview',float('nan')),('refined',-1)]:
   self.assertFalse(all(displayed_sky_currentness({'presentedFrame':{'owner':owner,'ageMs':age}}).values()))

 def test_unpaired_snapshot_checks_its_visible_owner(self):
  s={'displayedOwner':'preview','utc':100000,'preview':{'utcMs':99999},'sky':{'age':90000}}
  self.assertTrue(all(displayed_sky_currentness(s).values()))
  s['preview']['utcMs']=1
  self.assertFalse(all(displayed_sky_currentness(s).values()))

if __name__=='__main__':unittest.main()
