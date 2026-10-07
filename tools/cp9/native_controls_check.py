#!/usr/bin/env python3
"""Focused actual-widget time/config/invalid-input controls; no reference-viewer replacement."""
import argparse,json,time,hashlib,sys
from pathlib import Path
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True);results=[];errors=[]
 with sync_playwright() as p:
  b=launch_browser(p);page=b.new_page(viewport={'width':400,'height':600},reduced_motion='reduce')
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&simTime=23:30&simWx=0&simCloud=0&simPrecip=0&units=c&qa=1'")
  page.evaluate(INIT);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load')
  def wait():page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000)
  def capture(name):
   d=page.evaluate("()=>({sky:realSkyState(),native:SalahNativeSkyHost.capture(),rows:document.querySelectorAll('.p').length,synthetic:document.querySelectorAll('.stars circle,.milkyway circle,.starglints line').length,visible:document.querySelector('.real-sky-canvas').style.visibility,moon:document.querySelector('.mphoto').getAttribute('href').length})")
   results.append({'name':name,**d});return d
  wait();a=capture('initial-madinah');assert a['rows']==6 and a['synthetic']==0
  page.evaluate("async()=>{window.__testTimezone='America/New_York';await applyConfig({...CONFIG,lat:28.5383,lon:-81.3792,tz:'America/New_York',label:'Florida'},{save:false});SalahRealSky.request(true);}")
  page.wait_for_function("realSkyState().status==='ready'&&realSkyState().last.observer.latDeg===28.5383",timeout=90000)
  c=capture('accepted-florida');assert c['sky']['last']['native']['generation']>a['sky']['last']['native']['generation'];assert c['rows']==6
  page.evaluate("async()=>{window.__testTimezone='Asia/Riyadh';await applyConfig({...CONFIG,lat:24.47,lon:39.61,tz:'Asia/Riyadh',label:'Madinah-return'},{save:false});SalahRealSky.request(true);}")
  page.wait_for_function("realSkyState().status==='ready'&&realSkyState().last.observer.latDeg===24.47",timeout=90000)
  d=capture('accepted-return');assert d['sky']['last']['native']['generation']>c['sky']['last']['native']['generation']
  before=d['sky']['last']['utcMs'];page.evaluate("()=>{_simBase+=3600000;render();SalahRealSky.request(true);}")
  page.wait_for_function("(n)=>realSkyState().status==='ready'&&realSkyState().last.utcMs===n",arg=before+3600000,timeout=90000)
  e=capture('accepted-one-hour-seek');assert e['sky']['last']['sources']!=d['sky']['last']['sources']
  page.evaluate("()=>{window.__savedLat=lat;lat=null;SalahRealSky.request(true);}")
  page.wait_for_function("realSkyState().status==='unavailable'",timeout=5000)
  f=capture('invalid-observer');assert f['rows']==6 and f['visible']=='hidden' and f['synthetic']==0
  page.evaluate("()=>{lat=window.__savedLat;SalahRealSky.request(true);}");wait();capture('observer-restored')
  page.screenshot(path=str(out/'controls-restored.png'))
  b.close()
 result={'passed':not errors,'controls':results,'pageErrors':errors,'harness':'Actual native app; provider fixtures and direct controlled calls to native applyConfig and explicit-time owner; not a live provider audit.'}
 (out/'results.json').write_text(json.dumps(result,indent=2));assert not errors,errors
 print('Native controls PASS',len(results));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(ROOT));a.add_argument('--output',required=True);x=a.parse_args();run(Path(x.root),Path(x.output))
