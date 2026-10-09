"""Synthetic predicate controls, explicitly not measured product latency."""
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).resolve().parents[2]/'tools/cp9/first_complete_scene.py'
spec=importlib.util.spec_from_file_location('first_complete_scene',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CompleteScene(unittest.TestCase):
 def receipt(self,**changes):
  return {'browser':'chromium','observerKnown':True,'evidenceKind':'presented-pixels','frames':['bound-frame'],
   'maximumUncoveredMs':40,'sceneMs':300,'acceptedMs':200,'baselineSceneMs':250,
   'moonWarranted':True,'starsWarranted':True,'moonMs':300,'starsMs':340,**changes}
 def test_positive_and_exact_gap_boundary(self):
  self.assertEqual(m.first_complete_scene(self.receipt(starsMs=380))['status'],'PASS')
  self.assertEqual(m.first_complete_scene(self.receipt(starsMs=380.01))['status'],'FAIL')
 def test_old_eventual_ready_counterexamples_fail(self):
  for delay in [500,2000,8000,30000]:
   self.assertEqual(m.first_complete_scene(self.receipt(moonMs=delay,refinedObserved=True,blankAfterSurface=[]))['status'],'FAIL')
 def test_cannot_move_delay_behind_a_loader(self):
  self.assertEqual(m.first_complete_scene(self.receipt(sceneMs=900,acceptedMs=800,moonMs=900,starsMs=900))['status'],'FAIL')
 def test_missing_pixels_or_coverage_are_not_success(self):
  for change in [{'moonMs':None},{'frames':[]},{'evidenceKind':'getter'},{'maximumUncoveredMs':200},{'moonMs':float('nan')}]:
   self.assertEqual(m.first_complete_scene(self.receipt(**change))['status'],'FAIL')
 def test_rain_and_day_only_exempt_demonstrably_unwarranted_components(self):
  self.assertEqual(m.first_complete_scene(self.receipt(starsWarranted=False,starsMs=None))['status'],'PASS')
  self.assertEqual(m.first_complete_scene(self.receipt(starsMs=None))['status'],'FAIL')
 def test_acquisition_is_not_celestial_qualification(self):
  self.assertEqual(m.first_complete_scene(self.receipt(observerKnown=False))['status'],'SEPARATE_ACQUISITION_CASE')
 def test_later_blank_is_not_repaired_startup(self):
  self.assertEqual(m.first_complete_scene(self.receipt(laterUnwarrantedGaps=[3000]))['status'],'FAIL')
 def test_coverage_must_be_a_finite_nonnegative_number(self):
  for value in [None,False,True,-1,float('nan'),float('inf'),float('-inf'),'40']:
   with self.subTest(value=value):
    self.assertEqual(m.first_complete_scene(self.receipt(maximumUncoveredMs=value))['status'],'FAIL')
  for value in [0,80]:
   self.assertEqual(m.first_complete_scene(self.receipt(maximumUncoveredMs=value))['status'],'PASS')
  self.assertEqual(m.first_complete_scene(self.receipt(maximumUncoveredMs=80.01))['status'],'FAIL')
 def test_acceptance_cannot_follow_its_complete_presentation(self):
  self.assertEqual(m.first_complete_scene(self.receipt(acceptedMs=340))['status'],'PASS')
  self.assertEqual(m.first_complete_scene(self.receipt(acceptedMs=340.01))['status'],'FAIL')
  self.assertEqual(m.first_complete_scene(self.receipt(acceptedMs=1000))['status'],'FAIL')
  self.assertEqual(m.first_complete_scene(self.receipt(acceptedMs=90))['status'],'PASS')
  self.assertEqual(m.first_complete_scene(self.receipt(acceptedMs=89.99))['status'],'FAIL')

if __name__=='__main__':unittest.main()
