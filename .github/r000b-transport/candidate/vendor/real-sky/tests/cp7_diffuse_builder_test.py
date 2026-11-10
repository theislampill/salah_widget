import unittest,sys,json,math,gzip,csv,io
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_diffuse_diagnostic import partition,deposit,cell_areas,spherical_smooth,rebin_flux,map_asset

def row(i,**kw):
 r=dict(id=str(i),hip='',hd='',hr='',ra='1',dec='0',mag='8',comp='1',comp_primary=str(i));r.update({k:str(v) for k,v in kw.items()});return r

def point(i,enabled=True,mag=8):return {'hygId':i,'vmag':mag,'emission':{'enabled':enabled}}
def source(ra=0,dec=0,flux=1):return {'raDeg':ra,'decDeg':dec,'relativeV0Flux':flux,'category':'residual-diagnostic'}
class DiffuseBuilderTests(unittest.TestCase):
 def test_runtime_emitter_and_withheld_both_excluded(self):
  a=partition([row(1),row(2),row(3)],[point(1),point(2,False)])
  self.assertEqual([r['category'] for r in a],['runtime-emitter','runtime-withheld','residual-diagnostic'])
 def test_alias_shared_with_runtime_is_not_faint_background(self):
  a=partition([row(1,hd=10),row(2,hd=10)],[point(1)])
  self.assertEqual(a[1]['category'],'linked-to-runtime-withheld')
 def test_components_linked_transitively_to_runtime_are_excluded(self):
  a=partition([row(1),row(2,comp_primary=1,comp=2),row(3,comp_primary=2,comp=3)],[point(1)])
  self.assertTrue(all(r['category']=='linked-to-runtime-withheld' for r in a[1:]))
 def test_source_only_ambiguous_groups_not_invented_deblending(self):
  a=partition([row(1,hip=10),row(2,hip=10)],[])
  self.assertTrue(all(r['category']=='ambiguous-source-group-withheld' for r in a))
 def test_missing_component_primary_is_withheld(self):self.assertEqual(partition([row(1,comp_primary=999)],[])[0]['category'],'ambiguous-source-group-withheld')
 def test_sun_not_stellar_field(self):self.assertEqual(partition([row(0,mag=-26)],[])[0]['relativeV0Flux'],0)
 def test_photometric_drift_is_refused(self):
  with self.assertRaises(ValueError):partition([row(1)],[point(1,mag=7)])
 def test_duplicate_hyg_identity_refused(self):
  with self.assertRaises(ValueError):partition([row(1),row(1)],[])
 def test_spherical_cell_areas_cover_sphere(self):
  for w,h in [(16,8),(64,32),(256,128)]:self.assertAlmostEqual(float(cell_areas(w,h).sum()*w),4*math.pi,12)
 def test_deposition_conserves_flux_at_wrap_and_poles(self):
  es=[source(ra,dec,1.23) for ra in [0,359.999,180] for dec in [-90,0,90]]
  self.assertAlmostEqual(float(deposit(es,32,16).sum()),len(es)*1.23,12)
 def test_ra_periodicity(self):np.testing.assert_allclose(deposit([source(0)],32,16),deposit([source(360)],32,16),atol=1e-15)
 def test_smoothing_conserves_flux(self):
  f=deposit([source(0,0),source(170,89,2)],32,16);a,r=spherical_smooth(f)
  self.assertAlmostEqual(float(a.sum()),3,11);self.assertTrue((a>=0).all())
 def test_smoothing_preserves_constant_surface_brightness(self):
  f=cell_areas(32,16)[:,None]*np.ones((16,32));a,r=spherical_smooth(f)
  np.testing.assert_allclose(a,f,rtol=1e-11,atol=1e-13)
 def test_smoothing_azimuth_rotation_commutes(self):
  f=deposit([source(30,40)],32,16);a,_=spherical_smooth(f);b,_=spherical_smooth(np.roll(f,3,axis=1));np.testing.assert_allclose(b,np.roll(a,3,axis=1),atol=1e-13)
 def test_area_rebin_preserves_flux_and_constant_field(self):
  f=cell_areas(32,16)[:,None]*np.ones((16,32))*2;a=rebin_flux(f);self.assertAlmostEqual(a.sum(),f.sum(),12);np.testing.assert_allclose(a/cell_areas(16,8)[:,None],2,atol=1e-13)
 def test_rebin_rejects_nondividing_factor(self):
  with self.assertRaises(ValueError):rebin_flux(np.zeros((7,8)),2)
 def test_asset_cannot_call_itself_a_survey(self):
  a=map_asset(np.ones((4,8)), 'a'*64,'b'*64,{})
  self.assertFalse(a['productionAdmissible']);self.assertIsNone(a['observationalCoverage']);self.assertIn('not-survey',a['role'])
 def test_rejects_negative_flux_and_invalid_filter(self):
  with self.assertRaises(ValueError):spherical_smooth(-np.ones((4,8)))
  with self.assertRaises(ValueError):spherical_smooth(np.ones((4,8)),float('nan'))
if __name__=='__main__':unittest.main()

class RetainedAssetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads((ROOT/'checkpoints/cp7_2/build-report.json').read_text())
 def test_full_source_partition_counts(self):
  self.assertEqual(sum(self.report['partitionCounts'].values()),119626)
  self.assertEqual(self.report['residualSourceCount'],109852)
 def test_all_runtime_rows_absent_not_just_bright_emitters(self):
  self.assertTrue(self.report['allRuntimeRowsExcluded']);self.assertEqual(self.report['runtimeEmittingIdIntersection'],[])
 def test_asset_hashes_and_finite_nonnegative_values(self):
  import hashlib
  for record in self.report['assets']:
   p=ROOT/record['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),record['sha256']);a=json.loads(p.read_text());self.assertTrue(all(math.isfinite(v) and v>=0 for v in a['values']));self.assertEqual(len(a['values']),record['width']*record['height'])
 def test_all_tiers_have_same_source_flux_and_closed_production_gate(self):
  expected=self.report['fluxBudgetRelativeV0']['residual-diagnostic']
  for record in self.report['assets']:
   a=json.loads((ROOT/record['path']).read_text());self.assertFalse(a['productionAdmissible']);self.assertAlmostEqual(a['totalRelativeV0Flux'],expected,10)
 def test_partition_trace_has_unique_ids_and_no_point_rows_as_residual(self):
  es=list(csv.DictReader(io.StringIO(gzip.decompress((ROOT/'data/diffuse/finite-source-partition.csv.gz').read_bytes()).decode())))
  self.assertEqual(len({e['hygId'] for e in es}),len(es));ids={str(s['hygId']) for s in json.loads((ROOT/'data/bright-stars.json').read_text())['stars']}
  self.assertFalse(any(e['hygId'] in ids and e['category']=='residual-diagnostic' for e in es))
