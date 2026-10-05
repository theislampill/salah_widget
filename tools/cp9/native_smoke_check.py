"""Run the repository's unchanged browser smoke instrument through actual HTTP."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_browser_check import ROOT,Quiet
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity
def run(root,out):
    out.mkdir(parents=True,exist_ok=True);server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            b=launch_browser(p);q=b.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
            q.goto(f'http://127.0.0.1:{server.server_port}/tests/smoke.html',wait_until='domcontentloaded')
            q.wait_for_function('!!window.__smoke',timeout=240000);r=q.evaluate('window.__smoke');r.update(pageErrors=errors,browser=browser_identity(b),runtimeTreeSha256=runtime_identity(root)['treeSha256'])
            (out/'results.json').write_text(json.dumps(r,indent=2),encoding='utf-8');(out/'rendered.txt').write_text(q.locator('#out').inner_text(),encoding='utf-8');q.screenshot(path=str(out/'smoke.png'));b.close();return r
    finally:server.shutdown()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.root,a.output);print(r['status'],r['pass'],r['fail']);raise SystemExit(0 if r['status']=='PASS' else 1)
