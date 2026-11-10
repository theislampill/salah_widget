#!/usr/bin/env python3
"""Measured main-thread CPU attribution at the failing CPUx4 case.
CDP sampling is diagnostic, not a proof of browser-process or worker memory cost.
"""
from pathlib import Path
import argparse,json,collections,hashlib
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser,browser_identity,browser_options
from native_browser_check import ROOT,INIT
from cp9_responsiveness import MONITOR

def summarise(profile):
 nodes={n['id']:n for n in profile['nodes']};parent={c:n['id'] for n in profile['nodes'] for c in n.get('children',[])};selftime=collections.Counter();inclusive=collections.Counter()
 for nid,dt in zip(profile.get('samples',[]),profile.get('timeDeltas',[])):
  selftime[nid]+=dt
  here=nid
  while here in nodes:inclusive[here]+=dt;here=parent.get(here)
 def rows(counter):
  return [{'function':nodes[k]['callFrame']['functionName'] or '(anonymous)','url':nodes[k]['callFrame']['url'],'line':nodes[k]['callFrame']['lineNumber']+1,'sampledMs':v/1000} for k,v in counter.most_common(25)]
 return {'topSelf':rows(selftime),'topInclusive':rows(inclusive),'sampledMs':sum(profile.get('timeDeltas',[]))/1000,'sampleCount':len(profile.get('samples',[]))}

def run(root,out):
 out.mkdir(parents=True,exist_ok=True);records=[]
 if browser_options()[0]!='chromium':raise RuntimeError('CDP CPU attribution requires explicitly selected Chromium; no fallback to another engine.')
 with sync_playwright() as p:
  b=launch_browser(p);ident=browser_identity(b)
  for baseline in [True,False]:
   name='native-baseline' if baseline else 'cp9';c=b.new_context(viewport={'width':430,'height':640},reduced_motion='no-preference');page=c.new_page();page.route('**/*',lambda r:r.abort());errors=[];page.on('pageerror',lambda e:errors.append(str(e)));cdp=c.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
   page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=CPU-profile&method=4&simTime=23:30&timeScale=1&simWx=2&simCloud=60&simPrecip=0&qa=1&motion=full'");page.evaluate(INIT)
   src=(root/('src/native/index.html' if baseline else 'offline.html')).read_text(encoding='utf-8')
   if baseline:src=src.replace('<script src="config.js"></script>','<script>'+(root/'src/native/config.js').read_text(encoding='utf-8').replace('</script','<\\/script')+'</script>')
   page.set_content(src,wait_until='load',timeout=90000);page.wait_for_function("document.querySelectorAll('.p').length===6&&document.querySelector('.c').classList.contains('moon-ready')",timeout=90000)
   if not baseline:page.wait_for_function("realSkyState()?.status==='ready'",timeout=90000)
   cdp.send('Profiler.enable');cdp.send('Profiler.setSamplingInterval',{'interval':1000});cdp.send('Profiler.start');page.evaluate(MONITOR)
   if not baseline:page.evaluate('()=>SalahRealSky.request(true)')
   page.wait_for_timeout(6000);profile=cdp.send('Profiler.stop')['profile'];measure=page.evaluate('()=>{clearInterval(__cp9Timer);return __cp9Perf;}')
   (out/(name+'.cpuprofile')).write_text(json.dumps(profile));records.append({'name':name,'cpuThrottle':4,'sourceSha256':hashlib.sha256((root/('src/native/index.html' if baseline else 'index.html')).read_bytes()).hexdigest(),'measurement':measure,'profile':summarise(profile),'pageErrors':errors});c.close();print(name,records[-1]['profile']['topSelf'][:6],flush=True)
  b.close()
 report={'status':'RECORDED','browser':ident,'cases':records,'scope':'Requested six-second loaded main-thread V8 interval at CPUx4; actual sampled duration is recorded and may be longer when the stop command is delayed. Inclusive times overlap; not an additive cost breakdown. No worker/GPU samples and not a real mobile/device benchmark. DOM/dialog activity included; profile instrumentation itself has overhead.'};(out/'results.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.root,x.output)
