"""CP3 source and ontology contract tests, independent of browser presentation."""
import unittest,sys,json,math,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build_ontology as api
class OntologyBuilderTests(unittest.TestCase):
 def test_all_source_blobs_authenticate(self):
  for name in api.PINS:self.assertTrue(api.checked(ROOT,name))
 def test_tampered_source_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'upstream').mkdir();(p/'upstream/constellation_names.dat').write_text('altered')
   with self.assertRaises(ValueError):api.checked(p,'constellation_names.dat')
 def test_incomplete_pattern_population_rejected(self):
  with self.assertRaises(ValueError):api.read_patterns('Ori 1 27989 24436')
 def test_bad_pair_count_rejected(self):
  with self.assertRaises(ValueError):api.read_patterns('Ori 2 27989 24436')
 def test_table_incomplete_rejected(self):
  with self.assertRaises(ValueError):api.parse_table('0 24 -90 Oct')
 def test_boundary_adjacent_regions_are_distinct(self):
  a=json.loads((ROOT/'data/constellations.json').read_text());self.assertEqual(len(a['regions']),88)
  self.assertAlmostEqual(sum(x['areaSteradians'] for x in a['regions']),4*math.pi,places=10)
  for edge in a['edges']:self.assertNotEqual(*edge['regions'])
 def test_faint_anchor_is_exception_not_brightened(self):
  a=json.loads((ROOT/'data/bright-stars.json').read_text())['stars'];extra=[s for s in a if s['vmag']>6.5]
  self.assertEqual([(s['hip'],s['vmag']) for s in extra],[(33165,6.65)]);self.assertTrue(extra[0]['isRequiredEndpoint'])
if __name__=='__main__':unittest.main()
