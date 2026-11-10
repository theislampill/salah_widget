import unittest,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class SpectralAssets(unittest.TestCase):
 def test_retained_inputs_are_authenticated(self):
  for s in json.loads((R/'provenance/cp5-spectral-acquisition.json').read_text())['sources']:
   b=(R/s['path']).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),s['sha256'])
   if s['fullBlobVerified']:self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),s['upstreamGitBlob'])
 def test_normalised_spectral_shapes(self):
  d=json.loads((R/'data/spectral-tables.json').read_text())
  for s in d['standards']:
   self.assertEqual(len(s['samples']),95);self.assertTrue(all(x>0 for x in s['samples']))
   self.assertAlmostEqual(sum(x*w*v*dw for x,w,v,dw in zip(s['samples'],d['wavelengthNm'],d['passbands']['V'],d['weightsNm'])),1,12)
 def test_quality_rejection_is_preserved(self):
  d=json.loads((R/'data/spectral-tables.json').read_text());self.assertEqual(d['rejectedStandards'][0]['hr'],4534);self.assertNotIn(4534,[s['hr'] for s in d['standards']])
 def test_runtime_retains_actual_spectral_metadata(self):
  d=json.loads((R/'data/bright-stars.json').read_text());s=next(s for s in d['stars'] if s['hip']==91262);self.assertEqual(s['spectralType'],'A0Vvar');self.assertEqual(s['hr'],7001)
