"""A served Moon asset change must invalidate receiving qualification."""
import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('runtime_identity',ROOT/'tools/cp9/runtime_identity.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MoonRuntimeIdentity(unittest.TestCase):
 def test_all_moon_delivery_paths_are_bound(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)
   for n in ['index.html','offline.html','config.js','builder.html','moon/moon-host.js','moon/moon-worker.js','moon/moon_kernel.wasm','moon/assets/dem.bin.gz','moon/file-data/dem-000.js']:
    p=r/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'original')
   before=m.runtime_identity(r)
   for n in ['moon/moon-host.js','moon/moon-worker.js','moon/moon_kernel.wasm','moon/assets/dem.bin.gz','moon/file-data/dem-000.js']:
    self.assertIn(n,before['files'])
    (r/n).write_bytes(b'changed');self.assertNotEqual(before['treeSha256'],m.runtime_identity(r)['treeSha256']);(r/n).write_bytes(b'original')
if __name__=='__main__':unittest.main()
