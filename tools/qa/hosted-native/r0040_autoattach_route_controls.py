"""Exact opt-in selection and failure precedence, with no native execution."""
import sys
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import lanes
import r0040_autoattach_central as automatic


class AutomaticRouteControls(unittest.TestCase):
    def test_explicit_new_mode_selects_only_original_chromium_r0040_population(self):
        self.assertEqual(lanes.rain_mode('capture-mechanism-autoattach',['R0040'],'chromium'),'capture-mechanism-autoattach')
        for selected,engine in [(['R0040','R0035'],'chromium'),(['R0035'],'chromium'),(['R0040'],'firefox')]:
            with self.assertRaises(ValueError):
                lanes.rain_mode('capture-mechanism-autoattach',selected,engine)

    def test_all_old_r0040_modes_keep_their_existing_selection(self):
        for mode in ['options','capture','capture-dateonly','capture-passive','capture-mechanism']:
            self.assertEqual(lanes.rain_mode(mode,['R0040'],'chromium'),mode)

    def test_current_central_refuses_missing_changed_or_aliased_new_source_bytes(self):
        with tempfile.TemporaryDirectory(prefix='autoattach-source-closure-') as temporary:
            root=Path(temporary)
            for name in automatic.verify_sources(): shutil.copy2(HERE/name,root/name)
            with patch.object(automatic,'HERE',root):
                automatic.verify_sources()
                for name in ('r0040_autoattach.cjs','r0040_autoattach_network.cjs','r0040_mechanism.cjs','r0040_mechanism_network.cjs'):
                    original=(root/name).read_bytes()
                    for change in ('missing','changed','symlink'):
                        with self.subTest(name=name,change=change):
                            (root/name).unlink()
                            if change=='changed': (root/name).write_bytes(original+b'\n// changed source\n')
                            if change=='symlink': (root/name).symlink_to(HERE/name)
                            with self.assertRaises((ValueError,OSError)): automatic.verify_sources()
                            if (root/name).is_symlink() or (root/name).exists(): (root/name).unlink()
                            (root/name).write_bytes(original)

    def test_actual_entry_import_refuses_changed_automatic_helper_before_any_driver(self):
        with tempfile.TemporaryDirectory(prefix='autoattach-entry-closure-') as temporary:
            root=Path(temporary)
            for name in automatic.verify_sources(): shutil.copy2(HERE/name,root/name)
            command=['node','-e',"require(process.argv[1]).verifySources()",str(root/'r0040_autoattach.cjs')]
            good=subprocess.run(command,capture_output=True,timeout=5)
            self.assertEqual(good.returncode,0,good.stderr)
            with (root/'r0040_autoattach_network.cjs').open('ab') as file: file.write(b'\n// changed observer\n')
            bad=subprocess.run(command,capture_output=True,timeout=5)
            self.assertEqual(bad.returncode,1)
            self.assertIn(b'mechanism dependency source drift: r0040_autoattach_network.cjs',bad.stderr)
            self.assertNotIn(b'playwright',bad.stderr)

    def test_explicit_current_caller_population_binds_new_caller_without_replacing_old(self):
        self.assertEqual(automatic.CALLER_FILES[:8],('r0040_autoattach_central.py','r0040_mechanism_central.py',
            'r0040_passive_central.py','lanes.py','observe.py','capture_pipeline.py','prepare.py','r0040_capture_prepare.py'))
        self.assertEqual(set(automatic.CALLER_FILES),set(automatic.composed.producer_source_files()))
        with tempfile.TemporaryDirectory(prefix='autoattach-caller-closure-') as temporary:
            root=Path(temporary)/'tools/qa/hosted-native';root.mkdir(parents=True)
            for name in automatic.CALLER_FILES:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,target)
            with patch.object(automatic,'HERE',root):
                before=automatic.caller_sources()
                with (root/'r0040_autoattach_central.py').open('ab') as file: file.write(b'\n# changed caller\n')
                after=automatic.caller_sources()
                self.assertNotEqual(before['r0040_autoattach_central.py'],after['r0040_autoattach_central.py'])
                self.assertEqual({k:v for k,v in before.items() if k!='r0040_autoattach_central.py'},
                                 {k:v for k,v in after.items() if k!='r0040_autoattach_central.py'})
                for name in ('r002f_bfcache_preload.cjs','r0040_autoattach_network.cjs','retention-pins.json',
                             '../../../docs/state-contracts/R0040-native-capture-preflight.md','node/package-lock.json'):
                    original=(root/name).read_bytes();(root/name).unlink()
                    with self.assertRaises((ValueError,OSError)):automatic.caller_sources()
                    (root/name).write_bytes(original+b'\n')
                    self.assertNotEqual(before[name],automatic.caller_sources()[name])
                    (root/name).unlink();(root/name).symlink_to(HERE/name)
                    with self.assertRaises((ValueError,OSError)):automatic.caller_sources()
                    (root/name).unlink();(root/name).write_bytes(original)


if __name__=='__main__':
    unittest.main()
