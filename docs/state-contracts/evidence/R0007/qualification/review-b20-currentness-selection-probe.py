"""Independent pure launcher probes; no browser/server, target repo edits, or commits."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exact_candidate_native',ROOT/'snapshot/tools/qualification/r0007_native.py')
N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
PACKET=json.loads((ROOT/'snapshot/tests/rlgwo/R0007-next-event-recipes.json').read_text())
class IndependentLauncherProbes(unittest.TestCase):
 def test_each_mutant_closes_healthy_control_selection_before_itself(self):
  for mutant in [c for c in PACKET['cases'] if c.get('expectedFailure')]:
   selected=N.select_cases(PACKET,[mutant['caseId']]);ids=[c['caseId'] for c in selected]
   self.assertEqual(set(ids),set(mutant['healthyControlCaseIds'])|{mutant['caseId']})
   self.assertEqual(ids[-1],mutant['caseId'])
   self.assertTrue(all(not c.get('expectedFailure') for c in selected[:-1]))
 def test_hosted_selection_is_exactly_thirty_unique_cases(self):
  ex=PACKET['execution'];chosen=ex['defaultCaseIds']+ex['conditionalPreservationCaseIds']+ex['mutationCaseIds']
  selected=N.select_cases(PACKET,chosen)
  self.assertEqual(len(selected),30);self.assertEqual({c['caseId'] for c in selected},{c['caseId'] for c in PACKET['cases']})
 def test_unknown_and_unsafe_and_duplicate_case_names_reject(self):
  with self.assertRaises(ValueError):N.select_cases(PACKET,['unknown'])
  for cases in [[{'caseId':'../outside'}],[{'caseId':'same'},{'caseId':'same'}]]:
   with self.assertRaises(ValueError):N.select_cases({'cases':cases},[])
 def test_cross_case_cache_dependency_and_mutant_as_control_reject(self):
  for change in [{'cacheSeedsFromCase':'source'}, {'expectedFailure':True,'expectedFailureContains':'wanted','healthyControlCaseIds':['a']}]:
   with self.assertRaises(ValueError):N.select_cases({'cases':[{'caseId':'a',**change}]},[])
 def test_dirty_identity_refuses_source(self):
  root=ROOT.resolve()
  with patch.object(N,'git',side_effect=[str(root),' M index.html']):
   with self.assertRaisesRegex(ValueError,'not clean'):N.clean_identity(root)
 def test_ignored_uncommitted_recipe_must_not_claim_commit_binding(self):
  # Simulate the clean Git interface for a source tree containing an ignored
  # __pycache__/ recipe. Candidate .gitignore explicitly ignores __pycache__.
  # Only filesystem inputs and the tracked runtime census are exercised here.
  # The test does not create a Git commit or mutate the review target.
  with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
   root=Path(temp).resolve();recipe=root/'__pycache__/uncommitted-recipe.json'
   required={'src/native/index.html','index.html','offline.html','config.js',N.DRIVER,N.FIXTURE,N.RUNTIME,'tools/qualification/r0007_native.py'}
   for rel in required:
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'SYNTHETIC INPUT ONLY')
   recipe.parent.mkdir(parents=True,exist_ok=True)
   original={'schema':'remaining-prayer-cases/v1','issue':7,'cases':[copy.deepcopy(PACKET['cases'][0])]}
   recipe.write_text(json.dumps(original))
   calls=[]
   def git(root,*args):
    calls.append(args)
    if args==('rev-parse','--show-toplevel'):return str(root)
    if args==('status','--porcelain','--untracked-files=normal'):return ''
    if args==('rev-parse','HEAD'):return 'test-committed-head'
    if args==('rev-parse','HEAD^{tree}'):return 'test-committed-tree'
    if args==('ls-files','--','real-sky','moon'):return ''
    raise AssertionError('Unexpected Git command '+repr(args))
   with patch.object(N,'git',side_effect=git):
    identity=N.clean_identity(root)
    try:result=N.bind_packet(root,recipe,identity,original['cases'])
    except ValueError:return
   print(json.dumps({'probe':'ignored-recipe','acceptedRecipe':result['acquisitionBinding']['recipe'],'claimedCommit':result['sourceCommit'],'recipeHashRecorded':True,'membershipChecked':False,'gitCalls':calls}))
   self.fail('bind_packet accepts an ignored, uncommitted --recipe and labels it with the clean commit/tree')
if __name__=='__main__':unittest.main(verbosity=2)
