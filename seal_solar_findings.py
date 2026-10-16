"""Bind the owner symptom, bounded observations and separate source corrections."""
from pathlib import Path
import datetime, hashlib, json
O=Path(__file__).resolve().parent
R=Path(r'<candidate>')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pin=lambda p:{'path':p.relative_to(O).as_posix(),'sha256':sha(p)}
cases=[]
for name in ['chromium-sunrise-prayer-r3','chromium-sunrise-prayer-r4','firefox-sunrise-prayer-r4','firefox-forenoon-cloud-strobe-r5']:
 p=O/'solar-analysis-r2'/name/'RESULT.json';d=json.loads(p.read_text())
 raw=json.loads((O/'native'/name/'results.json').read_text());q=raw['runs'][0]['final']['qa']
 cases.append({'case':name,'analysis':pin(p),'runtime':d['runtime'],'frames':d['frameCount'],
  'physicalSolarAltitudeDeg':d['physicalSolarAltitudeDeg'],'prayerReady':d['prayerReady'],
  'weatherEligible':q['cache']['currentEligible'],'weatherReason':q['cache']['currentUnavailableReason'],
  'actualCloudLayers':{k:q['clouds'][k] for k in ['low','mid','high']},
  'requestedWeather':d['syntheticWeather'],'skyFinal':d['skyFinal'],
  'phaseSelectionStatistics':{k:{x:v[x] for x in ['frames','range','maxSourceGapMs','maxAdjacentCoreChange']} for k,v in d['phases'].items()},
  'traceCounts':{k:d['trace'][k] for k in ['samples','states','solarVectors','masks']},
  'limitations':d['limitations']})
evidence=['solar-flicker-recordings-r1/RESULTS.json','solar-flicker-cloud-analysis-r1/RESULTS.json',
 'intake/solar-currentness-red-r3-valid.txt','intake/solar-regression-red-r3-valid.txt',
 'intake/solar-optics-red-r4-both.txt','intake/solar-regression-green-r5.txt',
 'intake/solar-preservation-r5.json','intake/native-regression-r5.txt',
 'preservation-r5/RESULTS.json','preservation-r5/RUNTIME.json',
 'independent-review/candidate-final-r1-review.json','independent-review/solar-source-r4-review.json',
 'solar-probe-tools-r1/PREPARATION.json','solar-probe-tools-r2/PREPARATION.json',
 'prepare_solar_probe_r2.py','run_solar_probe_r2.py','inspect_solar_r2.py']
d={'schema':'r0021-owner-sun-strobe-investigation/v1','atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'OWNER_RAPID_SUN_STROBE_UNCONFIRMED_UNFIXED; SEPARATE_SOURCE_CURRENTNESS_CORRECTIONS_VERIFIED_WITHIN_SCOPE',
 'ownerObservation':'Sun at sunrise or forenoon, possible cloud involvement, like a bad fluorescent bulb; browser/URL unspecified.',
 'placement':'Existing R0021 S4/S6/S10 and source/currentness qualification; original S1 and callback-cost contracts unchanged.',
 'source':{'path':'src/native/index.html','sha256':sha(R/'src/native/index.html'),
  'runtimeSha256':'c24fe3819371386952c41de4135ef6fa896ce676b18c2b1d1b679640cbe7d5bb',
  'semanticOwner':'nativeSolarPresentation / paintSolarPresentation / paintCelestialWithoutTimetable',
  'correction':'Share existing solar formulas and sinks with no-timetable publication; derive absent arc horizon from existing SVG104/180; withdraw prior six optional solar/lunar optical permissions until current complete atmosphere.',
  'excludedClaim':'Not a fix for rapid strobing. No new mask/CSS/compositor workaround, timer, radiometric formula or H1/V5 material change.'},
 'classification':{
  'renderedSunAlternation':'Not reproduced in bounded readable Chromium source samples, including actual varying cloud obstruction. No all-platform absence claim.',
  'visibilityOpacityBrightness':'Separate no-timetable omission/stale Sun and old cloud-optics permissions reproduced by source controls and corrected. Diagnostic Sun body/disc stayed1 after correction; no rapid alternation established.',
  'staleCurrentAsync':'Source generation/epoch fences inspected; no competing stale/current Sun publisher established. Counts alone do not align worker publication with exact presented pixels.',
  'browserPresentation':'Unresolved for Firefox whole-frame blanks; no unique compositor/GPU diagnosis.',
  'captureArtefact':'Firefox blanks remove the exterior marker too, with identical blank JPEG bytes across scenes. This does not establish whether blanks occur on the physical display and does not explain a Sun-only owner report.'},
 'existingCoverage':'Original clear-day roughly60-degree Sun; dawn below horizon is negative control; night cloud/rain cases do not cover Sun/cloud flicker. Existing S1-S10 cannot already certify this symptom absent.',
 'newConditions':{'browsers':['Chromium148','Firefox150.0.2'],'viewport':[390,600],'dpr':1,'card':[325,530],
  'location':'Orlando28.5383,-81.3792','clock':'Advancing1x anchored2026-09-25T11:25Z sunrise or17:00Z forenoon',
  'durationSeconds':45,'ordinarySeconds':30,'diagnosticSeconds':15,
  'observer':'Original JPEG/source sidecar plus resampled25fps WebM; CSS/state polling only after30s.'},
 'cases':cases,
 'caseInterpretation':[
  'Chromium sunrise r3/r4 use10s prayer delay, meeting actual10s deadline; neither settles. Before Sun absent; after Sun visible. r4 WinError10053 retained. qa.sunEl0 without model is not physical ephemeris.',
  'Firefox sunrise r4 uses5s delay after identifying deadline. Original5s Sun while pending;9/12s whole blanks;44s intact settled frame. Not uninterrupted settlement proof.',
  'Final Firefox r5 forenoon weather unavailable: requested35percent fixture not admitted, clouds0, one mask alpha255. Missing cloud coverage, not successful cloud test. Whole blanks recur.',
  'Earlier Chromium cloudy r3:190 changing decoded masks, body/disc1, no rapid Sun-only alternation in sampled original pairs. Ordinary5-30s max adjacent solar ROI change .15893 code; diagnostic31-45s .20734. Means are selection only.'
 ],
 'regression':'704PASS0FAIL0cancel4TODO/708 final native source tests;29 focused tests;110 old/new full-atmosphere plus22 sink parity cases and42 pending/settled vector cases; two deterministic142-file builds;201 protected owner files unchanged.',
 'performanceLimit':'Existing reviewed r3 cost measurement remains incomplete24/24 scopes. Finalr5 helper/extra pending work not qualified by a cost comparison; no performancePASS or unchanged-allocation claim.',
 'residuals':['Owner browser/exact URL or extension and triggering state unknown','Firefox cloud condition not exercised','Firefox blank capture/presentation unresolved','Chromium ordinary sunrise source gaps175-177ms','Continuous initial/preview/refined and H1 acceptance remain open','No exact worker-publication/presented-frame causal alignment'],
 'nextDiscriminatingObservation':'Browser/version, exact widget URL or extension, startup versus settled, and10-20s whole-card recording of Sun strobe. If screen recording is steady while display strobes, phone recording of same event distinguishes capture/display path.',
 'evidence':[pin(O/p) for p in evidence],
 'rootPixelInspection':{'derivedSelectionSheets':['solar-analysis-r2/'+c['case']+'/selection.png' for c in cases[1:]],
  'originals':['native/firefox-forenoon-cloud-strobe-r5/video/page@8ff4c88a200a32a754d9361fef5bb056.webm.frames/000123.jpeg',
   'native/firefox-forenoon-cloud-strobe-r5/video/page@8ff4c88a200a32a754d9361fef5bb056.webm.frames/000124.jpeg',
   'native/firefox-sunrise-prayer-r4/video/page@98bdb1d523b5669f2d66b15e256df27b.webm.frames/001060.jpeg'],
  'scope':'Selected original full frames viewed, plus ranked sheets and prior views retained in tool record; not a continuous watch certificate.'}}
for p in d['rootPixelInspection']['originals']:assert (O/p).is_file()
out=O/'SOLAR-INVESTIGATION-r1.json';assert not out.exists();out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(pin(out)))
