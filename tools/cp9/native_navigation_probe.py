#!/usr/bin/env python3
"""Report direct navigation separately from embedded actual-widget qualification."""
from pathlib import Path
import argparse,functools,http.server,threading,json,hashlib
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,Quiet,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True);server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'.')));threading.Thread(target=server.serve_forever,daemon=True).start();results=[]
 fragment='#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&simTime=23:30&simWx=0&simCloud=0&simPrecip=0&qa=1'
 try:
  with sync_playwright() as p:
   browser=launch_browser(p)
   for kind,url in [('HTTP',f'http://127.0.0.1:{server.server_port}/index.html'),('file',(root/'index.html').as_uri())]:
    c=browser.new_context(viewport={'width':430,'height':640},reduced_motion='reduce');c.add_init_script(INIT);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort());entry={'kind':kind,'status':'NOT_VERIFIED','error':None}
    try:
     page.goto(url+fragment,wait_until='domcontentloaded',timeout=15000);page.wait_for_function("document.querySelectorAll('.p').length===6&&window.realSkyState?.().status==='ready'",timeout=45000)
     entry.update(status='PASS',state=page.evaluate('()=>({rows:document.querySelectorAll(".p").length,sky:realSkyState()})'));page.locator('.c').screenshot(path=str(out/(kind+'.png')))
    except Exception as e:entry.update(status='ENVIRONMENT_BLOCKED' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(e) else 'NOT_VERIFIED',error=str(e))
    entry['pageErrors']=errors;results.append(entry);c.close()
   version=browser.version;browser.close()
 finally:server.shutdown()
 result={'scope':'Informational direct top-level navigation probe. An administrative block is not a product pass, nor an independent Windows/Firefox result. Embedded/subresource actual-widget gates are separate.','browser':version,'sourceSha256':hashlib.sha256((root/'index.html').read_bytes()).hexdigest(),'results':results};(out/'results.json').write_text(json.dumps(result,indent=2));print([(r['kind'],r['status']) for r in results]);return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.root.resolve(),x.output)
