import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class BuildContract(unittest.TestCase):
 def test_builder_exists(self):
  self.assertTrue((ROOT/'tools/build_moon.py').is_file(), 'Missing deterministic authored-source Moon builder')
 def test_asset_identification(self):
  m=json.loads((ROOT/'moon/asset-manifest.json').read_text())
  for s in list(m['assets'].values())+[dict(m['wasm'],path='moon_kernel.wasm')]:
   p=ROOT/'moon'/s['path'];self.assertEqual(p.stat().st_size,s['bytes']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
