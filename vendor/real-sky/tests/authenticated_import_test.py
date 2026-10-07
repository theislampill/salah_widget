"""Checkpoint 2 tests: real source custody plus admission edge cases."""
import unittest, sys, hashlib, json, csv, io, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
try:
 import build_authenticated_catalogue as api
except ImportError:
 api=None
class AuthenticatedImportTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(api,'authenticated catalogue builder must exist')
 def sample(self,**kw):
  x=dict(id='12',hip='13',hd='',hr='',ra='1',dec='60',mag='2',ci='0',pmra='1000',pmdec='0',rv='0',dist='100000',spect='',proper='',var='',var_min='',var_max='',con='Ori',comp='1',comp_primary='12',base='')
  x.update(kw);return x
 def test_no_hip_still_has_stable_identity(self):
  s=api.normalise(self.sample(hip=''),5)
  self.assertEqual(s['id'],'hyg:12');self.assertIsNone(s['hip'])
 def test_zero_bv_and_zero_dec_motion_are_values(self):
  s=api.normalise(self.sample(),5);self.assertEqual(s['bv'],0);self.assertEqual(s['pmDecMasYr'],0)
 def test_motion_convention_is_tangent_not_ra_coordinate_rate(self):
  self.assertEqual(api.normalise(self.sample(),5)['pmRaCosDecMasYr'],1000)
 def test_source_rv_zero_is_ambiguous_not_observed_zero(self):
  s=api.normalise(self.sample(),5);self.assertIsNone(s['radialVelocityKmS']);self.assertEqual(s['sourceValues']['rv'],0)
 def test_distance_sentinel_is_not_a_hundred_kiloparsec_star(self):
  self.assertIsNone(api.normalise(self.sample(),5)['distancePc'])
 def test_missing_colour_not_spectral_fabrication(self):
  self.assertIsNone(api.normalise(self.sample(ci=''),5)['bv'])
 def test_faint_records_excluded_unless_required(self):
  self.assertIsNone(api.normalise(self.sample(mag='7'),5));self.assertTrue(api.normalise(self.sample(mag='7'),5,{13})['isRequiredEndpoint'])
 def test_sun_never_becomes_fixed_star(self):
  self.assertIsNone(api.normalise(self.sample(id='0',mag='-26.7'),6.5))
 def test_invalid_ra_and_nan_fail(self):
  for v in ['24','nan','-1']:
   with self.assertRaises(ValueError):api.normalise(self.sample(ra=v),5)
 def test_variable_magnitude_order_not_brightness_word_order(self):
  s=api.normalise(self.sample(var='Alp',var_min='2.3',var_max='1.9'),5)
  self.assertEqual(s['variability']['brightMagnitude'],1.9);self.assertEqual(s['variability']['faintMagnitude'],2.3)
 def test_raw_constellation_error_not_silently_relabelled(self):
  s=api.normalise(self.sample(con='Eco'),5);self.assertEqual(s['sourceValues']['con'],'Eco');self.assertIsNone(s['constellationAbbr'])
 def test_mismatched_high_precision_angles_reject(self):
  with self.assertRaises(ValueError):api.normalise(self.sample(rarad='2',decrad='1'),5)
 def test_actual_primary_hash_and_count(self):
  raw=api.source_bytes(ROOT/'upstream/hygdata_v40.csv.gz')
  self.assertEqual(len(raw),33932465);self.assertEqual(hashlib.sha256(raw).hexdigest(),api.SOURCE_SHA256)
  self.assertEqual(len(list(csv.DictReader(io.StringIO(raw.decode())))),119626)
 def test_wrong_input_hash_rejected_before_output(self):
  with self.assertRaises(ValueError):api.authenticate(b'not a catalogue')
 def test_full_source_selection_includes_all_fifty_non_hip_records(self):
  c=json.loads((ROOT/'data/catalogue-v6_5.json').read_text());self.assertEqual(sum(s['vmag']<=6.5 for s in c['stars']),8920);self.assertEqual(sum(s['hip'] is None for s in c['stars']),50)
 def test_catalogue_measured_field_coverage(self):
  c=json.loads((ROOT/'data/catalogue-v6_5.json').read_text());a=[s for s in c['stars'] if s['vmag']<=6.5]
  self.assertEqual(sum(s['bv'] is not None for s in a),8880)
  self.assertEqual(sum(s['pmRaCosDecMasYr'] is not None and s['pmDecMasYr'] is not None for s in a),8920)
  self.assertEqual(sum(s['distancePc'] is not None for s in a),8714)
 def test_stable_sorted_unique_ids(self):
  a=json.loads((ROOT/'data/catalogue-v6_5.json').read_text())['stars']
  self.assertEqual(len(a),len({s['id'] for s in a}));self.assertEqual(a,sorted(a,key=lambda s:(s['vmag'],s['hygId'])))
if __name__=='__main__':unittest.main()
