import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/cp9'))
from chromium_startup_defaults import VERSION,OLD_ARGUMENT,NEW_ARGUMENT,restore_options,verify_launch

class StartupDefaults(unittest.TestCase):
 def test_only_render_document_removed_and_existing_options_preserved(self):
  original={'args':['--disable-dev-shm-usage'],'ignore_default_args':['--enable-automation'],'headless':True,'chromium_sandbox':True}
  changed=restore_options(original)
  self.assertEqual(original['args'],['--disable-dev-shm-usage'])
  self.assertEqual(changed['args'],original['args']+[NEW_ARGUMENT])
  self.assertEqual(changed['ignore_default_args'],original['ignore_default_args']+[OLD_ARGUMENT])
  self.assertTrue(changed['chromium_sandbox'])
  self.assertEqual(NEW_ARGUMENT.split('=',1)[1].split(','),[x for x in OLD_ARGUMENT.split('=',1)[1].split(',')if x!='RenderDocument'])
 def test_actual_launch_is_bound_to_one_exact_feature_list_and_version(self):
  self.assertTrue(verify_launch(VERSION,'chrome '+NEW_ARGUMENT)['otherDisabledFeaturesUnchanged'])
  for line in ['chrome '+OLD_ARGUMENT,'chrome',NEW_ARGUMENT+' '+NEW_ARGUMENT,NEW_ARGUMENT+',Unexpected',NEW_ARGUMENT+' --enable-features=RenderDocument']:
   with self.subTest(line=line),self.assertRaises(ValueError):verify_launch(VERSION,line)
  with self.assertRaises(ValueError):verify_launch('149.0.0.0',NEW_ARGUMENT)
if __name__=='__main__':unittest.main()
