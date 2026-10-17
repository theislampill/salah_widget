"""Controls for the native sunset source-frame regression detector."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('solar_continuity',Path(__file__).resolve().parents[1]/'tools/cp9/solar_continuity.py')
owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)

def frames(sun):
    return [{'seq':i,'at':i*.041,'roiReadable':True,'sun':[s,s,s],'reference':[140,155,177]} for i,s in enumerate(sun)]

class SolarContinuity(unittest.TestCase):
    def test_fixed_roi_requires_matching_geometry_clock_and_location(self):
        fixture={'scene':'day','stamp':'2026-09-25T22:54:15Z','dpr':1,'entry':'direct',
                 'viewport':{'width':390,'height':600},'runs':[{'video':'fixture.webm','at30s':{
                 'card':{'x':0,'y':0,'width':325,'height':530},
                 'native':{'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','timeScale':1}}}]}
        self.assertEqual(owner.fixture_errors(fixture),[])
        import copy
        for key,value in [('dpr',2),('entry','iframe'),('stamp','2026-09-25T12:00:00Z')]:
            changed=copy.deepcopy(fixture);changed[key]=value
            self.assertTrue(owner.fixture_errors(changed),key)
        for target,key,value in [('card','x',1),('card','width',326),('native','timeScale',600),('native','lat',0)]:
            changed=copy.deepcopy(fixture);changed['runs'][0]['at30s'][target][key]=value
            self.assertTrue(owner.fixture_errors(changed),key)
        changed=copy.deepcopy(fixture);changed['runs'][0]['video']=None
        self.assertTrue(owner.fixture_errors(changed))
    def test_no_readable_triplet_is_incomplete_not_a_negative_result(self):
        for rows in [[],frames([247]),[{**r,'roiReadable':False} for r in frames([247,247,247])]]:
            self.assertEqual(owner.result_for(rows,[]),'INSUFFICIENT_READABLE_TRIPLETS')
        self.assertEqual(owner.result_for(frames([247,247,247]),[]),'NO_ALTERNATION_OBSERVED')
    def test_rapid_solar_on_off_on_at_unchanged_geometry_is_detected(self):
        self.assertEqual(owner.alternations(frames([247,151,247]))[0]['seq'],[0,1,2])
    def test_smooth_or_one_way_weather_change_is_not_strobe(self):
        for signal in [[247,246,247],[247,240,233],[247,151,151]]:
            self.assertEqual(owner.alternations(frames(signal)),[])
    def test_whole_capture_flash_is_not_solar_specific(self):
        rows=frames([247,151,247]);rows[1]['reference']=[255]*3
        self.assertEqual(owner.alternations(rows),[])
    def test_unreadable_missing_or_slow_frames_never_bridge_into_a_triplet(self):
        for kind in ['unreadable','missing','slow']:
            rows=frames([247,151,247])
            if kind=='unreadable':rows[1]['roiReadable']=False
            if kind=='missing':rows[1]['seq']=8
            if kind=='slow':rows[1]['at']=.2;rows[2]['at']=.4
            self.assertEqual(owner.alternations(rows),[])

if __name__=='__main__':unittest.main()
