"""Pure host-observer controls: no browser or native acceptance."""
import importlib.util, os, unittest
from unittest.mock import patch
from pathlib import Path
path=Path(os.environ.get("R0007_TIMING_DRIVER", str(Path(__file__).resolve().parents[1]/"tools/cp9/r0007_browser.py")))
spec=importlib.util.spec_from_file_location("timing_subject",path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class TimingTests(unittest.TestCase):
 def test_exact_return_and_single_execution(self):
  trace={}; result=object(); calls=[]
  with patch.object(module.time,"monotonic_ns",side_effect=[100,250]):
   actual=module.observe_operation(trace,3,"capture.receipt",lambda:(calls.append("called"),result)[1])
  self.assertIs(actual,result);self.assertEqual(calls,["called"])
  self.assertEqual(trace["operationTimings"],[{"actionIndex":3,"operation":"capture.receipt","clock":"host-monotonic-ns","started":100,"returned":True,"finished":250,"elapsedNs":150}])
 def test_same_exception_propagates_with_failed_timing(self):
  trace={}; failure=ValueError("retained original failure"); calls=[]
  def operation(): calls.append("called");raise failure
  with patch.object(module.time,"monotonic_ns",side_effect=[100,300]):
   with self.assertRaises(ValueError) as caught:module.observe_operation(trace,4,"release",operation)
  self.assertIs(caught.exception,failure);self.assertEqual(calls,["called"])
  row=trace["operationTimings"][0];self.assertFalse(row["returned"]);self.assertEqual(row["errorType"],"ValueError");self.assertEqual(row["elapsedNs"],200)
 def test_pending_operation_is_recorded_before_execution_without_page_calls(self):
  trace={}
  def operation():
   row=trace["operationTimings"][0];self.assertFalse(row["returned"]);self.assertNotIn("finished",row);return False
  with patch.object(module.time,"monotonic_ns",side_effect=[50,50]):
   self.assertIs(module.observe_operation(trace,0,"wait",operation),False)
  self.assertEqual(trace["operationTimings"][0]["elapsedNs"],0)
if __name__=="__main__":unittest.main()
