"""Entry transaction controls with tiny synthetic payloads; no renderer qualification."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[2]/'tools/build_moon.py'
sys.path.insert(0,str(SOURCE.parent))
SPEC=importlib.util.spec_from_file_location('moon_builder',SOURCE)
builder=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(builder)
PLAIN='<!doctype html><html><head></head><body><script>\nboot();\n</script></body></html>'
sha=lambda b:hashlib.sha256(b).hexdigest()

def fixture():
 root=Path(tempfile.mkdtemp(prefix='salah-moon-build-guard-'))
 moon=root/'moon'
 for directory in [moon/'src',moon/'assets',root/'real-sky']:
  directory.mkdir(parents=True)
 for name in set(builder.WORKER_UNITS+builder.HOST_UNITS+['moon-native.mjs','moon_kernel.c']):
  (moon/'src'/name).write_text('// Synthetic build control.\n',encoding='utf-8')
 (root/'real-sky/native-cloud-transfer.mjs').write_text('// Synthetic build control.\n')
 data=b'fixture';wasm=b'fixture-wasm';initial=b'fixture-initial'
 (moon/'assets/data.bin').write_bytes(data);(moon/'moon_kernel.wasm').write_bytes(wasm)
 (moon/'assets/initial-receivers.bin').write_bytes(initial)
 asset={'path':'assets/data.bin','bytes':len(data),'sha256':sha(data),'rawSha256':sha(data)}
 manifest={'assets':{'dem':asset,'colour':asset},'wasm':{'bytes':len(wasm),'sha256':sha(wasm)}}
 raw=json.dumps(manifest).encode();(moon/'asset-manifest.json').write_bytes(raw)
 pin={'bytes':len(initial),'sha256':sha(initial),'source':{},'parent':{'manifestSha256':sha(raw),'wasmSha256':sha(wasm),'demRawSha256':sha(data),'colourRawSha256':sha(data)}}
 (moon/'initial-manifest.json').write_text(json.dumps(pin))
 pin.update(schema='moon-initial-receivers/1',size=1,records=1,geometry={})
 (moon/'initial-manifest.json').write_text(json.dumps(pin))
 (root/'src/native').mkdir(parents=True);(root/'src/native/index.html').write_text('// Synthetic native owner')
 (root/'tools').mkdir();(root/'tools/compact_receivers.py').write_bytes((SOURCE.parent/'compact_receivers.py').read_bytes())
 for name in ['index.html','offline.html']:(root/name).write_text(PLAIN)
 # Preserve the small fixture after the test so rejected effects remain inspectable.
 print('Retained fixture: '+str(root))
 return root

def inventory(root):
 return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}

class MoonBuildGuard(unittest.TestCase):
 def setUp(self):
  # These transaction controls deliberately use tiny synthetic renderer inputs.
  # The real compact source/codec is qualified separately; never relax its pin.
  def compact(data):
   return data,{'schema':'fixture-only','sha256':sha(data),'decodedSha256':sha(data),'fields':[]}
  self.compact=patch.object(builder,'compact_receivers',compact);self.compact.start();self.addCleanup(self.compact.stop)
  self.native=patch.object(builder,'native_lunar_owner',lambda root:'// Synthetic native owner');self.native.start();self.addCleanup(self.native.stop)
 def test_fresh_build_then_duplicate_is_rejected_before_any_write(self):
  root=fixture();builder.build_moon(root)
  self.assertEqual((root/'index.html').read_text().count('window.__SALAH_MOON_INLINE__=true'),1)
  before=inventory(root)
  with self.assertRaises(ValueError):
   builder.build_moon(root)
  self.assertEqual(inventory(root),before)
 def test_offline_duplicate_is_checked_before_index_changes(self):
  root=fixture();builder.build_moon(root);(root/'index.html').write_text(PLAIN)
  before=inventory(root)
  with self.assertRaises(ValueError):
   builder.build_moon(root)
  self.assertEqual(inventory(root),before)
 def test_invalid_offline_boundary_is_checked_before_any_write(self):
  root=fixture();(root/'offline.html').write_text(PLAIN.replace('\nboot();',''))
  before=inventory(root)
  with self.assertRaisesRegex(ValueError,'boot boundary'):
   builder.build_moon(root)
  self.assertEqual(inventory(root),before)

if __name__=='__main__':unittest.main()
