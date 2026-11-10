import importlib.util,unittest,tempfile,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class SealTests(unittest.TestCase):
 def api(self):
  path=R/'tools/seal_cp7_final.py';self.assertTrue(path.is_file(),'final cumulative seal utility required')
  s=importlib.util.spec_from_file_location('cp7_seal',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_payload_excludes_caches_fonts_and_uncompressed_duplicate(self):
  m=self.api()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)
   for name in ['src/ok.mjs','raw/input.gz','MANIFEST.sha256','node_modules/junk.js','cache/__pycache__/x.pyc','font.ttf','hygdata_v40.csv']:
    p=r/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('data')
   self.assertEqual([p.relative_to(r).as_posix() for p in m.selected(r)],['raw/input.gz','src/ok.mjs'])
 def test_manifest_rejects_changed_payload(self):
  m=self.api()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a';p.write_text('original');manifest={'a':m.sha(p)};m.verify_manifest(r,manifest);p.write_text('changed')
   with self.assertRaises(RuntimeError):m.verify_manifest(r,manifest)
 def test_manifest_rejects_missing_and_unlisted_payload(self):
  m=self.api()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a';p.write_text('original');manifest={'a':m.sha(p)};(r/'extra').write_text('unlisted')
   with self.assertRaises(RuntimeError):m.verify_manifest(r,manifest)
   (r/'extra').unlink();p.unlink()
   with self.assertRaises(RuntimeError):m.verify_manifest(r,manifest)
 def test_symlinks_never_pull_external_bytes_into_archive(self):
  m=self.api()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'local').write_text('ok')
   try:(r/'link').symlink_to(r/'local')
   except OSError:self.skipTest('host cannot create symlinks')
   with self.assertRaises(ValueError):m.selected(r)
