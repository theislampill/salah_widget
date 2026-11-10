#!/usr/bin/env python3
"""Probe only the requested engine. Missing installations are not successful tests."""
from pathlib import Path
import argparse,json,os,platform,traceback
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser,browser_identity
from native_browser_check import ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True);rows=[];original=os.environ.get('SALAH_BROWSER')
 try:
  with sync_playwright() as p:
   for family in ['chromium','firefox','webkit']:
    os.environ['SALAH_BROWSER']=family
    try:
     b=launch_browser(p);row={'requested':family,'status':'ENGINE_LAUNCH_ONLY','identity':browser_identity(b)};b.close()
    except Exception as e:row={'requested':family,'status':'NOT_TESTED','error':str(e),'reason':'Requested browser could not be launched; no engine substitution'}
    rows.append(row)
 finally:
  if original is None:os.environ.pop('SALAH_BROWSER',None)
  else:os.environ['SALAH_BROWSER']=original
 report={'status':'RECORDED_NOT_CROSS_PLATFORM_PASS','host':platform.platform(),'engines':rows,'nativeWindows':{'status':'NOT_TESTED','reason':f'Host OS is {platform.system()}. Engine launch and display-DPR emulation alone do not establish native Windows widget qualification.'}}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.root,x.output)
