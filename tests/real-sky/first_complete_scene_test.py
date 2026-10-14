"""Synthetic contract controls. No elapsed rendering or native/browser execution."""
import asyncio
import copy
import tempfile
import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cp9'))
from first_complete_scene import first_complete_scene, BUDGETS
from startup_timing import normalize_startup_timing
from startup_capture_clock import CaptureClock
from review_startup_frames import identity_marker, pixel_observation


def ref(label):
    return {'file':'synthetic/'+label,'sha256':hashlib.sha256(label.encode()).hexdigest()}



# Temporary source-contract fixtures, not native/JPEG/browser evidence.
_fixture_directories=[]


def artifact(path):
    return {'file':str(path),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


async def retain_clock_inputs(folder,comparison,width):
    clock=CaptureClock(folder/'clock');clock.clock=copy.deepcopy(comparison['captureClock'])
    clock.now=lambda:10000
    navigation=clock.navigation();clock.now=lambda:99000
    comparison['navigation']=clock.retain_navigation(navigation)
    class ControlledFrame:
        async def evaluate(self,_expression):
            return {'atMs':15000,'clock':copy.deepcopy(comparison['observer']['clock'])}
    sequence=iter([25000-width,25000+width]);clock.now=lambda:next(sequence)
    window=await clock.browser_bridge(ControlledFrame())
    rpc=folder/'rpc';rpc.mkdir()
    async def reply():
        for _ in range(100):
            files=list(rpc.glob('*.request.json'))
            if files:
                request=json.loads(files[0].read_bytes())
                response={'schema':'salah-capture-clock-response/1','requestId':request['requestId'],
                    'clock':{'id':'driver:control','kind':'node-hrtime','unit':'ms'},'atMs':515000}
                write_json(rpc/(request['requestId']+'.response.json'),response)
                return
            await asyncio.sleep(.001)
        raise AssertionError('controlled clock request absent')
    sequence=iter([25000-width,25000+width]);clock.now=lambda:next(sequence)
    task=asyncio.create_task(reply())
    node=await clock.driver_bridge(rpc,timeout=1);await task
    if window is None or node is None:raise AssertionError('controlled clock samples absent')
    comparison['bridges']=[window,node]


def retain_capture(value):
    # Call only when the test intentionally changes producer input/history.
    # Carrier-only negatives deliberately never call this helper.
    comparison=value['timingComparison'];path=Path(comparison['observerArtifact']['file'])
    raw=json.loads(path.read_bytes())
    capture=raw['runs'][0]['captureTiming']
    for key in ['captureClock','navigation','bridges','observer']:
        capture[key]=copy.deepcopy(comparison[key])
    write_json(path,raw);comparison['observerArtifact']=artifact(path)


def retain_window_sample(value,sample):
    comparison=value['timingComparison'];folder=Path(comparison['observerArtifact']['file']).parent
    path=folder/'second-browser-clock.json'
    raw={key:copy.deepcopy(field)for key,field in sample.items()if key!='artifact'}
    raw['sample']={'atMs':sample['sourceAtMs'],'clock':copy.deepcopy(comparison['observer']['clock'])}
    write_json(path,raw);sample['artifact']=artifact(path)


def retain_frame_inputs(value):
    # A coherence control changes actual synthetic callback input, not a carrier.
    observations=value['timingComparison']['observations']
    path=Path(next(iter(observations.values()))['sourceReceipt']['receiptArtifact']['file'])
    rows=[json.loads(line)for line in path.read_text(encoding='utf-8').splitlines()]
    sources={item['sourceReceipt']['eventId']:item['sourceReceipt']for item in observations.values()}
    for row in rows:
        source=sources[row['sourceEventId']]
        row['receiptMonotonicMs']=source['atMs'];row['sourceTimeSeconds']=source['rawProtocolTimeSeconds']
    path.write_text(''.join(json.dumps(row,allow_nan=False)+'\n'for row in rows),encoding='utf-8')
    reference=artifact(path)
    for observation in observations.values():
        observation['sourceReceipt']['receiptArtifact']=copy.deepcopy(reference)
        observation['presentedReceipt']['receiptArtifact']=copy.deepcopy(reference)


def retain_fixture(value,width):
    temporary=tempfile.TemporaryDirectory(prefix='f2-first-admission-')
    _fixture_directories.append(temporary);folder=Path(temporary.name)
    comparison=value['timingComparison'];asyncio.run(retain_clock_inputs(folder,comparison,width))
    video=folder/'synthetic-not-native.webm';frames=Path(str(video)+'.frames');frames.mkdir()
    receipt_path=Path(str(video)+'.frames.jsonl');rows=[]
    for index,(component,observation)in enumerate(comparison['observations'].items(),1):
        pixel=frames/(str(index).zfill(6)+'.jpeg')
        pixel.write_bytes(('SYNTHETIC_NON_JPEG_BYTES_'+component).encode())
        source=observation['sourceReceipt'];presented=observation['presentedReceipt']
        source['artifact']=artifact(pixel);presented['artifact']=copy.deepcopy(source['artifact'])
        rows.append({'seq':index,'file':pixel.name,'bytes':pixel.stat().st_size,
            'sourceTimeSeconds':source['rawProtocolTimeSeconds'],'receiptMonotonicMs':source['atMs'],
            'receiptClock':{'id':source['clockId'],'kind':'node-hrtime','unit':'ms'},
            'sourceEventId':source['eventId'],'presentedReceiptEventId':presented['eventId']})
    receipt_path.write_text(''.join(json.dumps(row,allow_nan=False)+'\n'for row in rows),encoding='utf-8')
    for observation in comparison['observations'].values():
        observation['sourceReceipt']['receiptArtifact']=artifact(receipt_path)
        observation['presentedReceipt']['receiptArtifact']=artifact(receipt_path)
    path=folder/'results.json'
    write_json(path,{'schema':'celestial-startup/1','runs':[{'mode':'synthetic-contract-control',
        'video':str(video),'captureTiming':{key:copy.deepcopy(comparison[key])
            for key in ['captureClock','navigation','bridges','observer']}}]})
    comparison['observerArtifact']=artifact(path)
    return value


def raw_fixture_digests(value):
    folder=Path(value['timingComparison']['observerArtifact']['file']).parent
    return {str(path):hashlib.sha256(path.read_bytes()).hexdigest()
        for path in folder.rglob('*')if path.is_file()}


def fixture(complete=500, baseline=300, width=0):
    doc='control-document';clock='document:'+doc
    b={'sceneIdentity':'source-scene-1','configIdentity':'opaque-nativeIdentity-output', 'generation':0,'dpr':1}
    first={'kind':'valid-shared-scene-admission','eventId':clock+'/a1','admissionId':clock+'/a1',
        'clockId':clock,'documentId':doc,'atMs':300,'binding':b,'source':'head',
        'utcMs':1790294400000,'markerToken':'12345678abcdef0098765432100f00ff'}
    def stage(kind,at,source,index):
        value={'kind':kind,'eventId':clock+'/e'+str(index),'admissionId':first['admissionId'],
            'clockId':clock,'documentId':doc,'atMs':at,'binding':copy.deepcopy(b),'source':source,'utcMs':1790294400000}
        if kind=='head-work-end':value['status']='published'
        return value
    observer={'schema':'salah-startup-timing/1','clock':{'id':clock,'kind':'window-performance',
        'unit':'ms','documentId':doc,'timeOriginMs':1700000000000},'firstValidAdmission':first,
        'admissions':[copy.deepcopy(first)],'events':[stage('head-work-start',301,'head',1),
         stage('head-work-end',370,'head',2),stage('native-adoption',550,'native',3)],
        'rejected':[],'overflow':False}
    bridge=lambda cid,kind,at,center:{'kind':'bracketed-clock-sample','sampleId':'synthetic-'+kind,
        'sourceClockId':cid,'sourceKind':kind,'targetClockId':'capture:control','sourceAtMs':at,
        'targetBeforeMs':center-width,'targetAfterMs':center+width,'artifact':ref(kind+'-clock')}
    comparison={'schema':'salah-startup-comparison/1',
        'captureClock':{'id':'capture:control','kind':'python-monotonic','unit':'ms'},
        'navigation':{'kind':'navigation-request','clockId':'capture:control','atMs':10000,'artifact':ref('navigation')},
        'observer':observer,'observerArtifact':ref('observer'),
        'bridges':[bridge(clock,'window-performance',15000,25000),
          bridge('driver:control','node-hrtime',515000,25000)],'observations':{}}
    for component in ['scene','moon','stars']:
        source={'kind':'native-source-receipt','eventId':'source:'+component,'clockId':'driver:control',
          'atMs':500000+complete,'rawProtocolTimeSeconds':999999.1,'artifact':ref(component+'.jpeg'),
          'receiptArtifact':ref('frames.jsonl')}
        presented={**copy.deepcopy(source),'kind':'presented-pixels-receipt-upper-bound',
          'eventId':'pixel-receipt:'+component,'sourceEventId':source['eventId']}
        comparison['observations'][component]={'admissionId':first['admissionId'],'documentId':doc,
          'binding':copy.deepcopy(b),'markerToken':first['markerToken'],'sourceReceipt':source,'presentedReceipt':presented}
    return retain_fixture({'browser':'chromium','observerKnown':True,'evidenceKind':'presented-pixels',
        'frames':['synthetic-not-a-browser-capture'],'maximumUncoveredMs':40,'moonWarranted':True,
        'starsWarranted':True,'baselineSceneMs':baseline,'timingComparison':comparison},width)


class FirstAdmissionTests(unittest.TestCase):
    def tearDown(self):
        while _fixture_directories:_fixture_directories.pop().cleanup()

    def expect(self,receipt,status):
        result=first_complete_scene(receipt)
        self.assertEqual(result['status'],status,result)
        return result


    def test_first_endpoint_cannot_be_replaced_by_later_adoption(self):
        value=fixture(600,400);result=self.expect(value,'FAIL')
        self.assertIs(result['checks']['acceptedScene'],False)
        self.expect({**value,'acceptedMs':550},'FAIL')
        self.expect({**value,'acceptedEventKind':'native-adoption'},'FAIL')

    def test_original_budgets_are_literal(self):
        self.assertEqual(BUDGETS,{'chromium':{'navigationMs':1000,'acceptedMs':250,'frameGapMs':80,'regressionMs':250},
           'firefox':{'navigationMs':1500,'acceptedMs':400,'frameGapMs':80,'regressionMs':400}})

    def test_reference_and_exact_accepted_boundary(self):
        self.expect(fixture(),'PASS')
        self.expect(fixture(550,350),'PASS')
        self.expect(fixture(550.01,350),'FAIL')
        firefox=fixture(700,400);firefox['browser']='firefox';self.expect(firefox,'PASS')
        firefox=fixture(700.01,400);firefox['browser']='firefox';self.expect(firefox,'FAIL')

    def test_missing_first_is_unknown_despite_legacy_ready(self):
        raw={'browser':'chromium','observerKnown':True,'acceptedMs':550,'sceneMs':600,
          'at15s':{'moon':{'firstInitial':{'capturedAt':550,'publishedAt':551}}}}
        self.expect(raw,'UNKNOWN')
        value=fixture();value['timingComparison']['observer']['firstValidAdmission']=None
        value['acceptedMs']=550;retain_capture(value);self.expect(value,'UNKNOWN')
        self.expect({**fixture(),'observerKnown':False},'SEPARATE_ACQUISITION_CASE')


    def test_astronomical_utc_and_epoch_origin_are_not_endpoints(self):
        value=fixture();before=first_complete_scene(value)
        observer=value['timingComparison']['observer'];observer['clock']['timeOriginMs']=123
        for row in observer['admissions']+observer['events']+[observer['firstValidAdmission']]:row['utcMs']=-8000000000000
        retain_capture(value)
        after=self.expect(value,'PASS')
        self.assertEqual(before['intervalsMs'],after['intervalsMs'])

    def test_later_distinct_admission_does_not_replace_first(self):
        value=fixture(600,400);observer=value['timingComparison']['observer']
        later=copy.deepcopy(observer['admissions'][0]);later.update(eventId='a2',admissionId='a2',atMs=549,source='native',markerToken='0'*32)
        later['binding']['generation']=1;observer['admissions'].append(later)
        event=observer['events'][-1];event.update(admissionId='a2',binding=copy.deepcopy(later['binding']))
        retain_capture(value)
        result=self.expect(value,'FAIL');self.assertEqual(result['timing']['firstAdmissionId'],observer['admissions'][0]['admissionId'])
        observer['firstValidAdmission']=copy.deepcopy(later);retain_capture(value);self.expect(value,'FAIL')

    def test_identity_and_document_corruption(self):
        for field,changed in [('sceneIdentity','other'),('configIdentity','forged'),('generation',1),('dpr',2)]:
            with self.subTest(field=field):
                value=fixture();value['timingComparison']['observations']['moon']['binding'][field]=changed
                self.expect(value,'FAIL')
        for field,changed in [('admissionId','other'),('documentId','old-document'),('markerToken','f'*32)]:
            with self.subTest(field=field):
                value=fixture();value['timingComparison']['observations']['scene'][field]=changed
                self.expect(value,'FAIL')

    def test_required_stage_history_and_publication(self):
        for index in range(3):
            value=fixture();value['timingComparison']['observer']['events'].pop(index);retain_capture(value);self.expect(value,'UNKNOWN')
        for status in ['error','superseded']:
            value=fixture();value['timingComparison']['observer']['events'][1]['status']=status;retain_capture(value);self.expect(value,'FAIL')
        value=fixture();value['timingComparison']['observer']['overflow']=True;retain_capture(value);self.expect(value,'UNKNOWN')
        value=fixture();value['timingComparison']['observer']['rejected']=[{'reason':'invalid'}];retain_capture(value);self.expect(value,'FAIL')

    def test_no_bridge_no_common_domain(self):
        value=fixture();value['timingComparison']['bridges']=[];retain_capture(value);self.expect(value,'UNKNOWN')
        value=fixture();value['timingComparison']['navigation']['clockId']='wall-clock';self.expect(value,'FAIL')
        value=fixture();value['timingComparison']['bridges'][0]['targetClockId']='other-capture';self.expect(value,'FAIL')
        value=fixture();value['timingComparison']['bridges'][1]['sourceKind']='unix-utc';self.expect(value,'FAIL')

    def test_measured_bridge_uncertainty_does_not_inflate_budgets(self):
        self.expect(fixture(550,350,width=1),'UNKNOWN')
        self.expect(fixture(500,300,width=1),'PASS')
        self.expect(fixture(600,400,width=1),'FAIL')
        value=fixture();sample=copy.deepcopy(value['timingComparison']['bridges'][0]);sample['sampleId']='second'
        sample['targetBeforeMs']+=1;sample['targetAfterMs']+=1
        retain_window_sample(value,sample)
        value['timingComparison']['bridges'].append(sample);retain_capture(value);self.expect(value,'FAIL')

    def test_clock_and_endpoint_types(self):
        for invalid in [True,-1,float('nan'),float('inf'),'300']:
            value=fixture();observer=value['timingComparison']['observer']
            observer['firstValidAdmission']['atMs']=invalid;observer['admissions'][0]['atMs']=invalid
            self.expect(value,'FAIL')
        for invalid in [False,float('nan'),float('inf'),-1]:
            self.expect({**fixture(),'acceptedMs':invalid},'FAIL')
        value=fixture();value['timingComparison']['observer']['events'][0]['atMs']=299;self.expect(value,'FAIL')

    def test_source_presented_roles_and_raw_bytes(self):
        mutations=[lambda x:x['presentedReceipt'].update(kind='native-adoption'),
            lambda x:x['presentedReceipt'].update(sourceEventId='other-source'),
            lambda x:x['presentedReceipt'].update(eventId=x['sourceReceipt']['eventId']),
            lambda x:x['presentedReceipt'].update(artifact=ref('different.jpeg')),
            lambda x:x['presentedReceipt'].update(receiptArtifact=ref('different.jsonl')),
            lambda x:x['presentedReceipt'].update(atMs=x['presentedReceipt']['atMs']+100)]
        for index,mutation in enumerate(mutations):
            with self.subTest(index=index):
                value=fixture();mutation(value['timingComparison']['observations']['scene']);self.expect(value,'FAIL')

    def test_unchanged_independent_coverage_and_presence_gates(self):
        for changes in [{'frames':[]},{'maximumUncoveredMs':81},{'maximumUncoveredMs':False},
            {'maximumUncoveredMs':float('nan')},{'evidenceKind':'state-getter'},
            {'laterUnwarrantedGaps':[{'synthetic':True}]},{'baselineSceneMs':-1}]:
            self.expect({**fixture(),**changes},'FAIL')

    def test_coherence_navigation_and_loading_regression(self):
        value=fixture(500,300)
        for component in ['moon']:
            observation=value['timingComparison']['observations'][component]
            observation['sourceReceipt']['atMs']+=81;observation['presentedReceipt']['atMs']+=81
        retain_frame_inputs(value)
        result=self.expect(value,'FAIL');self.assertFalse(result['checks']['coherentFirstScene'])
        result=self.expect(fixture(1100,900),'FAIL');self.assertFalse(result['checks']['navigation'])
        result=self.expect(fixture(500,249),'FAIL');self.assertFalse(result['checks']['noLoadingGateRegression'])

    def test_full_128_bit_marker_roundtrip_and_ambiguous_sample(self):
        token='12345678abcdef0098765432100f00ff';pixels={(361,4):(255,0,255)}
        for row in range(4):
            word=int(token[row*8:row*8+8],16)
            for bit in range(32):
                index=row*32+bit
                pixels[(370+(index%2)*13,4+(index//2)*8)]=(255,255,255) if word>>bit&1 else (0,0,0)
        class Image:
            def getpixel(self,point):return pixels[point]
        self.assertEqual(identity_marker(Image()),token)
        pixels[(370,4)]=(128,128,128);self.assertIsNone(identity_marker(Image()))



    def test_carried_first_and_frame_substitutions_preserve_raw_contradiction(self):
        value=fixture(551,351);raw=raw_fixture_digests(value)
        result=self.expect(value,'FAIL')
        self.assertEqual(result['timing']['status'],'BOUND')
        self.assertEqual(result['intervalsMs']['acceptedScene'],[251,251])
        changed=copy.deepcopy(value);observer=changed['timingComparison']['observer']
        observer['firstValidAdmission']['atMs']=301;observer['admissions'][0]['atMs']=301
        result=self.expect(changed,'FAIL');self.assertEqual(result['timing']['status'],'INVALID')
        changed=copy.deepcopy(value)
        for observation in changed['timingComparison']['observations'].values():
            observation['sourceReceipt']['atMs']-=1;observation['presentedReceipt']['atMs']-=1
        result=self.expect(changed,'FAIL');self.assertEqual(result['timing']['status'],'INVALID')
        self.assertEqual(raw_fixture_digests(value),raw)

    def test_actual_raw_provenance_absent_is_unknown(self):
        value=fixture();comparison=value['timingComparison']
        reference=comparison['navigation']['artifact'];Path(reference['file']).unlink()
        self.expect(value,'UNKNOWN')


if __name__=='__main__':unittest.main(verbosity=2)
