#!/usr/bin/env python3
"""Actual native 1x/10x/60x/600x preview availability and stale-publication stress.
Measurement completion is distinct from meeting the acceptance targets.
"""
from pathlib import Path
import argparse,json,time,traceback,hashlib
from browser_runtime import launch_browser,browser_identity
from playwright.sync_api import sync_playwright
from native_lifecycle_check import Widget,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True);rows=[]
 with sync_playwright() as p:
  b=launch_browser(p);identity=browser_identity(b)
  for rate in [1,10,60,600]:
   w=Widget(b,root,out,'rate-'+str(rate));row={'rate':rate,'sampleAgeBudgetMs':30000,'observationSeconds':10}
   try:
    w.ready();w.proof_ui();start=w.page.evaluate('realSkyState().renders')
    w.page.evaluate('rate=>{_simBase=simNow();_rafT0=_RAFNOW();TIMESCALE=rate;render();SalahRealSky.request(true);window.__rateSamples=[];window.__rateTimer=setInterval(()=>{let s=realSkyState(),h=SalahNativeSkyHost.capture();__rateSamples.push({at:performance.now(),status:s.status,renders:s.renders,utcMs:h.utcMs,frame:s.last?.utcMs??null,age:s.last?h.utcMs-s.last.utcMs:null,visible:!!s.last&&getComputedStyle(document.querySelector(".real-sky-canvas")).visibility!=="hidden",lifecycle:s.lifecycle});},100);}',rate)
    w.page.wait_for_timeout(10000)
    samples=w.page.evaluate('()=>{clearInterval(__rateTimer);return __rateSamples;}');s=w.snap('running');w.proof_ui()
    new=s['sky']['renders']-start
    first=next((i for i,x in enumerate(samples) if x['visible']),None)
    row['firstCurrentSeconds']=None if first is None else (samples[first]['at']-samples[0]['at'])/1000
    row['visibleFractionAfterFirstCurrent']=None if first is None else sum(x['visible'] for x in samples[first:])/len(samples[first:])
    row.update(samples=samples,newAcceptedFrames=new,visibleSamples=sum(x['visible'] for x in samples),sampleCount=len(samples),state=s,stalePublications=[x for x in s['publishes'] if abs(x['frame']-x['hostUTC'])>30000],continuousAvailability=bool(samples) and new>=2 and sum(x['visible'] for x in samples)/len(samples)>=.8)
    # A native pause is recovery, not permission to admit an obsolete moving frame.
    w.page.evaluate('()=>{_simBase=simNow();_rafT0=_RAFNOW();TIMESCALE=0;render();SalahRealSky.request(true);}')
    w.ready();recovered=w.snap('frozen-recovery');row['frozenRecoveryCurrent']=recovered['sky']['last']['utcMs']==recovered['host']['utcMs']
   except Exception:row['error']=traceback.format_exc();row['continuousAvailability']=False
   row['pageErrors']=w.errors;w.finish();rows.append(row);(out/'results.json').write_text(json.dumps({'status':'RUNNING','cases':rows},indent=2));print(rate,row.get('newAcceptedFrames'),row.get('visibleSamples'),row.get('sampleCount'),row.get('frozenRecoveryCurrent'),flush=True)
  b.close()
 report={'status':'MEASURED','browser':identity,'cases':rows,'currentnessStatus':'PASS' if all(not x.get('stalePublications') and not x.get('error') and not x.get('pageErrors') and x.get('frozenRecoveryCurrent') for x in rows) else 'FAIL','availabilityTarget':'At least two new accepted frames and >=80% visible samples during each 10-second accelerated-preview observation; no relaxation of 30-second accepted-UTC limit. This is a CP9 stress target, not an inherited native promise.','availabilityStatus':'PASS' if all(x['continuousAvailability'] for x in rows) else 'NOT_ALL_PASSED','runtimeSha256':hashlib.sha256((root/'real-sky/native-sky.js').read_bytes()).hexdigest(),'scope':'Actual native timeScale on the same widget; no alternative astronomical clock. Controlled provider/date fixture. Continuous visibility is distinct from stale-safety.'}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();r=run(x.root,x.output);raise SystemExit(0 if r['currentnessStatus']=='PASS' else 1)
