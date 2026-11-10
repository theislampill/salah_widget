"""The evidence collector must not turn missing observations into a PASS."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'cp9'))
from moon_continuity_check import observer_coverage


class ContinuityObserverTest(unittest.TestCase):
 def sample(self):
  return {'frames':[{'at':t} for t in range(0,10001,1000)]},[{'at':20},{'capturedAt':10100}]

 def test_dense_complete_receipt(self):
  telemetry,rows=self.sample()
  self.assertTrue(all(observer_coverage(telemetry,rows,10)['checks'].values()))

 def test_recorded_exception_rejects_otherwise_good_observations(self):
  telemetry,rows=self.sample();telemetry['error']='controlled observer failure'
  self.assertFalse(observer_coverage(telemetry,rows,10)['checks']['observerNoError'])

 def test_missing_middle_observations(self):
  telemetry,rows=self.sample();del telemetry['frames'][3:6]
  self.assertFalse(observer_coverage(telemetry,rows,10)['checks']['observerHeartbeat'])

 def test_observer_stops_before_last_capture(self):
  telemetry,rows=self.sample();telemetry['frames']=telemetry['frames'][:5]
  self.assertFalse(observer_coverage(telemetry,rows,10)['checks']['observerCoversCaptures'])

 def test_requested_full_duration_cannot_pass_truncated_run(self):
  telemetry,rows=self.sample()
  self.assertFalse(observer_coverage(telemetry,rows,60)['checks']['observerFullDuration'])

 def test_empty_nonfinite_and_out_of_order_are_rejected(self):
  for times in [[],[0,float('nan')],[1000,0],[0,0]]:
   with self.subTest(times=times):
    result=observer_coverage({'frames':[{'at':t} for t in times]},[{'at':0,'capturedAt':1000}])
    self.assertFalse(result['checks']['observerOrdered'])


if __name__=='__main__':unittest.main()
