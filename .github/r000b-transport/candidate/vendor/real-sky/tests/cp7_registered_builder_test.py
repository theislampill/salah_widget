import unittest,sys,importlib,json,subprocess,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
class Builder(unittest.TestCase):
 def module(self):
  try:return importlib.import_module('build_registered_starlight')
  except ModuleNotFoundError:self.fail('Actual source exclusion/asset builder is not implemented')
 def test_source_exclusion_is_not_blurring(self):
  m=self.module();a=np.arange(1,49,dtype=float);mask=np.zeros(48,dtype=bool);mask[[1,10,20]]=True
  donors=np.array([[0,2,3,4],[9,11,12,13],[18,19,21,22]])
  one=m.fill_masked(a,mask,donors);a[mask]=1e30;two=m.fill_masked(a,mask,donors)
  np.testing.assert_array_equal(one,two);np.testing.assert_array_equal(one[~mask],a[~mask])
 def test_donors_cannot_include_excluded_source(self):
  m=self.module();a=np.ones(12);mask=np.zeros(12,dtype=bool);mask[1]=True
  with self.assertRaises(ValueError):m.fill_masked(a,mask,np.array([[1,2,3]]))
 def test_equal_area_tier_conservation(self):
  m=self.module();a=np.linspace(.1,100,12*32*32)
  for n in [32,16,8]:
   b=m.tier(a,32,n);self.assertLess(abs(b.mean()/a.mean()-1),1e-13)
 def test_emitter_export_uses_permission_not_record_count(self):
  self.module();out=subprocess.run(['node','tools/export_cp7_emitters.mjs'],cwd=R,check=True,capture_output=True,text=True);e=json.loads(out.stdout);cat=json.loads((R/'data/bright-stars.json').read_text())
  self.assertEqual({s['id'] for s in e['stars']},{s['id'] for s in cat['stars'] if s['emission']['enabled']});self.assertEqual(e['withheldCount'],37);self.assertEqual(e['epochs'],[1991.25,2000,2015.5,2016])
 def test_guard_covers_contaminant_pixels(self):
  m=self.module();from healpix_grid import ang2pix,unit_vectors
  n=32;directions=[{'raDeg':0.,'decDeg':0.},{'raDeg':359.99,'decDeg':89.8},{'raDeg':151.,'decDeg':-89.8}]
  mask,_,_=m.exclusion(n,directions,tolerance_deg=.1)
  for d in directions:
   for dx in [-.1,0,.1]:
    p=int(ang2pix(n,(d['raDeg']+dx)%360,d['decDeg']));self.assertTrue(mask[p])
 def test_reject_nonfinite_and_bad_shapes(self):
  m=self.module()
  with self.assertRaises(ValueError):m.fill_masked(np.array([float('nan'),1]),np.array([True,False]),np.array([[1]]))
  with self.assertRaises(ValueError):m.tier(np.ones(12),1,2)
if __name__=='__main__':unittest.main()
