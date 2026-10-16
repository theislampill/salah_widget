"""Preserve prior cutoffs, apply the owner clarification, and seal the next review."""
from pathlib import Path
import datetime, hashlib, json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
old=O/'SOLAR-INVESTIGATION-r1.json';d=json.loads(old.read_text())
d['schema']='r0021-owner-sun-flicker-investigation/v2';d['atUtc']=now()
d['supersedes']={'path':old.name,'sha256':sha(old),'scope':'Owner clarification: irregular brightness fluctuations, not rapid regular strobe; bounded investigation only. Original observations preserved.'}
d['status']='NOT_INDEPENDENTLY_REPRODUCED; POTENTIALLY_ADDRESSED_BY_VERIFIED_SOLAR_CURRENTNESS_CORRECTION; EXACT_INDEPENDENT_REVIEW_PENDING'
d['ownerObservation']='Irregular Sun brightness fluctuations like a failing fluorescent bulb at sunrise or forenoon; not rapid regular strobe. Cloud involvement uncertain; browser/URL unspecified.'
d['classification']['renderedSunAlternation']='Owner symptom not independently reproduced in bounded readable Chromium source samples, including changing cloud obstruction. This does not certify absence of intermittent irregular flicker.'
d['source']['excludedClaim']='The verified currentness correction potentially addresses the owner symptom; causal explanation unconfirmed. No new mask/CSS/compositor workaround, timer, radiometric formula or H1/V5 material change.'
d['ownerDisposition']='Finish already warranted regression/native verification and exact independent review; if no demonstrated remaining defect, return to principal R0021 obligations. No indefinite symptom search, no new RLGWO now, no waiver of original acceptances.'
d['nextDiscriminatingObservation']='Only if the owner observes recurrence after production delivery and commissions a focused investigation: browser/version, exact URL or extension, startup versus settled,10-20s whole-card recording; phone recording if display flickers but screen capture does not.'
d['evidence'].append({'path':'intake/head-handoff-r5.txt','sha256':sha(O/'intake/head-handoff-r5.txt')})
out=O/'SOLAR-INVESTIGATION-r2.json';assert not out.exists();out.write_text(json.dumps(d,indent=2)+'\n')
old=O/'QUALIFICATION-FRONTIER-r2.json';f=json.loads(old.read_text());f['atUtc']=now()
f['supersedes']={'path':old.name,'sha256':sha(old),'scope':'Final r5 source correction, owner flicker clarification, bounded native observations and regression; prior evidence and all original gates preserved.'}
f['source'].update(candidateBuild='builds/integrated-r5',runtimeSha256=d['source']['runtimeSha256'],indexSha256='916a79b5cc18916309d36c85174293b87cb4549209d01ff2c4268534399d585b',nativeSourceSha256=d['source']['sha256'])
rows={r['id']:r for r in f['acceptance']}
def append(name,claim,paths):
 r=rows['R0021-'+name];r['claimAndLimit']+=' '+claim
 r['evidence'].extend({'path':p,'sha256':sha(O/p)} for p in paths)
append('A01','The measurements bind integrated-r3, not finalr5. The shared solar helper and added no-timetable work have no qualified final cost comparison. Parity is not timing/allocation proof; all24 scopes and whole21-08.b remain OPEN.',['preservation-r5/RUNTIME.json'])
append('S4','Owner clarified irregular Sun brightness fluctuations, not rapid regular strobe. Not independently reproduced; potentially addressed by verified solar-currentness correction, subject to exact final review. No indefinite symptom search or new waiver. Firefox source blanks and actual-cloud omission remain named coverage limits.',['SOLAR-INVESTIGATION-r2.json'])
append('S6','New source controls reproduce then correct absent/stale Sun and inherited six optional solar/lunar optical permissions when timetable unavailable. Pending/settled42 vectors and old/new110 full atmosphere+22sinks match; bounded native sunrise source regression supports Sun presence. This does not establish the cause of the owner symptom.',['intake/solar-regression-red-r3-valid.txt','intake/solar-optics-red-r4-both.txt','intake/solar-regression-green-r5.txt','intake/solar-preservation-r5.json','intake/head-handoff-r5.txt'])
rows['R0021-S8']['claimAndLimit']='Finalr5 canonical source checkout and two builds agree on142 runtime files,201 protected owners unchanged. Final native regression704PASS0FAIL0cancel4TODO/708; host48 retained, final head handoff allPassed. Earlier r3/r4 source-slice fixture failures and corrected reruns are preserved. No runtime change followed finalr5 checks. Exact final candidate review pending.'
append('S8','', ['preservation-r5/RESULTS.json','preservation-r5/RUNTIME.json','intake/native-regression-r5.txt','intake/native-regression-r4.txt','intake/native-regression-r4-repaired.txt','intake/delivery-build-r5.txt'])
append('S10','Solar source correction retains original radiometry, geometry with the existing horizon and H1/V5 owners. No new H1 appearance decision is inferred. Native r4 sunrise body evidence predates r5 six-optics withdrawal; exact-source parity supports bounded reuse only. Continuous original S10 remains open.',['SOLAR-INVESTIGATION-r2.json','independent-review/solar-source-r4-review.json'])
f['retainedFailures']+=['Sunrise10s prayer hold meets10s deadline; no successful settlement in paired Chromium cases','Chromium sunrise r4 WinError10053 retained','FinalFirefox forenoon fixture not admitted; no cloud coverage and whole-frame blanks recur']
f['ownerFlickerDisposition']=d['status']
f['next']='Exact finalr5 source/build/docs and bounded native evidence review by existing sole reviewer; explicit public projection review; nondeploying immutable evidence publication plus Git/HTTP readback; focused unqualified Draft PR Implements #33. No production merge or closure while original timing/cost/continuity/Firefox-parent gates remain unresolved. Owner symptom receives bounded potentially-addressed disposition, no indefinite search.'
out=O/'QUALIFICATION-FRONTIER-r3.json';assert not out.exists();out.write_text(json.dumps(f,indent=2)+'\n')
s=(O/'seal_candidate.py').read_text()
s=s.replace('CANDIDATE-REVIEW-REQUEST-r1.json','CANDIDATE-REVIEW-REQUEST-r2.json').replace('len(names) == 64','len(names) == 65').replace("pathspec = O / 'CANDIDATE-PATHS-r1.nul'","pathspec = O / 'CANDIDATE-PATHS-r2.nul'\nprior_pathspec = O / 'CANDIDATE-PATHS-r1.nul'")
s=s.replace("assert pathspec.is_file(), 'Do not replace pre-existing staging'","assert prior_pathspec.is_file(), 'Do not replace pre-existing staging'")
s=s.replace("staged == set(pathspec.read_text().split('\\0'))", "staged == set(prior_pathspec.read_text().split('\\0'))")
s=s.replace("assert staged == set(names), 'Unexpected unstaged paths'","assert set(names) - staged == {'tests/real-sky/native-solar-startup.test.cjs'}, 'Unexpected additional paths'")
s=s.replace('intake/delivery-runtime-r3.json','preservation-r5/RUNTIME.json').replace('QUALIFICATION-FRONTIER-r2.json','QUALIFICATION-FRONTIER-r3.json').replace('candidate-final-r1-review','candidate-final-r2-review')
anchor="pins = {name: sha((O / name).read_bytes()) for name in evidence}"
extra=['SOLAR-INVESTIGATION-r1.json','SOLAR-INVESTIGATION-r2.json','CANDIDATE-REVIEW-REQUEST-r1.json','independent-review/candidate-final-r1-review.json','independent-review/solar-source-r4-review.json','preservation-r5/RESULTS.json','intake/native-regression-r5.txt','intake/solar-regression-red-r3-valid.txt','intake/solar-optics-red-r4-both.txt','intake/solar-regression-green-r5.txt','intake/solar-preservation-r5.json','intake/head-handoff-r5.txt']
extra+=['solar-analysis-r2/'+c['case']+'/RESULT.json' for c in d['cases']]
assert s.count(anchor)==1;s=s.replace(anchor,'evidence += '+repr(extra)+'\n'+anchor)
p=O/'seal_candidate_r2.py';assert not p.exists();p.write_text(s)
s=(O/'commit_candidate.py').read_text().replace('-r1','-r2')
s=s.replace("'Join the catalogue and compact Moon startup owners to delivered H1,\\n'", "'Join the catalogue and compact Moon startup owners to delivered H1,\\n'\n    'and publish current solar state independently of prayer acquisition.\\n'")
p=O/'commit_candidate_r2.py';assert not p.exists();p.write_text(s)
print(json.dumps({'solar':sha(O/'SOLAR-INVESTIGATION-r2.json'),'frontier':sha(O/'QUALIFICATION-FRONTIER-r3.json'),'candidateSealer':sha(O/'seal_candidate_r2.py')}))
