import unittest,importlib.util,os
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[2]/'tools/cp9/browser_runtime.py'
class BrowserRuntimeTests(unittest.TestCase):
 def load(self):
  self.assertTrue(P.exists(),'Portable browser selector missing')
  spec=importlib.util.spec_from_file_location('cp9runtime',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_default_uses_chromium(self):
  m=self.load()
  with patch.dict(os.environ,{},clear=True):self.assertEqual(m.browser_options()[0],'chromium')
 def test_explicit_firefox_does_not_fall_back(self):
  m=self.load()
  with patch.dict(os.environ,{'SALAH_BROWSER':'firefox'},clear=True):
   family,opts=m.browser_options();self.assertEqual(family,'firefox');self.assertNotIn('args',opts);self.assertNotIn('executable_path',opts)
 def test_explicit_webkit_does_not_gain_chromium_flags(self):
  m=self.load()
  with patch.dict(os.environ,{'SALAH_BROWSER':'webkit'},clear=True):self.assertNotIn('args',m.browser_options()[1])
 def test_bad_family_rejected(self):
  m=self.load()
  with patch.dict(os.environ,{'SALAH_BROWSER':'imaginary'},clear=True):
   with self.assertRaises(ValueError):m.browser_options()
 def test_explicit_binary_is_not_silently_replaced(self):
  m=self.load()
  with patch.dict(os.environ,{'SALAH_BROWSER_EXECUTABLE':'/definitely/missing/executable'},clear=True):
   with self.assertRaises(FileNotFoundError):m.browser_options()
if __name__=='__main__':unittest.main()
