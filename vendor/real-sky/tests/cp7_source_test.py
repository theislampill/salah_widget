import unittest,sys,json,hashlib,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from inspect_diffuse_source import read_retained_catalogue,assert_survey_admitted,write_greyscale_png
class SourceGateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows,cls.auth=read_retained_catalogue(ROOT/'upstream/hygdata_v40.csv.gz');cls.gate=json.loads((ROOT/'provenance/cp7/source-gate.json').read_text())
 def test_full_retained_hyg_is_authenticated(self):
  self.assertEqual(self.auth['gitBlobSha1'],'c119fd384ed53d95f8c62d32e9dcdee5f7248dbb');self.assertEqual(len(self.rows),119626)
 def test_gate_is_not_promoted_by_catalogue_presence(self):
  with self.assertRaisesRegex(ValueError,'CP7_SURVEY_SOURCE_BLOCKED'):assert_survey_admitted(self.gate)
 def test_boolean_alone_cannot_admit_source(self):
  for value in [None,{},'yes',False]:
   with self.assertRaises(ValueError):assert_survey_admitted({'productionSourceAdmitted':True,'admittedSurvey':value})
 def test_claimed_survey_needs_science_and_permission_metadata(self):
  with self.assertRaises(ValueError):assert_survey_admitted({'productionSourceAdmitted':True,'admittedSurvey':{'path':'fake'}})
 def test_source_dispositions_do_not_claim_array_acquisition(self):
  self.assertTrue(all(not c['localScienceBytesAcquired'] for c in self.gate['candidates']));self.assertIsNone(self.gate['admittedSurvey'])
 def test_known_sun_is_not_a_diffuse_source(self):self.assertEqual(sum(r['id']=='0' for r in self.rows),1)
 def test_runtime_all_identities_exist_in_source(self):
  ids={int(r['id']) for r in self.rows};cat=json.loads((ROOT/'data/bright-stars.json').read_text())
  self.assertTrue(all(s['hygId'] in ids for s in cat['stars']))
 def test_corrupt_source_rejected_before_use(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.csv';p.write_bytes(b'id,ra\n1,0\n')
   with self.assertRaises(ValueError):read_retained_catalogue(p)
 def test_count_preview_is_valid_png_and_deterministic(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.png';b=Path(d)/'b.png';write_greyscale_png(a,2,2,[0,1,2,3]);write_greyscale_png(b,2,2,[0,1,2,3]);self.assertEqual(a.read_bytes(),b.read_bytes());self.assertTrue(a.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
if __name__=='__main__':unittest.main()
