"""Pure host-observer controls: no browser or native acceptance."""
import ast, copy, importlib.util, json, os, unittest
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
class DiagnosticSleepDispatchTests(unittest.TestCase):
 def setUp(self):
  # Execute the actual dispatcher and its actual local measure wrapper. Only
  # external time and browser boundaries are replaced; no browser is launched.
  tree=ast.parse(path.read_text(encoding="utf-8"))
  measures=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="measure"]
  loops=[n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple)
         and [getattr(x,"id",None) for x in n.target.elts]==["action_index","action"]]
  self.assertEqual(len(measures),1);self.assertEqual(len(loops),1)
  self.dispatch=compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(measures[0]),copy.deepcopy(loops[0])],type_ignores=[])),str(path),"exec")
  helper_path=path.with_name("r0007_font_ingress.py")
  helper_spec=importlib.util.spec_from_file_location("sleep_error_boundary",helper_path)
  self.helper=importlib.util.module_from_spec(helper_spec);helper_spec.loader.exec_module(self.helper)
 def environment(self,active):
  namespace=dict(vars(module));trace={"actions":[]};calls=[]
  class Frame:
   def evaluate(self,expression,argument):calls.append((expression,argument));return True
  actions=[{"type":"sleep","ms":250},{"type":"release","id":"capture-current"}]
  namespace.update(trace=trace,case={"orderedActions":actions},ingress_active=active,ingress_module=self.helper,frame=Frame())
  return namespace,trace,calls
 def test_diagnostic_dispatch_records_requested_sleep_and_elapsed_span_before_release(self):
  # A missing timing branch, duplicate sleep, changed delay or early release
  # must fail. The 7.640-second value is a synthetic clock witness only.
  namespace,trace,calls=self.environment(True);requested=[]
  def sleep(seconds):
   self.assertEqual(calls,[]);requested.append(seconds)
  with patch.object(module.time,"sleep",side_effect=sleep),patch.object(module.time,"monotonic_ns",side_effect=[1000000000,8640000000,9000000000,9000000100]):
   exec(self.dispatch,namespace)
  self.assertEqual(requested,[0.25]);self.assertEqual(len(calls),1)
  self.assertEqual(calls[0][1],["release","capture-current",1])
  self.assertEqual(trace["actions"],[{"type":"sleep","ms":250},{"type":"release","id":"capture-current"}])
  self.assertEqual([r["operation"] for r in trace["operationTimings"]],["sleep","release"])
  self.assertEqual(trace["operationTimings"][0],{"actionIndex":0,"operation":"sleep","clock":"host-monotonic-ns","started":1000000000,"returned":True,"finished":8640000000,"elapsedNs":7640000000})
  self.assertEqual(trace["operationTimings"][1]["started"],9000000000)
 def test_absent_diagnostic_keeps_existing_unmeasured_sleep_dispatch(self):
  namespace,trace,calls=self.environment(False);requested=[]
  with patch.object(module.time,"sleep",side_effect=requested.append),patch.object(module.time,"monotonic_ns",side_effect=[100,200]):
   exec(self.dispatch,namespace)
  self.assertEqual(requested,[0.25]);self.assertEqual(len(calls),1)
  self.assertEqual([r["operation"] for r in trace["operationTimings"]],["release"])
 def test_failed_sleep_is_recorded_and_release_is_not_attempted(self):
  namespace,trace,calls=self.environment(True)
  with patch.object(module.time,"sleep",side_effect=RuntimeError("synthetic-untrusted-error-marker")),patch.object(module.time,"monotonic_ns",side_effect=[100,300]):
   with self.assertRaises(RuntimeError) as caught:exec(self.dispatch,namespace)
  self.assertEqual(calls,[]);self.assertEqual(trace["actions"],[{"type":"sleep","ms":250}])
  self.assertIn("operationTimings",trace,"failed diagnostic sleep needs its own original timing receipt")
  row=trace["operationTimings"][0]
  self.assertEqual(row["operation"],"sleep");self.assertFalse(row["returned"])
  self.assertEqual(row["errorType"],"RuntimeError");self.assertEqual(row["elapsedNs"],200)
  self.assertNotIn("synthetic-untrusted-error-marker",str(caught.exception)+json.dumps(trace))
  self.assertIsNone(caught.exception.__cause__)

if __name__=="__main__":unittest.main()
