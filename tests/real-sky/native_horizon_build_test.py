"""The boundary correction must fail closed if its immutable input drifts."""
from pathlib import Path
import sys,unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from native_core_horizon import correct_horizon

class HorizonBuildTest(unittest.TestCase):
    def test_source_drift_is_not_silently_patched(self):
        source=(ROOT/'vendor/real-sky/src/physical-sky-renderer.mjs').read_bytes()
        self.assertEqual(correct_horizon(source),(ROOT/'real-sky/core/src/physical-sky-renderer.mjs').read_bytes())
        with self.assertRaisesRegex(ValueError,'source drift'):
            correct_horizon(source+b'\n')

if __name__=='__main__':unittest.main()
