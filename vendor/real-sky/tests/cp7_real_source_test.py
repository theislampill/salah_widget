import unittest,sys,importlib,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
class Geometry(unittest.TestCase):
 def module(self):
  try:return importlib.import_module('healpix_grid')
  except ModuleNotFoundError:self.fail('Native HEALPix source converter is not implemented')
 def test_base_faces(self):
  m=self.module();lon,lat=m.pix2ang(1,np.arange(12))
  np.testing.assert_allclose(lon,[45,135,225,315,0,90,180,270,45,135,225,315],atol=1e-12)
  np.testing.assert_allclose(lat,[math.degrees(math.asin(2/3))]*4+[0]*4+[-math.degrees(math.asin(2/3))]*4,atol=1e-12)
 def test_all_centres_roundtrip(self):
  m=self.module()
  for n in [1,2,4,16,64,256]:
   p=np.arange(12*n*n);a,b=m.pix2ang(n,p);np.testing.assert_array_equal(m.ang2pix(n,a,b),p)
 def test_wrap(self):
  m=self.module();a=np.arange(-720,1080,13.);np.testing.assert_array_equal(m.ang2pix(256,a,33.),m.ang2pix(256,a%360,33.))
 def test_nested_parent(self):
  m=self.module();p=np.arange(12*64*64);a,b=m.pix2ang(64,p);np.testing.assert_array_equal(m.ang2pix(16,a,b),p//16)
 def test_bad_parameters(self):
  m=self.module()
  for args in [(3,[0],[0]),(256,[0],[91]),(256,[float('nan')],[0])]:
   with self.assertRaises(ValueError):m.ang2pix(*args)
  with self.assertRaises(ValueError):m.pix2ang(4,[-1])
 def test_unit_vectors_and_area(self):
  m=self.module();v=m.centres(32);np.testing.assert_allclose(np.linalg.norm(v,axis=1),1,atol=1e-14);self.assertAlmostEqual(m.pixel_area(32)*len(v),4*math.pi)
class Source(unittest.TestCase):
 def module(self):
  try:return importlib.import_module('qualify_starmap')
  except ModuleNotFoundError:self.fail('Real map qualification is not implemented')
 def test_actual_source_decodes_and_retains_units(self):
  m=self.module();v,h=m.load_source(R);self.assertEqual(v.shape,(786432,4));self.assertTrue(np.isfinite(v).all());self.assertTrue((v>=0).all());self.assertIn('passband-averaged spectral radiance', '\n'.join(h))
 def test_zero_point_consistency(self):
  m=self.module();v,h=m.load_source(R);z=m.zero_points(h);self.assertEqual(set(z),set('BVRI'));self.assertAlmostEqual(z['V'],3.62708e-11,places=20)
 def test_reject_wrong_calibration_factor(self):
  m=self.module();h=m.header(R/m.SOURCE);h=[s.replace('5.977651e-22','9.977651e-22') for s in h]
  with self.assertRaises(ValueError):m.zero_points(h)
 def test_reject_duplicate_calibration(self):
  m=self.module();h=m.header(R/m.SOURCE);h.append(next(s for s in h if s.startswith('# zero points V:')))
  with self.assertRaises(ValueError):m.zero_points(h)
 def test_reject_conflicting_units(self):
  m=self.module()
  with self.assertRaises(ValueError):m.zero_points(['# quantity: band-integrated radiance'])
if __name__=='__main__':unittest.main()
