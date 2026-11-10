import unittest, tempfile, sys, csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from import_hyg import normalise_rows
class ImportTests(unittest.TestCase):
 def sample(self,**kw):
  return dict(hip='123',id='999',ra='1.0',dec='60',mag='2.5',ci='0',pmra='1000',pmdec='-100',rv='',dist='100000',proper='',var='',spect='',con='Ori',**kw)
 def test_zero_bv_is_measurement_not_falsy_default(self):
  s=normalise_rows([self.sample()],6.5,set())[0];self.assertEqual(s['bv'],0);self.assertIsNone(s['distancePc'])
 def test_units_hours_to_degrees_and_motion(self):
  s=normalise_rows([self.sample()],6.5,set())[0];self.assertEqual(s['raDeg'],15);self.assertEqual(s['pmRaCosDecMasYr'],1000)
 def test_blank_motion_not_measured_zero(self):
  r=self.sample();r.update(pmra='',pmdec='');s=normalise_rows([r],6.5,set())[0];self.assertIsNone(s['pmRaCosDecMasYr'])
 def test_sol_excluded_even_if_named_oddly(self):
  r=self.sample();r.update(id='0',hip='',proper='Sol',mag='-26.7');self.assertEqual(normalise_rows([r],6.5,set()),[])
 def test_faint_required_endpoint_retained(self):
  r=self.sample();r['mag']='7';self.assertEqual(len(normalise_rows([r],6.5,{123})),1)
 def test_nan_coordinates_raise_not_silently_ignored(self):
  r=self.sample();r['ra']='nan';self.assertRaises(ValueError,normalise_rows,[r],6.5,set())
 def test_duplicates_raise(self):self.assertRaises(ValueError,normalise_rows,[self.sample(),self.sample()],6.5,set())
 def test_missing_colour_preserved(self):
  r=self.sample();r['ci']='';self.assertIsNone(normalise_rows([r],6.5,set())[0]['bv'])
 def test_reject_out_of_range_ra(self):
  r=self.sample();r['ra']='25';self.assertRaises(ValueError,normalise_rows,[r],6.5,set())
 def test_uncertain_zero_rv_preserved_as_unknown(self):
  r=self.sample();r['rv']='0';self.assertIsNone(normalise_rows([r],6.5,set())[0]['radialVelocityKmS'])
if __name__=='__main__':unittest.main()
