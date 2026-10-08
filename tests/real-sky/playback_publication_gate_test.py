"""Continuous presentation evidence must gate success, not just sampled PNGs."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'cp9'))
import hotfix_stress_check as runner

class PlaybackPublicationGate(unittest.TestCase):
    def test_good_current_preview_is_eligible_without_claiming_refined_throughput(self):
        self.assertEqual(runner.playback_publication_failures({'presentedAge':{
            'samples':100,'expiredFrames':0,'unavailableFrames':0,'maximumCurrentAgeMs':27120}}), [])

    def test_telemetry_only_expiry_and_gap_fail_even_if_every_screenshot_passes(self):
        for field in ['expiredFrames','unavailableFrames']:
            evidence={'samples':100,'expiredFrames':0,'unavailableFrames':0,'maximumCurrentAgeMs':27120}
            evidence[field]=1
            self.assertTrue(runner.playback_publication_failures({'failures':[], 'presentedAge':evidence}))

    def test_missing_or_internally_inconsistent_observation_does_not_pass(self):
        self.assertTrue(runner.playback_publication_failures({}))
        self.assertTrue(runner.playback_publication_failures({'presentedAge':{
            'samples':100,'expiredFrames':0,'unavailableFrames':0,'maximumCurrentAgeMs':30060}}))

if __name__ == '__main__': unittest.main()
