import unittest,json,hashlib,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class CP75ViewerTests(unittest.TestCase):
 def test_current_viewer_and_worker_builder_exist(self):
  self.assertTrue((R/'tools/build_cp75_viewer.py').is_file(),'CP7.5 worker viewer builder missing')
  self.assertTrue((R/'demo/accepted-sky.mjs').is_file(),'CP7.5 viewer missing')
 def test_default_tier_keeps_fine_structure(self):
  self.assertIn('value="128" selected',(R/'demo/accepted-sky.html').read_text())
 def test_manifest_pins_every_runtime_asset_byte(self):
  m=json.loads((R/'data/registered-starlight/runtime-manifest.json').read_text())
  for d in [m['catalogue'],*m['assets'].values()]:
   data=(R/d['path']).read_bytes();self.assertEqual(len(data),d['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),d['sha256'])
 def test_viewer_includes_explicit_fallback_fault_status_and_no_remote_scripts(self):
  p=R/'dist/accepted-physical-sky-viewer.html';self.assertTrue(p.is_file(),'CP7.5 embedded viewer missing')
  s=p.read_text();self.assertIn('LatestRenderQueue',s);self.assertIn('main-thread-fallback',s);self.assertIn('cp6-fallback',s);self.assertIn('assetFault',s);self.assertNotRegex(s,r'<script[^>]+src=["\']https?://')
if __name__=='__main__':unittest.main()
