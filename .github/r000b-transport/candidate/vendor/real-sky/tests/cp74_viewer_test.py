import unittest,importlib.util,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class CP74ViewerTests(unittest.TestCase):
 def test_builder_exists_and_source_bundle_is_offline(self):
  script=R/'tools/build_cp74_viewer.py';self.assertTrue(script.is_file(),'physical diffuse viewer builder is required')
  spec=importlib.util.spec_from_file_location('builder74',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  result=m.build();html=(R/result['path']).read_text();self.assertNotIn('src="./physical-diffuse.mjs"',html);self.assertIn('window.__physicalDiffuseAssets=',html);self.assertIn('bindRegisteredStarlight',html)
  self.assertIn('one display transform',html);self.assertIn('assumed-nonstellar-residual',html)
 def test_scene_definitions_are_retained_and_explicit(self):
  path=R/'data/cp74-scenes.json';self.assertTrue(path.exists(),'physical scene fixtures required')
  scenes=json.loads(path.read_text());self.assertGreaterEqual(len(scenes),7)
  self.assertTrue(all(s['utc'].endswith('Z') for s in scenes));self.assertTrue(all('atmosphere' in s for s in scenes))
if __name__=='__main__':unittest.main()
