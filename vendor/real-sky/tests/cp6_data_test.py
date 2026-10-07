import unittest,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class CP6DataTests(unittest.TestCase):
 def test_fixture_matrix(self):
  f=json.loads((R/'tests/fixtures/cp6-illumination.json').read_text());self.assertEqual(len(f['rows']),3456);self.assertEqual(len({(x['observer']['utcMs'],x['site']) for x in f['rows']}),3456)
 def test_fixture_numbers(self):
  f=json.loads((R/'tests/fixtures/cp6-illumination.json').read_text())
  for x in f['rows']:
   for body in ['sun','moon']:
    self.assertTrue(all(math.isfinite(v) for v in x[body].values()));self.assertGreater(x[body]['distanceKm'],0)
 def test_conditions_not_measured_weather(self):
  d=json.loads((R/'data/atmosphere-scenes.json').read_text());self.assertIn('not measured',d['conditions']);self.assertEqual(len(d['scenes']),7)
 def test_no_new_generated_point_source_dataset(self):
  d=json.loads((R/'data/bright-stars.json').read_text());self.assertEqual(len(d['stars']),8921)
